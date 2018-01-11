from llvmlite import ir
from llvmlite.ir._utils import DuplicatedNameError

CONSTANT = ['int', 'double', 'char']

int_type = ir.IntType(32)
char_type = ir.IntType(8)
double_type = ir.DoubleType()
char_ptr_type = char_type.as_pointer()
void_type = ir.VoidType()
bool_type = ir.IntType(1)
int64_type = ir.IntType(64)

type_map = {
    'int': int_type,
    'char': char_type,
    'double': double_type,
    'string': char_ptr_type,
    'void': void_type,
    'bool': bool_type,
    'int64': int64_type
}

struct_map = {}

loop_stack = []

function_stack = []

memcpy_name = None
memcpy_func = None
memset_name = None
memset_func = None

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
        identifier = None
        if isinstance(array, tuple):
            identifier = get_identifier(scope_stack, array[1])
        item = get_pointer(scope_stack, builder, array)
        if identifier and identifier['type'] == 'val_ptr':
            item = builder.load(item)
            return builder.gep(item, [index], True)
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

def get_bool(scope_stack, builder: ir.IRBuilder, value):
    value = get_value(scope_stack, builder, value)
    if isinstance(value, ir.Constant):
        return bool_type(1 if value.constant else 0)
    if isinstance(value.type, ir.DoubleType):
        return builder.fcmp_ordered('!=', value, value.type(0))
    if isinstance(value.type, ir.IntType) and value.type.width != 1:
        return builder.icmp_signed('!=', value, value.type(0))
    return value


def get_type_rank(item):
    if isinstance(item, ir.DoubleType):
        return (5, float)
    elif isinstance(item, ir.IntType) and item.width == int_type.width:
        return (3, int)
    elif isinstance(item, ir.IntType) and item.width == char_type.width:
        return (1, int)
    elif isinstance(item, ir.IntType) and item.width == 1:
        return (0, bool)
    else:
        return (6, None)

def get_proper_type(*type_list):
    assert len(type_list) > 0
    proper_type = type_list[0]
    proper_type_item = get_type_rank(proper_type)
    for item in type_list[1:]:
        rank_item = get_type_rank(item)
        if  rank_item[0] > proper_type_item[0] :
            proper_type = item
            proper_type_item = rank_item
    return (proper_type, proper_type_item[1])


def type_check(builder: ir.IRBuilder, lhs, rhs):
    if isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
        pass
    elif isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
        if lhs.type.width == rhs.type.width:
            pass
        elif lhs.type.width > rhs.type.width:
            rhs = convert(builder, rhs, lhs.type)
        elif lhs.type.width < rhs.type.width:
            lhs = convert(builder, lhs, rhs.type)
        assert lhs.type.width == rhs.type.width
    elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.IntType):
        rhs = convert(builder, rhs, lhs.type)
    elif isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.DoubleType):
        lhs = convert(builder, lhs, rhs.type)
    assert lhs.type == rhs.type
    return (lhs, rhs)

def opt_base(builder: ir.IRBuilder, lhs, rhs, int_opt, double_opt):
    lhs, rhs = type_check(builder, lhs, rhs)
    if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
        return int_opt(lhs, rhs)
    elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
        return double_opt(lhs, rhs)


def opt_add(builder: ir.IRBuilder, lhs, rhs):
    return opt_base(builder, lhs, rhs, builder.add, builder.fadd)
    # if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
    #     return builder.add(lhs, rhs)
    # elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
    #     return builder.fadd(lhs, rhs)

def opt_sub(builder: ir.IRBuilder, lhs, rhs):
    return opt_base(builder, lhs, rhs, builder.sub, builder.fsub)
    # if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
    #     return builder.sub(lhs, rhs)
    # elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
    #     return builder.fsub(lhs, rhs)

def opt_mul(builder: ir.IRBuilder, lhs, rhs):
    return opt_base(builder, lhs, rhs, builder.mul, builder.fmul)
    # if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
    #     return builder.mul(lhs, rhs)
    # elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
    #     return builder.fmul(lhs, rhs)

def opt_div(builder: ir.IRBuilder, lhs, rhs):
    return opt_base(builder, lhs, rhs, builder.udiv, builder.fdiv)
    # if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
    #     return builder.udiv(lhs, rhs)
    # elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
    #     return builder.fdiv(lhs, rhs)

def opt_rem(builder: ir.IRBuilder, lhs, rhs):
    return opt_base(builder, lhs, rhs, builder.urem, builder.frem)
    # if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
    #     return builder.urem(lhs, rhs)
    # elif isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
    #     return builder.frem(lhs, rhs)

def opt_cmp(builder: ir.IRBuilder, cmpop, lhs, rhs):
    if isinstance(lhs, ir.Constant):
        if type(lhs.type) != type(rhs.type):
            lhs = rhs.type(get_type_rank(rhs.type)[1](lhs.constant))
        if isinstance(rhs.type, ir.DoubleType):
            return builder.fcmp_ordered(cmpop, lhs, rhs)
        elif isinstance(rhs.type, ir.IntType):
            return builder.icmp_signed(cmpop, lhs, rhs)
    elif isinstance(rhs, ir.Constant):
        if type(rhs.type) != type(lhs.type):
            rhs = lhs.type(get_type_rank(lhs.type)[1](rhs.constant))
        if isinstance(lhs.type, ir.DoubleType):
            return builder.fcmp_ordered(cmpop, lhs, rhs)
        elif isinstance(lhs.type, ir.IntType):
            return builder.icmp_signed(cmpop, lhs, rhs)
    else:
        lhs, rhs = type_check(builder, lhs, rhs)
        if isinstance(lhs.type, ir.DoubleType) and isinstance(rhs.type, ir.DoubleType):
            return builder.fcmp_ordered(cmpop, lhs, rhs)
        elif isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
            return builder.icmp_signed(cmpop, lhs, rhs)


def opt_store(builder: ir.IRBuilder, value, ptr):
    assert isinstance(ptr.type, ir.PointerType)
    if isinstance(value, ir.Constant) and type(value.type) != type(ptr.type.pointee):
        value = ptr.type(get_type_rank(ptr.type.pointee)[1](value.constant))
    else:
        proper_type = get_proper_type(value.type, ptr.type.pointee)
        if type(value.type) != type(proper_type[0]):
            value = convert(builder, value, proper_type[0])
    builder.store(value, ptr)

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
            elif arg[1][0] == 'array_pointer':
                arg_type = type_map[arg[0][-1]].as_pointer()
            else:
                arg_type = type_map[arg[0][-1]]
        else:
            if arg == '...':
                var_arg = True
                arg_type = None
            else:
                arg_type = type_map[arg[0][-1]]
        if arg_type and not isinstance(arg_type, ir.VoidType):
            arg_list.append(arg_type)
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
        val = builder.alloca(type_map[type_list[-1]], name = module.get_unique_name(val_name[1]))
        if val_value:
            opt_store(builder, val_value, val)
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
        val = ir.GlobalVariable(module, val_type, module.get_unique_name(val_name[2][1]))
        if val_value:
            val.initializer = val_value
    else:
        val = builder.alloca(val_type, name = module.get_unique_name(val_name[2][1]))
        if val_value:
            opt_store(builder, val_value, val)
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
        val = builder.alloca(array_type, name = module.get_unique_name(val_name[1]))
        # if val_value:
        #     opt_store(builder, val_value, val)
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
    if isinstance(value, ir.Constant):
        return type(get_type_rank(type)[1](value.constant))
    elif isinstance(type, ir.IntType) and isinstance(value.type, ir.IntType):
        if type.width > value.type.width:
            return builder.zext(value, type)
        elif type.width < value.type.width:
            return builder.trunc(value, type)
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


def insert_memcpy(module: ir.Module, scope_stack: list):
    """declare void @llvm.memcpy.p0i8.p0i8.i32(i8* nocapture, i8* nocapture readonly, i32, i32, i1) #1"""
    global memcpy_name
    global memcpy_func
    memcpy_name = 'llvm.memcpy.p0i8.p0i8.i32'
    memcpy_func = insert_function(module, scope_stack, ['void'], ('id', memcpy_name),
                    [[['char'], ('pointer', ['*'])], [['char'], ('pointer', ['*'])],
                     [['int']], [['int']], [['bool']]])
    return memcpy_func

def memcpy(module: ir.Module, scope_stack: list, builder: ir.IRBuilder, dst, src, len, size):
    size >>= 3
    dst = get_pointer(scope_stack, builder, dst)
    insert_memcpy(module, scope_stack)
    builder.call(memcpy_func, [builder.bitcast(dst, char_ptr_type), src, int_type(len), int_type(size), bool_type(0)])


def insert_memset(module: ir.Module, scope_stack: list):
    """declare void @llvm.memset.p0i8.i32(i8* nocapture, i8, i32, i32, i1)"""
    global memset_name
    global memset_func
    memset_name = 'llvm.memset.p0i8.i32'
    memset_func = insert_function(module, scope_stack, ['void'], ('id', memset_name),
                    [[['char'], ('pointer', ['*'])], [['char']],
                     [['int']], [['int']], [['bool']]])
    return memset_func

def get_type_size(type):
    if isinstance(type, ir.DoubleType):
        return 8
    elif isinstance(type, ir.IntType):
        return type.width
    raise AssertionError

def memzero(module: ir.Module, scope_stack: list, builder: ir.IRBuilder, dst, len):
    len *= get_type_size(dst.type.pointee.element)
    len >>= 3
    dst = get_pointer(scope_stack, builder, dst)
    insert_memset(module, scope_stack)
    builder.call(memset_func, [builder.bitcast(dst, char_ptr_type), char_type(0), int_type(len), int_type(4), bool_type(0)])