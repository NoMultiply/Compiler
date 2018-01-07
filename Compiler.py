from IRLibs import *

def get_identifier(scope_stack, id):
    identifier = None
    for scope in reversed(scope_stack):
        try:
            identifier = scope[id]
        except KeyError:
            pass
    assert identifier is not None
    return identifier

def get_pointer(scope_stack, builder: ir.IRBuilder, item):
    if isinstance(item, tuple) and item[0] == 'id':
        item = get_identifier(scope_stack, item[1])['value']
    return item

def get_value(scope_stack, builder: ir.IRBuilder, item):
    if isinstance(item, tuple) and item[0] == 'id':
        item = get_identifier(scope_stack, item[1])['value']
        if item.opname == 'alloca':
            item = builder.load(item)
    return item

def parse_postfix_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_primary_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 5 and exp[2] == '(':
        func_id = parse_postfix_expression(exp[1], module, scope_stack, builder)
        func = get_pointer(scope_stack, builder, func_id)
        raw_arg_list = parse_argument_expression_list(exp[3], module, scope_stack, builder)
        arg_list = []
        for arg in raw_arg_list:
            arg = get_value(scope_stack, builder, arg)
            arg_list.append(arg)
        builder.call(func, arg_list)
    elif len(exp) == 3:
        postfix_expression = parse_postfix_expression(exp[1], module, scope_stack, builder)
        temp = None
        value = get_value(scope_stack, builder, postfix_expression)
        if exp[2] == '++':
            temp = builder.add(value, int_type(1))
        elif exp[2] == '--':
            temp = builder.sub(value, int_type(1))
        builder.store(temp, get_pointer(scope_stack, builder, postfix_expression))
        return value


def parse_primary_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 4:
        return parse_expression(exp[2], module, scope_stack, builder)
    elif len(exp) == 2:
        if exp[1][0] == 'id':
            return exp[1]
        elif exp[1][0] == 'string':
            return insert_string(module, scope_stack, builder, exp[1][1], True)
        elif exp[1][0] in type_map:
            return type_map[exp[1][0]](exp[1][1])


def parse_argument_expression_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    if len(exp) == 2:
        result.append(parse_assignment_expression(exp[1], module, scope_stack, builder))
    elif len(exp) == 4:
        result.extend(parse_argument_expression_list(exp[1], module, scope_stack, builder))
        result.append(parse_assignment_expression(exp[3], module, scope_stack, builder))
    return result


def parse_unary_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_postfix_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 3 and exp[1][0] == 'unary_operator':
        unary_operator = parse_unary_operator(exp[1])
        cast_expression = parse_cast_expression(exp[2], module, scope_stack, builder)
        if unary_operator == '&':
            return get_pointer(scope_stack, builder, cast_expression)
    elif len(exp) == 3:
        unary_expression = parse_unary_expression(exp[2], module, scope_stack, builder)
        temp = None
        if exp[1] == '++':
            temp = builder.add(get_value(scope_stack, builder, unary_expression), int_type(1))
        elif exp[1] == '--':
            temp = builder.sub(get_value(scope_stack, builder, unary_expression), int_type(1))
        builder.store(temp, get_pointer(scope_stack, builder, unary_expression))
        return temp

def parse_unary_operator(exp):
    return exp[1]


def parse_cast_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_unary_expression(exp[1], module, scope_stack, builder)


def parse_multiplicative_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_cast_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_multiplicative_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_cast_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            if exp[2] == '*':
                return left.type(left.constant * right.constant)
            elif exp[2] == '/':
                return left.type(left.constant / right.constant)
            elif exp[2] == '%':
                return left.type(left.constant % right.constant)
        else:
            if exp[2] == '*':
                return builder.mul(left, right)
            elif exp[2] == '/':
                return builder.udiv(left, right)
            elif exp[2] == '%':
                return builder.urem(left, right)


def parse_additive_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_multiplicative_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_additive_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_multiplicative_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            if exp[2] == '+':
                return left.type(left.constant + right.constant)
            elif exp[2] == '-':
                return left.type(left.constant - right.constant)
        else:
            if exp[2] == '+':
                return builder.add(left, right)
            elif exp[2] == '-':
                return builder.sub(left, right)


def parse_assignment_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_conditional_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_pointer(scope_stack, builder, parse_unary_expression(exp[1], module, scope_stack, builder))
        assignment_operator = parse_assignment_operator(exp[2])
        right = get_value(scope_stack, builder, parse_assignment_expression(exp[3], module, scope_stack, builder))
        if assignment_operator == '=':
            builder.store(right, left)
        elif assignment_operator == '*=':
            temp = builder.mul(left, right)
            builder.store(temp, left)
        elif assignment_operator == '/=':
            temp = builder.udiv(left, right)
            builder.store(temp, left)
        elif assignment_operator == '%=':
            temp = builder.urem(left, right)
            builder.store(temp, left)
        elif assignment_operator == '+=':
            temp = builder.add(left, right)
            builder.store(temp, left)
        elif assignment_operator == '-=':
            temp = builder.sub(left, right)
            builder.store(temp, left)
        elif assignment_operator == '<<=':
            temp = builder.shl(left, right)
            builder.store(temp, left)
        elif assignment_operator == '>>=':
            temp = builder.ashr(left, right)
            builder.store(temp, left)
        elif assignment_operator == '&=':
            temp = builder.and_(left, right)
            builder.store(temp, left)
        elif assignment_operator == '|=':
            temp = builder.or_(left, right)
            builder.store(temp, left)
        elif assignment_operator == '^=':
            temp = builder.xor(left, right)
            builder.store(temp, left)

def parse_assignment_operator(exp):
    return exp[1]


def parse_constant_expression(exp):
    pass


def parse_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_assignment_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        parse_expression(exp[1], module, scope_stack, builder)
        return parse_assignment_expression(exp[2], module, scope_stack, builder)


def parse_logical_or_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_logical_and_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_logical_or_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_logical_and_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            return left.type(left.constant or right.constant)
        else:
            condition = builder.or_(left, right)
            return condition


def parse_logical_and_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_inclusive_or_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_logical_and_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_inclusive_or_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            return left.type(left.constant and right.constant)
        else:
            condition = builder.and_(left, right)
            return condition


def parse_conditional_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_logical_or_expression(exp[1], module, scope_stack, builder)
    else:
        pass


def parse_inclusive_or_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_exclusive_or_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_inclusive_or_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_exclusive_or_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            return left.type(left.constant | right.constant)
        else:
            condition = builder.or_(left, right)
            return condition


def parse_exclusive_or_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_and_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_exclusive_or_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_and_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            return left.type(left.constant ^ right.constant)
        else:
            condition = builder.xor(left, right)
            return condition


def parse_and_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_equality_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_and_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_equality_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            return left.type(left.constant & right.constant)
        else:
            condition = builder.and_(left, right)
            return condition


def parse_equality_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_relational_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_equality_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_relational_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            if exp[2] == '==':
                return left.type(left.constant == right.constant)
            elif exp[2] == '!=':
                return right.type(right.constant == right.constant)
        else:
            condition = builder.icmp_unsigned(exp[2], left, right)
            return condition


def parse_relational_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_shift_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_relational_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_shift_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            if exp[2] == '<':
                return left.type(left.constant < right.constant)
            elif exp[2] == '>':
                return right.type(right.constant > right.constant)
            elif exp[2] == '<=':
                return right.type(right.constant <= right.constant)
            elif exp[2] == '>=':
                return right.type(right.constant >= right.constant)
        else:
            condition = builder.icmp_unsigned(exp[2], left, right)
            return condition


def parse_shift_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_additive_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_value(scope_stack, builder, parse_shift_expression(exp[1], module, scope_stack, builder))
        right = get_value(scope_stack, builder, parse_additive_expression(exp[3], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and isinstance(right, ir.Constant):
            if exp[2] == '<<':
                return left.type(left.constant << right.constant)
            elif exp[2] == '>>':
                return right.type(right.constant >> right.constant)
        else:
            result = None
            if exp[2] == '<<':
                result = builder.shl(left, right)
            elif exp[2] == '>>':
                result = builder.ashr(left, right)
            return result


def parse_declaration(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder = None):
    declaration_specifiers = parse_declaration_specifiers(exp[1])
    if len(exp) == 4:
        init_declarator_list = parse_init_declarator_list(exp[2], module, scope_stack, builder)
        if len(init_declarator_list) == 1 and init_declarator_list[0][0][0] == 'function':
            insert_function(module, scope_stack, declaration_specifiers, init_declarator_list[0][0][1], init_declarator_list[0][0][2])
        else:
            for init_declarator in init_declarator_list:
                if init_declarator[0][0] == 'id':
                    insert_val(module, scope_stack, builder, declaration_specifiers, init_declarator[0], init_declarator[1])
    elif len(exp) == 2:
        pass

def parse_declaration_specifiers(exp):
    result = []
    if exp[1][0] == 'storage_class_specifier':
        result.append(parse_storage_class_specifier(exp[1]))
    elif exp[1][0] == 'type_specifier':
        result.append(parse_type_specifier(exp[1]))
    elif exp[1][0] == 'type_qualifier':
        result.append(parse_type_qualifier(exp[1]))
    if len(exp) == 3:
        result.extend(parse_declaration_specifiers(exp[2]))
    return result


def parse_init_declarator_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    for i in range(1, len(exp)):
        if exp[i][0] == 'init_declarator_list':
            result.extend(parse_init_declarator_list(exp[i], module, scope_stack, builder))
        elif exp[i][0] == 'init_declarator':
            result.append(parse_init_declarator(exp[i], module, scope_stack, builder))
    return result


def parse_init_declarator(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    declarator = parse_declarator(exp[1])
    initializer = None
    if len(exp) == 4:
        initializer = parse_initializer(exp[3], module, scope_stack, builder)
    return (declarator, initializer)

def parse_storage_class_specifier(exp):
    return exp[1][1]


def parse_type_specifier(exp):
    if exp[1][0] == 'struct_or_union_specifier':
        pass # TODO
    elif exp[1][0] == 'enum_specifier':
        pass # TODO
    else:
        return exp[1][1]


def parse_struct_or_union_specifier(exp):
    pass


def p_struct_or_union(exp):
    pass


def parse_struct_declaration_list(exp):
    pass


def parse_struct_declaration(exp):
    pass


def parse_specifier_qualifier_list(exp):
    pass


def parse_struct_declarator_list(exp):
    pass


def parse_struct_declarator(exp):
    pass


def parse_enum_specifier(exp):
    pass


def parse_enumerator_list(exp):
    pass


def parse_enumerator(exp):
    pass


def parse_type_qualifier(exp):
    return exp[1][1]


def parse_declarator(exp):
    if len(exp) == 2:
        return parse_direct_declarator(exp[1])
    else:
        return ('pointer', parse_pointer(exp[1]), parse_direct_declarator(exp[2]))


def parse_direct_declarator(exp):
    if len(exp) == 2:
        return exp[1]
    elif len(exp) == 5:
        if exp[2] == '(' and exp[3][0] == 'parameter_type_list':
            return ('function', parse_direct_declarator(exp[1]), parse_parameter_type_list(exp[3]))
        elif exp[2] == '(' and exp[3][0] == 'identifier_list':
            pass
        elif exp[2] == '[':
            pass
    elif len(exp) == 4:
        if exp[2] == '(':
            return ('function', parse_direct_declarator(exp[1]), [])
        elif exp[2] == '[':
            pass


def parse_pointer(exp):
    result = []
    if len(exp) == 2:
        result.append(exp[1])
    elif len(exp) == 3 and exp[2][0] == 'pointer':
        result.extend(parse_pointer(exp[2]))
    else:
        pass
    return result


def parse_type_qualifier_list(exp):
    pass


def parse_parameter_type_list(exp):
    result = []
    result.extend(parse_parameter_list(exp[1]))
    if len(exp) == 4:
        result.append(exp[3])
    return result


def parse_parameter_list(exp):
    result = []
    if len(exp) == 2:
        result.append(parse_parameter_declaration(exp[1]))
    elif len(exp) == 4:
        result.extend(parse_parameter_list(exp[1]))
        result.append(parse_parameter_declaration(exp[3]))
    return result


def parse_parameter_declaration(exp):
    result = []
    result.append(parse_declaration_specifiers(exp[1]))
    if len(exp) == 3 and exp[2][0] == 'declarator':
        result.append(parse_declarator(exp[2]))
    elif len(exp) == 3 and exp[2][0] == 'abstract_declarator':
        result.append(parse_abstract_declarator(exp[2]))
    return result


def parse_identifier_list(exp):
    pass


def parse_type_name(exp):
    pass


def parse_abstract_declarator(exp):
    pass


def parse_direct_abstract_declarator(exp):
    pass


def parse_initializer(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_assignment_expression(exp[1], module, scope_stack, builder)


def parse_initializer_list(exp):
    pass


def parse_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if exp[1][0] == 'labeled_statement':
        parse_labeled_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'compound_statement':
        parse_compound_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'expression_statement':
        parse_expression_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'selection_statement':
        parse_selection_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'iteration_statement':
        parse_iteration_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'jump_statement':
        parse_jump_statement(exp[1], module, scope_stack, builder)
    pass


def parse_statement_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        parse_statement(exp[1], module, scope_stack, builder)
    elif len(exp) == 3:
        parse_statement_list(exp[1], module, scope_stack, builder)
        parse_statement(exp[2], module, scope_stack, builder)


def parse_labeled_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    pass


def parse_compound_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    scope_stack.append({})
    if len(exp) == 3:
        pass # Nothing TODO
    elif len(exp) == 4 and exp[2][0] == 'statement_list':
        parse_statement_list(exp[2], module, scope_stack, builder)
    elif len(exp) == 4 and exp[2][0] == 'declaration_list':
        parse_declaration_list(exp[2], module, scope_stack, builder)
    if len(exp) == 5:
        parse_declaration_list(exp[2], module, scope_stack, builder)
        parse_statement_list(exp[3], module, scope_stack, builder)
    scope_stack.pop()


def parse_declaration_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    if len(exp) == 2:
        parse_declaration(exp[1], module, scope_stack, builder)
    elif len(exp) == 3:
        parse_declaration_list(exp[1], module, scope_stack, builder)
        parse_declaration(exp[2], module, scope_stack, builder)
    return result


def parse_expression_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return
    elif len(exp) == 3:
        return parse_expression(exp[1], module, scope_stack, builder)


def parse_selection_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 6 and exp[1][1] == 'if':
        expression = get_value(scope_stack, builder, parse_expression(exp[3], module, scope_stack, builder))
        condition = builder.icmp_unsigned('!=', expression, int_type(0))
        with builder.if_then(condition):
            parse_statement(exp[5], module, scope_stack, builder)
    elif len(exp) == 8:
        expression = get_value(scope_stack, builder, parse_expression(exp[3], module, scope_stack, builder))
        condition = builder.icmp_unsigned('!=', expression, int_type(0))
        with builder.if_else(condition) as (then, otherwise):
            with then:
                parse_statement(exp[5], module, scope_stack, builder)
            with otherwise:
                parse_statement(exp[7], module, scope_stack, builder)



def parse_iteration_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    print(len(exp), exp)


def parse_jump_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 4 and exp[1][1] == 'return':
        val = parse_expression(exp[2], module, scope_stack, builder)
        builder.ret(val)
    elif len(exp) == 3 and exp[1][1] == 'return':
        builder.ret_void()

def parse_translation_unit(exp, module: ir.Module = None, scope_stack: list = None):
    start = False
    if module is None:
        start = True
        module = ir.Module()
        scope_stack = []
        scope_stack.append({})
    if len(exp) == 2:
        parse_external_declaration(exp[1], module, scope_stack)
    elif len(exp) == 3:
        parse_translation_unit(exp[1], module, scope_stack)
        parse_external_declaration(exp[2], module, scope_stack)
    if start:
        data = str(module)
        data = '\n'.join(data.split('\n')[4:])
        return data


def parse_external_declaration(exp, module: ir.Module, scope_stack: list):
    if exp[1][0] == 'function_definition':
        parse_function_definition(exp[1], module, scope_stack)
    elif exp[1][0] == 'declaration':
        parse_declaration(exp[1], module, scope_stack)


def parse_function_definition(exp, module: ir.Module, scope_stack: list):
    if len(exp) == 4 and exp[1][0] == 'declaration_specifiers':
        return_type = parse_declaration_specifiers(exp[1])
        func_data = parse_declarator(exp[2])
        func = insert_function(module, scope_stack, return_type, func_data[1], func_data[2])
        block = func.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)
        parse_compound_statement(exp[3], module, scope_stack, builder)
    else:
        pass
