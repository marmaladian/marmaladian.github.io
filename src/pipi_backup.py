import os

data_dir = 'data'
output_dir = 'site'

def get_files_recursive(path, filetype):
    file_list = []
    for f in os.listdir(path):
        full_path = os.path.join(path, f)
        if os.path.isdir(full_path):
            file_list.extend(get_files_recursive(full_path, filetype))
        elif f.endswith(filetype):
            file_list.append(full_path)
    return file_list

def index_header(page_title):
    return f'<!DOCTYPE html>\n<html lang="en" dir="ltr">\n<head>\n\t<meta charset="UTF-8">\n\t<link rel="stylesheet" href="css/style.css" />\n\t<title>Park Imminent</title>\n</head>\n<body>\n'

def html_header(page_title):
    return f'<!DOCTYPE html>\n<html lang="en" dir="ltr">\n<head>\n\t<meta charset="UTF-8">\n\t<link rel="stylesheet" href="css/style.css" />\n\t<title>{page_title} &mdash; Park Imminent</title>\n</head>\n<body>\n<div class="running-head"><a href="index.html">Park Imminent</a></div>\n'

def html_footer():
    return '\n<div class="running-footer">Next, prev</div>\n</body>\n</html>'

def html_unhandled(line):
    return f'<p><strike>UNHANDLED: {line}</strike></p>\n'

def html_h1(line):
    return f'<h1>{line}</h1>\n'

def html_h2(line):
    return f'<h2>{line}</h2>\n'

def html_h3(line):
    return f'<h3>{line}</h3>\n'

def html_h4(line):
    return f'<h4>{line}</h4>\n'

def html_open_p(line):
    return f'<p>{line}'

def html_close_p():
    return '</p>\n'

def html_open_ul(line):
    return f'<ul>\n\t{html_li(line)}'

def html_open_ol(line):
    return f'<ol>\n\t{html_li(line)}'

def html_li(line):
    return f'\t<li>{line}</li>\n'

def html_close_ul():
    return f'</ul>\n'

def html_close_ol():
    return f'</ol>\n'

def html_img(line):
    print('\tFinding image:', line)
    img_caption = line.split(',', 1)
    img = img_caption[0]
    if len(img_caption) > 1:
        caption = img_caption[1].strip()
        return f'<figure><img src="media/{img}"><figcaption>{caption}</figcaption></figure>'
    else:
        return f'<figure><img src="media/{img}"></figure>'

def html_join(line):
    return f' {line}'

def has_link(line):
    return '[[' in line

def has_italics(line):
    return '__' in line

def has_bold(line):
    return '**' in line

def format_line(line):
    while has_link(line):
        link_start = line.find('[[')
        link_end = line.find(']]')
        if link_end == -1:
            print('INVALID LINK FORMAT:', line)
            return line
        link_mid = line.find('][')

        if link_mid == -1:
            url = line[link_start + 2: link_end]
            line = line[:link_start] + '<a href="' + url + '">' + url + '</a>' + line[link_end + 2:]
        else:
            url = line[link_start + 2: link_mid]
            label = line[link_mid + 2: link_end]
            line = line[:link_start] + '<a href="' + url + '">' + label + '</a>' + line[link_end + 2:]

    while has_italics(line):
        start = line.find('__')
        end = line.find('__', start + 2)
        text = line[start + 2: end]
        line = line[:start] + '<i>' + text + '</i>' + line[end + 2:]

    while has_bold(line):
        start = line.find('**')
        end = line.find('**', start + 2)
        text = line[start + 2: end]
        line = line[:start] + '<b>' + text + '</b>' + line[end + 2:]

    return line

def ends_mode(line):
    if len(line) < 3 or line[:-1].isspace():
        # print('short/space', line)
        return True
    elif para_mode and line[0] != ' ':
        # print('para interrupt', line)
        return True
    elif list_stack and line[0] != '-':
        return True
    
def parse_line(line):
    global para_mode
    global list_stack

    html_string = ''

    # if the line is all blank, or too short
    # then close off paragraphs, lists.
    if ends_mode(line):
        if para_mode:
            html_string += html_close_p()
            para_mode = False
        while list_stack:
            list_close_fn = list_stack.pop()
            html_string += list_close_fn()
    
    # if it's just a rune with no content, skip it
    if len(line) < 3:
        return html_string

    rune = line[0]
    line = line[2:]

    # parse all the links, italics in the line
    # line = format_line(line)

    if rune == '-' or rune == '*':
        if not list_stack:
            list_stack.append(html_close_ul)
            html_string += html_open_ul(line)
        else:
            html_string += html_li(line)
    elif rune == '1':
        html_string += html_h1(line)
    elif rune == '2':
        html_string += html_h2(line)
    elif rune == '3':
        html_string += html_h3(line)
    elif rune == '4':
        html_string += html_h4(line)
    elif rune == '+':
        html_string += html_img(line)
    elif rune == ' ':
            if para_mode:
                html_string += html_join(line) # TODO joining lines
            else:
                para_mode = True
                html_string += html_open_p(line)
    else:
        html_string += html_unhandled(line)
    
    return html_string

def parse(file):
    print('Parsing:', file)
    global para_mode, list_stack
    para_mode = False
    list_stack = []

    html = ''
    title = ''
    with open(file, 'rt') as f:
        first_line = f.readline()
        title = first_line[2:-1]
        html += html_h1(title)
        for line in f:
            line = format_line(line)
            html += parse_line(line[:-1])
    return html, title


## MAIN

for out in get_files_recursive(output_dir, '.html'):
    os.remove(out)

pages = []

for src in get_files_recursive(data_dir, '.pi'):
    name = os.path.basename(src)
    name = os.path.splitext(name)[0]
    title = 'MISSING TITLE'
    with open(f'{output_dir}/{name}.html', 'wt') as out:
        print(html_header(name), file=out)
        body, title = parse(src)
        print(body, file=out)
        print(html_footer(), file=out)
    pages.append((name, title))

with open(f'{output_dir}/index.html', 'wt') as index:
    print(index_header('Park Imminent'), file=index)
    print(html_h1('Park Imminent'), file=index)
    print('<ul class="nobullets">', file=index)
    for page in pages:
        print(f'<li><a href="{page[0]}.html">{page[1]}</a></li>', file=index)
    print('</ul>', file=index)
    print(html_footer(), file=index)