// fold.c
// static site builder

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fts.h>

#include "f_node.h"
#include "dir_stack.h"

// f_status to string
const char *f_status_str(f_status s) {
    switch (s) {
        case F_NEW: return "new";
        case F_LOAD_ERROR: return "load error";
        case F_PARSE_ERROR: return "parse error";
        case F_PENDING: return "pending";
        case F_OK: return "ok";
        default: return "unknown";
    }
}


int num_lines_in_file(FILE *fp) {
    int num_lines = 0;
    char buf[4096];
    while (fgets(buf, sizeof buf, fp)) {
        num_lines++;
    }
    return num_lines;
}


static void parse_file(FILE *fp) {
    // f->status = F_PARSE_ERROR;

    // read the file line by line
    // translate custom markup to html

    char buf[4096];
    while (fgets(buf, sizeof buf, fp)) {
        printf("line: %s", buf);
    }

    // f->status = F_OK;
}


// // read files
// f_status read_data_dir(char *path, f_node_vec *out) {
//     FTS *ftsp;  // file traversal system
//     FTSENT *f;  // entry
    
//     char *paths[] = {path, NULL};
    
//     ftsp = fts_open(paths, FTS_NOCHDIR, NULL);
//     if (!ftsp) {
//         perror("fts_open");
//         return F_LOAD_ERROR;
//     }

//     while ((f = fts_read(ftsp)) != NULL) {
//         if (f->fts_info == FTS_F) { // if it's a file

//             if (strlen(f->fts_name) < 3 || strcmp(f->fts_name + strlen(f->fts_name) - 2, ".f") != 0) {
//                 continue; // skip non-.f files
//             }

//             if (!node_vec_push(out, &f)) {
//                 perror("realloc/strdup");
//                 fts_close(ftsp);
//                 return F_LOAD_ERROR;
//             }
//         }
//     }
//     fts_close(ftsp);
//     return F_OK;
// }


f_node *build_tree(const char *root_path) {
    char *paths[] = {(char*)root_path, NULL};
    FTS *ftsp = fts_open(paths, FTS_NOCHDIR, NULL);
    if (!ftsp) { perror("fts_open"); return NULL; }

    dir_stack stack = {0};

    // create root node (index page)
    f_node *root = node_new(N_DIR, "index", root_path, NULL);
    if (!root) { fts_close(ftsp); return NULL; }
    if (!stack_push(&stack, root)) { node_free_recursive(root); fts_close(ftsp); return NULL; }

    for (FTSENT *e; (e = fts_read(ftsp)) != NULL; ) {
        switch (e->fts_info) {
        case FTS_D: {
            // skip root
            if (e->fts_level == 0) break;

            f_node *parent = stack_top(&stack);
            f_node *dir = node_new(N_DIR, e->fts_name, e->fts_path, parent);
            if (!dir) goto fail;

            if (!node_vec_push(&parent->children, dir)) {
                node_free_recursive(dir);
                goto fail;
            }
            if (!stack_push(&stack, dir)) goto fail;
            break;
        }

        case FTS_DP: {
            if (e->fts_level > 0) stack_pop(&stack);
            break;
        }

        case FTS_F: {
            f_node *parent = stack_top(&stack);
            f_node *file = node_new(N_FILE, e->fts_name, e->fts_path, parent);
            if (!file) goto fail;

            if (!node_vec_push(&parent->children, file)) {
                node_free_recursive(file);
                goto fail;
            }
            break;
        }

        case FTS_DNR:
        case FTS_ERR:
        case FTS_NS:
            break;
        }
    }

    fts_close(ftsp);
    stack_free(&stack);
    return root;

fail:
    fts_close(ftsp);
    stack_free(&stack);
    node_free_recursive(root);
    return NULL;
}


static void print_tree(const f_node *n, int depth) {
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


int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <directory>\n", argv[0]);
        return 1;
    }

    printf("Reading directory: %s\n", argv[1]);
    f_node *site = build_tree(argv[1]);

    print_tree(site, 0);

    // f_node_vec files = {0};

    // if (read_data_dir(argv[1], &files) != F_OK) return 1;

    // // status print
    // for (size_t i = 0; i < files.len; i++) {
    //     const char* status_str = f_status_str(files.items[i].status);
    //     printf("%4d %-40s\t%4d lines\t%s\n", (int)i+1, files.items[i].path, files.items[i].total_lines, 
    //            status_str);
    // }

    // // open file
    // for (size_t i = 0; i < files.len; i++) {
    //     f_node *f = &files.items[i];
    //     if (f->status != F_PENDING) continue;

    //     FILE *fp = fopen(f->path, "r");
    //     if (!fp) {
    //         perror("fopen");
    //         continue;
    //     }

    //     parse_file(fp);

    //     fclose(fp);
    // }

    
    // vec_free(&files);

    return 0;
}