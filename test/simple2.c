#include <stdlib.h>

void bar(){
	bar();
	int* arr = (int *)malloc(sizeof(int) * 1024);
	free(arr);
}	
