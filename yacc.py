import ply.yacc as yacc
from lex import tokens, type_list

from Compiler import parse_pointer

def deal_direct_declarator(exp):
    if len(exp) == 2:
        return exp[1]

def deal_declarator(exp):
    if len(exp) == 2:
        return deal_direct_declarator(exp[1])
    else:
        return ('pointer', parse_pointer(exp[1]), deal_direct_declarator(exp[2]))

def deal_init_declarator(exp):
    return deal_declarator(exp[1])

def deal_init_declarator_list(exp):
    result = []
    for i in range(1, len(exp)):
        if exp[i][0] == 'init_declarator_list':
            result.extend(deal_init_declarator_list(exp[i]))
        elif exp[i][0] == 'init_declarator':
            result.append(deal_init_declarator(exp[i]))
    return result


def deal_declaration_specifiers(exp):
    if len(exp) == 3 and exp[1][0] == 'storage_class_specifier':
        return exp[1][1][1]

def deal_declaration(exp):
    declaration_specifiers = deal_declaration_specifiers(exp[1])
    if len(exp) == 4:
        init_declarator_list = deal_init_declarator_list(exp[2])
        if declaration_specifiers == 'typedef':
            for init_declarator in init_declarator_list:
                type_list.append(init_declarator[1])


class ParseError(Exception):
    def __init__(self, pos):
        self.pos = pos


class YaccParser(object):
    def __init__(self):
        self.tokens = tokens
        self.parser = yacc.yacc(module=self,
                                debug=False,
                                start='translation_unit')

    # 后缀表达式：
    def p_postfix_expression(self, p):
        """	postfix_expression : primary_expression
                               | postfix_expression '[' expression ']'
                               | postfix_expression '(' ')'
                               | postfix_expression '(' argument_expression_list ')'
                               | postfix_expression '.' IDENTIFIER
                               | postfix_expression PTR_OP IDENTIFIER
                               | postfix_expression INC_OP
                               | postfix_expression DEC_OP
        """
        p[0] = ('postfix_expression', *p[1:])

    # 基本表达式→标识符  | 常量 | 字符串常量 |  '('表达式')'
    def p_primary_expression(self, p):
        """	primary_expression : IDENTIFIER
                               | CONSTANT
                               | STRING_LITERAL
                               | '(' expression ')'
        """
        p[0] = ('primary_expression', *p[1:])

    # 参数表达式列表: 赋值表达式 | 参数表达式列表','赋值表达式
    def p_argument_expression_list(self, p):
        """ argument_expression_list : assignment_expression
                                     | argument_expression_list ',' assignment_expression
        """
        p[0] = ('argument_expression_list', *p[1:])

    # 一元表达式：后缀表达式 | INC运算一元表达式 | DEC运算一元表达式 | 一元运算符将表达式 |  结构体变量的一元表达式 |  结构体变量的'(' 类型名称 ')'
    def p_unary_expression(self, p):
        """ unary_expression : postfix_expression
                             | INC_OP unary_expression
                             | DEC_OP unary_expression
                             | unary_operator cast_expression
                             | SIZEOF unary_expression
                             | SIZEOF '(' type_name ')'
        """
        p[0] = ('unary_expression', *p[1:])

    # 一元运算符
    def p_unary_operator(self, p):
        """ unary_operator : '&'
                           | '*'
                           | '+'
                           | '-'
                           | '~'
                           | '!'
        """
        p[0] = ('unary_operator', *p[1:])

    # 强制转换表达式：一元表达式  |  '(' 类型名称 ')'强制转换表达式
    def p_cast_expression(self, p):
        """ cast_expression : unary_expression
                            | '(' type_name ')' cast_expression
        """
        p[0] = ('cast_expression', *p[1:])

    # 乘法表达式：强制转换表达式 | 乘法表达式'*'强制转换表达式 | 乘法表达式'/'强制转换表达式 | 乘法表达式'%'强制转换表达式
    def p_multiplicative_expression(self, p):
        """	multiplicative_expression : cast_expression
                                      | multiplicative_expression '*' cast_expression
                                      | multiplicative_expression '/' cast_expression
                                      | multiplicative_expression '%' cast_expression
        """
        p[0] = ('multiplicative_expression', *p[1:])

    # 加法表达式：乘法表达式 | 加法表达式'+'乘法表达式 | 加法表达式'-'乘法表达式
    def p_additive_expression(self, p):
        """	additive_expression : multiplicative_expression
                                | additive_expression '+' multiplicative_expression
                                | additive_expression '-' multiplicative_expression
        """
        p[0] = ('additive_expression', *p[1:])

    # 赋值表达式→条件表达式  |  一元表达式赋值运算符  赋值表达式
    def p_assignment_expression(self, p):
        """assignment_expression : conditional_expression
                                 | unary_expression assignment_operator assignment_expression
        """
        p[0] = ('assignment_expression', *p[1:])

    # 赋值运算符
    def p_assignment_operator(self, p):
        """assignment_operator : '='
                               | MUL_ASSIGN
                               | DIV_ASSIGN
                               | MOD_ASSIGN
                               | ADD_ASSIGN
                               | SUB_ASSIGN
                               | LEFT_ASSIGN
                               | RIGHT_ASSIGN
                               | AND_ASSIGN
                               | XOR_ASSIGN
                               | OR_ASSIGN
        """
        p[0] = ('assignment_operator', *p[1:])

    # 常数
    def p_constant_expression(self, p):
        """constant_expression : conditional_expression
        """
        p[0] = ('conditional_expression', *p[1:])

    # 表达式：赋值表达式  |  表达式 ',' 赋值表达式
    def p_expression(self, p):
        """expression : assignment_expression
                      | expression ',' assignment_expression
        """
        p[0] = ('expression', *p[1:])

    # 逻辑或表达→逻辑与表达  | 逻辑或表达  或运算 逻辑表达式
    def p_logical_or_expression(self, p):
        """logical_or_expression : logical_and_expression
                                 | logical_or_expression OR_OP logical_and_expression
        """
        p[0] = ('logical_or_expression', *p[1:])

    #  逻辑与表达：或表达式 | 逻辑表达式 和运算 或表达式
    def p_logical_and_expression(self, p):
        """logical_and_expression : inclusive_or_expression
                                  | logical_and_expression AND_OP inclusive_or_expression
        """
        p[0] = ('logical_and_expression', *p[1:])

    # 条件表达式→逻辑或表达 | 逻辑或表达'?' 表达式 ':'条件表达式
    def p_conditional_expression(self, p):
        """conditional_expression : logical_or_expression
                                  | logical_or_expression '?' expression ':' conditional_expression
        """
        p[0] = ('conditional_expression', *p[1:])

    # 或运算表达式→异或表达式 | 或运算表达式 '|' 异或表达式
    def p_inclusive_or_expression(self, p):
        """inclusive_or_expression : exclusive_or_expression
                                   | inclusive_or_expression '|' exclusive_or_expression
        """
        p[0] = ('inclusive_or_expression', *p[1:])

    # 异或表达式：与表达式 |  异或表达式'^'与表达式
    def p_exclusive_or_expression(self, p):
        """exclusive_or_expression : and_expression
                                   | exclusive_or_expression '^' and_expression
        """
        p[0] = ('exclusive_or_expression', *p[1:])

    # 与表达式：相等表达式 | 与表达式'&'相等表达式
    def p_and_expression(self, p):
        """and_expression : equality_expression
                          | and_expression '&' equality_expression
        """
        p[0] = ('and_expression', *p[1:])

    # 相等表达式：关系表达式 | 相等表达式等于运算关系表达式 | 相等表达式不等于运算关系表达式
    def p_equality_expression(self, p):
        """equality_expression : relational_expression
                               | equality_expression EQ_OP relational_expression
                               | equality_expression NE_OP relational_expression
        """
        p[0] = ('equality_expression', *p[1:])

    # 关系表达式：移位表达式 | 关系表达式'<'移位表达式 | 关系表达式'>'移位表达式  |  关系表达式小于等于运算移位表达式 | 关系表达式大于等于运算移位表达式
    def p_relational_expression(self, p):
        """relational_expression : shift_expression
                                   | relational_expression '<' shift_expression
                                   | relational_expression '>' shift_expression
                                   | relational_expression LE_OP shift_expression
                                   | relational_expression GE_OP shift_expression
        """
        p[0] = ('relational_expression', *p[1:])

    # 移位表达式：加法表达式 | 移位表达式 左运算 加法表达式  | 移位表达式 右运算 加法表达式
    def p_shift_expression(self, p):
        """shift_expression : additive_expression
                              | shift_expression LEFT_OP additive_expression
                              | shift_expression RIGHT_OP additive_expression
        """
        p[0] = ('shift_expression', *p[1:])

    # 声明
    def p_declaration(self, p):
        """declaration : declaration_specifiers ';'
                       | declaration_specifiers init_declarator_list ';'
        """
        p[0] = ('declaration', *p[1:])
        deal_declaration(p[0])

    # 声明说明符
    def p_declaration_specifiers(self, p):
        """declaration_specifiers : storage_class_specifier
                                  | storage_class_specifier declaration_specifiers
                                  | type_specifier
                                  | type_specifier declaration_specifiers
                                  | type_qualifier
                                  | type_qualifier declaration_specifiers
        """
        p[0] = ('declaration_specifiers', *p[1:])

    #  初始化声明列表
    def p_init_declarator_list(self, p):
        """init_declarator_list	: init_declarator
                                | init_declarator_list ',' init_declarator
        """
        p[0] = ('init_declarator_list', *p[1:])

    # 初始化声明→ 声明 | 声明'='初始化程序
    def p_init_declarator(self, p):
        """init_declarator : declarator
                           | declarator '=' initializer
        """
        p[0] = ('init_declarator', *p[1:])

    # 存储类说明符→定义类型 | 外部变量 | 静态  | 自动  | 寄存器
    def p_storage_class_specifier(self, p):
        """storage_class_specifier : TYPEDEF
                                   | EXTERN
                                   | STATIC
                                   | AUTO
                                   | REGISTER
        """
        p[0] = ('storage_class_specifier', *p[1:])

    # 类型说明符
    def p_type_specifier(self, p):
        """type_specifier : VOID
                          | CHAR
                          | SHORT
                          | INT
                          | LONG
                          | FLOAT
                          | DOUBLE
                          | SIGNED
                          | UNSIGNED
                          | struct_or_union_specifier
                          | enum_specifier
                          | TYPE_NAME
        """
        p[0] = ('type_specifier', *p[1:])

    # 结构或联合说明
    def p_struct_or_union_specifier(self, p):
        """struct_or_union_specifier : struct_or_union IDENTIFIER '{' struct_declaration_list '}'
                                     | struct_or_union '{' struct_declaration_list '}'
                                     | struct_or_union IDENTIFIER
        """
        p[0] = ('struct_or_union_specifier', *p[1:])

    # 结构或联合：结构体 | 联合
    def p_struct_or_union(self, p):
        """struct_or_union : STRUCT
                           | UNION
        """
        p[0] = ('struct_or_union', *p[1:])

    # 结构体声明列表
    def p_struct_declaration_list(self, p):
        """struct_declaration_list : struct_declaration
                                   | struct_declaration_list struct_declaration
        """
        p[0] = ('struct_declaration_list', *p[1:])

    # 结构体声明
    def p_struct_declaration(self, p):
        """struct_declaration : specifier_qualifier_list struct_declarator_list ';'
        """
        p[0] = ('struct_declaration', *p[1:])

    #
    def p_specifier_qualifier_list(self, p):
        """specifier_qualifier_list : type_specifier specifier_qualifier_list
                                    | type_specifier
                                    | type_qualifier specifier_qualifier_list
                                    | type_qualifier
        """
        p[0] = ('specifier_qualifier_list', *p[1:])

    # 结构说明符列表→结构体声明 | 结构说明符列表','结构体声明
    def p_struct_declarator_list(self, p):
        """struct_declarator_list : struct_declarator
                                  | struct_declarator_list ',' struct_declarator
        """
        p[0] = ('struct_declarator_list', *p[1:])

    # 结构体声明→：声明 |  ':'常量表达式 | 声明':'常量表达式
    def p_struct_declarator(self, p):
        """struct_declarator : declarator
                             | ':' constant_expression
                             | declarator ':' constant_expression
        """
        p[0] = ('struct_declarator', *p[1:])

    # 枚举声明→枚举'{'枚举器列表'}'  | 枚举标识符'{'枚举器列表'}'  | 枚举标识符
    def p_enum_specifier(self, p):
        """enum_specifier : ENUM '{' enumerator_list '}'
                          | ENUM IDENTIFIER '{' enumerator_list '}'
                          | ENUM IDENTIFIER
        """
        p[0] = ('enum_specifier', *p[1:])

    # 枚举器列表→枚举器 | 枚举器列表','枚举器
    def p_enumerator_list(self, p):
        """enumerator_list : enumerator
                           | enumerator_list ',' enumerator
        """
        p[0] = ('enumerator_list', *p[1:])

    # 枚举器→标识符 | 标识符'='常量表达式
    def p_enumerator(self, p):
        """enumerator : IDENTIFIER
                      | IDENTIFIER '=' constant_expression
        """
        p[0] = ('enumerator', *p[1:])

    # 类型限定符→常量 | 易失的
    def p_type_qualifier(self, p):
        """type_qualifier : CONST
                          | VOLATILE
        """
        p[0] = ('type_qualifier', *p[1:])

    # 声明
    def p_declarator(self, p):
        """declarator : pointer direct_declarator
                      | direct_declarator
        """
        p[0] = ('declarator', *p[1:])

    #
    def p_direct_declarator(self, p):
        """direct_declarator : IDENTIFIER
                             | '(' declarator ')'
                             | direct_declarator '[' constant_expression ']'
                             | direct_declarator '[' ']'
                             | direct_declarator '(' parameter_type_list ')'
                             | direct_declarator '(' identifier_list ')'
                             | direct_declarator '(' ')'
        """
        p[0] = ('direct_declarator', *p[1:])

    # 指针
    def p_pointer(self, p):
        """pointer : '*'
                   | '*' type_qualifier_list
                   | '*' pointer
                   | '*' type_qualifier_list pointer
        """
        p[0] = ('pointer', *p[1:])

    # 类型限定符列表→类型限定符 | 类型限定符列表  类型限定符
    def p_type_qualifier_list(self, p):
        """type_qualifier_list : type_qualifier
                               | type_qualifier_list type_qualifier
        """
        p[0] = ('type_qualifier_list', *p[1:])

    # 参数类型列表→参数列表 | 参数列表','省略符号
    def p_parameter_type_list(self, p):
        """parameter_type_list : parameter_list
                               | parameter_list ',' ELLIPSIS
        """
        p[0] = ('parameter_type_list', *p[1:])

    # 参数列表→：声明参数 | 参数列表','声明参数
    def p_parameter_list(self, p):
        """parameter_list : parameter_declaration
                          | parameter_list ',' parameter_declaration
        """
        p[0] = ('parameter_list', *p[1:])

    # 声明参数
    def p_parameter_declaration(self, p):
        """parameter_declaration : declaration_specifiers declarator
                                 | declaration_specifiers abstract_declarator
                                 | declaration_specifiers
        """
        p[0] = ('parameter_declaration', *p[1:])

    # 标识符列表
    def p_identifier_list(self, p):
        """identifier_list : IDENTIFIER
                           | identifier_list ',' IDENTIFIER
        """
        p[0] = ('identifier_list', *p[1:])

    # 类型名称
    def p_type_name(self, p):
        """type_name : specifier_qualifier_list
                     | specifier_qualifier_list abstract_declarator
        """
        p[0] = ('type_name', *p[1:])

    # 抽象说明符
    def p_abstract_declarator(self, p):
        """abstract_declarator : pointer
                               | direct_abstract_declarator
                               | pointer direct_abstract_declarator
        """
        p[0] = ('abstract_declarator', *p[1:])

    # 直接抽象说明符
    def p_direct_abstract_declarator(self, p):
        """direct_abstract_declarator : '(' abstract_declarator ')'
                                      | '[' ']'
                                      | '[' constant_expression ']'
                                      | direct_abstract_declarator '[' ']'
                                      | direct_abstract_declarator '[' constant_expression ']'
                                      | '(' ')'
                                      | '(' parameter_type_list ')'
                                      | direct_abstract_declarator '(' ')'
                                      | direct_abstract_declarator '(' parameter_type_list ')'
        """
        p[0] = ('direct_abstract_declarator', *p[1:])

    # 初始化程序
    def p_initializer(self, p):
        """initializer : assignment_expression
                       | '{' initializer_list '}'
                       | '{' initializer_list ',' '}'
        """
        p[0] = ('initializer', *p[1:])

    # 初始化列表
    def p_initializer_list(self, p):
        """initializer_list : initializer
                            | initializer_list ',' initializer
        """
        p[0] = ('initializer_list', *p[1:])

    # 语句
    def p_statement(self, p):
        """statement : labeled_statement
                     | compound_statement
                     | expression_statement
                     | selection_statement
                     | iteration_statement
                     | jump_statement
        """
        p[0] = ('statement', *p[1:])

    # 语句列表
    def p_statement_list(self, p):
        """statement_list : statement
                          | statement_list statement
        """
        p[0] = ('statement_list', *p[1:])

    # 有标号语句
    def p_labeled_statement(self, p):
        """labeled_statement : IDENTIFIER ':' statement
                             | CASE constant_expression ':' statement
                             | DEFAULT ':' statement
        """
        p[0] = ('labeled_statement', *p[1:])

    # 复合语句
    def p_compound_statement(self, p):
        """compound_statement : '{' '}'
                              | '{' statement_list '}'
                              | '{' declaration_list '}'
                              | '{' declaration_list statement_list '}'
        """
        p[0] = ('compound_statement', *p[1:])

    # 声明列表
    def p_declaration_list(self, p):
        """declaration_list : declaration
                            | declaration_list declaration
        """
        p[0] = ('declaration_list', *p[1:])

    # 表达式语句→';'   |  表达式 ';'
    def p_expression_statement(self, p):
        """expression_statement : ';'
                                | expression ';'
        """
        p[0] = ('expression_statement', *p[1:])

    # 条件语句：IF'('表达式”)语句  |  IF'(' 表达式 ')'语句  条件语句
    def p_selection_statement(self, p):
        """selection_statement : IF '(' expression ')' statement
                               | IF '(' expression ')' statement ELSE statement
                               | SWITCH '(' expression ')' statement
        """
        p[0] = ('selection_statement', *p[1:])

    # 循环语句→ WHILE '(' 表达式')' 语句 | FOR '(' 表达式语句 表达式语句 ')' 语句 | FOR '(' 表达式语句  表达式语句  表达式')'语句
    def p_iteration_statement(self, p):
        """iteration_statement : WHILE '(' expression ')' statement
                               | DO statement WHILE '(' expression ')' ';'
                               | FOR '(' expression_statement expression_statement ')' statement
                               | FOR '(' expression_statement expression_statement expression ')' statement
        """
        p[0] = ('iteration_statement', *p[1:])

    # 跳转语句 |  CONTINUE ';'  |  BREAK ';'  |  RETURN ';'  | RETURN 表达式 ';'
    def p_jump_statement(self, p):
        """jump_statement : GOTO IDENTIFIER ';'
                          | CONTINUE ';'
                          | BREAK ';'
                          | RETURN ';'
                          | RETURN expression ';'
        """
        p[0] = ('jump_statement', *p[1:])

    # start
    def p_translation_unit(self, p):
        """translation_unit : external_declaration
                            | translation_unit external_declaration
        """
        p[0] = ('translation_unit', *p[1:])

    #
    def p_external_declaration(self, p):
        """external_declaration : function_definition
                                | declaration
        """
        p[0] = ('external_declaration', *p[1:])

    # 函数定义
    def p_function_definition(self, p):
        """function_definition : declaration_specifiers declarator declaration_list compound_statement
                               | declaration_specifiers declarator compound_statement
                               | declarator declaration_list compound_statement
                               | declarator compound_statement
        """
        p[0] = ('function_definition', *p[1:])

    def p_error(self, p):
        # print(p)
        raise ParseError(p.lexpos)