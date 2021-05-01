import parser

code = input("%>")
while code:
    parser.parse(code)
    code = input("%>")
