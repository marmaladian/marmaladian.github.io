#include "dir_stack.h"
#include "f_node.h"

int stack_push(dir_stack *s, f_node *n) {
    if (s->len == s->cap) {
        size_t nc = s->cap ? s->cap * 2 : 16;
        void *p = realloc(s->items, nc * sizeof *s->items);
        if (!p) return 0;
        s->items = p;
        s->cap = nc;
    }
    s->items[s->len++] = n;
    return 1;
}

f_node *stack_top(dir_stack *s) {
    return (s->len ? s->items[s->len - 1] : NULL);
}

void stack_pop(dir_stack *s) {
    if (s->len) s->len--;
}

void stack_free(dir_stack *s) {
    free(s->items);
    *s = (dir_stack){0};
}