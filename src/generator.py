import copy

class generator_state():
    def __init__(self, function_list):
        self.stack_position = 0;
        self.base_stack_position = 0; #stores the stack position before we're entering a function
        self.variable_list = {} #this one stores variable positions
        self.text_section = ""
        self.data_section = ""
        self.subroutine_section = ""
        self.data_count = 0
        self.label_count = 0
        self.function_list = function_list
        self.continue_label = ""
        self.break_label = ""
    def add_data(self, value, size="db"):
        self.data_count += 1
        self.data_section += "_DATA" + str(self.data_count) + " " + size + " " + value + "\n"
        return "_DATA" + str(self.data_count)

class item():
    def __init__(self, val, dtype, size, is_constant, in_memory, is_writeable=True):
        self.val = val
        self.type = dtype
        self.size = size
        self.in_memory = in_memory
        self.is_constant = is_constant
        self.is_writeable = is_writeable

def generate(ast, function_list = None, state = None):
    if state is None:
        state = generator_state(function_list)
    for tree in ast:
        if tree["context"] == "expression":
            generate_expression(tree["content"], state) 
        elif tree["context"] == "variable_declaration":
            generate_variable_declaration(tree["content"], state)
        elif tree["context"] == "function_declaration":
            generate_function_declaration(tree["content"], state)
        elif tree["context"] == "if":
            generate_if(tree["content"], state)
        elif tree["context"] == "while":
            generate_while(tree["content"], state)
        elif tree["context"] == "return":
            generate_return(tree["content"], state)
        elif tree["context"] == "break":
            generate_break(tree, state)
        elif tree["context"] == "continue":
            generate_continue(tree, state)
    output = ""
    if len(state.data_section) > 0:
        output += "section .data\n"
        output += state.data_section
        output += "\n"
    output += "section .text\n"
    output += "\tglobal _start\n"
    output += state.subroutine_section
    output += "_start:\n"
    output += state.text_section
    return output

def generate_variable_declaration(ast, state):
    size = size_to_number(ast["size"].val)
    if ast["array-size"] is not None:
        size *= int(ast["array-size"].val)
    state.stack_position += size
    state.variable_list[ast["id"].val] = {"size":ast["size"].val, "position":state.stack_position}
    state.text_section += "sub rsp, " + str(size) + "\n"
    if ast["init"] is not None:
        init = generate_expression(ast["init"]["content"], state)
        if ast["init-sign"].val == ":=":
            if init.in_memory:
                if init.is_writeable: #if it's a variable
                    if init.size == "qword":
                        state.text_section += "movsd xmm0, " + init.val + "\n"
                        init.val = "xmm0"
                    elif init.size == "dword":
                        state.text_section += "movss xmm0, " + init.val + "\n"
                        init.val = "xmm0"
                    else:
                        state.text_section += "mov " + convert_64bit_reg("rax", init.size) + ", " + init.val + "\n"
                        state.text_section += "movq xmm0, rax"
                        init.val = "xmm0"
                else:
                    state.text_section += "movsd xmm0, " + init.val + "\n"
                    init.val = "xmm0"
            if ast["size"].val == "qword":
                state.text_section += "movsd qword [rsp], xmm0 \n"
            elif ast["size"].val == "dword":
                state.text_section += "movss dword [rsp], xmm0 \n"
            else:
                state.text_section += "movq rax, xmm0 \n"
                state.text_section += "mov " + ast["size"].val + " [rsp], " + convert_64bit_reg("rax", ast["size"].val) + "\n"
        else:
            if init.in_memory:
                state.text_section += "mov " + convert_64bit_reg("rax", init.size) + ", " + init.val + "\n"
                init.val = "rax"
            if init.size != "qword":
                state.text_section += "movsx rax, " + convert_64bit_reg(init.val, init.size) + "\n"
                init.size = "qword"
            state.text_section += "mov " + ast["size"].val + " [rsp], " + convert_64bit_reg(init.val, ast["size"].val) + "\n"

def generate_function_declaration(ast, state):
    state.subroutine_section += "_" + ast["id"].val + ":\n"
    local = copy.deepcopy(state)
    local.variable_list = {}
    i = 8
    for item in ast["parameters"]:
        #add the parameter to the variable list with the value from the stack
        local.variable_list[item["content"]["id"].val] = {"size":item["content"]["size"].val, "position":-i}
        i += size_to_number(item["content"]["size"].val)
    #generate body#
    local.stack_position = 0
    local.base_stack_position = local.stack_position
    local.text_section = ""
    generate(ast["body"], state=local)
    state.subroutine_section += local.text_section
    state.label_count = local.label_count

def generate_return(ast, state):
    init = generate_expression(ast["value"]["content"], state, "rax") 
    if init.is_constant or init.in_memory:
        state.text_section += "mov " + convert_64bit_reg("rax", init.size) + ", " + init.val +"\n"
        init.val = "rax"
    if init.size != "qword":
        state.text_section += "movsx rax, " + convert_64bit_reg("rax", init.size) + "\n"
    if state.stack_position - state.base_stack_position != 0:
        state.text_section += "add rsp, " + str(state.stack_position - state.base_stack_position) + "\n"
    state.text_section += "ret \n"

def generate_expression(ast, state, res_register="rax", is_parsing_left=True):
    if ast["context"] == "unary_expression":
        return generate_unary(ast["content"], state)
    elif ast["context"] == "infix_expression":
        return generate_infix(ast["content"], state, res_register, is_parsing_left)
    else:
        return generate_value(ast, state)
 
def generate_infix(ast, state, res_register, is_parsing_left): 
    if is_parsing_left:
        if ast[1].tag == "PRECISE_RELATIONAL_OPERATOR" or\
           ast[1].tag == "PRECISE_ASSIGNMENT_OPERATOR" or\
           ast[1].tag == "PRECISE_ARITHMETICAL_OPERATOR" or\
           ast[1].tag == "PRECISE_CONDITIONAL_OPERATOR":
            left = generate_expression(ast[0], state, "xmm2", True)
            right = generate_expression(ast[2], state, "xmm3", True)
        else:
            left = generate_expression(ast[0], state, "r8", True)
            right = generate_expression(ast[2], state, "r9", False)
    else:
        if ast[1].tag == "PRECISE_RELATIONAL_OPERATOR" or\
           ast[1].tag == "PRECISE_ASSIGNMENT_OPERATOR" or\
           ast[1].tag == "PRECISE_ARITHMETICAL_OPERATOR" or\
           ast[1].tag == "PRECISE_CONDITIONAL_OPERATOR":
            left = generate_expression(ast[0], state, "xmm4", True)
            right = generate_expression(ast[2], state, "xmm3", True)
        else:
            left = generate_expression(ast[0], state, "r11", True)
            right = generate_expression(ast[2], state, "r9", False)
    #check if both variables are constant, if yes then do a constant fold
    if right.is_constant and left.is_constant:
        if left.type == "FLOAT":
            left_val = float(left.val)
        else:
            left_val = int(left.val)
        if right.type == "FLOAT":
            right_val = float(right.val)
        else:
            right_val = int(right.val)
        if ast[1].val == "+":
            return item(str(left_val + right_val), left.type, "qword", True, False)
        elif ast[1].val == "-":
            return item(str(left_val - right_val), left.type, "qword", True, False)
        elif ast[1].val == "*":
            return item(str(left_val * right_val), left.type, "qword", True, False)
        elif ast[1].val == "/":
            return item(str(left_val / right_val), left.type, "qword", True, False)
        elif ast[1].val == ">":
            return item(str(int(left_val > right_val)), left.type, "qword", True, False)
        elif ast[1].val == "<":
            return item(str(int(left_val < right_val)), left.type, "qword", True, False)
        elif ast[1].val == ">=":
            return item(str(int(left_val >= right_val)), left.type, "qword", True, False)
        elif ast[1].val == "<=":
            return item(str(int(left_val <= right_val)), left.type, "qword", True, False)
        elif ast[1].val == "==":
            return item(str(int(left_val == right_val)), left.type, "qword", True, False)
        elif ast[1].val == "!=":
            return item(str(int(left_val != right_val)), left.type, "qword", True, False)
        elif ast[1].val == "||":
            return item(str(left_val or right_val), left.type, "qword", True, False)
        elif ast[1].val == "&&":
            return item(str(left_val and right_val), left.type, "qword", True, False)
        elif ast[1].val == ":+":
            return item(str(left_val + right_val), left.type, "qword", True, False)
        elif ast[1].val == ":-":
            return item(str(left_val - right_val), left.type, "qword", True, False)
        elif ast[1].val == ":*":
            return item(str(left_val * right_val), left.type, "qword", True, False)
        elif ast[1].val == ":/":
            return item(str(left_val / right_val), left.type, "qword", True, False)
        elif ast[1].val == ":>":
            return item(str(int(left_val > right_val)), left.type, "qword", True, False)
        elif ast[1].val == ":<":
            return item(str(int(left_val < right_val)), left.type, "qword", True, False)
        elif ast[1].val == ":>=":
            return item(str(int(left_val >= right_val)), left.type, "qword", True, False)
        elif ast[1].val == ":<=":
            return item(str(int(left_val <= right_val)), left.type, "qword", True, False)
        elif ast[1].val == ":==":
            return item(str(int(left_val == right_val)), left.type, "qword", True, False)
        elif ast[1].val == ":!=":
            return item(str(int(left_val != right_val)), left.type, "qword", True, False)
        elif ast[1].val == ":||":
            return item(str(left_val or right_val), left.type, "qword", True, False)
        elif ast[1].val == ":&&":
            return item(str(left_val and right_val), left.type, "qword", True, False)
    else:
        if ast[1].tag == "PRECISE_RELATIONAL_OPERATOR" or\
           ast[1].tag == "PRECISE_ASSIGNMENT_OPERATOR" or\
           ast[1].tag == "PRECISE_ARITHMETICAL_OPERATOR" or\
           ast[1].tag == "PRECISE_CONDITIONAL_OPERATOR":
            if ast[1].tag != "PRECISE_ASSIGNMENT_OPERATOR" and left.in_memory:
                if right.val == "xmm0":
                    state.text_section += "movssdd xmm1, xmm0\n"
                    right.val = "xmm1"
                if left.size == "qword":
                    state.text_section += "movsd xmm0, qword " + left.val + "\n"
                elif left.size == "dword":
                    state.text_section += "movss xmm0, dword " + left.val + "\n"
                else:
                    state.text_section += "mov rbx, " + left.val +"\n"
                    state.text_section += "movq xmm0, rbx\n"
                left.val = "xmm0"
                left.size = "qword"
            if right.size != "qword" and right.size != "dword":
                state.text_section += "mov rbx, " + right.val + "\n"
                state.text_section += "movq xmm1, rbx \n"
                right.val = "xmm1"
                right.size = "qword"
                right.in_memory = False
            if ast[1].val == ":+":
                if right.size == "qword":
                    state.text_section += "addsd " + left.val + ", qword " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "addss " + left.val + ", dword " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":-":
                if right.size == "qword":
                    state.text_section += "subsd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "subss " + left.val + ", " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":*":
                if right.size == "qword":
                    state.text_section += "mulsd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "mulss " + left.val + ", " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":/":
                if right.size == "qword":
                    state.text_section += "divsd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "divss " + left.val + ", " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":<":
                if right.size == "qword":
                    state.text_section += "ucomisd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "ucomiss " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                left.val = "rax"
                left.type = "INT"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovl " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":<=":
                if right.size == "qword":
                    state.text_section += "ucomisd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "ucomiss " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                left.val = "rax"
                left.type = "INT"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovle " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":>":
                if right.size == "qword":
                    state.text_section += "ucomisd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "ucomiss " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                left.val = "rax"
                left.type = "INT"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovg " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":>=":
                if right.size == "qword":
                    state.text_section += "ucomisd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "ucomiss " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                left.val = "rax"
                left.type = "INT"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovge " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":==":
                if right.size == "qword":
                    state.text_section += "ucomisd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "ucomiss " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                left.val = "rax"
                left.type = "INT"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmove " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":!=":
                if right.size == "qword":
                    state.text_section += "ucomisd " + left.val + ", " + right.val + "\n"
                elif right.size == "dword":
                    state.text_section += "ucomiss " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                left.val = "rax"
                left.type = "INT"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovne " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":||":
                if right.in_memory:
                    state.text_section += "mov " + convert_64bit_reg("rbx", right.val) + ", " + right.val + "\n"
                    state.text_section += "movq xmm1, rbx\n"
                    right.val = "xmm1"
                state.text_section += "por " + left.val + ", " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":&&":
                if right.in_memory:
                    state.text_section += "mov " + convert_64bit_reg("rbx", right.val) + ", " + right.val + "\n"
                    state.text_section += "movq xmm1, rbx\n"
                    right.val = "xmm1"
                state.text_section += "pand " + left.val + ", " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "movq " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ":=":
                if right.in_memory:
                    if right.size == "qword":
                        state.text_section += "movsd xmm1, qword " + right.val + "\n"
                    elif right.size == "dword":
                        state.text_section += "movss xmm1, dword " + right.val + "\n"
                    else:
                        state.text_section += "mov " + convert_64bit_reg("rax", right.size) + ", " + right.size + " " + right.val +"\n"
                        state.text_section += "movq xmm1, rax\n"
                    right.val = "xmm1"
                if left.size == "qword":
                    state.text_section += "movsd qword " + left.val + ", " + right.val + "\n"
                elif left.size == "dword":
                    state.text_section += "movss dword " + left.val + ", " + right.val + "\n"
                else:
                    state.text_section += "movq rbx, " + right.val + "\n"
                    state.text_section += "mov " + left.size + " " + left.val + ", " + convert_64bit_reg("rbx", left.size) + "\n"
                return item(left.val, left.type, left.size, False, True) 
                if right.in_memory:
                    state.text_section += "mov " + convert_64bit_reg("rbx", size_to_number(right.size)) + ", " + right.val + "\n"
                    right.val = "rbx"
                if left.size == "qword" and right.size != "qword":
                    state.text_section += "movsx " + right.val + ", " + convert_64bit_reg(right.val, right.size) + "\n"
                    right.size = "qword"
                state.text_section += "sub " + left.size + " " + left.val + ", " + convert_64bit_reg(right.val, left.size) + "\n"
                return item(left.val, left.type, left.size, False, True)
        else:
            if ast[1].tag != "ASSIGNMENT_OPERATOR" and (left.is_constant or left.in_memory):
                if right.val == "rax":
                    state.text_section += "mov rbx, rax \n"
                    right.val = "rbx"
                state.text_section += "mov " + convert_64bit_reg("rax", left.size) + ", " + left.val +"\n"
                left.val = "rax"
            if ast[1].val == "+":
                if right.in_memory:
                    state.text_section += "add " + right.size + " " + convert_64bit_reg(left.val, right.size) + ", " + right.val + "\n"
                else:
                    state.text_section += "add " + left.val + ", " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "-":
                if right.in_memory:
                    state.text_section += "sub " + right.size + " " + convert_64bit_reg(left.val, right.size) + ", " + right.val + "\n"
                else:
                    state.text_section += "sub " + left.val + ", " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "*":
                if left.val != "rax":
                    if right.val == "rax":
                        state.text_section += "mov r10, rax \n"
                        right.val = "r10"
                    state.text_section += "mov " + convert_64bit_reg("rax", left.size) +", " + convert_64bit_reg(left.val, left.size) + "\n"
                    left.val = "rax"
                if right.is_constant:
                    state.text_section += "mov " + convert_64bit_reg("rbx", right.size) + ", " + right.val + "\n"
                    right.val = "rbx"
                if not right.is_constant and not right.in_memory:
                    right.val = convert_64bit_reg(right.val, right.size)
                state.text_section += "mul " + right.size + " " + right.val + "\n"
                if left.val != res_register: 
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "/":
                if left.val != "rax":
                    if right.val == "rax":
                        state.text_section += "mov r10, rax \n"
                        right.val = "r10"
                    state.text_section += "mov " + convert_64bit_reg("rax", left.size) +", " + convert_64bit_reg(left.val, left.size) + "\n"
                    left.val = "rax"
                if right.is_constant:
                    state.text_section += "mov " + convert_64bit_reg("rbx", right.size) + ", " + right.val + "\n"
                    right.val = "rbx"
                state.text_section += "mov rdx, 0\n"
                if not right.is_constant and not right.in_memory:
                    right.val = convert_64bit_reg(right.val, right.size)
                state.text_section += "div " + right.size + " " + right.val + "\n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "<":
                if right.in_memory:
                    state.text_section += "cmp " + convert_64bit_reg(left.val, right.size) + ", " + right.val + "\n"
                else:
                    state.text_section += "cmp " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovl " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "<=":
                if right.in_memory:
                    state.text_section += "cmp " + convert_64bit_reg(left.val, right.size) + ", " + right.val + "\n"
                else:
                    state.text_section += "cmp " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovle " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ">":
                if right.in_memory:
                    state.text_section += "cmp " + convert_64bit_reg(left.val, right.size) + ", " + right.val + "\n"
                else:
                    state.text_section += "cmp " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovg " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == ">=":
                if right.in_memory:
                    state.text_section += "cmp " + convert_64bit_reg(left.val, right.size) + ", " + right.val + "\n"
                else:
                    state.text_section += "cmp " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovge " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "==":
                if right.in_memory:
                    state.text_section += "cmp " + convert_64bit_reg(left.val, right.size) + ", " + right.val + "\n"
                else:
                    state.text_section += "cmp " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmove " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "!=":
                if right.in_memory:
                    state.text_section += "cmp " + convert_64bit_reg(left.val, right.size) + ", " + right.val + "\n"
                else:
                    state.text_section += "cmp " + left.val + ", " + right.val + "\n"
                state.text_section += "mov rbx, 1\n"
                state.text_section += "mov " + left.val  + ", 0\n"
                state.text_section += "cmovne " + left.val + ", rbx \n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "||":
                if right.is_constant:
                    state.text_section += "mov rbx, " + right.val + "\n"
                    right.val = "rbx"
                state.text_section += "cmp " + right.val + ", 0\n"
                state.text_section += "cmovne " + left.val + ", " + right.val + " \n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "&&":
                if right.is_constant:
                    state.text_section += "mov rbx, " + right.val + "\n"
                    right.val = "rbx"
                state.text_section += "cmp " + right.val + ", 0\n"
                state.text_section += "cmove " + left.val + ", " + right.val + " \n"
                if left.val != res_register:
                    state.text_section += "mov " + res_register + ", " + left.val + "\n"
                    left.val = res_register
                return item(res_register, left.type, left.size, False, False)
            elif ast[1].val == "=":
                if right.in_memory:
                    state.text_section += "mov " + convert_64bit_reg("rbx", size_to_number(right.size)) + ", " + right.val + "\n"
                    right.val = "rbx"
                if left.size == "qword" and right.size != "qword":
                    state.text_section += "movsx " + right.val + ", " + convert_64bit_reg(right.val, right.size) + "\n"
                    right.size = "qword"
                state.text_section += "mov " + left.size + " " + left.val + ", " + convert_64bit_reg(right.val, left.size) + "\n"
                return item(left.val, left.type, left.size, False, True) 
            elif ast[1].val == "+=":
                if right.in_memory:
                    state.text_section += "mov " + convert_64bit_reg("rbx", size_to_number(right.size)) + ", " + right.val + "\n"
                    right.val = "rbx"
                if left.size == "qword" and right.size != "qword":
                    state.text_section += "movsx " + right.val + ", " + convert_64bit_reg(right.val, right.size) + "\n"
                    right.size = "qword"
                state.text_section += "add " + left.size + " " + left.val + ", " + convert_64bit_reg(right.val, left.size) + "\n"
                return item(left.val, left.type, left.size, False, True) 
            elif ast[1].val == "-=":
                if right.in_memory:
                    state.text_section += "mov " + convert_64bit_reg("rbx", size_to_number(right.size)) + ", " + right.val + "\n"
                    right.val = "rbx"
                if left.size == "qword" and right.size != "qword":
                    state.text_section += "movsx " + right.val + ", " + convert_64bit_reg(right.val, right.size) + "\n"
                    right.size = "qword"
                state.text_section += "sub " + left.size + " " + left.val + ", " + convert_64bit_reg(right.val, left.size) + "\n"
                return item(left.val, left.type, left.size, False, True)

def generate_unary(ast, state):
    if ast[0].val == "-" or ast[0].val == "+":
        operand = generate_expression(ast[1], state)
        if operand.is_constant or operand.in_memory:
            state.text_section += "mov r13, " + operand.val + "\n"
            operand.val = "r13"
        state.text_section += "neg " + operand.val + "\n"
        return item(operand.val, operand.type, "qword", False, False)
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
    elif ast[0].val == "!":
        operand = generate_expression(ast[1], state)
        if operand.is_constant or operand.in_memory:
            state.text_section += "mov r13, " + operand.val + "\n"
            operand.val = "r13"
        state.text_section += "cmp " + operand.val + ", 0\n"
        state.text_section += "mov " + operand.val + ", 0\n"
        state.text_section += "mov rbx, 1\n"
        state.text_section += "cmove " + operand.val + ", rbx\n"
        return item(operand.val, "INT", "qword", False, False)

def generate_value(ast, state):
    if ast["context"] == "identifier":
        return generate_variable(ast, state)
    elif ast["context"] == "function_call":
        return generate_function_call(ast, state)
    elif ast["context"] == "constant":
        if ast["value"].tag == "STRING":
            val = state.add_data(ast["value"].val + ", 0", "db")
            return item("[" + val + "]", ast["value"].tag, "byte", False, True, False)
        elif ast["value"].tag == "FLOAT":
            val = state.add_data(ast["value"].val, "dq")
            return item("[" + val + "]", ast["value"].tag, "qword", False, True, False)
        else:
            return to_int(item(ast["value"].val, ast["value"].tag, "qword", True, False))

def generate_variable(ast, state):
    pos = state.stack_position - state.variable_list[ast["value"].val]["position"]
    if ast["array-value"] is not None:
        array_val = generate_expression(ast["array-value"]["content"], state)
        if array_val.is_constant:
            pos += int(array_val.val) * size_to_number(state.variable_list[ast["value"].val]["size"])
        else:
            if array_val.in_memory:
                state.text_section += "mov " + convert_64bit_reg("rbx", array_val.size) + ", " + array_val.val + "\n"
                array_val.val = "rbx"
            pos = array_val.val + " * " + str(size_to_number(state.variable_list[ast["value"].val]["size"])) + " + " + str(pos)
    return item("[rsp + " + str(pos) + "]", "INT", state.variable_list[ast["value"].val]["size"], False, True)

def generate_function_call(ast, state):
    i = len(ast["parameters"])-1
    total_argument_size = 0
    while i >= 0:
        arg_size = state.function_list[ast["value"].val]["parameters"][i]["size"]
        total_argument_size += size_to_number(arg_size)
        state.text_section += "sub rsp, " + str(size_to_number(arg_size)) + "\n"
        state.stack_position += size_to_number(arg_size)
        param = generate_expression(ast["parameters"][i]["content"], state)
        if param.in_memory:
            state.text_section += "mov " + convert_64bit_reg("rbx", param.size) + ", " + param.val + "\n"
            param.val = "rbx"
        if param.is_constant:
            state.text_section += "mov " + arg_size + " [rsp], " + param.val + "\n"
        else:
            if param.size != "qword":
                state.text_section += "movsx " + param.val + ", " + convert_64bit_reg(param.val, param.size) + "\n"
            state.text_section += "mov " + arg_size + " [rsp], " + convert_64bit_reg(param.val, arg_size) + "\n"
        i-=1
    state.text_section += "call _" + ast["value"].val + "\n"
    if len(ast["parameters"]) != 0:
        state.text_section += "add rsp, " + str(total_argument_size) + "\n"
    return item("rax", "INT", "qword", False, False)

def generate_if(ast, state):
    end_label = "_END" + str(state.label_count) #label for jump after if or elif condition (called the end label here)
    #generate if condition
    condition = generate_expression(ast["condition"]["content"], state)
    if condition.is_constant:
        state.text_section += "mov rax, " + condition.val + "\n" 
        condition.val = "rax"
    state.text_section += "cmp " + condition.val + ", 0\n"
    state.text_section += "jne _IF" + str(state.label_count) + "\n"
    if_label = "_IF" + str(state.label_count)
    state.label_count += 1 
    elif_body = []
    #generate elif conditions
    for item in ast["elif"]:
        item = item["content"]
        condition = generate_expression(item["condition"]["content"], state)
        if condition.is_constant:
            state.text_section += "mov rax, " + condition.val + "\n" 
            condition.val = "rax"
        state.text_section += "cmp " + condition.val + ", 0\n"
        state.text_section += "jne _ELIF" + str(state.label_count) + "\n"
        elif_body.append(["_ELIF" + str(state.label_count) , item["body"]])
        state.label_count += 1
    #generate else body
    #if if and elif conditions were not fulfilled then it'll go here, wich is the else body 
    if ast["else"]:
        local = copy.deepcopy(state)
        local.text_section = ""
        base_stack_position = local.stack_position
        generate(ast["else"]["content"]["body"], state=local)
        state.text_section += local.text_section
        state.label_count += local.label_count
        if local.stack_position - base_stack_position != 0:
            state.text_section += "add rsp, " + str(local.stack_position - base_stack_position) + "\n"
    state.text_section += "jmp " + end_label + "\n"
    #generate if body
    state.text_section += if_label + ":\n"
    local = copy.deepcopy(state)
    local.text_section = ""
    base_stack_position = local.stack_position
    generate(ast["body"], state=local)
    state.text_section += local.text_section
    state.label_count += local.label_count
    if local.stack_position - base_stack_position != 0:
        state.text_section += "add rsp, " + str(local.stack_position - base_stack_position) + "\n"
    state.text_section += "jmp " + end_label + "\n"
    #generate elif bodies
    for label, body in elif_body:
        state.text_section += label + ":\n"
        local = copy.deepcopy(state)
        local.text_section = ""
        base_stack_position = local.stack_position
        generate(body, state=local)
        state.text_section += local.text_section
        state.label_count += local.label_count
        if local.stack_position - base_stack_position != 0:
            state.text_section += "add rsp, " + str(local.stack_position - base_stack_position) + "\n"
        state.text_section += "jmp " + end_label + "\n" 
    #generate the end label
    state.text_section += end_label + ":\n"

def generate_while(ast, state):
    #generate `while` condition
    while_label = "_WHILE" + str(state.label_count)
    state.text_section += while_label + ":\n"
    condition = generate_expression(ast["condition"]["content"], state)
    if condition.is_constant:
        state.text_section += "mov rax, " + condition.val + "\n" 
        condition.val = "rax"
    state.label_count += 1
    state.text_section += "cmp " + condition.val + ", 0\n"
    end_label = "_END" + str(state.label_count)
    state.label_count += 1
    state.text_section += "je " + end_label + "\n"
 
    #generate `while` body
    local = copy.deepcopy(state)
    local.text_section = ""
    local.continue_label = while_label
    local.break_label = end_label
    base_stack_position = local.stack_position
    generate(ast["body"], state=local)
    state.text_section += local.text_section
    state.label_count += local.label_count    
    if local.stack_position - base_stack_position != 0:
        state.text_section += "add rsp, " + str(local.stack_position - base_stack_position) + "\n"
    state.text_section += "jmp " + while_label + "\n" 

    state.text_section += end_label + ":\n"

def generate_continue(ast, state):
    state.text_section += "jmp " + state.continue_label + "\n"

def generate_break(ast, state):
    state.text_section += "jmp " + state.break_label + "\n"

def to_int(token):
    val = 0
    if token.type == "CHAR":
        val = ord(token.val)
    elif token.type == "INT":
        val = int(token.val)
    elif token.type == "FLOAT":
        #TODO:ADD FLOAT SUPPORT
        val = float(token.val)
    elif token.type == "BOOL":
        if token.val == "true":
            val = 1
        elif token.val == "false":
            val = 0
    token.val = str(val)
    token.tag = "INT"
    return token

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
    if reg_list.get(reg):
        return reg_list[reg][size]
    else:
        return reg

def size_to_number(size):
    if size == "qword":
        return 8
    elif size == "dword":
        return 4
    elif size == "word":
        return 2
    elif size == "byte":
        return 1
