import lexer
import sys

#TODO
#REWRITE THIS THING IN ASCA WHEN THE ENTIRE COMPILER IS DONE

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
    if state.get_token().val != ";":
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
    if state.get_token().val != ";":
        state.dec_position()
        throw_semicolon_error(state)
    return state    

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
                        #catch_not_match(state)
                        #state.inc_position()
                        #continue

        state = res
        output.append(res.get_output())
        state.inc_position()

    state.set_output(output)
    return state

def catch_not_match(state):
    if state.get_token().val != None:
        if state.get_token().tag == "STRING":
            throw_parse_error("unexpected token with type 'string'",state)
        else:
            throw_parse_error("unexpected token: %s " % state.get_token().val, state)
    else:
        sys.stderr.write("syntax_error: unexpected EOF\n")

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
        state.set_output(output)
        return state        

    state.inc_position()
    if state.get_token().tag != "SIZE":
        return None
    output["content"]["min_size"] = state.get_token()

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
        if state.get_token().val == ")":
            break
        res = parse_variable_declaration(state, is_arg=True)
        if res is None:
            return None
        state = res
        output["content"]["parameters"].append(state.get_output())
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

    state = res
    output["content"]["body"] = res.get_output()

    state.inc_position()
    if state.get_token().val != "}":
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
    if state.get_token().val != "while":
        return None

    state.inc_position()
    if state.get_token().val != "(":
        return None

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        return None
    state = res
    output["content"]["condition"] = res.get_output()

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

    state = res
    output["content"]["body"] = res.get_output()

    state.inc_position()
    if state.get_token().val != "}":
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
    if state.get_token().val != "for":
        return None

    state.inc_position()
    if state.get_token().val != "(":
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
    if state.get_token().val != ")":
        return None

    state.inc_position()
    if state.get_token().val != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None

    state = res
    output["body"] = res.get_output()

    state.inc_position()
    if state.get_token().val != "}":
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
    if state.get_token().val != "if":
        return None

    state.inc_position()
    if state.get_token().val != "(":
        return None

    state.inc_position()
    res = parse_expression(state)
    if res is None:
        return None
    state = res
    output["content"]["condition"] = res.get_output()

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
    state = res
    output["content"]["body"] = res.get_output()

    state.inc_position()
    if state.get_token().val != "}":
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
        state = res
        small_output["content"]["condition"] = res.get_output()

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

        state = res
        small_output["content"]["body"] = res.get_output()

        state.inc_position()
        if state.get_token().val != "}":
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

    if state.get_token().val != "else":
        return None

    state.inc_position()
    if state.get_token().val != "{":
        return None

    state.inc_position()
    res = parse_body(state)
    if res is None:
        return None
    state = res
    output["content"]["body"] = res.get_output()

    state.inc_position()
    if state.get_token().val != "}":
        return None

    state.set_output(output)
    return state

def parse_variable_declaration(state, is_arg=False):
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
    if state.get_token().tag != "SIZE":
        return None

    output["content"]["size"] = state.get_token()

    state.inc_position()
    if state.get_token().val == "[":
        #array is not allowed in argument
        if is_arg:
            return None
        #expect a integer literal (VLA is not allowed in asca)
        state.inc_position()
        if state.get_token().tag != "INT":
            throw_parse_error("expected an integer literal", state)

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
    
    if state.peek_next_token().val == '=':
        #can't assign in argument (currently, parameters cant have default values. I'll consider adding it in future version tho)
        if is_arg:
            return None
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
    if state.get_token().val == "(":
        state.inc_position()
        res = parse_expression_recursive(state)
        if res is None:
            return None
        res.inc_position()
        if res.get_token().val != ")":
            return None
    else:
        res = parse_value(state)
        if res is None:
            res = parse_unary(state)
            if res is None:
                return None
    state = res
    left = res.get_output()

    operator = state.peek_next_token().val
    if get_priority(operator) is None:
        state.set_output(left)
        return state

    while get_priority(operator) > rbp:
        state.inc_position()
        operator_token = state.get_token()
        operator = state.get_token().val
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
        left = [left, operator_token, res.get_output()]

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
    if state.get_token().val == "@" or\
       state.get_token().val == "-" or\
       state.get_token().val == "+":
        output.append(state.get_token())
    elif state.get_token().val == "$":
        output.append(state.get_token())
        state.inc_position()
        if state.get_token().val != "(":
            return None
        state.inc_position()
        if state.get_token().tag != "SIZE":
            return None
        state.inc_position()
        if state.get_token().val != ")":
            return None
    else:
        return None

    state.inc_position()
    res = parse_value(state)
    if res is None:
        res = parse_expression_recursive(state)
        if res is None:
            res = parse_unary(state)
            if res is None:
                return None
    state = res
    output.append(res.get_output()) 

    state.set_output(output)
    return state

def parse_value(state):
    token_type = state.get_token().tag
    value = state.get_token()
    if token_type == "STRING":
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
    elif token_type == "ID":
        res = parse_identifier(state)
        if res is not None:
            state = res
            #no need to set output
        else:
            return None
    elif token_type == "INT" or\
         token_type == "FLOAT" or\
         token_type == "BOOL":
        state.set_output(value)
    else:
        return None
    return state

def parse_identifier(state):
    output = {
            "type": "identifier",
            "value":None,
            "array-value": None,
        }
    output["value"] = state.get_token()
    if state.peek_next_token().val == "(":
        res = parse_function_call(state)
        if res is None:
            return None
        state = res
        return state
    elif state.peek_next_token().val == "[":
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
        if state.get_token().val != "]":
            throw_parse_error("expected a closing ']'", state)
            return None

        state.set_output(output)
        return state
    else:
        state.set_output(output)
        return state

def parse_string(state):
    token = state.get_token()
    #if it contains 0 char (specified 2 here cos the '"' is counted)
    if len(token.val) == 2:
        throw_parse_error("a string literal cannot be empty", state)
        return None
    
    state.set_output(token)
    return state

def parse_char(state):
    token = state.get_token()
    #if it contains 2 or more character
    if len(token.val) > 3:
        throw_parse_error("a char literal can only contain 1 character", state)
        return None
    #if it contains 0 char
    elif len(token.val) == 2:
        throw_parse_error("a char literal cannot be empty", state)
        return None

    state.set_output(token)
    return state

def parse_function_call(state):
    output = {
        "type": "function_call",
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
        state = res
        output["parameters"].append(state.get_output())
        state.inc_position()
        if state.get_token().val == ",":
            state.inc_position()
            if state.get_token().val == ")":
                return None

    state.set_output(output)
    return state

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
    state = res
    output["content"]["value"] = res.get_output()
    state.set_output(output)
    return state

def parse_break(state):
    output = {
        "context": "break",
        "value": None
    }
    if state.get_token().val != "break":
        return None

    output["value"] = state.get_token()

    state.set_output(output)
    return state

def parse_continue(state):
    output = {
        "context": "continue",
        "value": None
    }
    if state.get_token().val != "continue":
        return None

    output["value"] = state.get_token()
        
    state.set_output(output)
    return state

def throw_parse_error(msg, state):
    sys.stderr.write("syntax_error: %s at line %s: %s \n" % (msg, state.get_token().line, state.get_token().char))
    state.is_error = True

def throw_semicolon_error(state):
    sys.stderr.write("syntax_error: expected a semicolon at line %s: %s \n" % (state.get_token().line, state.get_token().char+len(state.get_token().val)))
    state.is_error = True    
