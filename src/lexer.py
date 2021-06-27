import sys
import re
import preprocessor

class token():
    def __init__ (self, val, tag, char, line):
        self.val = val
        self.tag = tag
        self.char = char
        self.line = line

def lex(characters, token_exprs):
    pos = 0

    line = 1
    char = 0
    char_before_line = 0

    tokens = []
    while pos < len(characters):
        match = None
        for token_expr in token_exprs:
            pattern, tag = token_expr
            regex = re.compile(pattern)
            match = regex.match(characters, pos)
            if match:
                text = match.group(0)
                if tag:
                    tokens.append(token(text, tag, char, line))
                break
        if not match:
            sys.stderr.write('lexical_error: unexpected character: %s at line %s: %s \n' % (characters[pos], line, char+1))
            #sys.exit(1)
        else:
            if characters[pos] == "\n":
                line += 1
                char_before_line = match.end(0)
            pos = match.end(0)
            char = match.end(0) - char_before_line
    
    return tokens
