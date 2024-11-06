How to add dummy system call in linux kernel:

1) copy dummy folder in linux source code root
2) add below line of code in include/linux/syscalls.h
    asmlinkage int sys_dummy(int fid); 
3) add below line of code in arch/x86/entry/syscalls/syscall_64.tbl
    549 common  dummy               sys_dummy

How to compile kernel:

1)  Download and extrace linux kernel
2)  copy dummy folder in linux kernel source code root
3)  cp -v /boot/config-$(uname -r) .config
4)  make menuconfig
5)  Enable BPF_SYSCALL
6)  make -j7
7)  scripts/config --disable SYSTEM_TRUSTED_KEYS (optional)
8)  scripts/config --disable SYSTEM_REVOCATION_KEYS (optional)
9)  sudo make modules_install
10) sudo make install