import lexer
import sys

def analyze(ast):
	for item in ast:
		if item["context"] == "expression":
			analyze_expression(item["content"])

def analyze_expression(ast):
    if type(ast) is list:
            if len(ast) == 2:
                return analyze_unary(ast)
            else:
                return analyze_infix(ast)
    else:
        return ast.tag

def analyze_infix(ast):
    left = analyze_expression(ast[0])
    operator = ast[1]
    right = analyze_expression(ast[2])
    #do more check with left right and operator here later. Below is just a small test
    if left != right:
        throw_error("Mismatched type", ast[2])
    return left

def analyze_unary(ast):
    operator = ast[0]
    operand = analyze_expression(ast[1])

    #do check with operator and operand later
    return operand

def throw_error(msg, token):
    sys.stderr.write("Error: %s at line %s: %s \n" % (msg, token.line , token.char))
