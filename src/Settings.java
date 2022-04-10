package src;

import java.util.HashMap;
import java.time.format.DateTimeFormatter;

public class Settings {
    public final String siteName = "Park Imminent";
    public final String logPath = "./src/data/log";
    public final String sourcePath = "./src/pages";
    public final String outputPath = "./site";
    public final int numHeaderLines = 1;    // title, (code)name, section, created, updated, ----
    public final char LC_PARA = ' ';
    public final int recentItems = 6;
    public final HashMap<String, String> sections = new HashMap<String, String>();
    public final DateTimeFormatter dateFormat = DateTimeFormatter.ofPattern("MMMM d, yyyy");

    public Settings() {
        sections.put("craft", "Craft");
        sections.put("games", "Games");
        sections.put("languages", "Languages");
        sections.put("misc", "Miscellaneous");
        sections.put("programming", "Programming");
        sections.put("recipes", "Recipes");
        sections.put("tempo", "Tempo");
        sections.put("travel", "Travel");
        sections.put("design", "Design");
    }
}
