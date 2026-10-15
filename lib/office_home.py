#!/usr/bin/env python3
"""The home screen: `office` on a terminal (0.22.0).

Walking in off a terminal prints the page and ends with its Next line
(bin/office walk_in; lib/office_bale.py next_move), for the scripts and
sessions that read it, and that is unchanged. On a terminal the same
facts are a home screen the occupant acts from: each project the office
scopes, one line each (what is in flight on it, or what last landed and
when), then what waits on him, each thing with a key. Choosing a key runs
the code the verb already runs, with its arguments filled in.

He never types a session id or a file name to act from it. The office
resolves them itself: the sessions from bale's records and the folders
that name them, the responses and the planner bundles from this machine's
downloads (machine.toml's `downloads`, the office's own setting). A
session is named by its folder (`folder 3, Fix the login`), or by its slug
when no folder records it; a bundle by its file's stem.

Two rules hold it to the doctrine (section 10):

- Whether a response has arrived is bale's to say. A file in the
  downloads is a file to offer, never a verdict: the home screen offers
  `office land` for it, and land asks bale.
- Whether a bundle was opened is read from bale's records, never guessed:
  a session's attempts carry the bundle it was opened from
  (attempts[].bundle.stem in its dossier). Only the sessions whose id
  carries the bundle's own slug are read, since bale mints a session's id
  from the slug its pack line gives.

The command line:

    office_home.py page OFFICE --today DAY --tz ZONE --skew S --founded yes|no
                        --menu-file FILE [--since DAY] [--dir DIR]... [--now ISO]
        the home screen's sections on stdout (Projects, Waiting on you, the
        keys), and the menu in FILE for bin/office: one line per key,
        KEY<tab>KIND<tab>ARG..., KIND office (ARGs are the office's
        argv), shell (one ARG, a command bash runs), note (ask for the
        line, then office note) or quit
    office_home.py bundles OFFICE [--dir DIR]... [--now ISO]
        the planner bundles in the downloads that no session opened, newest
        first, for office start's offer: PATH<tab>STEM<tab>AGE<tab>WORDS
    office_home.py copies --name NAME [--dir DIR]... [--now ISO]
        every browser copy of one name in the downloads, newest first:
        PATH<tab>AGE (office land's choice after a HOLD)
    office_home.py words --text-file FILE [--projects NAMES]
        what office open makes of the occupant's words: title, slug-from,
        goal and project lines, KEY<tab>VALUE

Standard library only. Logs on stderr with an [office] prefix; exits 0 on
success, 1 on a refusal, 2 on an internal error.
"""

import argparse
import datetime as dt
import os
import pathlib
import re
import shlex
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_bale as ob  # noqa: E402
import office_drop as odrop  # noqa: E402
import office_sort as osort  # noqa: E402

BUNDLE_EXT = ".bale-bundle"
# A bundle downloaded longer ago than this is not offered: a planner's
# bundle that waited two weeks unopened was withdrawn or replaced, and the
# home screen is for what waits now. office start --bundle still opens it.
RECENT_DAYS = 14
# The home screen's waiting list holds at most this many keyed things;
# the rest are counted, and office desk lists them.
MAX_ITEMS = 9
COPY_RE = re.compile(r" \(\d+\)$")


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- time, in words -----------------------------------------------------------------

def age_words(then, now):
    """How long ago, in plain words: `just now`, `12 minutes ago`, `3 hours
    ago`, `yesterday`, `4 days ago`."""
    secs = max(0, int((now - then).total_seconds()))
    if secs < 60:
        return "just now"
    if secs < 3600:
        n = secs // 60
        return f"{n} minute{'s' if n != 1 else ''} ago"
    if secs < 86400:
        n = secs // 3600
        return f"{n} hour{'s' if n != 1 else ''} ago"
    n = secs // 86400
    return "yesterday" if n == 1 else f"{n} days ago"


def local_day(stamp, tz):
    """The office's local date of a UTC stamp (bale's clock is UTC)."""
    when = ob.parse_stamp(stamp)
    if tz is not None:
        when = when.astimezone(tz)
    return when.strftime("%Y-%m-%d")


def zone(name):
    """The office's zone, or None (UTC) when it does not resolve here."""
    if not name:
        return None
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception as exc:  # ZoneInfoNotFoundError, ValueError: said, and UTC stands
        debug(f"the zone {name!r} does not resolve here ({exc}); dates are UTC")
        return None


def file_time(path):
    return dt.datetime.fromtimestamp(pathlib.Path(path).stat().st_mtime, dt.timezone.utc)


# --- naming a session the way the occupant knows it ----------------------------------

def slug_of(sid):
    """A session id's slug: YYYY-MM-DD-SLUG-NNN without its date and count."""
    return sid[11:-4] if oh.SID_RE.match(sid) else sid


class Names:
    """How the home screen names a session: by the folder that records it
    (`folder 3, Fix the login`), the standalone sort as the in-tray's, else
    by its slug. The folders are read once."""

    def __init__(self, office_root):
        self.naming = ob.folders_naming(office_root)
        self.folders = {}
        for f in oh.read_folders(office_root):
            if f["problem"] is None:
                self.folders[f["rel"]] = f

    def folder_words(self, rel):
        f = self.folders.get(rel)
        if f is None:
            return rel.split("/", 1)[-1]
        title = f.get("title") or f["name"]
        return f"{oh.cite(f)}, {title}" if f.get("number") else title

    def of(self, sid):
        rels = self.naming.get(sid) or []
        if rels:
            return self.folder_words(rels[0])
        if osort.is_sort_sid(sid):
            return "the in-tray's sort"
        return slug_of(sid)


# --- the projects, one line each -------------------------------------------------------

def landed_at(view):
    """When a session landed: its last applied attempt, else its record's
    last update."""
    stamps = [a["at"] for a in view["attempts"] if a["outcome"] == "applied" and a["at"]]
    return stamps[-1] if stamps else view["updated"]


def flight_words(rd, cwd, sid, read_only, names, now):
    """One session in flight, in words: its name, a sitting or held when it
    is, and how long ago it went out."""
    name = names.of(sid)
    try:
        d = rd.dossier(cwd, sid)
    except ob.BaleError as exc:
        debug(f"{sid}: its dossier could not be read for the home screen: {exc}")
        d = None
    if d is None:
        return f"{name}{', a sitting' if read_only else ''}"
    v = ob.session_view(rd, d)
    state = "a sitting, " if read_only else ("held by bale, " if v["in_flight"] and v["outcome"] == "held" else "")
    when = age_words(ob.parse_stamp(v["created"]), now) if v["created"] else "when, bale does not say"
    return f"{name} ({state}went out {when})"


def place_row(rd, cwd, names, now, tz):
    """(words, sessions) for one place the office reads: what is in flight
    there, or what last landed and when, or that nothing has. Raises
    BaleError when the place cannot be read."""
    opened = rd.open_sessions(cwd)
    if opened:
        first = flight_words(rd, cwd, opened[0][0], opened[0][1], names, now)
        more = f"; and {len(opened) - 1} more" if len(opened) > 1 else ""
        return f"in flight: {first}{more}", [sid for sid, _ in opened]
    latest = ob.applied_latest(rd, cwd)
    if not latest:
        return "nothing landed yet", []
    d = rd.dossier(cwd, latest)
    if d is None:
        return f"last landed: {names.of(latest)} (bale keeps no record of when)", []
    stamp = landed_at(ob.session_view(rd, d))
    if not stamp:
        return f"last landed: {names.of(latest)}", []
    return f"last landed: {names.of(latest)}, {local_day(stamp, tz)} ({age_words(ob.parse_stamp(stamp), now)})", []


def project_rows(rd, office_root, names, now, tz):
    """[(label, words)]: each project the office scopes, then the office
    itself when a session is open there. A project that cannot be read
    says why on its own line; the others are read all the same."""
    projects = ob.office_projects(office_root)
    rows = []
    if not projects:
        rows.append(("", "this office scopes no project yet"))
    for p in projects or []:
        try:
            words, _ = place_row(rd, ob.readable(p), names, now, tz)
        except ob.BaleError as exc:
            words = f"cannot be read: {exc}"
        rows.append((p["name"], words))
    own = ob.office_registry(office_root)
    if own is not None:
        try:
            if rd.open_sessions(own):
                words, _ = place_row(rd, own, names, now, tz)
                rows.append(("the office", words))
        except ob.BaleError as exc:
            rows.append(("the office", f"cannot be read: {exc}"))
    return rows


# --- planner bundles in the downloads, and whether one was opened ----------------------

def bundle_stem(name):
    """A bundle file's stem as bale records it (the name without .bale-bundle),
    a browser's ` (N)` copy suffix taken off: the copy is the same bundle."""
    stem = name[:-len(BUNDLE_EXT)] if name.endswith(BUNDLE_EXT) else name
    return COPY_RE.sub("", stem)


def downloaded_bundles(directories, now, days=RECENT_DAYS):
    """[{stem, path, at}] for the planner bundles in the downloads saved in
    the last `days` days, one per stem (its newest copy), newest first."""
    newest = {}
    for d in directories or []:
        d = pathlib.Path(os.path.expanduser(str(d)))
        try:
            entries = list(d.iterdir())
        except OSError as exc:
            debug(f"the downloads directory {d} cannot be read: {exc}")
            continue
        for f in entries:
            if not f.name.endswith(BUNDLE_EXT) or not f.is_file():
                continue
            at = file_time(f)
            if days is not None and (now - at).total_seconds() > days * 86400:
                continue
            stem = bundle_stem(f.name)
            if stem not in newest or at > newest[stem]["at"]:
                newest[stem] = {"stem": stem, "path": f.resolve(), "at": at}
    return sorted(newest.values(), key=lambda b: (-b["at"].timestamp(), b["stem"]))


def bundle_reading(path):
    """(slug, goal) of a bundle's stored pack line, read the way bale pack
    reads its flags; (None, None) when the office cannot read it."""
    argv = ob.bundle_pack_argv(path)
    if argv is None:
        return None, None
    try:
        parts = ob.bundle_argv_parts(argv)
    except ValueError as exc:
        debug(f"{path}: its pack line does not read ({exc})")
        return None, None
    slug = parts.slug[-1] if parts.slug else None
    return (oh.ascii_escape(slug)[0] if slug else None), parts.goal


def sid_for_slug(slug):
    return re.compile(r"^\d{4}-\d{2}-\d{2}-" + re.escape(slug) + r"-\d{3}$")


def every_place(office_root):
    """[(label, where)] for the office's own registry and each project it
    scopes that can be read; a project that cannot is said under
    OFFICE_DEBUG and skipped."""
    found, bad = ob.repos(office_root)
    for line in bad:
        debug(f"no bundle is looked for there: {line}")
    return [(label, cwd) for label, _, cwd in found]


def opened_from(rd, office_root, bundles):
    """Each bundle dict gains opened (the sid of a session bale records as
    opened from it, else None) and slug and goal (its pack line's, or None).
    Only the sessions whose id carries the bundle's slug are read, each
    through its dossier's attempts[].bundle.stem."""
    places = every_place(office_root) if bundles else []
    sids = {}
    for label, cwd in places:
        try:
            sids[label] = (cwd, rd.known_sids(cwd))
        except ob.BaleError as exc:
            debug(f"{label}: its sessions could not be listed, so no bundle is matched there: {exc}")
    for b in bundles:
        b["slug"], b["goal"] = bundle_reading(b["path"])
        b["opened"] = None
        if b["slug"] is None:
            continue
        pattern = sid_for_slug(b["slug"])
        for label, (cwd, known) in sids.items():
            for sid in known:
                if not pattern.match(sid):
                    continue
                try:
                    d = rd.dossier(cwd, sid)
                except ob.BaleError as exc:
                    debug(f"{sid}: its dossier could not be read, so whether it opened {b['stem']} is unknown: {exc}")
                    continue
                if d is not None and b["stem"] in [bundle_stem(x) for x in ob.bundle_stems(rd, d)]:
                    b["opened"] = sid
                    break
            if b["opened"]:
                break
    return bundles


def waiting_bundles(rd, office_root, directories, now):
    """The bundles in the downloads that no session opened, newest first."""
    return [b for b in opened_from(rd, office_root, downloaded_bundles(directories, now)) if not b["opened"]]


# --- what waits on him -----------------------------------------------------------------

def item(label, argv, kind="office"):
    return {"label": label, "argv": list(argv), "kind": kind}


def command_argv(command):
    """A Next line's command as (kind, argv): `office VERB ...` runs the
    office; anything else (the install's line) runs through bash. A word
    the Next line leaves for him to fill (`--lane LANE`) is left out: the
    verb asks it, by key."""
    if command.startswith("office "):
        argv = shlex.split(command)[1:]
        if "--lane" in argv and argv[argv.index("--lane") + 1:argv.index("--lane") + 2] == ["LANE"]:
            at = argv.index("--lane")
            argv = argv[:at] + argv[at + 2:]
        return "office", argv
    return "shell", [command]


def response_items(out, names, directories, now):
    """A land item for each session out whose response is in the downloads:
    a file to offer, never a verdict (land asks bale)."""
    items = []
    for s in out:
        name = f"response-{s['sid']}.tar.gz"
        copies = ob.browser_copies(directories or [], name)
        if not copies:
            continue
        where = "the office" if s["label"] == ob.OFFICE_LABEL else s["label"]
        saved = age_words(dt.datetime.fromtimestamp(copies[0][1] / 1e9, dt.timezone.utc), now)
        words = (f"Land {names.of(s['sid'])} ({where}) again: bale held it, and a response saved {saved} is in "
                 "your downloads" if s["held"] else
                 f"Land {names.of(s['sid'])} ({where}): a response for it was saved {saved} in your downloads")
        items.append(item(words, ["land", s["sid"]]))
    return items


def drop_items(groups, projects):
    names = [p["name"] for p in projects or []]
    out = []
    for d in groups.get("drops") or []:
        resolved = odrop.resolve_project(d.get("project"), names) if names else None
        for_whom = resolved or (f"for {d['project']!r}, no project of this office" if d.get("project") else "no project")
        out.append(item(f"Send out the drop \"{d['heading']}\" ({for_whom})", ["start", "--drop", d["rel"]]))
    return out


def home_items(skew, founded, out, groups, projects, slips, behind, bundles, names, directories, now, sittings=()):
    """The waiting list, in order: the Next line's move first (marked),
    then each response in the downloads, each unopened bundle, each
    unsorted drop and the sort, the desk moves, the office out of step
    with the install, and last each read-only sitting a folder records,
    which only he can say is over. A move already in the list is not
    repeated."""
    command, why = ob.next_move(skew, founded, out, groups, projects, slips, behind)
    kind, argv = command_argv(command)
    items = []
    if skew == "behind" and argv == ["upgrade"]:
        items.append(item(f"Upgrade this office to the installed office-src: {why}", argv))
    elif skew in ("ahead", "unreadable") and argv == ["status"]:
        items.append(item(f"See what is out of step: {why}", argv))
    items += response_items(out, names, directories, now)
    items += [item(f"Start the planner's bundle {b['stem']} (saved {age_words(b['at'], now)})",
                   ["start", "--bundle", str(b["path"])]) for b in bundles]
    items += drop_items(groups, projects)
    sort = ob.sort_move(groups.get("drops") or [], groups, projects)
    if sort is not None:
        items.append(item(f"Sort the in-tray: {sort[1]}", ["start", "--sort"]))
    count, sources, errors = groups.get("moves", (0, "", []))
    if count or errors:
        items.append(item(f"Apply the desk moves: {count} pending ({sources or 'none readable'})"
                          + (f", {len(errors)} line(s) that do not read" if errors else ""), ["moves"]))
    # A sitting lands nothing, and nothing in the office knows when it is
    # over (doctrine section 7): never the Next line, but a key that ends it.
    items += [item(f"End the sitting {names.of(s['sid'])} ({'the office' if s['label'] == ob.OFFICE_LABEL else s['label']}), "
                   "once it is over", ["land", s["sid"]]) for s in sittings]
    # The Next line's move, first: an item above when it is one, else its
    # own line in the Next line's words. "office open" and "office desk"
    # are the keys every screen has, so they are not repeated.
    nxt = next((i for i in items if i["argv"] == argv), None)
    if nxt is None and argv not in (["open"], ["desk"]):
        if argv and argv[0] == "land":
            sid = argv[1] if len(argv) > 1 else ""
            label = f"Land {names.of(sid)}: {why}" if sid else f"Land: {why}"
        elif argv and argv[0] == "start" and groups.get("ready") and argv[1:2] == [groups["ready"][0]["name"]]:
            label = f"Start {names.folder_words(groups['ready'][0]['rel'])}: {why}"
        elif argv and argv[0] == "start" and groups.get("open") and argv[1:2] == [groups["open"][0]["name"]]:
            label = f"Start {names.folder_words(groups['open'][0]['rel'])}: {why}"
        else:
            label = f"{why[:1].upper()}{why[1:]}"
        nxt = item(label, argv, kind)
        items.insert(0, nxt)
    elif nxt is not None:
        items.remove(nxt)
        items.insert(0, nxt)
    if nxt is not None:
        nxt["next"] = True
    return items


# --- the page ---------------------------------------------------------------------------

FIXED_KEYS = (
    ("o", "a new job", "office", ["open"]),
    ("s", "send a session out", "office", ["start"]),
    ("l", "bring one back", "office", ["land"]),
    ("n", "note a line", "note", []),
    ("d", "drop a message", "office", ["drop"]),
    ("k", "the whole desk", "office", ["desk"]),
    ("h", "help", "office", ["help"]),
    ("q", "leave", "quit", []),
)


def desk_words(groups):
    """The desk in one line: how many jobs are in flight, ready, parked and
    candidates, the ones there are."""
    parked = sum(len(v) for v in (groups.get("parked") or {}).values())
    counts = [(len(groups.get("flying") or []) + len(groups.get("open") or []), "in flight"),
              (len(groups.get("ready") or []), "ready"), (parked, "parked"),
              (len(groups.get("candidates") or []), "candidate(s)")]
    said = [f"{n} {what}" for n, what in counts if n]
    return ("On the desk: " + ", ".join(said) if said else "The desk is clear") + "; [k] shows every job."


def key_lines(keys, width=76):
    """The fixed keys, as few lines as fit the width."""
    lines, line = [], ""
    for k in keys:
        if line and len(line) + 3 + len(k) > width:
            lines.append(line)
            line = ""
        line = f"{line}   {k}" if line else k
    return [f"  {l}" for l in lines + ([line] if line else [])]


def render_page(rows, items, out_count, desk_line=None):
    """(lines, menu): the home screen below its heading lines, and the
    menu bin/office reads, one (key, kind, argv) per key."""
    lines = ["Projects:"]
    width = max((len(label) for label, _ in rows), default=0)
    for label, words in rows:
        lines.append(f"  {label.ljust(width)}  {words}" if label else f"  {words}")
    if desk_line:
        lines += ["", desk_line]
    lines += ["", "Waiting on you:"]
    menu = []
    shown = items[:MAX_ITEMS]
    if not shown:
        lines.append("  nothing waits on you")
    for n, it in enumerate(shown, 1):
        mark = "  (next)" if it.get("next") else ""
        lines.append(f"  [{n}] {it['label']}{mark}")
        menu.append((str(n), it["kind"], it["argv"]))
    if len(items) > MAX_ITEMS:
        lines.append(f"  and {len(items) - MAX_ITEMS} more: office desk lists the drops and the folders")
    keys = []
    for key, words, kind, argv in FIXED_KEYS:
        if key == "l" and not out_count:
            continue
        keys.append(f"[{key}] {words}")
        menu.append((key, kind, argv))
    lines += [""] + key_lines(keys)
    return lines, menu


def write_menu(path, menu):
    with open(path, "w", encoding="utf-8") as f:
        for key, kind, argv in menu:
            for word in argv:
                if "\t" in word or "\n" in word:
                    raise oh.HelperError(f"a menu word holds a tab or a line break: {word!r}")
            f.write("\t".join([key, kind, *argv]) + "\n")


def home(rd, office_root, today, since, skew, founded, tz_name, directories, now, menu_file):
    """The home screen's lines, and its menu written to menu_file."""
    tz = zone(tz_name)
    names = Names(office_root)
    groups = {}
    ob.render_desk(rd, office_root, today, since, walk_in=True, now=now, groups_out=groups)
    out, problems = ob.sessions_to_land(rd, office_root)
    for p in problems:
        debug(f"the home screen could not read every repo: {p}")
    try:
        behind = ob.install_behind(office_root)
    except (OSError, oh.HelperError) as exc:
        debug(f"the install could not be compared with its source: {exc}")
        behind = None
    projects = ob.office_projects(office_root)
    every, _ = ob.open_anywhere(rd, office_root)
    sittings = [x for x in every if x["read_only"] and x["folders"]]
    rows = project_rows(rd, office_root, names, now, tz)
    bundles = waiting_bundles(rd, office_root, directories, now) if directories else []
    items = home_items(skew, founded, out, groups, projects, ob.count_slips(office_root), behind, bundles, names,
                       directories, now, sittings)
    lines, menu = render_page(rows, items, len(out), desk_words(groups))
    if directories is None:
        lines.insert(lines.index("Waiting on you:") + 1,
                     "  (this machine's downloads are not set, so no response or bundle there is offered)")
    write_menu(menu_file, menu)
    return lines


# --- office open's reading of his words -------------------------------------------------

def words_reading(text, project_names):
    """What office open makes of the occupant's words: the title (the first
    line, trimmed as a drop's heading is, kept ASCII), the line the slug is
    made from (the first line as typed), the goal (every line as one, kept
    ASCII) and the project, when exactly one of the office's projects is
    named in them as a word."""
    text = odrop.normalize_text(text)
    if not text.strip():
        raise oh.HelperError("the words are empty")
    title = oh.ascii_escape(odrop.heading_text(text))[0]
    # Every line as one: a line that ends without its own stop is joined
    # to the next with a semicolon, so his sentences stay apart.
    said = [" ".join(l.split()) for l in text.splitlines() if l.strip()]
    goal = oh.ascii_escape(" ".join(l if l[-1] in ".!?;:," or i == len(said) - 1 else l + ";"
                                    for i, l in enumerate(said)))[0]
    # A goal is a word bale reads first: a leading dash or list marker
    # would read as a flag, so it is left off the goal (the Asked section
    # keeps the words as given).
    goal = goal.lstrip("-*+ ").strip() or goal
    named = [n for n in project_names
             if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", text, re.I)]
    return {"title": title, "slug-from": odrop.first_line(text), "goal": goal,
            "project": named[0] if len(named) == 1 else ""}


# --- the command line ------------------------------------------------------------------

def now_from(a):
    return ob.parse_stamp(a.now) if a.now else dt.datetime.now(dt.timezone.utc)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_home.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("page", help="the home screen's sections, and its menu into --menu-file")
    p.add_argument("office"); p.add_argument("--today", required=True); p.add_argument("--since")
    p.add_argument("--tz", default="")
    p.add_argument("--skew", choices=("current", "behind", "ahead", "unreadable"), default="current")
    p.add_argument("--founded", choices=("yes", "no"), default="yes")
    p.add_argument("--menu-file", required=True)
    p.add_argument("--dir", action="append", default=[], help="a downloads directory (repeatable)")
    p.add_argument("--no-downloads", action="store_true", help="machine.toml sets no downloads")
    p.add_argument("--now", help="an ISO timestamp to measure ages from (default: now)")
    p = sub.add_parser("bundles", help="the bundles in the downloads no session opened: PATH, STEM, AGE, WORDS")
    p.add_argument("office"); p.add_argument("--dir", action="append", default=[]); p.add_argument("--now")
    p = sub.add_parser("copies", help="every browser copy of a name in the downloads, newest first: PATH, AGE")
    p.add_argument("--name", required=True); p.add_argument("--dir", action="append", default=[])
    p.add_argument("--now")
    p = sub.add_parser("bundle-goal", help="a bundle's goal, from its stored pack line: the planner's words")
    p.add_argument("--bundle", required=True)
    p = sub.add_parser("words", help="office open's reading of the occupant's words: KEY<tab>VALUE")
    p.add_argument("--text-file", required=True)
    p.add_argument("--projects", default="", help="the floor plan's project names, one per line")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "words":
            raw = pathlib.Path(a.text_file).read_bytes().decode("utf-8", "surrogateescape")
            got = words_reading(raw, [n for n in a.projects.splitlines() if n.strip()])
            for key in ("title", "slug-from", "goal", "project"):
                print(f"{key}\t{got[key]}")
            return 0
        if a.cmd == "bundle-goal":
            _, goal = bundle_reading(a.bundle)
            if not goal:
                log(f"error: {a.bundle}: no goal the office can read in its pack line")
                return 1
            print(goal)
            return 0
        now = now_from(a)
        if a.cmd == "copies":
            for path, ns in ob.browser_copies(a.dir, a.name):
                print(f"{path}\t{age_words(dt.datetime.fromtimestamp(ns / 1e9, dt.timezone.utc), now)}")
            return 0
        rd = ob.Reader()
        if a.cmd == "bundles":
            for b in waiting_bundles(rd, a.office, a.dir, now):
                words = " ".join((b["goal"] or "").split())
                print(f"{b['path']}\t{b['stem']}\t{age_words(b['at'], now)}\t{oh.ascii_escape(words)[0]}")
            return 0
        dt.date.fromisoformat(a.today)
        if a.since:
            dt.date.fromisoformat(a.since)
        lines = home(rd, a.office, a.today, a.since, a.skew, a.founded == "yes", a.tz,
                     None if a.no_downloads else a.dir, now, a.menu_file)
        print("\n".join(lines))
        return 0
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except ob.BaleError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError) as exc:
        log(f"error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
