struct cake_t {	// 16 bytes
    uint64_t price;
    char name[8];
};

struct shop_t {
    uint64_t sold;
    uint64_t customers;
    cake_t * cakes[16];
} shop;

void eat_line()
{
...
}

void fgets_eat(char * buf, size_t size)
{
    if (fgets(stdin, buf, size)) {
        char * p = strchr(buf, '\n');
        if (p == NULL) {
            eat_line();
        } else {
            *p = 0;
        }
    }
}

// protected by canary @ [rbp - 8]
uint64_t get()
{
    uint64_t result;
    scanf("%lu", &result);
    eat_line();
    return result;
}

void make(shop_t * arg)
{
    shop_t * s = arg;   // rbp - 0x28
    for(int var_14 = 0; var_14 <= 16; var_14++) {
        if (var_14 == 16) {
            puts("Ran out of counter space :(");
            continue;
        }

        if (s->cakes[var_14] == NULL) {
            break;
        }
    }

    printf("Making the cake");

    spin(100, 6);

    putchar('\n');

    cake_t * cake = malloc(sizeof(cake_t));
    s->cakes[var_14] = cake;
    if (NULL == s->cakes[var_14]) {
        puts("malloc() returned NULL. Out of Memory\n");
        exit(1);
    }

    printf("Made cake %d.\nName> ", var_14);
    fgets_eat(s->cakes[var_14]->name, 8);

    printf("Price> ");
    s->cakes[var_14]->price = get();
}

void serve(shop_t * s)
{
    shop_t * var_18 = s;

    printf("This customer looks really hungry. Which cake would you like to give them?\n> ");
    uint64_t var_8 = get();
    if (var_8 > 15 || NULL == var_18->cakes[var_8]) {
        puts("Oops! You reach for a cake that isn't there yet.");
        return;
    }

    printf("The customer looks really happy with %s!\n", var_18->cakes[var_8]->name);
    var_18->sold += var_18->cakes[var_8]->price;
    free(var_18->cakes[var_8]);
    // didn't clear the pointer after free, so chance of fastbin attack
    var_18->customers--;
}

void inspect(shop_t * s)
{
    shop_t * var_18 = s;

    printf("Which one?\n> ");
    uint64_t var_8 = get();
    if (var_8 > 15 || NULL == var_18->cakes[var_8]) {
        printf("You didn't make cake %lu yet.\n", var_18);
        return;
    }

printf("%s is being sold for $%lu\n",
    var_18->cakes[var_8]->name, var_18->cakes[var_8]->price);
}

int main(int argc, const char * argv[])
{
    alarm(180);
    setbuf(stdout, NULL);
    srand(735);	// why?

...

    while(1) {
        // generate some random values   
        if ((rand() % 3) == 0) {
           shop.customers++;
        }
        printf("In total, you have sold $%lu worth of merchandise, and have %lu customers waiting.\n", shop.sold, shop.customers);

...
    }

    return 0;
}
