// f_tree.c

#include "f_node.h"
#include "dir_stack.h"

int handle_file(FTSENT *entry, dir_stack *stack) {
    // only if file name is .f
    size_t len = strlen(entry->fts_name);
    if (len < 3 || strcmp(entry->fts_name + len - 2, ".f") != 0) return 0;
    
    char *friendly_name = strndup(entry->fts_name, len - 2);
    if (!friendly_name) return -1;
    f_node *parent = stack_top(stack);
    f_node *file = node_new(N_FILE, friendly_name, entry->fts_path, parent);
    if (!file) return -1;

    if (!node_vec_push(&parent->children, file)) {
        node_free_recursive(file);
        return -1;
    }

    return 0;
}

int handle_dir(FTSENT *entry, dir_stack *stack) {
    // skip root
    if (entry->fts_level == 0) return 0;

    f_node *parent = stack_top(stack);
    f_node *dir_node = node_new(N_DIR, entry->fts_name, entry->fts_path, parent);
    
    if (!dir_node) return -1;

    if (!node_vec_push(&parent->children, dir_node)) {
        node_free_recursive(dir_node);
        return -1;
    }

    if (!stack_push(stack, dir_node)) return -1;

    return 0;
}

f_node *build_tree(const char *root_path) {
    char *paths[] = {(char*)root_path, NULL};
    FTS *tree = fts_open(paths, FTS_NOCHDIR, NULL);
    if (!tree) { perror("fts_open"); return NULL; }

    dir_stack stack = {0};

    // create root node (index page)
    f_node *root = node_new(N_DIR, "index", root_path, NULL);
    if (!root) { fts_close(tree); return NULL; }
    if (!stack_push(&stack, root)) { node_free_recursive(root); fts_close(tree); return NULL; }

    for (FTSENT *entry; (entry = fts_read(tree)) != NULL; ) {
        switch (entry->fts_info) {
        case FTS_D:
            if (handle_dir(entry, &stack) != 0) goto fail;
            break;
        case FTS_DP:
            // if we are leaving a directory, pop the stack
            if (entry->fts_level > 0) stack_pop(&stack);
            break;
        case FTS_F:
            if (handle_file(entry, &stack) != 0) goto fail;
            break;
        case FTS_DNR:
        case FTS_ERR:
        case FTS_NS:
        default:
            break;
        }
    }

    fts_close(tree);
    stack_free(&stack);
    return root;

fail:
    fts_close(tree);
    stack_free(&stack);
    node_free_recursive(root);
    return NULL;
}

void print_tree(const f_node *n, int depth) {
    for (int i = 0; i < depth; i++) printf("  ");

    if (n->kind == N_DIR)
        printf("[D] %s\n", n->name);
    else
        printf("[F] %s (%d lines)\n", n->name, n->total_lines);

    if (n->kind == N_DIR) {
        for (size_t i = 0; i < n->children.len; i++)
            print_tree(n->children.items[i], depth + 1);
    }
}

