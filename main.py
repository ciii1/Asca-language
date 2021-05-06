import parser
import sys

if len(sys.argv) > 1:
    f = open(sys.argv[1])
    res = parser.parse(f.read())
    if res.is_error:
        print("Compilation canceled due to previous error(s)")
    else:
        print(res.get_output())
else:
    code = input("%>")
    while code:
        res = parser.parse(code)
        if not res.is_error:
            print(res.get_output(), "\n")
        code = input("%>")  

