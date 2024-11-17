from bcc import BPF
import os
import signal

class DataLoader:
    def __init__(self, function_map_path="musl_functions.txt", function_list_path="library_function_list.txt"):
        self._path_lib_func = function_map_path
        self._lib_called_func_path = function_list_path
        self.function_map = {}
        self.rev_function_map = {}
        self.library_function_called = []
        self.read_function_list()
        self.read_function_map()

    def read_function_list(self):
        with open(self._lib_called_func_path, "r") as file:
            functions = [line.strip() for line in file if line.strip()]
        self.library_function_called = functions
    
    def read_function_map(self):
        function_map = {}
        rev_function_map = {}
        with open(self._path_lib_func, "r") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) != 2:
                    continue
                func_name, func_id = parts
                function_map[func_name] = int(func_id)
                rev_function_map[int(func_id)] = func_name
        self.function_map = function_map
        self.rev_function_map = rev_function_map

    def get_lib_function_map(self):
        return self.function_map, self.rev_function_map
    
    def get_library_function_called(self):
        return self.library_function_called

class Graph:
    def __init__(self, dot_file):
        self._graph = {}
        self._start = None
        self._end = None
        self._heads = []

        self.build_from_dotfile(dot_file)
        self._initialize()

    def build_from_dotfile(self, dot_file):
        graph = {}
        incoming_edges = {}

        with open(dot_file, "r") as file:
            for line in file:
                line = line.strip()
                if "->" not in line or '[label="' not in line:
                    continue
                parts = line.split("->")
                src = parts[0].strip()
                dst_label = parts[1].strip()
                dst_part, label_part = dst_label.split("[label=")
                dst = dst_part.strip()
                label = label_part.replace('"]', "").strip('"')

                if src not in graph:
                    graph[src] = []
                graph[src].append((dst, label))

                if dst not in graph:
                    graph[dst] = []

                # Track incoming edges
                if dst not in incoming_edges:
                    incoming_edges[dst] = 0
                incoming_edges[dst] += 1

                if src not in incoming_edges:
                    incoming_edges[src] = 0

        # Find start and end nodes
        start_nodes = [node for node in graph if incoming_edges[node] == 0]
        end_nodes = [node for node in graph if not graph[node]]  # Nodes with no outgoing edges

        self._graph = graph
        self._start = start_nodes
        self._end = end_nodes

    def _initialize(self):
        self._heads = ["main_0"]
        self.next_func_call = None
        self.function_call_list = []
        self.update_epsillon_heads()
        
    def reset(self):
        self._initialize()

    def get_heads(self):
        return self._heads

    def update_epsillon_heads(self):
        new_heads = []
        stack = list(self._heads)
        visited = set()
        while stack:
            curr = stack.pop()
            if curr not in visited:
                visited.add(curr)
            new_heads.append(curr)
            for node, label in self._graph.get(curr, []):
                if label == "e" or label.startswith("call_") or label.startswith("ret_") or curr.split("_")[0] == label:
                    stack.append(node)
        self._heads = new_heads

    def check_func_call(self, next_func_call):
        if not next_func_call:
            return False
        
        new_heads = set()
        for head in self._heads:
            edges = self._graph[head]
            for e in edges:
                if e[1] == next_func_call:
                    new_heads.add(e[0])

        self._heads = list(new_heads)
        self.update_epsillon_heads()
        if new_heads: return  True
        return False



class EBPFTracer:
    def __init__(self, graph, libc_path, functions_to_trace, function_map, rev_function_map):
        self.graph = graph
        self.libc_path = libc_path
        self.functions_to_trace = functions_to_trace
        self.function_map = function_map
        self.rev_function_map = rev_function_map

        self.bpf = None
        self.next_func_call = None
        self.function_call_list = []

    def generate_ebpf_program(self):
        base_program = """
#include <uapi/linux/ptrace.h>

BPF_PERF_OUTPUT(output);
BPF_HASH(process, u32, u32);
BPF_ARRAY(stack, int, 10);

struct command {
    char type[64];
    char func[128];
    int next_lib_call;
    int pid;
};

TRACEPOINT_PROBE(syscalls, sys_enter_dummy) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    if (process.lookup(&pid) == NULL) {
        process.update(&pid, &pid);
    }

    int zero = 0;
    int init_count = 0;
    if (stack.lookup(&zero) == NULL) {
        stack.update(&zero, &init_count);
    }

    struct command c = {.type = "dummy_sys_call", .func = "", .next_lib_call = args->value, .pid = pid};
    output.perf_submit(args, &c, sizeof(c));
    return 0;
}
"""

        for func in self.functions_to_trace:
            trace_function = f"""
int trace_lib_{func}_enter(struct pt_regs *ctx) {{
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    if (process.lookup(&pid) == NULL) return 0;

    int zero = 0;
    int *st_count = stack.lookup(&zero);
    if (st_count) {{
        if (*st_count == 0) {{
            struct command c = {{}};
            c.next_lib_call = PT_REGS_IP(ctx);
            c.pid = pid;
            __builtin_strncpy(c.type, "libc_call", sizeof(c.type));
            __builtin_strncpy(c.func, "{func}", sizeof(c.func));
            int new_count = *st_count + 1;
            stack.update(&zero, &new_count);
            output.perf_submit(ctx, &c, sizeof(c));
        }} else {{
            int new_count = *st_count + 1;
            stack.update(&zero, &new_count);
        }}
    }}
    return 0;
}}

int trace_lib_{func}_exit(struct pt_regs *ctx) {{
    u32 pid = bpf_get_current_pid_tgid();
    if (process.lookup(&pid) == NULL) return 0;

    int zero = 0;
    int *st_count = stack.lookup(&zero);
    if (st_count && *st_count > 0) {{
        int new_count = *st_count - 1;
        stack.update(&zero, &new_count);
    }}
    return 0;
}}
"""
            base_program += trace_function
        return base_program

    def initialize_bpf(self):
        self.bpf = BPF(text=self.generate_ebpf_program())
        for func in self.functions_to_trace:
            try:
                self.bpf.attach_uprobe(name=self.libc_path, sym=func, fn_name=f"trace_lib_{func}_enter")
                self.bpf.attach_uretprobe(name=self.libc_path, sym=func, fn_name=f"trace_lib_{func}_exit")
            except Exception as e:
                print(f"Unable to trace lib: {func}: {e}")

    def print_event(self, cpu, data, size):
        event = self.bpf["output"].event(data)
        type_, func, next_lib_call, pid = event.type.decode(), event.func.decode(), event.next_lib_call, event.pid


        if type_ == "dummy_sys_call":
            self.next_func_call = self.rev_function_map.get(next_lib_call, None)
            print("-" * 80)
            print("command : ", type_)
            print("next_lib_call : ", next_lib_call, self.next_func_call)
            print("pid : ", pid)
            print("-" * 80)
        elif type_ == "libc_call":
            print("-" * 80)
            print("command : ", type_)
            print("func_call : ", func)
            print("pid : ", pid)
            print("-" * 80)
            old_heads = self.graph.get_heads()
            # print(self.next_func_call, old_heads)
            flag = self.graph.check_func_call(self.next_func_call)
            new_heads = self.graph.get_heads()
            if not flag:
                print("Killing process with ID : ", pid)
                os.kill(pid, signal.SIGKILL)
                print(self.function_call_list)
                graph.reset()
            else:
                # print(old_heads, new_heads)
                self.function_call_list.append(func)
                if self.graph._end[0] in new_heads and len(new_heads) == 1:
                    print(self.function_call_list)
                    graph.reset()

    def start_tracing(self):
        self.bpf["output"].open_perf_buffer(self.print_event, page_cnt=2 << 10)
        while True:
            self.bpf.perf_buffer_poll(5)


if __name__ == "__main__":
    graph = Graph(dot_file="./graph.dot")
    data_loader = DataLoader("musl_functions.txt", "library_function_list.txt")
    function_map, rev_function_map = data_loader.get_lib_function_map()
    functions_to_trace = data_loader.get_library_function_called()


    tracer = EBPFTracer(
        graph=graph,
        libc_path="/lib/x86_64-linux-gnu/libc.so.6",
        functions_to_trace=functions_to_trace,
        function_map=function_map,
        rev_function_map=rev_function_map
    )
    tracer.initialize_bpf()
    tracer.start_tracing()
