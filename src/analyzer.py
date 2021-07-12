import copy
import lexer
import sys

#TODO:

#wrapper for global variables
class analyzer_state():
    def __init__(self):
        self.function_list = {}
        self.variable_list = {}
        self.type_list = {}
        self.is_error = False
        self.is_in_loop = False
        self.parent_function = None
        self.has_return_value = False

class item():
    def __init__(self, token, dtype, is_array, is_in_memory):
        self.token = token
        self.type = dtype
        self.is_array = is_array
        self.is_in_memory = is_in_memory  
        
def analyze(ast, state = analyzer_state()):
    for tree in ast:
        if tree["context"] == "expression":
            res = analyze_expression(tree["content"], state)
            if res is None:
                state.is_error = True
        elif tree["context"] == "variable_declaration":
            res = analyze_variable_declaration(tree["content"], state)
            if res is None:
                state.is_error = True
        elif tree["context"] == "type_declaration":
            res = analyze_type_declaration(tree["content"], state)
            if res is None:
                state.is_error = True
        elif tree["context"] == "function_declaration":
            res = analyze_function_declaration(tree["content"], state)
            if res is None:
                state.is_error = True
        elif tree["context"] == "return":
            if analyze_return(tree["content"], state) is None:
                state.is_error = True
        elif tree["context"] == "for":
            if analyze_for(tree["content"], state) is None:
                state.is_error = True
        elif tree["context"] == "break":
            if analyze_break(tree, state) is None:
                state.is_error = True
        elif tree["context"] == "continue":
            if analyze_continue(tree, state) is None:
                state.is_error = True
        elif tree["context"] == "while":
            if analyze_while(tree["content"], state) is None:
                state.is_error = True
        elif tree["context"] == "if":
            if analyze_if(tree["content"], state) is None:
                state.is_error = True
    return state

def analyze_function_declaration(ast, state):
    if state.function_list.get(ast["id"].val) or state.variable_list.get(ast["id"].val) or state.type_list.get(ast["id"].val):
        throw_error("name '%s' is already exist" % ast["id"].val, ast["id"]);
        return None
    local = copy.deepcopy(state)
    local.is_error = False
    local.variable_list = {}
    local.parent_function = {"id": ast["id"].val, "type": ast["type"].val}
    if state.type_list.get(ast["type"].val) is None:
        throw_error("undeclared type", ast["type"])
        return None
    if len(ast["parameters"]) == 0:
        state.function_list[ast["id"].val] = {"parameters":{}, "type":ast["type"].val}
    else:
        for param in ast["parameters"]:
            res = analyze_variable_declaration(param["content"], local)
            if res is None:
                return None
            if param["content"]["array-size"] is not None:
                throw_error("can't use array as a parameter for a function", ast["id"])
                return None
            if param["content"]["init"] is not None:
                throw_error("cannot assign in parameter list", ast["id"])
                return None
        state.function_list[ast["id"].val] = {"parameters":copy.deepcopy(res.variable_list), "type":ast["type"].val}
    if analyze(ast["body"], local).is_error:
        return None
    if not local.has_return_value:
        throw_error("a function must has a return value" , ast["id"])
        return None
    return state

def analyze_if(ast, state):
    if analyze_expression(ast["condition"]["content"], state) is None:
        return None
    local = copy.deepcopy(state)
    if ast["body"] is not None:
        if analyze(ast["body"], local) is None:
            return None
    if ast["elif"] is not None:
        for item in ast["elif"]:
            if analyze_expression(item["content"]["condition"]["content"], state) is None:
                return None
            local = copy.deepcopy(state)
            if item["content"]["body"] is not None:
                if analyze(item["content"]["body"], local).is_error:
                    return None
    if ast["else"] is not None:
        local = copy.deepcopy(state)
        if ast["else"]["content"]["body"]: 
            if analyze(ast["else"]["content"]["body"], local).is_error:
                return None
    return state

def analyze_while(ast, state):
    if analyze_expression(ast["condition"]["content"], state) is None:
        return None
    local = copy.deepcopy(state)
    local.is_in_loop = True
    if ast["body"] is not None:
        if analyze(ast["body"], local).is_error:
            return None
    return state

def analyze_for(ast, state):
    if analyze([ast["setup"]], state).is_error:
        return None
    if analyze([ast["condition"]], state).is_error:
        return None
    if analyze([ast["increment"]], state).is_error:
        return None
    local = copy.deepcopy(state)
    local.is_in_loop = True
    if ast["body"] is not None:
        if analyze(ast["body"], local).is_error:
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
    state.has_return_value = True
    return res

def analyze_type_declaration(ast, state):
    if state.type_list.get(ast["id"].val) or state.function_list.get(ast["id"].val) or state.variable_list.get(ast["id"].val):
        throw_error("name '%s' is already exist" % ast["id"].val, ast["id"])
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
            throw_error("can't assign '%s' to '%s'" % (res.type, ast["type"].val), ast["size"])
            return None
    if state.variable_list.get(ast["id"].val) or state.function_list.get(ast["id"].val) or state.type_list.get(ast["id"].val):
        throw_error("name %s is already exist" % ast["id"].val, ast["size"])
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
        return None
    return state

def analyze_expression(ast, state):
    if ast["context"] == "unary_expression":
        return analyze_unary(ast["content"], state)
    elif ast["context"] == "infix_expression":
        return analyze_infix(ast["content"], state)
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
           left.type != right.type:
            throw_error("mismatched type", left.token)
            return None
        if left.is_array:
            throw_error("can't use array as operand", left.token)
            return None
        if right.is_array:
            throw_error("can't use array as operand", right.token)
            return None
    elif operator.tag == "ASSIGNMENT_OPERATOR":
        if left.is_array:
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
    if operator.val == "-" or\
       operator.val == "+":
        operand = analyze_expression(ast[1], state)
        if operand is None:
            return None
        if is_literal(operand) or\
           operand.type == "LIT" or\
           operand.is_in_memory:
            return operand
    elif operator.val == "@":
        operand = analyze_expression(ast[1], state)
        if operand is None:
            return None
        if operand.is_array or\
           operand.is_in_memory:
            operand.type = "INT" #@ is just an operator that lookup the memory address of a value, it'll return an int ofc
            operand.is_array = False
            return operand
    elif operator.val == "$":
        operand = analyze_expression(ast[2], state)
        if operand is None:
            return None
        if not operand.is_array:
            operand.type = "LIT"
            operand.is_in_memory = True
            operand.is_array = False
            return operand    
    throw_error("mismatched type for unary operator %s" % operator.val, operator)
    return None

def analyze_value(ast, state):
    if ast["context"] == "identifier":
        return analyze_identifier(ast, state)
    elif ast["context"] == "function_call":
        return analyze_function_call(ast, state)
    elif ast["context"] == "constant":
        if ast["value"].tag == "STRING":
            return item(ast["value"], ast["value"].tag, True, True)
        else:
            return item(ast["value"], ast["value"].tag, False, False)

def analyze_identifier(ast, state):
    if state.variable_list.get(ast["value"].val) is None and state.function_list.get(ast["value"].val) is None:
        throw_error("undeclared variable: %s" % ast["value"].val, ast["value"])
        return None
    if state.variable_list[ast["value"].val]["array-size"] is None or ast["array-value"] is not None:
        return item(ast["value"], state.variable_list[ast["value"].val]["type"], False, True)
    else:
        return item(ast["value"], state.variable_list[ast["value"].val]["type"], True, True)

def analyze_function_call(ast, state):
    res = state.function_list.get(ast["value"].val)
    if res is None:
        throw_error("undeclared function '%s'" % ast["value"].val, ast["value"])
        return None
    #check parameters 
    for arg in ast["parameters"]:
        expr = analyze_expression(arg["content"], state)
        if expr is None:
            return None
        if expr.is_array:
            throw_error("can't pass array to function", ast["value"])
            return None
    #check length
    if len(ast["parameters"]) != len(state.function_list[ast["value"].val]["parameters"]):
        throw_error("expected %i parameters but %i were given" % (len(state.function_list[ast["value"].val]["parameters"]), len(ast["parameters"])), ast["value"])
        return None
    return item(ast["value"], res["type"], False, False)

def is_literal(val):
    if val.type == "INT"   or\
       val.type == "FLOAT" or\
       val.type == "CHAR"  or\
       val.type == "BOOL"  or\
       val.type == "LIT":
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
