#include <stdio.h>
#include <stdlib.h>

void bar(){
	bar();
	int* arr = (int *)malloc(sizeof(int) * 1024);
	free(arr);
}	

int func_defined(){
	bar();
	return 0;
}

int main(){
	func_defined();
	printf("Hello World");
	return 0;
}
