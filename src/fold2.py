import os
import re
import html as html_lib

PAGES_DIR    = "data/pages"
INCLUDES_DIR = "data/includes"
OUTPUT_DIR   = "docs"

LOGO_SVG = "docs/media/blg.svg"


# The mark is drawn small and centred inside a square 512 viewBox, which is
# what you want for a favicon and not for a wordmark slot. These are the
# bounds of the drawing itself: translate(171.667 40.006) scale(15.339)
# applied to a path spanning 11 x 28 units.
LOGO_VIEWBOX_SQUARE = 'viewBox="0 0 512 512"'
LOGO_VIEWBOX_CROPPED = 'viewBox="171.667 40.006 168.73 429.5"'


def logo_svg():
    """The logo is inlined rather than linked so its fill can be currentColor
    (i.e. var(--ink), following the theme toggle). An <img> can't see the
    page's CSS, and a CSS mask is treated as cross-origin over file://.

    The viewBox is cropped to the drawing on the way out, so the nav can size
    the mark by its own height instead of by the padding around it. The file
    itself is left square, since that is the right shape for an icon."""
    with open(LOGO_SVG, encoding="utf-8") as f:
        svg = f.read().strip()

    if LOGO_VIEWBOX_SQUARE in svg:
        svg = svg.replace(LOGO_VIEWBOX_SQUARE, LOGO_VIEWBOX_CROPPED, 1)
    else:
        print(f"[WARN] {LOGO_SVG}: expected {LOGO_VIEWBOX_SQUARE}, leaving the "
              f"viewBox alone — the mark may sit in its own padding")

    # The link around it carries the accessible name, so the mark itself is
    # hidden rather than announced twice.
    if "aria-hidden" not in svg:
        svg = svg.replace("<svg ", '<svg aria-hidden="true" ', 1)
    return svg


# Directories under data/pages become the section label above a page title.
# A page can override it with `section:` in its front matter, and the index,
# which sits at the root, gets none.
SECTION_LABELS = {
    "gait": "Games and AI",
    "library": "Library",
    "meta": "Meta",
    "projects": "Projects",
    "recipes": "Recipes",
    "shrines": "Shrines",
    "test": "Test",
}


def section_for(src_path):
    rel = os.path.relpath(src_path, PAGES_DIR)
    parts = rel.split(os.sep)
    if len(parts) < 2:
        return ""
    return SECTION_LABELS.get(parts[0], parts[0].replace("-", " ").title())


def build_pagehead(title, section, meta):
    """The header row: section label, page title, and any front-matter fields
    worth showing. All three live in one .titleblock because the vertical
    rules are drawn in the row's first grid row, so a row's children have to
    share it."""
    parts = ['  <header class="row pagehead">\n',
             '    <a class="brand" href="index.html" aria-label="gray.land — home">{{logo}}</a>\n',
             '    <div class="titleblock">\n']
    if section:
        parts.append(f'      <div class="eyebrow">{section}</div>\n')
    parts.append(f'      <h1 id="page-title">{title}</h1>\n')
    if meta:
        parts.append('      <dl class="meta">\n')
        for label, value in meta:
            parts.append(f'        <dt>{label}</dt><dd>{value}</dd>\n')
        parts.append('      </dl>\n')
    parts.append('    </div>\n')
    parts.append('  </header>\n')
    return "".join(parts)


# Block-level tags that may be written straight into a page. A line beginning
# with one of these is copied through verbatim to its matching close rather
# than being read as Markdown. Inline tags are deliberately absent: they are
# already passed through by the paragraph path and should stay in prose.
RAW_BLOCK_TAGS = (
    "table", "div", "section", "article", "aside", "figure", "figcaption",
    "details", "summary", "ul", "ol", "dl", "blockquote", "pre", "nav",
    "header", "footer", "form", "video", "audio", "iframe", "svg", "picture",
)


def strip_tags(text):
    """The <title> element renders markup literally, so inline HTML from the
    heading has to come off before it goes in there."""
    return re.sub(r'<[^>]+>', '', text)


def slugify(text):
    text = re.sub(r'[*_`#]', '', text)
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_]+', '-', text).strip('-')


def apply_inline(text, fn=None):
    """Convert inline Markdown to HTML.

    fn: dict mapping footnote label → number, for [^label] references.
    """
    spans = []

    def protect(s):
        idx = len(spans)
        spans.append(s)
        return f"\x00{idx}\x00"

    # Code spans — protect content from further processing
    text = re.sub(r'`([^`]+)`',
        lambda m: protect(f"<code>{html_lib.escape(m.group(1))}</code>"), text)

    # Footnote references [^label]
    if fn:
        def replace_fn(m):
            label = m.group(1)
            if label in fn:
                n = fn[label]
                return protect(f'<sup><a href="#fn-{label}" id="fnref-{label}">{n}</a></sup>')
            return m.group(0)
        text = re.sub(r'\[\^([^\]]+)\]', replace_fn, text)

    # Links — protect so URL isn't mangled by bold/italic passes
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: protect(f'<a href="{m.group(2)}">{m.group(1)}</a>'), text)

    # Bold (**) before italic (*)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Underline (__) before italic (_)
    text = re.sub(r'__(.+?)__', r'<u>\1</u>', text)

    # Italic — word-boundary aware for _ to avoid foo_bar_baz
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_([^_\n]+)_(?!\w)', r'<em>\1</em>', text)

    for i, s in enumerate(spans):
        text = text.replace(f"\x00{i}\x00", s)
    return text


def strip_markdown(text):
    """Reduce inline Markdown to plain text, for use in HTML attributes like alt."""
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'(\*\*|__)(.+?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.+?)\1', r'\2', text)
    return html_lib.escape(text, quote=True)


def parse_frontmatter(lines):
    """Strip --- delimited front-matter from the top of the file.
    Returns (dict, remaining_lines). Values are raw strings."""
    if not lines or lines[0].rstrip('\n') != '---':
        return {}, lines
    for i, line in enumerate(lines[1:], 1):
        if line.rstrip('\n') == '---':
            fm = {}
            for raw in lines[1:i]:
                if ':' in raw:
                    key, _, val = raw.partition(':')
                    fm[key.strip()] = val.strip()
            return fm, lines[i + 1:]
    return {}, lines


def parse_footnotes(lines):
    """Extract [^label]: text definition lines from content.
    Returns (definitions dict, cleaned lines with definitions removed)."""
    defn_re = re.compile(r'^\[\^([^\]]+)\]:\s*(.+)$')
    definitions = {}
    cleaned = []
    for line in lines:
        m = defn_re.match(line.rstrip('\n'))
        if m:
            definitions[m.group(1)] = m.group(2)
        else:
            cleaned.append(line)
    return definitions, cleaned


def order_footnotes(lines, definitions):
    """Return footnote labels in the order they first appear as [^label] in the text."""
    ref_re = re.compile(r'\[\^([^\]]+)\]')
    seen = []
    in_code = False
    for raw in lines:
        line = raw.rstrip('\n')
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        for m in ref_re.finditer(line):
            label = m.group(1)
            if label not in seen and label in definitions:
                seen.append(label)
    return seen


def build_endnotes(ordered_labels, definitions, fn):
    if not ordered_labels:
        return ""
    parts = ['<section class="endnotes">\n<ol>\n']
    for label in ordered_labels:
        text = apply_inline(definitions.get(label, ''), fn)
        parts.append(
            f'<li id="fn-{label}">{text}'
            f' <a href="#fnref-{label}" aria-label="Back to reference">↩</a>'
            f'</li>\n'
        )
    parts.append('</ol>\n</section>\n')
    return ''.join(parts)


def collect_headings(lines, max_depth):
    """Return [(level, text, slug), ...] for headings up to max_depth."""
    heading_re = re.compile(r'^(#{1,6}) (.+)$')
    headings = []
    in_code = False
    for raw in lines:
        line = raw.rstrip('\n')
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = heading_re.match(line)
        if m and len(m.group(1)) <= max_depth:
            text = re.sub(r'[*_`]', '', m.group(2)).strip()
            headings.append((len(m.group(1)), text, slugify(m.group(2))))
    return headings


def build_toc(headings):
    headings = [(l, t, s) for l, t, s in headings if l > 1]
    if not headings:
        return ""

    parts = ['<nav class="toc">\n<h2>Contents</h2>\n']
    stack = []

    for level, text, slug in headings:
        while stack and stack[-1] > level:
            parts.append('</li>\n</ul>\n')
            stack.pop()
        if not stack or stack[-1] < level:
            parts.append('<ul>\n')
            stack.append(level)
        else:
            parts.append('</li>\n')
        parts.append(f'<li><a href="#{slug}">{text}</a>\n')

    while stack:
        parts.append('</li>\n</ul>\n')
        stack.pop()

    parts.append('</nav>\n')
    return ''.join(parts)


def parse_table(rows, fn=None):
    def cells(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]

    out = ["<table>\n<thead><tr>"]
    for cell in cells(rows[0]):
        out.append(f"<th>{apply_inline(cell, fn)}</th>")
    out.append("</tr></thead>\n")

    if len(rows) > 2:
        out.append("<tbody>\n")
        for row in rows[2:]:
            out.append("<tr>")
            for cell in cells(row):
                out.append(f"<td>{apply_inline(cell, fn)}</td>")
            out.append("</tr>\n")
        out.append("</tbody>\n")

    out.append("</table>\n")
    return "".join(out)


def convert(filename, lines, directives=None, fn=None):
    """Convert content lines to HTML.

    directives: dict mapping directive name → HTML string to splice in
                when [name] appears as a standalone line.
    fn: footnote numbers dict {label: number} for [^label] inline references.
    """
    if directives is None:
        directives = {}

    # Local wrapper so fn is always threaded through without repeating it
    def inline(text):
        return apply_inline(text, fn)

    html_parts = []
    errors = []

    para_buf         = []
    list_type        = None
    list_items       = []
    table_rows       = []
    blockquote_lines = []
    code_lines       = []
    code_lang        = ""
    in_code          = False
    in_gallery       = False
    gallery_items    = []
    page_title       = None
    raw_tag          = None
    raw_lines        = []
    raw_depth        = 0
    pending_h4       = None

    # .content wraps the whole article and is its own grid, using the same
    # column tracks as the row, so body copy can be pushed out into the side
    # tracks. Nothing sits outside it any more — the page title has moved to
    # the header row — so it opens here rather than waiting for the h1. A page
    # with no h1 gets the same wrapper as any other.
    html_parts.append('<article class="content">\n')

    heading_re   = re.compile(r"^(#{1,6}) (.+)$")
    img_re       = re.compile(r'^!\[(.*)\]\(([^\s"]+)(?:\s+"([^"]*)")?\)$')
    ul_re        = re.compile(r"^[-*] (.+)$")
    ol_re        = re.compile(r"^\d+\. (.+)$")
    hr_re        = re.compile(r"^[-*_]{3,}$")
    directive_re = re.compile(r'^\[(\w+)\]$')
    raw_open_re  = re.compile(r'^<(' + '|'.join(RAW_BLOCK_TAGS) + r')(?=[\s>])', re.I)

    def gallery_figure(caption, src):
        return (
            f'<figure class="gallery">\n'
            f'<img src="{src}" alt="{strip_markdown(caption)}">\n'
            f'<figcaption>{inline(caption)}</figcaption>\n'
            f'</figure>\n'
        )

    def flush_para(resolve_pending=True):
        nonlocal pending_h4
        if para_buf:
            content = inline(" ".join(para_buf))
            if pending_h4:
                slug, htext = pending_h4
                # \paragraph{}-style run-in: bold, full stop, folded into
                # the paragraph that follows rather than its own element.
                # This has to happen at the HTML level, not in CSS — the
                # h4 and the paragraph after it would otherwise be two
                # separate children of .content, which is a grid, and grid
                # blockifies every direct child regardless of its own
                # display value, so no display trick can put them on one
                # line if they stay separate elements.
                content = f'<strong class="run-in-h4" id="{slug}">{htext}.</strong> ' + content
                pending_h4 = None
            html_parts.append(f"<p>{content}</p>\n")
            para_buf.clear()
        elif pending_h4 and resolve_pending:
            # Nothing to run into — falls back to an ordinary heading.
            slug, htext = pending_h4
            html_parts.append(f'<h4 id="{slug}">{htext}</h4>\n')
            pending_h4 = None

    def flush_list():
        nonlocal list_type
        if list_type:
            html_parts.append(f"<{list_type}>\n")
            for item in list_items:
                html_parts.append(f"<li>{inline(item)}</li>\n")
            html_parts.append(f"</{list_type}>\n")
            list_items.clear()
            list_type = None

    def flush_table():
        if table_rows:
            html_parts.append(parse_table(table_rows, fn))
            table_rows.clear()

    def flush_blockquote():
        if blockquote_lines:
            html_parts.append("<blockquote>\n")
            for bq_line in blockquote_lines:
                html_parts.append(f"<p>{inline(bq_line)}</p>\n")
            html_parts.append("</blockquote>\n")
            blockquote_lines.clear()

    def flush_all():
        flush_para()
        flush_list()
        flush_table()
        flush_blockquote()

    for lineno, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")

        # --- Code block fence ---
        if line.strip().startswith("```"):
            if in_code:
                lang_attr = f' class="language-{code_lang}"' if code_lang else ""
                escaped = html_lib.escape("\n".join(code_lines))
                html_parts.append(f"<pre><code{lang_attr}>{escaped}</code></pre>\n")
                code_lines.clear()
                code_lang = ""
                in_code = False
            else:
                flush_all()
                code_lang = line.strip()[3:].strip()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        # --- Inside a raw HTML block: copy through, counting nesting ---
        if raw_tag is not None:
            raw_lines.append(line)
            raw_depth += len(re.findall(rf'<{raw_tag}(?=[\s>])', line, re.I))
            raw_depth -= len(re.findall(rf'</{raw_tag}\s*>', line, re.I))
            if raw_depth <= 0:
                html_parts.append("\n".join(raw_lines) + "\n")
                raw_lines = []
                raw_tag = None
            continue

        # --- Comment: a whole line of <!-- ... --> is dropped entirely ---
        if re.match(r"^\s*<!--.*-->\s*$", line):
            continue

        # --- Empty line ---
        if line.strip() == "":
            # A pending h4 rides through blank lines rather than resolving
            # here — markdown convention is a blank line between a heading
            # and the paragraph under it, so resolving on the first one
            # would make the run-in case (the common one) never fire.
            flush_para(resolve_pending=False)
            flush_list()
            flush_table()
            continue

        stripped = line.strip()

        # --- Raw HTML block ---
        # A block-level tag starting a line is handed through untouched to the
        # matching close, so hand-written tables and embeds survive. Without
        # this the opening tag is treated as prose and the whole block ends up
        # inside a <p>, which is invalid and puts the element out of reach of
        # the layout classes, since it is no longer a child of .content.
        m = raw_open_re.match(stripped)
        if m:
            flush_all()
            raw_tag = m.group(1).lower()
            raw_lines = [line]
            raw_depth = (len(re.findall(rf'<{raw_tag}(?=[\s>])', line, re.I))
                         - len(re.findall(rf'</{raw_tag}\s*>', line, re.I)))
            if raw_depth <= 0:
                html_parts.append(line + "\n")
                raw_lines = []
                raw_tag = None
            continue

        # --- Gallery block: [gallery] ... [/gallery] ---
        if stripped == "[gallery]":
            flush_all()
            in_gallery = True
            gallery_items.clear()
            continue

        if in_gallery:
            if stripped == "[/gallery]":
                figures = "".join(gallery_figure(c, s) for c, s in gallery_items)
                html_parts.append(f'<div class="full">\n<div class="gallery">\n{figures}</div>\n</div>\n')
                gallery_items.clear()
                in_gallery = False
                continue
            m = img_re.match(stripped)
            if m:
                gallery_items.append((m.group(1), m.group(2)))
            elif stripped:
                errors.append((lineno, f"Expected an image inside [gallery]: {line}"))
            continue

        # --- Directive: [name] ---
        m = directive_re.match(stripped)
        if m:
            name = m.group(1)
            flush_all()
            if name in directives:
                html_parts.append(directives[name])
            else:
                errors.append((lineno, f"Unknown directive: [{name}]"))
            continue

        # --- Horizontal rule ---
        if hr_re.match(stripped):
            flush_all()
            html_parts.append("<hr>\n")
            continue

        # --- Heading ---
        m = heading_re.match(line)
        if m:
            flush_all()
            level = len(m.group(1))
            # The page title belongs to the header row, not to the article, so
            # the first h1 is taken out of the body and handed back to the
            # caller to put in .pagehead. Any later h1 stays where it is.
            if level == 1 and page_title is None:
                page_title = inline(m.group(2))
                continue
            slug = slugify(m.group(2))
            if level == 4:
                # Held rather than emitted — resolved by flush_para() once
                # it knows whether a paragraph actually follows.
                pending_h4 = (slug, inline(m.group(2)))
                continue
            html_parts.append(f'<h{level} id="{slug}">{inline(m.group(2))}</h{level}>\n')
            continue

        # --- Block image → figure ---
        m = img_re.match(stripped)
        if m:
            flush_all()
            caption, src, modifier = m.group(1), m.group(2), (m.group(3) or "").strip().lower()
            cls = f' class="{modifier}"' if modifier in ("side", "wide", "wide-alt", "full") else ""
            html_parts.append(
                f'<figure{cls}>\n'
                f'<img src="{src}" alt="{strip_markdown(caption)}">\n'
                f'<figcaption>{inline(caption)}</figcaption>\n'
                f'</figure>\n'
            )
            continue

        # --- Table row ---
        if stripped.startswith("|"):
            flush_para()
            flush_list()
            table_rows.append(line)
            continue

        # --- Unordered list item ---
        m = ul_re.match(line)
        if m:
            flush_para()
            flush_table()
            if list_type == "ol":
                flush_list()
            list_type = "ul"
            list_items.append(m.group(1))
            continue

        # --- Ordered list item ---
        m = ol_re.match(line)
        if m:
            flush_para()
            flush_table()
            if list_type == "ul":
                flush_list()
            list_type = "ol"
            list_items.append(m.group(1))
            continue

        # --- Blockquote ---
        if stripped.startswith("> "):
            flush_para()
            flush_list()
            flush_table()
            blockquote_lines.append(stripped[2:])
            continue

        # --- Paragraph text ---
        para_buf.append(line)

    if raw_tag is not None:
        errors.append((len(lines), f"Unclosed raw <{raw_tag}> block"))
        html_parts.append("\n".join(raw_lines) + "\n")

    flush_all()
    html_parts.append('</article>\n')
    return "".join(html_parts), errors, page_title


def clear_html(output_dir):
    for root, _dirs, files in os.walk(output_dir):
        for f in files:
            if f.endswith(".html"):
                os.remove(os.path.join(root, f))


def main():
    with open(os.path.join(INCLUDES_DIR, "header.html"), encoding="utf-8") as f:
        header = f.read()
    with open(os.path.join(INCLUDES_DIR, "footer.html"), encoding="utf-8") as f:
        footer = f.read()

    logo = logo_svg()

    clear_html(OUTPUT_DIR)

    md_files = []
    for root, _dirs, files in os.walk(PAGES_DIR):
        for f in files:
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))
    md_files.sort()

    seen = {}
    for src_path in md_files:
        stem = os.path.splitext(os.path.basename(src_path))[0]
        if stem in seen:
            print(f"[ERROR] filename collision: {src_path} and {seen[stem]} both output to {stem}.html — skipping {src_path}")
            continue
        seen[stem] = src_path

    for src_path in md_files:
        md_file = os.path.basename(src_path)
        stem = os.path.splitext(md_file)[0]
        if seen.get(stem) != src_path:
            continue
        out_path = os.path.join(OUTPUT_DIR, stem + ".html")

        with open(src_path, encoding="utf-8") as f:
            lines = f.readlines()

        frontmatter, content_lines = parse_frontmatter(lines)
        definitions, content_lines = parse_footnotes(content_lines)
        ordered_labels = order_footnotes(content_lines, definitions)
        fn = {label: i + 1 for i, label in enumerate(ordered_labels)}

        directives = {}
        toc_html = ""
        if frontmatter.get('toc', 'false').lower() == 'true':
            max_depth = int(frontmatter.get('toc_depth', '3'))
            headings = collect_headings(content_lines, max_depth)
            toc_html = build_toc(headings)
        # The contents is placed automatically, outside the article. [toc] is
        # kept as a no-op so a directive left in an older page is ignored
        # rather than reported as unknown.
        directives['toc'] = ""
        if ordered_labels:
            directives['endnotes'] = build_endnotes(ordered_labels, definitions, fn)

        body, errors, page_title = convert(md_file, content_lines, directives, fn)

        # Auto-append endnotes if [endnotes] wasn't placed manually. This has
        # to go inside the article, so it is spliced in before the closing tag
        # rather than tacked on the end.
        if ordered_labels and '[endnotes]' not in ''.join(content_lines):
            body = body.replace('</article>\n', '<hr>\n' + directives['endnotes'] + '</article>\n')

        # The contents list is a sibling of the article, not a child of it.
        # Both sit in the same grid row, which gives the sticky column the full
        # height of the article to travel through; nested inside, it would stop
        # at the end of its own row.
        if toc_html:
            body += toc_html

        # optional per-page hook: `class: foo` in front-matter lands on the
        # .content element, so a stylesheet can target one page
        page_class = frontmatter.get('class', '')
        if page_class:
            body = body.replace('<article class="content">',
                                f'<article class="content {page_class}">', 1)

        for lineno, msg in errors:
            print(f"[{md_file}:{lineno}] {msg}")

        if not page_title:
            print(f"[{md_file}] no h1 — falling back to the filename for the title")
            page_title = stem

        section = frontmatter.get('section', section_for(src_path))
        meta = [(k.title(), frontmatter[k])
                for k in ('date', 'read', 'makes', 'time', 'serves')
                if frontmatter.get(k)]

        # {{pagehead}} first: the header block it inserts carries its own
        # {{logo}} placeholder, which the following replace then fills.
        page = (header
                .replace("{{title}}", strip_tags(page_title))
                .replace("{{pagehead}}", build_pagehead(page_title, section, meta))
                .replace("{{logo}}", logo)
                .replace("{{runhead_title}}", strip_tags(page_title)))

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
            f.write(body)
            f.write(footer)

        print(f"Built {out_path}")


if __name__ == "__main__":
    main()
