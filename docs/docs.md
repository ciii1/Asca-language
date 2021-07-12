
# About

Asca is a language that aims to remove all the unnecesary high level abstractions
to let you gain control of your program.

# Variables

In asca, a size of a variable does not depedend on it's type,
rather you specify it manually everytime you declare a variable.
the size keywords are:
qword: 8 bytes,
dword: 4 bytes,
word: 2 bytes,
byte: 1 byte,

for example:

```
type int; //declare a type called int
dword i:int; //declare a variable i with the type int and size of a dword
```

this, while it maybe an exhausting thing to do, gives you more control
to your own program.

Asca also doesn't have global variables, due to it's structure,
this perhaps would explain why:

```
type int;

dword a:int = 1;

func getOne() {
	return 1;
}

a = 1;
```

You see? the main "function" of an ascs program is the part where you declare
global variables in a C program. This make asca doesn't have a global variable, because
there is no room to declare one.

Also, all variables are stored in the stack.

# Arrays

The syntax to declare an array is:
```
dword[5] a:int;
```
this will store 5 dwords onto the stack.
how you will fill this with the number 2 would be:

```
a[0] = 2;
a[1] = 2;
a[2] = 2;
a[3] = 2;
a[5] = 2;
```

Or you can do it with a loop.

Asca also doesn't allow VLAs (Variable length array), your program safety is always
been our priority.

this means you can't do:
```
dword[a] b:int;
```

# Pointers

In asca, pointers are just numbers that holds the address of a memory.
Nothing special with it.
To get an address of a value, you can use the @ operator:
```
dword a:int;
qword b:ptr;
b = @a;
```
this will get the address of a and store it in b.

To access the value of a memory address, you can use the $ operator:
```
dword c:int;
c = $(dword)b;
```
Unlike C, Asca pointers don't have type. This means you'll need to specify the size
you wan't to read everytime you access the value of a memory address.
the syntax of $ operator is:
```
$(size)address;
```
You can also type cast using this:
```
dword a:int = 2;
byte b:char = 'a';
a = $(byte)@b;
```
this will assign the value of b to a.

# Strings

string literals are stored into the .data section. And since it's
considered as an array, you can't assign it directly into a variable.
Doing this will give you an error:
```
byte[5] a:char = "hello";
```
You should assign a pointer that points to the string literal "hello":
```
qword a:ptr = @"hello";
```
this (for me at least) gives you more consistency than C where variables are not clear wether it's stored in .data section or in the stack,
but in Asca, every variables is stored on the stack.

# Loops
there are two types of loop in asca: while and for loop.
their syntax is the same with C loops' syntax.

# If, elif, else.
the syntax of if, elif and else is the same with
C. Just that the "else if" is replaced with "elif"

# Functions

In asca you can declare functions with the 'func' keyword.
```
func add(qword a:int, qword b:int):int {
	return a+b;
}
```

Note that Asca parameters are pass by value, like C
and not pass by reference like python and php.
