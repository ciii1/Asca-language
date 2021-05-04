import parser

code = input("%>")
while code:
    print(parser.parse(code), "\n")
    code = input("%>")  
