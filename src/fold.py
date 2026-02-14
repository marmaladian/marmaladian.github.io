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
        page_file = p["file"] if isinstance(p, dict) else p
        print(f"{indent}  {page_file}")

def get_page_metadata(filepath):
    """Extract title and style from a .f file's front-matter."""
    metadata = {"title": None, "style": "default.css"}
    try:
        with open(filepath, "r") as f:
            for line in f:
                if line.startswith(": "):
                    parts = line[2:].split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key == "title":
                            metadata["title"] = value
                        elif key == "style":
                            metadata["style"] = value if value.endswith(".css") else value + ".css"
                elif not line.startswith(": "):
                    # stop at first non-frontmatter line
                    break
    except:
        pass
    return metadata

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
                filepath = os.path.join(root, file)
                metadata = get_page_metadata(filepath)
                # Store page as dict with filename and metadata
                page_entry = {"file": file, "metadata": metadata}
                current_node["pages"].append(page_entry)
    return index  

def html_header(title, rel_root="", css_file="default.css", site=None):
    nav_html = ""
    # if site:
    #     nav_html = build_full_nav(site, rel_root)
    return f"""
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="{rel_root}css/{css_file}">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Baskervville:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap" rel="stylesheet">
        <title>{title} &mdash; Benjamin Grayland</title>
    </head>
    <body>
    """

def layout_open(rel_root="", nav_html=""):
    return f"""
        <div class=\"layout\">
            <div class=\"kicker\"><img src=\"{rel_root}media/eico.gif\">{nav_html}</div>
    """
def html_footer():
    return """
            <footer class="text">
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

def apply_inline_formatting(text, site=None, rel_root="", errors=None):
    # apply inline formatting for **bold** (or __bold__) and *italic* (or _italic_)
    # `code`, ~~strikethough~~, and {{link text|url}}
    # note that urls not starting with https are links to a page in the site, so {{About|about}} would link to about.html.
    # need to search the site tree for the page with the name of the url, and link to it if it exists, otherwise report an error.
    import re
    if errors is None:
        errors = []
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
                    for page_entry in n["pages"]:
                        page_file = page_entry["file"] if isinstance(page_entry, dict) else page_entry
                        page_name = os.path.splitext(page_file)[0]
                        if page_name == url:
                            return f'<a href="{rel_root}{n["attrs"]["path"]}/{page_name}.html">{link_text}</a>'
                errors.append(f"Could not find page '{url}' for link text '{link_text}'")
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

def parse_frontmatter(content_lines):
    """Extract front-matter from the beginning of a file.
    
    Front-matter lines start with ': ' and contain 'key: value' pairs.
    Returns (frontmatter_dict, remaining_lines)
    """
    frontmatter = {}
    remaining_lines = []
    parsing_frontmatter = True
    
    for line in content_lines:
        if parsing_frontmatter and line.startswith(": "):
            # Parse front-matter line: ": key: value"
            parts = line[2:].split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                frontmatter[key] = value
        else:
            parsing_frontmatter = False
            remaining_lines.append(line)
    
    return frontmatter, remaining_lines

def create_page(src_file, path, rel_root="", site=None):
    if site is None:
        raise ValueError("create_page requires a site tree for inline links")

    # read the .f file and convert it to html
    with open(src_file, "r") as f:
        content_lines = f.read().splitlines()

    # extract front-matter
    frontmatter, content_lines = parse_frontmatter(content_lines)
    
    # get title and style from front-matter, with fallbacks
    page_title = frontmatter.get("title", os.path.splitext(os.path.basename(src_file))[0].capitalize())
    css_file = frontmatter.get("style", "default.css")
    if not css_file.endswith(".css"):
        css_file += ".css"

    # parse line by line: the first character is a prefix indicating the type of line. the rest [2:] is the actual content
    
    html_content = f"<div class='page-header'><h1 class='page-title'>{page_title}</h1></div>"
    list_stack = []
    blockquote_open = False
    div_stack = []
    text_div_open = False
    errors = []
    nav_html = ""

    html_content += layout_open(rel_root, nav_html)

    for line in content_lines:
        if len(line) < 3 and not line.startswith("|"):
            continue
        if line.startswith("|"):
            # close text div if open before processing explicit div
            if text_div_open:
                html_content += "</div>"
                text_div_open = False
            class_name = line[1:].strip()
            if class_name:
                div_stack.append(class_name)
                html_content += f"<div class='{class_name}'>"
            else:
                if div_stack:
                    div_stack.pop()
                    html_content += "</div>"
                else:
                    errors.append(f"Unmatched div close in line: {line}")
            continue
        prefix, rest = line[0], line[2:]
        rest = apply_inline_formatting(rest, site, rel_root, errors)

        if prefix in ["1", "2", "3", "4", "5", "6"]:
            if prefix == "1" and rest.strip().lower() == page_title.strip().lower():
                continue
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
            html_content += f"<h{prefix}>{rest}</h{prefix}>"

        elif prefix == "%":
            # % Doenjang jjigae | full | journal/2026-W03.jpg
            #   figure caption | class | image path
            if text_div_open:
                html_content += "</div>"
                text_div_open = False
            html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
            parts = rest.split("|")
            caption = parts[0].strip() if len(parts) > 0 else ""
            cls = parts[1].strip() if len(parts) > 1 else ""
            img_path = parts[2].strip() if len(parts) > 2 else ""
            # figures get "side" class if no class specified, otherwise use specified class
            if not cls:
                cls = "side"
            html_content += f"<figure class='{cls}'><img src='{rel_root}media/{img_path}' alt='{caption}'><figcaption>{caption}</figcaption></figure>"

        elif prefix == ">":
            # blockquote
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            if not blockquote_open:
                html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
                html_content += "<blockquote>"
                blockquote_open = True
            html_content += f"<p>{rest}</p>"

        elif prefix in ["*", "#", " "]:
            # check first non-space character in content
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            if blockquote_open:
                html_content += "</blockquote>"
                blockquote_open = False
            html_content = handle_list_or_para(html_content, list_stack, line, site, rel_root, errors)

        elif prefix == "/":
            if (SHOW_COMMENTS):
                html_content += f"<span class='comment'>{rest}</span>"
        
        else:
            html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            errors.append(f"Unknown prefix '{prefix}' in line: {line}")
            html_content += f"<pre><b>UNKNOWN: </b>{line}</pre>"

    html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
    if text_div_open:
        html_content += "</div>"
        text_div_open = False
    if div_stack:
        errors.append(f"Unclosed div(s): {', '.join(div_stack)}")
        while div_stack:
            div_stack.pop()
            html_content += "</div>"
    
    with open(path, "w") as f:
        f.write(html_header(page_title, rel_root, css_file, site))
        f.write(html_content)
        f.write(html_footer())
    
    return errors

def handle_list_or_para(html_content, list_stack, line, site=None, rel_root="", errors=None):
    if errors is None:
        errors = []
    list_type, num_leading_spaces = next(((c, i) for i, c in enumerate(line) if c != " "), (None, 0))
    list_level = (num_leading_spaces // 2) + 1 if list_type in ["*", "#"] else 0

    diff = list_level - len(list_stack)

    if list_type not in ["*", "#"]:
        # either we're not in a list, or we need to close it off
        rest = line[num_leading_spaces:]
        rest = apply_inline_formatting(rest, site, rel_root, errors)
        html_content, list_stack = clear_list_stack(html_content, list_stack, 0)
        html_content += f"<p>{rest}</p>"
    else:
        # we're already in a list, are we continuing, changing the depth, or changing the type
        rest = line[num_leading_spaces + 2:]
        rest = apply_inline_formatting(rest, site, rel_root, errors)
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

def close_open_blocks(html_content, list_stack, blockquote_open):
    """Close any open list and blockquote blocks."""
    html_content, list_stack = clear_list_stack(html_content, list_stack, 0)
    if blockquote_open:
        html_content += "</blockquote>"
        blockquote_open = False
    return html_content, list_stack, blockquote_open

# Build a nav menu for the index.html page.
# It will list all the child nodes of the root as paras in a div, and for each of these
# nodes it will list the pages in a ul. Where a node has child nodes (i.e. directories), those should at the start of the ul as 'name...' linking to the index.html for that directory
def build_full_nav(site, rel_root="") -> str:
    nav_html = "<nav>" if site else ""
    if not site:
        return nav_html
    for child in site["children"]:
        nav_html += f"<div><h2><a href='{rel_root}{child['attrs']['path']}/index.html'>{child['name'].capitalize()}</a></h2>"
        if child["pages"] or child["children"]:
            nav_html += "<ul>"
            if child["children"]:
                for subchild in child["children"]:
                    nav_html += f"<li><a href='{rel_root}{subchild['attrs']['path']}/index.html'>{subchild['name'].capitalize()}...</a></li>"
            for page_entry in child["pages"]:
                page_file = page_entry["file"]
                page_name = os.path.splitext(page_file)[0]
                page_title = page_entry["metadata"].get("title") or page_name.capitalize()
                nav_html += f"<li><a href='{rel_root}{child['attrs']['path']}/{page_name}.html'>{page_title}</a></li>"
            nav_html += "</ul>"
        nav_html += "</div>"
    nav_html += "</nav>"
    return nav_html


def main():
    site = build_site_tree()
    pretty(site) 

    # track all errors
    all_errors = {} 

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
        f.write(html_header("Home", rel_root_for(index_path), "default.css", site))
        f.write("<div class='page-header'><h1 class='page-title'>Home</h1></div>")
        f.write(layout_open(rel_root_for(index_path)))
        f.write("<div class='text'>")
        f.write("<ul>")
        for child in site["children"]:
            f.write(f'<li><a href="{child["name"]}/index.html">{child["name"].capitalize()}</a></li>')
        f.write("</ul>")
        f.write("</div>")
        f.write(html_footer())

    # for each node in site, create a directory, and for each page then call create_page() to produce a html file
    for n in walk(site):
        if n["name"] != "index":  # skip the root node
            # use the path attribute to create the directory structure in the output dir
            dir_path = os.path.join(OUTPUT_DIR, n["attrs"]["path"])
            os.makedirs(dir_path, exist_ok=True)
            index_path = os.path.join(dir_path, "index.html")
            with open(index_path, "w") as f:
                f.write(html_header(n["name"].capitalize(), rel_root_for(index_path), "default.css", site))
                f.write(f"<div class='page-header'><h1 class='page-title'>{n['name'].capitalize()}</h1></div>")
                f.write(layout_open(rel_root_for(index_path)))
                f.write("<div class='text'>")
                if n["children"]:
                    f.write("<h2>Subsections</h2>")
                    f.write("<ul>")
                    for child in n["children"]:
                        f.write(f'<li><a href="{child["name"]}/index.html">{child["name"].capitalize()}</a></li>')
                    f.write("</ul>")
                if n["pages"]:
                    f.write("<h2>Pages</h2>")
                    f.write("<ul>")
                    for page_entry in n["pages"]:
                        page_file = page_entry["file"]
                        page_name = os.path.splitext(page_file)[0]
                        page_title = page_entry["metadata"].get("title") or page_name.capitalize()
                        f.write(f'<li><a href="{page_name}.html">{page_title}</a></li>')
                    f.write("</ul>")
                f.write("</div>")
                f.write(html_footer())

            for page_entry in n["pages"]:
                page_file = page_entry["file"]
                src_file = os.path.join(DATA_DIR, n["attrs"]["path"], page_file)
                output_file = os.path.join(dir_path, os.path.splitext(page_file)[0] + ".html")
                errors = create_page(src_file, output_file, rel_root_for(output_file), site)
                if errors:
                    pretty_path = os.path.join(n["attrs"]["path"], page_file)
                    all_errors[pretty_path] = errors
    
    # print error log
    if all_errors:
        print("\n" + "="*60)
        print("ERRORS FOUND DURING PAGE GENERATION")
        print("="*60)
        for page_path, errors in all_errors.items():
            print(f"\n[{page_path}]")
            for error in errors:
                print(f"  - {error}")
    else:
        print("✓ All pages generated successfully with no errors")

if __name__ == "__main__":
    main()