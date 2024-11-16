#include <sys/syscall.h>
#include <stdio.h>

#define SYS_DUMMY_NUM 549

// int dummy(int code){
//     // int sys_call_number_for_dummy = 549;
//     // printf("function Called with ID : %d\n", code);
//     return syscall(SYS_DUMMY_NUM, code);
// }

int dummy(int code) {
    long result;
    asm volatile (
        "movq %1, %%rax;"  // Load system call number into RAX
        "movq %2, %%rdi;"  // Load the first argument into RDI
        "syscall;"       
        "movq %%rax, %0;"  // Store the result from RAX into the output variable
        : "=r" (result)    // Output operands
        : "r" ((long)SYS_DUMMY_NUM), "r" ((long)code) // Input operands
        : "%rax", "%rdi"   // Clobbered registers
    );
    return (int)result;
}