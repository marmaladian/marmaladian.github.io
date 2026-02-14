#pragma once

#include "f_node.h"

void erase_output_dir(const char *output_path);
void to_html(const char *output_path, const f_node *f, const f_node *site);

void parse_and_print(FILE *html_fp, FILE *fp, const f_node *site);

void parse_main_content(FILE *fp, FILE *html_fp);
