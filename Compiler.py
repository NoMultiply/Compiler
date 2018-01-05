from llvmlite import ir
from llvmlite.ir._utils import DuplicatedNameError

int_type = ir.IntType(32)
char_type = ir.IntType(8)
double_type = ir.DoubleType()
float_type = ir.FloatType()
void_type = ir.VoidType()
char_ptr_type = ir.IntType(8).as_pointer()

type_map = {
    'int': int_type,
    'char': char_type,
    'double': double_type,
    'float': float_type,
    'void': void_type,
    'string': char_ptr_type
}


def parse_translation_unit(exp):
    module = ir.Module(name=__file__)
    parse_function_definition(exp[2], module)
    file_data = str(module)
    file_data = '\n'.join(file_data.split('\n')[4:])
    return file_data


def parse_function_definition(exp, module: ir.Module):
    function_type = ir.FunctionType(type_map[exp[1][1]], ())
    func = ir.Function(module, function_type, name=exp[2][1])
    block = func.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    parse_compound_statement(exp[5], module, builder)


def parse_compound_statement(exp, module: ir.Module, builder: ir.IRBuilder):
    parse_statement_list(exp[2], module, builder)


def parse_statement_list(exp, module: ir.Module, builder: ir.IRBuilder):
    for i in range(1, len(exp)):
        if exp[i][0] == 'statement_list':
            parse_statement_list(exp[i], module, builder)
        elif exp[i][0] == 'statement':
            parse_statement(exp[i][1], module, builder)


def parse_statement(exp, module: ir.Module, builder: ir.IRBuilder):
    parse_expression_statement(exp[1], module, builder)


def parse_expression_statement(exp, module: ir.Module, builder: ir.IRBuilder):
    parse_expression(exp, module, builder)


def parse_expression(exp, module: ir.Module, builder: ir.IRBuilder):
    if exp[1][0] == 'postfix_expression':
        parse_postfix_expression(exp[1], module, builder)
    elif exp[1][0] == 'return_expression':
        parse_return_expression(exp[1], module, builder)


def parse_postfix_expression(exp, module: ir.Module, builder: ir.IRBuilder):
    if len(exp) == 4:
        pass
    elif len(exp) == 5:
        func_name = parse_primary_expression(exp[1])
        raw_arg_list = parse_argument_expression_list(exp[3])
        if func_name[1] == 'printf':
            function_type = ir.FunctionType(int_type, (ir.PointerType(ir.IntType(8)), ))
            global printf_func
            try:
                printf_func = ir.Function(module, function_type, "printf")
            except DuplicatedNameError:
                pass
            arg_list = []
            for arg in raw_arg_list:
                if arg[0] == 'string':
                    data = eval("'%s'" % arg[1]) + '\00'
                    str_type = ir.ArrayType(char_type, len(data))
                    const_string = ir.Constant(str_type, bytearray(data.encode()))
                    global_string = ir.GlobalVariable(module, str_type, module.get_unique_name(''))
                    global_string.initializer = const_string
                    str_ptr = builder.gep(global_string, [int_type(0), int_type(0)], True)
                    arg_list.append(ir.IntType(8).as_pointer()(str_ptr.get_reference()))
            builder.call(printf_func, arg_list)



def parse_argument_expression_list(exp):
    result = ()
    for i in range(1, len(exp)):
        if exp[i][0] == 'primary_expression':
            result = (*result, exp[i][1])
        elif exp[i][0] == 'argument_expression_list':
            result = (*result, *(parse_argument_expression_list(exp[i][1])), )
    return result


def parse_primary_expression(exp):
    return exp[1]


def parse_return_expression(exp, module: ir.Module, builder: ir.IRBuilder):
    builder.ret(type_map[exp[2][0]](exp[2][1]))