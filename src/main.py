import preprocessor
import lexer
import parser
import analyzer
import sys

def init_tokens(input):

    RESERVED     = 'RESERVED'
    INT          = 'INT'
    FLOAT        = 'FLOAT'
    BOOL         = 'BOOL'
    CHAR         = 'CHAR'
    ID           = 'ID'
    SIZE         = 'SIZE'
    STRING       = 'STRING'
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
        (r'@',                              OPERATOR),
        (r'\$',                             OPERATOR),
        (r'!',                              OPERATOR),
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

if len(sys.argv) > 1:
    f = open(sys.argv[1])
    code = preprocessor.preprocess(f.read())
    tokens = init_tokens(code)
    res = parser.parse(tokens)
    if res.is_error:
        print("Compilation canceled due to previous error(s)")
    else:
        print(res.get_output())
else:
    code = input("@>")
    while code:
        code = preprocessor.preprocess(code)
        tokens = init_tokens(code)
        res = parser.parse(tokens)
        if not res.is_error:
            #print(res.get_output())
            
            analyzer.analyze(res.get_output())
        code = input("@>")  
