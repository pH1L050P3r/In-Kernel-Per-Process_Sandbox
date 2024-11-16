#include <stdio.h>
#include<stdlib.h>

extern void bar();
int func_defined();

int func_defined(){
	bar();
	return 0;
}

int main(){
	int x;
	for(int c = 1; c < 2; c++) bar();
p:
	getchar();
	func_defined();
	if(x > 10)
		printf("Hello World\n");
	func_defined();
	for(int i = 0; i < 2; i++)
	{
		printf("Hello\n");
	}
	int* arr = (int *)malloc(sizeof(int) * 1024);
	free(arr);
	
	return 0;
}
