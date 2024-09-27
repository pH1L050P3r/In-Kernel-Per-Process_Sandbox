#include <stdio.h>

extern void bar();
int func_defined();

int func_defined(){
	bar();
	return 0;
}

int main(){
	int x;
	for(int c; c < 100; c++) bar();
p:
	getchar();
	func_defined();
	if(x > 10)
		printf("Hello World");
	func_defined();
	while (getchar() == 'a')
	{
		main();
	}
	
	return 0;
}
