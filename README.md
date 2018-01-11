# Compiler
A simple Compiler

## Development Environment
+ OS£ºWindows10, Mac
+ Programming Language£ºC + llvm + Python
+ C-Version£ºC11
+ Python-Version£ºPython3

## Installation

Remember to use python3.

### install llvm
For Linux user you can simply run
 
    sudo apt-get install llvm 

For Mac OS user you can simply run
 
    brew install homebrew/versions/llvm38

You can also install llvm by compling the source code.

### install llvmlite

    pip install llvmlite

### install PLY

    pip install PLY

## Usage

To Run source code, you can use the follow script
    
    python main.py [-o outfile] infile
   
For example
    
    python main.py KMP.c
    
Another example

    python main.py -o test.ll KMP.c

You can use `pyinstaller` to pack it.

## Directory

+ `lex.py`: The lex define of compiler
+ `yacc.py`: The yacc define of compiler
+ `Precompiler.py`: The Precompiler of compiler
+ `IRLibs.py`: The IR libs to generate IR code
+ `Compiler.py`: The compiler core to parse syntax tree
+ `main.py`: The entry to run compiler
+ `Debug.py`: Run compiler to compile `test.c` file
+ `test.c`': You can put your test code here when debugging