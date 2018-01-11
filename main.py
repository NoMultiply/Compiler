from lex import lexer
from yacc import YaccParser, ParseError
from Precompiler import precompile
from Compiler import parse_translation_unit
import sys

def Compile(data):
    data = precompile(data)
    parser = YaccParser()
    try:
        result = parser.parser.parse(data, lexer=lexer)
        assert result[0] == 'translation_unit'
        data = parse_translation_unit(result)
        print("Parse Successfully")
        return data
    except ParseError as e:
        print("Lexical or Syntax Error")
    except:
        print("Error when generate IR")
    return None

def main(argv: list):
    infile = ''
    outfile = ''
    if len(argv) == 2:
        infile = argv[1]
    elif len(argv) == 4 and argv[1] == '-o':
        outfile = argv[2]
        infile = argv[3]
    else:
        print('Usage: python main.py [-o outfile] infile')
        return
    try:
        filein = open(infile, 'r')
        data = Compile(filein.readlines())
        filein.close()
        if data:
            if outfile == '':
                try:
                    outfile = infile[:infile.rindex('.')] + '.ll'
                except ValueError:
                    outfile = infile + '.ll'
            fileout = open(outfile, 'w')
            fileout.write(data)
            fileout.close()
    except FileNotFoundError:
        print('Cannot find file: ', infile)


if __name__ == '__main__':
    main(sys.argv)

