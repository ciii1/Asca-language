import copy
import lexer
import sys

#TODO:
#-if elif else

#wrapper for global variables
class analyzer_state():
    def __init__(self):
        self.function_list = {}
        self.variable_list = {}
        self.type_list = {}
        self.is_error = False
        self.is_in_loop = False
        self.parent_function = None

    def is_variable_exist(self, token):
        res = self.variable_list.get(token.val)
        if res is None:
            res = self.function_list.get(token.val)
            if res is None:
                return None
        else:
            return res

class item():
    def __init__(self, token, dtype, is_in_memory):
        self.token = token
        self.type = dtype
        self.is_in_memory = is_in_memory        
        
def analyze(ast, state = None):
    if state is None:
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
        elif item["context"] == "type_declaration":
            res = analyze_type_declaration(item["content"], state)
            if res is None:
                state.is_error = True
        elif item["context"] == "function_declaration":
            res = analyze_function_declaration(item["content"], state)
            if res is None:
                state.is_error = True
        elif item["context"] == "return":
            if analyze_return(item["content"], state) is None:
                state.is_error = True
        elif item["context"] == "for":
            if analyze_for(item["content"], state) is None:
                state.is_error = True
        elif item["context"] == "break":
            if analyze_break(item, state) is None:
                state.is_error = True
        elif item["context"] == "continue":
            if analyze_continue(item, state) is None:
                state.is_error = True
        elif item["context"] == "while":
            if analyze_while(item["content"], state) is None:
                state.is_error = True

    return state

def analyze_function_declaration(ast, state):
    local = copy.deepcopy(state)
    local.is_error = False
    local.variable_list = {}
    local.parent_function = {"id": ast["id"].val, "type": ast["type"].val}
    if state.is_variable_exist(ast["id"]):
        throw_error("variable %s is already exist" % ast["id"].val, ast["id"])
        return None
    if state.type_list.get(ast["type"].val) is None:
        throw_error("undeclared type", ast["type"])
        return None
    res = analyze(ast["parameters"], local)
    if res.is_error:
        print(ast["id"].val)
        return None
    local.variable_list = res.variable_list
    state.function_list[ast["id"].val] = {"parameters":copy.deepcopy(res.variable_list), "type":ast["type"].val}
    if analyze(ast["body"], local).is_error:
        return None
    return state

def analyze_while(ast, state):
    if analyze_expression(ast["condition"]["content"], state) is None:
        return None
    local = copy.deepcopy(state)
    local.is_in_loop = True
    if ast["body"] is not None:
        if analyze(ast["body"], local) is None:
            return None
    return state

def analyze_for(ast, state):
    if analyze([ast["setup"]], state) is None:
        return None
    if analyze([ast["condition"]], state) is None:
        return None
    if analyze([ast["increment"]], state) is None:
        return None
    local = copy.deepcopy(state)
    local.is_in_loop = True
    if ast["body"] is not None:
        if analyze(ast["body"], local) is None:
            return None
    return state

def analyze_continue(ast, state):
    if not state.is_in_loop:
        throw_error("continue keyword outside a loop", ast["value"])
        return None
    return 0

def analyze_break(ast, state):
    if not state.is_in_loop:
        throw_error("break keyword outside a loop", ast["value"])
        return None
    return 0

def analyze_return(ast, state):
    if state.parent_function is None:
        throw_error("return keyword outside function", ast["keyword"])
        return None
    res = analyze_expression(ast["value"]["content"], state)
    if res is None:
        return None
    if not is_literal(res) and\
       res.type != state.parent_function["type"]:
        throw_error("return value mismatched with the function type", ast["keyword"])
        return None
    return res.type
    
def analyze_type_declaration(ast, state):
    is_exist = state.type_list.get(ast["id"].val)
    if is_exist:
        throw_error("type '%s' is already exist" % ast["id"].val, ast["id"])
        return None
    if ast["min_size"] is None:
        state.type_list[ast["id"].val] = {"min_size":"byte"}
    else:
        state.type_list[ast["id"].val] = {"min_size":ast["min_size"].val}
    return state

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
            throw_error("cannot assign '%s' to '%s'" % (res.type, ast["type"].val), ast["size"])
            return None
    if state.is_variable_exist(ast["id"]):
        throw_error("variable %s is already exist" % ast["id"].val, ast["size"])
        return None
    if ast["array-size"] is None:
        state.variable_list[ast["id"].val] = {"size": ast["size"].val, "type": ast["type"].val, "array-size": None, "init":ast["init"]}
    else:
        state.variable_list[ast["id"].val] = {"size": ast["size"].val, "type": ast["type"].val, "array-size": ast["array-size"].val, "init":ast["init"]}
    res = state.type_list.get(ast["type"].val)
    if res is None:
        throw_error("undeclared type", ast["type"])
        return None
    if size_to_number(res["min_size"])  > size_to_number(ast["size"].val):
        throw_error("the size of variable '%s' is below the minimum size of type '%s'" % (ast["id"].val, ast["type"].val), ast["size"]) 
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
    if operator.tag == "ARITHMETICAL_OPERATOR" or\
       operator.tag == "RELATIONAL_OPERATOR":
        if not is_literal(left) and not is_literal(right) and\
           left.type  != right.type:
            throw_error("mismatched type", left.token)
    elif operator.tag == "ASSIGNMENT_OPERATOR":
        if is_array(left):
            throw_error("cannot assign to an array", left.token)
            return None
        if not left.is_in_memory:
            throw_error("cannot assign to a non-memory-stored value", left.token)
            return None
        if left.type != right.type and\
           left.type != "LIT" and\
           not is_literal(right):
            throw_error("mismatched type", left.token)
            return None
        
    return left

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
            operand.type = "INT" #@ is just an operator that lookup the memory address of a value, it'll return an int ofc
            return operand
    elif operator.val == "$":
        if not is_array(operand):
            operand.type = "LIT"
            operand.is_in_memory = True
            return operand    
    throw_error("mismatched type for unary operator %s" % operator.val, operator)
    return None

def analyze_value(ast, state):
    if type(ast) is dict:
        if ast["type"] == "identifier":
            return analyze_identifier(ast, state)
        elif ast["type"] == "function_call":
            return analyze_function_call(ast, state)
    else:
        return item(ast, ast.tag, False)

def analyze_identifier(ast, state):
    res = state.is_variable_exist(ast["value"])
    if res is None:
        throw_error("undeclared variable: %s" % ast["value"].val, ast["value"])
        return None
    return item(ast["value"], res["type"], True)

def analyze_function_call(ast, state):
    res = state.function_list.get(ast["value"].val)
    if res is None:
        throw_error("undeclared function '%s'" % ast["value"].val, ast["value"])
        return None
    #check parameters 
    expr = analyze(ast["parameters"], state)
    if expr is None:
        return None    
    #check length
    if len(ast["parameters"]) != len(state.function_list[ast["value"].val]["parameters"]):
        throw_error("expected %i parameters but %i were given" % (len(state.function_list[ast["value"].val]["parameters"]), len(ast["parameters"])), ast["value"])
        return None
    return item(ast["value"], res["type"], False)

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

def size_to_number(size):
    if size == "qword":
        return 8
    elif size == "dword":
        return 4
    elif size == "word":
        return 2
    elif size == "byte":
        return 1
