#include <sys/syscall.h>
#include <stdio.h>

int dummy(int code){
    int sys_call_number_for_dummy = 549;
    printf("function Called with ID : %d\n", code);
    return syscall(sys_call_number_for_dummy, code);
}