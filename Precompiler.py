file = open('main.cpp', 'r')

data = file.readlines()
strlen = "extern unsigned int strlen(char *s);\n"
printf = "extern int printf(const char *format,...);\n"
scanf = "int scanf(const char * restrict format,...);\n"
atoi = "int atoi(const char *nptr);\n"
getchar = "int getchar(void);\n"
string = strlen + printf + scanf + atoi + getchar
for line in data:
    if line.startswith('#'):
        if line.find("#define") != -1:
            str = line.split(" ")
            str[2] = str[2].strip('\n')
            index = 0
            for i in data:
                data[index] = i.replace(str[1], str[2])
                index = index + 1
    else:
        string = string + line

file1 = open('main.c', 'w')
file1.write(string)
file.close()
file1.close()