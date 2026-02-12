// fold.c
// static site builder

// abstract the token splitting function
// build nav and add to pages
// insert page title in html title tag
// free memory
// handle front matter
// add figures and images
// build index page (nav, journal, intro)
// handle italics, bold
// handle code blocks, inline code, blockquotes, etc.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fts.h>

#include "f_node.h"
#include "dir_stack.h"
#include "f_tree.h"
#include "to_html.h"

// f_status to string
static const char *f_status_str(f_status s) {
    switch (s) {
        case F_NEW: return "new";
        case F_LOAD_ERROR: return "load error";
        case F_PARSE_ERROR: return "parse error";
        case F_PENDING: return "pending";
        case F_DONE: return "ok";
        default: return "unknown";
    }
}


// static int num_lines_in_file(FILE *fp) {
//     int num_lines = 0;
//     char buf[4096];
//     while (fgets(buf, sizeof buf, fp)) {
//         num_lines++;
//     }
//     return num_lines;
// }

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <directory>\n", argv[0]);
        return 1;
    }

    printf("Reading directory: %s\n", argv[1]);
    f_node *site = build_tree(argv[1]);

    print_tree(site, 0);

    erase_output_dir("docs");
    to_html("docs", site, site);

    //  copy static files    
    char *copy_dirs[] = {"css", "media", NULL};

    for (char **d = copy_dirs; *d; d++) {
        char src_path[4096], dst_path[4096];
        snprintf(src_path, sizeof src_path, "%s/%s", argv[1], *d);
        snprintf(dst_path, sizeof dst_path, "docs/%s", *d);
        printf("Copying directory %s to %s\n", src_path, dst_path);
        // use system cp command to copy the directory
        char cmd[8192];
        snprintf(cmd, sizeof cmd, "cp -r %s %s", src_path, dst_path);
        int r = system(cmd);
        if (r != 0) {
            fprintf(stderr, "Failed to copy directory %s: %d\n", *d, r);
        }
    }

    // vec_free(&files);

    return 0;
}