from IRLibs import *


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
        for i in range(len(func.args)):
            arg_list[i] = convert(builder, arg_list[i], func.args[i].type)
        return builder.call(func, arg_list)
    elif len(exp) == 3:
        postfix_expression = parse_postfix_expression(exp[1], module, scope_stack, builder)
        temp = None
        value = get_value(scope_stack, builder, postfix_expression)
        if exp[2] == '++':
            temp = opt_add(builder, value, int_type(1))
        elif exp[2] == '--':
            temp = opt_sub(builder, value, int_type(1))
        opt_store(builder, temp, get_pointer(scope_stack, builder, postfix_expression))
        return value
    elif len(exp) == 5 and exp[2] == '[':
        array = parse_postfix_expression(exp[1], module, scope_stack, builder)
        index = get_value(scope_stack, builder, parse_expression(exp[3], module, scope_stack, builder))
        return ('array_index', get_array_pointer(scope_stack, builder, array, index))
    elif len(exp) == 4 and exp[2] == '.':
        postfix_expression = parse_postfix_expression(exp[1], module, scope_stack, builder)
        return ('struct', postfix_expression[1], exp[3][1])
    elif len(exp) == 4 and exp[2] == '->':
        postfix_expression = parse_postfix_expression(exp[1], module, scope_stack, builder)
        return ('struct_ptr', postfix_expression[1], exp[3][1])
    elif len(exp) == 4 and exp[2] == '(':
        func_id = parse_postfix_expression(exp[1], module, scope_stack, builder)
        func = get_pointer(scope_stack, builder, func_id)
        builder.call(func, [])


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
        elif unary_operator == '*':
            return get_pointer_value(scope_stack, builder, cast_expression)
        elif unary_operator == '-':
            val = get_value(scope_stack, builder, cast_expression)
            if isinstance(val, ir.Constant):
                return val.type(-val.constant)
            else:
                return builder.neg(val)
        elif unary_operator == '!':
            val = get_value(scope_stack, builder, cast_expression)
            if isinstance(val, ir.Constant):
                return val.type(not val.constant)
            else:
                return builder.not_(val)
    elif len(exp) == 3:
        unary_expression = parse_unary_expression(exp[2], module, scope_stack, builder)
        temp = None
        if exp[1] == '++':
            temp = opt_add(builder, get_value(scope_stack, builder, unary_expression), int_type(1))
        elif exp[1] == '--':
            temp = opt_sub(builder, get_value(scope_stack, builder, unary_expression), int_type(1))
        opt_store(builder, temp, get_pointer(scope_stack, builder, unary_expression))
        return temp


def parse_unary_operator(exp):
    return exp[1]


def parse_cast_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_unary_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 5:
        type_name = parse_type_name(exp[2], module, scope_stack, builder)
        cast_expression = get_value(scope_stack, builder, parse_cast_expression(exp[4], module, scope_stack, builder))
        return convert(builder, cast_expression, type_map[type_name])


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
                return opt_mul(builder, left, right)
            elif exp[2] == '/':
                return opt_div(builder, left, right)
            elif exp[2] == '%':
                return opt_rem(builder, left, right)


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
                return opt_add(builder, left, right)
            elif exp[2] == '-':
                return opt_sub(builder, left, right)


def parse_assignment_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_conditional_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_pointer(scope_stack, builder, parse_unary_expression(exp[1], module, scope_stack, builder))
        assignment_operator = parse_assignment_operator(exp[2])
        right = get_value(scope_stack, builder, parse_assignment_expression(exp[3], module, scope_stack, builder))
        if assignment_operator == '=':
            opt_store(builder, right, left)
        elif assignment_operator == '*=':
            temp = opt_mul(builder, left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '/=':
            temp = opt_div(builder, left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '%=':
            temp = opt_rem(builder, left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '+=':
            temp = opt_add(builder, left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '-=':
            temp = opt_sub(builder, left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '<<=':
            temp = builder.shl(left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '>>=':
            temp = builder.ashr(left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '&=':
            temp = builder.and_(left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '|=':
            temp = builder.or_(left, right)
            opt_store(builder, temp, left)
        elif assignment_operator == '^=':
            temp = builder.xor(left, right)
            opt_store(builder, temp, left)


def parse_assignment_operator(exp):
    return exp[1]


def parse_constant_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    return parse_conditional_expression(exp[1], module, scope_stack, builder)


def parse_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_assignment_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        parse_expression(exp[1], module, scope_stack, builder)
        return parse_assignment_expression(exp[3], module, scope_stack, builder)


def parse_logical_or_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_logical_and_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_bool(scope_stack, builder, parse_logical_or_expression(exp[1], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and left.constant != 0:
            return bool_type(1)
        else:
            if isinstance(left, ir.Constant):
                right = parse_logical_and_expression(exp[3], module, scope_stack, builder)
                return get_bool(scope_stack, builder, right)
            else:
                result = builder.alloca(bool_type)
                with builder.if_else(left) as (then, otherwise):
                    with then:
                        opt_store(builder, bool_type(1), result)
                    with otherwise:
                        right = get_bool(scope_stack, builder,
                                         parse_logical_and_expression(exp[3], module, scope_stack, builder))
                        opt_store(builder, right, result)
                return builder.load(result)


def parse_logical_and_expression(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_inclusive_or_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        left = get_bool(scope_stack, builder, parse_logical_and_expression(exp[1], module, scope_stack, builder))
        if isinstance(left, ir.Constant) and left.constant == 0:
            return bool_type(0)
        else:
            if isinstance(left, ir.Constant):
                right = parse_inclusive_or_expression(exp[3], module, scope_stack, builder)
                return get_bool(scope_stack, builder, right)
            else:
                result = builder.alloca(bool_type)
                with builder.if_else(left) as (then, otherwise):
                    with then:
                        right = get_bool(scope_stack, builder, parse_inclusive_or_expression(exp[3], module, scope_stack, builder))
                        opt_store(builder, right, result)
                    with otherwise:
                        opt_store(builder, bool_type(0), result)
                return builder.load(result)


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
            return left.type(left.constant or right.constant)
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
            return left.type(left.constant and right.constant)
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
            condition = opt_cmp(builder, exp[2], left, right)
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
            return opt_cmp(builder, exp[2], left, right)


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
    declaration_specifiers = parse_declaration_specifiers(exp[1], module, scope_stack, builder)
    if len(exp) == 4:
        init_declarator_list = parse_init_declarator_list(exp[2], module, scope_stack, builder)
        if declaration_specifiers[0] == 'typedef':
            insert_type(module, scope_stack, builder, declaration_specifiers[-1], init_declarator_list[0][0][1])
        else:
            if len(init_declarator_list) == 1 and init_declarator_list[0][0][0] == 'function':
                insert_function(module, scope_stack, declaration_specifiers, init_declarator_list[0][0][1], init_declarator_list[0][0][2])
            else:
                for init_declarator in init_declarator_list:
                    if init_declarator[0][0] == 'id':
                        insert_val(module, scope_stack, builder, declaration_specifiers, init_declarator[0],
                                   get_value(scope_stack, builder, init_declarator[1]))
                    elif init_declarator[0][0] == 'array':
                        array = insert_array(module, scope_stack, builder, declaration_specifiers, init_declarator[0][2],
                                     init_declarator[0][1])
                        if isinstance(init_declarator[1], list):
                            if len(init_declarator[1]) > 0:
                                memzero(module, scope_stack, builder, array, init_declarator[0][2].constant)
                                for i in range(len(init_declarator[1])):
                                    array_i = get_array_pointer(scope_stack, builder, array, int_type(i))
                                    opt_store(builder, init_declarator[1][i], array_i)
                        elif declaration_specifiers[-1] == 'char' and init_declarator[1]:
                            array_type = init_declarator[1].pointer.type.pointee
                            memcpy(module, scope_stack, builder, array, init_declarator[1], array_type.count, array_type.element.width)
                    elif init_declarator[0][0] == 'pointer':
                        insert_pointer(module, scope_stack, builder, declaration_specifiers, init_declarator[0],
                                   get_value(scope_stack, builder, init_declarator[1]))
                    elif init_declarator[0][0] == 'array_pointer':
                        array_type = init_declarator[1].pointer.type.pointee
                        assert isinstance(array_type, ir.ArrayType)
                        array_len = array_type.count
                        val = insert_array(module, scope_stack, builder, declaration_specifiers, int_type(array_len), init_declarator[0][1])
                        memcpy(module, scope_stack, builder, val, init_declarator[1], array_len, array_type.element.width)
    elif len(exp) == 2:
        pass


def parse_declaration_specifiers(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    if exp[1][0] == 'storage_class_specifier':
        result.append(parse_storage_class_specifier(exp[1]))
    elif exp[1][0] == 'type_specifier':
        result.append(parse_type_specifier(exp[1], module, scope_stack, builder))
    elif exp[1][0] == 'type_qualifier':
        result.append(parse_type_qualifier(exp[1]))
    if len(exp) == 3:
        result.extend(parse_declaration_specifiers(exp[2], module, scope_stack, builder))
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
    declarator = parse_declarator(exp[1], module, scope_stack, builder)
    initializer = None
    if len(exp) == 4:
        initializer = parse_initializer(exp[3], module, scope_stack, builder)
    return (declarator, initializer)


def parse_storage_class_specifier(exp):
    return exp[1][1]


def parse_type_specifier(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if exp[1][0] == 'struct_or_union_specifier':
        return parse_struct_or_union_specifier(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'enum_specifier':
        pass # TODO
    else:
        return exp[1][1]


def parse_struct_or_union_specifier(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 5:
        struct_or_union = parse_struct_or_union(exp[1])
        struct_declaration_list = parse_struct_declaration_list(exp[3], module, scope_stack, builder)
        if struct_or_union[1] == 'struct':
            struct = {
                'type': 'struct',
                'list': struct_declaration_list
            }
            return struct


def parse_struct_or_union(exp):
    return exp[1]


def parse_struct_declaration_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    if len(exp) == 2:
        result.append(parse_struct_declaration(exp[1], module, scope_stack, builder))
    elif len(exp) == 3:
        result.extend(parse_struct_declaration_list(exp[1], module, scope_stack, builder))
        result.append(parse_struct_declaration(exp[2], module, scope_stack, builder))
    return result


def parse_struct_declaration(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    specifier_qualifier_list = parse_specifier_qualifier_list(exp[1], module, scope_stack, builder)
    struct_declarator_list = parse_struct_declarator_list(exp[2], module, scope_stack, builder)
    return (specifier_qualifier_list, struct_declarator_list)


def parse_specifier_qualifier_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2 and exp[1][0] == 'type_specifier':
        return parse_type_specifier(exp[1], module, scope_stack, builder)


def parse_struct_declarator_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    if len(exp) == 2:
        result.append(parse_struct_declarator(exp[1], module, scope_stack, builder))
    elif len(exp) == 4:
        result.extend(parse_struct_declarator_list(exp[1], module, scope_stack, builder))
        result.append(parse_struct_declarator(exp[3], module, scope_stack, builder))
    return result


def parse_struct_declarator(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_declarator(exp[1], module, scope_stack, builder)


def parse_enum_specifier(exp):
    pass


def parse_enumerator_list(exp):
    pass


def parse_enumerator(exp):
    pass


def parse_type_qualifier(exp):
    return exp[1][1]


def parse_declarator(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_direct_declarator(exp[1], module, scope_stack, builder)
    else:
        return ('pointer', parse_pointer(exp[1]), parse_direct_declarator(exp[2], module, scope_stack, builder))


def parse_direct_declarator(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return exp[1]
    elif len(exp) == 5:
        if exp[2] == '(' and exp[3][0] == 'parameter_type_list':
            return ('function', parse_direct_declarator(exp[1], module, scope_stack, builder), parse_parameter_type_list(exp[3], module, scope_stack, builder))
        elif exp[2] == '(' and exp[3][0] == 'identifier_list':
            pass
        elif exp[2] == '[':
            return ('array', parse_direct_declarator(exp[1], module, scope_stack, builder), parse_constant_expression(exp[3], module, scope_stack, builder))
    elif len(exp) == 4:
        if exp[2] == '(':
            return ('function', parse_direct_declarator(exp[1], module, scope_stack, builder), [])
        elif exp[2] == '[':
            return ('array_pointer', parse_direct_declarator(exp[1], module, scope_stack, builder))


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


def parse_parameter_type_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    result.extend(parse_parameter_list(exp[1], module, scope_stack, builder))
    if len(exp) == 4:
        result.append(exp[3])
    return result


def parse_parameter_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    if len(exp) == 2:
        result.append(parse_parameter_declaration(exp[1], module, scope_stack, builder))
    elif len(exp) == 4:
        result.extend(parse_parameter_list(exp[1], module, scope_stack, builder))
        result.append(parse_parameter_declaration(exp[3], module, scope_stack, builder))
    return result


def parse_parameter_declaration(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    result.append(parse_declaration_specifiers(exp[1], module, scope_stack, builder))
    if len(exp) == 3 and exp[2][0] == 'declarator':
        result.append(parse_declarator(exp[2], module, scope_stack, builder))
    elif len(exp) == 3 and exp[2][0] == 'abstract_declarator':
        result.append(parse_abstract_declarator(exp[2]))
    return result


def parse_identifier_list(exp):
    pass


def parse_type_name(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_specifier_qualifier_list(exp[1], module, scope_stack, builder)


def parse_abstract_declarator(exp):
    pass


def parse_direct_abstract_declarator(exp):
    pass


def parse_initializer(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        return parse_assignment_expression(exp[1], module, scope_stack, builder)
    elif len(exp) == 4:
        return parse_initializer_list(exp[2], module, scope_stack, builder)


def parse_initializer_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    result = []
    if len(exp) == 2:
        result.append(parse_initializer(exp[1], module, scope_stack, builder))
    elif len(exp) == 4:
        result.extend(parse_initializer_list(exp[1], module, scope_stack, builder))
        result.append(parse_initializer(exp[3], module, scope_stack, builder))
    return result


def parse_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if exp[1][0] == 'labeled_statement':
        parse_labeled_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'compound_statement':
        scope_stack.append({
            '@type': 'others'
        })
        parse_compound_statement(exp[1], module, scope_stack, builder)
        scope_stack.pop()
    elif exp[1][0] == 'expression_statement':
        parse_expression_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'selection_statement':
        parse_selection_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'iteration_statement':
        parse_iteration_statement(exp[1], module, scope_stack, builder)
    elif exp[1][0] == 'jump_statement':
        parse_jump_statement(exp[1], module, scope_stack, builder)


def parse_statement_list(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 2:
        parse_statement(exp[1], module, scope_stack, builder)
    elif len(exp) == 3:
        parse_statement_list(exp[1], module, scope_stack, builder)
        parse_statement(exp[2], module, scope_stack, builder)


def parse_labeled_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 5:
        label_block = builder.block
        case_block = builder.append_basic_block('case_block')
        builder.position_at_end(label_block)
        try:
            builder.branch(case_block)
        except AssertionError:
            pass
        builder.position_at_end(loop_stack[-1]['start'])
        constant = get_value(scope_stack, builder, parse_constant_expression(exp[2], module, scope_stack, builder))
        condition = opt_cmp(builder, '==', loop_stack[-1]['value'], constant)
        with builder.if_then(condition):
            builder.branch(case_block)
        loop_stack[-1]['start'] = builder.block
        builder.position_at_end(case_block)
        parse_statement(exp[4], module, scope_stack, builder)
    elif len(exp) == 4 and exp[1][1] == 'default':
        label_block = builder.block
        default_block = builder.append_basic_block('default')
        builder.position_at_end(label_block)
        try:
            builder.branch(default_block)
        except AssertionError:
            pass
        builder.position_at_end(loop_stack[-1]['start'])
        with builder.if_then(bool_type(1)):
            builder.branch(default_block)
        loop_stack[-1]['start'] = builder.block
        builder.position_at_end(default_block)
        parse_statement(exp[3], module, scope_stack, builder)


def parse_compound_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 3:
        pass # Nothing TODO
    elif len(exp) == 4 and exp[2][0] == 'statement_list':
        parse_statement_list(exp[2], module, scope_stack, builder)
    elif len(exp) == 4 and exp[2][0] == 'declaration_list':
        parse_declaration_list(exp[2], module, scope_stack, builder)
    if len(exp) == 5:
        parse_declaration_list(exp[2], module, scope_stack, builder)
        parse_statement_list(exp[3], module, scope_stack, builder)
    if scope_stack[-1]['@type'] == 'function':
        return_type = scope_stack[-1]['@return_type'][-1]
        try:
            if return_type == 'void':
                builder.ret_void()
            else:
                builder.ret(type_map[return_type](0))
        except AssertionError:
            pass


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
        condition = get_bool(scope_stack, builder, expression)
        with builder.if_then(condition):
            parse_statement(exp[5], module, scope_stack, builder)
    elif len(exp) == 8:
        expression = get_value(scope_stack, builder, parse_expression(exp[3], module, scope_stack, builder))
        condition = get_bool(scope_stack, builder, expression)
        with builder.if_else(condition) as (then, otherwise):
            with then:
                parse_statement(exp[5], module, scope_stack, builder)
            with otherwise:
                parse_statement(exp[7], module, scope_stack, builder)
    elif len(exp) == 6 and exp[1][1] == 'switch':
        cur_block = builder.block
        start_block = builder.append_basic_block('start_switch')
        label_block = builder.append_basic_block('label_switch')
        end_block = builder.append_basic_block('end_switch')
        loop_stack.append({
            'start': start_block,
            'end': end_block,
            'value': get_value(scope_stack, builder, parse_expression(exp[3], module, scope_stack, builder)),
        })
        builder.position_at_end(cur_block)
        builder.branch(start_block)
        builder.position_at_end(label_block)
        parse_statement(exp[5], module, scope_stack, builder)
        try:
            builder.branch(end_block)
        except AssertionError:
            pass
        builder.position_at_end(loop_stack[-1]['start'])
        builder.branch(end_block)
        builder.position_at_start(end_block)
        loop_stack.pop()


def parse_iteration_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 8 and exp[1][1] == 'for':
        parse_expression_statement(exp[3], module, scope_stack, builder)
        start_block = builder.append_basic_block('start_for')
        builder.branch(start_block)
        builder.position_at_start(start_block)
        condition_in = parse_expression_statement(exp[4], module, scope_stack, builder)
        with builder.if_then(condition_in) as end_block:
            update_block = builder.append_basic_block('update_for')
            loop_stack.append({
                'start': start_block,
                'end': end_block,
                'continue': update_block
            })
            parse_statement(exp[7], module, scope_stack, builder)
            builder.branch(update_block)
            builder.position_at_start(update_block)
            parse_expression(exp[5], module, scope_stack, builder)
            builder.branch(start_block)
        loop_stack.pop()
    elif len(exp) == 8 and exp[1][1] == 'do':
        start_block = builder.append_basic_block('start_do_while')
        builder.branch(start_block)
        continue_block = builder.append_basic_block('continue_do_while')
        builder.position_at_start(continue_block)
        condition_in = get_bool(scope_stack, builder, parse_expression(exp[5], module, scope_stack, builder))
        with builder.if_then(condition_in) as end_block:
            builder.branch(start_block)
            loop_stack.append({
                'start': start_block,
                'end': end_block,
                'continue': continue_block
            })
            builder.position_at_start(start_block)
            parse_statement(exp[2], module, scope_stack, builder)
            builder.branch(continue_block)
        loop_stack.pop()
    elif len(exp) == 7:
        parse_expression_statement(exp[3], module, scope_stack, builder)
        start_block = builder.append_basic_block('start_for')
        builder.branch(start_block)
        builder.position_at_start(start_block)
        condition_in = get_bool(scope_stack, builder, parse_expression_statement(exp[4], module, scope_stack, builder))
        with builder.if_then(condition_in) as end_block:
            loop_stack.append({
                'start': start_block,
                'end': end_block,
                'continue': start_block
            })
            parse_statement(exp[6], module, scope_stack, builder)
            builder.branch(start_block)
        loop_stack.pop()
    elif len(exp) == 6:
        start_block = builder.append_basic_block('start_while')
        builder.branch(start_block)
        builder.position_at_start(start_block)
        condition_in = get_bool(scope_stack, builder, parse_expression(exp[3], module, scope_stack, builder))
        # if isinstance(condition_in, ir.Constant):
        #     condition_in = bool_type(condition_in.constant)
        # else:
        #     condition_in = builder.trunc(condition_in, bool_type)
        with builder.if_then(condition_in) as end_block:
            loop_stack.append({
                'start': start_block,
                'end': end_block,
                'continue': start_block
            })
            parse_statement(exp[5], module, scope_stack, builder)
            builder.branch(start_block)
        loop_stack.pop()


def parse_jump_statement(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder):
    if len(exp) == 4 and exp[1][1] == 'return':
        val = get_value(scope_stack, builder, parse_expression(exp[2], module, scope_stack, builder))
        return_type = type_map[function_stack[-1]['@return_type'][-1]]
        if val is not None:
            val = convert(builder, val, return_type)
        builder.ret(val)
        # with builder.if_then(bool_type(1)):
        #     if val is not None:
        #         val = convert(builder, val, return_type)
        #     builder.ret(val)
    elif len(exp) == 3 and exp[1][1] == 'return':
        builder.ret_void()
        # with builder.if_then(bool_type(1)):
        #     builder.ret_void()
    elif len(exp) == 3 and exp[1][1] == 'break':
        with builder.if_then(bool_type(1)):
            builder.branch(loop_stack[-1]['end'])
    elif len(exp) == 3 and exp[1][1] == 'continue':
        with builder.if_then(bool_type(1)):
            builder.branch(loop_stack[-1]['continue'])


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


def parse_function_definition(exp, module: ir.Module, scope_stack: list, builder: ir.IRBuilder = None):
    if len(exp) == 4 and exp[1][0] == 'declaration_specifiers':
        return_type = parse_declaration_specifiers(exp[1], module, scope_stack, builder)
        func_data = parse_declarator(exp[2], module, scope_stack, builder)
        func = insert_function(module, scope_stack, return_type, func_data[1], func_data[2])
        block = func.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)
        scope_stack.append({
            '@type': 'function',
            '@return_type': return_type
        })
        function_stack.append({
            '@return_type': return_type
        })
        for param, value in zip(func_data[2], func.args):
            val = builder.alloca(value.type)
            opt_store(builder, value, val)
            if param[1][0] == 'id':
                scope_stack[-1][param[1][1]] = {
                    'type': 'struct' if isinstance(type_map[param[0][-1]], ir.IdentifiedStructType) else 'val',
                    'val_type': param[0][-1],
                    'value': val
                }
            elif param[1][0] == 'pointer':
                scope_stack[-1][param[1][2][1]] = {
                    'type': 'struct_ptr' if isinstance(type_map[param[0][-1]], ir.IdentifiedStructType) else 'val_ptr',
                    'val_type': param[0][-1],
                    'value': val
                }
            elif param[1][0] == 'array_pointer':
                scope_stack[-1][param[1][1][1]] = {
                    'type': 'struct_ptr' if isinstance(type_map[param[0][-1]], ir.IdentifiedStructType) else 'val_ptr',
                    'val_type': param[0][-1],
                    'value': val
                }
        parse_compound_statement(exp[3], module, scope_stack, builder)
        function_stack.pop()
        scope_stack.pop()
    else:
        pass

