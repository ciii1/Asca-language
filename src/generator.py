
class generator_state():
    def __init__(self):
        self.stack_position = 0;
        self.variable_list = {} #this one stores variables positions
        self.text_section = ""
        self.data_section = ""
        self.data_count = 0

    def add_data(self, value, size="db"):
        self.data_section += "_DATA" + self.data_count + " " + size + " " +  value
        self.data_count += 1
        return "_DATA" + self.data_count - 1 + "\n"

class item():
    def __init__(self, val, dtype, size, is_constant, in_memory):
        self.val = val
        self.type = dtype
        self.size = size
        self.in_memory = in_memory
        self.is_constant = is_constant

def generate(ast):
    state = generator_state()
    for tree in ast:
        if tree["context"] == "expression":
            generate_expression(tree["content"], state) 
        elif tree["context"] == "variable_declaration":
            generate_variable_declaration(tree["content"], state)
    output = ""
    if state.data_section != None:
        output += "section .data\n\n"
        output += state.data_section
    output += "section .text\n"
    output += "\tglobal _start\n"
    output += "_start:\n"
    output += state.text_section
    return output

def generate_variable_declaration(ast, state):
    state.stack_position += size_to_number(ast["size"].val)
    state.variable_list[ast["id"].val] = {"size":ast["size"].val, "position":state.stack_position}
    state.text_section += "sub rsp, " + str(size_to_number(ast["size"].val)) + "\n"
    if ast["init"] is not None:
        init = generate_expression(ast["init"]["content"], state)
        state.text_section += "mov " + ast["size"].val + " [rsp], " + init.val + "\n"
    else:
        state.text_section += "mov " + ast["size"].val + " [rsp], 0\n"

def generate_expression(ast, state, res_register="rax", is_parsing_left=True):
    if ast["context"] == "unary_expression":
        return generate_unary(ast["content"], state)
    elif ast["context"] == "infix_expression":
        return generate_infix(ast["content"], state, res_register, is_parsing_left)
    else:
        return generate_value(ast, state)
 
def generate_infix(ast, state, res_register, is_parsing_left): 
    if is_parsing_left:
        left = generate_expression(ast[0], state, "r8", True)
        right = generate_expression(ast[2], state, "r9", False)
    else:
        left = generate_expression(ast[0], state, "r10", True)
        right = generate_expression(ast[2], state, "r9", False)
    #check if both variables are constant, if yes then do a constant fold
    if right.is_constant and left.is_constant:
        if ast[1].val == "+":
            return item(str(to_int(left) + to_int(right)), "INT", "qword", True, False)
        elif ast[1].val == "-":
            return item(str(to_int(left) - to_int(right)), "INT", "qword", True, False)
        elif ast[1].val == "*":
            return item(str(to_int(left) * to_int(right)), "INT", "qword", True, False)
        elif ast[1].val == "/":
            return item(str(to_int(left) / to_int(right)), "INT", "qword", True, False)
        return item
    else:
        if left.is_constant or left.in_memory:
            if right.val == "rax":
                state.text_section += "mov rbx, rax \n"
                right.val = "rbx"
            state.text_section += "mov " + convert_64bit_reg("rax", left.size) + ", " + left.val +"\n"
            left.val = "rax"
        if ast[1].val == "+":
            state.text_section += "add qword " + left.val + ", " + right.val + "\n"
            if left.val != res_register:
                state.text_section += "mov " + res_register + ", " + left.val + "\n"
                left.val = res_register
            return item(res_register, "INT", "qword", False, False)
        elif ast[1].val == "-":
            state.text_section += "sub qword " + left.val + ", " + right.val + "\n"
            if left.val != res_register:
                state.text_section += "mov " + res_register + ", " + left.val + "\n"
                left.val = res_register
            return item(res_register, "INT", "qword", False, False)
        elif ast[1].val == "*":
            if left.val != "rax":
                if right.val == "rax":
                    state.text_section += "mov r10, rax \n"
                    right.val = "r10"
                state.text_section += "mov rax, " + left.val + "\n"
                left.val = "rax"
            if right.is_constant:
                state.text_section += "mov rbx, " + right.val + "\n"
                right.val = "rbx"
            state.text_section += "mul " + right.size + " " + right.val + "\n"
            if left.val != res_register: 
                state.text_section += "mov " + res_register + ", " + left.val + "\n"
                left.val = res_register
            return item(res_register, "INT", "qword", False, False)
        elif ast[1].val == "/":
            if left.val != "rax":
                if right.val == "rax":
                    state.text_section += "mov r10, rax \n"
                    right.val = "r10"
                state.text_section += "mov rax, " + left.val + "\n"
                left.val = "rax"
            if right.is_constant:
                state.text_section += "mov rbx, " + right.val + "\n"
                right.val = "rbx"
            state.text_section += "mov rdx, 0\n"
            state.text_section += "div " + right.size + " " + right.val + "\n"
            if left.val != res_register:
                state.text_section += "mov " + res_register + ", " + left.val + "\n"
                left.val = res_register
            return item(res_register, "INT", "qword", False, False)

def generate_unary(ast, state):
    if ast[0].val == "-" or ast[0].val == "+":
        operand = generate_expression(ast[1], state)
        if operand.is_constant or operand.in_memory:
            state.text_section += "mov r13, " + operand.val + "\n"
            operand.val = "r13"
        state.text_section += "neg " + operand.val + "\n"
        return item(operand.val, "INT", "qword", False, False)
    elif ast[0].val == "$":
        operand = generate_expression(ast[2], state)
        if operand.is_constant or operand.in_memory:
            state.text_section += "mov r13, " + operand.val + "\n"
            operand.val = "r13"
        return item("["+operand.val+"]", "INT", ast[1].val, False, True)
    elif ast[0].val == "@":
        operand = generate_expression(ast[1], state)
        if operand.in_memory:
            state.text_section += "lea r13, " + operand.val + "\n"
            operand.val = "r13"           
        return item(operand.val, "INT", "qword", True, False) 

def generate_value(ast, state):
    if ast["context"] == "identifier":
        return generate_variable(ast, state)
    elif ast["context"] == "function_call":
        #NOT IMPLEMENTED
        pass
    elif ast["context"] == "constant":
        if ast["value"].tag == "STRING":
            ast["value"].val = state.add_data(ast["value"].val, "db")
            return item(ast["value"].val, ast["value"].tag, "byte", False, True)
        else:
            return item(ast["value"].val, ast["value"].tag, "qword", True, False)

def generate_variable(ast, state):
    pos = state.stack_position - state.variable_list[ast["value"].val]["position"]
    return item("[rsp+"+str(pos)+"]", "INT", state.variable_list[ast["value"].val]["size"], False, True)

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
