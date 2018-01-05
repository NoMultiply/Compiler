import ply.lex as lex

reserved = {
    'break': 'BREAK',
    'case': 'CASE',
    'char': 'CHAR',
    'const': 'CONST',
    'continue': 'CONTINUE',
    'default': 'DEFAULT',
    'double': 'DOUBLE',
    'else': 'ELSE',
    'extern': 'EXTERN',
    'for': 'FOR',
    'if': 'IF',
    'int': 'INT',
    'return': 'RETURN',
    'struct': 'STRUCT',
    'switch': 'SWITCH',
    'typedef': 'TYPEDEF',
    'void': 'VOID',
    'unsigned': 'UNSIGNED',
    'while': 'WHILE',
}

tokens = [
    'STRING_LITERAL',
    'NUMBER',
    'IDENTIFIER',
    'CHARACTER',
    'ELLIPSIS',
    'INC_OP',
    'DEC_OP',
    'PTR_OP',
    'AND_OP',
    'OR_OP',
    'LE_OP',
    'GE_OP',
    'EQ_OP',
    'NE_OP',
] + list(reserved.values())

literals = r";{}(),:=[]&!+-*/%<>^|?"
t_ELLIPSIS = r'\.\.\.'
t_INC_OP = r'\+\+'
t_DEC_OP = r'\-\-'
t_PTR_OP = r'\-\>'
t_AND_OP = r'\&\&'
t_OR_OP = r'\|\|'
t_LE_OP = r'\<\='
t_GE_OP = r'\>\='
t_EQ_OP = r'\=\='
t_NE_OP = r'\!\='
t_STRING_LITERAL = r'"(\.|[^\"])*"'
t_CHARACTER = r'\'(\\.|[^\\\'])+\''

t_ignore = ' \t\v\n\f'

def t_DOUBLE(t):
    r"""\d+.\d+"""
    t.value = ('double', t.value)
    return t

def t_NUMBER(t):
    r"""\d+"""
    t.value = ('int', int(t.value))
    return t

def t_IDENTIFIER(t):
    r"""[a-zA-Z_][a-zA-Z_0-9]*"""
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex()
