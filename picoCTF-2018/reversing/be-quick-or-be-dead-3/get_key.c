#include <stdio.h>

int calc(int x) {
    if (x <= 4) {
        return x * x + 0x2345;
    }

    int c[5];    
    for(int i = 0; i < 5; i++) {
        c[i] = calc(i);
    }

    for(int i = 5; i <= x; i++) {
        int r = c[4] - c[3] + c[2] - c[1] + c[0] * 0x1234;
        for (int j = 0; j < 4; j++) {
            c[j] = c[j + 1];
        }
        c[4] = r;
    }

    return c[4];
}

int main() {
    printf("0x%08x\n", calc(0x186b5));
    return 0;
}
