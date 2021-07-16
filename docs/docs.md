
### About

Asca is a language that aims to remove all the unnecesary high level abstractions
to let you gain more control of your program.

### Basics

#### Principles
There are two main principles that asca operates on:
- every value is treated the same. Meaning that a float will be treated the same as an int.
- a type is used to differentiate those values; it restricts you from doing operations on different type.

now you'd probably start to wonder, how can Asca treat every value as the same thing as each values has different memory representations and operations? Well, that's why Asca has a lot operators; you simply differentiate the operations yourself (like how you'd do it in assembly). For example:

```
type float; //declare a type called float
qword a:float := 1.2;
a := 13.2;
```
notice the `:=` operator? It's called precise-assigment operator. You can use it for floating point values, it uses the `movss`/`movsd`/`movq` (depends to the variable size) instruction to assign to a memory while `=` uses the `mov` instruction. You can, for sure, use the the `=` operator for floats but you wouldn't get the precision you'd have with `:=`, but sometimes, that's what you want, so Asca allows you to do that.

#### Values

as i said, every values is treated the same in Asca, they can be divided into two categories:
- memory-stored values : values stored in memory, like variables
- constants : constant values, like `12`, `'a'` or `4.2`

Constants are stored in the registers unless literal floats and literal strings, they are stored in read-only memory (`.data` section).

With these in mind, let's continue with the syntax.

### Types

As mentioned before, types are just things that restrict you from doing operations with different types. You can declare it with the `type` keyword:
```
type int1;
type int2;
dword a:int1;
dword b:int2;
a+b; //semantic_error: mismatched type
dword a:int1 = b; //semantic_error: cannot assign type 'int2' to 'int1'
```
a size can have a minimum value:
```
type float:dword;
word a:float = 1; //semantic_error: variable a's size is less than minimum size of a the type 'float'
```

### Variables

In asca, a size of a variable does not depedend on it's type,
rather you specify it manually everytime you declare a variable.
the size keywords are:
- `qword`: 8 bytes,
- `dword`: 4 bytes,
- `word`: 2 bytes,
- `byte`: 1 byte,

for example:

```
type int; //declare a type called int
dword i:int; //declare a variable i with the type int and size of a dword
```

this, while it maybe an exhausting thing to do, gives you more control
to your own program.

Asca also doesn't allow global variables.
All variables are stored in the stack.

### Arrays

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
By meaning you can't do it with this: (at least for now)

```
dword[5] a:int = {2, 2, 2, 2, 2};
```

Asca also doesn't allow VLAs (Variable length array), your program safety is always our priority.
You can use the heap for dynamic memory instead.

this means you can't do:
```
dword[a] b:int;
```

### Pointers

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
Because asca pointers are just the same as an int and other values. This means you'll need to specify the size
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
this will assign a pointer that points to `b`, read one byte from it and assign it to `a`.

### Strings

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

### Loops
there are two types of loop in asca: `while` and `for` loop.
their syntax is the same with C loops' syntax:
```
for(initialisation; condition; expression) {
	statements;
}
```
and `while`:

```
while(condition) {
	statements;
}
```

### `If`, `elif`, `else`.
the syntax of `if`, `elif` and `else` is the same with
C. Just that the `else if` is replaced with `elif`:
```
if(condition) {
	statements;
} elif (condition) {
	statements;
} else (condition) {
	statements;
}
```
### Functions

In asca you can declare functions with the `func` keyword.
```
func add(qword a:int, qword b:int):int {
	return a+b;
}
```

Note that Asca parameters are pass by value, like C
and not pass by reference like python and php.

### Comments

```
/*
	multiline comments
*/
```
and single-line comments:

```
//single-line comments
```



