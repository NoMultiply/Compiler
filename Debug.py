from main import Compile

file_in = open('test.c', 'r')

if __name__ == '__main__':
    Compile(file_in.readlines())


