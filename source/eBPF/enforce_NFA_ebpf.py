from bcc import BPF

# Graph construction
def construct_from_dot(filepath):
    graph = {}
    
    with open(filepath, "r") as file:
        for line in file:
            line = line.strip()
            if "->" not in line or '[label="' not in line: continue
            parts = line.split("->")
            src = parts[0].strip()
            dst_label = parts[1].strip()
            dst_part, label_part = dst_label.split("[label=")
            dst = dst_part.strip()
            label = label_part.replace('"]', "").strip('"')
            
            if src not in graph: graph[src] = []
            graph[src].append((dst, label))
            if dst not in graph: graph[dst] = []
    return graph


def read_function_map(file_path):
    function_map = {}
    rev_function_map = {}
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 2: continue
            func_name, func_id = parts
            function_map[func_name] = int(func_id)
            rev_function_map[int(func_id)] = func_name
    return function_map, rev_function_map


def get_new_heads(graph, heads):
    new_heads = []
    stack = list(heads)
    visited = set()
    while len(stack) > 0:
        curr = stack.pop()
        if curr not in visited: visited.add(curr)
        new_heads.append(curr)
        for node, label in graph.get(curr, []):
            if label == "e" or label.startswith("call_") or label.startswith("ret_") or curr.split("_")[0] == label:
                stack.append(node)
    return new_heads


def check_func_call(graph_data, heads,next_func_call):
    if not next_func_call:
        return [], False
    
    new_heads = set()
    for head in heads:
        edges = graph_data[head]
        for e in edges:
            if e[1] == next_func_call:
                new_heads.add(e[0])
    
    if new_heads:
        return list(new_heads), True
    return [], False


def generate_ebpf_program(functions):
    base_program = """
#include <uapi/linux/ptrace.h>

BPF_PERF_OUTPUT(output);
BPF_HASH(process, u32, u32);
BPF_ARRAY(stack, int, 10);

struct command {
    char type[64];
    char func[128];
    int next_lib_call;
};

TRACEPOINT_PROBE(syscalls, sys_enter_dummy) {
    u32 pid = bpf_get_current_pid_tgid();
    if (process.lookup(&pid) == NULL) {
        process.update(&pid, &pid);
    }

    int zero = 0;
    int init_count = 0;
    if (stack.lookup(&zero) == NULL) {
        stack.update(&zero, &init_count);
    }

    struct command c = {.type = "dummy_sys_call", .func = "", .next_lib_call = args->value};
    output.perf_submit(args, &c, sizeof(c));
    return 0;
}
"""

    for func in functions:
        trace_function = f"""
int trace_lib_{func}_enter(struct pt_regs *ctx) {{
    u32 pid = bpf_get_current_pid_tgid();
    if (process.lookup(&pid) == NULL) return 0;

    int zero = 0;
    int *st_count = stack.lookup(&zero);
    if (st_count) {{
        if (*st_count == 0) {{
            struct command c = {{}};
            c.next_lib_call = PT_REGS_IP(ctx);
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

file_path = "musl_functions.txt"
function_map, rev_function_map = read_function_map(file_path)
# functions_to_trace = [func for func in function_map.keys() if func[0] != '_']
functions_to_trace = ["getchar", "printf", "malloc", "free"]
graph_data = construct_from_dot("./graph.dot")


b = BPF(text=generate_ebpf_program(functions_to_trace))
libc_path = "/lib/x86_64-linux-gnu/libc.so.6"
for func in functions_to_trace:
    try:
        b.attach_uprobe(name=libc_path, sym=func, fn_name=f"trace_lib_{func}_enter")
        b.attach_uretprobe(name=libc_path, sym=func, fn_name=f"trace_lib_{func}_exit")
    except Exception as e:
        print(f"Unable to trace lib : {func} : {e}")


heads = get_new_heads(graph_data, ["main_0"])
next_func_call = None
function_call_list = []

def print_event(cpu, data, size):
    global heads, next_func_call
    data = b["output"].event(data)
    type_, func, next_lib_call = data.type.decode(), data.func.decode(), data.next_lib_call
    print("-"*80)
    print("command : ", type_)
    print("func_name : ", func)
    print("next_lib_call : ", next_lib_call)
    print("-"*80)

    if(type_ == "dummy_sys_call"):
        next_func_call = rev_function_map.get(next_lib_call, None)
        print(next_func_call, next_lib_call)
    elif(type_ == "libc_call"):
        new_heads, flag = check_func_call(graph_data, heads,next_func_call)
        if(flag == False):
            # exit programm
            print(function_call_list)
            exit(0)
        else:
            old = heads
            heads = get_new_heads(graph_data, new_heads)
            print(heads, new_heads, old)


# b["output"].open_perf_buffer()
b["output"].open_perf_buffer(print_event, page_cnt=2<<10)
while True:
    b.perf_buffer_poll(5)