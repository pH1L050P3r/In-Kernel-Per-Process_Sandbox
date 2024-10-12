clang-12 -fno-builtin -Xclang -load -Xclang ../source/llvm-pass/build/CallGraphPass/libCallGraphPass.* $1 $2
clang-12 -fno-builtin -Xclang -load -Xclang ../source/llvm-pass/build/DummyCallAddPass/libDummyCallAddPass.* $1 $2 -Wl ../source/dummy/build/libdummy.so
