#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#define STACK_SIZE 100

typedef struct {
    double data[STACK_SIZE];
    int pos;
} stack;

void init_stack(stack * s) {
    s->pos = 0;
}

int push_stack(stack * s, double e) {
    if (s->pos >= STACK_SIZE)
        return 1;
    s->data[s->pos++] = e;
    return 0;
}

int pop_stack(stack * s, double * e) {
    if (s->pos == 0)
        return 1;
    *e = s->data[--s->pos];
    return 0;
}

int top_stack(stack * s, double * e) {
    if (s->pos == 0)
        return 1;
    *e = s->data[s->pos - 1];
    return 0;
}

int empty_stack(stack * s) {
    return s->pos == 0;
}

int rank(double opt) {
    switch ((int)opt) {
    case '(':
        return 0;
    case '+':
    case '-':
        return 1;
    case '*':
    case '/':
        return 2;
    default:
        return -1;
    }
}

double calculate(double a, double opt, double b) {
    switch ((int)opt) {
    case '+':
        return a + b;
    case '-':
        return a - b;
    case '*':
        return a * b;
    case '/':
        return a / b;
    default:
        return 0;
    }
}

int main() {
    while (1) {
        char str[STACK_SIZE];
        stack opt_stack;
        stack num_stack;
        char num_str[10];
        int num_str_pos = 0;
        int l;
        int error = 0;
        int i;
        printf("Input: ");
        scanf("%[^\n]", str);
	    getchar();
        l = strlen(str);
        str[l] = ')';
        ++l;
        init_stack(&opt_stack);
        init_stack(&num_stack);
        if (push_stack(&opt_stack, '(')) {
            error = 1;
        }
        for (i = 0; i < l; ++i) {
            if (str[i] >= '0' && str[i] <= '9') {
                num_str[num_str_pos++] = str[i];
            }
            else if (str[i] == '(') {
                if (push_stack(&opt_stack, str[i])) {
                    error = 1;
                    break;
                }
            }
            else if (str[i] == ')' || str[i] == '+' || str[i] == '-'
                || str[i] == '*' || str[i] == '/' || str[i] == '#') {
                if (num_str_pos) {
                    num_str[num_str_pos] = '\0';
                    if (push_stack(&num_stack, atoi(num_str))) {
                        error = 1;
                        break;
                    }
                    num_str_pos = 0;
                }
                else if (str[i] == '-') {
                    num_str[num_str_pos++] = str[i];
                    continue;
                }
                else if (str[i] == '+') {
                    continue;
                }
                if (str[i] == ')') {
                    while (1) {
                        double opt;
                        double b;
                        double a;
                        if (pop_stack(&opt_stack, &opt)) {
                            error = 1;
                            break;
                        }
                        if (opt == '(') {
                            break;
                        }

                        if (pop_stack(&num_stack, &b)) {
                            error = 1;
                            break;
                        }
                        if (pop_stack(&num_stack, &a)) {
                            error = 1;
                            break;
                        }
                        if (push_stack(&num_stack, calculate(a, opt, b))) {
                            error = 1;
                            break;
                        }
                    }
                }
                else {
                    double top;
                    if (top_stack(&opt_stack, &top)) {
                        error = 1;
                        break;
                    }
                    while (rank(str[i]) <= rank(top)) {
                        double opt;
                        double b;
                        double a;
                        if (pop_stack(&opt_stack, &opt)) {
                            error = 1;
                            break;
                        }
                        if (opt == '#') {
                            break;
                        }
                        if (pop_stack(&num_stack, &b)) {
                            error = 1;
                            break;
                        }
                        if (pop_stack(&num_stack, &a)) {
                            error = 1;
                            break;
                        }
                        if (push_stack(&num_stack, calculate(a, opt, b))) {
                            error = 1;
                            break;
                        }
                    }
                    if (error) {
                        break;
                    }
                    if (push_stack(&opt_stack, str[i])) {
                        error = 1;
                        break;
                    }
                }
            }
            else {
                error = 1;
                break;
            }
            if (error) {
                break;
            }
        }
        if (num_stack.pos != 1 || opt_stack.pos != 0) {
            error = 1;
        }
        if (error) {
            printf("Error formulation.\n");
        }
        else {
            double num;
            pop_stack(&num_stack, &num);
            str[l - 1] = '\0';
            printf("Result: %s=%g\n", str, num);
        }
    }
    return 0;
}
