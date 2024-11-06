#include <sys/syscall.h>
#include <stdio.h>

#define SYS_DUMMY_NUM 549

inline int dummy(int code){
    // int sys_call_number_for_dummy = 549;
    // printf("function Called with ID : %d\n", code);
    return syscall(SYS_DUMMY_NUM, code);
}