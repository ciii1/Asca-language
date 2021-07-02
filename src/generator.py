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

def generate(ast):
    state = generator_state()
    for tree in ast:
        if tree["context"] == "expression":
            generate_expression(tree["content"], state)

    print(state.text_section)
    return state

def generate_expression(ast, state, is_rax_used = False):
    if type(ast) is list:
            if len(ast) == 2:
                return generate_unary(ast, state)
            else:
                return generate_infix(ast, state, is_rax_used)
    else:
        return generate_value(ast, state)
 
def generate_infix(ast, state, is_rax_used = False):
    left = generate_expression(ast[0], state)
    if type(ast[0]) is list:
        right = generate_expression(ast[2], state, True)
    else:
        right = generate_expression(ast[2], state, False)
    if ast[1].val == "+": 
        if right == "rax":
            state.text_section += "mov rbx, " + left + "\n"
            state.text_section += "add rax, rbx \n"
            return "rax"
        else:
            if left != "rax":
                if is_rax_used:
                    state.text_section += "mov r15, rax \n"
                state.text_section += "mov rax, " + left + "\n"
            state.text_section += "add rax, " + right + "\n"
            return "rax"
    elif ast[1].val == "*":
        if right == "rax":
                state.text_section += "mov rbx, rax \n"
                right = "rbx"
        if left != "rax":
            if is_rax_used:
                state.text_section += "mov r15, rax \n" 
            state.text_section += "mov rax, " + left + "\n"
        state.text_section += "mul " + right + "\n"
        if is_rax_used:
            state.text_section += "mov rbx, rax \n"
            state.text_section += "mov rax, r15 \n"
            return "rbx"
        return "rax"
    elif ast[1].val == "/":
        if right == "rax":
                state.text_section += "mov rbx, rax \n"
                right = "rbx"
        if left != "rax":
            if is_rax_used:
                state.text_section += "mov r15, rax \n"
            state.text_section += "mov rax, " + left + "\n"
        state.text_section += "div " + right + "\n"
        if is_rax_used:
            state.text_section += "mov rbx, rax \n"
            state.text_section += "mov rax, r15 \n"
            return "rbx"
        return "rax"
    elif ast[1].val == "-":
        if right == "rax":
            state.text_section += "mov rbx, " + left + "\n"
            state.text_section += "sub rbx, rax \n"
            return "rbx"
        else:
            if left != "rax":
                if is_rax_used:
                    state.text_section += "mov r15, rax \n"
                state.text_section += "mov rax, " + left + "\n"
            state.text_section += "sub rax, " + right + "\n"
            return "rax"

def generate_unary(ast, state):
    operand = generate_expression(ast[1], state)
    if ast[0] == "-" or ast[0] == "+":
        if operand != "rax":
            state.text_section += "mov rax, " + operand.val + "\n"
        state.text_section += "neg rax, " + operand.val + "\n"
        return "rax"
    elif ast[0] == "$":
        return "["+operand.val+"]"
    elif ast[0] == "@":
        return operand.val

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
            return state.add_data(ast.val, "db")
        else:
            return ast.val

