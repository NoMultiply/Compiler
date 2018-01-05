def parse_declaration_specifiers(exp):
    # TODO
    if exp[1][0] == 'storage_class_specifier' and exp[1][1][1] == 'typedef':
        return exp[1][1][1]


def parse_init_declarator_list(exp):
    result = []
    for i in range(1, len(exp)):
        if exp[i][0] == 'init_declarator_list':
            result.extend(parse_init_declarator_list(exp[i]))
        elif exp[i][0] == 'init_declarator':
            result.append(parse_init_declarator(exp[i]))
    return result


def parse_init_declarator(exp):
    if len(exp) == 4:
        # TODO
        pass
    elif len(exp) == 2:
        return parse_declarator(exp[1])


def parse_declarator(exp):
    if len(exp) == 2:
        return parse_direct_declarator(exp[1])
    else:
        # TODO
        pass


def parse_direct_declarator(exp):
    if len(exp) == 2:
        return exp[1][1]
    else:
        # TODO
        pass