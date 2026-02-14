// to_html.c

#include "to_html.h"
#include <sys/stat.h>
#include <unistd.h>
#include <stddef.h>

static const char *header = "<!doctype html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                "<link rel=\"stylesheet\" href=\"../../css/default.css\">\n"
                "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">\n"
                "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>\n"
                "<link href=\"https://fonts.googleapis.com/css2?family=Baskervville:ital,wght@0,400..700;1,400..700&display=swap\" rel=\"stylesheet\">\n"
                "<link href=\"https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap\" rel=\"stylesheet\">\n"
                "<title>XXXYYYZZZ &mdash; Benjamin Grayland</title>\n"
                "</head>\n"
                "<body>\n"
                "<div class=\"wrapper\">\n";

static const char *footer = "<footer>\n"
                "<hr>\n"
                "<div>Updated 5 October 2025, Melbourne</div>\n"
                "</footer>\n"
                "</div>\n"
                "</body>\n"
                "</html>\n";

// erase the output directory and its contents
void erase_output_dir(const char *output_path) {
    char cmd[4096];
    snprintf(cmd, sizeof cmd, "rm -rf %s", output_path);
    int r = system(cmd);
    if (r != 0) {
        fprintf(stderr, "Failed to erase output directory %s\n", output_path);  
    }
    mkdir(output_path, 0755);
}

char *create_site_nav_recursive(const f_node *n, char *buffer, size_t bufsize) {
    if (n->kind == N_FILE) {
        char link[512];
        snprintf(link, sizeof link, "<li><a href=\"../%s.html\">%s</a></li>\n", n->path, n->name);
        strncat(buffer, link, bufsize - strlen(buffer) - 1);
    } else if (n->kind == N_DIR && n->children.len > 0) {
        char link[512]; 
        sprintf(link, "<li>%s\n<ul>\n", n->name);
        strncat(buffer, link, bufsize - strlen(buffer) - 1);
        for (size_t j = 0; j < n->children.len; j++) {
            create_site_nav_recursive(n->children.items[j], buffer, bufsize);
        }
        strncat(buffer, "</ul>\n</li>\n", bufsize - strlen(buffer) - 1);
    }
    return buffer;
}

char *create_site_nav(const f_node *site, char *buffer, size_t bufsize) {

    strncat(buffer, "<nav>\n<h2>site map</h2>\n<ul>\n", bufsize - strlen(buffer) - 1);

    for (size_t i = 0; i < site->children.len; i++) {
        create_site_nav_recursive(site->children.items[i], buffer, bufsize);
    }

    strncat(buffer, "</ul>\n</nav>\n", bufsize - strlen(buffer) - 1);

    return buffer;
}

char *create_nav_b(const f_node *site, char *buffer, size_t bufsize) {
    strncat(buffer, "<nav>\n", bufsize - strlen(buffer) - 1);

    for (size_t i = 0; i < site->children.len; i++) {
        if (site->children.items[i]->children.len == 0) continue; // only include directories in the nav
        char section[512];
        sprintf(section, "<ul>\n<li>%s\n</li>\n", site->children.items[i]->name);
        strncat(buffer, section, bufsize - strlen(buffer) - 1);
        // now add children
        for (size_t j = 0; j < site->children.items[i]->children.len; j++) {
            char link[512];
            if (site->children.items[i]->children.items[j]->kind == N_DIR) {
                snprintf(link, sizeof link, "<li><a href=\"../%s/index.html\">%s&mldr;</a></li>\n", site->children.items[i]->children.items[j]->path, site->children.items[i]->children.items[j]->name);
            } else {
                snprintf(link, sizeof link, "<li><a href=\"../%s.html\">%s</a></li>\n", site->children.items[i]->children.items[j]->path, site->children.items[i]->children.items[j]->name);
            }
            strncat(buffer, link, bufsize - strlen(buffer) - 1);
        }

        // now close ul
        char *section_end = "</ul>\n";
        strncat(buffer, section_end, bufsize - strlen(buffer) - 1);
    }

    strncat(buffer, "</nav>\n", bufsize - strlen(buffer) - 1);

    return buffer;
}

void to_html(const char *output_path, const f_node *f, const f_node *site) {
    // if dir, create the folder in output_path, then recursively call to_html on children
    // if file, read the file, translate to html, and write to output_path

    if (f->kind == N_DIR) {
        if (f->children.len == 0) return; // skip empty directories

        // create directory
        char dir_path[4096];
        snprintf(dir_path, sizeof dir_path, "%s/%s", output_path, f->name);
        mkdir(dir_path, 0755);

        // recursively process children
        for (size_t i = 0; i < f->children.len; i++) {
            to_html(dir_path, f->children.items[i], site);
        }
    } else if (f->kind == N_FILE) {
        // read file and translate to html
        FILE *fp = fopen(f->path, "r");
        if (!fp) {
            perror("fopen");
            return;
        }
        char html_path[4096];
        snprintf(html_path, sizeof html_path, "%s/%s.html", output_path, f->name);
        FILE *html_fp = fopen(html_path, "w");
        if (!html_fp) {
            perror("fopen");
            fclose(fp);
            return;
        }

        parse_and_print(html_fp, fp, site);

        fclose(fp);
        fclose(html_fp);
    } else {
        fprintf(stderr, "Unknown node kind\n");
    }
}

typedef enum {
    LIST_UL,
    LIST_OL
} html_list_tag;

typedef struct {
    html_list_tag *items;
    size_t len, cap;
} indent_stack;

int push_indent(indent_stack *s, html_list_tag tag) {
    if (s->len == s->cap) {
        size_t new_cap = s->cap == 0 ? 4 : s->cap * 2;
        html_list_tag *new_items = realloc(s->items, new_cap * sizeof(html_list_tag));
        if (!new_items) return -1;
        s->items = new_items;
        s->cap = new_cap;
    }
    s->items[s->len++] = tag;
    return 0;
}

html_list_tag pop_indent(indent_stack *s) {
    if (s->len == 0) return -1; // stack underflow
    return s->items[--s->len];
}

void close_indents(FILE *html_fp, indent_stack *s, int target_depth) {
    while (s->len > target_depth) {
        html_list_tag tag = pop_indent(s);
        if (tag == LIST_UL) {
            fprintf(html_fp, "</ul>\n");
        } else if (tag == LIST_OL) {
            fprintf(html_fp, "</ol>\n");
        }
    }
}

void handle_heading(char prefix, char *content, FILE *html_fp, indent_stack *indents) {
    close_indents(html_fp, indents, 0);
    fprintf(html_fp, "<h%d>%s</h%d>\n", prefix - '0', content, prefix - '0');
}

void handle_figure(char *content, FILE *html_fp, indent_stack *indents) {
    close_indents(html_fp, indents, 0);
    // split the content into tokens on |

    char *token = strtok(content, "|");
    int token_index = 0;

    while (token) {
        // trim leading and trailing whitespace from token
        size_t token_len = strlen(token);
        size_t start = 0, end = token_len;
        while (start < token_len && (token[start] == ' ' || token[start] == '\t')) {
            start++;
        }
        while (end > start && (token[end - 1] == ' ' || token[end - 1] == '\t')) {
            end--;
        }
        token[end] = '\0';
        token += start;

        // first token is figure caption
        // second is class name to apply
        // third is the filename
        if (token_index == 0) {
            fprintf(html_fp, "<figure class=\"fig full-width\">\n<figcaption>%s</figcaption>\n", token);
        } else if (token_index == 1) {
            // do nothing for now, but we could use this to apply a class to the figure or something
        } else if (token_index == 2) {
            fprintf(html_fp, "<img src=\"../../media/%s\" />\n", token);
        }
        token = strtok(NULL, "|");
        token_index++;
    }
    fprintf(html_fp, "</figure>\n");
}

void handle_blockquote(char *content, FILE *html_fp, indent_stack *indents) {
    close_indents(html_fp, indents, 0);
    fprintf(html_fp, "<blockquote>%s</blockquote>\n", content);
}

void handle_list_and_paragraph(char prefix, char *content, FILE *html_fp, indent_stack *indents) {
    if (prefix == '*' || prefix == '#') {
        // if stack depth is 0, start a new ul/ol    
        if (indents->len == 0) {
            push_indent(indents, prefix == '*' ? LIST_UL : LIST_OL);
            fprintf(html_fp, "%s\n", prefix == '*' ? "<ul>" : "<ol>");
        } else if (indents->len == 1 && indents->items[indents->len - 1] == (prefix == '*' ? LIST_UL : LIST_OL)) {
            // if stack depth is 1 and top of stack is the same list type, add a new li
            // don't need to do anything here.
        } else {
            // otherwise, close indents to 0, then start a new ul/ol and add a new li
            close_indents(html_fp, indents, 0);
            push_indent(indents, prefix == '*' ? LIST_UL : LIST_OL);
            fprintf(html_fp, "%s\n", prefix == '*' ? "<ul>" : "<ol>");
        }
        fprintf(html_fp, "<li>%s</li>\n", content);
    } else {
        // else, not a list just a paragraph
        close_indents(html_fp, indents, 0);
        fprintf(html_fp, "<p>%s</p>\n", content);                    
    }
}

static int replace_marker_pair(char **p,
                               const char *marker,
                               int marker_len,
                               const char *open_tag,
                               const char *close_tag,
                               size_t open_tag_len,
                               size_t close_tag_len) {
    char *start = *p;
    if (strncmp(start, marker, marker_len) != 0) return 0;

    // Ensure there is a closing marker before inserting anything
    char *close = strstr(start + marker_len, marker);
    if (!close) return 0;

    // Replace opening marker with opening tag
    memmove(start + open_tag_len, start + marker_len, strlen(start + marker_len) + 1);
    memcpy(start, open_tag, open_tag_len);

    // Adjust close position after opening tag expansion/shrink
    ptrdiff_t delta_open = (ptrdiff_t)open_tag_len - marker_len;
    close += delta_open;

    // Replace closing marker with closing tag
    memmove(close + close_tag_len, close + marker_len, strlen(close + marker_len) + 1);
    memcpy(close, close_tag, close_tag_len);

    // Advance p to just after the opening tag
    *p = start + open_tag_len;
    return 1;
}

static void apply_inline_formatting(char *content) {
    char *p = content;
    int in_code = 0;

    while (*p) {
        if (replace_marker_pair(&p, "``", 2, "<code>", "</code>", 6, 7)) {
            continue;
        } else if (replace_marker_pair(&p, "**", 2, "<b>", "</b>", 3, 4)) {
            continue;
        } else if (replace_marker_pair(&p, "__", 2, "<i>", "</i>", 3, 4)) {
            continue;
        } else if (replace_marker_pair(&p, "~~", 2, "<s>", "</s>", 3, 4)) {
            continue;
        } else {
            p++;
        }
    }
}

void parse_and_print(FILE *html_fp, FILE *fp, const f_node *site) {
    fprintf(html_fp, "%s", header);

    // nav
    char nav_buffer[8192] = "";
    fprintf(html_fp, "%s", create_nav_b(site, nav_buffer, sizeof(nav_buffer)));

    parse_main_content(fp, html_fp);

    fprintf(html_fp, "%s", footer);
}

void parse_main_content(FILE *fp, FILE *html_fp)
{
    indent_stack indents = {0};

    char buf[4096];
    while (fgets(buf, sizeof buf, fp))
    {
        if (strlen(buf) < 3)
        {
            close_indents(html_fp, &indents, 0);
            continue; // skip blank lines
        }

        // split the line into the first character and the rest of the line
        char prefix = buf[0];
        char *content = buf + 2;

        // trim trailing newlines and whitespace
        size_t len = strlen(content);
        while (len > 0 && (content[len - 1] == '\n' ||
                           content[len - 1] == '\r' ||
                           content[len - 1] == ' ' ||
                           content[len - 1] == '\t'))
        {
            content[--len] = '\0';
        }

        apply_inline_formatting(content);

        switch (prefix)
        {
        case ':':
            continue; // skip comment lines
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
            handle_heading(prefix, content, html_fp, &indents);
            break;
        case '%':
            handle_figure(content, html_fp, &indents);
            break;
        case '>':
            handle_blockquote(content, html_fp, &indents);
            break;
        case '*':
        case '#':
        case ' ':
            handle_list_and_paragraph(prefix, content, html_fp, &indents);
            break;
        case '&':
        {
            // space
            // scan ahead and count leading spaces before a * or #
            size_t space_count = 0;
            while (content[space_count] == ' ')
            {
                space_count++;
            }
            // if the count is non-zero and even, then divided by two gives us the current indent level
            // the next character is the list type

            char list_type = content[space_count];
            // printf("%c", list_type);

            if (list_type == '*' || list_type == '#')
            {
                printf("List item with indent level %zu (space count %zu) and type %c\n", (space_count + 2) / 2 + 1, space_count, list_type);
                // if there are leading spaces before a list item, we need to indent
                // the list item by pushing to the indent stack and printing the appropriate tag

                //  difference between the current indent level and the stack depth gives us how many levels we need to push/pop
                int indent_level = (space_count + 2) / 2 + 1;
                int diff = indent_level - indents.len;

                if (diff > 0)
                {
                    // we need to push diff levels of indentation
                    for (int i = 0; i < diff; i++)
                    {
                        push_indent(&indents, list_type == '*' ? LIST_UL : LIST_OL);
                        fprintf(html_fp, "%s\n", list_type == '*' ? "<ul>" : "<ol>");
                    }
                }
                else if (diff == 0)
                {
                    if (indents.items[indents.len - 1] == LIST_UL && list_type != '*' ||
                        indents.items[indents.len - 1] == LIST_OL && list_type != '#')
                    {
                        // if the indent level is the same but the list type is different, we need to pop the current indent and push the new one
                        close_indents(html_fp, &indents, indents.len - 1);
                        push_indent(&indents, list_type == '*' ? LIST_UL : LIST_OL);
                        fprintf(html_fp, "%s\n", list_type == '*' ? "<ul>" : "<ol>");
                    }
                }
                else if (diff < 0)
                {
                    // we need to pop -diff levels of indentation
                    close_indents(html_fp, &indents, indent_level);
                }

                fprintf(html_fp, "<li>%s</li>\n", content + space_count + 2);
                continue; // skip the rest of the switch statement
            }
            else
            {
                // else, not a list just a paragraph
                close_indents(html_fp, &indents, 0);
                fprintf(html_fp, "<p>%s</p>\n", content);
            }

            break;
        }
        case '$':
            // asterisk
            // if stack depth is 0, start a new ul
            if (indents.len == 0)
            {
                push_indent(&indents, LIST_UL);
                fprintf(html_fp, "<ul>\n");
            }
            else if (indents.len == 1 && indents.items[indents.len - 1] == LIST_UL)
            {
                // if stack depth is 1 and top of stack is ul, add a new li
                // don't need to do anything here.
            }
            else
            {
                // otherwise, close indents to 0, then start a new ul and add a new li
                close_indents(html_fp, &indents, 0);
                push_indent(&indents, LIST_UL);
                fprintf(html_fp, "<ul>\n");
            }
            fprintf(html_fp, "<li>%s</li>\n", content);
            break;
        case '@':
            // hash
            // if stack depth is 0, start a new ul
            if (indents.len == 0)
            {
                push_indent(&indents, LIST_OL);
                fprintf(html_fp, "<ol>\n");
            }
            else if (indents.len == 1 && indents.items[indents.len - 1] == LIST_OL)
            {
                // if stack depth is 1 and top of stack is ul, add a new li
                // don't need to do anything here.
            }
            else
            {
                // otherwise, close indents to 0, then start a new ul and add a new li
                close_indents(html_fp, &indents, 0);
                push_indent(&indents, LIST_OL);
                fprintf(html_fp, "<ol>\n");
            }
            fprintf(html_fp, "<li>%s</li>\n", content);
            break;
        default:
            // unknown prefix
            close_indents(html_fp, &indents, 0);
            fprintf(html_fp, "<pre style=\"background-color: yellow;\">%s</pre>\n", buf);
            break;
        }
    }

    close_indents(html_fp, &indents, 0);
}
