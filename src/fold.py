# a python version of fold to test out some ideas

DATA_DIR = "data/"
OUTPUT_DIR = "docs/"

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
                add_child(current_node, child)
            current_node = child

        for file in files:
            if fnmatch.fnmatch(file, "*.f"):
                current_node["pages"].append(file)
    return index  



def html_header(title):
    return f"""
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="../../css/default.css">
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

    # create index.html
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
        f.write(html_header("Home"))
        f.write("<h1>Home</h1>")
        f.write("<ul>")
        for child in site["children"]:
            f.write(f'<li><a href="{child["name"]}/index.html">{child["name"].capitalize()}</a></li>')
        f.write("</ul>")
        f.write(html_footer())        

if __name__ == "__main__":
    main()