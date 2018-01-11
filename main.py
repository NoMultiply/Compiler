from lex import lexer
from yacc import YaccParser, ParseError
from Compiler import parse_translation_unit
from Precompiler import precompile

file_in = open('test.c', 'r')
data = precompile(file_in.readlines())

#lexer.input(data)

# while True:
#     tok = lexer.token()
#     if not tok:
#         break
#     print(tok)
#

parser = YaccParser()
try:
    result = parser.parser.parse(data, lexer=lexer)
    print(result)
    assert result[0] == 'translation_unit'
    data = parse_translation_unit(result)
    print()
    print(data)
    file_out = open('test.ll', 'w')
    file_out.write(data)
except ParseError as e:
    print(data[:e.pos])
    print(data[e.pos:e.pos + 10])


