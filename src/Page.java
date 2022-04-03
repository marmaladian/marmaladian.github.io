package src;

import java.io.File;
import java.io.IOException;
import java.io.FileWriter;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

public class Page {
    private final Settings settings;
    private File file;
    private String[] body;
    private String title;
    private String id;
    private LocalDate createdDate;  // this is actual the first appearance in the logs, not the date the page was created.
    private LocalDate updatedDate;
    private ArrayList<LogEntry> logs = new ArrayList<LogEntry>();
    private String section;
    final String NL = System.getProperty("line.separator");

    public Page(File f, Settings s) {
        this.file = f;
        this.settings = s;
        //  need to put file contents into body
        if (file != null) {
            try(Scanner sc = new Scanner(file)) {
                List<String> lines = new ArrayList<String>();
                while (sc.hasNextLine()) {
                    lines.add(sc.nextLine());
                }
                body = lines.toArray(new String[0]);
                // String[] arr = lines.toArray(new String[0]);  // why new String[0]? https://docs.oracle.com/javase/8/docs/api/java/util/List.html#toArray-T:A-
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        setIDFromFilename();
        setSectionFromFilename();
        this.createdDate = LocalDate.now();
        this.updatedDate = LocalDate.now();
        parsePiHeader(body[0]);
    }

    public Page(String[] body, Settings s) {
        //` FIXME this is hacky to get index page working
        this.settings = s;
        this.body = body;
        this.createdDate = LocalDate.now();
        this.updatedDate = LocalDate.now();
        parsePiHeader(body[0]);
    }

    private void setIDFromFilename() {
        // returns filename without extension
        String fileName = file.getName();
        int pos = fileName.lastIndexOf(".");
        if (pos > 0 && pos < (fileName.length() - 1)) { // If '.' is not the first or last character.
            fileName = fileName.substring(0, pos);
        }
        id = fileName;
    }

    private void setSectionFromFilename() {
        section = file.getParentFile().getName();
    }

    public void setBody(String[] body) {
        this.body = body;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public void setID(String id) {
        this.id = id;
    }

    public String getID() {
        return id;
    }

    public void setSection(String section) {
        this.section = section;
    }

    public String getSection() {
        return section;
    }

    public void addLogEntry(LogEntry l) {
        logs.add(l);
        // System.out.println("Adding log entry: " + l.toString());
    }

    private void parsePiHeader(String header) {
        /* Should be { key: value, key: value, key: value } */
        header = header.replaceAll("\\{", "").replaceAll("\\}", "");
        String[] options = header.split(",");
        for (String option : options) {
            String[] kv = option.split(":");
            switch (kv[0].trim()) {
                case "title":
                    setTitle(kv[1].trim());
                    break;
                default:
                    System.out.println("Header key " + kv[0].trim() + " refers to non-existent page property.");
                    break;
            }
        }
    }

    private String parsePiContent() {
        int lineNum = 0;
        String s = "";    

        lineNum = settings.numHeaderLines;

        ParseMode mode = ParseMode.NORMAL;
            
        for(; lineNum < body.length; ++lineNum) {
            String line = body[lineNum];
            // parse bold/italics
            line = parsePiTags(line, "\\*\\*(.*?)\\*\\*", "strong");
            line = parsePiTags(line, "__(.*?)__", "em");
            line = parsePiTags(line, "~~(.*?)~~", "strike");

            // parse URLs
            line = parsePiLinks(line);

            if ((mode == ParseMode.PARAGRAPH) 
                && (line.length() <= 2
                    || line.charAt(0) != ' ')) {
                mode = ParseMode.NORMAL; // then this line is not part of the para.
                s += "</p>" + NL; 
            } else {
                s += " "; // otherwise, need to add a space when joining up the next line.
            }

            if ((mode == ParseMode.UNORDERED_LIST) 
                && (line.length() <= 2
                    || line.charAt(0) != '-')) {
                mode = ParseMode.NORMAL; // then this line is not part of the para.
                s += "</ul>" + NL; 
            }

            if ((mode == ParseMode.ORDERED_LIST) 
                && (line.length() <= 2
                    || line.charAt(0) != '#')) {
                mode = ParseMode.NORMAL; // then this line is not part of the para.
                s += "</ol>" + NL; 
            }

            if (line.length() > 2) {
                switch (line.charAt(0)) {
                    case ' ':   // FIXME why can't i use settings.LC_PARA here?
                        if (mode != ParseMode.PARAGRAPH) {
                            s += "<p>";
                            mode = ParseMode.PARAGRAPH;
                        }
                        s += line.substring(2);
                        break;
                    case '1':   // H1
                        s += "<h1>" + line.substring(2) + "</h1>";
                        s += NL;
                        break;
                    case '2':   // H2
                        s += "<h2>" + line.substring(2) + "</h2>";
                        s += NL;
                        break;
                    case '3':   // H3
                        s += "<h3>" + line.substring(2) + "</h3>";
                        s += NL;
                        break;
                    case '4':   // H4
                        s += "<h4>" + line.substring(2) + "</h4>";
                        s += NL;
                        break;
                    case '+':   // img
                        //  TODO change the two paths to reference settings obj
                        String[] tokens = line.substring(2).split(" / ");
                        String[] filename = tokens[0].split("\\.");
                        if (tokens.length > 1) {
                            s += HTMLFigure(filename[0], filename[1], "../media/other/", tokens[1]);    
                        } else {
                            s += HTMLFigure(filename[0], filename[1], "../media/other/", "");
                        }
                        s += NL;
                        break;
                    case '-':   // unordered list
                        if (mode != ParseMode.UNORDERED_LIST) {
                            s += "<ul>" + NL;
                            mode = ParseMode.UNORDERED_LIST;
                        }
                        s += "<li>" + line.substring(2) + "</li>";
                        break;
                    case '#':   // ordered list
                        if (mode != ParseMode.ORDERED_LIST) {
                            s += "<ol>" + NL;
                            mode = ParseMode.ORDERED_LIST;
                        }
                        s += "<li>" + line.substring(2) + "</li>";
                        break;
                    default:
                        break;
                }
            }
        }
        //  all lines processed. check if we need to close off any <p>, <ul>, <ol>, tables, etc.
        switch (mode) {
            case UNORDERED_LIST:
                s += "</ul>";
                break;
            case ORDERED_LIST:
                s += "</ol>";
                break;
            case PARAGRAPH:
                s += "</p>";
                break;
            case NORMAL:
            default:
                break;
        }
        return s;
    }

    private String parsePiTags(String s, String regex, String tag) {
        String replacement = String.format("<%s>$1</%s>", tag, tag); 
        s = s.replaceAll(regex, replacement);
        return s;
    }

    private String parsePiLinks(String s) {
        int opening = s.indexOf("[[");
        int closing = s.indexOf("]]") + 2;

        while (opening > 0 && closing > 0) {
            String sub = s.substring(opening, closing);
            int split = sub.indexOf("][");
            if (split < 0) {
                //  link with no description
                //  check if it's a url or a page name.
                String stringStart = s.substring(0, opening);
                String url = sub.substring(2, sub.length() - 2);
                String stringEnd = s.substring(closing, s.length());
                s = stringStart + "<a href=\"" + url + "\">" + url + "</a>" + stringEnd;
            } else {
                //  link with description
                String stringStart = s.substring(0, opening);
                String url = sub.substring(2, split);
                String desc = sub.substring(split + 2, sub.length() - 2);
                String stringEnd = s.substring(closing, s.length());
                s = stringStart + "<a href=\"" + url + "\">" + desc + "</a>" + stringEnd;
            }
            opening = s.indexOf("[[");
            closing = s.indexOf("]]") + 2;
        }
        return s;
    }

    private String HTMLHeader() {
        String str = "<!DOCTYPE html>" + NL +
        "   <head>"  + NL +
        "       <title>%s - %s</title>" + NL +
        (this.getID().equals("index") ? "       <link rel=\"stylesheet\" href=\"css\\main.css\">" : "       <link rel=\"stylesheet\" href=\"..\\css\\main.css\">") + NL +
        "   </head>" + NL +
        "   <body>" + NL +
        "       <h1>%s</h1>" + NL;
        return String.format(str, title, settings.siteName, title);
    }

    public static String HTMLFigure(String filename, String extension, String path, String caption) {
        //  TODO add check to see if image file actually exists or id is "---"
        //  TODO add date back to caption?
        //  path = "../media/log/"
        //  extension = "jpg"
        //  filename = picid or image
        String s = "<figure><img src=\"" + path + filename + "." + extension + "\">";
        if (caption != null && !caption.equals("")) {
            s += "<figcaption>" + caption + "</figcaption>";
        }
        s += "</figure>";
        return s;
    }

    private String HTMLFooter() {
        final String NL = System.getProperty("line.separator");

        String str = NL + "      <div class=\"rule\"></div><hr>" + NL +
        "<div class=\"footer\"><p>id: " + id + "</p>" + NL +
        String.format("       <p>created: %s</p>\n", createdDate.toString()) + NL +
        String.format("       <p>updated: %s</p>\n", updatedDate.toString()) + NL +
        "      </div>" + NL +
        "   </body>" + NL +
        "</html>";
        return String.format(str, settings.siteName);
    }

    public String toHTMLString() {
        String s = "";
        s += HTMLHeader();

        // add header image, if one exists in logs
        System.out.println("\t" + logs.size() + " logs");
        for (LogEntry l : logs) {
            System.out.println("\t" + l.toString());
            if (!l.getPic().equals("---")) {
                if (l.getID().equals("index")) {
                    s += HTMLFigure(l.getPic(), "jpg", "./media/log/", l.getCaption());
                } else {
                    s += HTMLFigure(l.getPic(), "jpg", "../media/log/", l.getCaption());
                }
                l.setProcessed(true);
                break;
            }
        }

        s += parsePiContent();    
        
        //s += parseBody();

        //  add remaining images
        //  TODO change this to use an iterator https://www.java67.com/2018/12/how-to-remove-objects-or-elements-while-iterating-Arraylist-java.html
        for (LogEntry l : logs) {
            System.out.println("\t" + l.toString());
            if (!l.getPic().equals("---")  && l.getProcessed() == false) {
                s += HTMLFigure(l.getPic(), "jpg", "../media/log/", l.getCaption());
                l.setProcessed(true);
            }
        }

        // add remaining captions
        if (logs.size() > 0) {
            boolean logsToDisplay = false;
            for (LogEntry l : logs) {
                if (l.getCaption().length() > 0 && l.getProcessed() == false) {
                    if (logsToDisplay == false) {
                        logsToDisplay = true;
                        s += "<h2>Log entries</h2>" + NL;
                        s += "<ul>" + NL;
                    }
                    s += "<li>" + l.getCaption() + " &#8211; " + l.getDate()+ "</li>" + NL;
                    l.setProcessed(true);
                }
            }
            if (logsToDisplay == true) {
                s += "</ul>" + NL;
            }
        }

        s += HTMLFooter();
        return s;
    }

    public void toFile() {
        System.out.println("Generating " + this.getID());
        try {
            String path = this.getID().equals("index") ? "./" : settings.outputPath;    //  put the index in the root directory
            FileWriter fw = new FileWriter(path + "/" + getID() + ".html");
            // FIXME    handle crash if /site subdir does not exist.
            fw.write(toHTMLString());
            fw.close();
            //System.out.println("Successfully wrote to the file.");
        } catch (IOException e) {
            System.out.println("An error occurred.");
            e.printStackTrace();
        }
    }
}