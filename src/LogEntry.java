package src;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

public class LogEntry {
    LocalDate date;
    String pic;
    String id;
    String caption;
    boolean isProcessed = false;

    public LogEntry(String date, String pic, String id, String caption) {
        this.date = LocalDate.parse(date, DateTimeFormatter.ofPattern("yyMMdd"));
        this.pic = pic;
        this.id = id;
        this.caption = caption;
    }

    public LocalDate getDate() {
        return date;
    }

    public String getPic() {
        return pic;
    }

    public String getID() {
        return id;
    }

    public String getCaption() {
        return caption;
    }

    public boolean getProcessed() {
        return isProcessed;
    }

    public void setProcessed(boolean isProcessed) {
        this.isProcessed = isProcessed;
    }

    public String toString() {
        return "" + date.toString() + ", " + pic + ", " + id + ", " + caption;
    }
}