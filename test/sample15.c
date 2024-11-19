#include<stdio.h>
#include <unistd.h>

void copy_fd(int x)
{
    if(x == 0)
        return;
    int file_desc = openat("test");
    int copy_desc = dup(file_desc);
    copy_fd(--x);
}

int main()
{
    int x = 1, y = 2, z = 3;
    brk(0);
    pipe((int *)x);
    socket();

    if(y-x == z-1)
        connect();
    else if(z-y == x)
        read(2, (void *)x, 5);
    else
        write(2,"hello",5);
    dup(y);
    getpid();
    uname();

}
