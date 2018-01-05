from lex import lexer
#from yacc import parser
# from Compiler import parse_translation_unit

file = open('main.c', 'r')
# file1 = open('result.txt', 'w')
data = file.read()
lexer.input(data)
while True:
    tok = lexer.token()
    if not tok:
        break
    print(tok)
    # file1.write(str(tok))
# file1.close()
# result = parser.parse(data, lexer=lexer)
# print(result)
# assert result[0] == 'translation_unit'
# parse_translation_unit(result)