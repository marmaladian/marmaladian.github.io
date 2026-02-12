# a python version of fold to test out some ideas

DATA_DIR = "data/"
OUTPUT_DIR = "docs/"

SHOW_COMMENTS = False

import os
import fnmatch

def node(name, children=(), pages=(), **attrs):
    return {"name": name, "children": list(children), "pages": list(pages), "attrs": dict(attrs)}

def add_child(parent, child):
    parent["children"].append(child)
    return child

def walk(n):
    yield n
    for c in n["children"]:
        yield from walk(c)

def pretty(n, indent=""):
    print(f"{indent}{n['name']}")
    for c in n["children"]:
        pretty(c, indent + "  ")
    for p in n["pages"]:
        print(f"{indent}  {p}")

def build_site_tree():
    index = node("index")

    # root is curdir
    # dir is list of directories in curdir
    # files is list of files in curdir

    for root, dir, files in os.walk(DATA_DIR):
        # if no .f files in files, skip
        if not any(fnmatch.fnmatch(file, "*.f") for file in files):
            continue

        parts = root.split(os.sep)
        current_node = index
        for part in parts[1:]:  # skip the first part which is "data"
            # find the child node with the name of part
            child = next((c for c in current_node["children"] if c["name"] == part), None)
            if child is None:
                child = node(part)
                # store the full path for the node (without the data/ prefix)
                child["attrs"]["path"] = os.path.join(*parts[1:])
                add_child(current_node, child)
            current_node = child

        for file in files:
            if fnmatch.fnmatch(file, "*.f"):
                current_node["pages"].append(file)
    return index  

def html_header(title, rel_root=""):
    return f"""
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="{rel_root}css/default.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Baskervville:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap" rel="stylesheet">
        <title>{title} &mdash; Benjamin Grayland</title>
    </head>
    <body>
        <div class="wrapper">
    """
def html_footer():
    return """
            <footer>
                <hr>
                <div>Updated 5 October 2025, Melbourne</div>
            </footer>
        </div>
    </body>
</html>
    """

def rel_root_for(output_path):
    rel_dir = os.path.relpath(os.path.dirname(output_path), OUTPUT_DIR)
    if rel_dir == ".":
        return ""
    depth = len(rel_dir.split(os.sep))
    return "../" * depth

def apply_inline_formatting(text, site=None, rel_root=""):
    # apply inline formatting for **bold** (or __bold__) and *italic* (or _italic_)
    # `code`, ~~strikethough~~, and {{link text|url}}
    # note that urls not starting with https are links to a page in the site, so {{About|about}} would link to about.html.
    # need to search the site tree for the page with the name of the url, and link to it if it exists, otherwise report an error.
    import re
    # handle links first since they can contain other formatting
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        if url.startswith("http") or url.startswith("https"):
            return f'<a href="{url}">{link_text}</a>'
        else:
            # search the site tree for the page with the name of the url
            if site:
                for n in walk(site):
                    # check if url matches a node name
                    if n["name"] == url:
                        return f'<a href="{rel_root}{n["attrs"]["path"]}/index.html">{link_text}</a>'
                    # check if url matches a page in this node
                    for page in n["pages"]:
                        page_name = os.path.splitext(page)[0]
                        if page_name == url:
                            return f'<a href="{rel_root}{n["attrs"]["path"]}/{page_name}.html">{link_text}</a>'
                print(f"Error: could not find page with name {url} for link {link_text}")
            return link_text  # return the text without a link
    
    # the urls are encoded like {{link text|url}} or {{link text | url}} with spaces around the |, so we need to handle that in the regex
    text = re.sub(r"\{\{\s*(\S(?:.*\S)?)\s*\|\s*(\S(?:.*\S)?)\s*\}\}", replace_link, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"_([^_]+)_", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)
    return text

def create_page(src_file, path, rel_root="", site=None):
    if site is None:
        raise ValueError("create_page requires a site tree for inline links")


    # read the .f file and convert it to html
    with open(src_file, "r") as f:
        content = f.read()

    # parse line by line: the first character is a prefix indicating the type of line. the rest [2:] is the actual content
    
    html_content = ""
    list_stack = []

    for line in content.splitlines():
        if len(line) < 3:
            continue
        prefix, rest = line[0], line[2:]
        rest = apply_inline_formatting(rest, site, rel_root)

        if prefix in ["1", "2", "3", "4", "5", "6"]:
            html_content, list_stack = clear_list_stack(html_content, list_stack, 0)
            html_content += f"<h{prefix}>{rest}</h{prefix}>"

        elif prefix == "%":
            # % Doenjang jjigae | full | journal/2026-W03.jpg
            #   figure caption | class | image path
            parts = rest.split("|")
            caption = parts[0].strip() if len(parts) > 0 else ""
            cls = parts[1].strip() if len(parts) > 1 else ""
            img_path = parts[2].strip() if len(parts) > 2 else ""
            html_content += f"<figure class='{cls}'><img src='{rel_root}media/{img_path}' alt='{caption}'><figcaption>{caption}</figcaption></figure>"

        elif prefix in ["*", "#", " "]:
            # check first non-space character in content
            html_content = handle_list_or_para(html_content, list_stack, line, site, rel_root)

        elif prefix == "/":
            if (SHOW_COMMENTS):
                html_content += f"<span class='comment'>{rest}</span>"
        
        else:
            html_content, list_stack = clear_list_stack(html_content, list_stack, 0)
            html_content += f"<pre><b>UNKNOWN: </b>{line}</pre>"

    html_content, list_stack = clear_list_stack(html_content, list_stack, 0)
    
    with open(path, "w") as f:
        f.write(html_header(os.path.splitext(os.path.basename(src_file))[0].capitalize(), rel_root))
        f.write(html_content)
        f.write(html_footer())

def handle_list_or_para(html_content, list_stack, line, site=None, rel_root=""):
    list_type, num_leading_spaces = next(((c, i) for i, c in enumerate(line) if c != " "), (None, 0))
    list_level = (num_leading_spaces // 2) + 1 if list_type in ["*", "#"] else 0

    diff = list_level - len(list_stack)

    if list_type not in ["*", "#"]:
        # either we're not in a list, or we need to close it off
        rest = line[num_leading_spaces:]
        rest = apply_inline_formatting(rest, site, rel_root)
        html_content, list_stack = clear_list_stack(html_content, list_stack, 0)
        html_content += f"<p>{rest}</p>"
    else:
        # we're already in a list, are we continuing, changing the depth, or changing the type
        rest = line[num_leading_spaces + 2:]
        rest = apply_inline_formatting(rest, site, rel_root)
        if diff > 0:
            # we need to open a new list
            html_content += f"<{ 'ul' if list_type == '*' else 'ol' }>"
            list_stack.append(list_type)
        elif diff < 0:
            # we need to close the current list
            html_content, list_stack = clear_list_stack(html_content, list_stack, list_level)
        elif list_stack and list_stack[-1] != list_type:
            # we need to close the current list and open a new one
            html_content, list_stack = clear_list_stack(html_content, list_stack, list_level - 1)
            html_content += f"<{ 'ul' if list_type == '*' else 'ol' }>"
            list_stack.append(list_type)
        html_content += f"<li>{rest}</li>"
    return html_content

def clear_list_stack(html_content, list_stack, target_depth):
    while len(list_stack) > target_depth:
        html_content += f"</{ 'ul' if list_stack[-1] == '*' else 'ol' }>"
        list_stack.pop()
    return html_content, list_stack

def main():
    site = build_site_tree()
    pretty(site) 

    # produce global nav

    # clear output dir
    if os.path.exists(OUTPUT_DIR):
        for root, dir, files in os.walk(OUTPUT_DIR, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for d in dir:
                os.rmdir(os.path.join(root, d))
    else:
        os.mkdir(OUTPUT_DIR)

    COPY_DIRS = ["css", "media"]
    # copy these directories recursvieyl to output dir
    for copy_dir in COPY_DIRS:
        src_dir = os.path.join(DATA_DIR, copy_dir)
        dst_dir = os.path.join(OUTPUT_DIR, copy_dir)
        if os.path.exists(src_dir):
            os.makedirs(dst_dir, exist_ok=True)
            for root, dir, files in os.walk(src_dir):
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dst_dir, os.path.relpath(src_file, src_dir))
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    with open(src_file, "rb") as f_src:
                        with open(dst_file, "wb") as f_dst:
                            f_dst.write(f_src.read())


    # create index.html
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w") as f:
        f.write(html_header("Home", rel_root_for(index_path)))
        f.write("<h1>Home</h1>")
        f.write("<ul>")
        for child in site["children"]:
            f.write(f'<li><a href="{child["name"]}/index.html">{child["name"].capitalize()}</a></li>')
        f.write("</ul>")
        f.write(html_footer())

    # for each node in site, create a directory, and for each page then call create_page() to produce a html file
    for n in walk(site):
        if n["name"] != "index":  # skip the root node
            # use the path attribute to create the directory structure in the output dir
            dir_path = os.path.join(OUTPUT_DIR, n["attrs"]["path"])
            os.makedirs(dir_path, exist_ok=True)
            index_path = os.path.join(dir_path, "index.html")
            with open(index_path, "w") as f:
                f.write(html_header(n["name"].capitalize(), rel_root_for(index_path)))
                f.write(f"<h1>{n['name'].capitalize()}</h1>")
                if n["children"]:
                    f.write("<h2>Subsections</h2>")
                    f.write("<ul>")
                    for child in n["children"]:
                        f.write(f'<li><a href="{child["name"]}/index.html">{child["name"].capitalize()}</a></li>')
                    f.write("</ul>")
                if n["pages"]:
                    f.write("<h2>Pages</h2>")
                    f.write("<ul>")
                    for page in n["pages"]:
                        page_name = os.path.splitext(page)[0]
                        f.write(f'<li><a href="{page_name}.html">{page_name.capitalize()}</a></li>')
                    f.write("</ul>")
                f.write(html_footer())

            for page in n["pages"]:
                src_file = os.path.join(DATA_DIR, n["attrs"]["path"], page)
                output_file = os.path.join(dir_path, os.path.splitext(page)[0] + ".html")
                create_page(src_file, output_file, rel_root_for(output_file), site)

if __name__ == "__main__":
    main()