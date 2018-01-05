import ply.yacc as yacc
from lex import tokens

start = 'translation_unit'


def p_translation_unit(p):
    """translation_unit : macro_expression function_definition"""
    p[0] = ('translation_unit', *p[1:])


def p_marco_expression(p):
    """macro_expression : INCLUDE STRING_LITERAL"""
    p[0] = ('macro_expression', *p[1:])


def p_function_definition(p):
    """function_definition : INT IDENTIFIER '(' ')' compound_statement"""
    p[0] = ('function_definition', *p[1:])


def p_compound_statement(p):
    """compound_statement : '{' statement_list '}'"""
    p[0] = ('compound_statement', *p[1:])


def p_statement_list(p):
    """statement_list : statement
                      | statement_list statement"""
    p[0] = ('statement_list', *p[1:])


def p_statement(p):
    """statement : expression_statement"""
    p[0] = ('statement', *p[1:])


def p_expression_statement(p):
    """expression_statement : expression ';'"""
    p[0] = ('expression_statement', *p[1:])


def p_expression(p):
    """expression : postfix_expression
                  | return_expression"""
    p[0] = ('expression', *p[1:])


def p_return_expression(p):
    """return_expression : RETURN NUMBER"""
    p[0] = ('return_expression', *p[1:])


def p_primary_expression(p):
    """primary_expression : IDENTIFIER
                          | NUMBER
                          | STRING_LITERAL"""
    p[0] = ('primary_expression', *p[1:])


def p_postfix_expression(p):
    """postfix_expression : primary_expression
                         | postfix_expression '(' ')'
                         | postfix_expression '(' argument_expression_list ')'"""
    p[0] = ('postfix_expression', *p[1:])


def p_argument_expression_list(p):
    """argument_expression_list : primary_expression
                               | argument_expression_list ',' primary_expression"""
    p[0] = ('argument_expression_list', *p[1:])


def p_error(p):
    print("Syntax error in input!")


parser = yacc.yacc()