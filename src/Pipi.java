package src;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class Pipi {

   private static final Settings settings = new Settings(); 
   private static ArrayList<String> ids = new ArrayList<String>();

   private static void collectFilesWithExtension(File path, ArrayList<Page> list, String ext) {
      // adds any files in specified folder + subfolders with extension to arraylist
      for (final File f : path.listFiles()) {
         if (f.isDirectory()) {
            collectFilesWithExtension(f, list, ext);
         } else {
            if (hasExtension(f, ext)) {
               Page p = new Page(f, settings);
               list.add(p);
            }
         }
      }
   }

   private static String getFileExtension(File f) {
      String filename = f.toString();
      String extension = "";
      int index = filename.lastIndexOf('.');
      if (index > 0) {
         extension = filename.substring(index + 1);
      }
      return extension;
   }

   private static boolean hasExtension(File f, String extension) {
      return getFileExtension(f).equals(extension);
   }

   private static void addID(String id) {
      if (!ids.contains(id)) {
         ids.add(id);
      }
   }

   private static void deleteFilesInDir(File dir) {
      for (File file: dir.listFiles()) {
            if (file.isDirectory())
               deleteFilesInDir(dir);
            file.delete();
      }  
   }

   public static void main(String[] args) {
      // parse pages
      ArrayList<Page> pages = new ArrayList<Page>();
      ArrayList<String> ids = new ArrayList<String>();
      final File sourceFolder = new File(settings.sourcePath);
      collectFilesWithExtension(sourceFolder, pages, "pi");

      // parse log file
      File log = new File(settings.logPath);
      LogEntry mostRecentImage = null;
      try(BufferedReader br = new BufferedReader(new FileReader(log))) {
         int numLines = 1;
         br.readLine(); // skip header row
         for(String line; (line = br.readLine()) != null; ) {
            ++numLines;
            // read log, generate list of photos+captions, or just captions with matching pages.
            // add those to the pages and also the 'timeline' page.
            // TODO skip adding log entries that don't have an x in the 'display' column
            String[] tokens = line.split("\t");

            if (tokens.length > 2) {
               String date = tokens[0];
               String pic = tokens[1];
               String id = tokens[2];
               if (!ids.contains(id)) {
                  ids.add(id);
               }
               String caption = "";
               if (tokens.length > 3) {
                   caption = tokens[3];
               }
               LogEntry l = new LogEntry(date, pic, id, caption);
               System.out.println("!!\t" + id);

               if (mostRecentImage == null && !(l.getPic().equals("---"))) {
                  // FIXME ugh, using date below.
                  // we're creaitng this so we can add it as a log to the index page later.
                  // but it doesn't work, because the index page is already at the root dir...
                  mostRecentImage = new LogEntry(date, l.getPic(), "index", l.getCaption());
               }

               // iterate through pages and find one with matching topic
               for (Page p : pages) {
                  if (p.getID().equals(l.getID())) {
                     System.out.println("Adding " + l.getID() + " to " + p.getID());
                     p.addLogEntry(l);
                     break;
                  }
               }
            } else {
               System.out.print("ERROR\t  Invalid log entry, line " + numLines + ".");
            }

         }
      } catch (Exception e) {
         e.printStackTrace();
      }

      // delete old pages
      deleteFilesInDir(new File(settings.outputPath));

      // generate pages
      for (Page p : pages) {
         p.toFile();
      }

      // generate index
      final String NL = System.getProperty("line.separator");
      // header
      String body = "{ title: Park Imminent, section: root, created: 1982-06-28, updated: 1982-06-28 }" + NL;
      // body
      
      //    recent
      body += "2 Recent" + NL;

      System.out.println("Finding recently logged pages...");
      int found = 0;
      for (int i = 0; i < ids.size(); ++i) {
         System.out.println(ids.get(i));
         for (Page p : pages) {
            System.out.println("\t" + p.getID());
            if (p.getID().equals(ids.get(i))) {
               body += "- [[" + settings.outputPath + "/" + p.getID() + ".html" + "][" + p.getTitle() + "]]" + NL;
               ++found;
            }
            if (found >= settings.recentItems) {
               break;
            }
         }
         if (found >= settings.recentItems) {
            break;
         }
      }
      //    all
      //    create h2s for sections
      List<String> sectionList = new ArrayList<String>(settings.sections.keySet());
      for (String section : sectionList) {
         body += "2 " + settings.sections.get(section) + NL;
         for (Page p : pages) {
            if (p.getSection().equals(section)) {
               body += "- [[" + settings.outputPath + "/" + p.getID() + ".html" + "][" + p.getTitle() + "]]" + NL;
            }
         }
         body += NL;
      }

      //    create <p>s for pages;


      // now put all this into a special index page
      Page index = new Page(body.split("\n"), settings);
      index.setTitle("Park Imminent");
      index.setID("index");
      index.setIsIndex(true);
      index.addLogEntry(mostRecentImage);
      index.toFile();
  }
}