#include <sys/syscall.h>

int dummy(int code){
    int sys_call_number_for_dummy = 1024;
    return syscall(sys_call_number_for_dummy, code);
}