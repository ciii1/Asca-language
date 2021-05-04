import lexer
import sys
from ast import literal_eval

class parser_state():
    def __init__ (self, tokens, pos=0):
        self.tokens = tokens
        self.pos = pos
        self.output = []

    def inc_position(self):
        self.pos += 1
    def dec_position(self):
        self.pos -= 1
    def jump_position(self, index):
        self.pos = index

    def set_output(self, out):
        self.output = out
    def get_output(self):
        return self.output

    def get_token_type(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos][1]
        else:
            return None
    def get_token_val(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos][0]
        else:
            return None
    def get_tokens_len(self):
        return len(self.tokens)
    def get_pos(self):
        return self.pos

def parse(input):
    tokens = init_tokens(input)
    state = parser_state(tokens)
    state.jump_position(-1)
    output = []

    while state.get_pos() < state.get_tokens_len():
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
    return output

def init_tokens(input):

    RESERVED = 'RESERVED'
    INT      = 'INT'
    ID       = 'ID'
    SIZE     = 'SIZE'
    STRING   = 'STRING'
    BOOL     = 'BOOL'
    OPERATOR = 'OPERATOR'
    
    token_exprs = [
        (r'[ \n\t]+',                None),
        (r'#[^\n]*',                 None),
        (r'\=',                      RESERVED),
        (r'\:',                      RESERVED),
        (r'\(',                      RESERVED),
        (r'\)',                      RESERVED),
        (r'\{',                      RESERVED),
        (r'\}',                      RESERVED),
        (r'(?<![0-9])[+-]?[0-9]+',   INT),
        (r'\+',                      OPERATOR),
        (r'-',                       OPERATOR),
        (r'\*',                      OPERATOR),
        (r'/',                       OPERATOR),
        (r'<=',                      OPERATOR),
        (r'<',                       OPERATOR),
        (r'>=',                      OPERATOR),
        (r'>',                       OPERATOR),
        (r'=',                       OPERATOR),
        (r'!=',                      OPERATOR),
        (r'&&',                      OPERATOR),
        (r'\|\|',                    OPERATOR),
        (r'!',                       OPERATOR),
        (r'if',                      RESERVED),
        (r'then',                    RESERVED),
        (r'else',                    RESERVED),
        (r'while',                   RESERVED),
        (r'qword',                   SIZE),
        (r'dword',                   SIZE),
        (r'word',                    SIZE),
        (r'byte',                    SIZE),
        (r'true|false',              BOOL),
        (r'\".*?\"',                 STRING),
        (r'[_A-Za-z][A-Za-z0-9_]*',  ID)
    ]

    return lexer.lex(input, token_exprs)


def parse_variable_declaration(state):
    output = {
        "size": None,
        "id": None,
        "type": None,
        "init": None,
    }
    if state.get_token_type() == 'SIZE':
        output["size"] = state.get_token_val()
    else:
        return None

    state.inc_position()
    if state.get_token_type() == 'ID':
        output["id"] = state.get_token_val()
    else:
        throw_parse_error("Illegal identifier name", state)
        return None
    state.inc_position()
    if state.get_token_val() != ':':
        throw_parse_error("Expected a colon", state)
        return None
    state.inc_position()
    if state.get_token_type() == 'ID':
        output["type"] = state.get_token_val()
    else:
        throw_parse_error("Expected a type", state)
        return None
    state.inc_position()
    if state.get_token_val() == '=':
        state.inc_position()
        res = parse_expression(state)
        if res is not None:
            state = res
            output["init"] = state.get_output()
            state.set_output(output)
            return state
        else:
            throw_parse_error("Expected a value", state)
            return None
    else:
        state.set_output(output)
        return state

def parse_expression(state):
    output = []

    if is_value(state.get_token_type()):
        output.append([parse_value(state)])
    else:
        return None

    while True:
        if is_value(state.get_token_type()):
            state.inc_position()
            if state.get_token_type() != 'OPERATOR':
                break
        if state.get_token_val() == "+" or\
           state.get_token_val() == "-":
            output.append(parse_value(state))
            state.inc_position()
            if is_value(state.get_token_type()):
                output.append([parse_value(state)])
            else:
                throw_parse_error("expected an operand", state)
                return None

        if state.get_token_val() == "*" or\
           state.get_token_val() == "/":
            if type(output[-1]) is list:
                output[-1].append(parse_value(state))
                state.inc_position()
                if is_value(state.get_token_type()):
                    output[-1].append(parse_value(state))
                else:
                    throw_parse_error("expected an operand", state)
                    return None
            else:
                output.append(parse_value(state))
                state.inc_position()
                if is_value(state.get_token_type()):
                    output.append([parse_value(state)])
                else:
                    throw_parse_error("expected an operand", state)
                    return None

    state.set_output(output)
    return state
    
def is_value(token_type):
    if token_type == "INT":
        return True
    elif token_type == "STRING":
        return True
    elif token_type == "BOOL":
        return True
    elif token_type == "ID":
        return True
    return False

def parse_value(state):
    token_type = state.get_token_type()
    value = state.get_token_val()
    if token_type == "INT":
        return {"type": "int", "value": value}
    elif token_type == "STRING":
        return {"type": "string", "value": value}
    elif token_type == "BOOL":
        return {"type": "bool", "value": value}
    elif token_type == "ID":
        return {"type": "identifier", "value": value}
    elif token_type == "OPERATOR":
        return {"type": "operator", "value": value}
    return None

def throw_parse_error(msg, state):
    sys.stderr.write("Error: %s at token %s \n" % (msg, state.get_pos()+1))

def throw_EOF_error(msg):
    sys.stderr.write("Error: %s \n" % msg)
    sys.exit(1)

def is_tag_id(token_type, tag):
    if token_type is tag or token_type == "ID":
        return True
    else:
        return False