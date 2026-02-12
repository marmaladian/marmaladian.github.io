#pragma once

#include "f_node.h"

f_node *build_tree(const char *root_path);
void print_tree(const f_node *n, int depth);