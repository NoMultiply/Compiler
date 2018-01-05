from llvmlite import ir


type_map = {
    'int': ir.IntType()
}


def parse_translation_unit(exp):
    global module
    module = ir.Module(name=__file__)
    parse_function_definition(exp[2])


def parse_function_definition(exp):
    pass