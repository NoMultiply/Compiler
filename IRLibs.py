from llvmlite import ir
from llvmlite.ir._utils import DuplicatedNameError

CONSTANT = ['int', 'double', 'char']

int_type = ir.IntType(32)
char_type = ir.IntType(8)
double_type = ir.DoubleType()
char_ptr_type = char_type.as_pointer()
void_type = ir.VoidType()

type_map = {
    'int': int_type,
    'char': char_type,
    'double': double_type,
    'string': char_ptr_type,
    'void': void_type
}

struct_map = {}

loop_stack = []

function_stack = []

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
    elif isinstance(item, tuple) and item[0] == 'array_index':
        item = item[1]
    elif isinstance(item, tuple) and item[0] == 'struct':
        item = get_struct_pointer(scope_stack, builder, item[1], item[2])
    elif isinstance(item, tuple) and item[0] == 'struct_ptr':
        item = get_struct_ptr_pointer(scope_stack, builder, item[1], item[2])
    return item


def get_value(scope_stack, builder: ir.IRBuilder, item):
    if isinstance(item, tuple) and item[0] == 'id':
        identifier = get_identifier(scope_stack, item[1])
        item = identifier['value']
        if item.opname == 'alloca' and identifier['type'] != 'array':
            item = builder.load(item)
        elif item.opname == 'alloca' and identifier['type'] == 'array':
            item = builder.gep(item, [int_type(0), int_type(0)])
    elif isinstance(item, tuple) and item[0] == 'array_index':
        item = builder.load(item[1])
    elif isinstance(item, tuple) and item[0] == 'struct':
        item = get_struct_pointer(scope_stack, builder, item[1], item[2])
        item = builder.load(item)
    elif isinstance(item, tuple) and item[0] == 'struct_ptr':
        item = get_struct_ptr_pointer(scope_stack, builder, item[1], item[2])
        item = builder.load(item)
    return item


def get_pointer_value(scope_stack, builder: ir.IRBuilder, item):
    item = get_pointer(scope_stack, builder, item)
    return builder.load(item)


def get_array_pointer(scope_stack, builder: ir.IRBuilder, array, index):
    if isinstance(array, tuple) and array[0] == 'struct':
        item = get_struct_pointer(scope_stack, builder, array[1], array[2])
    elif isinstance(array, tuple) and array[0] == 'struct_ptr':
        item = get_struct_ptr_pointer(scope_stack, builder, array[1], array[2])
    else:
        item = get_pointer(scope_stack, builder, array)
    return builder.gep(item, [int_type(0), index], True)


def get_struct_pointer(scope_stack, builder: ir.IRBuilder, struct, item, index = int_type(0)):
    identifier = get_identifier(scope_stack, struct)
    assert identifier['type'] == 'struct'
    item = struct_map[identifier['val_type']][item]
    return builder.gep(identifier['value'], [index, item['index']], True)


def get_struct_ptr_pointer(scope_stack, builder: ir.IRBuilder, struct, item, index = int_type(0)):
    identifier = get_identifier(scope_stack, struct)
    assert identifier['type'] == 'struct_ptr'
    item = struct_map[identifier['val_type']][item]
    value = builder.load(identifier['value'])
    return builder.gep(value, [index, item['index']], True)


def opt_add(builder: ir.IRBuilder, lhs, rhs):
    if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
        return builder.add(lhs, rhs)
    elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
        return builder.fadd(lhs, rhs)

def opt_sub(builder: ir.IRBuilder, lhs, rhs):
    if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
        return builder.sub(lhs, rhs)
    elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
        return builder.fsub(lhs, rhs)

def opt_mul(builder: ir.IRBuilder, lhs, rhs):
    if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
        return builder.mul(lhs, rhs)
    elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
        return builder.fmul(lhs, rhs)

def opt_div(builder: ir.IRBuilder, lhs, rhs):
    if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
        return builder.udiv(lhs, rhs)
    elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
        return builder.fdiv(lhs, rhs)

def opt_rem(builder: ir.IRBuilder, lhs, rhs):
    if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
        return builder.urem(lhs, rhs)
    elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
        return builder.frem(lhs, rhs)

def opt_cmp(builder: ir.IRBuilder, cmpop, lhs, rhs):
    if isinstance(lhs, ir.Constant):
        if isinstance(rhs.type, ir.DoubleType):
            rhs = rhs.type(lhs.constant)
            return builder.fcmp_ordered(cmpop, lhs, rhs)
    elif isinstance(rhs, ir.Constant):
        if isinstance(lhs.type, ir.DoubleType):
            rhs = lhs.type(rhs.constant)
            return builder.fcmp_ordered(cmpop, lhs, rhs)
    elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
        return builder.fcmp_ordered(cmpop, lhs, rhs)
    return builder.icmp_signed(cmpop, lhs, rhs)

def insert_function(module: ir.Module, scope_stack: list, return_type: list, func_name: tuple, raw_arg_list: list):
    return_type = type_map[return_type[-1]]
    func_name = func_name[1]
    var_arg = False
    arg_list = []
    for arg in raw_arg_list:
        if isinstance(arg, list) and len(arg) > 1:
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
    try:
        func = ir.Function(module, func_type, func_name)
    except DuplicatedNameError:
        func = get_identifier(scope_stack, func_name)['value']
    scope_stack[-1][func_name] = {
        'type': 'function',
        'value': func
    }
    return func


def insert_val(module: ir.Module, scope_stack: list, builder: ir.IRBuilder, type_list: list, val_name: tuple, val_value = None):
    if builder is None:
        val = ir.GlobalVariable(module, type_map[type_list[-1]], module.get_unique_name(val_name[1]))
        if val_value:
            val.initializer = val_value
    else:
        val = builder.alloca(type_map[type_list[-1]])
        if val_value:
            builder.store(val_value, val)
    scope_stack[-1][val_name[1]] = {
        'type': 'struct' if isinstance(type_map[type_list[-1]], ir.IdentifiedStructType) else 'val',
        'val_type': type_list[-1],
        'value': val
    }
    return val


def insert_pointer(module: ir.Module, scope_stack: list, builder: ir.IRBuilder, type_list: list, val_name: tuple, val_value = None):
    val_type = type_map[type_list[-1]]
    for pointer in val_name[1]:
        if pointer == '*':
            val_type = val_type.as_pointer()
    if builder is None:
        val = ir.GlobalVariable(module, val_type, module.get_unique_name(val_name[1]))
        if val_value:
            val.initializer = val_value
    else:
        val = builder.alloca(val_type)
        if val_value:
            builder.store(val_value, val)
    scope_stack[-1][val_name[2][1]] = {
        'type': 'struct_ptr' if isinstance(type_map[type_list[-1]], ir.IdentifiedStructType) else 'val_ptr',
        'val_type': type_list[-1],
        'value': val
    }
    return val


def insert_array(module: ir.Module, scope_stack: list, builder: ir.IRBuilder, type: list, num, val_name: tuple, val_value = None):
    array_type = ir.ArrayType(type_map[type[-1]], num.constant)
    if builder is None:
        val = ir.GlobalVariable(module, array_type, module.get_unique_name(val_name[1]))
        if val_value:
            val.initializer = val_value
    else:
        val = builder.alloca(array_type)
        if val_value:
            builder.store(val_value, val)
    scope_stack[-1][val_name[1]] = {
        'type': 'array',
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

def convert(builder: ir.IRBuilder, value, type):
    if isinstance(type, ir.IntType) and isinstance(value.type, ir.IntType):
        return builder.zext(value, type)
    elif isinstance(type, ir.DoubleType) and isinstance(value.type, ir.IntType):
        return builder.sitofp(value, type)
    elif isinstance(type, ir.IntType) and isinstance(value.type, ir.DoubleType):
        return builder.fptosi(value, type)
    return value

def insert_type(module: ir.Module, scope_stack: list, builder: ir.IRBuilder, type, name):
    assert name not in type_map
    try:
        type_map[name] = type_map[type]
    except (KeyError, TypeError):
        if type['type'] == 'struct':
            ir.IdentifiedStructType(module.context, name)
            struct = module.context.get_identified_type(name)
            type_map[name] = struct
            struct_list = type['list']
            elems = []
            struct_map[name] = {}
            index = 0
            for item in struct_list:
                item_type = type_map[item[0]]
                for id in item[1]:
                    if id[0] == 'id':
                        elems.append(item_type)
                        struct_map[name][id[1]] = {
                            'type': 'val',
                            'index': int_type(index)
                        }
                    elif id[0] == 'array':
                        array_type = ir.ArrayType(item_type, id[2].constant)
                        elems.append(array_type)
                        struct_map[name][id[1][1]] = {
                            'type': 'array',
                            'index': int_type(index)
                        }
                    index += 1
            struct.set_body(*elems)
    return type_map[name]