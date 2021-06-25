import lexer
import sys

#TODO
#chapter 1: expressions(DONE)~
#-----
#
#chapter 2: control flow(DONE)~
#------
#
#chapter 3: functional(DONE)~
#-------
#
#chapter 4: final touch~
#-better error output
#-better error recovery

class parser_state():
    def __init__ (self, tokens, pos=0):
        self.tokens = tokens
        self.pos = pos
        self.output = []
        self.is_error = False
        self.symbol_table = []

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

    def insert(self, item):
        if self.lookup(item) is None:
            self.symbol_table.append(item)
        else:
            return None

    def lookup(self, item):
        try:
            return self.symbol_table[item]
        except KeyError:
            return None

def parse(input):
    tokens = init_tokens(input)
    state = parser_state(tokens)
    output = []

    while state.get_pos() < state.get_tokens_len():
        res = parse_basic(state)
        if res is None:
            res = parse_blocked(state)
            if res is None:
                catch_not_match(state)
                state.inc_position()
                continue

        state = res
        output.append(res.get_output())
        state.inc_position()

    state.set_output(output)
    return state

def parse_basic(state):
    res = parse_variable_declaration(state)
    if res is None:
        res = parse_expression(state)
        if res is None:
            res = parse_return(state)
            if res is None:
                res = parse_break(state)
                if res is None:
                    res = parse_continue(state)
                    if res is None:
                        res = parse_type_declaration(state)
                        if res is None:
                            return None
    state = res
    state.inc_position()
    if state.get_token_val() != ";":
        state.dec_position()
        throw_semicolon_error(state)
    return state

def parse_blocked(state):
    res = parse_while(state)
    if res is None:
        res = parse_for(state)
        if res is None:
            res = parse_if(state)
            if res is None:
                res = parse_function_declaration(state)
                if res is None:
                    return None

    state = res
    return state

def parse_body_basic(state):
    res = parse_variable_declaration(state)
    if res is None:
        res = parse_expression(state)
        if res is None:
            res = parse_return(state)
            if res is None:
                res = parse_break(state)
                if res is None:
                    res = parse_continue(state)
                    if res is None:
                        return None
    state = res
    state.inc_position()
    if state.get_token_val() != ";":
        state.dec_position()
        throw_semicolon_error(state)
    return state    

def parse_body(state):
    output = []
    while state.get_token_val() is not None:
        if state.get_token_val() == "}":
            #we're passing the end of the body, decrement and then break
            state.dec_position()
            break
        res = parse_body_basic(state)
        if res is None:
            res = parse_while(state)
            if res is None:
                res = parse_for(state)
                if res is None:
                    res = parse_if(state)
                    if res is None:
                        return None
                        #catch_not_match(state)
                        #state.inc_position()
                        #continue

        state = res
        output.append(res.get_output())
        state.inc_position()

    state.set_output(output)
    return state

def catch_not_match(state):
    if state.get_token_val() != None:
        if state.get_token_tag() == "STRING":
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
        (r'type',                           RESERVED),
        (r'func',                           RESERVED),
        (r'if',                             RESERVED),
        (r'elif',                           RESERVED),
        (r'else',                           RESERVED),
        (r'else',                           RESERVED),
        (r'while',                          RESERVED),
        (r'for',                            RESERVED),
        (r'break',                          RESERVED),
        (r'continue',                       RESERVED),
        (r'return',                         RESERVED),
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

def parse_type_declaration(state):
    output = {
        "context":"type_declaration",
        "content":{
            "id":None,
            "min_size": None,
        }
    }
    if state.get_token_val() != "type":
        return None

    state.inc_position()
    if state.get_token_tag() != "ID":
        return None
    output["content"]["id"] = state.get_token_val()

    state.inc_position()
    if state.get_token_val() != ":":
        state.dec_position()
        output["content"]["min_size"] = "byte";
        state.set_output(output)
        return state        

    state.inc_position()
    if state.get_token_tag() != "SIZE":
        return None
    output["content"]["min_size"] = state.get_token_val()

    state.set_output(output)
    return state

def parse_function_declaration(state):
    output = {
        "context": "function_declaration",
        "content": {
            "id": None,
            "parameters": [],
            "body": None,
            "type": None
        }
    }

    if state.get_token_val() != "func":
        return None

    state.inc_position()
    if state.get_token_tag() != "ID":
        return None
    output["content"]["id"] = state.get_token_val()

    state.inc_position()
    if state.get_token_val() != "(":
        return None

    state.inc_position()
    while True:
        if state.get_token_val() == ")":
            break
        res = parse_variable_declaration(state)
        if res is None:
            return None
        state = res
        output["content"]["parameters"].append(state.get_output())
        state.inc_position()
        if state.get_token_val() == ",":
            state.inc_position()
            if state.get_token_val() == ")":
                return None

    state.inc_position()
    if state.get_token_val() != ":":
        return None

    state.inc_position()
    if state.get_token_tag() != "ID":
        return None
    output["content"]["type"] = state.get_token_val()

    state.inc_position()
    if state.get_token_val() != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None

    state = res
    output["content"]["body"] = res.get_output()

    state.inc_position()
    if state.get_token_val() != "}":
        return None

    state.set_output(output)
    return state

def parse_while(state):
    output = {
        "context":"while",
        "content": {
            "condition": None,
            "body": None
        }
    }
    if state.get_token_val() != "while":
        return None

    state.inc_position()
    if state.get_token_val() != "(":
        return None

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        return None
    state = res
    output["content"]["condition"] = res.get_output()

    state.inc_position()
    if state.get_token_val() != ")":
        return None

    state.inc_position()
    if state.get_token_val() != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None

    state = res
    output["content"]["body"] = res.get_output()

    state.inc_position()
    if state.get_token_val() != "}":
        return None

    state.set_output(output)
    return state

def parse_for(state):
    output = {
        "context":"for",
        "content": {
            "condition": None,
            "setup": None,
            "increment": None,
            "body": None
        }
    }
    if state.get_token_val() != "for":
        return None

    state.inc_position()
    if state.get_token_val() != "(":
        throw_parse_error("expected a '('", state)

    state.inc_position()
    res = parse_basic(state)
    if res is None:
        return None
    state = res
    output["content"]["setup"] = res.get_output()
    
    state.inc_position()
    res = parse_basic(state)
    if res is None:
        return None
    state = res
    output["content"]["condition"] = res.get_output()

    state.inc_position()
    res = parse_basic(state)
    if res is None:
        return None
    state = res
    output["content"]["increment"] = res.get_output()

    state.inc_position()
    if state.get_token_val() != ")":
        return None

    state.inc_position()
    if state.get_token_val() != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None

    state = res
    output["body"] = res.get_output()

    state.inc_position()
    if state.get_token_val() != "}":
        return None

    state.set_output(output)
    return state

def parse_if(state):
    output = {
        "context":"if",
        "content": {
            "condition": None,
            "body": None,
            "else":None,
            "elif":[]
        }
    }
    if state.get_token_val() != "if":
        return None

    state.inc_position()
    if state.get_token_val() != "(":
        return None

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        return None
    state = res
    output["content"]["condition"] = res.get_output()

    state.inc_position()
    if state.get_token_val() != ")":
        throw_parse_error("expected a ')'", state)

    state.inc_position()
    if state.get_token_val() != "{":
        throw_parse_error("expected a '{'", state)

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None
    state = res
    output["content"]["body"] = res.get_output()

    state.inc_position()
    if state.get_token_val() != "}":
        return None

    state.inc_position()
    res = parse_elif(state)
    if res is not None:
        state = res
        output["content"]["elif"] = res.get_output()
        state.inc_position()

    res = parse_else(state)
    if res is None:
        state.dec_position()
        state.set_output(output)
        return state

    state = res
    output["content"]["else"] = res.get_output()
    state.set_output(output)
    return state

def parse_elif(state):
    output = []
    small_output = {
        "context" : "elif",
        "content" : {
            "conditon" : None,
            "body": None
        }
    }
    if state.get_token_val() != "elif":
        return None

    while state.get_token_val() == "elif":
        state.inc_position()
        if state.get_token_val() != "(":
            return None

        state.inc_position()
        res = parse_expression(state)
        if res is None:
            return None
        state = res
        small_output["content"]["condition"] = res.get_output()

        state.inc_position()
        if state.get_token_val() != ")":
            return None

        state.inc_position()
        if state.get_token_val() != "{":
            return None

        state.inc_position()
        res = parse_body(state)
        if res is None:
            return None

        state = res
        small_output["content"]["body"] = res.get_output()

        state.inc_position()
        if state.get_token_val() != "}":
            return None

        output.append(small_output)
        state.inc_position()

    state.dec_position()
    state.set_output(output)
    return state

def parse_else(state):
    output = {
        "context" : "else",
        "content" : {
            "body": None
        }
    }

    if state.get_token_val() != "else":
        return None

    state.inc_position()
    if state.get_token_val() != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None
    state = res
    output["content"]["body"] = res.get_output()

    state.inc_position()
    if state.get_token_val() != "}":
        return None

    state.set_output(output)
    return state

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
    if state.get_token_tag() != "SIZE":
        return None

    output["content"]["size"] = state.get_token_val()

    state.inc_position()
    if state.get_token_val() == "[":
        #expect a integer literal (VLA is not allowed in asca)
        state.inc_position()
        if state.get_token_tag() != "INT":
            throw_parse_error("expected an integer literal", state)

        output["content"]["array-size"] = state.get_token_val()
        state.inc_position()
        if state.get_token_val() != "]":
            return None
        state.inc_position()

    if state.get_token_tag() != "ID":
        return None
    output["content"]["id"] = state.get_token_val()

    state.inc_position()
    if state.get_token_val() != ":":
        return None

    state.inc_position()
    if state.get_token_tag() == "ID":
        output["content"]["type"] = state.get_token_val()
    else:
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

#use pratt parsing because it's cool
def parse_expression_recursive(state, rbp = 0):
    if state.get_token_val() == "(":
        state.inc_position()
        res = parse_expression_recursive(state)
        if res is None:
            return None
        res.inc_position()
        if res.get_token_val() != ")":
            return None
    else:
        res = parse_value(state)
        if res is None:
            res = parse_unary(state)
            if res is None:
                return None
    state = res
    left = res.get_output()

    operator = state.peek_next_token_val()
    if get_priority(operator) is None:
        state.set_output(left)
        return state

    while get_priority(operator) > rbp:
        state.inc_position()
        operator = state.get_token_val()
        if get_priority(operator) is None:
            state.dec_position()
            state.set_output(left)
            return state

        state.inc_position()
        if get_associativity(operator) == "left":
            res = parse_expression_recursive(state, get_priority(operator))
        else:
            res = parse_expression_recursive(state, get_priority(operator) - 1)
        if res is None:
            return None
        state = res
        left = [left, operator, res.get_output()]

    state.set_output(left)
    return state

def get_priority(token):
    if token == "=" or\
         token == "+=" or\
         token == "-=" or\
         token == "*=" or\
         token == "/=":
        return 10
    elif token == "||":
        return 20
    elif token == "&&":
        return 30
    elif token == ">=" or\
         token == ">"  or\
         token == "<=" or\
         token == "<"  or\
         token == "==" or\
         token == "!=":
        return 40
    elif token == "+" or\
         token == "-":
        return 50
    elif token == "*" or\
         token == "/":
        return 60

def get_associativity(token):
    if token == "||":
        return "left"
    elif token == "&&":
        return "left"
    elif token == "+" or\
         token == "-":
        return "left"
    elif token == "*" or\
         token == "/":
        return "left"
    elif token == ">=" or\
         token == ">"  or\
         token == "<=" or\
         token == "<"  or\
         token == "==" or\
         token == "!=":
        return "left"
    elif token == "="  or\
         token == "+=" or\
         token == "-=" or\
         token == "*=" or\
         token == "/=":
        return "right"

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
            res = parse_expression_recursive(state)
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
        state.set_output({"type": "int", "value": value})
    elif token_type == "STRING":
        res = parse_string(state)
        if res is not None:
            state = res
            #no need to set output
        else:
            return None
    elif token_type == "CHAR":
        res = parse_char(state)
        if res is not None:
            state = res
            #no need to set output
        else:
            return None
    elif token_type == "BOOL":
        return {"type": "bool", "value": value}
    elif token_type == "ID":
        res = parse_identifier(state)
        if res is not None:
            state = res
            #no need to set output
        else:
            return None
    elif token_type == "FLOAT":
        state.set_output({"type": "float", "value": value})
    else:
        return None
    return state

def parse_identifier(state):
    output = {
            "type": "identifier",
            "value":None,
            "array-value": None,
        }
    output["value"] = state.get_token_val()
    if state.peek_next_token_val() == "(":
        res = parse_function_call(state)
        if res is None:
            return None
        state = res
        return state
    elif state.peek_next_token_val() == "[":
        state.inc_position(2)
        res = parse_expression(state)
        if res is not None:
            state = res
            output["array-value"] = res.get_output()
            state.set_output(output)
        else:
            return None
        #expect for closing ']'
        state.inc_position()
        if state.get_token_val() != "]":
            throw_parse_error("expected a closing ']'", state)
            return None

        state.set_output(output)
        return state
    else:
        state.set_output(output)
        return state

def parse_string(state):
    value = state.get_token_val()
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
    return state

def parse_char(state):
    value = state.get_token_val()
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

    state.inc_position()
    if state.get_token_val() != "(":
        state.dec_position()
        return None

    state.inc_position()
    while True:
        if state.get_token_val() == ")":
            break
        res = parse_expression(state)
        if res is None:
            return None
        state = res
        output["parameters"].append(state.get_output())
        state.inc_position()
        if state.get_token_val() == ",":
            state.inc_position()
            if state.get_token_val() == ")":
                return None

    state.set_output(output)
    return state

def parse_return(state):
    output = {
        "context" : "return",
        "content" : {
            "value": None
        }
    }
    if state.get_token_val() != "return":
        return None

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        return None

    state = res
    output["content"]["value"] = res.get_output()
    state.set_output(output)
    return state

def parse_break(state):
    output = {
        "context": "break"
    }
    if state.get_token_val() != "break":
        return None

    state.set_output(output)
    return state

def parse_continue(state):
    output = {
        "context": "continue"
    }
    if state.get_token_val() != "continue":
        return None
        
    state.set_output(output)
    return state

def throw_parse_error(msg, state):
    sys.stderr.write("Error: %s at line %s: %s \n" % (msg, state.get_token_line(), state.get_token_char()))
    state.is_error = True

def throw_semicolon_error(state):
    sys.stderr.write("Error: expected a semicolon at line %s: %s \n" % (state.get_token_line(), state.get_token_char()+len(state.get_token_val())))
    state.is_error = True    
