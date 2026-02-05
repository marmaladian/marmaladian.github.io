// f_node.h

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fts.h>

#include "f_node.h"

// vector of source files
int node_vec_push(f_node_vec *v, f_node *f) {
    if (v->len == v->cap) {
        size_t new_cap = v->cap ? v->cap * 2 : 32;
        void *p = realloc(v->items, new_cap * sizeof *v->items);
        if (!p) return 0;
        v->items = p;
        v->cap = new_cap;
    }

    v->items[v->len++] = f;
    return 1;
}

void node_vec_free(f_node_vec *v) {
    free(v->items);
    *v = (f_node_vec){0};
}


f_node *node_new(node_kind kind, const char *name, const char *path, f_node *parent) {
    f_node *n = calloc(1, sizeof *n);
    if (!n) return NULL;

    n->kind = kind;
    n->name = strdup(name ? name : "");
    n->path = strdup(path ? path : "");
    n->parent = parent;

    if (!n->name || !n->path) {
        free(n->name); free(n->path); free(n);
        return NULL;
    }

    n->status = F_NEW;
    n->total_lines = 0;
    return n;
}

void node_free_recursive(f_node *n) {
    if (!n) return;
    if (n->kind == N_DIR) {
        for (size_t i = 0; i < n->children.len; i++) {
            node_free_recursive(n->children.items[i]);
        }
        node_vec_free(&n->children);
    }
    free(n->name);
    free(n->path);
    free(n);
}