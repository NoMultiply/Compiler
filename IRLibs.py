from llvmlite import ir

CONSTANT = ['int', 'double', 'char']

int_type = ir.IntType(32)
char_type = ir.IntType(8)
double_type = ir.DoubleType()
char_ptr_type = char_type.as_pointer()

type_map = {
    'int': int_type,
    'char': char_type,
    'double': double_type,
    'string': char_ptr_type
}

def insert_function(module: ir.Module, scope_stack: list, return_type: list, func_name: tuple, raw_arg_list: list):
    return_type = type_map[return_type[-1]]
    func_name = func_name[1]
    var_arg = False
    arg_list = []
    for arg in raw_arg_list:
        if isinstance(arg, list):
            if arg[1][0] == 'pointer':
                arg_type = type_map[arg[0][-1]]
                for pointer in arg[1][1]:
                    if pointer == '*':
                        arg_type = arg_type.as_pointer()
                arg_list.append(arg_type)
            else:
                arg_list.append(type_map[arg[0][-1]])
        else:
            if arg == '...':
                var_arg = True
    func_type = ir.FunctionType(return_type, arg_list, var_arg)
    func = ir.Function(module, func_type, func_name)
    scope_stack[-1][func_name] = {
        'type': 'function',
        'value': func
    }
    return func


def insert_val(module: ir.Module, scope_stack: list, builder: ir.IRBuilder, type: list, val_name: tuple, val_value = None):
    if builder is None:
        val = ir.GlobalVariable(module, type_map[type[-1]], module.get_unique_name(val_name[1]))
        if val_value:
            val.initializer = val_value
    else:
        val = builder.alloca(type_map[type[-1]])
        if val_value:
            builder.store(val_value, val)
    scope_stack[-1][val_name[1]] = {
        'type': 'val',
        'value': val
    }
    return val

def insert_string(module: ir.Module, scope_stack: list, builder: ir.IRBuilder, raw_data: str, prt = False):
    try:
        global_string = scope_stack[0][raw_data]
    except KeyError:
        data = eval('%s' % raw_data)
        data += '\00'
        data = data.encode()
        str_type = ir.ArrayType(char_type, len(data))
        const_string = ir.Constant(str_type, bytearray(data))
        global_string = ir.GlobalVariable(module, str_type, module.get_unique_name(raw_data))
        global_string.initializer = const_string
        scope_stack[0][raw_data] = global_string
    if prt:
        return builder.gep(global_string, [int_type(0), int_type(0)], True)
    else:
        return global_string
