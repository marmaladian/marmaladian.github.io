: title: Site to-do list

* build proper navigation
* create a photo journal
* formatting
  * ~~italics~~
  * ~~bold~~
  * ~~strikeout~~
  * ~~``inline code`` (``)~~
  * ~~prevent these from running** past __the** end__ of a line~~
  * ~~prevent an __**opening**__ without a closing from doing anything~~
* code block
* block quotes
  * allow multiple paragraphs in a single blockquote
* clean up the ludopax page and add emoji
* fix site structure
* navigation
  * hide directories with no .f files (don't create nodes for these)
  * don't create directory nodes if none of their descendant directories have files in them

* add a front-matter option to create toc from the headers.
* still need to figure out something better for blank directory pages. maybe just select the first child page automatically?

> Avoid system("rm -rf ..."): use nftw/fts or unlinkat for safe, predictable deletion. Eliminate unchecked strncat/sprintf risks: track remaining buffer space and use snprintf.
> Centralize HTML escaping for content and n->name to prevent invalid output.
> Factor parsing into small handlers (handle_heading, handle_list, handle_fig) to reduce the large switch.
> Unify list logic: the ' ' case and '*'/'#' cases overlap; consolidate into one list handler.
> Use const char * for string literals (header, footer) and make them static const.
> Check indent_stack_push failures and handle allocation errors.
> Remove debug printf or gate it behind a verbose flag.
> Use size_t consistently (avoid signed/unsigned mixing in diff).