#include <stdlib.h>

void bar(){
	while(getchar() == 'a')
		bar();
	int* arr = (int *)malloc(sizeof(int) * 1024);
	free(arr);
}	
