#!/usr/bin/env python3
"""The map: `office map` (0.46.0), every project and its folders on one page.

The occupant works with folders (one job each) and projects (a repo
each), and before this page the two met nowhere: office desk names a
folder's lane only inside its cite, and office projects names no folder.
The map reads both, once, and puts each folder beside the project its lane
names. Since 0.49.0 the page is two tables, read at a glance:

    office_map.py page OFFICE --today DAY [--project NAME | --folder REL] [--all] [--now ISO]
        the page on stdout. With no option, two tables under a header row
        each, columns aligned: the projects, one row each (PROJECT, WHERE
        it is, its AUDIENCE or none, PAUSED, and what RIDES with it and
        what runs AFTER it lands in one cell, a declaration problem said in
        that cell); then the folders, one row each (FOLDER, PROJECT, TITLE,
        SIZE, STATE in a few words), grouped by project in the floor
        plan's order and the office's own last, open folders before closed
        ones, each newest number first. Of a project's closed folders the
        newest CLOSED_SHOWN show and the rest fold into one line, `and N
        more closed: office map --all`; --all shows every row. On a
        terminal the page is cut to its width (the title column gives way
        first, then the state, each cut with `...`); piped, every cell is
        whole. With --project, that project's rows in both tables, nothing
        folded; with --folder (desk/NAME or filing-cabinet/NAME), one
        folder's whole record, ending with the lines that change its fields.
    office_map.py fields OFFICE REL
        office folder N with no flag: the folder's fields, then the line
        that changes each.
    office_map.py open-for OFFICE REL
        the sessions open that the folder records, SID<tab>WHERE (a
        project's name, or `this office`), for office folder --lane's
        word on a session out elsewhere

The map reads what the desk reads, once (office_bale.render_desk's
groups: what is in flight, landed and not delivered, the merge jobs and
the reviews), bale's records of the sessions open (one status per repo,
cached by the reader), the floor plan and the folders' pages. It writes
nothing, on a terminal or off one. Every line it prints shows his words as
he wrote them (office_helper.shown); the pages keep their ASCII.

Standard library only. Logs on stderr with an [office] prefix; exits 0 on
success, 1 on a refusal, 2 on an internal error.
"""

import argparse
import datetime as dt
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

THE_OFFICE = "the office"


def job_kind_word(job):
    """merge or undo (0.51.0): which kind of job a folder's waiting job is."""
    import office_bale as ob
    return "undo" if ob.odl_is_undo(job) else "merge"


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- a folder's state, in the desk's words ---------------------------------------------

def folder_place(f, names):
    """(project or None, the lane's words when it names no project here):
    where the folder's lane puts it on the map."""
    lane = (f.get("fields", {}).get("lane") or [""])[0]
    if oh.lane_is_office(lane):
        return None, None
    project = oh.lane_project(lane)
    if project in names:
        return project, None
    return None, (f"lane: {lane}, not a project here" if lane else None)


class Reading:
    """Everything the map says, read once: the desk's groups, the sessions
    open and the folders they map to, the floor plan's projects."""

    def __init__(self, rd, office_root, today, now=None):
        import office_bale as ob
        self.rd = rd
        self.root = pathlib.Path(office_root)
        self.now = now or dt.datetime.now(dt.timezone.utc)
        self.groups = {}
        ob.render_desk(rd, office_root, today, walk_in=True, now=self.now, groups_out=self.groups)
        self.projects = ob.office_projects(office_root) or []
        self.names = [p["name"] for p in self.projects]
        self.folders = [f for f in oh.read_folders(office_root)]
        every, problems = ob.open_anywhere(rd, office_root, rendering=True)
        for line in problems:
            debug(f"the map could not read every repo: {line}")
        self.open_by_rel = {}
        for x in every:
            for rel in x["folders"]:
                self.open_by_rel.setdefault(rel, []).append(x)
        self.desk_group = {}
        for key, words in (("open", "open, no session in flight"), ("ready", "ready"), ("candidates", "candidate"),
                           ("no_status", "no status line"), ("misplaced", "on the desk with a closed status")):
            for f in self.groups.get(key) or []:
                self.desk_group[f["rel"]] = words
        for heading, rows in (self.groups.get("parked") or {}).items():
            for f, _ in rows:
                self.desk_group[f["rel"]] = f"parked: {heading}"

    def age(self, x):
        import office_bale as ob
        import office_home as hs
        try:
            d = self.rd.dossier(x["place"], x["sid"])
        except ob.BaleError as exc:
            debug(f"{x['sid']}: its dossier could not be read for the map: {exc}")
            return None
        if d is None:
            return None
        v = ob.session_view(self.rd, d)
        if not v["created"]:
            return None
        when = ob.parse_stamp(v["created"])
        return f"{hs.local_day(v['created'], ob.office_zone(self.root))}, {hs.age_words(when, self.now)}"

    def out_on(self, f):
        """The sessions open that the folder records, the ones that land
        first, each oldest first."""
        return sorted(self.open_by_rel.get(f["rel"]) or [], key=lambda x: (x["read_only"], x["sid"]))

    def state(self, f):
        """The folder's state in the desk's words (0.41.0 to 0.43.0)."""
        import office_review as orev
        import office_standing as ostand
        import office_bale as ob
        if f.get("problem"):
            return f"cannot be read: {f['problem']}"
        said = []
        out = self.out_on(f)
        if out:
            x = out[0]
            age = self.age(x)
            when = f", out since {age}" if age else ""
            if x["read_only"]:
                words = f"a sitting out: {x['sid']}{when}"
                st = ostand.folder_standing(self.root, f["rel"])
                if st is not None:
                    words += f"; step {st['step']} of {st['of']}"
            else:
                words = f"in flight: {x['sid']}{when}"
            if len(out) > 1:
                words += f"; and {len(out) - 1} more open"
            said.append(words)
        m = (self.groups.get("merge_by_rel") or {}).get(f["rel"])
        u = (self.groups.get("undelivered_by_rel") or {}).get(f["rel"])
        if m is not None and not m["landed"]:
            said.append(f"{job_kind_word(m['job'])} job waiting")
        elif u is not None:
            said.append(f"landed {u['sid']} on {u['day']}, not delivered")
        if not said:
            if f["space"] == "filing-cabinet":
                said.append(f"closed, {f.get('status') or 'no status line'}")
            else:
                said.append(self.desk_group.get(f["rel"], f.get("status") or "no status line"))
        try:
            delivered = oh.delivered_records(f["path"])
        except (OSError, UnicodeDecodeError) as exc:
            debug(f"{f['rel']}: its deliveries could not be read: {exc}")
            delivered = []
        if delivered and u is None:
            day, rec = delivered[-1]
            said.append(f"delivered {rec['branch']} on {day}")
        rows = (self.groups.get("reviews_by_rel") or {}).get(f["rel"])
        if rows:
            said.append(orev.folder_words(rows))
        if f["space"] == "filing-cabinet" and out:
            said.append(f"in the filing cabinet ({ob.folder_key(f)})")
        return "; ".join(said)


def folder_title(f):
    return f.get("title") or f["name"]


def folder_head(f):
    size = (f.get("fields", {}).get("size") or [None])[0]
    head = f"folder {f['number']}" if f.get("number") else f["name"]
    return f"{head}  {folder_title(f)}" + (f"  ({size})" if size else "")


def newest_first(folders):
    return sorted(folders, key=lambda f: (-(f.get("number") or 0), f["rel"]))


# --- the two tables (0.49.0) ------------------------------------------------------------

# Of a project's closed folders, the newest this many show; the rest fold
# into one line (office map --all shows them).
CLOSED_SHOWN = 3
FOLD_WORDS = "and {n} more closed: office map --all"
CUT = "..."

PROJECT_HEADER = ("PROJECT", "WHERE", "AUDIENCE", "PAUSED", "RIDES AND AFTER-LAND")
FOLDER_HEADER = ("FOLDER", "PROJECT", "TITLE", "SIZE", "STATE")
# On a terminal narrower than a table, the columns that give way, in order,
# each no narrower than its floor: the folders' title first, then their
# state; the projects' rides first, then the audience, then where.
PROJECT_GIVE = ((4, 16), (2, 12), (1, 16))
FOLDER_GIVE = ((2, 16), (4, 20), (1, 10))


def cut(cell, width):
    """cell, cut to width with `...` when it is longer."""
    if len(cell) <= width:
        return cell
    return cell[:max(0, width - len(CUT))] + CUT if width > len(CUT) else cell[:width]


def table(header, rows, width=None, give=(), under=0):
    """Lines: the header row, then a row per entry, columns aligned two
    spaces apart, the last column unpadded, every cell as he wrote it
    (office_helper.shown, before anything is measured). width (the
    terminal's, or None piped) cuts the columns give names, in order, each
    to no less than its floor, until the table fits; what still does not
    fit runs on. A row that is a str is a line of its own (the fold line),
    set under column `under`, never cut."""
    rows = [oh.shown(r) if isinstance(r, str) else [oh.shown(c) for c in r] for r in rows]
    cells = [list(header)] + [list(r) for r in rows if not isinstance(r, str)]
    widths = [max(len(c[i]) for c in cells) for i in range(len(header))]
    if width:
        over = sum(widths) + 2 * (len(widths) - 1) - width
        for col, floor in give:
            if over <= 0:
                break
            take = min(over, max(0, widths[col] - floor))
            widths[col] -= take
            over -= take

    def line(r):
        out = [cut(c, widths[i]).ljust(widths[i]) for i, c in enumerate(r[:-1])] + [cut(r[-1], widths[-1])]
        return "  ".join(out).rstrip()
    indent = " " * (sum(widths[:under]) + 2 * under)
    return [line(list(header))] + [indent + r if isinstance(r, str) else line(r) for r in rows]


def project_row(p):
    """A project's row: its name, where it is, its audience, paused, and
    what rides with it and runs after it lands in one cell."""
    if p.get("problem"):
        return [p["name"], f"cannot be read: {p['problem']}", "-", "-", "-"]
    where = f"on {p['host']} ({p['path']})" if p.get("host") else f"here ({p['path']})"
    if p.get("audience"):
        aud = p["audience"]
        if p.get("author"):
            aud += f", author {p['author']}"
        aud += f", base {p['base'] or 'the audience HEAD'}"
        if p.get("branch_prefix"):
            aud += f", branch_prefix {p['branch_prefix']}"
    else:
        aud = "none"
    said = []
    if p.get("rides"):
        # A ride on the project's host (0.50.0) as stored, marked as the
        # host's: the map reaches no host for it.
        said.append("rides: " + ", ".join(oh.ride_words(r, p.get("host")) for r in p["rides"]))
    if p.get("after_land"):
        said.append("after: " + "; ".join(p["after_land"]))
    said += [f"declaration problem: {x}" for x in p.get("declaration_problems") or []]
    return [p["name"], where, aud, "yes" if p.get("paused") else "no", "; ".join(said) or "none"]


def short_age(x, reading):
    """How long a session has been out, in two words (`3 days`), or None
    when bale's records do not say."""
    import office_bale as ob
    import office_home as hs
    try:
        d = reading.rd.dossier(x["place"], x["sid"])
    except ob.BaleError as exc:
        debug(f"{x['sid']}: its dossier could not be read for the map: {exc}")
        return None
    if d is None:
        return None
    v = ob.session_view(reading.rd, d)
    if not v["created"]:
        return None
    words = hs.age_words(ob.parse_stamp(v["created"]), reading.now)
    return {"yesterday": "1 day", "just now": "just now"}.get(words, words.removesuffix(" ago"))


# The desk's group words (Reading.desk_group) said short.
DESK_WORDS = {"open, no session in flight": "open"}


def short_state(reading, f):
    """The folder's state cell (0.49.0): a few words, the session's id left
    to office map N. `sitting out 2 days, step 8 of 14`, `in flight 3
    days`, `landed, not delivered`, `merge job waiting`, `delivered
    BRANCH`, `review #N STATE`, `open`, `ready`, `done`, `retired`; `; and N
    more open` when the folder records more than one session out."""
    import office_review as orev
    import office_standing as ostand
    if f.get("problem"):
        return f"cannot be read: {f['problem']}"
    said = []
    out = reading.out_on(f)
    if out:
        x = out[0]
        age = short_age(x, reading)
        words = ("sitting out" if x["read_only"] else "in flight") + (f" {age}" if age else "")
        if x["read_only"]:
            st = ostand.folder_standing(reading.root, f["rel"])
            if st is not None:
                words += f", step {st['step']} of {st['of']}"
        if len(out) > 1:
            words += f"; and {len(out) - 1} more open"
        said.append(words)
    m = (reading.groups.get("merge_by_rel") or {}).get(f["rel"])
    u = (reading.groups.get("undelivered_by_rel") or {}).get(f["rel"])
    if m is not None and not m["landed"]:
        said.append(f"{job_kind_word(m['job'])} job waiting")
    elif u is not None:
        said.append("landed, not delivered")
    if not said:
        if f["space"] == "filing-cabinet":
            said.append(f.get("status") or "no status line")
        else:
            group = reading.desk_group.get(f["rel"])
            if group is None:
                said.append(f.get("status") or "no status line")
            elif group.startswith("parked"):
                said.append("parked")
            elif group == "on the desk with a closed status":
                said.append(f"{f.get('status')} on the desk")
            else:
                said.append(DESK_WORDS.get(group, group))
    try:
        delivered = oh.delivered_records(f["path"])
    except (OSError, UnicodeDecodeError) as exc:
        debug(f"{f['rel']}: its deliveries could not be read: {exc}")
        delivered = []
    if delivered and u is None:
        said.append(f"delivered {delivered[-1][1]['branch']}")
    rows = (reading.groups.get("reviews_by_rel") or {}).get(f["rel"])
    if rows:
        said.append(orev.folder_words(rows))
    if f["space"] == "filing-cabinet" and out:
        said.append("in the filing cabinet")
    return "; ".join(said)


def is_closed(reading, f):
    """Whether a folder folds with the closed ones: in the filing cabinet,
    with no session out, no merge job and nothing landed and not delivered
    (one that has is shown with the open folders, so the fold never hides
    something waiting)."""
    if f.get("problem") or f["space"] != "filing-cabinet":
        return False
    if reading.out_on(f):
        return False
    return f["rel"] not in (reading.groups.get("merge_by_rel") or {}) and \
        f["rel"] not in (reading.groups.get("undelivered_by_rel") or {})


def folder_row(reading, f):
    lane = (f.get("fields", {}).get("lane") or [""])[0]
    if f.get("problem"):
        project = "-"
    else:
        project = oh.folder_project_words(lane, reading.names)
    size = (f.get("fields", {}).get("size") or [None])[0] if not f.get("problem") else None
    head = f"folder {f['number']}" if f.get("number") else f["name"]
    return [head, project, folder_title(f), size or "-", short_state(reading, f)]


def folder_rows(reading, folders, fold):
    """A group's rows: its open folders, then its closed ones, each newest
    number first; with fold, the closed beyond CLOSED_SHOWN as one line."""
    live = [f for f in folders if not is_closed(reading, f)]
    closed = [f for f in folders if is_closed(reading, f)]
    rows = [folder_row(reading, f) for f in newest_first(live)]
    closed = newest_first(closed)
    shown_closed = closed[:CLOSED_SHOWN] if fold else closed
    rows += [folder_row(reading, f) for f in shown_closed]
    if len(closed) > len(shown_closed):
        rows.append(FOLD_WORDS.format(n=len(closed) - len(shown_closed)))
    return rows


def terminal_width():
    """The terminal's width when the page goes to one, else None (piped,
    every cell is whole)."""
    import shutil
    try:
        if not sys.stdout.isatty():
            return None
    except (AttributeError, ValueError):
        return None
    return shutil.get_terminal_size().columns or None


def page(reading, project=None, fold=True, width=None):
    """The map's page: the projects' table, then the folders' table, then
    the footer line. project: that project's rows alone, nothing folded."""
    import office_bale as ob
    if project is not None:
        projects = ob.select(reading.projects, project)[:1]
        fold = False
    else:
        projects = reading.projects
    lines = []
    if projects:
        lines += table(PROJECT_HEADER, [project_row(p) for p in projects], width, PROJECT_GIVE)
    else:
        lines.append("this office scopes no project yet (office projects add NAME PATH adds one)")
    rows = []
    readable = [f for f in reading.folders if not f.get("problem")]
    for p in projects:
        rows += folder_rows(reading, [f for f in readable if folder_place(f, reading.names)[0] == p["name"]], fold)
    if project is None:
        theirs = [f for f in reading.folders if f.get("problem") or folder_place(f, reading.names)[0] is None]
        rows += folder_rows(reading, theirs, fold)
    lines.append("")
    if rows:
        lines += table(FOLDER_HEADER, rows, width, FOLDER_GIVE, under=FOLDER_HEADER.index("TITLE"))
    else:
        lines.append("no folder" + (f" on {projects[0]['name']}" if project is not None else
                                    " on the desk or in the filing cabinet"))
    return lines + ["", "office map N shows one folder's whole record and the lines that change it."]


# --- one folder ---------------------------------------------------------------------------

def change_lines(f, projects):
    """The lines that change each of the folder's fields, filled in with
    its values: the exact line, then what it does."""
    import shlex
    values, provisional = oh.folder_field_values(f["path"])
    key = f["number"] if f.get("number") else f["name"]
    q = shlex.quote
    lane = values["lane"]
    rows = [
        (f"office folder {key} --lane {q(oh.lane_project(lane) or (projects[0] if projects else 'PROJECT'))}",
         "puts its work on that project (" + (", ".join(projects) or "the office scopes none") + ")"),
        (f"office folder {key} --in-office", "says its work is the office's own"),
        (f"office folder {key} --title {q(values['title'] or 'TITLE')}", "renames it"),
        (f"office folder {key} --size {values['size'] or 'small'}", "sizes it: " + ", ".join(oh.SIZES)),
        (f"office folder {key} --goal {q(values['goal'] or 'TEXT')}", "the one sentence office start offers"),
        (f"office folder {key} --source {q(values['source'] or 'WHO')}", "who or what asked for it"),
        (f"office folder {key} --class {values['class'] or 'code'}", "bale's work class: " + ", ".join(oh.WORK_CLASSES)),
    ]
    width = max(len(line) for line, _ in rows)
    out = [f"  {line.ljust(width)}  {what}" for line, what in rows]
    if provisional:
        out.append(f"  (provisional, a session's to set until you set it: {', '.join(provisional)})")
    return out


def field_lines(f):
    values, _ = oh.folder_field_values(f["path"])
    lane = values["lane"]
    if oh.lane_is_office(lane):
        lane = f"{oh.OFFICE_LANE} (its work is the office's own)"
    shown = dict(values, lane=lane)
    return [f"  {k}: {shown[k] if shown[k] is not None else 'none'}" for k in oh.EDIT_FIELDS] + \
        [f"  status: {f.get('status') or 'none'} (open, close and reopen write it)"]


def next_lines(reading, f):
    """The lines that act on the folder next, as the Next line would pick
    them, each the line to type and what it does."""
    import office_bale as ob
    key = ob.folder_key(f)
    rows = []
    for x in reading.out_on(f):
        if x["read_only"]:
            rows.append((f"office land {x['sid']}", "ends the sitting, once it is over"))
        else:
            rows.append((f"office land {x['sid']}", "brings the session back once its response is in your downloads"))
        rows.append((f"office tray {x['sid']}", "opens its out tray again and prints its opener"))
    m = (reading.groups.get("merge_by_rel") or {}).get(f["rel"])
    u = (reading.groups.get("undelivered_by_rel") or {}).get(f["rel"])
    if m is not None and not m["landed"]:
        kind = job_kind_word(m["job"])
        bailed = ob.job_bailed(m["job"])
        rows.append((ob.job_start_line(f, m["job"]),
                     f"hands off {bailed}, which bailed out of the {kind} job" if bailed
                     else f"sends the {kind} session office deliver wrote"))
    elif u is not None:
        rows.append((f"office deliver {key}", f"carries {u['sid']}'s work to {u['project']}'s audience"))
    if not rows:
        if f["space"] == "filing-cabinet":
            rows.append((f"office reopen {key}", "brings it back to the desk"))
        else:
            rows.append((f"office start {key}", "sends its session out"))
    width = max(len(line) for line, _ in rows)
    return [f"  {line.ljust(width)}  {what}" for line, what in rows]


def folder_record(reading, rel):
    import office_bale as ob
    import office_review as orev
    import office_standing as ostand
    import office_drafting as od
    f = next((x for x in reading.folders if x["rel"] == rel), None)
    if f is None:
        raise oh.HelperError(f"no folder {rel} in this office")
    if f.get("problem"):
        raise oh.HelperError(f"{rel} cannot be read: {f['problem']}")
    project, odd = folder_place(f, reading.names)
    lines = [f"{folder_head(f)}  ({rel})", f"  {reading.state(f)}",
             f"  on {project}" if project else f"  in {THE_OFFICE}" + (f" ({odd})" if odd else ""), "", "Fields:"]
    lines += field_lines(f)
    lines += ["", "Sessions:"]
    try:
        said, _ = ob.render_folder_sessions(reading.rd, reading.root, f["path"])
    except ob.BaleError as exc:
        said = [f"cannot read bale's records: {exc}"]
    lines += [f"  {l}" for l in said]
    text = pathlib.Path(f["path"]).read_text(encoding="utf-8").splitlines()
    s, e = oh.section_bounds(text, "Riders")
    riders = od.rider_blocks(text, s + 1, e) if s is not None else []
    lines += ["", "Riders:"] + ([f"  rider {r['number']}  {r['title']}  ({r['status'] or 'no status'})"
                                 for r in riders] or ["  none"])
    delivered = oh.delivered_records(f["path"])
    rows = (reading.groups.get("reviews_by_rel") or {}).get(f["rel"]) or []
    lines += ["", "Deliveries and reviews:"]
    lines += [f"  {day}: delivered {rec['branch']} on {rec['audience']} of {rec['project']}, sessions "
              f"{', '.join(rec['sessions']) or 'none'}" for day, rec in delivered]
    lines += [f"  review {r['words']}" for r in rows]
    if not delivered and not rows:
        lines.append("  none")
    st = ostand.folder_standing(reading.root, f["rel"])
    lines += ["", "Standing:", f"  {st['sitting']}'s: {ostand.words(st)}" if st else "  none filed"]
    lines += ["", "Next:"] + next_lines(reading, f)
    lines += ["", "Change a field (office folder writes the line, its History says so, and nothing else):"]
    lines += change_lines(f, reading.names)
    return lines


def folders_fields(office_root, rel):
    """office folder N with no flag: the fields, then the line that
    changes each."""
    import office_bale as ob
    f = next((x for x in oh.read_folders(office_root) if x["rel"] == rel), None)
    if f is None:
        raise oh.HelperError(f"no folder {rel} in this office")
    if f.get("problem"):
        raise oh.HelperError(f"{rel} cannot be read: {f['problem']}")
    names = [p["name"] for p in ob.office_projects(office_root) or []]
    return [f"{folder_head(f)}  ({rel})", "", "Fields:"] + field_lines(f) + ["", "The lines that change each:"] + \
        change_lines(f, names)


def main(argv=None):
    import office_bale as ob
    ap = argparse.ArgumentParser(prog="office_map.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("page", help="the map, or one project's section, or one folder's record")
    p.add_argument("office"); p.add_argument("--today", required=True)
    p.add_argument("--project"); p.add_argument("--folder"); p.add_argument("--now")
    p.add_argument("--all", action="store_true", help="every closed folder, none folded")
    p = sub.add_parser("fields", help="a folder's fields and the line that changes each")
    p.add_argument("office"); p.add_argument("rel")
    p = sub.add_parser("open-for", help="the sessions open that a folder records: SID, WHERE")
    p.add_argument("office"); p.add_argument("rel")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "open-for":
            every, problems = ob.open_anywhere(ob.Reader(), a.office, rendering=True)
            for line in problems:
                debug(f"not every repo could be read for the sessions out on {a.rel}: {line}")
            for x in every:
                if a.rel in x["folders"]:
                    print(f"{x['sid']}\t{x['label']}")
            return 0
        if a.cmd == "fields":
            print(oh.shown("\n".join(folders_fields(a.office, a.rel))))
            return 0
        dt.date.fromisoformat(a.today)
        if a.project and a.folder:
            raise oh.HelperError("the map shows a project or a folder, not both")
        now = ob.parse_stamp(a.now) if a.now else None
        reading = Reading(ob.Reader(), a.office, a.today, now)
        if a.folder:
            lines = [oh.shown(line) for line in folder_record(reading, a.folder)]
        else:
            lines = page(reading, a.project, fold=not a.all, width=terminal_width())
        print("\n".join(lines))
        return 0
    except (oh.HelperError, ob.BaleError) as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError) as exc:
        log(f"error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
