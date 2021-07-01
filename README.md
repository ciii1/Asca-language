# Asca
a language where you able to specify variables size manually, this means that you're able to store an int with size of 1 byte. This gives you more control to your program.
example syntax:
```
qword a:int = 3; //declare an int with size of 8 byte (qword) on the stack
qword str:ptr = @"Hello world"; //declare a pointer to a string that is located on the data section (the @ sign means a pointer)
print(str);
```
there will be ```type``` keyword wich lets you declare your own type
```
type color: dword;

dword a:color = 1;
byte b:color = 3; //error: trying to declare a variable below minimum size of type 'color'
```
It is compiled to nasm assembly



  
