import lexer
import sys

class parser_state():
    def __init__ (self, tokens, pos=0):
        self.tokens = tokens
        self.pos = pos
        self.output = []
        self.is_error = False

    def inc_position(self, n=1):
        self.pos += n
    def dec_position(self, n=1):
        self.pos -= n
    def jump_position(self, index):
        self.pos = index
    def get_pos(self):
        return self.pos

    def set_output(self, out):
        self.output = out
    def get_output(self):
        return self.output

    def get_token_type(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos].get_tag()
        else:
            return None
    def get_token_val(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos].get_token()
        else:
            return None
    def get_tokens_len(self):
        return len(self.tokens)
    def peek_next_token_val(self, n=1):
        if self.pos + n < len(self.tokens):
            return self.tokens[self.pos+n].get_token()
        else:
            return None
    def peek_next_token_type(self, n=1):
        if self.pos + n < len(self.tokens):
            return self.tokens[self.pos+n].get_tag()
        else:
            return None


    def get_token_line(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos].get_line()
        else:
            return self.tokens[-1].get_line()
    def get_token_char(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos].get_char()+1
        else:
            return self.tokens[-1].get_char()

def parse(input):
    tokens = init_tokens(input)
    state = parser_state(tokens)
    state.jump_position(-1)
    output = []

    while state.get_pos() < state.get_tokens_len()-1:
        state.inc_position()
        res = parse_variable_declaration(state)
        if res is not None:
            state = res
            output.append(state.get_output())
            continue
        res = parse_expression(state)
        if res is not None:
            state = res
            output.append(state.get_output())
            continue
        else:
            catch_not_match(state)
            continue
    state.set_output(output)
    return state

def catch_not_match(state):
    if state.get_token_val() == ")":
        throw_parse_error("unexpected ')'", state)
    elif state.get_token_val() == "(":
        throw_parse_error("expected an ending for '('")
    elif state.get_token_val() != None:
        throw_parse_error("unexpected token: %s " % state.get_token_val(), state)
    else:
        throw_parse_error("unexpected EOF", state)

def init_tokens(input):

    RESERVED = 'RESERVED'
    INT      = 'INT'
    ID       = 'ID'
    SIZE     = 'SIZE'
    STRING   = 'STRING'
    BOOL     = 'BOOL'
    OPERATOR = 'OPERATOR'
    CHAR     = 'CHAR'
    FLOAT    = 'FLOAT'
    
    token_exprs = [
        (r'\n',                             None),
        (r'[ \n\t]+',                       None),
        (r'#[^\n]*',                        None),
        (r'\=',                             RESERVED),
        (r'@',                              RESERVED),
        (r'\[',                             RESERVED),
        (r'\]',                             RESERVED),
        (r'\:',                             RESERVED),
        (r',',                              RESERVED),
        (r'\(',                             RESERVED),
        (r'\)',                             RESERVED),
        (r'\{',                             RESERVED),
        (r'\}',                             RESERVED),
        (r'((?<![0-9\"a-zA-Z_)])[+-])?'+
          '[0-9]+\.[0-9]+',                 FLOAT),
        (r'((?<![0-9\"a-zA-Z_)])[+-])?'+
          '[0-9]+',                         INT),
        (r'\+',                             OPERATOR),
        (r'-',                              OPERATOR),
        (r'\*',                             OPERATOR),
        (r'/',                              OPERATOR),
        (r'<=',                             OPERATOR),
        (r'<',                              OPERATOR),
        (r'>=',                             OPERATOR),
        (r'>',                              OPERATOR),
        (r'=',                              OPERATOR),
        (r'!=',                             OPERATOR),
        (r'&&',                             OPERATOR),
        (r'\|\|',                           OPERATOR),
        (r'!',                              OPERATOR),
        (r'if',                             RESERVED),
        (r'then',                           RESERVED),
        (r'else',                           RESERVED),
        (r'while',                          RESERVED),
        (r'qword',                          SIZE),
        (r'dword',                          SIZE),
        (r'word',                           SIZE),
        (r'byte',                           SIZE),
        (r'true|false',                     BOOL),
        (r'\".*?\"',                        STRING),
        (r'\'.*?\'',                        CHAR),
        (r'[_A-Za-z][A-Za-z0-9_]*',         ID)
    ]

    return lexer.lex(input, token_exprs)

def parse_variable_declaration(state):
    output = {
        "context": "variable_declaration",
        "content": {
            "size": None,
            "array-size": None,
            "id": None,
            "type": None,
            "init": None,
        }
    }
    if state.get_token_type() == "SIZE":
        output["content"]["size"] = state.get_token_val()
    else:
        return None

    state.inc_position()
    if state.get_token_val() == "[":
        #expect a integer literal (VLA is not allowed in asca)
        state.inc_position()
        if state.get_token_type() != "INT":
            throw_parse_error("expected an integer literal", state)

        output["content"]["array-size"] = state.get_token_val()
        state.inc_position()
        if state.get_token_val() != "]":
            throw_parse_error("expected a ']'", state)
        state.inc_position()

    if state.get_token_type() == "ID":
        output["content"]["id"] = state.get_token_val()
    else:
        throw_parse_error("illegal identifier name", state)
        return None

    state.inc_position()
    if state.get_token_val() != ":":
        throw_parse_error("expected a colon", state)
        return None
    state.inc_position()
    if state.get_token_type() == "ID":
        output["content"]["type"] = state.get_token_val()
    else:
        throw_parse_error("expected a type", state)
        return None
    if state.peek_next_token_val() == '=':
        state.inc_position(2)
        res = parse_expression(state)
        if res is not None:
            state = res
            output["content"]["init"] = state.get_output()
            state.set_output(output)
            return state
        else:
            throw_parse_error("expected a value", state)
            return None
    else:
        state.set_output(output)
        return state

def parse_expression(state):
    output = {
        "context": "expression",
        "content": None
    }
    res = parse_expression_recursive(state)
    if res is not None:
        state = res
        output['content'] = state.get_output()
        state.set_output(output)
        return state
    else:
        return None

def parse_expression_brackets(state, in_brackets = False):
    output = []
    if state.get_token_val() != "(":
        return None

    state.inc_position()

    #parse the expression inside the bracket
    res = parse_expression_recursive(state, True)
    if res is not None:
        state = res
        output.append(res.get_output())
        state.set_output(output)
    else:
        return None

    state.inc_position()

    #expect a closing bracket
    if state.get_token_val() != ")":
        throw_parse_error("expected a closing ')'", state)
        return None
        
    return state

def parse_expression_recursive(state, in_brackets=False):
    output = []

    if is_value(state.get_token_type()):
        #the first operand will always on a sub-list
        #so the "*" and "/" is able to get inserted to it
        res = parse_value(state)
        if res is not None:
            state = res
            output.append([state.get_output()])
        else:
            return None
    elif state.get_token_val() == "(":
        res = parse_expression_brackets(state, in_brackets)
        if res is not None:
            state = res
            #append the parsed tokens inside brackets to the output
            output.append(state.get_output())
        else:
            return None
    else:
        return None

    while True:
        if state.get_token_val() == "(":
            res = parse_expression_brackets(state, in_brackets)
            if res is not None:
                state = res
                #the expression inside brackets will always be inserted to
                #the last element if it's sub-list on the output
                if type(output[-1]) is list:
                    output[-1].append(state.get_output())
                else:
                    output.append(state.get_output())
            else:
                return None

        elif state.get_token_val() == "+" or\
             state.get_token_val() == "-":
            #append the operator to the output
            #note: we dont need to check if the parse_value
            #returns None since this code we'll be only 
            #executed if the current token is a "+" or a "-"
            output.append(parse_value(state).get_output())

            state.inc_position()
            if is_value(state.get_token_type()):
                #an element after "+" or "-" operator will always be in a sublist
                #so "*" and "/" could get inserted later to it
                res = parse_value(state)
                if res is not None:
                    state = res
                    output.append([state.get_output()])
                else:
                    return None

            #if the next element is a "(" then continue to the next round
            #let the "(" handler above handles it
            elif state.get_token_val() == "(":
                continue
            else:
                throw_parse_error("expected an operand", state)
                return None

        elif state.get_token_val() == "*" or\
             state.get_token_val() == "/":
            #a "*" and "/" will always be inserted to 
            #the last element, that's why we insert the numbers and operators
            #inside a sub-list earlier.

            output[-1].append(parse_value(state).get_output())
            state.inc_position()
            if is_value(state.get_token_type()):
                res = parse_value(state)
                if res is not None:
                    state = res
                    output[-1].append(state.get_output())
                else:
                    return None
            elif state.get_token_val() == "(":
                continue
            else:
                throw_parse_error("expected an operand", state)
                return None
        elif state.peek_next_token_type() != "OPERATOR":
            break
        else:
            state.inc_position()

    #since we inserted a lot of operands on a sublist,
    #there could be a single operand on a sublist, so we
    #need to get get those operands out of the sublist
    state.set_output(clean_tree(output))
    return state
    
def is_value(token_type):
    if token_type == "INT":
        return True
    elif token_type == "STRING":
        return True
    elif token_type == "CHAR":
        return True
    elif token_type == "BOOL":
        return True
    elif token_type == "ID":
        return True
    elif token_type == "FLOAT":
        return True
    return False

def parse_value(state):
    token_type = state.get_token_type()
    value = state.get_token_val()
    if token_type == "INT":
        state.set_output({"type": "int", "value": value})
    elif token_type == "STRING":
        #if it contains 2 or more character
        if len(value) > 3:
            value = value[1:-1]
        #if it contains 0 char (specified 2 here cos the '"' is counted)
        elif len(value) == 2:
            throw_parse_error("a string literal cannot be empty", state)
            return None
        #if it contains  1 character
        else:
            value = value[1]
        state.set_output({"type": "string", "value": value})
    elif token_type == "CHAR":
        #if it contains 2 or more character
        if len(value) > 3:
            throw_parse_error("a char literal can only contain 1 character", state)
            return None
        #if it contains 0 char
        elif len(value) == 2:
            throw_parse_error("a char literal cannot be empty", state)
            return None
        #if it contains  1 character
        else:
            state.set_output({"type": "char", "value": value[1]})
    elif token_type == "BOOL":
        return {"type": "bool", "value": value}
    elif token_type == "ID":
        #check if its a function
        res = parse_function_call(state)
        if res is not None:
            state = res
            #no need to set output cos it's already set by
            #the parse_function_call function
        else:
            state.set_output({"type": "identifier", "value": value})
    elif token_type == "OPERATOR":
        state.set_output({"type": "operator", "value": value})
    elif token_type == "FLOAT":
        state.set_output({"type": "float", "value": value})
    else:
        return None
    return state

def parse_function_call(state):
    output = {
        "type": "function_call",
        "value": None,
        "parameters": []
    }

    if state.get_token_type() == "ID":
        output["value"] = state.get_token_val()
    else:
        return None

    if state.peek_next_token_val() != "(":
        return None

    state.inc_position(2)
    if state.get_token_val() == ")":
        output['parameters'] = None
    else:
        while True:
            #parse the expresion inside, the second argument says to the
            #expression parser that it's parsing inside brackets
            res = parse_expression(state)
            if res is not None:
                state = res
                output['parameters'].append(state.get_output())
                state.inc_position()
                if state.get_token_val() == ",":
                    state.inc_position()
                elif state.get_token_val() == ")":
                    break
                else:
                    throw_parse_error("expected a ')'", state)
                    return None
            else:
                #if it returns none, it means that there's an
                #invalid expression inside the brackets
                catch_not_match(state)
                return None

    state.set_output(output)
    return state

def throw_parse_error(msg, state):
    sys.stderr.write("Error: %s at line %s: %s \n" % (msg, state.get_token_line(), state.get_token_char()))
    state.is_error = True

def throw_EOF_error(msg):
    sys.stderr.write("Error: %s \n" % msg)
    sys.exit(1)

def clean_tree(tree):
    output = []
    for i in tree:
        if type(i) is list:
            if len(i) == 1:
                if type(i[0]) is list:
                    output.append(clean_tree(i[0]))
                else:
                    output.append(i[0])
            elif len(i) > 1:
                output.append(clean_tree(i))
        else:
            output.append(i)
    return output