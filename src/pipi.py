# TODO implement inline links as commands
# TODO implement inline asides
# TODO display inline asides correctly?
# TODO CSS for smaller screens
# TODO log errors and return to pipi.py?
# TODO print line numbers for errors
# TODO add blockquotes + attributions (style like poetry)
# TODO add header
# TODO add footer + webring links
# TODO work out image storage - log, etc.
# TODO put log images down the sidebar?
# TODO fix issue with html blocks overlapping (fullwidth image followed by poem)
# TODO make asides styled with background when placed inline (small screen)
# TODO fix bug where files require a last blank line (log.pi)
# TODO build categories (use numbers to order, trim numbers)

# NOTE commands
#      --------
#      ruby: <rb:rt>, rb:rt>...
#      html: <html literal>
#      link: url
#      link: url, link-text
#      link: page-name
#
#      formatting
#      ----------
#      __ italics     
#      ** bold
#      [[url]]
#      [[url][link-text]
#      
#      line types
#      ----------
#      A aside

import os

from page import Page

data_dir = 'data'
output_dir = 'site'

def build_site():

    # remove html from last build
    for out in get_files_recursive(output_dir, '.html'):
        os.remove(out)
    
    # remove dynamically generated index source
    index_src_file = f'{data_dir}/index.pi'
    if os.path.exists(index_src_file):
        os.remove(index_src_file)

    # get source files
    src_files = get_files_recursive(data_dir, '.pi')

    pages = []
    categories = {}

    # create page objects
    # pages are responsible for rendering their html
    for src in src_files:
        p = Page(src)
        if not p.category() in categories:
            categories[p.category()] = []
        categories[p.category()].append(p)
        pages.append(p)

    # build index
    with open(f'{data_dir}/index.pi', 'wt') as out:
        print('1 Park Imminent\n', file=out)
        print('  ', file=out)
        for category in categories:
            print(f'2 {category}', file=out)
            for page in categories[category]:
                print(f'- {{{{link: {output_dir}/{page.filename()}.html, {page.title()}}}}}', file=out)
    index = Page(f'{data_dir}/index.pi')

    for page in pages:
        with open(f'{output_dir}/{page.filename()}.html', 'wt') as out:
            print(page.html(), file=out)

    with open(f'index.html', 'wt') as out:
        print(index.html(), file=out)


def get_files_recursive(path, filetype):
    file_list = []
    for f in os.listdir(path):
        full_path = os.path.join(path, f)
        if os.path.isdir(full_path):
            file_list.extend(get_files_recursive(full_path, filetype))
        elif f.endswith(filetype):
            file_list.append(full_path)
    return file_list

build_site()