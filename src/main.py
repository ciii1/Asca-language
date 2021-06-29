import preprocessor
import lexer
import parser
import analyzer
import sys

def init_tokens(input):

    ARITHMETICAL_OPERATOR = 'ARITHMETIC_OPERATOR'
    CONDITIONAL_OPERATOR = 'CONDITIONAL_OPERATOR'
    RELATIONAL_OPERATOR = 'RELATIONAL_OPERATOR'

    
    token_exprs = [
        (r'\n',                             None),
        (r'[ \t]+',                         None),
        (r'#[^\n]*',                        None),
        (r'\[',                             'RESERVED'),
        (r'\]',                             'RESERVED'),
        (r'\:',                             'RESERVED'),
        (r'\;',                             'RESERVED'),
        (r',',                              'RESERVED'),
        (r'\(',                             'RESERVED'),
        (r'\)',                             'RESERVED'),
        (r'\{',                             'RESERVED'),
        (r'\}',                             'RESERVED'),
        (r'@',                              'UNARY_OPERATOR'),
        (r'\$',                             'UNARY_OPERATOR'),
        (r'!',                              'UNARY_OPERATOR'),
        (r'==',                             'RELATIONAL_OPERATOR'),
        (r'<=',                             'RELATIONAL_OPERATOR'),
        (r'<',                              'RELATIONAL_OPERATOR'),
        (r'>=',                             'RELATIONAL_OPERATOR'),
        (r'>',                              'RELATIONAL_OPERATOR'),
        (r'!=',                             'RELATIONAL_OPERATOR'),
        (r'&&',                             'CONDITIONAL_OPERATOR'),
        (r'\|\|',                           'CONDITIONAL_OPERATOR'),
        (r'=',                              'ASSIGNMENT_OPERATOR'),
        (r'\+=',                            'ASSIGNMENT_OPERATOR'),
        (r'\-=',                            'ASSIGNMENT_OPERATOR'),
        (r'\/=',                            'ASSIGNMENT_OPERATOR'),
        (r'\*=',                            'ASSIGNMENT_OPERATOR'),
        (r'\+',                             'ARITHMETICAL_OPERATOR'),
        (r'-',                              'ARITHMETICAL_OPERATOR'),
        (r'\*',                             'ARITHMETICAL_OPERATOR'),
        (r'/',                              'ARITHMETICAL_OPERATOR'),
        (r'type',                           'RESERVED'),
        (r'func',                           'RESERVED'),
        (r'if',                             'RESERVED'),
        (r'elif',                           'RESERVED'),
        (r'else',                           'RESERVED'),
        (r'while',                          'RESERVED'),
        (r'for',                            'RESERVED'),
        (r'break',                          'RESERVED'),
        (r'continue',                       'RESERVED'),
        (r'return',                         'RESERVED'),
        (r'\".*?\"',                        'STRING'),
        (r'[0-9]+\.[0-9]+',                 'FLOAT'),
        (r'\'.*?\'',                        'CHAR'),
        (r'true|false',                     'BOOL'),
        (r'qword',                          'SIZE'),
        (r'dword',                          'SIZE'),
        (r'word',                           'SIZE'),
        (r'byte',                           'SIZE'),
        (r'[0-9]+',                         'INT'),
        (r'[_A-Za-z][A-Za-z0-9_]*',         'ID')
    ]

    return lexer.lex(input, token_exprs)

if len(sys.argv) > 1:
    f = open(sys.argv[1])
    print("compiling", sys.argv[1])
    code = preprocessor.preprocess(f.read())
    tokens = init_tokens(code)
    res = parser.parse(tokens)
    if res.is_error:
        print("compilation canceled due to previous error(s)")
    else:
        res = analyzer.analyze(res.get_output())
        if res.is_error:
            print("compilation canceled due to previous error(s)")
        else:
            print("compilation completed with no error")
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
