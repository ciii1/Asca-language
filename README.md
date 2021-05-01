# Asca
a language where you able to specify a variables size manually, this means that you're able to store an int with size of 1 byte. This gives you more control to your program. You also able to decide wether it should be stored on the heap or the stack.
example syntax:
```
qword a:int = 3 //declare an int with size of 8 byte (qword) on the stack
*byte[20] str:char = "Hello world" //a string with size of 20 byte on the heap
print(str + a)
```
