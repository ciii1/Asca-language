
class generator_state():
    def __init__(self):
        self.stack_position = 0;
        self.variable_list = {} #this one stores variables positions
        self.text_section = ""
        self.data_section = ""
        self.data_count = 0
        self.data

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

def generate_variable_declaration(ast, state):
    state.stack_position += size_to_number(ast["size"].val)
    state.variable_list[ast["id"].val] = {"size":ast["size"].val, "position":state.stack_position}
    if ast["init"] is not None:
        init = generate_expression(ast["init"], state)
        state.text_section += "mov " + ast["size"].val + " [rsp], " + init + "\n"
    else:
        state.text_section += "mov " + ast["size"].val + " [rsp], 0\n"

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
    else:
        #if left.is_constant:
        #    state.text_section += "mov rax, " + left.val "\n"
        #    st
        if ast[1].token == "+":
        elif ast[1].token == "-":
        elif ast[1].token == "*":
        elif ast[1].token == "/":

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
            generate_variable(ast, state)
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

def generate_variable(ast, state):
    pos = state.stack_position - size_to_number(state.variable_list[ast["value"].val]["size"])
    return item("[rsp-"+pos"]", "INT", False, True)

def to_int(token):
    if token.type == "CHAR":
        return ord(token.val)
    elif token.type == "INT":
        return int(token.val)
    elif token.type == "FLOAT":
        #TODO:ADD FLOAT SUPPORT
        return int(token.val)

def convert_64bit_reg(reg, size):
    reg_list = {
            "rax":{
                8:"rax",
                4:"eax",
                2:"ax",
                1:"al"
            },
            "rbx":{
                8:"rbx",
                4:"ebx",
                2:"bx",
                1:"bl"
            },
            "rcx":{
                8:"rcx",
                4:"ecx",
                2:"cx",
                1:"cl"
            },
            "rdx":{
                8:"rdx",
                4:"edx",
                2:"dx",
                1:"dl"
            },
            "rsi":{
                8:"rsi",
                4:"esi",
                2:"si",
                1:"sil"
            },
            "rdi":{
                8:"rdi",
                4:"edi",
                2:"di",
                1:"dil"
            },
            "rsp":{
                8:"rsp",
                4:"esp",
                2:"sp",
                1:"spl"
            },
             "rbp":{
                8:"rbp",
                4:"ebp",
                2:"bp",
                1:"bpl"
            },
            "r8":{
		    	8:"r8",
		    	4:"r8d",
		    	2:"r8w",
		    	1:"r8b"
		    },
		    "r9":{
		    	8:"r9",
		    	4:"r9d",
		    	2:"r9w",
		    	1:"r9b"
		    },
		    "r10":{
		    	8:"r10",
		    	4:"r10d",
		    	2:"r10w",
		    	1:"r10b"
		    },
		    "r11":{
		    	8:"r11",
		    	4:"r11d",
		    	2:"r11w",
		    	1:"r11b"
		    },
		    "r12":{
		    	8:"r12",
		    	4:"r12d",
		    	2:"r12w",
		    	1:"r12b"
		    },
		    "r13":{
		    	8:"r13",
		    	4:"r13d",
		    	2:"r13w",
		    	1:"r13b"
		    },
		    "r14":{
		    	8:"r14",
		    	4:"r14d",
		    	2:"r14w",
		    	1:"r14b"
		    },
		    "r15":{
		    	8:"r15",
		    	4:"r15d",
		    	2:"r15w",
		    	1:"r15b"
		    }
    }
    res = size_to_number(size)
    if res is not None:
        size = res
    return reg_list[reg][size]

def size_to_number(size):
    if size == "qword":
        return 8
    elif size == "dword":
        return 4
    elif size == "word":
        return 2
    elif size == "byte":
        return 1
