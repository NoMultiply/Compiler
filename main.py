from lex import lexer
from yacc import parser
from Compiler import parse_translation_unit

file_in = open('test.c', 'r')

data = file_in.read()
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
file_out = open('test.ll', 'w')
data = parse_translation_unit(result)
print(data)
file_out.write(data)
