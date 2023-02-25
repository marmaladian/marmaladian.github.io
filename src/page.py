import os

class Page:

    def __init__(self, src_file) -> None:
        self._src_file = src_file
        self._title = "Untitled page"
        file_and_ext = os.path.basename(src_file)
        self._filename = os.path.splitext(file_and_ext)[0]
        self._category = os.path.basename(os.path.dirname(src_file))
        self._references = [] # a list of images or other pages referenced.
        self._html = ""
        self.read_file()
        # self.join_lines()
        print(f"PAGE: {self._title} for file [{self._filename}]")
        self.parse_lines()
        # TODO self.check_references()

    def filename(self):
        return self._filename
    
    def title(self):
        return self._title

    def category(self):
        return self._category

    def html(self):
        return f"""
            {self.html_header()}
                <article>
                    <h1>{self.title()}</h1>
                    <section>
                        {self.html_body()}
                    </section>
                </article>
            {self.html_footer()}
            """
## INTERNAL ####################################################################

## html ------------------------------------------------------------------------

    def html_header(self):
        return f"""
            <!DOCTYPE html>
            <html lang="en" dir="ltr">
            <head>
                <meta charset="UTF-8">
                <link rel="stylesheet" href="/css/style.css" />
                <title>{self.title()} &mdash; Park Imminent</title>
            </head>
            <body>
            """

    def html_footer(self):
        return """
            </body>
            </html>
            """

    def html_body(self):
        return self._html

## file ------------------------------------------------------------------------

    def read_file(self):
        with open(self._src_file, 'rt') as f:
            self._lines = f.readlines()
            self._title = self._lines[0][2:-1]
            self._lines.pop(0)
        # for line in self._lines:
        #     print(len(line), '\t', line)

    def parse_lines(self):
        mode = None
        for line in self._lines:
            html, mode = self.parse_line(line, mode)
            self._html += html

    def parse_line(self, line, mode):
        line = format_line(line)
        html_string = ''
        
        if len(line) < 3:
            if mode == '.':
                mode = None
            elif mode in ['*', '-']:
                html_string += '</ul>\n'
                mode = None
            elif mode == '#':
                html_string += '</ol>\n'
                mode = None
            return html_string, mode

        rune = line[0]
        line = line[2:]

        if mode == '-' and rune not in ['-', '*']:
            html_string += '</ul>\n'
            mode = None
        if mode == '#' and rune != '#':
            html_string += '</ol>\n'
            mode = None
        if mode == '.' and rune != '.':
            html_string += '</p>\n'
            mode = None

        if mode is None:
            if rune in ['-', '*']:
                html_string += '<ul>'
                mode = '-'
            elif rune == '#':
                html_string += '<ol>'
                mode = '#'
            elif rune == '.':
                html_string += '<p>'
                mode = '.'

        if rune in ['-', '*', '#']:
            html_string += f'<li>{line}</li>\n'
        elif rune == '1':
            html_string += f'<h1>{line}</h1>\n'
        elif rune == '2':
            html_string += f'<h2>{line}</h2>\n'
        elif rune == '3':
            html_string += f'<h3>{line}</h3>\n'
        elif rune == '4':
            html_string += f'<h4>{line}</h4>\n'
        elif rune == '+':
            html_string += parse_img(line)
        elif rune == ' ':
            html_string += f'<p>{line}</p>\n'
        elif rune == '.':   # preserve linebreaks, for poetry.
            html_string += f'{line}<br>\n'
        elif rune == 'A':   # aside... should this have para formatting?
            html_string += f'<span class="right">{line}</span>\n'
        elif rune == '%':
            html_string += parse_command(line)
        else:
            html_string += f'<p style="color:green;"><b>???</b> {line}</p>\n'
        
        return html_string, mode

    def check_references():
        # check all linked files exist.
        # report errors otherwise.
        pass

## html ------------------------------------------------------------------------

def parse_img(line):
    # count / characters at the start
    num_slashes = len(line) - len(line.lstrip('/'))
    line = line.lstrip('/').lstrip()
    img_file, caption = (line.split(',', 1) + [None])[:2]
    # img_file, style, caption = (line.split(',', 2) + [None])[:3]
    img_class = {
        0: 'left',
        1: 'right',
        2: 'fullwidth'
    }
    if caption is None:
        html_string = f"""
            <figure class="{img_class[num_slashes]}">
                <img src="media\other\{img_file}">
            </figure>\n
            """
    else:
        html_string = f"""
            <figure class="{img_class[num_slashes]}">
                <img src="media\other\{img_file}">
                <figcaption>{caption}</figcaption>
            </figure>\n
            """
    return html_string

def parse_command(line):
    command_end = line.find(':')
    parsed_line = ''
    if command_end == -1:
        print('INVALID COMMAND FORMAT: ', line)
        return None
    else:
        command = line[:command_end]
        line = line[command_end + 1:].lstrip()
        match command:
            case 'html':
                parsed_line = line
            case 'ruby':
                # split on comma to get ruby pairs
                # split on colon to get ruby and ruby tag
                rubies = line.split(',')
                if len(rubies) < 1:
                    print('INVALID RUBY COMMAND: ', line)
                else:
                    for ruby in rubies:
                        if ruby.find(':') == -1:
                            print('INVALID RUBY COMMAND: ', line)
                            return None
                        else:
                            rb, rt = ruby.split(':', 1)
                            parsed_line += f'<ruby>{rb}<rp>(</rp><rt>{rt}</rt><rp>)</rp></ruby>'
            case 'link':
                comma_at = line.find(',')
                if comma_at == -1:
                    # url only
                    parsed_line = f'<a href="{line}">{line}</a>'
                else:
                    # url and description
                    parsed_line = f'<a href="{line[:comma_at]}">{line[comma_at + 1:].strip()}</a>'
            case _:
                print('UNKNOWN COMMAND: ', line)
                return None
        return parsed_line

def format_line(line):

    while has_command(line):
        com_start = line.find('{{')
        com_end = line.find('}}')
        if com_end == -1:
            print('INVALID COMMAND FORMAT: ', line)
            return line
        cmd_substring = line[com_start + 2: com_end]

        if com_end + 3 == len(line):
            line = line[:com_start] + parse_command(cmd_substring)
        else:
            line = line[:com_start] + parse_command(cmd_substring) + line[com_end + 2:]
        

    while has_link(line):
        link_start = line.find('[[')
        link_end = line.find(']]')
        if link_end == -1:
            print('INVALID LINK FORMAT: ', line)
            return line
        link_mid = line.find('][')

        if link_mid == -1 or (link_mid > link_end):
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

def has_command(line):
    return '{{' in line

def has_link(line):
    return '[[' in line

def has_italics(line):
    return '__' in line

def has_bold(line):
    return '**' in line