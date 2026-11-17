# gray.land

This repository includes the data and static site builder for gray.land.

## Directory structure
```
.
├── README.md           You are here!
├── data                Source files for the site content
│   ├── pages           Source files for pages
│   └── includes        Partial HTML for footers, etc.
├── docs                Built site pages go here (flat file structure)
│   ├── css             
│   └── media           Images
└── src                 Static site generator

/src    Static site generator
/data   Raw data for site

/docs   built site
```

## Pages
The `data/pages` directory contains Markdown source files that are used to
produce the built site. There are no subdirectories, page names must be unique.

### Special pages
The contents page is automatically generated lists all pages in alphabetical
order.

## Images
Images are named yyyy-mm-dd-123.png when they relate to a specific date
or event, such as an image for a journal entry or a personal photograph.

They are named page-title-123.png when they are associated with a specific page.

Images that are reused on multiple pages may just be named according to
their content.