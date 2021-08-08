import preprocessor
import lexer
import parser
import analyzer
import generator
import sys
import subprocess

def init_tokens(input):
    token_exprs = [
        (r'\n',                                             None),
        (r'[ \t]+',                                         None),
        (r'#[^\n]*',                                        None),
        (r'\[',                                             'RESERVED'),
        (r'\]',                                             'RESERVED'),
        (r'\;',                                             'RESERVED'),
        (r',',                                              'RESERVED'),
        (r'\(',                                             'RESERVED'),
        (r'\)',                                             'RESERVED'),
        (r'\{',                                             'RESERVED'),
        (r'\}',                                             'RESERVED'),
        (r'@',                                              'UNARY_OPERATOR'),
        (r'\$',                                             'UNARY_OPERATOR'),
        (r'!',                                              'UNARY_OPERATOR'),
        (r'==',                                             'RELATIONAL_OPERATOR'),
        (r'<=',                                             'RELATIONAL_OPERATOR'),
        (r'<',                                              'RELATIONAL_OPERATOR'),
        (r'>=',                                             'RELATIONAL_OPERATOR'),
        (r'>',                                              'RELATIONAL_OPERATOR'),
        (r'!=',                                             'RELATIONAL_OPERATOR'),
        (r':==',                                            'PRECISE_RELATIONAL_OPERATOR'),
        (r':<=',                                            'PRECISE_RELATIONAL_OPERATOR'),
        (r':<',                                             'PRECISE_RELATIONAL_OPERATOR'),
        (r':>=',                                            'PRECISE_RELATIONAL_OPERATOR'),
        (r':>',                                             'PRECISE_RELATIONAL_OPERATOR'),
        (r':!=',                                            'PRECISE_RELATIONAL_OPERATOR'),
        (r'&&',                                             'CONDITIONAL_OPERATOR'),
        (r'\|\|',                                           'CONDITIONAL_OPERATOR'),
        (r':&&',                                            'PRECISE_CONDITIONAL_OPERATOR'),
        (r':\|\|',                                          'PRECISE_CONDITIONAL_OPERATOR'),
        (r'=',                                              'ASSIGNMENT_OPERATOR'),
        (r'\+=',                                            'ASSIGNMENT_OPERATOR'),
        (r'\-=',                                            'ASSIGNMENT_OPERATOR'), 
        (r':=',                                             'PRECISE_ASSIGNMENT_OPERATOR'),
        (r'\+',                                             'ARITHMETICAL_OPERATOR'),
        (r'-',                                              'ARITHMETICAL_OPERATOR'),
        (r'\*',                                             'ARITHMETICAL_OPERATOR'),
        (r'/',                                              'ARITHMETICAL_OPERATOR'),
        (r':\+',                                            'PRECISE_ARITHMETICAL_OPERATOR'),
        (r':-',                                             'PRECISE_ARITHMETICAL_OPERATOR'),
        (r':\*',                                            'PRECISE_ARITHMETICAL_OPERATOR'),
        (r':/',                                             'PRECISE_ARITHMETICAL_OPERATOR'),
        (r'\:',                                             'RESERVED'),
        (r'(?<![A-Za-z0-9_])type(?![A-Za-z0-9_])',          'RESERVED'),
        (r'(?<![A-Za-z0-9_])func(?![A-Za-z0-9_])',          'RESERVED'),
        (r'(?<![A-Za-z0-9_])if(?![A-Za-z0-9_])',            'RESERVED'),
        (r'(?<![A-Za-z0-9_])elif(?![A-Za-z0-9_])',          'RESERVED'),
        (r'(?<![A-Za-z0-9_])else(?![A-Za-z0-9_])',          'RESERVED'),
        (r'(?<![A-Za-z0-9_])while(?![A-Za-z0-9_])',         'RESERVED'),
        (r'(?<![A-Za-z0-9_])for(?![A-Za-z0-9_])',           'RESERVED'),
        (r'(?<![A-Za-z0-9_])break(?![A-Za-z0-9_])',         'RESERVED'),
        (r'(?<![A-Za-z0-9_])continue(?![A-Za-z0-9_])',      'RESERVED'),
        (r'(?<![A-Za-z0-9_])return(?![A-Za-z0-9_])',        'RESERVED'),
        (r'(?<![A-Za-z0-9_])global(?![A-Za-z0-9_])',        'RESERVED'),
        (r'(?<![A-Za-z0-9_])extern(?![A-Za-z0-9_])',        'RESERVED'),
        (r'[0-9]+\.[0-9]+',                                 'FLOAT'),
        (r'(?<!\\)\"(.*?)(?<!\\)\"',                        'STRING'),
        (r'(?<!\\)\'(\\.|.)(?<!\\)\'',                      'CHAR'),
        (r"(?<![A-Za-z0-9_])true(?![A-Za-z0-9_])|(?<![A-Za-z0-9_])false(?![A-Za-z0-9_])",   'BOOL'),
        (r'(?<![A-Za-z0-9_])qword(?![A-Za-z0-9_])',          'SIZE'),
        (r'(?<![A-Za-z0-9_])dword(?![A-Za-z0-9_])',          'SIZE'),
        (r'(?<![A-Za-z0-9_])word(?![A-Za-z0-9_])',           'SIZE'),
        (r'(?<![A-Za-z0-9_])byte(?![A-Za-z0-9_])',           'SIZE'),
        (r'[0-9]+',                                          'INT'),
        (r'[_A-Za-z][A-Za-z0-9_]*',                          'ID')
    ]
    return lexer.lex(input, token_exprs)

if len(sys.argv) > 1:
    f = open(sys.argv[1])
    print("compiling", sys.argv[1])
    code = preprocessor.preprocess(f.read())
    tokens = init_tokens(code)
    Parser = parser.parse(tokens)
    if Parser.is_error:
        print("compilation canceled due to previous error(s)")
    else:
        Analyzer = analyzer.analyze(Parser.get_output())
        if Analyzer.is_error:
            print("compilation canceled due to previous error(s)")
        else:
            output = generator.generate(Parser.get_output(), Analyzer.function_list)
            fp = open("a.asm", "w")
            fp.write(output)
            fp.close()
            subprocess.call(["nasm", "-felf64", "a.asm"])
            #subprocess.call(["gcc", "-no-pie", "a.o"])
            #subprocess.call(["rm", "a.asm"])
            #subprocess.call(["rm", "a.o"])
            print("compilation completed, output: a.o \n (i) If you're using gcc then link with gcc -no-pie a.o")
else:
    print("Asca interactive syntax and semantic tester (for debugging purpose)")
    print("(i) the code you type wouldn't be compiled \n")
    code = input("@>")
    while code:
        code = preprocessor.preprocess(code)
        tokens = init_tokens(code)
        Parser = parser.parse(tokens)
        if not Parser.is_error:
            Analyzer = analyzer.analyze(Parser.get_output())
        code = input("@>")  
