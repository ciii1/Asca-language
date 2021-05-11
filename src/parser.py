import lexer
import sys

#TODO
#chapter 1 (DONE)#
#
#chapter 2#
#-if
#-->elif
#-->else
#-while
#-for
#-function declaration
#-type declaration

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

    def get_token_tag(self):
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
    def peek_next_token_tag(self, n=1):
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
        if res is None:
            res = parse_expression(state)
            if res is None:
                catch_not_match(state)
                continue

        state = res
        output.append(state.get_output())
        state.inc_position()
        if state.get_token_val() != ";":
            state.dec_position()
            throw_semicolon_error(state)
        continue

    state.set_output(output)
    return state

def catch_not_match(state):
    if state.get_token_val() != None:
        if state.get_token_tag() != "RESERVED":
            throw_parse_error("unexpected token with type 'string'",state)
        else:
            throw_parse_error("unexpected token: %s " % state.get_token_val(), state)
    else:
        throw_parse_error("unexpected EOF", state)

def init_tokens(input):

    RESERVED     = 'RESERVED'
    INT          = 'INT'
    ID           = 'ID'
    SIZE         = 'SIZE'
    STRING       = 'STRING'
    BOOL         = 'BOOL'
    CHAR         = 'CHAR'
    FLOAT        = 'FLOAT'
    OPERATOR     = 'OPERATOR'
    
    token_exprs = [
        (r'\n',                             None),
        (r'[ \t]+',                         None),
        (r'#[^\n]*',                        None),
        (r'\[',                             RESERVED),
        (r'\]',                             RESERVED),
        (r'\:',                             RESERVED),
        (r'\;',                             RESERVED),
        (r',',                              RESERVED),
        (r'\(',                             RESERVED),
        (r'\)',                             RESERVED),
        (r'\{',                             RESERVED),
        (r'\}',                             RESERVED),
        (r'@',                              RESERVED),
        (r'\$',                             RESERVED),
        (r'!',                              RESERVED),
        (r'==',                             OPERATOR),
        (r'<=',                             OPERATOR),
        (r'<',                              OPERATOR),
        (r'>=',                             OPERATOR),
        (r'>',                              OPERATOR),
        (r'!=',                             OPERATOR),
        (r'&&',                             OPERATOR),
        (r'\|\|',                           OPERATOR),
        (r'=',                              OPERATOR),
        (r'\+=',                            OPERATOR),
        (r'\-=',                            OPERATOR),
        (r'\/=',                            OPERATOR),
        (r'\*=',                            OPERATOR),
        (r'\+',                             OPERATOR),
        (r'-',                              OPERATOR),
        (r'\*',                             OPERATOR),
        (r'/',                              OPERATOR),
        (r'if',                             RESERVED),
        (r'then',                           RESERVED),
        (r'else',                           RESERVED),
        (r'while',                          RESERVED),
        (r'\".*?\"',                        STRING),
        (r'[0-9]+\.[0-9]+',                 FLOAT),
        (r'\'.*?\'',                        CHAR),
        (r'true|false',                     BOOL),
        (r'qword',                          SIZE),
        (r'dword',                          SIZE),
        (r'word',                           SIZE),
        (r'byte',                           SIZE),
        (r'[0-9]+',                         INT),
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
    if state.get_token_tag() == "SIZE":
        output["content"]["size"] = state.get_token_val()
    else:
        return None

    state.inc_position()
    if state.get_token_val() == "[":
        #expect a integer literal (VLA is not allowed in asca)
        state.inc_position()
        if state.get_token_tag() != "INT":
            throw_parse_error("expected an integer literal", state)

        output["content"]["array-size"] = state.get_token_val()
        state.inc_position()
        if state.get_token_val() != "]":
            throw_parse_error("expected a ']'", state)
        state.inc_position()

    if state.get_token_tag() == "ID":
        output["content"]["id"] = state.get_token_val()
    else:
        throw_parse_error("illegal identifier name", state)
        return None

    state.inc_position()
    if state.get_token_val() != ":":
        throw_parse_error("expected a colon", state)
        return None
    state.inc_position()
    if state.get_token_tag() == "ID":
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

def parse_expression_brackets(state):
    output = []
    if state.get_token_val() != "(":
        return None

    state.inc_position()

    #parse the expression inside the bracket
    res = parse_expression_recursive(state)
    if res is not None:
        state = res
        output.append(res.get_output())
        state.set_output(output)
    else:
        return None

    state.inc_position()

    #expect a closing bracket
    if state.get_token_val() != ")":
        return None
        
    return state

def parse_expression_recursive(state):
    output = []

    res = parse_value(state)
    if res is None:
        res = parse_unary(state)
        if res is None:
            res = parse_expression_brackets(state)
            if res is None:
                return None
    state = res
    operand = res.get_output()
    for i in range(0, get_highest_priority()):
        operand = [operand]
    output.append(operand)

    while True:
        if state.get_token_tag() == "OPERATOR":
            priority = get_priority(state.get_token_val())
            associativity = get_associativity(state.get_token_val())
            nest = get_highest_priority() - priority
            index = []
            for i in range(0, priority):
                index.append(-1)
            operator = state.get_token_val()

            state.inc_position()
            operand = None

            if associativity == "left-to-right":
                res = parse_value(state)
                if res is None:
                    res = parse_unary(state)
                    if res is None:
                        if state.get_token_val() == "(":
                            continue
                        else:
                            return None
                state = res
                operand = res.get_output()
                for i in range(0, nest):
                    operand = [operand]
            elif associativity == "right-to-left":
                res = parse_expression_recursive(state)
                if res is not None:
                    state = res
                    operand = res.get_output()
                else:
                    return None

            append_to_nested(output, index, operator)
            append_to_nested(output, index, operand)

        elif state.get_token_val() == "(":
            res = parse_expression_brackets(state)
            if res is not None:
                state = res
                #append it to the highest level of nested list
                nest = output
                index = []
                while True:
                    if type(nest[-1]) is list:
                        nest = nest[-1]
                        index.append(-1)
                    else:
                        break

                append_to_nested(output, index, res.get_output())
            else:
                return None
        elif state.peek_next_token_tag() != "OPERATOR":
            break
        else:
            state.inc_position()

    state.set_output(clean_tree(output))
    #state.set_output(output)
    return state

def get_priority(token):
    if token == "=" or\
       token == "+=" or\
       token == "-=" or\
       token == "*=" or\
       token == "/=":
        return 0
    elif token == "||":
        return 1
    elif token == "&&":
        return 2
    elif token == ">=" or\
         token == ">"  or\
         token == "<=" or\
         token == "<"  or\
         token == "==" or\
         token == "!=":
        return 3
    elif token == "+" or\
         token == "-":
        return 4
    elif token == "*" or\
         token == "/":
        return 5

def get_associativity(token):
    if token == "||":
        return "left-to-right"
    elif token == "&&":
        return "left-to-right"
    elif token == "+" or\
         token == "-":
        return "left-to-right"
    elif token == "*" or\
         token == "/":
        return "left-to-right"
    elif token == ">=" or\
         token == ">"  or\
         token == "<=" or\
         token == "<"  or\
         token == "==" or\
         token == "!=":
        return "left-to-right"
    elif token == "="  or\
         token == "+=" or\
         token == "-=" or\
         token == "*=" or\
         token == "/=":
        return "right-to-left"

def get_highest_priority():
    return 5

def parse_unary(state):
    output = []
    if state.get_token_val() == "$" or\
       state.get_token_val() == "@" or\
       state.get_token_val() == "-" or\
       state.get_token_val() == "+":
        output.append(state.get_token_val())
    else:
        return None

    state.inc_position()
    res = parse_value(state)
    if res is None:
        res = parse_unary(state)
        if res is None:
            res = parse_expression_brackets(state)
            if res is None:
                return None
    state = res
    output.append(res.get_output()) 

    state.set_output(output)
    return state

def parse_value(state):
    token_type = state.get_token_tag()
    value = state.get_token_val()
    if token_type == "INT":
        state.set_output({"type": "int", 
                          "value": value, 
                          "is_negative": False})

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
        state.set_output({"type": "string", 
                          "value": value})
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
            state.set_output({"type": "char", 
                              "value": value[1]})
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
            #check for array accessing
            if state.peek_next_token_val() == "[":
                state.inc_position(2)
                res = parse_expression(state)
                if res is not None:
                    state = res
                    state.set_output({"type"       : "identifier", 
                                      "value"      : value, 
                                      "is_negative": False, 
                                      "array-value": res.get_output()})
                else:
                    return None
                #expect for closing ']'
                state.inc_position()
                if state.get_token_val() != "]":
                    throw_parse_error("expected a closing ']'", state)
                    return None
            else:       
                state.set_output({"type"       : "identifier", 
                                  "value"      : value, 
                                  "is_negative": False, 
                                  "array-value": None})
    elif token_type == "FLOAT":
        state.set_output({"type": "float", 
                          "value": value, 
                          "is_negative": False})
    else:
        return None
    return state

def parse_function_call(state):
    output = {
        "type": "function_call",
        "value": None,
        "parameters": []
    }

    if state.get_token_tag() == "ID":
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

def throw_semicolon_error(state):
    sys.stderr.write("Error: expected a semicolon at line %s: %s \n" % (state.get_token_line(), state.get_token_char()+len(state.get_token_val())))
    state.is_error = True    

def clean_tree(tree):
    output = []
    for i in tree:
        if type(i) is list:
            x = i
            while type(x) is list:
                if len(x) == 1:
                    x = x[0]
                else:
                    x = clean_tree(x)
                    break
            output.append(x)
        else:
            output.append(i)
    return output

def append_to_nested(initializer, iterable, val):
    function = lambda s, i: s[i]
    it = iter(iterable)
    if initializer is None:
        value = next(it)
    else:
        value = initializer
    for element in it:
        value = function(value, element)
    value.append(val)
    return value
