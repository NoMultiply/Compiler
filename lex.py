import ply.lex as lex

reserved = {
   'int' : 'INT',
   'return' : 'RETURN'
}

tokens = [
    'STRING_LITERAL',
    'INCLUDE',
    'NUMBER',
    'IDENTIFIER',
] + list(reserved.values())

literals = r";{}()"

t_INCLUDE = r'\#include'
t_STRING_LITERAL = r'"(\.|[^\"])*"'

t_ignore = ' \t\v\n\f'


def t_NUMBER(t):
    r"""\d+"""
    t.value = int(t.value)
    return t


def t_IDENTIFIER(t):
    r"""[a-zA-Z_][a-zA-Z_0-9]*"""
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex()
