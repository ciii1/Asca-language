import copy
import lexer
import sys

#TODO
#fix error recovery. ITS A CHAOS RN
class parser_state():
    def __init__ (self, tokens, pos=0):
        self.tokens = tokens
        self.pos = pos
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

    def set_output(self, output):
        self.output = output
    def get_output(self):
        return self.output

    def get_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        else:
            return lexer.token(None, None, 0, 0)

    def peek_next_token(self, n=1):
        if self.pos + n < len(self.tokens):
            return self.tokens[self.pos+n]
        else:
            return lexer.token(None, None, 0, 0)

def parse(tokens):
    state = parser_state(tokens)
    output = []
    while state.get_pos() < len(state.tokens):
        res = parse_basic(state)
        if res is None:
            res = parse_blocked(state)
            if res is None:
                catch_not_match(state)
                state.inc_position()
                continue
        output.append(res)
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
                            res = parse_global(state)
                            if res is None:
                                res = parse_extern(state)
                                if res is None:
                                    return None
    state.inc_position()
    if state.get_token().val != ";":
        state.dec_position()
        throw_semicolon_error(state)
    return res

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
    return res

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
    state.inc_position()
    if state.get_token().val != ";":
        state.dec_position()
        throw_semicolon_error(state)
    return res   

def parse_body(state):
    output = []
    while state.get_token().val is not None:
        if state.get_token().val == "}":
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
        output.append(res)
        state.inc_position()
    return output

def catch_not_match(state):
    if state.get_token().val != None:
        if state.get_token().tag == "STRING":
            throw_parse_error("unexpected token with type 'string'",state)
        else:
            throw_parse_error("unexpected token: %s " % state.get_token().val, state)
    else:
        throw_eof_error(state)

def parse_type_declaration(state):
    output = {
        "context":"type_declaration",
        "content":{
            "id":None,
            "min_size": None,
        }
    }
    if state.get_token().val != "type":
        return None

    state.inc_position()
    if state.get_token().tag != "ID":
        return None
    output["content"]["id"] = state.get_token()

    state.inc_position()
    if state.get_token().val != ":":
        state.dec_position()
        return output        

    state.inc_position()
    if state.get_token().tag != "SIZE":
        return None
    output["content"]["min_size"] = state.get_token()

    return output

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

    if state.get_token().val != "func":
        return None

    state.inc_position()
    if state.get_token().tag != "ID":
        return None
    output["content"]["id"] = state.get_token()

    state.inc_position()
    if state.get_token().val != "(":
        return None

    state.inc_position()
    while True:
        template = {
                "expression": None,
                "is_floating_point": False
        }
        if state.get_token().val == ")":
            break
        if state.get_token().val == ":": #check for floating-point parameters
            template["is_floating_point"] = True
            state.inc_position()
        res = parse_variable_declaration(state)
        if res is None:
            return None
        template["expression"] = res
        output["content"]["parameters"].append(template)
        state.inc_position()
        if state.get_token().val == ",":
            state.inc_position()
            if state.get_token().val == ")":
                return None

    state.inc_position()
    if state.get_token().val != ":":
        return None

    state.inc_position()
    if state.get_token().tag != "ID":
        return None
    output["content"]["type"] = state.get_token()

    state.inc_position()
    if state.get_token().val != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None
    output["content"]["body"] = res

    state.inc_position()
    if state.get_token().val != "}":
        return None

    return output

def parse_while(state):
    output = {
        "context":"while",
        "content": {
            "condition": None,
            "body": None
        }
    }
    if state.get_token().val != "while":
        return None

    state.inc_position()
    if state.get_token().val != "(":
        return None

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        return None
    output["content"]["condition"] = res

    state.inc_position()
    if state.get_token().val != ")":
        return None

    state.inc_position()
    if state.get_token().val != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None
    output["content"]["body"] = res

    state.inc_position()
    if state.get_token().val != "}":
        return None

    return output

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
    if state.get_token().val != "for":
        return None

    state.inc_position()
    if state.get_token().val != "(":
        throw_parse_error("expected a '('", state)

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        res = parse_variable_declaration(state)
        if res is None:
            return None
    output["content"]["setup"] = res
    state.inc_position()
    if state.get_token().val != ";":
        return None

    state.inc_position() 
    res = parse_expression(state)
    if res is None:
        res = parse_variable_declaration(state)
        if res is None:
            return None
    output["content"]["condition"] = res
    state.inc_position()
    if state.get_token().val != ";":
        return None

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        res = parse_variable_declaration(state)
        if res is None:
            return None
    output["content"]["increment"] = res

    state.inc_position()
    if state.get_token().val != ")":
        return None
    state.inc_position()
    if state.get_token().val != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None
    output["content"]["body"] = res

    state.inc_position()
    if state.get_token().val != "}":
        return None

    return output

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
    if state.get_token().val != "if":
        return None

    state.inc_position()
    if state.get_token().val != "(":
        return None

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        return None
    output["content"]["condition"] = res

    state.inc_position()
    if state.get_token().val != ")":
        throw_parse_error("expected a ')'", state)

    state.inc_position()
    if state.get_token().val != "{":
        throw_parse_error("expected a '{'", state)

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None
    output["content"]["body"] = res

    state.inc_position()
    if state.get_token().val != "}":
        return None

    if state.peek_next_token().val == "elif":
        state.inc_position()
        res = parse_elif(state)
        if res is None:
            return None
        output["content"]["elif"] = res 
    if state.peek_next_token().val == "else":
        state.inc_position()
        res = parse_else(state)
        if res is None:
            return None
        output["content"]["else"] = res

    return output

def parse_elif(state):
    output = []
    small_output = {
        "context" : "elif",
        "content" : {
            "conditon" : None,
            "body": None
        }
    }
    if state.get_token().val != "elif":
        return None

    while state.get_token().val == "elif":
        state.inc_position()
        if state.get_token().val != "(":
            return None

        state.inc_position()
        res = parse_expression(state)
        if res is None:
            return None
        small_output["content"]["condition"] = res

        state.inc_position()
        if state.get_token().val != ")":
            return None

        state.inc_position()
        if state.get_token().val != "{":
            return None

        state.inc_position()
        res = parse_body(state)
        if res is None:
            return None
        small_output["content"]["body"] = res

        state.inc_position()
        if state.get_token().val != "}":
            return None

        output.append(copy.deepcopy(small_output))
        state.inc_position()

    state.dec_position()
    return output

def parse_else(state):
    output = {
        "context" : "else",
        "content" : {
            "body": None
        }
    }

    if state.get_token().val != "else":
        return None

    state.inc_position()
    if state.get_token().val != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None
    output["content"]["body"] = res

    state.inc_position()
    if state.get_token().val != "}":
        return None

    return output

def parse_variable_declaration(state):
    output = {
        "context": "variable_declaration",
        "content": {
            "size": None,
            "array-size": None,
            "id": None,
            "type": None,
            "init-sign": None,
            "init": None,
        }
    }
    if state.get_token().tag != "SIZE":
        return None
    output["content"]["size"] = state.get_token()

    state.inc_position()
    if state.get_token().val == "[":
        #expect an integer literal (VLA is not allowed in asca)
        state.inc_position()
        if state.get_token().tag != "INT":
            throw_parse_error("expected an integer literal", state)
            return None
        output["content"]["array-size"] = state.get_token()

        state.inc_position()
        if state.get_token().val != "]":
            return None
        state.inc_position()

    if state.get_token().tag != "ID":
        return None
    output["content"]["id"] = state.get_token()

    state.inc_position()
    if state.get_token().val != ":":
        return None

    state.inc_position()
    if state.get_token().tag == "ID":
        output["content"]["type"] = state.get_token()
    else:
        return None
    
    if state.peek_next_token().val == '=' or state.peek_next_token().val == ":=":
        state.inc_position()
        output["content"]["init-sign"] = state.get_token()
        state.inc_position()
        res = parse_expression(state)
        if res is not None:
            output["content"]["init"] = res
            return output
        return None
    else:
        return output

def parse_expression(state): 
    output = {
        "context": "expression",
        "content": None
    }
    res = parse_infix(state)
    if res is not None:
        output['content'] = res
        return output
    return None

#use pratt parsing because it's cool
def parse_infix(state, rbp = 0):
    if state.get_token().val == "(":
        state.inc_position()
        res = parse_infix(state)
        if res is None:
            return None
        state.inc_position()
        if state.get_token().val != ")":
            return None
    else:
        res = parse_value(state)
        if res is None:
            res = parse_unary(state)
            if res is None:
                return None
    left = res

    operator = state.peek_next_token()
    if get_priority(operator.val) is None:
        return left
    while get_priority(operator.val) > rbp:
        state.inc_position(2)
        if get_associativity(operator.val) == "left":
            res = parse_infix(state, get_priority(operator.val))
        else:
            res = parse_infix(state, get_priority(operator.val) - 1)
        if res is None:
            return None
        left = {"context":"infix_expression", "content":[left, operator, res]}
        operator = state.peek_next_token()
        if get_priority(operator.val) is None:
            return left
    return left

def get_priority(token):
    if token == "=" or\
       token == "+=" or\
       token == "-=" or\
       token == ":=":
        return 10
    elif token == "||" or\
         token == ":||":
        return 20
    elif token == "&&" or\
         token == ":&&":
        return 30
    elif token == ">=" or\
         token == ">"  or\
         token == "<=" or\
         token == "<"  or\
         token == "==" or\
         token == "!=" or\
         token == ":>=" or\
         token == ":>"  or\
         token == ":<=" or\
         token == ":<"  or\
         token == ":==" or\
         token == ":!=":
        return 40
    elif token == "+" or\
         token == "-" or\
         token == ":+" or\
         token == ":-":
        return 50
    elif token == "*" or\
         token == "/" or\
         token == ":*" or\
         token == ":/":
        return 60

def get_associativity(token):
    if token == "||":
        return "left"
    elif token == "&&":
        return "left"
    elif token == "+" or\
         token == "-" or\
         token == ":+" or\
         token == ":-":
        return "left"
    elif token == "*" or\
         token == "/" or\
         token == ":*" or\
         token == ":/":
        return "left"
    elif token == ">=" or\
         token == ">"  or\
         token == "<=" or\
         token == "<"  or\
         token == "==" or\
         token == "!=" or\
         token == ":>=" or\
         token == ":>"  or\
         token == ":<=" or\
         token == ":<"  or\
         token == ":==" or\
         token == ":!=":
        return "left"
    elif token == "="  or\
         token == "+=" or\
         token == "-=" or\
         token == "*=" or\
         token == "/=" or\
         token == ":="  or\
         token == ":+=" or\
         token == ":-=" or\
         token == ":*=" or\
         token == ":/=":
        return "right"

def parse_unary(state):
    output = {
            "context":"unary_expression",
            "content":[]
    }

    if state.get_token().val == "@" or\
       state.get_token().val == "-" or\
       state.get_token().val == "+" or\
       state.get_token().val == "!":
        output["content"].append(state.get_token())
    elif state.get_token().val == "$":
        output["content"].append(state.get_token())
        state.inc_position()
        if state.get_token().val != "(":
            return None
        state.inc_position()
        if state.get_token().tag != "SIZE":
            return None
        output["content"].append(state.get_token())
        state.inc_position()
        if state.get_token().val != ")":
            return None
    else:
        return None

    state.inc_position()
    res = parse_value(state)
    if res is None:
        res = parse_infix(state)
        if res is None:
            res = parse_unary(state)
            if res is None:
                return None
    output["content"].append(res) 

    return output

def parse_value(state):
    if state.get_token().tag == "ID":
        res = parse_identifier(state)
        if res is None:
            return None
        return res
    elif state.get_token().tag == "INT" or\
         state.get_token().tag == "FLOAT" or\
         state.get_token().tag == "BOOL" or\
         state.get_token().tag == "STRING" or\
         state.get_token().tag == "CHAR":
        return ({"context":"constant", "value":state.get_token()})
    else:
        return None

def parse_identifier(state):
    output = {
            "context": "identifier",
            "value":None,
            "array-value": None,
        }
    #if after it is a "(" then its a function call
    if state.peek_next_token().val == "(":
        res = parse_function_call(state)
        if res is None:
            return None
        return res
    
    output["value"] = state.get_token()
    if state.peek_next_token().val == "[":
        state.inc_position(2)
        res = parse_expression(state)
        if res is None:
            return None
        output["array-value"] = res
        state.inc_position()
        if state.get_token().val != "]":
            return None
    return output

def parse_function_call(state):
    output = {
        "context": "function_call",
        "value": None,
        "parameters": []
    }

    if state.get_token().tag == "ID":
        output["value"] = state.get_token()
    else:
        return None

    state.inc_position()
    if state.get_token().val != "(":
        state.dec_position()
        return None

    state.inc_position()
    while True:
        if state.get_token().val == ")":
            break
        res = parse_expression(state)
        if res is None:
            return None
        output["parameters"].append(res)
        state.inc_position()
        if state.get_token().val == ",":
            state.inc_position()
            if state.get_token().val == ")":
                return None

    return output

def parse_return(state):
    output = {
        "context" : "return",
        "content" : {
            "keyword": None,
            "value": None
        }
    }
    if state.get_token().val != "return":
        return None
    output["content"]["keyword"] = state.get_token()
    state.inc_position()
    res = parse_expression(state)
    if res is None:
        return None
    output["content"]["value"] = res
    return output

def parse_break(state):
    output = {
        "context": "break",
        "value": None
    }
    if state.get_token().val != "break":
        return None
    output["value"] = state.get_token()
    return output

def parse_continue(state):
    output = {
        "context": "continue",
        "value": None
    }
    if state.get_token().val != "continue":
        return None
    output["value"] = state.get_token()
    return output

def parse_global(state):
    output = {
        "context" : "global",
        "content" : {
            "keyword": None,
            "value": None
        }
    }
    if state.get_token().val != "global":
        return None
    output["content"]["keyword"] = state.get_token()
    state.inc_position()
    if state.get_token().tag != "ID":
        return None
    output["content"]["value"] = state.get_token()
    return output

def parse_extern(state):
    output = {
        "context" : "extern",
        "content" : {
            "id": None,
            "parameters": [],
            "type": None
        }
    }
    if state.get_token().val != "extern":
        return None

    state.inc_position()
    if state.get_token().tag != "ID":
        return None
    output["content"]["id"] = state.get_token()

    state.inc_position()
    if state.get_token().val != "(":
        return None

    state.inc_position()
    while True:
        template = {
                "expression": None,
                "is_floating_point": False
        }
        if state.get_token().val == ")":
            break
        if state.get_token().val == ":": #check for floating-point parameters
            template["is_floating_point"] = True
            state.inc_position()
        res = parse_variable_declaration(state)
        if res is None:
            return None
        template["expression"] = res 
        output["content"]["parameters"].append(template)
        state.inc_position()
        if state.get_token().val == ",":
            state.inc_position()
            if state.get_token().val == ")":
                return None

    state.inc_position()
    if state.get_token().val != ":":
        return None

    state.inc_position()
    if state.get_token().tag != "ID":
        return None
    output["content"]["type"] = state.get_token()
    return output

def throw_parse_error(msg, state):
    sys.stderr.write("syntax_error: %s at line %s: %s \n" % (msg, state.get_token().line, state.get_token().char))
    state.is_error = True

def throw_semicolon_error(state):
    sys.stderr.write("syntax_error: expected a semicolon at line %s: %s \n" % (state.get_token().line, state.get_token().char+len(state.get_token().val)))
    state.is_error = True    

def throw_eof_error(state):
    sys.stderr.write("syntax_error: unexpected EOF\n")
    state.is_error = True
