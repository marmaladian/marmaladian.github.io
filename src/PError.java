package src;
import java.io.File;

public class PError {
    private File file;
    private int lineNumber;
    private String description;
    private String line;

    public PError(String description, File file, String line, int lineNumber) {
        this.description = description;
        this.file = file;
        this.line = line;
        this.lineNumber = lineNumber;
    }

    public PError(String description, File file, String line) {
        this(description, file, line, -1);
    }

    public PError(String description) {
        this(description, null, "N/A", -1);
    }

    public String toString() {
        String s;
        if (file != null) {
            s = "" + description + ", on line " + lineNumber + " of " + file.getName() + "\n\t" + line;
        } else {
            s = description;
        }
        return s;
    }
}