#only include registers that we can actually use (rbp, etc excluded)
REGISTERS_LIST = ["rax", "rbx", "rcx", "rsi", "rdi", "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"]

class generator_state():
    def __init__(self):
        self.stack_position = 0;
        self.variable_list = {} #this one stores variables positions
        self.text_section = ""
        self.data_section = ""
        self.data_count = 0

    def add_data(self, value, size="db"):
        self.data_section += "_DATA" + self.data_count + size + value
        self.data_count += 1
        return "_DATA" + self.data_count - 1

class item():
    def __init__(self, val, dtype, is_constant, in_memory):
        self.val = val
        self.type = dtype
        self.in_memory = in_memory
        self.is_constant = is_constant

def generate(ast):
    state = generator_state()
    for tree in ast:
        if tree["context"] == "expression":
            res = generate_expression(tree["content"], state) 
            if res.val not in REGISTERS_LIST:
                state.text_section += "mov rax, " + res.val + "\n"
    print(state.text_section)
    return state

def generate_expression(ast, state):
    if type(ast) is list:
            if len(ast) == 2:
                return generate_unary(ast, state)
            else:
                return generate_infix(ast, state)
    else:
        return generate_value(ast, state)
 
def generate_infix(ast, state):
    global REGISTERS_LIST #python should rlly has global constant

    left = generate_expression(ast[0], state)
    right = generate_expression(ast[2], state)

    #check if both variables are constant, if yes then do a constant fold
    if right.is_constant and left.is_constant:
        if ast[1].val == "+":
            return item(str(to_int(left) + to_int(right)), "INT", True, False)
        elif ast[1].val == "-":
            return item(str(to_int(left) - to_int(right)), "INT", True, False)
        elif ast[1].val == "*":
            return item(str(to_int(left) * to_int(right)), "INT", True, False)
        elif ast[1].val == "/":
            return item(str(to_int(left) / to_int(right)), "INT", True, False)
        return item
    #else:
    #    if ast[1].token == "+":
    #    elif ast[1].token == "-":
    #    elif ast[1].token == "*":
    #    elif ast[1].token == "/":

def generate_unary(ast, state):
    operand = generate_expression(ast[1], state)
    if ast[0] == "-" or ast[0] == "+":
        if operand != "rax":
            state.text_section += "mov rax, " + operand.token + "\n"
        state.text_section += "neg rax, " + operand.token + "\n"
        return "rax"
    elif ast[0] == "$":
        return "["+operand.token+"]"
    elif ast[0] == "@":
        return operand.token

def generate_value(ast, state):
    if type(ast) is dict:
        if ast["type"] == "identifier":
            #NOT IMPLEMENTED
            pass
        elif ast["type"] == "function_call":
            #NOT IMPLEMENTED
            pass
    else:
        if ast.tag == "STRING":
            ast.val = state.add_data(ast.val, "db")
            return item(ast.val, ast.tag, False, True)
        else:
            return item(ast.val, ast.tag, True, False)

def to_int(token):
    if token.type == "CHAR":
        return ord(token.val)
    elif token.type == "INT":
        return int(token.val)
    elif token.type == "FLOAT":
        #TODO:ADD FLOAT SUPPORT
        return int(token.val)
