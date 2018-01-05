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
    'sizeof': 'SIZEOF',
    'static': 'STATIC',
    'auto': 'AUTO',
    'register': 'REGISTER',
    'short': 'SHORT',
    'long': 'LONG',
    'float': 'FLOAT',
    'signed': 'SIGNED',
    'union': 'UNION',
    'enum': 'ENUM',
    'volatile': 'VOLATILE',
    'do': 'DO',
    'goto': 'GOTO',
}

tokens = [
    'STRING_LITERAL',
    'IDENTIFIER',
    'ELLIPSIS',
    'CONSTANT',
    'INC_OP',
    'DEC_OP',
    'PTR_OP',
    'AND_OP',
    'OR_OP',
    'LE_OP',
    'GE_OP',
    'EQ_OP',
    'NE_OP',
    'LEFT_OP',
    'RIGHT_OP',
    'MUL_ASSIGN',
    'DIV_ASSIGN',
    'MOD_ASSIGN',
    'ADD_ASSIGN',
    'SUB_ASSIGN',
    'LEFT_ASSIGN',
    'RIGHT_ASSIGN',
    'AND_ASSIGN',
    'XOR_ASSIGN',
    'OR_ASSIGN',
    'TYPE_NAME'
] + list(reserved.values())


literals = r";{}(),:=[]&!+-*/%<>^|?."
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
t_LEFT_OP = r'\<\<'
t_RIGHT_OP = r'\>\>'
t_STRING_LITERAL = r'"(\.|[^\"])*"'
t_MUL_ASSIGN = r'\*\='
t_DIV_ASSIGN = r'\/\='
t_MOD_ASSIGN = r'\%\='
t_ADD_ASSIGN = r'\+\='
t_SUB_ASSIGN = r'\-\='
t_LEFT_ASSIGN = r'\<\<\='
t_RIGHT_ASSIGN = r'\>\>\='
t_AND_ASSIGN = r'\&\='
t_XOR_ASSIGN = r'\^\='
t_OR_ASSIGN = r'\|\='


t_ignore = ' \t\v\n\f'

def t_CHARACTER(t):
    r"""\'(\\.|[^\\\'])+\'"""
    t.value = ('char', t.value)
    t.type = 'CONSTANT'
    return t

def t_DOUBLE(t):
    r"""\d+.\d+"""
    t.value = ('double', t.value)
    t.type = 'CONSTANT'
    return t


def t_NUMBER(t):
    r"""\d+"""
    t.value = ('int', int(t.value))
    t.type = 'CONSTANT'
    return t


type_list = []


def t_IDENTIFIER(t):
    r"""[a-zA-Z_][a-zA-Z_0-9]*"""
    if t.value in reserved:
        t.type = reserved.get(t.value, 'IDENTIFIER')
    elif t.value in type_list:
        t.type = 'TYPE_NAME'
    t.value = ('id', t.value)
    return t


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex()
