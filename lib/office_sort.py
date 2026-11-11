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
  same way. The fact is filed bare (0.38.0): a leading `DATE:` and a
  trailing `(SID)` the session wrote itself are dropped first, since land
  adds both. The handbook arrives with the first landing that files a fact.

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
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = INSTALL / "templates"
MANIFEST_REL = "floor-plan/manifest.toml"
BALE_TOML_REL = "bale.toml"

# The standalone sort (office start --sort): an office session that
# belongs to no folder, known by its slug, so the walk-in, the desk and
# office land can tell it from any other session open in the office.
SORT_SLUG = "in-tray-sort"
SORT_GOAL = "Sort the in-tray's drops"
SORT_SID_RE = oh.LazyPattern(r"^\d{4}-\d{2}-\d{2}-" + re.escape(SORT_SLUG) + r"-\d{3}$")
SORT_BRIEF_TEMPLATE = "sort-brief.md"

SORT_FIELDS = ("project", "folder", "goal", "size", "tell", "facts")
SORT_KEY_RE = oh.LazyPattern(r"^- ([a-z]+):(?: (.*))?$")
QA_LINE_RE = oh.LazyPattern(r"^- \d{4}-\d{2}-\d{2} \S.*$")
# A Structure line (0.23.0): `- KEY: VALUE`, the key one of the fields a
# folder may mark provisional.
STRUCTURE_LINE_RE = oh.LazyPattern(r"^- ([a-z]+): ?(.*)$")
HEADING_RE = oh.LazyPattern(r"^(#{1,6}) (.+?)\s*$")
FENCE_RE = oh.LazyPattern(r"^\s*(```|~~~)")

HANDBOOK = "handbook"
HANDBOOK_FRONT = "README.md"
HANDBOOK_FRONT_TEMPLATE = "handbook-README.md"
CHAPTER_TEMPLATE = "handbook-chapter.md"
FACT_LINE_RE = oh.LazyPattern(r"^- (\d{4}-\d{2}-\d{2}): (.+) \((\S+)\)$")
# What a session may write around a fact that office land adds itself
# (0.38.0, the gaps of 2026-10-28, A8): a leading `YYYY-MM-DD:` and a
# trailing `(SID)`, either one or more times. bare_fact drops them.
FACT_LEADING_DATE_RE = oh.LazyPattern(r"^(?:\d{4}-\d{2}-\d{2}:(?: |$))+")
FACT_TRAILING_TAG_RE = oh.LazyPattern(r" ?\(([^()\s]+)\)$")
# The line office land writes above a session's Questions and answers in a
# folder (0.31.0: read back, so a response filed twice adds nothing twice).
QA_FROM_RE = oh.LazyPattern(r"^- from (\S+):$")
CHAPTER_NAME_RE = oh.LazyPattern(r"^[A-Za-z0-9][A-Za-z0-9_-]*\.md$")


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


def is_continuation(line):
    """True for a list item's continuation line as markdown wraps one: two
    or more spaces, then words (0.38.0). A blank line is not one."""
    return line.startswith("  ") and bool(line.strip())


def list_items(lines):
    """The `- ` items of lines outside fenced blocks, each joined whole
    (0.38.0): an indented continuation line (is_continuation) right below
    an item, or below another continuation, joins it with one space, so a
    fact wrapped the way markdown wraps a list item is read whole rather
    than cut off at its first line. Before 0.38.0 only the first line was
    read (the gaps of 2026-10-28: five of office-src's facts were filed
    so). Each item comes back without its `- ` and stripped."""
    inside = fenced(lines)
    items, open_ = [], False
    for n, line in enumerate(lines):
        if inside[n]:
            open_ = False
            continue
        if line.startswith("- "):
            items.append(line[2:].strip())
            open_ = True
        elif open_ and is_continuation(line):
            items[-1] = f"{items[-1]} {line.strip()}".strip()
        else:
            open_ = False
    return items


def parse_sort(name, body, brief_level=4):
    """One `### NAME.md` subsection as a dict: name, field_lines (verbatim),
    fields, facts, brief (lines, or None), problems. A subsection with
    problems is said and never filed: the office reads this format, so it
    is kept to the byte (doctrine section 4). brief_level is the Brief's
    heading level: 4 in notes.md, 3 on a drop's page, where page_sort
    reads it back with name None."""
    import office_drop as odrop
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
    # The field lines run to the first line that is neither a `- ` line
    # nor, below one, an indented continuation line (0.38.0: a fact that
    # wraps is kept whole, verbatim, and read whole below).
    inside = fenced(head)
    while i < len(head) and not inside[i] and (head[i].startswith("- ")
                                               or (out["field_lines"] and is_continuation(head[i]))):
        out["field_lines"].append(head[i])
        i += 1
    out["ignored"] = sum(1 for line in head[i:] if line.strip())
    keys = []
    for line in out["field_lines"]:
        if is_continuation(line):
            # A continuation joins the fact above it, with one space: the
            # facts: line's own fact, or the last fact line. Above the
            # facts: line a field does not wrap, as before 0.38.0.
            if len(keys) != len(SORT_FIELDS):
                break
            if out["facts"]:
                out["facts"][-1] = f"{out['facts'][-1]} {line.strip()}"
            elif out["fields"]["facts"] == "none":
                out["facts"].append(line.strip())  # said below: none, and a fact follows it
            else:
                out["fields"]["facts"] = f"{out['fields']['facts']} {line.strip()}".strip()
            continue
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


# The level-four parts a session may write under `### PROJECT` in its
# Handbook section (doctrine section 4): a front sheet since 0.23.0, its
# project's conventions since 0.57.0.
HANDBOOK_PARTS = ("Front sheet", "Conventions")


def handbook_parts(sub):
    """(head, {part: body lines}) of one `### PROJECT` subsection (0.57.0):
    the lines above the first `#### Front sheet` or `#### Conventions`
    heading, where the facts are, and each part's own lines, which end at
    the next part's heading (or the subsection's end), in either order. A
    heading that names no part stays inside the part it falls in, as it
    did inside the front sheet before 0.57.0; a part given twice is read
    as one, its bodies in order."""
    marks = [(i, t) for i, lv, t in headings(sub) if lv == 4 and t in HANDBOOK_PARTS]
    head = sub[:marks[0][0]] if marks else sub
    parts = {}
    for n, (i, title) in enumerate(marks):
        stop = marks[n + 1][0] if n + 1 < len(marks) else len(sub)
        parts.setdefault(title, []).extend(sub[i + 1:stop])
    return head, parts


def parse_handbook(body):
    """[(project, facts, front lines or None)] from a Handbook section. A
    fact that wraps onto indented continuation lines is read whole
    (list_items, 0.38.0). Since 0.57.0 a `#### Conventions` part, before
    or after the front sheet, is neither facts nor front sheet
    (parse_handbook_conventions reads it)."""
    out = []
    for project, sub in subsections(body, 3):
        head, parts = handbook_parts(sub)
        facts = list_items(head)
        front = trimmed(parts["Front sheet"]) if "Front sheet" in parts else None
        out.append((project.strip(), [f for f in facts if f], front or None))
    return out


def parse_handbook_conventions(body):
    """[(project, conventions, other)] for each `### PROJECT` of a Handbook
    section that carries a `#### Conventions` part (0.57.0): its `- `
    items, one convention each, a wrapped one read whole (list_items), and
    the count of its other non-blank lines, which are not conventions and
    are left out."""
    out = []
    for project, sub in subsections(body, 3):
        _, parts = handbook_parts(sub)
        if "Conventions" not in parts:
            continue
        lines = parts["Conventions"]
        items = [c for c in list_items(lines) if c]
        inside = fenced(lines)
        open_, other = False, 0
        for n, line in enumerate(lines):
            if not inside[n] and (line.startswith("- ") or (open_ and is_continuation(line))):
                open_ = True
                continue
            open_ = False
            other += 1 if line.strip() else 0
        out.append((project.strip(), items, other))
    return out


def parse_structure(body):
    """A Structure section's body (0.23.0) as {pairs, problems}: one
    `- KEY: VALUE` line for each of title, size and goal, in that order,
    and nothing else but blank lines; the office reads this format, so it
    is kept to the byte (doctrine section 4), and a section with problems
    is said and never filed."""
    out = {"pairs": [], "problems": []}
    lines = [line for line in body if line.strip()]
    keys = []
    for line in lines:
        m = STRUCTURE_LINE_RE.match(line)
        if not m:
            out["problems"].append(f"a line that is not `- KEY: VALUE`: {line.strip()}")
            continue
        keys.append(m.group(1))
        out["pairs"].append((m.group(1), m.group(2).strip()))
    if not out["problems"] and tuple(keys) != oh.PROVISIONAL_FIELDS:
        out["problems"].append(f"its lines are not {', '.join(oh.PROVISIONAL_FIELDS)}, one each and in that order")
    for key, value in out["pairs"]:
        if not value:
            out["problems"].append(f"its {key}: line is empty")
    return out


def parse_notes(text):
    """What office land files from a notes.md: {sorts, qa, qa_other,
    handbook, conventions, structure}, each None when the notes carry no
    such section (conventions rides on the Handbook section, 0.57.0)."""
    lines = text.splitlines()
    out = {"sorts": None, "qa": None, "qa_other": 0, "handbook": None, "conventions": None, "structure": None}
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
        out["conventions"] = parse_handbook_conventions(body)
    body = section(lines, "Structure")
    if body is not None:
        out["structure"] = parse_structure(body)
    return out


# --- a drop's page gains its Sort ----------------------------------------------------

def sort_section(sort, sid, day):
    """The lines office land appends to a drop's page: the office's first
    line, then the subsection's fields verbatim, then its Brief."""
    import office_drop as odrop
    lines = [odrop.SORT_HEADING, "", f"- sorted: {day}, by {sid}", *sort["field_lines"]]
    if sort["brief"] is not None:
        lines += ["", "### Brief", "", *sort["brief"]]
    return lines


def page_sort(sort_lines):
    """A filed Sort section read back (the lines after `## Sort`): sid,
    day, fields, brief (lines or None), problems."""
    import office_drop as odrop
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
    import office_drop as odrop
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
    import office_drop as odrop
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
    import office_drafting as od
    return od.catalog_entry(space=HANDBOOK)


def add_include_pull(bale_toml, pull):
    """Add a pull to bale.toml's include group, every other byte kept:
    True when added, False when there already, None when there is no
    group to add it to (office status says so)."""
    import tomllib
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
    import office_drafting as od
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


def bare_fact(fact, sid=None):
    """The fact alone, as office land files it (0.38.0, the gaps of
    2026-10-28, A8): its whitespace folded to single spaces, then a
    leading `YYYY-MM-DD:` and a trailing `(TAG)` dropped, each as many
    times as the session wrote them, since land adds the day and the
    session itself. TAG is a session id (YYYY-MM-DD-slug-NNN) or, given
    sid, that session's ask by name, its slug (`(fix-login)` for
    2026-10-14-fix-login-001). A date or an id inside the fact's own
    sentence stays, and so does a trailing parenthesis that is neither.
    The empty string when nothing is left.

    An office ask files its facts as a session's (0.48.0): sid is then the
    ask's name, ask-DATE-SLUG, and a trailing `(ask-DATE-SLUG)` of that
    ask, or its SLUG alone, is dropped as a session's id or slug is."""
    text = " ".join(str(fact).split())
    ask = sid[11:-4] if sid and oh.SID_RE.match(sid) else None
    asked = oh.ASK_NAME_RE.match(sid) if sid else None
    own = {sid, asked.group(2)} if asked else set()
    while True:
        before = text
        text = FACT_LEADING_DATE_RE.sub("", text).strip()
        m = FACT_TRAILING_TAG_RE.search(text)
        if m and (oh.SID_RE.match(m.group(1)) or (ask is not None and m.group(1) == ask) or m.group(1) in own):
            text = text[:m.start()].strip()
        if text == before:
            return text


def fact_line(day, fact, sid):
    """A Facts line, `- DAY: fact (SID)`, the fact made bare first, so a
    line office land writes carries one day and one session, whatever the
    session wrote. A fact that is nothing but a date and an id has no
    line: HelperError, which file_handbook never lets happen."""
    return f"- {day}: {oh.one_line(bare_fact(fact, sid), 'the fact')} ({sid})"


def fact_key(line):
    """(bare fact, sid) of a Facts line, or None when the line is not one.
    The fact is read back bare, so a doubled line filed before 0.38.0
    (`- DAY: DAY: fact (SID) (SID)`) keys as the same fact filed bare now,
    and the same response filed again adds it nowhere twice."""
    m = FACT_LINE_RE.match(line)
    return (bare_fact(m.group(2), m.group(3)), m.group(3)) if m else None


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


CONVENTIONS = "Conventions"
NONE_SETTLED = "None settled yet."   # the chapter template's place for them (0.56.0)


def convention_line(item):
    """One convention as the chapter keeps it (0.57.0): `- ` and its words
    on one line, in ASCII, as a front sheet's are."""
    return f"- {oh.one_line(item, 'a convention')}"


def conventions_body(path):
    """The chapter's `## Conventions` section's lines (the blank lines
    around them dropped), or None when the chapter has no such section."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    start, end = oh.section_bounds(lines, CONVENTIONS)
    return None if start is None else trimmed(lines[start + 1:end])


def settled_conventions(path):
    """The `- ` lines a chapter's Conventions section holds (0.57.0): none
    when there is no section, or it still reads None settled yet."""
    body = conventions_body(path) or []
    return [line for line in body if line.startswith("- ")]


def set_conventions(path, entries):
    """Replace the chapter's Conventions section whole with entries (each
    a convention_line), as set_front_sheet replaces the front sheet
    (0.57.0). A chapter with no such section (one made before 0.56.0)
    gains it between its front sheet and its facts: before `## Facts`,
    else after the front sheet, else at its end."""
    path = pathlib.Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    start, end = oh.section_bounds(lines, CONVENTIONS)
    if start is not None:
        tail = [""] + lines[end:] if end < len(lines) else []
        new = lines[:start + 1] + [""] + list(entries) + tail
    else:
        block = [f"## {CONVENTIONS}", ""] + list(entries)
        at, _ = oh.section_bounds(lines, "Facts")
        if at is None:
            _, at = oh.section_bounds(lines, "Front sheet")
        if at is None or at >= len(lines):
            new = trimmed(lines) + [""] + block
        else:
            new = trimmed(lines[:at]) + [""] + block + [""] + lines[at:]
    path.write_text("\n".join(new) + "\n", encoding="ascii")


def file_conventions(path, rel, conventions, sid):
    """A session's settled conventions into a chapter's `## Conventions`,
    whole (0.57.0). Returns (wrote, words): the set the chapter already
    reads is said and left; otherwise the section is replaced by sid's, and
    each line it held that the new set does not carry is named, so nothing
    settled leaves without a word. The caller has checked the floor (an
    answer of the occupant's in the notes) and that the set is not empty."""
    entries, keys, twice = [], set(), 0
    for item in conventions:
        line = convention_line(item)
        if line in keys:
            twice += 1
            continue
        keys.add(line)
        entries.append(line)
    body = conventions_body(path)
    if body == entries:
        return False, [f"{rel}: the conventions already read as {sid}'s, left as they are"]
    held = [" ".join(line.split()) for line in (body or []) if line.strip() and line.strip() != NONE_SETTLED]
    gone = [line for line in held if line not in keys]
    set_conventions(path, entries)
    words = [f"{rel}: the conventions, replaced whole by {sid}'s ({len(entries)})"
             + ("; the section is new in this chapter" if body is None else "")
             + (f"; {twice} given twice, kept once" if twice else "")]
    words += [f"{rel}: no longer settled, since {sid}'s set does not carry it: {line}" for line in gone]
    return True, words


def filed_facts(path):
    """{(fact, sid)} of the Facts lines a chapter holds, in the form
    office land writes, each fact read back bare (fact_key); the day each
    was filed is not part of the key, so a response filed again on a
    later day finds its facts there."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    start, end = oh.section_bounds(lines, "Facts")
    out = set()
    for line in lines[start + 1:end] if start is not None else []:
        key = fact_key(line)
        if key:
            out.add(key)
    return out


def front_sheet_body(path):
    """The chapter's Front sheet section as set_front_sheet writes it
    (its lines, the blank lines around them dropped), or None."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    start, end = oh.section_bounds(lines, "Front sheet")
    return None if start is None else trimmed(lines[start + 1:end])


def file_handbook(root, project, facts, front, sid, day, conventions=None):
    """One project's facts and front sheet into its chapter, and since
    0.57.0 its settled conventions (file_conventions; the caller checks
    the floor). Returns (changed, words). Each fact is filed bare (0.38.0,
    bare_fact), and keyed bare: filed twice (0.31.0), a fact the chapter
    already holds from the same session is said and left, as is a fact
    the same filing gives twice (a Handbook line and a Sort's facts: line,
    say), and a front sheet or a set of conventions the chapter already
    reads is not written again: the facts grow at their end and nothing
    filed is rewritten."""
    rel, changed, words = ensure_chapter(root, project)
    path = pathlib.Path(root) / rel
    wrote = bool(changed)
    # Who adds the day and the tag, and what the tag is (0.48.0): office
    # land and a session's id, or office ask and the ask's name.
    by, tag = ("office ask", "the ask's name") if oh.ASK_NAME_RE.match(sid or "") else ("office land", "a session id")
    if facts:
        have = filed_facts(path)
        new, seen, already, twice, dressed, empty = [], set(have), 0, 0, 0, 0
        for fact in facts:
            bare = bare_fact(fact, sid)
            if not bare:
                empty += 1
                continue
            if bare != " ".join(str(fact).split()):
                dressed += 1
            entry = fact_line(day, bare, sid)
            key = fact_key(entry)
            if key in have:
                already += 1
            elif key in seen:
                twice += 1
            else:
                seen.add(key)
                new.append(entry)
        if new:
            append_facts(path, new)
            wrote = True
            words.append(f"{rel}: {len(new)} fact(s) from {sid}"
                         + (f"; {already} already there, left as they are" if already else "")
                         + (f"; {twice} given twice, filed once" if twice else ""))
        elif already:
            words.append(f"{rel}: all {already} fact(s) from {sid} already there, left as they are")
        if dressed:
            words.append(f"{rel}: {dressed} fact(s) from {sid} came with a date or {tag} of their own, "
                         f"dropped before filing, since {by} adds both (write facts bare)")
        if empty:
            words.append(f"{rel}: {empty} fact(s) from {sid} held nothing but a date and {tag}, so "
                         "nothing of them is filed")
    if front:
        if front_sheet_body(path) == oh.ascii_escape("\n".join(trimmed(front)))[0].split("\n"):
            words.append(f"{rel}: the front sheet already reads as {sid}'s, left as it is")
        else:
            set_front_sheet(path, front)
            wrote = True
            words.append(f"{rel}: the front sheet, replaced whole by {sid}'s")
    if conventions:
        did, said = file_conventions(path, rel, conventions, sid)
        wrote = wrote or did
        words.extend(said)
    if wrote and rel not in changed:
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
    import office_drop as odrop
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
            # Filed twice (the same response by land and by sessions
            # --pages, 0.31.0): a line already in the section is said and
            # left, and nothing filed is rewritten.
            start, end = oh.section_bounds(lines, "Questions and answers")
            there = lines[start + 1:end] if start is not None else []
            entries = [oh.ascii_escape(q)[0] for q in notes["qa"]]
            new = [e for e in entries if e not in there]
            heads = [l for l in there if QA_FROM_RE.match(l)]
            head = [] if not new or (heads and heads[-1] == f"- from {sid}:") else [f"- from {sid}:"]
            for entry in head + new:
                lines = oh.append_line_to_section(lines, "Questions and answers", entry)
                if lines is None:
                    said.append(f"Questions and answers: {folder}/folder.md has no such section; nothing filed")
                    break
            else:
                already = len(entries) - len(new)
                if new:
                    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    note([f"{folder}/folder.md"],
                         [f"Questions and answers: {len(new)} line(s) filed in {folder}/folder.md"
                          + (f"; {already} already there, left as they are" if already else "")])
                else:
                    said.append(f"Questions and answers: all {already} line(s) already in {folder}/folder.md, "
                                "left as they are; nothing filed")
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
    settled = conventions_to_file(notes, names, sid, said)
    for proj in list(dict.fromkeys([*facts_by, *fronts, *settled])):
        facts, front = facts_by.get(proj, []), fronts.get(proj)
        if not facts and not front and not settled.get(proj):
            continue
        paths, words = file_handbook(root, proj, facts, front, sid, day, conventions=settled.get(proj))
        note(paths, [f"Handbook: {w}" for w in words])
    if notes["handbook"] is not None and not any(facts_by.values()) and not fronts and not settled \
            and not notes["conventions"]:
        said.append("Handbook: nothing in it to file")
    structure = notes["structure"]
    if structure is not None:
        if structure["problems"]:
            said.append(f"Structure: not filed, since its lines do not read: {'; '.join(structure['problems'])}")
        elif not folder:
            said.append(f"Structure: no folder records {sid}, so it is not filed")
        elif not folder.startswith("desk/"):
            said.append(f"Structure: not filed, since {folder} is in the filing cabinet, whose folders move whole")
        else:
            wrote, words = oh.file_structure(root / folder / "folder.md", structure["pairs"])
            if wrote:
                note([f"{folder}/folder.md"], [])
            said.append(f"Structure: {folder}: " + "; ".join(words))
    return said, changed


def conventions_to_file(notes, names, sid, said):
    """{project: conventions} of a notes.md's `#### Conventions` parts that
    office land files (0.57.0), each said in `said` when it is not: a part
    under a project the office does not scope (its Handbook line says so
    already), a part with no `- ` line (said, and never empties a settled
    section), and every part when the notes record no answer of the
    occupant's, the floor: a session writes its conventions only after he
    has answered a light block about them, so without one line under `##
    Questions and answers` they are said and left unfiled, and the rest of
    the notes is filed as ever."""
    import office_drop as odrop
    out = {}
    for project, items, other in notes["conventions"] or []:
        proj = odrop.resolve_project(project, names)
        if proj is None:
            continue
        if other:
            said.append(f"Handbook: ### {project}'s #### Conventions: {other} line(s) that are not `- ` lines were "
                        "left out (one convention a line)")
        if not items:
            said.append(f"Handbook: ### {project}'s #### Conventions holds no `- ` line, so nothing of it is "
                        "filed and the chapter's conventions are left as they are")
            continue
        if not notes["qa"]:
            said.append(f"Handbook: ### {project}'s #### Conventions is not filed: {sid}'s notes record no answer "
                        "of the occupant's (no `- DATE question? answer` line under ## Questions and answers), and "
                        "a session settles conventions only after he answers; the chapter is left as it is")
            continue
        out.setdefault(proj, []).extend(items)
    return out


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
    import office_drop as odrop
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
    import office_drop as odrop
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
    import subprocess
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
    import office_drafting as od
    import office_drop as odrop
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
            import office_drop as odrop
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
