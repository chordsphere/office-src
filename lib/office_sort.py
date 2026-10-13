#!/usr/bin/env python3
"""The return of a sort (0.20.0): what office land files from a session's
notes.md beyond the folder's two pages, the moves a sorted drop asks for,
the handbook, and the standalone sort session's brief.

A session never writes the office (doctrine section 4): it writes three
more sections in its notes.md, each only when it has something to say,
and office land files them after an applied landing, in this order:

- `## Sort`: one `### DATE-SLUG.md` subsection per drop, in the format the
  doctrine pins (project, folder, goal, size, tell, facts, and a
  `#### Brief`). The drop's page (in the in-tray, or the landed folder's
  drops/) gains a `## Sort` section at its end, whose first line is the
  office's (`- sorted: DATE, by SID`) and whose fields are the
  subsection's, verbatim and in its order, with `### Brief` exactly when
  the subsection had `#### Brief`; its status line becomes `sorted`,
  through office_drop.set_status, the one writer of that line.
- `## Questions and answers`: `- DATE question? answer` lines, the
  session's record of its light blocks and the occupant's replies,
  appended to the folder's Questions and answers section after a line
  naming the session.
- `## Handbook`: one `### PROJECT` subsection per project, `- ` fact
  lines and optionally a `#### Front sheet`; each fact is appended to the
  chapter's Facts as `- DATE: fact (SID)`, and a front sheet replaces the
  chapter's whole. A Sort's `facts:` lines go to its project's chapter the
  same way. The handbook arrives with the first landing that files a fact.

A sorted drop still in the in-tray is a desk move: office moves applies it
(bin/office), minting a folder through office open's own code for
`folder: new`, or moving the page into folder N, with this module's
`place` step doing the rest: the page into the folder's drops/, the
folder's brief.md from the Sort's Brief, the History line, the goal when
the folder has none, and the Sort's `tell:` on the folder's Next.

notes.md is read fence-aware: a heading inside a fenced block (an example
of the format, say) is never taken for a section.

Standard library only. The command line prints on stdout, logs to stderr
with an [office] prefix, and exits 0 on success, 1 on a refusal, 2 on an
internal error, and 3 when a check found problems (the lines say which).
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_drafting as od  # noqa: E402
import office_drop as odrop  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = INSTALL / "templates"
MANIFEST_REL = "floor-plan/manifest.toml"
BALE_TOML_REL = "bale.toml"

# The standalone sort (office start --sort): an office session that
# belongs to no folder, known by its slug, so the walk-in, the desk and
# office land can tell it from any other session open in the office.
SORT_SLUG = "in-tray-sort"
SORT_GOAL = "Sort the in-tray's drops"
SORT_SID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-" + re.escape(SORT_SLUG) + r"-\d{3}$")
SORT_BRIEF_TEMPLATE = "sort-brief.md"

SORT_FIELDS = ("project", "folder", "goal", "size", "tell", "facts")
SORT_KEY_RE = re.compile(r"^- ([a-z]+):(?: (.*))?$")
QA_LINE_RE = re.compile(r"^- \d{4}-\d{2}-\d{2} \S.*$")
HEADING_RE = re.compile(r"^(#{1,6}) (.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")

HANDBOOK = "handbook"
HANDBOOK_FRONT = "README.md"
HANDBOOK_FRONT_TEMPLATE = "handbook-README.md"
CHAPTER_TEMPLATE = "handbook-chapter.md"
FACT_LINE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}): (.+) \((\S+)\)$")
CHAPTER_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*\.md$")


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


def is_sort_sid(sid):
    """Whether a session id is a standalone sort's (office start --sort)."""
    return bool(SORT_SID_RE.match(sid or ""))


# --- notes.md, read fence-aware ------------------------------------------------------

def fenced(lines):
    """[bool] per line: inside a fenced block (the fence lines included)."""
    out, inside = [], False
    for line in lines:
        if FENCE_RE.match(line):
            out.append(True)
            inside = not inside
            continue
        out.append(inside)
    return out


def headings(lines, start=0, end=None):
    """[(index, level, title)] of the headings outside fenced blocks."""
    end = len(lines) if end is None else end
    inside = fenced(lines)
    out = []
    for i in range(start, end):
        if inside[i]:
            continue
        m = HEADING_RE.match(lines[i])
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def subsections(lines, level, start=0, end=None):
    """[(title, body lines)] for each heading of exactly `level` between
    start and end, its body running to the next heading of that level or
    above."""
    end = len(lines) if end is None else end
    heads = [h for h in headings(lines, start, end) if h[1] <= level]
    out = []
    for n, (i, lv, title) in enumerate(heads):
        if lv != level:
            continue
        stop = heads[n + 1][0] if n + 1 < len(heads) else end
        out.append((title, lines[i + 1:stop]))
    return out


def section(lines, title, level=2):
    """The body lines of the first `level` heading named title, or None."""
    for t, body in subsections(lines, level):
        if t == title:
            return body
    return None


def trimmed(lines):
    """lines without their leading and trailing blank lines."""
    lines = list(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def parse_sort(name, body, brief_level=4):
    """One `### NAME.md` subsection as a dict: name, field_lines (verbatim),
    fields, facts, brief (lines, or None), problems. A subsection with
    problems is said and never filed: the office reads this format, so it
    is kept to the byte (doctrine section 4). brief_level is the Brief's
    heading level: 4 in notes.md, 3 on a drop's page, where page_sort
    reads it back with name None."""
    out = {"name": name, "field_lines": [], "fields": {}, "facts": [], "brief": None, "problems": [],
           "ignored": 0}
    if name is not None and not odrop.PAGE_NAME_RE.match(name):
        out["problems"].append(f"### {name} does not name a drop's page (DATE-SLUG.md)")
    brief_at = next((i for i, lv, t in headings(body) if lv == brief_level and t == "Brief"), None)
    head = body[:brief_at] if brief_at is not None else body
    if brief_at is not None:
        out["brief"] = trimmed(body[brief_at + 1:])
        if not out["brief"]:
            out["problems"].append("its #### Brief is empty")
    i = 0
    while i < len(head) and not head[i].strip():
        i += 1
    while i < len(head) and head[i].startswith("- "):
        out["field_lines"].append(head[i])
        i += 1
    out["ignored"] = sum(1 for line in head[i:] if line.strip())
    keys = []
    for line in out["field_lines"]:
        if len(keys) == len(SORT_FIELDS):
            out["facts"].append(line[2:].strip())  # after facts:, a line is a fact
            continue
        m = SORT_KEY_RE.match(line)
        if not m:
            break
        keys.append(m.group(1))
        out["fields"][m.group(1)] = (m.group(2) or "").strip()
    if tuple(keys) != SORT_FIELDS:
        out["problems"].append(f"its field lines are not {', '.join(SORT_FIELDS)}, one each and in that order")
        return out
    f = out["fields"]
    for key in ("project", "goal", "size", "tell"):
        if not f[key]:
            out["problems"].append(f"its {key}: line is empty")
    folder = folder_ref(f["folder"])
    if folder is None:
        out["problems"].append(f"folder: is new or a folder number, not {f['folder']!r}")
    elif folder == "new" and out["brief"] is None:
        out["problems"].append(f"folder: new needs a {'#' * brief_level} Brief, the new folder's brief")
    facts = f["facts"]
    if facts == "none":
        if out["facts"]:
            out["problems"].append("facts: says none, and fact lines follow it")
    elif facts:
        out["facts"].insert(0, facts[2:].strip() if facts.startswith("- ") else facts)
    elif not out["facts"]:
        out["problems"].append("facts: is none or fact lines, each starting with - ")
    return out


def folder_ref(value):
    """`new`, a folder number (int) from `N` or `folder N`, or None."""
    text = " ".join((value or "").split()).lower()
    if text == "new":
        return "new"
    m = re.fullmatch(r"(?:folder )?(\d+)", text)
    return int(m.group(1)) if m else None


def parse_handbook(body):
    """[(project, facts, front lines or None)] from a Handbook section."""
    out = []
    for project, sub in subsections(body, 3):
        front_at = next((i for i, lv, t in headings(sub) if lv == 4 and t == "Front sheet"), None)
        head = sub[:front_at] if front_at is not None else sub
        inside = fenced(head)
        facts = [line[2:].strip() for n, line in enumerate(head) if line.startswith("- ") and not inside[n]]
        front = trimmed(sub[front_at + 1:]) if front_at is not None else None
        out.append((project.strip(), [f for f in facts if f], front or None))
    return out


def parse_notes(text):
    """What office land files from a notes.md: {sorts, qa, qa_other,
    handbook}, each None when the notes carry no such section."""
    lines = text.splitlines()
    out = {"sorts": None, "qa": None, "qa_other": 0, "handbook": None}
    body = section(lines, "Sort")
    if body is not None:
        out["sorts"] = [parse_sort(name.strip(), sub) for name, sub in subsections(body, 3)]
    body = section(lines, "Questions and answers")
    if body is not None:
        inside = fenced(body)
        out["qa"] = [line.rstrip() for n, line in enumerate(body) if not inside[n] and QA_LINE_RE.match(line)]
        out["qa_other"] = sum(1 for n, line in enumerate(body)
                              if line.strip() and not inside[n] and not QA_LINE_RE.match(line))
    body = section(lines, "Handbook")
    if body is not None:
        out["handbook"] = parse_handbook(body)
    return out


# --- a drop's page gains its Sort ----------------------------------------------------

def sort_section(sort, sid, day):
    """The lines office land appends to a drop's page: the office's first
    line, then the subsection's fields verbatim, then its Brief."""
    lines = [odrop.SORT_HEADING, "", f"- sorted: {day}, by {sid}", *sort["field_lines"]]
    if sort["brief"] is not None:
        lines += ["", "### Brief", "", *sort["brief"]]
    return lines


def page_sort(sort_lines):
    """A filed Sort section read back (the lines after `## Sort`): sid,
    day, fields, brief (lines or None), problems."""
    lines = trimmed(sort_lines or [])
    out = {"sid": None, "day": None, "fields": {}, "facts": [], "brief": None, "problems": []}
    if not lines or not odrop.SORTED_LINE_RE.match(lines[0]):
        out["problems"].append("its Sort section does not open with `- sorted: DATE, by SID`")
        return out
    m = odrop.SORTED_LINE_RE.match(lines[0])
    out["day"], out["sid"] = m.group(1), m.group(2)
    parsed = parse_sort(None, lines[1:], brief_level=3)
    for key in ("fields", "facts", "brief", "problems"):
        out[key] = parsed[key]
    return out


def find_page(root, name, folder=None):
    """A drop's page by name: in the in-tray, or in the landed folder's
    drops/ (space/name); its path relative to the office, or None."""
    root = pathlib.Path(root)
    for rel in [f"{odrop.SPACE}/{name}"] + ([f"{folder}/drops/{name}"] if folder else []):
        if (root / rel).is_file() and pathlib.PurePosixPath(rel).name != odrop.FRONT_PAGE:
            return rel
    return None


def file_sort(root, sort, sid, day, folder=None):
    """File one Sort subsection on its page. Returns (state, rel, words):
    state is filed, already (sorted before, left as it is), missing (no
    such page: said, never invented), or refused (the subsection or the
    page does not read)."""
    name = sort["name"]
    if sort["problems"]:
        return "refused", None, f"### {name} is not filed: " + "; ".join(sort["problems"])
    rel = find_page(root, name, folder)
    if rel is None:
        where = f"the in-tray or {folder}/drops/" if folder else "the in-tray"
        return "missing", None, f"### {name} names a page that is not in {where}, so nothing was filed for it"
    path = pathlib.Path(root) / rel
    parsed = odrop.parse_page(path.read_text(encoding="utf-8"))
    if parsed["fields"].get("status") == "sorted" or parsed["sort_lines"] is not None:
        return "already", rel, f"{rel} is sorted already, so it is left as it is"
    if parsed["problems"]:
        return "refused", rel, f"{rel} does not read as a drop's page ({'; '.join(parsed['problems'])}), so its Sort is not filed"
    text = path.read_text(encoding="utf-8").rstrip("\n")
    added = oh.ascii_escape("\n".join(sort_section(sort, sid, day)))[0]
    path.write_text(text + "\n\n" + added + "\n", encoding="ascii")
    odrop.set_status(path, "sorted")
    return "filed", rel, f"{rel}: sorted by {sid} (folder: {sort['fields']['folder']})"


# --- the handbook ----------------------------------------------------------------------

def handbook_entry():
    return od.catalog_entry(space=HANDBOOK)


def add_include_pull(bale_toml, pull):
    """Add a pull to bale.toml's include group, every other byte kept:
    True when added, False when there already, None when there is no
    group to add it to (office status says so)."""
    path = pathlib.Path(bale_toml)
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("include_group_pulls = "):
            try:
                have = tomllib.loads(line)["include_group_pulls"]
            except (tomllib.TOMLDecodeError, KeyError):
                return None  # a line that does not read is office status's to name
            if pull in have:
                return False
            lines[i] = f"include_group_pulls = {oh.toml_list(sorted(have + [pull]))}"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
    return None


def handbook_arrive(root):
    """Make the handbook arrive, or finish arriving: its front page from
    the install's template, the floor plan's entry as the catalog
    declares it (the front page hung), bale.toml's trigger and the hung
    pull, each only when missing. Returns (changed paths, words)."""
    root = pathlib.Path(root)
    entry = handbook_entry()
    changed, words = [], []
    (root / HANDBOOK).mkdir(exist_ok=True)
    front = root / HANDBOOK / HANDBOOK_FRONT
    if not front.exists():
        front.write_text((TEMPLATES / HANDBOOK_FRONT_TEMPLATE).read_text(encoding="utf-8"), encoding="utf-8")
        changed.append(f"{HANDBOOK}/{HANDBOOK_FRONT}")
        words.append(f"the handbook arrives in this office: made {HANDBOOK}/{HANDBOOK_FRONT} from the install's "
                     "template")
    if od.add_space_to_floor_plan(root / MANIFEST_REL, entry, HANDBOOK):
        changed.append(MANIFEST_REL)
        words.append(f"the floor plan now lists the {HANDBOOK} space, as the install's catalog declares it")
    trigger = od.add_include_trigger(root / BALE_TOML_REL, entry["path"])
    if trigger:
        words.append(f"bale.toml's include group now triggers on {entry['path']}")
    pulled = []
    for pull in oh.space_paths({"spaces": {HANDBOOK: entry}}, "hung"):
        got = add_include_pull(root / BALE_TOML_REL, pull)
        if got:
            pulled.append(pull)
            words.append(f"bale.toml's include group now pulls {pull}, the handbook's hung front page")
    if trigger or pulled:
        changed.append(BALE_TOML_REL)
    elif trigger is None:
        words.append(f"bale.toml has no include group to add {entry['path']} to (office status says so)")
    return changed, words


def chapter_rel(project):
    return f"{HANDBOOK}/{project}.md"


def render_chapter(project):
    return oh.render_template((TEMPLATES / CHAPTER_TEMPLATE).read_text(encoding="utf-8"), {"project": project})


def ensure_chapter(root, project):
    """The chapter's path, the handbook and the chapter made when missing.
    Returns (rel, changed, words)."""
    root = pathlib.Path(root)
    changed, words = handbook_arrive(root)
    rel = chapter_rel(project)
    if not (root / rel).exists():
        (root / rel).write_text(render_chapter(project), encoding="ascii")
        changed.append(rel)
        words.append(f"made {rel}, {project}'s chapter, from the install's template")
    return rel, changed, words


def append_facts(path, entries):
    """Append fact lines at the end of the chapter's Facts section."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    start, end = oh.section_bounds(lines, "Facts")
    if start is None:
        raise oh.HelperError(f"{path.name} has no '## Facts' section to append to")
    body = trimmed(lines[start + 1:end])
    tail = [""] + lines[end:] if end < len(lines) else []
    new = lines[:start + 1] + [""] + body + list(entries) + tail
    pathlib.Path(path).write_text("\n".join(new) + "\n", encoding="ascii")


def fact_line(day, fact, sid):
    return f"- {day}: {oh.one_line(fact, 'the fact')} ({sid})"


def set_front_sheet(path, front):
    """Replace the chapter's Front sheet section whole."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    start, end = oh.section_bounds(lines, "Front sheet")
    if start is None:
        raise oh.HelperError(f"{path.name} has no '## Front sheet' section")
    body = oh.ascii_escape("\n".join(trimmed(front)))[0].split("\n")
    tail = [""] + lines[end:] if end < len(lines) else []
    new = lines[:start + 1] + [""] + body + tail
    pathlib.Path(path).write_text("\n".join(new) + "\n", encoding="ascii")


def file_handbook(root, project, facts, front, sid, day):
    """One project's facts and front sheet into its chapter. Returns
    (changed, words)."""
    rel, changed, words = ensure_chapter(root, project)
    path = pathlib.Path(root) / rel
    if facts:
        append_facts(path, [fact_line(day, f, sid) for f in facts])
        words.append(f"{rel}: {len(facts)} fact(s) from {sid}")
    if front:
        set_front_sheet(path, front)
        words.append(f"{rel}: the front sheet, replaced whole by {sid}'s")
    if rel not in changed:
        changed.append(rel)
    return changed, words


def handbook_check(root):
    """(lines, problems) for office status: a handbook that exists, against
    the install's catalog and the chapter's shape; none, said so."""
    root = pathlib.Path(root)
    entry = handbook_entry()
    listed = oh.read_toml(root / MANIFEST_REL).get("spaces", {}).get(HANDBOOK)
    here = (root / HANDBOOK).is_dir()
    if not here and listed is None:
        return ["handbook:   none in this office; it arrives with the first office land that files a fact"], 0
    problems = []
    if here and listed is None:
        problems.append(f"{HANDBOOK}/ exists but the floor plan does not list it; the next landing that files a "
                        "fact adds it")
    if listed is not None:
        for key in ("path", "hung", "filed"):
            want = entry.get(key, False)
            if listed.get(key, False) != want:
                problems.append(f"the floor plan's {HANDBOOK} {key} is {listed.get(key)!r}; the install's catalog "
                                f"says {want!r}")
        if not here:
            problems.append(f"the floor plan lists {HANDBOOK} but there is no {HANDBOOK}/ directory")
    chapters = 0
    if here:
        if not (root / HANDBOOK / HANDBOOK_FRONT).is_file():
            problems.append(f"{HANDBOOK}/{HANDBOOK_FRONT} is missing; the next landing that files a fact makes it")
        for p in sorted((root / HANDBOOK).iterdir()):
            if p.name == HANDBOOK_FRONT:
                continue
            if p.is_dir() or not CHAPTER_NAME_RE.match(p.name):
                problems.append(f"{HANDBOOK}/{p.name} is not a chapter (handbook/PROJECT.md)")
                continue
            chapters += 1
            problems += [f"{HANDBOOK}/{p.name}: {why}" for why in chapter_problems(p)]
    if problems:
        return [f"handbook:   {len(problems)} problem(s) against the install's catalog and the chapter's shape:"] + \
            [f"  {p}" for p in problems], len(problems)
    return [f"handbook:   matches the install's catalog; {chapters} chapter(s)"], 0


def chapter_problems(path):
    """What a chapter lacks against its shape: its title, its two
    sections, and Facts lines in the form office land writes."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"it cannot be read: {exc}"]
    out = []
    if not lines or lines[0] != f"# {path.stem}":
        out.append(f"its first line is not '# {path.stem}'")
    for name in ("Front sheet", "Facts"):
        if oh.section_bounds(lines, name)[0] is None:
            out.append(f"it has no '## {name}' section")
    start, end = oh.section_bounds(lines, "Facts")
    if start is not None:
        for line in lines[start + 1:end]:
            if line.strip() and not FACT_LINE_RE.match(line):
                out.append(f"a Facts line is not `- DATE: fact (SID)`: {line}")
    return out


# --- what office land files ------------------------------------------------------------

def file_notes(root, notes_text, sid, day, folder=None, project_names=()):
    """Everything office land files from one notes.md, beyond the two
    pages. Returns (said lines, changed paths). folder is the landed
    folder (space/name) or None (a standalone sort)."""
    root = pathlib.Path(root)
    notes = parse_notes(notes_text)
    said, changed = [], []
    names = list(project_names)

    def note(paths, words):
        for p in paths:
            if p not in changed:
                changed.append(p)
        said.extend(words)

    facts_by, fronts = {}, {}
    if notes["sorts"] is not None:
        lines, filed, already = [], 0, 0
        for sort in notes["sorts"]:
            state, rel, words = file_sort(root, sort, sid, day, folder)
            lines.append(words)
            if state == "already":
                already += 1
            if state != "filed":
                continue
            filed += 1
            note([rel], [])
            if sort["facts"]:
                proj = odrop.resolve_project(sort["fields"]["project"], names)
                if proj is None:
                    lines.append(f"### {sort['name']}'s facts are not filed: its project, "
                                 f"{sort['fields']['project']!r}, is none of this office's "
                                 f"({', '.join(names) or 'it scopes none'})")
                else:
                    facts_by.setdefault(proj, []).extend(sort["facts"])
            if folder and rel.startswith(f"{folder}/drops/"):
                told = tell_on_next(root / folder / "folder.md", sort["fields"]["tell"], rel[len(folder) + 1:])
                if told:
                    note([f"{folder}/folder.md"], [])
                    lines.append(f"{folder}: Next: {told}")
        said.append(f"Sort: {len(notes['sorts'])} subsection(s) in {sid}'s notes.md, {filed} filed"
                    + (f", {already} sorted already" if already else ""))
        said.extend(f"  {w}" for w in lines)
    if notes["qa"] is not None:
        if not folder:
            said.append(f"Questions and answers: {len(notes['qa'])} line(s), and no folder records {sid}, so they "
                        "are not filed")
        elif not notes["qa"]:
            said.append("Questions and answers: the section holds no `- DATE question? answer` line; nothing filed")
        else:
            md = root / folder / "folder.md"
            lines = md.read_text(encoding="utf-8").splitlines()
            for entry in [f"- from {sid}:"] + [oh.ascii_escape(q)[0] for q in notes["qa"]]:
                lines = oh.append_line_to_section(lines, "Questions and answers", entry)
                if lines is None:
                    said.append(f"Questions and answers: {folder}/folder.md has no such section; nothing filed")
                    break
            else:
                md.write_text("\n".join(lines) + "\n", encoding="utf-8")
                note([f"{folder}/folder.md"],
                     [f"Questions and answers: {len(notes['qa'])} line(s) filed in {folder}/folder.md"])
        if notes["qa_other"]:
            said.append(f"  {notes['qa_other']} line(s) not of the form `- DATE question? answer` were left out")
    if notes["handbook"] is not None:
        for project, facts, front in notes["handbook"]:
            proj = odrop.resolve_project(project, names)
            if proj is None:
                said.append(f"Handbook: ### {project} is none of this office's projects "
                            f"({', '.join(names) or 'it scopes none'}), so nothing of it is filed")
                continue
            facts_by.setdefault(proj, []).extend(facts)
            if front:
                fronts[proj] = front
    for proj in list(dict.fromkeys([*facts_by, *fronts])):
        facts, front = facts_by.get(proj, []), fronts.get(proj)
        if not facts and not front:
            continue
        paths, words = file_handbook(root, proj, facts, front, sid, day)
        note(paths, [f"Handbook: {w}" for w in words])
    if notes["handbook"] is not None and not any(facts_by.values()) and not fronts:
        said.append("Handbook: nothing in it to file")
    return said, changed


def tell_on_next(folder_md, tell, page_rel):
    """The Sort's tell: on the folder's Next section, until the meeting
    spaces exist. Returns the line, or None (nobody to tell)."""
    tell = " ".join((tell or "").split())
    if not tell or tell.lower() == "nobody":
        return None
    line = f"- tell: {oh.ascii_escape(tell)[0]} ({page_rel})"
    path = pathlib.Path(folder_md)
    lines = path.read_text(encoding="utf-8").splitlines()
    if line in lines:
        return None
    new = oh.append_line_to_section(lines, "Next", line)
    if new is None:
        return None
    path.write_text("\n".join(new) + "\n", encoding="utf-8")
    return line[2:]


# --- the moves a sorted drop asks for ----------------------------------------------------

def move_plans(root, project_names=()):
    """One plan per sorted drop still in the in-tray, oldest first: a dict
    page, name, sid, kind (new or into), folder (int for into), title,
    slug, lane, size, goal, problem (None, or why the page stays)."""
    root = pathlib.Path(root)
    names = list(project_names)
    out = []
    for d in odrop.sorted_waiting(root):
        plan = {"page": d["rel"], "name": d["name"], "sid": "", "kind": "", "folder": "", "title": d["heading"],
                "slug": "", "lane": "", "size": "", "goal": "", "problem": None}
        out.append(plan)
        parsed = odrop.parse_page((root / d["rel"]).read_text(encoding="utf-8"))
        if parsed["problems"]:
            plan["problem"] = f"it does not read as a drop's page ({'; '.join(parsed['problems'])})"
            continue
        s = page_sort(parsed["sort_lines"])
        if s["problems"]:
            plan["problem"] = "; ".join(s["problems"])
            continue
        f = s["fields"]
        plan.update(sid=s["sid"], size=f["size"], goal=f["goal"])
        ref = folder_ref(f["folder"])
        if ref == "new":
            plan["kind"] = "new"
            lane = odrop.resolve_project(f["project"], names)
            if lane is None:
                plan["problem"] = (f"its Sort names the project {f['project']!r}, which is none of this office's "
                                   f"({', '.join(names) or 'it scopes none'}), so no folder is minted for it")
                continue
            plan["lane"] = lane
            slug = d["name"][:-3]
            plan["slug"] = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
        else:
            plan.update(kind="into", folder=str(ref))
    return out


def place(root, page_rel, folder_rel, day, sid=None):
    """Move a sorted drop into its folder: the page whole into drops/, the
    History line, brief.md from the Sort's Brief (the section's text,
    nothing added), the goal when the folder has none, and the tell on
    its Next. Returns (changed paths, words)."""
    root = pathlib.Path(root)
    src = root / page_rel
    parsed = odrop.parse_page(src.read_text(encoding="utf-8"))
    s = page_sort(parsed["sort_lines"])
    if s["problems"]:
        raise oh.HelperError(f"{page_rel}: {'; '.join(s['problems'])}")
    sid = sid or s["sid"]
    name = src.name
    folder = root / folder_rel
    md = folder / "folder.md"
    if not md.is_file():
        raise oh.HelperError(f"{folder_rel} has no folder.md")
    dest = folder / "drops" / name
    if dest.exists():
        raise oh.HelperError(f"{folder_rel}/drops/{name} is there already; the page stays in the in-tray")
    words = []
    dest.parent.mkdir(exist_ok=True)
    src.rename(dest)
    words.append(f"moved {page_rel} into {folder_rel}/drops/")
    oh.folder_event(md, day, "dropped", f"drops/{name}, sorted by {sid}")
    if s["brief"]:
        brief = folder / "brief.md"
        text = "\n".join(s["brief"]) + "\n"
        state = "rewrote" if brief.exists() and brief.read_text(encoding="utf-8") != text else \
            ("kept" if brief.exists() else "wrote")
        if state != "kept":
            brief.write_text(text, encoding="ascii")
        words.append(f"{state} {folder_rel}/brief.md from the Sort's Brief"
                     + (" (what it said before is in git)" if state == "rewrote" else ""))
    goal = s["fields"].get("goal")
    if goal and oh.folder_set_field(md, "goal", goal):
        words.append(f"{folder_rel}: goal: {oh.one_line(goal, 'goal')}")
    told = tell_on_next(md, s["fields"].get("tell"), f"drops/{name}")
    if told:
        words.append(f"{folder_rel}: Next: {told}")
    return [folder_rel, page_rel], words


def drops_waited(root, drops):
    """The rels of unsorted drops that have waited through one session: a
    session recorded in a folder (office start's `office sessions: SID
    in ...` commit) after the commit that dropped the page. From git, so
    it is what happened, not what a clock says."""
    root = pathlib.Path(root)

    def git(*args):
        try:
            p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=30,
                               stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return p.stdout.strip() if p.returncode == 0 else None

    if not drops:
        return set()
    last = git("log", "-1", "--format=%ct", "-E", "--grep=^office sessions: [0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+ in ")
    if not last:
        return set()
    out = set()
    for d in drops:
        added = git("log", "--format=%ct", "--diff-filter=A", "--", d["rel"])
        if added and int(added.splitlines()[-1]) < int(last):
            out.add(d["rel"])
    return out


# --- the standalone sort's brief ---------------------------------------------------------

def render_sort_brief(root, desk_text, drafting=None):
    """The brief office start --sort sends: the standing instructions,
    every unsorted drop between its DROP markers, the desk as office desk
    prints it, and the formats. drafting says whether the office has a
    drafting table (its moves page is the session's to write)."""
    root = pathlib.Path(root)
    drafting = (root / od.SPACE).is_dir() if drafting is None else drafting
    blocks = []
    every = odrop.unsorted(root)
    if not every:
        raise oh.HelperError("the in-tray holds no unsorted drop, so there is nothing to sort")
    for d in every:
        page = (root / d["rel"]).read_text(encoding="utf-8").rstrip("\n")
        for line in page.splitlines():
            if line == odrop.DROP_END or line.startswith("--- DROP BEGIN "):
                raise oh.HelperError(f"{d['rel']} holds a line that is the brief's own marker ({line!r})")
        blocks.append("\n".join([odrop.DROP_BEGIN.format(page=d["rel"]), page, odrop.DROP_END]))
    if drafting:
        moves = ("This office has a drafting table, so its moves page, drafting-table/moves.md, is yours to "
                 "write as a sitting writes it: one line per move the desk needs that is not a drop, appended "
                 "below the page's own lines. A folder whose job is finished is closed with `- [ ] DATE close "
                 "folder N`; one whose job lives on elsewhere is `- [ ] DATE absorb folder N into=\"folder M\"`; "
                 "one that will never be done is `- [ ] DATE retire folder N why=\"...\"`. DATE is today's; the "
                 "page's own lines say every move it takes. office moves applies them after the landing.")
    else:
        moves = ("This office has no drafting table, so there is no moves page to write: a move the desk needs "
                 "that is not a drop goes in your notes.md, said in a line, for the occupant to make.")
    template = (TEMPLATES / SORT_BRIEF_TEMPLATE).read_text(encoding="utf-8")
    return oh.render_template(template, {
        "count": str(len(every)), "drops": "\n\n".join(blocks), "desk": desk_text.rstrip("\n") or "(the desk is clear)",
        "moves": moves,
    })


# --- the command line ---------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(prog="office_sort.py", description="the return of a sort, the handbook, the sort")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("file-notes", help="file a response's Sort, Questions and answers and Handbook: "
                                          "say<TAB>WORDS and path<TAB>REL lines")
    s.add_argument("root"); s.add_argument("--response", required=True); s.add_argument("--sid", required=True)
    s.add_argument("--day", required=True); s.add_argument("--folder")
    s.add_argument("--projects", default="", help="the floor plan's project names, one per line")
    s = sub.add_parser("move-plans", help="the sorted drops in the in-tray, one record per line, fields split by "
                                          "\\x1e: page kind folder title slug lane size goal sid problem")
    s.add_argument("root"); s.add_argument("--projects", default="")
    s = sub.add_parser("place", help="move a sorted drop into its folder; prints the changed paths")
    s.add_argument("root"); s.add_argument("page"); s.add_argument("folder"); s.add_argument("--day", required=True)
    s = sub.add_parser("pending", help="exit 0 when a sorted drop waits in the in-tray, 3 when none does")
    s.add_argument("root")
    s = sub.add_parser("brief", help="the brief office start --sort sends")
    s.add_argument("root"); s.add_argument("--desk-file", required=True)
    s = sub.add_parser("handbook-check", help="office status's handbook line")
    s.add_argument("root")
    s = sub.add_parser("is-sort", help="exit 0 when SID is a standalone sort's")
    s.add_argument("sid")
    a = p.parse_args(argv)
    try:
        names = [n for n in getattr(a, "projects", "").splitlines() if n.strip()]
        if a.cmd == "file-notes":
            notes = oh.notes_from_response(a.response)
            if notes is None:
                print(f"say\t{a.sid}'s response carries no notes.md, so there is no Sort, Questions and answers "
                      "or Handbook to file")
                return 0
            said, changed = file_notes(a.root, notes, a.sid, a.day, a.folder, names)
            for w in said:
                print(f"say\t{w}")
            for c in changed:
                print(f"path\t{c}")
            return 0
        if a.cmd == "move-plans":
            for m in move_plans(a.root, names):
                print("\x1e".join(str(m[k] or "") for k in ("page", "kind", "folder", "title", "slug", "lane", "size",
                                                             "goal", "sid", "problem")))
            return 0
        if a.cmd == "place":
            changed, words = place(a.root, a.page, a.folder, a.day)
            for w in words:
                log(w)
            for c in changed:
                print(c)
            return 0
        if a.cmd == "pending":
            return 0 if odrop.sorted_waiting(a.root) else 3
        if a.cmd == "brief":
            desk = pathlib.Path(a.desk_file).read_text(encoding="utf-8")
            sys.stdout.write(render_sort_brief(a.root, desk))
            return 0
        if a.cmd == "handbook-check":
            lines, problems = handbook_check(a.root)
            print("\n".join(lines))
            return 3 if problems else 0
        if a.cmd == "is-sort":
            return 0 if is_sort_sid(a.sid) else 3
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        log(f"error: {exc.__class__.__name__}: {exc}")
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
