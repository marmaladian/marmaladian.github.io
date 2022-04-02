- start writing a simple html format (line based, except for tables + lists which will be mode based)
    - other inline
        ~~strong~~
        ~~emphasis~~
        ~~strikethrough~~
        - ?
    - tables (ayeeeee)
    - ~~ordered lists~~
    - ~~unordered lists~~
    - quotes
    - literal lines (i.e. ignore and place the exact html)
- ~~fix blank lines after anything but paras~~
- ~~build index~~
- build nav pages?
- build section indexes?
    - could give each page a parent to build a tree?
- internal links
- ~~get id from filename~~
- get section from folder name
- sort pages based on most recent order in the log
    - ~~go through logs, if there's an unseen ID add it to a list.~~
    - ~~then pick top X for recent~~
    - show the last date?
    - then put the rest under the sections in that order
    - sections appear in a predefined order (unless they're missing, in which case they appear at the end).
- set last activity for a page based on the log (respecting the display flag), get rid of created/updated dates.
- get created date from the first entry in the logs.
- create photo file (filename, corresponding page, date, caption)
    - ~~append automatically to a matching page (if photodb)~~
    - ~~show most recent photo at the top of the page, show rest at the bottom~~
    - ~~show captions below photos~~
    - build warning if missing caption
- convert the header info to a series of key/vals, so some can be optional.
- allow unicode
- make the generated HTML pretty
- change sections to be based on folders instead of listing in front matter
- delete old pages from the site build folder!
- add dates to log captions (with images and solo)
- check duplicate source files (had two dnd.pis)
- add flag to text only log entries indicating whether they should be displayed at the end of the topic
- abstract the figure/img/caption creation into a function (accepts img, or img and caption)
- put the caption date on a new line (p or li tags inside figcaption?)

# Errors
- how to log errors to a 'global' error db?
- build error if image or other linked file cannot be found.
- invalid date used
- if file does not fit format (e.g. log.pi), then program crashes

# CSS
- make page size consistent (seems to shrink in dev tools mode)

# Format
## Standard page
{ header }
content

## Log data
yyyymmdd project/page time-spent
yyyymmdd project/page photo comment
yyyymmdd project/page log

use log as a special page that includes log entries for all projects/pages.

# Structure
index
 |- page
     |- content
     |- relevant photos
     |- log entries
 |- page
 |- page

 /root
   /pages
   /scripts
   /css
   /databases
   /images
   /documents