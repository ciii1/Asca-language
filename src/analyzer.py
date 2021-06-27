import lexer
import sys

#wrapper for global variables
class analyzer_state():
    def __init__(self):
        self.function_list = {}
        self.variable_list = {}
        self.is_error = False
        self.is_in_while = False
        self.is_in_function = False

    def is_var_exist(self, token):
        res = self.variable_list.get(token.val)
        if res is None:
            res = self.function_list.get(token.val)
            if res is None:
                throw_error("undeclared variable: %s" % token.val, token)
                return None
        else:
            return res

    def is_function_exist(self, token):
        res = self.function_list.get(token.val)
        if res is None:
            res = self.variable_list.get(token.val)
            if res is None:
                throw_error("undeclared function %s" % token.val, token)
            else:
                throw_error("can't call a non-function identifier", token)
        else:
            return res

class item():
    def __init__(self, dtype, is_in_memory):
        self.type = dtype
        self.is_in_memory = is_in_memory
        
        
def analyze(ast):
    state = analyzer_state()
    for item in ast:
        if item["context"] == "expression":
            res = analyze_expression(item["content"], state)
            if res is None:
                state.is_error = True

def analyze_expression(ast, state):
    if type(ast) is list:
            if len(ast) == 2:
                return analyze_unary(ast, state)
            else:
                return analyze_infix(ast, state)
    else:
        return analyze_value(ast, state)

def analyze_infix(ast, state):
    left = analyze_expression(ast[0], state)
    operator = ast[1]
    right = analyze_expression(ast[2], state)
    if left is None or right is None:
        return None

    if operator.val == "+" or\
       operator.val == "-" or\
       operator.val == "*" or\
       operator.val == "/":
        if is_literal(left) and\
           is_literal(right):
            return left
        if left.type == right.type:
            return left
    
    throw_error("Mismatched type for operator %s" % operator.val, operator)

def analyze_unary(ast, state):
    operator = ast[0]
    operand = analyze_expression(ast[1], state)
    if operand is None:
        return None

    if operator.val == "-" or\
       operator.val == "+":
        if is_literal(operand) or\
           operand.type == "LIT":
            return operand
    elif operator.val == "@":
        if is_array(operand) or\
           operand.is_in_memory:
            operand.type = "LIT"
            return operand
    elif operator.val == "$":
        operand.type = "LIT"
        operand.is_in_memory = False
        return operand
    
    throw_error("Mismatched type for unary operator %s" % operator.val, operator)

def analyze_value(ast, state):
    if type(ast) is dict:
        if ast["type"] == "identifier":
            return analyze_identifier(ast, state)
        elif ast["type"] == "function_call":
            return analyze_function_call(ast, state)
    else:
        return item(ast.tag, False)

def analyze_identifier(ast, state):
    res = state.is_var_exist(ast["value"])
    if res is None:
        return None
    return item(res["tag"], True)

def analyze_function_call(ast, state):
    pass

def is_literal(val):
    if val.type == "INT"   or\
       val.type == "FLOAT" or\
       val.type == "CHAR"  or\
       val.type == "BOOL"  or\
       val.type == "LIT":
        return True
    else:
        return False
def is_array(val):
    if val.type == "STRING" or\
       val.type == "LIT":
        return True
    else:
        return False
    
def throw_error(msg, token):
    sys.stderr.write("semantic_error: %s at line %s: %s \n" % (msg, token.line , token.char+1))
