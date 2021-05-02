# Asca
a language where you able to specify variables size manually, this means that you're able to store an int with size of 1 byte. This gives you more control to your program.
example syntax:
```
qword a:int = 3 //declare an int with size of 8 byte (qword) on the stack
print(str + a)
```
there will be ```type``` keyword wich let you declare your own type
```
type color: dword;

dword a:color = 1
byte b:color = 3 //error: trying to declare a variable below minimum size of type 'color'
```
and structured type: 
```
type color: dword{ //error: can't manually assign size to a structured type (it should be "type color")
  byte red:int
  byte green:int
  byte blue:int
}

auto red: color = color(100, 0, 0)
auto green: color = color(0, 255, 0)

auto blank: color = color(green=12, blue=30) //error: the sub-type "red" doesn't have a default value
```
It is compiled to nasm assembly



  
