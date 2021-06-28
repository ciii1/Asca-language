import lexer
import sys

#wrapper for global variables
class analyzer_state():
    def __init__(self):
        self.function_list = {}
        self.variable_list = {}
        self.type_list = {}
        self.is_error = False
        self.is_in_while = False
        self.is_in_function = False

    def is_variable_exist(self, token):
        res = self.variable_list.get(token.val)
        if res is None:
            res = self.function_list.get(token.val)
            if res is None:
                return None
        else:
            return res

    def is_function_exist(self, token):
        res = self.function_list.get(token.val)
        if res is None:
            return None
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
        elif item["context"] == "variable_declaration":
            res = analyze_variable_declaration(item["content"], state)
            if res is None:
                state.is_error = True
            state = res

def analyze_variable_declaration(ast, state):
    if ast["init"] is not None:
        if ast["array-size"] is not None:
            throw_error("can't assign to an array", ast["size"])
            return None
        res = analyze_expression(ast["init"]["content"], state)
        if res is None:
            return None 
        if not is_literal(res) and\
           ast["type"].val != res.type:
            throw_error("cannot assign %s to %s" % (res.type, ast["type"].val), ast["size"])
            return None
    if state.is_variable_exist(ast["id"]):
        throw_error("variable %s is already exist" % ast["id"].val, ast["size"])
        return None
    if ast["array-size"] is None:
        state.variable_list[ast["id"].val] = {"size": ast["size"].val, "type": ast["type"].val, "array-size": None}
    else:
        state.variable_list[ast["id"].val] = {"size": ast["size"].val, "type": ast["type"].val, "array-size": ast["array-size"].val}
    return state

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
        if is_literal(left) or is_literal(right) or\
           left.type == right.type:
            return left
    
    throw_error("mismatched type" % operator.val, operator)

def analyze_unary(ast, state):
    operator = ast[0]
    operand = analyze_expression(ast[1], state)
    if operand is None:
        return None

    if operator.val == "-" or\
       operator.val == "+":
        if is_literal(operand) or\
           operand.type == "LIT" or\
           operand.is_in_memory:
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
    throw_error("mismatched type for unary operator %s" % operator.val, operator)

def analyze_value(ast, state):
    if type(ast) is dict:
        if ast["type"] == "identifier":
            return analyze_identifier(ast, state)
        elif ast["type"] == "function_call":
            return analyze_function_call(ast, state)
    else:
        return item(ast.tag, False)

def analyze_identifier(ast, state):
    res = state.is_variable_exist(ast["value"])
    if res is None:
        throw_error("undeclared variable: %s" % ast["value"].val, ast["value"])
        return None
    return item(res["type"], True)

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
    if val.type == "STRING":
        return True
    else:
        return False
    
def throw_error(msg, token):
    sys.stderr.write("semantic_error: %s at line %s: %s \n" % (msg, token.line , token.char+1))
