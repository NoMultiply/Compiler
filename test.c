#include <stdio.h>
#include <string.h>

int main() {
    char str[100];
    int i, l;
    scanf("%s", str);
    l = strlen(str);
    for (i = 0; i < l / 2; ++i) {
        if (str[i] != str[l - 1 - i]) {
            printf("不是回文字符串\n");
            return 0;
        }
    }
    printf("是回文字符串\n");
    return 0;
}