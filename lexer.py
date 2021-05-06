import sys
import re

[[[{'type': 'int', 'value': '33'}, {'type': 'operator', 'value': '*'}, [[{'type': 'int', 'value': '3'}]], '+', [{'type': 'int', 'value': '2'}, {'type': 'operator', 'value': '*'}, {'type': 'int', 'value': '3'}]]]] 

def lex(characters, token_exprs):
    pos = 0
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
                    token = (text, tag)
                    tokens.append(token)
                break
        if not match:
            sys.stderr.write('Illegal character: %s at char %s\n' % (characters[pos], pos+1))
            sys.exit(1)
        else:
            pos = match.end(0)
    return tokens