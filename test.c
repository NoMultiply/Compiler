#include <stdio.h>
#include <string.h>

int main() {
    char str[100];
    int i, l;
    scanf("%s", str);
    l = strlen(str);
    for (i = 0; i < l / 2; ++i) {
        if (str[i] != str[l - 1 - i]) {
            printf("���ǻ����ַ���\n");
            return 0;
        }
    }
    printf("�ǻ����ַ���\n");
    return 0;
}