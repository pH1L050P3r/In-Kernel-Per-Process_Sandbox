from bcc import BPF
import os
import signal


class EBPFTracer:
    def __init__(self, function_map_file, graph_file, libc_path, functions_to_trace):
        self.function_map_file = function_map_file
        self.graph_file = graph_file
        self.libc_path = libc_path
        self.functions_to_trace = functions_to_trace
        self.bpf = None
        self.graph_data = {}
        self.start = None
        self.end = None
        self.function_map = {}
        self.rev_function_map = {}
        self.heads = []
        self.next_func_call = None
        self.function_call_list = []

    def _reset(self):
        self.heads = self.get_new_heads(["main_0"])
        self.next_func_call = None
        self.function_call_list = []

    def construct_graph(self):
        graph = {}
        incoming_edges = {}

        with open(self.graph_file, "r") as file:
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

        self.graph_data = graph
        self.start = start_nodes
        self.end = end_nodes

    def read_function_map(self):
        function_map = {}
        rev_function_map = {}
        with open(self.function_map_file, "r") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) != 2:
                    continue
                func_name, func_id = parts
                function_map[func_name] = int(func_id)
                rev_function_map[int(func_id)] = func_name
        self.function_map = function_map
        self.rev_function_map = rev_function_map

    def get_new_heads(self, heads):
        new_heads = []
        stack = list(heads)
        visited = set()
        while stack:
            curr = stack.pop()
            if curr not in visited:
                visited.add(curr)
            new_heads.append(curr)
            for node, label in self.graph_data.get(curr, []):
                if label == "e" or label.startswith("call_") or label.startswith("ret_") or curr.split("_")[0] == label:
                    stack.append(node)
        return new_heads

    def check_func_call(self, heads, next_func_call):
        if not next_func_call:
            return [], False
        
        new_heads = set()
        for head in heads:
            edges = self.graph_data[head]
            for e in edges:
                if e[1] == next_func_call:
                    new_heads.add(e[0])
        
        if new_heads:
            return list(new_heads), True
        return [], False

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
            new_heads, flag = self.check_func_call(self.heads, self.next_func_call)
            if not flag:
                print("Killing process with ID : ", pid)
                os.kill(pid, signal.SIGKILL)
                print(self.function_call_list)
                self._reset()
            else:
                old_heads = self.heads
                self.heads = self.get_new_heads(new_heads)
                # print(self.heads, new_heads, old_heads)
                self.function_call_list.append(func)
                if self.end[0] in self.heads and len(self.heads) == 1:
                    print(self.function_call_list)
                    self._reset()

    def start_tracing(self):
        self.heads = self.get_new_heads(["main_0"])
        self.bpf["output"].open_perf_buffer(self.print_event, page_cnt=2 << 10)
        while True:
            self.bpf.perf_buffer_poll(5)

def get_function_list(file_path):
    with open(file_path, "r") as file:
        functions = [line.strip() for line in file if line.strip()]
    return functions


# Example Usage
if __name__ == "__main__":
    file_path = "library_function_list.txt"
    function_list = get_function_list(file_path)
    tracer = EBPFTracer(
        function_map_file="musl_functions.txt",
        graph_file="./graph.dot",
        libc_path="/lib/x86_64-linux-gnu/libc.so.6",
        functions_to_trace=["getchar", "printf", "malloc", "free"]
    )
    tracer.read_function_map()
    tracer.construct_graph()
    tracer.initialize_bpf()
    tracer.start_tracing()
