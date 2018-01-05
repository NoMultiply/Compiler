from lex import lexer
from yacc import parser
from Compiler import parse_translation_unit

file = open('test.c', 'r')

data = file.read()
# lexer.input(data)
#
# while True:
#     tok = lexer.token()
#     if not tok:
#         break
#     print(tok)

result = parser.parse(data, lexer=lexer)
print(result)
assert result[0] == 'translation_unit'
parse_translation_unit(result)