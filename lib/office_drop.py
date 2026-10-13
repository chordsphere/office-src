#!/usr/bin/env python3
"""The in-tray: office drop's pages, the space they arrive in, and the
readers office start, the desk and office status share (0.19.0).

A drop is one message or thread, captured instant and dumb (doctrine
principle 1) as one page, in-tray/DATE-SLUG.md. Its shape is pinned,
because two writers and one reader build against it (office drop writes
it, office start --drop moves it into a folder, and the next release's
office moves and office land read every key):

    # Drop: <the first line of the text, trimmed to 60 characters>

    - dropped: 2026-10-14 09:12
    - project: alpha
    - via: clipboard
    - status: unsorted

    ## Text

    <the text, verbatim>

`project` is the free text as given, or `none given`; `via` is
`clipboard`, `stdin` or `file NAME` (the basename); `status` is
`unsorted` when the drop lands and `sorted` once a Sort has been filed
under it. The field lines are the office command's, never written by
hand: render_page writes them, and set_status is the one writer of the
status line after that (0.20.0). The page stays ASCII: anything outside
it is kept as a backslash escape, as office note keeps it.

Once office land files a session's Sort for the drop (lib/office_sort.py,
0.20.0), the page ends with a `## Sort` section whose first line is
`- sorted: DATE, by SID`; the text under `## Text` stops above it.

The in-tray arrives with the first drop, the way the drafting table
arrives with the first verb that writes it (doctrine section 5): its
front page from the install's template, the floor plan's entry as the
install's catalog declares it, and bale.toml's include-group trigger,
through the drafting table's own arrival code. Nothing already there is
rewritten. Its pages are live, never hung and never filed: a sorted drop
leaves the in-tray whole.

Standard library only. The command line prints on stdout, logs to stderr
with an [office] prefix, and exits 0 on success, 1 on a refusal, 2 on an
internal error, and 3 when a check found problems (the lines say which).
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_drafting as od  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = INSTALL / "templates"
SPACE = "in-tray"
FRONT_PAGE = "README.md"
FRONT_TEMPLATE = "in-tray-README.md"
BRIEF_TEMPLATE = "drop-brief.md"
MANIFEST_REL = "floor-plan/manifest.toml"
BALE_TOML_REL = "bale.toml"

HEADING_PREFIX = "# Drop: "
HEADING_LIMIT = 60
FIELDS = ("dropped", "project", "via", "status")
NO_PROJECT = "none given"
STATUSES = ("unsorted", "sorted")
TEXT_HEADING = "## Text"
VIA_RE = re.compile(r"^(clipboard|stdin|file \S.*)$")
DROPPED_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})$")
PAGE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
FIELD_RE = re.compile(r"^- ([a-z]+): (.*)$")
# The section office land appends when it files a Sort (0.20.0): its
# first line names the day and the session.
SORT_HEADING = "## Sort"
SORTED_LINE_RE = re.compile(r"^- sorted: (\d{4}-\d{2}-\d{2}), by (\S+)$")

# The lines a drop's page sits between in the brief office start --drop
# writes: notepad-style markers, but their own, so office start never
# files a drop in the notepad (NOTEPAD PAGE markers are filed).
DROP_BEGIN = "--- DROP BEGIN {page} ---"
DROP_END = "--- DROP END ---"

# The direct path's goal: one sentence, no backticks (bale's goal is a
# shell word and the opener's first line).
DROP_GOAL = "Sort the dropped message and do what it asks"


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- the page --------------------------------------------------------------------

def normalize_text(text):
    """The text as a drop keeps it: line ends made LF (a Windows
    clipboard hands over CRLF), and the blank lines and spaces at its
    very end dropped. Everything else is kept as given."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.rstrip()


def first_line(text):
    """The text's first line with words on it, its runs of space made one."""
    for line in text.splitlines():
        if line.strip():
            return " ".join(line.split())
    return ""


def heading_text(text, limit=HEADING_LIMIT):
    """A drop's heading: the first line, trimmed to `limit` characters,
    cut at a word and marked with ... when it is longer."""
    line = first_line(text)
    if len(line) <= limit:
        return line
    cut = line[:limit - 3].rstrip()
    if " " in cut[limit // 2:]:
        cut = cut[:cut.rindex(" ")].rstrip()
    return cut + "..."


def render_page(text, project, via, dropped, status="unsorted"):
    """(page, escaped): the drop's page, every byte ASCII, and how many
    characters were kept as escapes. Raises HelperError for what no page
    can hold: an empty text, a via or a stamp that is not one."""
    text = normalize_text(text)
    if not text.strip():
        raise oh.HelperError("nothing to drop: the text is empty")
    if not VIA_RE.match(via or ""):
        raise oh.HelperError(f"via is clipboard, stdin or file NAME, not {via!r}")
    if not DROPPED_RE.match(dropped or ""):
        raise oh.HelperError(f"dropped is YYYY-MM-DD HH:MM, not {dropped!r}")
    if status not in STATUSES:
        raise oh.HelperError(f"status is one of {', '.join(STATUSES)}, not {status!r}")
    project = " ".join((project or "").split()) or NO_PROJECT
    # Trimmed first, escaped after: the 60 are the text's characters. The
    # heading repeats the text's first line, so its escapes are not
    # counted again.
    head = oh.ascii_escape(heading_text(text))[0]
    project, n_project = oh.ascii_escape(project)
    via, n_via = oh.ascii_escape(via)
    body, n_body = oh.ascii_escape(text)
    escaped = n_project + n_via + n_body
    page = "\n".join([f"{HEADING_PREFIX}{head}", "",
                      f"- dropped: {dropped}", f"- project: {project}", f"- via: {via}", f"- status: {status}",
                      "", TEXT_HEADING, "", body]) + "\n"
    return page, escaped


def parse_page(text):
    """Everything a reader takes from a drop's page: heading, the four
    fields, the text under ## Text, and the problems (lines that do not
    read). A page with problems is still returned, so the desk and
    office status can name it."""
    lines = text.splitlines()
    out = {"heading": None, "fields": {}, "text": None, "problems": []}
    if not lines or not lines[0].startswith(HEADING_PREFIX):
        out["problems"].append(f"its first line is not '{HEADING_PREFIX.strip()} ...'")
    else:
        out["heading"] = lines[0][len(HEADING_PREFIX):]
    i = 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and lines[i].startswith("- "):
        m = FIELD_RE.match(lines[i])
        if m and m.group(1) in FIELDS and m.group(1) not in out["fields"]:
            out["fields"][m.group(1)] = m.group(2)
        else:
            out["problems"].append(f"line {i + 1} is not one of its field lines: {lines[i]!r}")
        i += 1
    for key in FIELDS:
        if key not in out["fields"]:
            out["problems"].append(f"it has no {key} line")
    f = out["fields"]
    if "dropped" in f and not DROPPED_RE.match(f["dropped"]):
        out["problems"].append(f"dropped is not YYYY-MM-DD HH:MM: {f['dropped']!r}")
    if "status" in f and f["status"] not in STATUSES:
        out["problems"].append(f"status is not {' or '.join(STATUSES)}: {f['status']!r}")
    if "via" in f and not VIA_RE.match(f["via"]):
        out["problems"].append(f"via is not clipboard, stdin or file NAME: {f['via']!r}")
    out["sort_lines"] = None
    try:
        at = lines.index(TEXT_HEADING, i)
    except ValueError:
        out["problems"].append(f"it has no '{TEXT_HEADING}' section")
        return out
    end = sort_start(lines, at + 1)
    if end is not None:
        out["sort_lines"] = lines[end + 1:]
    out["text"] = "\n".join(lines[at + 1:end]).strip("\n")
    if f.get("status") == "sorted" and end is None:
        out["problems"].append(f"it says status sorted, and no '{SORT_HEADING}' section says by whom")
    return out


def sort_start(lines, start=0):
    """The index of the page's filed Sort section, `## Sort` with its
    `- sorted: DATE, by SID` line, at or after start; None when the page
    has none. The last such heading counts, so a thread that quotes a
    `## Sort` line of its own keeps it in its text."""
    found = None
    for i in range(start, len(lines)):
        if lines[i] != SORT_HEADING:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and SORTED_LINE_RE.match(lines[j]):
            found = i
    return found


def set_status(path, status):
    """The one writer of a drop's status line after render_page: the page
    with its `- status:` line set, every other byte kept. Returns the
    status it had. Raises HelperError for a page whose field lines do not
    read, or a status that is not one."""
    if status not in STATUSES:
        raise oh.HelperError(f"status is one of {', '.join(STATUSES)}, not {status!r}")
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("## "):
            break
        m = FIELD_RE.match(line)
        if m and m.group(1) == "status":
            lines[i] = f"- status: {status}"
            path.write_text("\n".join(lines), encoding="ascii")
            return m.group(2)
    raise oh.HelperError(f"{path.name} has no status line above its first section")


def project_text(fields):
    """The drop's project as given, or None for `none given`."""
    p = (fields.get("project") or "").strip()
    return None if not p or p == NO_PROJECT else p


def resolve_project(text, names):
    """The floor plan's project a drop's free text names, or None. It
    names one when it is the project's name, in any case, alone or
    before a colon (as a lane writes it, `alpha: src/`)."""
    if not text:
        return None
    names = list(names)
    for candidate in (text.strip(), text.split(":", 1)[0].strip()):
        if candidate in names:
            return candidate
        low = [n for n in names if n.lower() == candidate.lower()]
        if len(low) == 1:
            return low[0]
    return None


# --- the in-tray -----------------------------------------------------------------

def free_name(root, day, slug):
    """in-tray/DATE-SLUG.md, with -2, -3 ... when the name is taken."""
    slug = slug or "drop"
    base = f"{SPACE}/{day}-{slug}"
    rel, n = f"{base}.md", 1
    while (pathlib.Path(root) / rel).exists():
        n += 1
        rel = f"{base}-{n}.md"
    return rel


def arrive(root):
    """Make the in-tray arrive, or finish arriving: its front page, the
    floor plan's entry and bale.toml's trigger, each only when missing.
    Returns (changed paths, words for the log)."""
    root = pathlib.Path(root)
    entry = od.catalog_entry(space=SPACE)
    changed, words = [], []
    (root / SPACE).mkdir(exist_ok=True)
    front = root / SPACE / FRONT_PAGE
    if not front.exists():
        front.write_text((TEMPLATES / FRONT_TEMPLATE).read_text(encoding="utf-8"), encoding="utf-8")
        changed.append(f"{SPACE}/{FRONT_PAGE}")
        words.append(f"the in-tray arrives in this office: made {SPACE}/{FRONT_PAGE} from the install's template")
    if od.add_space_to_floor_plan(root / MANIFEST_REL, entry, SPACE):
        changed.append(MANIFEST_REL)
        words.append(f"the floor plan now lists the {SPACE} space, as the install's catalog declares it")
    added = od.add_include_trigger(root / BALE_TOML_REL, entry["path"])
    if added:
        changed.append(BALE_TOML_REL)
        words.append(f"bale.toml's include group now triggers on {entry['path']}")
    elif added is None:
        words.append(f"bale.toml has no include group to add {entry['path']} to (office status says so)")
    return changed, words


def write_drop(root, text, project, via, day, time, slug):
    """Write one drop: the in-tray arrives first when it must, then the
    page under a free name. Returns (page path, arrival's changed paths,
    words for the log). Never refuses a text it can write."""
    root = pathlib.Path(root)
    page, escaped = render_page(text, project, via, f"{day} {time}")
    changed, words = arrive(root)
    rel = free_name(root, day, slug)
    (root / rel).write_text(page, encoding="ascii")
    if escaped:
        words.append(f"{escaped} character(s) outside ASCII kept as backslash escapes")
    return rel, changed, words


def read_drop(root, rel):
    """One drop as the readers see it: name, rel, its parsed fields."""
    path = pathlib.Path(root) / rel
    try:
        parsed = parse_page(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        parsed = {"heading": None, "fields": {}, "text": None, "problems": [f"it cannot be read: {exc}"]}
    f = parsed["fields"]
    return {"name": path.name, "rel": rel, "heading": parsed["heading"] or "",
            "project": project_text(f), "via": f.get("via"), "status": f.get("status"),
            "dropped": f.get("dropped"), "problems": parsed["problems"]}


def drops(root):
    """Every page in the in-tray (its front page aside), oldest first:
    by the dropped stamp, then by name; a page whose stamp does not read
    sorts last."""
    tray = pathlib.Path(root) / SPACE
    if not tray.is_dir():
        return []
    out = [read_drop(root, f"{SPACE}/{p.name}") for p in sorted(tray.glob("*.md"))
           if p.is_file() and p.name != FRONT_PAGE]
    return sorted(out, key=lambda d: (d["dropped"] is None or not DROPPED_RE.match(d["dropped"] or ""),
                                      d["dropped"] or "", d["name"]))


def unsorted(root):
    """The drops office start carries: status unsorted, and readable."""
    return [d for d in drops(root) if d["status"] == "unsorted" and not d["problems"]]


def sorted_waiting(root):
    """The sorted drops still in the in-tray, oldest first: each is a desk
    move office moves applies (0.20.0), and the walk-in counts them as
    pending moves."""
    return [d for d in drops(root) if d["status"] == "sorted"]


def age_days(drop, today):
    """Whole days since the drop, by the office's calendar; None when its
    stamp does not read."""
    m = DROPPED_RE.match(drop.get("dropped") or "")
    if not m:
        return None
    return (dt.date.fromisoformat(today) - dt.date.fromisoformat(m.group(1))).days


def resolve_page(root, want, folder=None):
    """The page office start --drop names: in the in-tray by its path
    (in-tray/NAME.md) or its name (with or without .md); with a folder,
    in that folder's drops/ instead (a start that is retried after the
    page moved). Returns the page's path relative to the office root;
    raises HelperError naming where it looked."""
    root = pathlib.Path(root)
    want = (want or "").strip()
    if not want:
        raise oh.HelperError("--drop needs the drop's page: in-tray/NAME.md, or its name")
    name = pathlib.PurePosixPath(want).name
    if not name.endswith(".md"):
        name += ".md"
    if folder:
        rel = f"{folder}/drops/{name}"
        if (root / rel).is_file():
            return rel
        raise oh.HelperError(f"{folder}/drops/ has no {name}")
    rel = f"{SPACE}/{name}"
    if (root / rel).is_file() and name != FRONT_PAGE:
        return rel
    raise oh.HelperError(f"the in-tray has no {name} (office desk lists the unsorted drops)")


def tray_check(root):
    """(lines, problems) for office status: an in-tray that exists, against
    the install's catalog and the page shape; none, said so."""
    root = pathlib.Path(root)
    entry = od.catalog_entry(space=SPACE)
    manifest = oh.read_toml(root / MANIFEST_REL)
    listed = manifest.get("spaces", {}).get(SPACE)
    here = (root / SPACE).is_dir()
    if not here and listed is None:
        return ["in-tray:    none in this office; it arrives with the first office drop"], 0
    problems = []
    if here and listed is None:
        problems.append(f"{SPACE}/ exists but the floor plan does not list it; the next office drop adds it")
    if listed is not None:
        for key in ("path", "hung", "filed"):
            want = entry.get(key, False)
            if listed.get(key, False) != want:
                problems.append(f"the floor plan's {SPACE} {key} is {listed.get(key)!r}; the install's catalog "
                                f"says {want!r}")
        if not here:
            problems.append(f"the floor plan lists {SPACE} but there is no {SPACE}/ directory")
    if here and not (root / SPACE / FRONT_PAGE).is_file():
        problems.append(f"{SPACE}/{FRONT_PAGE} is missing; the next office drop makes it")
    every = drops(root) if here else []
    if here:
        for p in sorted((root / SPACE).iterdir()):
            if p.is_dir():
                problems.append(f"{SPACE}/{p.name}/ is not a page: the in-tray holds one page per drop")
            elif p.suffix != ".md":
                problems.append(f"{SPACE}/{p.name} is not a drop's page")
            elif p.name != FRONT_PAGE and not PAGE_NAME_RE.match(p.name):
                problems.append(f"{SPACE}/{p.name} is not named DATE-SLUG.md, as office drop names a drop")
        for d in every:
            for why in d["problems"]:
                problems.append(f"{d['rel']}: {why}")
    if problems:
        return [f"in-tray:    {len(problems)} problem(s) against the install's catalog and the drop's page:"] + \
            [f"  {p}" for p in problems], len(problems)
    waiting = [d for d in every if d["status"] == "unsorted"]
    return [f"in-tray:    matches the install's catalog; {len(waiting)} unsorted drop(s)"], 0


# --- what office start does with them ------------------------------------------------

def carried_words(names, place):
    """The out tray's line for the drops that ride, and where."""
    n = len(names)
    shown = ", ".join(names[:5]) + (f" and {n - 5} more" if n > 5 else "")
    return (f"({n} unsorted drop(s) from the in-tray ride {place}: {shown}; doctrine section 4 says what a "
            "session owes them)")


def opener_line(count, sitting=False):
    """The line office start adds to the opener when drops ride."""
    if sitting:
        return (f"{count} unsorted drop(s) from the office's in-tray ride with this sitting: read them; a sitting "
                "owes them no Sort (doctrine section 4).")
    return (f"{count} unsorted drop(s) from the office's in-tray ride with this session: read them before the work, "
            "and sort the ones you can judge in a Sort section of notes.md (doctrine section 4).")


def render_brief(root, folder, page_rel, number, title, project):
    """The brief office start --drop sends with the session: the standing
    sort instructions, the drop's page between its marker lines, and the
    Sort format, from the install's template."""
    root = pathlib.Path(root)
    page = (root / page_rel).read_text(encoding="utf-8").rstrip("\n")
    for line in page.splitlines():
        if line == DROP_END or line.startswith("--- DROP BEGIN "):
            raise oh.HelperError(f"{page_rel} holds a line that is the brief's own marker ({line!r}); the brief "
                                 "cannot carry it between its markers")
    template = (TEMPLATES / BRIEF_TEMPLATE).read_text(encoding="utf-8")
    page_in_folder = page_rel[len(folder) + 1:] if page_rel.startswith(folder + "/") else page_rel
    return oh.render_template(template, {
        "title": title, "number": str(number), "project": project, "folder": folder,
        "page": page_in_folder, "name": pathlib.PurePosixPath(page_rel).name,
        "begin": DROP_BEGIN.format(page=page_in_folder), "end": DROP_END, "drop": page,
    })


# --- the command line ---------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(prog="office_drop.py", description="the in-tray and office drop's pages")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("write", help="write one drop from --text-file; prints the page, then each changed path")
    s.add_argument("root"); s.add_argument("--text-file", required=True)
    s.add_argument("--project", default=""); s.add_argument("--via", required=True)
    s.add_argument("--day", required=True); s.add_argument("--time", required=True)
    s.add_argument("--slug", default="drop")
    s = sub.add_parser("took", help="what a text holds: LINES<tab>FIRST LINE")
    s.add_argument("--text-file", required=True)
    s = sub.add_parser("list", help="the drops: one JSON object per line, oldest first")
    s.add_argument("root"); s.add_argument("--unsorted", action="store_true")
    s = sub.add_parser("facts", help="one drop's page: KEY<tab>VALUE lines (rel, heading, project, via, status, "
                                     "dropped, resolved)")
    s.add_argument("root"); s.add_argument("page"); s.add_argument("--folder")
    s.add_argument("--projects", default="", help="the floor plan's project names, one per line")
    s = sub.add_parser("resolve-project", help="the project a free text names, or nothing (exit 3)")
    s.add_argument("text"); s.add_argument("--projects", default="")
    s = sub.add_parser("brief", help="the brief office start --drop sends")
    s.add_argument("root"); s.add_argument("folder"); s.add_argument("page")
    s.add_argument("--number", required=True); s.add_argument("--title", required=True)
    s.add_argument("--project", required=True)
    s = sub.add_parser("tray-check", help="office status's in-tray line")
    s.add_argument("root")
    a = p.parse_args(argv)
    try:
        if a.cmd == "write":
            raw = pathlib.Path(a.text_file).read_bytes().decode("utf-8", "surrogateescape")
            rel, changed, words = write_drop(a.root, raw, a.project, a.via, a.day, a.time, a.slug)
            for w in words:
                log(w)
            print(rel)
            for c in changed:
                print(c)
            return 0
        if a.cmd == "took":
            raw = normalize_text(pathlib.Path(a.text_file).read_bytes().decode("utf-8", "surrogateescape"))
            if not raw.strip():
                log("error: nothing to drop: the text is empty")
                return 1
            print(f"{len(raw.splitlines())}\t{oh.ascii_escape(first_line(raw))[0]}")
            return 0
        if a.cmd == "list":
            for d in (unsorted(a.root) if a.unsorted else drops(a.root)):
                print(json.dumps(d))
            return 0
        if a.cmd == "facts":
            rel = resolve_page(a.root, a.page, a.folder)
            d = read_drop(a.root, rel)
            if d["problems"]:
                for why in d["problems"]:
                    log(f"error: {rel}: {why}")
                log(f"error: {rel} does not read as a drop's page, so it is not sent out (office status names it)")
                return 1
            names = [n for n in a.projects.splitlines() if n.strip()]
            for key in ("rel", "heading", "via", "status", "dropped"):
                print(f"{key}\t{d[key]}")
            print(f"project\t{d['project'] or ''}")
            print(f"resolved\t{resolve_project(d['project'], names) or ''}")
            return 0
        if a.cmd == "resolve-project":
            found = resolve_project(a.text, [n for n in a.projects.splitlines() if n.strip()])
            if found is None:
                return 3
            print(found)
            return 0
        if a.cmd == "brief":
            sys.stdout.write(render_brief(a.root, a.folder, a.page, a.number, a.title, a.project))
            return 0
        if a.cmd == "tray-check":
            lines, problems = tray_check(a.root)
            print("\n".join(lines))
            return 3 if problems else 0
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, UnicodeDecodeError) as exc:
        log(f"error: {exc}")
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
