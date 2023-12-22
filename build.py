import os
import re
from datetime import datetime
from collections import defaultdict

# Function to extract metadata from file
def extract_metadata(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()

    metadata = {}
    index = content.index('---\n')

    meta_lines = content[:index]
    metadata['content'] = ''.join(content[index + 1:])

    for line in meta_lines:
        key, value = re.match(r'^(.*?):\s(.*?)\s*$', line).groups()
        metadata[key.lower()] = value.strip()

    return metadata

# Function to create HTML pages
def create_pages(input_dir, header_path, footer_path, output_dir):
    pages = defaultdict(list)

    # Read header and footer
    with open(header_path, 'r') as header_file:
        header = header_file.read()
    with open(footer_path, 'r') as footer_file:
        footer = footer_file.read()

    # Traverse input directory
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                metadata = extract_metadata(file_path)

                page_title = metadata.get('page title', 'Default Title')
                stylesheet = metadata.get('style sheet', 'style.css')
                parent_category = metadata.get('parent category')

                # Create output content
                output_content = header.replace('{{ page_title }}', page_title).replace('{{ stylesheet }}', stylesheet)
                output_content += metadata['content'] + footer

                # Create output directory
                output_subdir = os.path.join(output_dir, parent_category.lower().replace(' ', '_')) if parent_category else output_dir
                os.makedirs(output_subdir, exist_ok=True)

                # Generate output file path
                output_filename = re.sub(r'[^\w\s]', '', page_title).lower().replace(' ', '_') + '.html'
                output_path = os.path.join(output_subdir, output_filename)

                # Write to output file
                with open(output_path, 'w') as output_file:
                    output_file.write(output_content)

                # Update pages dictionary for index page
                last_updated = datetime.strptime(metadata['date last updated'], '%Y-%m-%d')
                pages[parent_category].append((page_title, output_path, last_updated))

    # Build index page
    with open(os.path.join(output_dir, 'index.html'), 'w') as index_file:
        index_file.write('<html>\n<body>\n')

        # Sort pages by last updated date
        for category, category_pages in sorted(pages.items()):
            index_file.write(f'<h2>{category}</h2>\n')
            sorted_pages = sorted(category_pages, key=lambda x: x[2], reverse=True)
            for page in sorted_pages:
                index_file.write(f'<a href="{page[1]}">{page[0]}</a> - Last Updated: {page[2].strftime("%Y-%m-%d")}<br>\n')

        index_file.write('</body>\n</html>')

# Usage
input_directory = 'src/pages'
header_file_path = 'src/partials/header.html'
footer_file_path = 'src/partials/footer.html'
output_directory = 'pages'

create_pages(input_directory, header_file_path, footer_file_path, output_directory)
