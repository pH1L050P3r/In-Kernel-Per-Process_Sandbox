#include <linux/kernel.h>
#include <linux/syscalls.h>

SYSCALL_DEFINE1(dummy, int, value)
{
    printk("Received value: %d\n", value);
    return 0;
}