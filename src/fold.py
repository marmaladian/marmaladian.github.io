# a python version of fold to test out some ideas

DATA_DIR = "data"
OUTPUT_DIR = "docs"

SHOW_COMMENTS = False

import os
import fnmatch
import re
from datetime import date

RUN_LOG_PATH = os.path.join(DATA_DIR, "special", "running.log")
RUN_DEFAULT_UNIT = "km"
HABIT_LOG_PATH = os.path.join(DATA_DIR, "special", "habits.log")

def node(name, children=(), pages=(), **attrs):
    return {"name": name, "children": list(children), "pages": list(pages), "attrs": dict(attrs)}

def add_child(parent, child):
    parent["children"].append(child)
    return child

def walk(n):
    yield n
    for c in n["children"]:
        yield from walk(c)

def pretty(n, indent=""):
    print(f"{indent}{n['name']}")
    for c in n["children"]:
        pretty(c, indent + "  ")
    for p in n["pages"]:
        page_file = p["file"] if isinstance(p, dict) else p
        print(f"{indent}  {page_file}")

def get_page_metadata(filepath):
    """Extract title, style, and order from a .f file's front-matter."""
    metadata = {"title": None, "style": "default.css", "order": None}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(": "):
                    parts = line[2:].split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if key == "title":
                            metadata["title"] = value
                        elif key == "style":
                            metadata["style"] = value if value.endswith(".css") else value + ".css"
                        elif key == "order":
                            metadata["order"] = value
                elif not line.startswith(": "):
                    # stop at first non-frontmatter line
                    break
    except:
        pass
    return metadata
    return metadata

def build_site_tree():
    index = node("index")

    # root is curdir
    # dir is list of directories in curdir
    # files is list of files in curdir

    for root, dir, files in os.walk(DATA_DIR):
        # if no .f files in files, skip
        if not any(fnmatch.fnmatch(file, "*.f") for file in files):
            continue

        rel_path = os.path.relpath(root, DATA_DIR)
        parts = [] if rel_path == "." else rel_path.split(os.sep)
        current_node = index
        path_parts = []
        for part in parts:
            if not part:
                continue
            path_parts.append(part)
            # find the child node with the name of part
            child = next((c for c in current_node["children"] if c["name"] == part), None)
            if child is None:
                child = node(part)
                # store the full path for the node (without the data/ prefix)
                child["attrs"]["path"] = os.path.join(*path_parts)
                add_child(current_node, child)
            current_node = child

        for file in files:
            if fnmatch.fnmatch(file, "*.f"):
                filepath = os.path.join(root, file)
                metadata = get_page_metadata(filepath)
                # Store page as dict with filename and metadata
                page_entry = {"file": file, "metadata": metadata}
                current_node["pages"].append(page_entry)
    return index  

def get_last_updated_date():
    """Return the current date in a readable format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

def parse_time_to_seconds(time_str):
    parts = time_str.split(":")
    try:
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + int(seconds)
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    except ValueError:
        return None
    return None

def format_time_seconds(total_seconds):
    total_seconds = int(round(total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"

def format_number(value, decimals=2):
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")

def format_distance(value, unit):
    return f"{format_number(value, 2)} {unit}"

def format_speed(value, unit):
    return f"{format_number(value, 2)} {unit}"

def format_pace(speed_kmh):
    """Return pace as MM:SS for a given speed in km/h."""
    if not speed_kmh or speed_kmh <= 0:
        return ""
    seconds_per_km = 3600 / speed_kmh
    minutes, seconds = divmod(int(round(seconds_per_km)), 60)
    return f"{minutes}:{seconds:02d}"

def format_run_type_with_dot(run_type):
    """Generate SVG dot + run type text for display in tables."""
    svg = f'<svg class="run-dot run-type-{run_type}" viewBox="0 0 12 12" xmlns="http://www.w3.org/2000/svg"><circle cx="6" cy="6" r="6"/></svg>'
    return f"{svg} {run_type}"

def convert_distance(value, unit, default_unit):
    if unit is None:
        unit = default_unit
    if unit == default_unit:
        return value
    if unit == "mi" and default_unit == "km":
        return value * 1.609344
    if unit == "km" and default_unit == "mi":
        return value * 0.621371
    return value

def convert_speed(value, unit, default_unit):
    default_speed_unit = "km/h" if default_unit == "km" else "mph"
    if unit is None:
        unit = default_speed_unit
    if unit == "kph":
        unit = "km/h"
    if unit == "km/h" and default_speed_unit == "mph":
        return value * 0.621371
    if unit == "mph" and default_speed_unit == "km/h":
        return value * 1.609344
    return value

def extract_value(rest, patterns):
    for pattern in patterns:
        match = re.search(pattern, rest)
        if match:
            value = match.group(1)
            unit = match.group(2) if match.lastindex and match.lastindex >= 2 else None
            rest = rest[:match.start()] + " " + rest[match.end():]
            return value, unit, rest
    return None, None, rest

def parse_running_log(path, default_unit="km"):
    runs = []
    errors = []
    if not os.path.exists(path):
        return runs, errors

    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            match = re.match(r"^(\d{4}-\d{2}-\d{2})\s+(\S+)\s+(.+)$", line)
            if not match:
                errors.append(f"Line {line_no}: Could not parse line '{line}'")
                continue

            date_str, run_type, rest = match.groups()
            try:
                run_date = date.fromisoformat(date_str)
            except ValueError:
                errors.append(f"Line {line_no}: Invalid date '{date_str}'")
                continue

            note = ""
            note_match = re.search(r"(?i)\bnote\s*[:=]\s*(.+)$", rest)
            if note_match:
                note = note_match.group(1).strip()
                rest = rest[:note_match.start()].strip()
            else:
                pipe_idx = rest.find("|")
                if pipe_idx >= 0:
                    note = rest[pipe_idx+1:].strip()
                    rest = rest[:pipe_idx].strip()
            note = re.sub(r"^(--|\||//)\s*", "", note).strip()

            speed_str, speed_unit, rest = extract_value(
                rest,
                [
                    r"(?i)\b(?:speed|v)\s*[:=]\s*(\d+(?:\.\d+)?)\s*(km\/h|kph|mph)\b",
                    r"(?i)\b(\d+(?:\.\d+)?)\s*(km\/h|kph|mph)\b",
                ],
            )
            distance_str, distance_unit, rest = extract_value(
                rest,
                [
                    r"(?i)\b(?:dist|distance|d)\s*[:=]\s*(\d+(?:\.\d+)?)\s*(km|mi)?\b",
                    r"(?i)\b(\d+(?:\.\d+)?)\s*(km|mi)\b",
                ],
            )
            time_str, _, rest = extract_value(
                rest,
                [
                    r"(?i)\b(?:time|t)\s*[:=]\s*(\d{1,2}:\d{2}(?::\d{2})?)\b",
                    r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b",
                ],
            )

            distance = float(distance_str) if distance_str else None
            if distance is not None:
                distance = convert_distance(distance, distance_unit, default_unit)

            speed = float(speed_str) if speed_str else None
            if speed is not None:
                speed = convert_speed(speed, speed_unit, default_unit)

            time_seconds = parse_time_to_seconds(time_str) if time_str else None

            fields_present = sum(value is not None for value in (distance, time_seconds, speed))
            if fields_present < 2:
                errors.append(f"Line {line_no}: Need at least two of distance, time, speed")
                continue

            if distance is None and speed is not None and time_seconds is not None:
                distance = speed * (time_seconds / 3600)
            if time_seconds is None and speed is not None and distance is not None:
                time_seconds = (distance / speed) * 3600
            if speed is None and distance is not None and time_seconds is not None:
                hours = time_seconds / 3600
                speed = distance / hours if hours > 0 else None

            if distance is None or time_seconds is None or speed is None:
                errors.append(f"Line {line_no}: Could not compute missing field")
                continue

            iso_year, iso_week, _ = run_date.isocalendar()
            runs.append(
                {
                    "date": run_date,
                    "type": run_type,
                    "distance": distance,
                    "time_seconds": time_seconds,
                    "speed": speed,
                    "note": note,
                    "week_key": f"{iso_year}-W{iso_week:02d}",
                }
            )

    return runs, errors

def parse_habits_log(path):
    entries = []
    errors = []
    habits = []
    active_indices = []
    header_found = False
    if not os.path.exists(path):
        return entries, habits, active_indices, errors

    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if not header_found:
                if "," not in line:
                    continue
                parts = [part.strip() for part in line.split(",")]
                if not parts or parts[0].lower() != "date":
                    errors.append(f"Line {line_no}: Header must start with 'date'")
                    continue
                for idx, raw_name in enumerate(parts[1:]):
                    name = raw_name.strip()
                    is_struck = name.startswith("~~") and name.endswith("~~") and len(name) > 4
                    if is_struck:
                        name = name[2:-2].strip()
                    habits.append(name)
                    if not is_struck:
                        active_indices.append(idx)
                header_found = True
                continue

            if "," in line:
                parts = [part.strip() for part in line.split(",", 1)]
            else:
                parts = line.split(None, 1)
            if len(parts) < 2:
                errors.append(f"Line {line_no}: Missing habit marks")
                continue

            date_str, marks_str = parts[0], parts[1].replace(" ", "")
            try:
                entry_date = date.fromisoformat(date_str)
            except ValueError:
                errors.append(f"Line {line_no}: Invalid date '{date_str}'")
                continue

            if not re.match(r"^[xX-]+$", marks_str):
                errors.append(f"Line {line_no}: Invalid habit marks '{marks_str}'")
                continue

            marks = [char.lower() for char in marks_str]
            if len(marks) < len(habits):
                marks.extend(["-"] * (len(habits) - len(marks)))
            if len(marks) > len(habits):
                marks = marks[:len(habits)]

            iso_year, iso_week, _ = entry_date.isocalendar()
            entries.append(
                {
                    "date": entry_date,
                    "marks": marks,
                    "week_key": f"{iso_year}-W{iso_week:02d}",
                }
            )

    if not header_found:
        errors.append("No header row found in habits log")

    return entries, habits, active_indices, errors

def build_runs_by_week(runs):
    runs_by_week = {}
    for run in runs:
        runs_by_week.setdefault(run["week_key"], []).append(run)
    for week_runs in runs_by_week.values():
        week_runs.sort(key=lambda r: r["date"])
    return runs_by_week

def build_habits_by_week(entries):
    habits_by_week = {}
    for entry in entries:
        habits_by_week.setdefault(entry["week_key"], []).append(entry)
    for week_entries in habits_by_week.values():
        week_entries.sort(key=lambda e: e["date"])
    return habits_by_week

def build_week_run_table_html(week_runs, default_unit):
    speed_unit = "km/h" if default_unit == "km" else "mph"
    total_distance = sum(run["distance"] for run in week_runs)
    total_time = sum(run["time_seconds"] for run in week_runs)
    total_speed = total_distance / (total_time / 3600) if total_time > 0 else 0

    parts = ["<div class='running'>", "<h4>Running</h4>", "<table>"]
    parts.append("<thead><tr><th>Day</th><th>Type</th><th>Distance</th><th>Time</th><th>Speed</th></tr></thead>")
    parts.append("<tbody>")

    for run in week_runs:
        date_label = run["date"].strftime("%a")
        distance_label = format_distance(run["distance"], default_unit)
        time_label = format_time_seconds(run["time_seconds"])
        speed_label = format_speed(run["speed"], speed_unit)
        type_label = format_run_type_with_dot(run["type"])
        row = (
            "<tr>"
            f"<td>{date_label}</td>"
            f"<td>{type_label}</td>"
            f"<td>{distance_label}</td>"
            f"<td>{time_label}</td>"
            f"<td>{speed_label}</td>"
            "</tr>"
        )
        parts.append(row)

    parts.append("</tbody>")

    total_distance_label = format_distance(total_distance, default_unit)
    total_time_label = format_time_seconds(total_time)
    total_speed_label = f"{format_speed(total_speed, speed_unit)} av."
    parts.append("<tfoot>")
    total_row = (
        "<tr>"
        f"<td>Total</td>"
        f"<td></td>"
        f"<td>{total_distance_label}</td>"
        f"<td>{total_time_label}</td>"
        f"<td>{total_speed_label}</td>"
        "</tr>"
    )
    parts.append(total_row)
    parts.append("</tfoot>")
    parts.append("</table>")
    parts.append("</div>")
    return "\n".join(parts)

def build_week_run_lines(week_runs, default_unit):
    html = build_week_run_table_html(week_runs, default_unit)
    return [f"! {line}" for line in html.splitlines()]

def build_week_habit_table_html(week_entries, habits, active_indices):
    if not week_entries or not active_indices:
        return ""

    parts = ["<div class='habits'>", "<h4>Habits</h4>", "<table class='habits-week'>"]
    header_cells = "".join(f"<th>{habits[i]}</th>" for i in active_indices)
    parts.append(f"<thead><tr><th>Day</th>{header_cells}</tr></thead>")
    parts.append("<tbody>")
    for entry in week_entries:
        date_label = entry["date"].strftime("%a")
        marks = "".join(
            f"<td>{'x' if entry['marks'][i] == 'x' else '-'}</td>" for i in active_indices
        )
        parts.append(f"<tr><td>{date_label}</td>{marks}</tr>")
    parts.append("</tbody></table></div>")
    return "\n".join(parts)

def build_week_habit_lines(week_entries, habits, active_indices):
    html = build_week_habit_table_html(week_entries, habits, active_indices)
    if not html:
        return []
    return [f"! {line}" for line in html.splitlines()]

def inject_weekly_runs(content_lines, runs_by_week, default_unit):
    updated = []
    current_week = None
    for line in content_lines:
        match = re.match(r"^3\s+(\d{4}-W\d{2})\s*$", line)
        if match:
            if current_week:
                week_runs = runs_by_week.get(current_week)
                if week_runs:
                    updated.extend(build_week_run_lines(week_runs, default_unit))
            current_week = match.group(1)
            updated.append(line)
            continue
        updated.append(line)
    if current_week:
        week_runs = runs_by_week.get(current_week)
        if week_runs:
            updated.extend(build_week_run_lines(week_runs, default_unit))
    return updated

def inject_weekly_habits(content_lines, habits_by_week, habits, active_indices):
    updated = []
    current_week = None
    for line in content_lines:
        match = re.match(r"^3\s+(\d{4}-W\d{2})\s*$", line)
        if match:
            if current_week:
                week_entries = habits_by_week.get(current_week)
                if week_entries:
                    updated.extend(build_week_habit_lines(week_entries, habits, active_indices))
            current_week = match.group(1)
            updated.append(line)
            continue
        updated.append(line)
    if current_week:
        week_entries = habits_by_week.get(current_week)
        if week_entries:
            updated.extend(build_week_habit_lines(week_entries, habits, active_indices))
    return updated

def build_running_week_graph(runs, default_unit):
    if not runs:
        return ""

    weeks = {}
    for run in runs:
        week = run["week_key"]
        bucket = weeks.setdefault(week, {"distance": 0.0, "time": 0.0, "count": 0})
        bucket["distance"] += run["distance"]
        bucket["time"] += run["time_seconds"]
        bucket["count"] += 1

    speed_unit = "km/h" if default_unit == "km" else "mph"
    distance_unit = default_unit
    week_keys = sorted(weeks.keys())
    if len(week_keys) > 8:
        week_keys = week_keys[-8:]
    stats = []
    for week in week_keys:
        bucket = weeks[week]
        avg_speed = bucket["distance"] / (bucket["time"] / 3600) if bucket["time"] > 0 else 0
        week_distance = bucket["distance"]
        stats.append((avg_speed, week_distance))

    speed_vals = [value[0] for value in stats]
    distance_vals = [value[1] for value in stats]
    all_vals = speed_vals + distance_vals
    min_val = min(all_vals)
    max_val = max(all_vals)
    left_pad = 2
    right_pad = 22
    vert_pad = 6
    width = 100
    height = 36
    plot_height = height

    if min_val == max_val:
        span = max_val if max_val != 0 else 1
        min_val = min_val - span * 0.5
        max_val = min_val + span

    def scale_y(value):
        return vert_pad + (plot_height - 2 * vert_pad) * (1 - (value - min_val) / (max_val - min_val))

    def scale_x(index):
        if len(stats) == 1:
            return width / 2
        return left_pad + index * (width - left_pad - right_pad) / (len(stats) - 1)

    speed_points = " ".join(
        f"{scale_x(i):.2f},{scale_y(value):.2f}" for i, value in enumerate(speed_vals)
    )
    distance_points = " ".join(
        f"{scale_x(i):.2f},{scale_y(value):.2f}" for i, value in enumerate(distance_vals)
    )

    speed_dots = []
    distance_dots = []
    for i, value in enumerate(speed_vals):
        x_pos = scale_x(i)
        y_pos = scale_y(value)
        speed_dots.append(
            f"<circle class='running-graph-point run-type-tempo' cx='{x_pos:.2f}' cy='{y_pos:.2f}' r='0.7'/>"
        )
    for i, value in enumerate(distance_vals):
        x_pos = scale_x(i)
        y_pos = scale_y(value)
        distance_dots.append(
            f"<circle class='running-graph-point run-type-long' cx='{x_pos:.2f}' cy='{y_pos:.2f}' r='0.7'/>"
        )

    last_index = len(stats) - 1
    last_x = scale_x(last_index)
    speed_last_y = scale_y(speed_vals[last_index])
    distance_last_y = scale_y(distance_vals[last_index])
    speed_label = f"{format_number(speed_vals[last_index], 2)} {speed_unit}"
    distance_label = f"{format_number(distance_vals[last_index], 2)} {distance_unit}"
    end_labels = (
        f"<text class='running-graph-value run-type-tempo' x='{last_x + 3:.2f}' y='{speed_last_y + 1:.2f}' text-anchor='start'>{speed_label}</text>"
        f"<text class='running-graph-value run-type-long' x='{last_x + 3:.2f}' y='{distance_last_y + 1:.2f}' text-anchor='start'>{distance_label}</text>"
    )

    return "".join(
        [
            "<div class='running-graph'>",
            "<svg viewBox='0 0 100 36' role='img' aria-label='Weekly running averages'>",
            f"<polyline class='running-graph-speed run-type-tempo' points='{speed_points}'/>",
            f"<polyline class='running-graph-distance run-type-long' points='{distance_points}'/>",
            "".join(speed_dots),
            "".join(distance_dots),
            end_labels,
            "</svg>",
            "</div>",
        ]
    )

def build_running_log_html(runs, default_unit):
    if not runs:
        return "<div class='text'><p>No runs found.</p></div>"

    speed_unit = "km/h" if default_unit == "km" else "mph"
    total_distance = sum(run["distance"] for run in runs)
    total_time = sum(run["time_seconds"] for run in runs)
    rows = []
    for run in sorted(runs, key=lambda r: r["date"], reverse=True):
        date_label = run["date"].strftime("%Y-%m-%d")
        distance_label = format_distance(run["distance"], default_unit)
        time_label = format_time_seconds(run["time_seconds"])
        speed_label = format_speed(run["speed"], speed_unit)
        pace_label = format_pace(run["speed"]) if default_unit == "km" else ""
        note_label = run.get("note", "")
        type_label = format_run_type_with_dot(run["type"])
        rows.append(
            "<tr>"
            f"<td>{date_label}</td>"
            f"<td>{type_label}</td>"
            f"<td>{distance_label}</td>"
            f"<td>{time_label}</td>"
            f"<td>{speed_label}</td>"
            f"<td>{pace_label}</td>"
            f"<td>{note_label}</td>"
            "</tr>"
        )

    total_distance_label = format_distance(total_distance, default_unit)
    total_time_label = format_time_seconds(total_time)
    avg_speed = total_distance / (total_time / 3600) if total_time > 0 else 0
    avg_pace_label = format_pace(avg_speed) if default_unit == "km" else ""
    total_row = (
        "<tr>"
        "<td>Total</td>"
        "<td></td>"
        f"<td>{total_distance_label}</td>"
        f"<td>{total_time_label}</td>"
        "<td></td>"
        f"<td>{avg_pace_label}</td>"
        "<td></td>"
        "</tr>"
    )

    graph_html = build_running_week_graph(runs, default_unit)
    return (
        "<div class='text'>"
        + graph_html +
        "<h2>Runs</h2>"
        "<table class='running-log'>"
        "<thead><tr><th>Date</th><th>Type</th><th>Distance</th><th>Time</th><th>Speed</th><th>Pace</th><th>Note</th></tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody>"
        "<tfoot>"
        + total_row
        + "</tfoot></table></div>"
    )

def build_habits_log_html(entries, habits, active_indices):
    if not entries or not active_indices:
        return "<div class='text'><p>No habits found.</p></div>"

    header_cells = "".join(f"<th>{habits[i]}</th>" for i in active_indices)
    rows = []
    for entry in sorted(entries, key=lambda e: e["date"], reverse=True):
        date_label = entry["date"].strftime("%Y-%m-%d")
        marks = "".join(
            f"<td>{'x' if entry['marks'][i] == 'x' else '-'}</td>" for i in active_indices
        )
        rows.append(f"<tr><td>{date_label}</td>{marks}</tr>")

    return (
        "<div class='text'>"
        "<h2>Habits</h2>"
        "<table class='habits-log'>"
        f"<thead><tr><th>Date</th>{header_cells}</tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )

def slugify_heading(text):
    """Convert heading text to a URL-safe anchor slug."""
    import re
    text = re.sub(r"\{\{\s*([^|]+?)\s*\|\s*[^}]+?\s*\}\}", r"\1", text)
    text = re.sub(r"(\*\*|__|\*|_|`|~~)", "", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text
    
def html_header(title, rel_root="", css_file="default.css", site=None):
    nav_html = ""
    # if site:
    #     nav_html = build_full_nav(site, rel_root)
    return f"""
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="{rel_root}css/{css_file}">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Baskervville:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap" rel="stylesheet">
        <title>{title} &mdash; gray.land</title>
    </head>
    <body id="top">
    """

def layout_open(rel_root="", nav_html=""):
    return f'''
        <div class="layout">
            <div class="kicker"><img src="{rel_root}media/eico-2.gif">{nav_html}</div>
    '''
def html_footer(rel_root=""):
    return f'''
            <footer class="text">
                <hr>
                <div>last updated {get_last_updated_date()} &middot; <a href=\"{rel_root}site-map.html\">site map</a> &middot; <a href=\"#top\">top ↑</a></div>
            </footer>
        </div>
    </body>
</html>
    '''

def rel_root_for(output_path):
    rel_dir = os.path.relpath(os.path.dirname(output_path), OUTPUT_DIR)
    if rel_dir == ".":
        return ""
    depth = len(rel_dir.split(os.sep))
    return "../" * depth

def apply_inline_formatting(text, site=None, rel_root="", errors=None):
    # apply inline formatting for **bold** (or __bold__) and *italic* (or _italic_)
    # `code`, ~~strikethough~~, and {{link text|url}}
    # note that urls not starting with https are links to a page in the site, so {{About|about}} would link to about.html.
    # need to search the site tree for the page with the name of the url, and link to it if it exists, otherwise report an error.
    import re
    if errors is None:
        errors = []
    # handle links first since they can contain other formatting
    link_tokens = []
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        html = None
        if url.startswith("#"):
            html = f'<a href="{url}">{link_text}</a>'
        elif url.startswith("http") or url.startswith("https"):
            html = f'<a href="{url}">{link_text}</a>'
        else:
            # search the site tree for the page with the name of the url
            if site:
                for n in walk(site):
                    # check if url matches a node name
                    if n["name"] == url:
                        html = f'<a href="{rel_root}{n["attrs"]["path"]}/index.html">{link_text}</a>'
                        break
                    # check if url matches a page in this node
                    for page_entry in n["pages"]:
                        page_file = page_entry["file"] if isinstance(page_entry, dict) else page_entry
                        page_name = os.path.splitext(page_file)[0]
                        if page_name == url:
                            html = f'<a href="{rel_root}{n["attrs"]["path"]}/{page_name}.html">{link_text}</a>'
                            break
                    if html is not None:
                        break
                if html is None:
                    errors.append(f"Could not find page '{url}' for link text '{link_text}'")
            if html is None:
                return link_text  # return the text without a link
        token = f"%%LINK{len(link_tokens)}%%"
        link_tokens.append(html)
        return token
    
    # the urls are encoded like {{link text|url}} or {{link text | url}} with spaces around the |, so we need to handle that in the regex
    text = re.sub(r"\{\{\s*([^|]+?)\s*\|\s*([^}]+?)\s*\}\}", replace_link, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"_([^_]+)_", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)
    for i, html in enumerate(link_tokens):
        text = text.replace(f"%%LINK{i}%%", html)
    return text

def parse_frontmatter(content_lines):
    """Extract front-matter from the beginning of a file.
    
    Front-matter lines start with ': ' and contain 'key: value' pairs.
    Returns (frontmatter_dict, remaining_lines)
    """
    frontmatter = {}
    remaining_lines = []
    parsing_frontmatter = True
    
    for line in content_lines:
        if parsing_frontmatter and line.startswith(": "):
            # Parse front-matter line: ": key: value"
            parts = line[2:].split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                frontmatter[key] = value
        else:
            parsing_frontmatter = False
            remaining_lines.append(line)
    
    return frontmatter, remaining_lines

def extract_headings(content_lines, page_title):
    """Extract h2-h6 headings from content lines.
    
    Returns a list of dicts: [{"level": 2, "text": "...", "id": "..."}, ...]
    """
    headings = []
    for line in content_lines:
        if len(line) < 3:
            continue
        prefix, rest = line[0], line[2:]
        
        if prefix in ["2", "3", "4", "5", "6"]:
            # Extract heading text (strip inline formatting for TOC)
            heading_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', rest)  # Remove links
            heading_text = re.sub(r'`([^`]+)`', r'\1', heading_text)  # Remove code
            heading_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', heading_text)  # Remove bold
            heading_text = re.sub(r'__([^_]+)__', r'\1', heading_text)  # Remove bold
            heading_text = re.sub(r'\*([^\*]+)\*', r'\1', heading_text)  # Remove italic
            heading_text = re.sub(r'_([^_]+)_', r'\1', heading_text)  # Remove italic
            heading_text = re.sub(r'~~([^~]+)~~', r'\1', heading_text)  # Remove strikethrough
            heading_text = heading_text.strip()
            
            heading_id = slugify_heading(rest)
            headings.append({
                "level": int(prefix),
                "text": heading_text,
                "id": heading_id
            })
    
    return headings

def build_toc_html(headings):
    """Build a nested unordered list from headings.
    
    Returns HTML string with class 'toc'.
    """
    if not headings:
        return ""
    
    html_parts = ["<div class='toc'>"]
    level_stack = []  # Stack of heading levels
    
    for heading in headings:
        level = heading["level"]
        text = heading["text"]
        heading_id = heading["id"]
        
        # Close lists when going back up to a shallower level
        while level_stack and level_stack[-1] > level:
            level_stack.pop()
            html_parts.append("</li></ul>")
        
        # Same level - close previous item and start new sibling
        if level_stack and level_stack[-1] == level:
            html_parts.append("</li>")
        
        # Open new nested list when going deeper
        if not level_stack or level_stack[-1] < level:
            html_parts.append("<ul>")
            level_stack.append(level)
        
        # Add the current item (leave it open for potential children)
        html_parts.append(f"<li><a href='#{heading_id}'>{text}</a>")
    
    # Close all remaining open items and lists
    while level_stack:
        level_stack.pop()
        html_parts.append("</li></ul>")
    
    html_parts.append("</div>")
    return "\n".join(html_parts)

def create_page(src_file, path, rel_root="", site=None, run_log=None, habit_log=None):
    if site is None:
        raise ValueError("create_page requires a site tree for inline links")

    # read the .f file and convert it to html
    with open(src_file, "r", encoding="utf-8") as f:
        content_lines = f.read().splitlines()

    # extract front-matter
    frontmatter, content_lines = parse_frontmatter(content_lines)
    
    # get title and style from front-matter, with fallbacks
    page_title = frontmatter.get("title", os.path.splitext(os.path.basename(src_file))[0].capitalize())
    css_file = frontmatter.get("style", "default.css")
    if not css_file.endswith(".css"):
        css_file += ".css"

    # parse line by line: the first character is a prefix indicating the type of line. the rest [2:] is the actual content
    
    # Extract headings for potential TOC
    headings = extract_headings(content_lines, page_title)
    toc_html = build_toc_html(headings) if headings else ""
    
    rel_dir = os.path.relpath(os.path.dirname(src_file), DATA_DIR)
    is_journal_year = rel_dir == "journal" and re.match(r"^\d{4}\.f$", os.path.basename(src_file))
    if is_journal_year and run_log:
        content_lines = inject_weekly_runs(content_lines, run_log.get("runs_by_week", {}), run_log.get("unit", RUN_DEFAULT_UNIT))
    if is_journal_year and habit_log:
        content_lines = inject_weekly_habits(
            content_lines,
            habit_log.get("habits_by_week", {}),
            habit_log.get("habits", []),
            habit_log.get("active_indices", []),
        )
    current_node = find_node_by_path(site, rel_dir)
    current_page = os.path.splitext(os.path.basename(src_file))[0]
    local_nav = build_local_nav(site, current_node, rel_root, current_page=current_page)
    page_title_id = slugify_heading(page_title)
    html_content = f"<div class='page-header'>{local_nav}<h1 class='page-title' id='{page_title_id}'>{page_title}</h1></div>"
    list_stack = []
    blockquote_open = False
    div_stack = []
    text_div_open = False
    raw_html_mode = False
    raw_html_class = None
    errors = []
    nav_html = ""

    html_content += layout_open(rel_root, nav_html)

    for line in content_lines:
        # Check for raw HTML block delimiter
        if line.strip().startswith("!!!"):
            if not raw_html_mode:
                # Entering raw HTML mode
                html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
                if text_div_open:
                    html_content += "</div>"
                    text_div_open = False
                # Extract optional class name
                parts = line.strip().split(None, 1)
                if len(parts) > 1:
                    raw_html_class = parts[1].strip()
                    html_content += f"<div class='{raw_html_class}'>"
                raw_html_mode = True
            else:
                # Exiting raw HTML mode
                if raw_html_class:
                    html_content += "</div>"
                    raw_html_class = None
                raw_html_mode = False
            continue
        
        # If in raw HTML mode, just append the line directly
        if raw_html_mode:
            html_content += line + "\n"
            continue
        
        # Check for TOC command
        if line.strip() == ": toc":
            if toc_html:
                html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
                if not text_div_open and not div_stack:
                    html_content += "<div class='text'>"
                    text_div_open = True
                html_content += toc_html
            continue
        
        if len(line) < 3 and not line.startswith("|"):
            continue
        if line.startswith("|"):
            # close text div if open before processing explicit div
            if text_div_open:
                html_content += "</div>"
                text_div_open = False
            class_name = line[1:].strip()
            if class_name:
                div_stack.append(class_name)
                html_content += f"<div class='{class_name}'>"
            else:
                if div_stack:
                    div_stack.pop()
                    html_content += "</div>"
                else:
                    errors.append(f"Unmatched div close in line: {line}")
            continue
        prefix, rest = line[0], line[2:]

        if prefix in ["1", "2", "3", "4", "5", "6"]:
            heading_id = slugify_heading(rest)
            rest = apply_inline_formatting(rest, site, rel_root, errors)
            if prefix == "1" and rest.strip().lower() == page_title.strip().lower():
                continue
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
            html_content += f"<h{prefix} id='{heading_id}'>{rest}</h{prefix}>"

        elif prefix == "%":
            # % Doenjang jjigae | full | journal/2026-W03.jpg
            #   figure caption | class | image path
            if text_div_open:
                html_content += "</div>"
                text_div_open = False
            html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
            parts = rest.rsplit(" | ", 2)
            if len(parts) == 3:
                caption_raw, cls_raw, img_path_raw = parts
            else:
                parts = rest.split("|")
                caption_raw = parts[0] if len(parts) > 0 else ""
                cls_raw = parts[1] if len(parts) > 1 else ""
                img_path_raw = parts[2] if len(parts) > 2 else ""
            caption = caption_raw.strip()
            caption_html = apply_inline_formatting(caption, site, rel_root, errors)
            cls = cls_raw.strip()
            img_path = img_path_raw.strip()
            # figures get "side" class if no class specified, otherwise use specified class
            if not cls:
                cls = "side"
            html_content += f"<figure class='{cls}'><img src='{rel_root}media/{img_path}' alt='{caption}'><figcaption>{caption_html}</figcaption></figure>"

        elif prefix == ">":
            # blockquote
            rest = apply_inline_formatting(rest, site, rel_root, errors)
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            if not blockquote_open:
                html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
                html_content += "<blockquote>"
                blockquote_open = True
            html_content += f"<p>{rest}</p>"

        elif prefix in ["*", "#", " "]:
            # check first non-space character in content
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            if blockquote_open:
                html_content += "</blockquote>"
                blockquote_open = False
            html_content = handle_list_or_para(html_content, list_stack, line, site, rel_root, errors)

        elif prefix == "/":
            rest = apply_inline_formatting(rest, site, rel_root, errors)
            if (SHOW_COMMENTS):
                html_content += f"<span class='comment'>{rest}</span>"

        elif prefix == "!":
            html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            html_content += rest
        
        else:
            html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
            if not text_div_open and not div_stack:
                html_content += "<div class='text'>"
                text_div_open = True
            errors.append(f"Unknown prefix '{prefix}' in line: {line}")
            html_content += f"<pre><b>UNKNOWN: </b>{line}</pre>"

    html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
    if text_div_open:
        html_content += "</div>"
        text_div_open = False
    if div_stack:
        errors.append(f"Unclosed div(s): {', '.join(div_stack)}")
        while div_stack:
            div_stack.pop()
            html_content += "</div>"

    if frontmatter.get("auto") == "running-log" and run_log:
        html_content += build_running_log_html(run_log.get("runs", []), run_log.get("unit", RUN_DEFAULT_UNIT))
    if frontmatter.get("auto") == "habits-log" and habit_log:
        html_content += build_habits_log_html(
            habit_log.get("entries", []),
            habit_log.get("habits", []),
            habit_log.get("active_indices", []),
        )
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_header(page_title, rel_root, css_file, site))
        f.write(html_content)
        f.write(html_footer(rel_root))
    
    return errors

def handle_list_or_para(html_content, list_stack, line, site=None, rel_root="", errors=None):
    if errors is None:
        errors = []
    list_type, num_leading_spaces = next(((c, i) for i, c in enumerate(line) if c != " "), (None, 0))
    list_level = (num_leading_spaces // 2) + 1 if list_type in ["*", "#"] else 0

    diff = list_level - len(list_stack)

    if list_type not in ["*", "#"]:
        # either we're not in a list, or we need to close it off
        rest = line[num_leading_spaces:]
        rest = apply_inline_formatting(rest, site, rel_root, errors)
        html_content, list_stack = clear_list_stack(html_content, list_stack, 0)
        html_content += f"<p>{rest}</p>"
    else:
        # we're already in a list, are we continuing, changing the depth, or changing the type
        rest = line[num_leading_spaces + 2:]
        rest = apply_inline_formatting(rest, site, rel_root, errors)
        if diff > 0:
            # we need to open a new list
            html_content += f"<{ 'ul' if list_type == '*' else 'ol' }>"
            list_stack.append(list_type)
        elif diff < 0:
            # we need to close the current list
            html_content, list_stack = clear_list_stack(html_content, list_stack, list_level)
        elif list_stack and list_stack[-1] != list_type:
            # we need to close the current list and open a new one
            html_content, list_stack = clear_list_stack(html_content, list_stack, list_level - 1)
            html_content += f"<{ 'ul' if list_type == '*' else 'ol' }>"
            list_stack.append(list_type)
        html_content += f"<li>{rest}</li>"
    return html_content

def clear_list_stack(html_content, list_stack, target_depth):
    while len(list_stack) > target_depth:
        html_content += f"</{ 'ul' if list_stack[-1] == '*' else 'ol' }>"
        list_stack.pop()
    return html_content, list_stack

def close_open_blocks(html_content, list_stack, blockquote_open):
    """Close any open list and blockquote blocks."""
    html_content, list_stack = clear_list_stack(html_content, list_stack, 0)
    if blockquote_open:
        html_content += "</blockquote>"
        blockquote_open = False
    return html_content, list_stack, blockquote_open

def find_node_by_name(site, name):
    for n in walk(site):
        if n["name"] == name:
            return n
    return None

def find_node_by_path(site, rel_dir):
    if rel_dir in ("", "."):
        return site
    # Use get_node_nav_path to compare paths instead of attrs["path"]
    # This handles cases where attrs["path"] may be incorrectly set
    for n in walk(site):
        nav_path = get_node_nav_path(site, n)
        if nav_path == rel_dir:
            return n
    # Fallback to old method for compatibility
    for n in walk(site):
        if n["attrs"].get("path") == rel_dir:
            return n
    return None

def find_parent_node(site, target):
    if target is None:
        return None
    def _walk(node, parent):
        if node is target:
            return parent
        for child in node["children"]:
            found = _walk(child, node)
            if found is not None:
                return found
        return None
    return _walk(site, None)

def get_node_nav_path(site, node):
    """Build the navigation path for a node by traversing from root to node."""
    if node is site:
        return ""
    
    path_parts = []
    current = node
    while current is not None and current is not site:
        path_parts.insert(0, current["name"])
        current = find_parent_node(site, current)
    
    return "/".join(path_parts) if path_parts else ""

def get_sort_order(item, index):
    """Get sort order from an item. Items can be directory nodes or page entries."""
    # For directory nodes
    if "name" in item and "children" in item:
        # Check if there's an index.f file for order metadata
        for page in item.get("pages", []):
            page_name = os.path.splitext(page["file"])[0]
            if page_name == "index":
                order_val = page.get("metadata", {}).get("order")
                if order_val is not None:
                    return int(order_val)
                return index
        return index
    # For page entries
    elif "file" in item:
        order_val = item.get("metadata", {}).get("order")
        if order_val is not None:
            return int(order_val)
        return index
    return index

def sort_with_order(items, item_type="page"):
    """Sort items by their order metadata, preserving original order for unspecified items."""
    indexed_items = []
    for i, item in enumerate(items):
        has_explicit_order = False
        sort_order = None
        
        # Check if this item has an explicit order
        if "name" in item and "children" in item:
            for page in item.get("pages", []):
                page_name = os.path.splitext(page["file"])[0]
                if page_name == "index":
                    sort_order = page.get("metadata", {}).get("order")
                    if sort_order is not None:
                        has_explicit_order = True
                        sort_order = int(sort_order)
                    break
        elif "file" in item:
            sort_order = item.get("metadata", {}).get("order")
            if sort_order is not None:
                has_explicit_order = True
                sort_order = int(sort_order)
        
        # For items without explicit order, use default value of 500
        if not has_explicit_order:
            sort_order = 500
        
        indexed_items.append((sort_order, i, item))
    
    indexed_items.sort(key=lambda x: (x[0], x[1]))
    return [item for _, _, item in indexed_items]

def build_local_nav(site, node, rel_root="", current_page=None):
    if not site or not node:
        return ""

    # Build path from root to current node
    path_to_current = []
    current = node
    while current is not None and current is not site:
        path_to_current.insert(0, current)
        current = find_parent_node(site, current)

    def is_in_path(check_node):
        """Check if a node is in the path from root to current"""
        return check_node in path_to_current

    def render_dir_link(dir_node, is_active=False):
        name = dir_node["name"] + "/"
        nav_path = get_node_nav_path(site, dir_node)
        path = f"{rel_root}{nav_path}/index.html" if nav_path else f"{rel_root}index.html"
        active_class = " class='active'" if is_active else ""
        return f"<li><a href='{path}'{active_class}>{name}</a></li>"

    def render_siblings_ul(parent_node):
        if not parent_node or not parent_node["children"]:
            return ""
        html = "<ul>"
        sorted_children = sort_with_order(parent_node["children"])
        for sibling in sorted_children:
            is_active = is_in_path(sibling)
            html += render_dir_link(sibling, is_active=is_active)
        html += "</ul>"
        return html

    def render_current_ul(current_node):
        items = []
        sorted_children = sort_with_order(current_node["children"])
        for child in sorted_children:
            items.append(render_dir_link(child))
        sorted_pages = sort_with_order(current_node["pages"])
        for page_entry in sorted_pages:
            page_file = page_entry["file"]
            page_name = os.path.splitext(page_file)[0]
            # Skip index.f since it's the directory's main content
            if page_name == "index":
                continue
            nav_path = get_node_nav_path(site, current_node)
            page_url = f"{rel_root}{nav_path}/{page_name}.html" if nav_path else f"{rel_root}{page_name}.html"
            # Mark current page as active
            is_active = (current_page is not None and page_name == current_page)
            active_class = " class='active'" if is_active else ""
            items.append(f"<li><a href='{page_url}'{active_class}>{page_name}</a></li>")
        if not items:
            return ""
        return "<ul>" + "".join(items) + "</ul>"

    parent = find_parent_node(site, node)
    grandparent = find_parent_node(site, parent) if parent else None

    uls = []
    
    # Always add home link as its own ul (active class since we're always descending from home)
    home_ul = f"<ul><li><a href='{rel_root}index.html' class='active'>gray.land</a></li></ul>"
    uls.append(home_ul)
    
    # Add hierarchy levels
    if grandparent is site:
        # Depth 2: show top-level dirs, then parent's siblings
        uls.append(render_siblings_ul(grandparent))
        uls.append(render_siblings_ul(parent))
    elif parent is site:
        # Depth 1: show top-level dirs
        uls.append(render_siblings_ul(parent))
    else:
        # Depth 3+: show full hierarchy
        if grandparent:
            uls.append(render_siblings_ul(grandparent))
        if parent:
            uls.append(render_siblings_ul(parent))
    
    current_ul = render_current_ul(node)
    if current_ul:
        uls.append(current_ul)

    if not uls:
        return ""
    return "<nav class='local-nav'>" + "".join(uls) + "</nav>"

def build_site_map(site, rel_root=""):
    def render_node(node):
        node_name = node["name"]
        node_path = f"{rel_root}{node['attrs']['path']}/index.html"
        html = f"<li><a href='{node_path}'>{node_name}</a>"
        if node["pages"] or node["children"]:
            html += "<ul>"
            sorted_pages = sort_with_order(node["pages"])
            for page_entry in sorted_pages:
                page_file = page_entry["file"]
                page_name = os.path.splitext(page_file)[0]
                # Skip index.f since it's the directory's main content
                if page_name == "index":
                    continue
                html += f"<li><a href='{rel_root}{node['attrs']['path']}/{page_name}.html'>{page_name}</a></li>"
            sorted_children = sort_with_order(node["children"])
            for child in sorted_children:
                html += render_node(child)
            html += "</ul>"
        html += "</li>"
        return html

    if not site:
        return ""
    html = "<ul>"
    html += f"<li><a href='{rel_root}index.html'>home</a>"
    html += "<ul>"
    html += f"<li><a href='{rel_root}site-map.html'>site-map</a></li>"
    for child in site["children"]:
        html += render_node(child)
    html += "</ul>"
    html += "</li>"
    html += "</ul>"
    return html

def build_root_content(site, rel_root=""):
    """Build content from root index.f file if it exists."""
    root_index = os.path.join(DATA_DIR, "index.f")
    if not os.path.exists(root_index):
        return ""
    
    with open(root_index, "r", encoding="utf-8") as f:
        content_lines = f.read().splitlines()
    
    # Extract and skip frontmatter
    _, content_lines = parse_frontmatter(content_lines)
    
    html_content = "<div class='text'>"
    list_stack = []
    blockquote_open = False
    errors = []
    
    for line in content_lines:
        if len(line) < 3 and not line.startswith("|"):
            continue
        if line.startswith("|"):
            class_name = line[1:].strip()
            if class_name:
                html_content += f"<div class='{class_name}'>"
            else:
                html_content += "</div>"
            continue
        
        prefix, rest = line[0], line[2:]
        
        if prefix in ["1", "2", "3", "4", "5", "6"]:
            heading_id = slugify_heading(rest)
            rest = apply_inline_formatting(rest, site, rel_root, errors)
            html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
            html_content += f"<h{prefix} id='{heading_id}'>{rest}</h{prefix}>"
        elif prefix == ">":
            rest = apply_inline_formatting(rest, site, rel_root, errors)
            if not blockquote_open:
                html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
                html_content += "<blockquote>"
                blockquote_open = True
            html_content += f"<p>{rest}</p>"
        elif prefix in ["*", "#", " "]:
            if blockquote_open:
                html_content += "</blockquote>"
                blockquote_open = False
            html_content = handle_list_or_para(html_content, list_stack, line, site, rel_root, errors)
    
    html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
    html_content += "</div>"
    return html_content

def build_latest_journal_entry(site, rel_root="", run_log=None, habit_log=None):
    journal_node = find_node_by_name(site, "journal")
    if not journal_node or not journal_node["pages"]:
        return "<div class='text'><p>No journal entries found.</p></div>"

    # Filter out index.f files and sort by filename
    journal_pages = [p for p in journal_node["pages"] if os.path.splitext(p["file"])[0] != "index"]
    if not journal_pages:
        return "<div class='text'><p>No journal entries found.</p></div>"
    
    latest_page = sorted(journal_pages, key=lambda p: p["file"], reverse=True)[0]
    src_file = os.path.join(DATA_DIR, journal_node["attrs"]["path"], latest_page["file"])

    with open(src_file, "r", encoding="utf-8") as f:
        content_lines = f.read().splitlines()

    _, content_lines = parse_frontmatter(content_lines)

    errors = []
    entry_title = None
    entry_lines = []
    entry_image = ""
    in_entry = False
    entry_week_key = None

    for line in content_lines:
        if len(line) < 3 and not line.startswith("|"):
            continue
        if line[0] in ["1", "2", "3", "4", "5", "6"]:
            if line[0] == "3":
                if not in_entry:
                    entry_title = apply_inline_formatting(line[2:], site, rel_root)
                    entry_week_key = line[2:].strip()
                    in_entry = True
                    continue
                break
            if in_entry:
                break
        if not in_entry:
            continue
        if line.startswith("%") and not entry_image:
            parts = line[2:].rsplit(" | ", 2)
            if len(parts) == 3:
                caption_raw, cls_raw, img_path_raw = parts
            else:
                parts = line[2:].split("|")
                caption_raw = parts[0] if len(parts) > 0 else ""
                cls_raw = parts[1] if len(parts) > 1 else ""
                img_path_raw = parts[2] if len(parts) > 2 else ""
            caption = caption_raw.strip()
            cls = cls_raw.strip()
            img_path = img_path_raw.strip()
            if not cls:
                cls = "side"
            caption_html = apply_inline_formatting(caption, site, rel_root, errors)
            entry_image = f"<figure class='{cls}'><img src='{rel_root}media/{img_path}' alt='{caption}'><figcaption>{caption_html}</figcaption></figure>"
            continue
        entry_lines.append(line)

    if not entry_title:
        return "<div class='text'><p>No journal entries found.</p></div>"

    html_content = "<div class='text'>"
    html_content += "<h2 id='now'>Now</h2>"
    list_stack = []
    blockquote_open = False
    errors = []

    for line in entry_lines:
        if len(line) < 3 and not line.startswith("|"):
            continue
        prefix, rest = line[0], line[2:]
        rest = apply_inline_formatting(rest, site, rel_root, errors)
        if prefix == ">":
            if not blockquote_open:
                html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
                html_content += "<blockquote>"
                blockquote_open = True
            html_content += f"<p>{rest}</p>"
        elif prefix in ["*", "#", " "]:
            if blockquote_open:
                html_content += "</blockquote>"
                blockquote_open = False
            html_content = handle_list_or_para(html_content, list_stack, line, site, rel_root, errors)

    html_content, list_stack, blockquote_open = close_open_blocks(html_content, list_stack, blockquote_open)
    if run_log and entry_week_key:
        week_runs = run_log.get("runs_by_week", {}).get(entry_week_key)
        if week_runs:
            html_content += build_week_run_table_html(week_runs, run_log.get("unit", RUN_DEFAULT_UNIT))
    if habit_log and entry_week_key:
        week_entries = habit_log.get("habits_by_week", {}).get(entry_week_key)
        if week_entries:
            html_content += build_week_habit_table_html(
                week_entries,
                habit_log.get("habits", []),
                habit_log.get("active_indices", []),
            )
    latest_page_name = os.path.splitext(latest_page["file"])[0]
    html_content += "</div>"
    if entry_image:
        html_content += entry_image
    html_content += "<div class='text'>"
    html_content += f"<p>See my <a href='journal/{latest_page_name}.html'>journal</a> for more.</p>"
    html_content += "</div>"
    return html_content

# Build a nav menu for the index.html page.
# It will list all the child nodes of the root as paras in a div, and for each of these
# nodes it will list the pages in a ul. Where a node has child nodes (i.e. directories), those should at the start of the ul as 'name...' linking to the index.html for that directory
def build_full_nav(site, rel_root="") -> str:
    nav_html = "<nav>" if site else ""
    if not site:
        return nav_html
    for child in site["children"]:
        nav_html += f"<div><h2><a href='{rel_root}{child['attrs']['path']}/index.html'>{child['name'].capitalize()}</a></h2>"
        if child["pages"] or child["children"]:
            nav_html += "<ul>"
            if child["children"]:
                for subchild in child["children"]:
                    nav_html += f"<li><a href='{rel_root}{subchild['attrs']['path']}/index.html'>{subchild['name'].capitalize()}...</a></li>"
            for page_entry in child["pages"]:
                page_file = page_entry["file"]
                page_name = os.path.splitext(page_file)[0]
                page_title = page_entry["metadata"].get("title") or page_name.capitalize()
                nav_html += f"<li><a href='{rel_root}{child['attrs']['path']}/{page_name}.html'>{page_title}</a></li>"
            nav_html += "</ul>"
        nav_html += "</div>"
    nav_html += "</nav>"
    return nav_html


def main():
    site = build_site_tree()
    pretty(site) 

    # track all errors
    all_errors = {} 

    runs, run_errors = parse_running_log(RUN_LOG_PATH, RUN_DEFAULT_UNIT)
    run_log = {
        "runs": runs,
        "runs_by_week": build_runs_by_week(runs),
        "unit": RUN_DEFAULT_UNIT,
    }
    if run_errors:
        all_errors["special/running.log"] = run_errors

    habit_entries, habit_names, habit_active_indices, habit_errors = parse_habits_log(HABIT_LOG_PATH)
    habit_log = {
        "entries": habit_entries,
        "habits": habit_names,
        "active_indices": habit_active_indices,
        "habits_by_week": build_habits_by_week(habit_entries),
    }
    if habit_errors:
        all_errors["special/habits.log"] = habit_errors

    # produce global nav

    # clear output dir
    if os.path.exists(OUTPUT_DIR):
        for root, dir, files in os.walk(OUTPUT_DIR, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for d in dir:
                os.rmdir(os.path.join(root, d))
    else:
        os.mkdir(OUTPUT_DIR)

    COPY_DIRS = ["css", "media"]
    # copy these directories recursvieyl to output dir
    for copy_dir in COPY_DIRS:
        src_dir = os.path.join(DATA_DIR, copy_dir)
        dst_dir = os.path.join(OUTPUT_DIR, copy_dir)
        if os.path.exists(src_dir):
            os.makedirs(dst_dir, exist_ok=True)
            for root, dir, files in os.walk(src_dir):
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dst_dir, os.path.relpath(src_file, src_dir))
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    with open(src_file, "rb") as f_src:
                        with open(dst_file, "wb") as f_dst:
                            f_dst.write(f_src.read())

    cname_src = os.path.join(DATA_DIR, "CNAME")
    cname_dst = os.path.join(OUTPUT_DIR, "CNAME")
    if os.path.exists(cname_src):
        with open(cname_src, "rb") as f_src:
            with open(cname_dst, "wb") as f_dst:
                f_dst.write(f_src.read())


    # create index.html
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        rel_root = rel_root_for(index_path)
        root_metadata = get_page_metadata(os.path.join(DATA_DIR, "index.f"))
        root_title = root_metadata.get("title") or "Home"
        f.write(html_header(root_title, rel_root, "default.css", site))
        local_nav = build_local_nav(site, site, rel_root)
        root_title_id = slugify_heading(root_title)
        f.write(f"<div class='page-header'>{local_nav}<h1 class='page-title' id='{root_title_id}'>{root_title}</h1></div>")
        f.write(layout_open(rel_root))
        f.write(build_root_content(site, rel_root))
        f.write(build_latest_journal_entry(site, rel_root, run_log, habit_log))
        f.write(html_footer(rel_root))

    # create site-map.html
    site_map_path = os.path.join(OUTPUT_DIR, "site-map.html")
    with open(site_map_path, "w", encoding="utf-8") as f:
        rel_root = rel_root_for(site_map_path)
        f.write(html_header("site-map", rel_root, "default.css", site))
        local_nav = build_local_nav(site, site, rel_root)
        f.write(f"<div class='page-header'>{local_nav}<h1 class='page-title' id='site-map'>site-map</h1></div>")
        f.write(layout_open(rel_root))
        f.write("<div class='text'>")
        f.write(build_site_map(site, rel_root))
        f.write("</div>")
        f.write(html_footer(rel_root))

    # for each node in site, create a directory, and for each page then call create_page() to produce a html file
    for n in walk(site):
        if n["name"] != "index":  # skip the root node
            # use the path attribute to create the directory structure in the output dir
            dir_path = os.path.join(OUTPUT_DIR, n["attrs"]["path"])
            os.makedirs(dir_path, exist_ok=True)
            
            # Check if there's a page named index.f (e.g., index.f in about/)
            # If so, use it as the index.html instead of auto-generating
            dir_index_page = None
            for page_entry in n["pages"]:
                page_name = os.path.splitext(page_entry["file"])[0]
                if page_name == "index":
                    dir_index_page = page_entry
                    break
            
            if dir_index_page:
                # Use the index.f file as the index.html
                src_file = os.path.join(DATA_DIR, n["attrs"]["path"], dir_index_page["file"])
                index_path = os.path.join(dir_path, "index.html")
                errors = create_page(src_file, index_path, rel_root_for(index_path), site, run_log, habit_log)
                if errors:
                    pretty_path = os.path.join(n["attrs"]["path"], dir_index_page["file"])
                    all_errors[pretty_path] = errors
            else:
                # Auto-generate index.html
                index_path = os.path.join(dir_path, "index.html")
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(html_header(n["name"].capitalize(), rel_root_for(index_path), "default.css", site))
                    local_nav = build_local_nav(site, n, rel_root_for(index_path))
                    title = n["name"].capitalize()
                    title_id = slugify_heading(title)
                    f.write(f"<div class='page-header'>{local_nav}<h1 class='page-title' id='{title_id}'>{title}</h1></div>")
                    f.write(layout_open(rel_root_for(index_path)))
                    f.write("<div class='text'>")
                    if n["children"]:
                        f.write("<h2>Subsections</h2>")
                        f.write("<ul>")
                        sorted_children = sort_with_order(n["children"])
                        for child in sorted_children:
                            f.write(f'<li><a href="{child["name"]}/index.html">{child["name"].capitalize()}</a></li>')
                        f.write("</ul>")
                    if n["pages"]:
                        f.write("<h2>Pages</h2>")
                        f.write("<ul>")
                        sorted_pages = sort_with_order(n["pages"])
                        for page_entry in sorted_pages:
                            page_file = page_entry["file"]
                            page_name = os.path.splitext(page_file)[0]
                            # Skip index.f since it's used as the directory's main content
                            if page_name == "index":
                                continue
                            page_title = page_entry["metadata"].get("title") or page_name.capitalize()
                            f.write(f'<li><a href="{page_name}.html">{page_title}</a></li>')
                        f.write("</ul>")
                    f.write("</div>")
                    f.write(html_footer(rel_root_for(index_path)))

            # Create pages for all entries in the directory (except index.f if it was used as index.html)
            for page_entry in n["pages"]:
                page_file = page_entry["file"]
                page_name = os.path.splitext(page_file)[0]
                # Skip if this is the index.f file (already used as index.html)
                if dir_index_page and page_name == "index":
                    continue
                src_file = os.path.join(DATA_DIR, n["attrs"]["path"], page_file)
                output_file = os.path.join(dir_path, os.path.splitext(page_file)[0] + ".html")
                errors = create_page(src_file, output_file, rel_root_for(output_file), site, run_log, habit_log)
                if errors:
                    pretty_path = os.path.join(n["attrs"]["path"], page_file)
                    all_errors[pretty_path] = errors
    
    # print error log
    if all_errors:
        print("\n" + "="*60)
        print("ERRORS FOUND DURING PAGE GENERATION")
        print("="*60)
        for page_path, errors in all_errors.items():
            print(f"\n[{page_path}]")
            for error in errors:
                print(f"  - {error}")
    else:
        print("All pages generated successfully with no errors")

if __name__ == "__main__":
    main()