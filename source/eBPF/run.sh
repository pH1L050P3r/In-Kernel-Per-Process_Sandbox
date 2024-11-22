ulimit -u 65000
export BCC_PROBE_LIMIT=50000
python3 enforce_NFA_ebpf.py --dot-file ./graph.dot --function-map ./library_functions.txt --library-functions ./called_lib_functions.txt