mkdir ./build
gcc -c -fPIC dummy.c -o ./build/dummy.o
gcc -shared -o ./build/libdummy.so ./build/dummy.o