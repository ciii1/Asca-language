import sys
import re
import preprocessor

class token():
    def __init__ (self, token, tag, char, line):
        self.token = token
        self.tag = tag
        self.char = char
        self.line = line

    def get_line(self):
        return self.line
    def get_char(self):
        return self.char

    def get_token(self):
        return self.token
    def get_tag(self):
        return self.tag

def lex(characters, token_exprs):
    characters = preprocessor.preprocess(characters)
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
            sys.stderr.write('Unexpected character: %s at line %s: %s \n' % (characters[pos], line, char+1))
            sys.exit(1)
        else:
            if characters[pos] == "\n":
                line += 1
                char_before_line = match.end(0)
            pos = match.end(0)
            char = match.end(0) - char_before_line
    
    return tokens