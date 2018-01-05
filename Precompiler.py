import re
from lex import lexer


system_files_all = ['stdio.h', 'stdlib.h', 'string.h']
system_functions_dict = {
    'printf': "extern int printf(const char *format,...);\n",
    'scanf': "int scanf(const char * format,...);\n",
    'getchar': "int getchar(void);\n",
    'atoi': "int atoi(const char *nptr);\n",
    'strlen': "extern unsigned int strlen(char *s);\n"
}
system_functions_all = {
    'stdio.h': ['printf', 'scanf', 'getchar'],
    'stdlib.h': ['atoi',],
    'string.h': ['strlen',]
}


def precompile(file_lines):
    result = ''
    system_functions = []
    define_map = {}
    for line in file_lines:
        temp_line = line.strip()
        if temp_line.startswith('#define'):
            define_unit = re.split('\s+', line)
            define_map[define_unit[1]] = define_unit[2]
            continue
        elif line.startswith('#include'):
            try:
                match_obj = re.match('#include\s+<(.+)>', temp_line)
                if match_obj:
                    raise KeyError
                else:
                    match_obj = re.match('#include\s+"(.+)"', temp_line)
                    if match_obj:
                        raise KeyError
            except KeyError:
                if match_obj.group(1) in system_files_all:
                    system_functions.extend(system_functions_all[match_obj.group(1)])
                    continue
        result += line
    lexer.input(result)
    replace_list = []
    system_function_list = []
    system_functions_string = ''
    while True:
        tok = lexer.token()
        if not tok:
            break
        if tok.type == 'IDENTIFIER':
            tok_val = tok.value[1]
            if tok_val in define_map:
                replace_list.append((tok_val, tok.lexpos))
                tok_val = define_map[tok_val]
            if tok_val in system_functions and not tok_val in system_function_list:
                system_function_list.append(tok_val)
                system_functions_string += system_functions_dict[tok_val]
    replace_result = ''
    for item in reversed(replace_list):
        replace_result = define_map[item[0]] + result[item[1] + len(item[0]):] + replace_result
        result = result[:item[1]]
    result += replace_result
    result = system_functions_string + result
    return result
