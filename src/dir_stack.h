#pragma once

#include "f_node.h"

typedef struct {
    f_node **items;
    size_t len, cap;
} dir_stack;

int stack_push(dir_stack *s, f_node *n);
f_node *stack_top(dir_stack *s);
void stack_pop(dir_stack *s);
void stack_free(dir_stack *s);