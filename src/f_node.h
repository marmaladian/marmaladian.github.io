// f_node.h

#pragma once
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fts.h>

#include "f_node.h"

typedef enum {
    F_NEW,
    F_LOAD_ERROR,
    F_PARSE_ERROR,
    F_PENDING,
    F_OK
} f_status;

typedef enum {
    N_FILE,
    N_DIR
} node_kind;

typedef struct f_node f_node;

typedef struct {
    f_node **items;
    size_t len;
    size_t cap;
} f_node_vec;

struct f_node {
    node_kind kind;

    char *name;
    char *path;
    
    f_node* parent;
    f_node_vec children;

    int total_lines;
    f_status status;
};

int node_vec_push(f_node_vec *v, f_node *f);
void node_vec_free(f_node_vec *v);

f_status read_data_dir(char *path, f_node_vec *out);

f_node *node_new(node_kind kind, const char *name, const char *path, f_node *parent);
void node_free_recursive(f_node *n);