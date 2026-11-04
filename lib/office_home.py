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
    office_home.py withdraw-bundle OFFICE --stem STEM [--dir DIR]... [--check]
        office withdraw --bundle STEM (0.41.0): every copy of the stem in
        the downloads renamed NAME.bale-bundle.declined, one line each;
        --check prints the stem and the copies, or refuses
    office_home.py responses [--dir DIR]... [--sid SID]...
        of the sessions named, those whose response-SID.tar.gz is in the
        downloads (0.44.0): SID<tab>PATH, its newest copy; office land's
        bare reading of which session lands
    office_home.py tray OFFICE --tray-root DIR [--sid SID | --folder REL]
        office tray (0.46.0): the out tray to open again, KEY<tab>VALUE
        lines: sid, path, one file per line, and opener (the copy of the
        opener start keeps beside the tray, or nothing)
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
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

BUNDLE_EXT = ".bale-bundle"
# A bundle downloaded longer ago than this is not offered: a planner's
# bundle that waited two weeks unopened was withdrawn or replaced, and the
# home screen is for what waits now. office start --bundle still opens it.
RECENT_DAYS = 14
# The home screen's first keys are the digits 1 to 9 (MAX_ITEMS); since
# 0.46.0 every item past them takes a letter no fixed key takes
# (item_keys), so nothing it lists goes without a key.
MAX_ITEMS = 9
COPY_RE = oh.LazyPattern(r" \(\d+\)$")


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
    import office_bale as ob
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
        import office_bale as ob
        self.root = office_root
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
        import office_sort as osort
        import office_meeting as om
        rels = self.naming.get(sid) or []
        if rels:
            return self.folder_words(rels[0])
        if osort.is_sort_sid(sid):
            return "the in-tray's sort"
        try:
            prep = om.prep_of(self.root, sid)
        except (OSError, oh.HelperError) as exc:
            debug(f"the calendar could not be read to name {sid}: {exc}")
            prep = None
        if prep:
            return f"the prep for {prep['title']}"
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
    import office_bale as ob
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
    import office_bale as ob
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


def project_rows(rd, office_root, names, now, tz, reviews=None):
    """[(label, words)]: each project the office scopes, then the office
    itself when a session is open there. A project that cannot be read
    says why on its own line; the others are read all the same. reviews
    (0.42.0; office_review.office_reviews, read once with the desk) adds
    each project's review state after what is in flight on it."""
    import office_bale as ob
    import office_review as orev
    said = {got["name"]: orev.project_words(got, cites=False) for got in reviews or []}
    projects = ob.office_projects(office_root)
    rows = []
    if not projects:
        rows.append(("", "this office scopes no project yet"))
    for p in projects or []:
        try:
            words, _ = place_row(rd, ob.rendered(p), names, now, tz)
        except ob.BaleError as exc:
            # A paused project (0.41.0) is read for nothing: its row says so.
            words = (f"paused (office projects set {p['name']} --unpaused)" if exc.kind == "paused"
                     else f"cannot be read: {exc}")
        if p["name"] in said:
            words += f"; reviews: {said[p['name']]}"
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
    """[{stem, path, at, copies}] for the planner bundles in the downloads
    saved in the last `days` days, one per stem (its newest copy), newest
    first; copies (0.41.0) counts every copy of the stem the downloads hold,
    whatever its age, so the offer can say when there are two. A bundle
    withdrawn from the offer (office withdraw --bundle) is named
    NAME.bale-bundle.declined, and is no bundle here."""
    newest, copies = {}, {}
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
            stem = bundle_stem(f.name)
            copies[stem] = copies.get(stem, 0) + 1
            if days is not None and (now - at).total_seconds() > days * 86400:
                continue
            if stem not in newest or at > newest[stem]["at"]:
                newest[stem] = {"stem": stem, "path": f.resolve(), "at": at}
    for b in newest.values():
        b["copies"] = copies.get(b["stem"], 1)
    return sorted(newest.values(), key=lambda b: (-b["at"].timestamp(), b["stem"]))


def saved_words(b, now):
    """How a bundle's offer says when it was saved: `saved AGE`, and when
    the downloads hold more than one copy of its stem (0.41.0), how many,
    the newest offered."""
    words = f"saved {age_words(b['at'], now)}"
    if b.get("copies", 1) > 1:
        words += f"; {b['copies']} copies, the newest offered"
    return words


def bundle_copies(directories, stem):
    """Every copy of a bundle's stem in the downloads (STEM.bale-bundle and
    a browser's `STEM (N).bale-bundle`), each a Path, sorted by name; a
    withdrawn copy (.declined) is not one."""
    stem = bundle_stem(stem.removesuffix(BUNDLE_EXT))
    out = []
    for d in directories or []:
        d = pathlib.Path(os.path.expanduser(str(d)))
        try:
            entries = list(d.iterdir())
        except OSError as exc:
            debug(f"the downloads directory {d} cannot be read: {exc}")
            continue
        out += [f for f in entries if f.is_file() and f.name.endswith(BUNDLE_EXT) and bundle_stem(f.name) == stem]
    return sorted(out, key=lambda f: (str(f.parent), f.name))


def downloaded_stems(directories):
    """The stems the downloads hold a bundle of, any age, sorted."""
    return sorted({b["stem"] for b in downloaded_bundles(directories, dt.datetime.now(dt.timezone.utc), days=None)})


DECLINED_EXT = ".declined"


def withdraw_bundle_check(rd, office_root, directories, stem):
    """(stem, the copies) for office withdraw --bundle STEM (0.41.0): STEM as
    the home screen names it, with or without .bale-bundle. Refuses (a
    HelperError) a stem no file in the downloads carries, naming the stems
    they hold, and a bundle a session opened (bale's records say), naming
    the session."""
    stem = bundle_stem(stem.strip().removesuffix(BUNDLE_EXT))
    found = bundle_copies(directories, stem)
    if not found:
        held = downloaded_stems(directories)
        raise oh.HelperError(f"no bundle named {stem} is in your downloads (they hold: {', '.join(held) or 'none'}); "
                             "nothing was renamed")
    newest = max(found, key=lambda f: f.stat().st_mtime)
    b = opened_from(rd, office_root, [{"stem": stem, "path": newest.resolve(), "at": file_time(newest)}])[0]
    if b["opened"]:
        raise oh.HelperError(f"{stem} was opened by {b['opened']}, so it is not in the offer; the session is office "
                             f"land's, or office withdraw {b['opened']}'s if it was never worked")
    return stem, found


def withdraw_bundle(found):
    """Rename each copy NAME.bale-bundle to NAME.bale-bundle.declined, the
    only thing the office ever writes in the downloads, and nothing is
    deleted there. Returns the line said for each."""
    lines = []
    for f in found:
        target = f.with_name(f.name + DECLINED_EXT)
        if target.exists():
            raise oh.HelperError(f"{target} is there already, so {f} was not renamed (rename or move one of them "
                                 "by hand)")
        f.rename(target)
        lines.append(f"{f} is now {target.name}: the home screen and office start no longer offer it (rename it "
                     "back to offer it again)")
    return lines


def bundle_reading(path):
    """(slug, goal) of a bundle's stored pack line, read the way bale pack
    reads its flags; (None, None) when the office cannot read it."""
    import office_bale as ob
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
    OFFICE_DEBUG and skipped. A paused project is read here too (0.46.0):
    which bundle one of its sessions opened is the one thing the home
    screen and bare start read of it (one status call per screen), so a
    bundle opened there leaves the offer as any other."""
    import office_bale as ob
    found, bad = ob.repos(office_root, rendering=False)
    for line in bad:
        debug(f"no bundle is looked for there: {line}")
    return [(label, cwd) for label, _, cwd in found]


def opened_from(rd, office_root, bundles):
    """Each bundle dict gains opened (the sid of a session bale records as
    opened from it, else None) and slug and goal (its pack line's, or None).
    Only the sessions whose id carries the bundle's slug are read, each
    through its dossier's attempts[].bundle.stem."""
    import office_bale as ob
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


# --- the other offices on this machine (0.44.0) ------------------------------------------
#
# Two offices may share one occupant and one downloads directory, and a
# bundle or a response for either lands there. machine.toml's offices lists
# them (lib/office_helper.py OFFICES_KEY); each office's home screen and
# walk-in show, after their own sections, what waits for each other office,
# read from that office's bale registry (its own, and its projects') and
# the downloads alone, never its desk, notepad or handbook, and a key runs
# the verb there, as if typed there (OFFICE_ROOT=ROOT office VERB).

ELSEWHERE = "elsewhere"


def other_offices(office_root, machine_file):
    """[(root, name)] of the offices machine.toml lists other than this
    one, and the lines for listed roots that are no longer offices (said
    under OFFICE_DEBUG by the caller, skipped)."""
    if not machine_file:
        return [], []
    try:
        found, skipped = oh.listed_offices(machine_file)
    except oh.HelperError as exc:
        return [], [str(exc)]
    me = os.path.realpath(office_root)
    return [(r, n) for r, n in found if r != me], skipped


def scoped_by(root):
    """The project names an office's floor plan scopes ([] when none, or
    when it does not read)."""
    import office_bale as ob
    try:
        return [p["name"] for p in ob.office_projects(root) or []]
    except (OSError, oh.HelperError) as exc:
        debug(f"{root}: its projects could not be read: {exc}")
        return []


def bundle_lands_project(path):
    """The project a bundle's brief's LANDS line names, or None (no brief,
    no LANDS line, or the office)."""
    import office_bale as ob
    text = ob.bundle_brief(path)
    if text is None:
        return None
    mark, _ = oh.brief_lands(text)
    if mark is None or mark["place"] == "office":
        return None
    return mark["place"]


def cut_by_office(rd, office_root, bundles, others):
    """(here, there, nowhere) of the bundles this office's own reading left
    waiting (0.44.0): a bundle any other listed office's registry records
    as opened leaves every offer; one whose LANDS line names a project this
    office does not scope leaves this office's and goes, in there (root ->
    [bundles]), to each listed office that scopes it, or, when none does,
    to nowhere. The rest are here."""
    for root, name in others:
        left = [b for b in bundles if not b.get("opened")]
        if not left:
            break
        copies = [dict(b) for b in left]
        try:
            opened_from(rd, root, copies)
        except Exception as exc:  # one office that cannot be read never takes the screen down
            debug(f"{name}: whether it opened a bundle could not be read: {exc}")
            continue
        for b, c in zip(left, copies):
            if c.get("opened"):
                b["opened"], b["opened_in"] = c["opened"], name
    mine = set(scoped_by(office_root))
    scopes = {root: set(scoped_by(root)) for root, _ in others}
    here, there, nowhere = [], {}, []
    for b in bundles:
        if b.get("opened"):
            continue
        project = bundle_lands_project(b["path"])
        if project is None or project in mine:
            here.append(b)
            continue
        homes = [root for root, _ in others if project in scopes[root]]
        b["lands_on"] = project
        if not homes:
            nowhere.append(b)
        for root in homes:
            there.setdefault(root, []).append(b)
    return here, there, nowhere


def nowhere_line(nowhere):
    """The one line for the bundles that land on projects no office on
    this machine scopes, or None."""
    if not nowhere:
        return None
    stems = ", ".join(b["stem"] for b in nowhere)
    return (f"{len(nowhere)} bundle(s) in your downloads land on projects no office on this machine scopes: "
            f"{stems}; office withdraw --bundle {nowhere[0]['stem']} takes one out of the offer")


def elsewhere_item(root, label, argv):
    """A waiting item that runs its verb in another office: the menu's kind
    elsewhere, the office's root its first word."""
    return {"label": label, "argv": [root, *argv], "kind": ELSEWHERE}


def elsewhere_line(it):
    """An elsewhere item as the line to type, for the walk-in page."""
    import shlex
    root, *argv = it["argv"]
    return f"OFFICE_ROOT={shlex.quote(root)} office " + " ".join(shlex.quote(w) for w in argv)


def office_section(rd, root, name, directories, now, bundles):
    """(heading, lines, items) for one other office: the responses in the
    downloads for the sessions it or its projects have out, the bundles
    cut to it, and the sittings out there, each a key that runs the verb
    there. Read from its bale registries and the downloads alone; an
    office that cannot be read is one line under its heading."""
    import office_bale as ob
    heading = f"{name} ({root})"
    try:
        found, bad = ob.repos(root, rendering=True)
    except (OSError, oh.HelperError) as exc:
        return heading, [f"cannot be read: {exc}"], []
    items, lines, sittings = [], [], []
    for line in bad:
        debug(f"{name}: {line}")
    for label, _, cwd in found:
        try:
            opened = rd.open_sessions(cwd)
        except ob.BaleError as exc:
            lines.append(f"{label if label != ob.OFFICE_LABEL else 'the office'}: cannot be read: {exc}")
            continue
        where = "the office" if label == ob.OFFICE_LABEL else label
        for sid, read_only in opened:
            if read_only:
                sittings.append((sid, where))
                continue
            copies = ob.browser_copies(directories or [], f"response-{sid}.tar.gz")
            if copies:
                saved = age_words(dt.datetime.fromtimestamp(copies[0][1] / 1e9, dt.timezone.utc), now)
                items.append(elsewhere_item(root, f"Land {slug_of(sid)} ({where}, in {name}): a response for it was "
                                                  f"saved {saved} in your downloads", ["land", sid]))
    for b in bundles:
        items.append(elsewhere_item(root, f"Start the planner's bundle {b['stem']} in {name} (it lands on "
                                          f"{b['lands_on']}; {saved_words(b, now)})", ["start", "--bundle", str(b["path"])]))
    for sid, where in sittings:
        items.append(elsewhere_item(root, f"End the sitting {slug_of(sid)} ({where}, in {name}), once it is over",
                                    ["land", sid]))
    if sittings:
        items.append(elsewhere_item(root, f"Run the probe on the clipboard in {name}", ["probe"]))
    return heading, lines, items


def other_sections(rd, office_root, machine_file, directories, now, bundles=None):
    """(sections, nowhere line, the bundles left here) for the home screen
    and the walk-in: one (heading, lines, items) per other listed office,
    in machine.toml's order. bundles are this office's waiting bundles,
    cut by office (cut_by_office); None reads them from the downloads."""
    others, skipped = other_offices(office_root, machine_file)
    for why in skipped:
        debug(why)
    if bundles is None:
        bundles = waiting_bundles(rd, office_root, directories, now) if directories else []
    here, there, nowhere = cut_by_office(rd, office_root, bundles, others)
    sections = [office_section(rd, root, name, directories, now, there.get(root, [])) for root, name in others]
    return sections, nowhere_line(nowhere), here


# --- what waits on him -----------------------------------------------------------------

def item(label, argv, kind="office"):
    return {"label": label, "argv": list(argv), "kind": kind}


def command_argv(command):
    """A Next line's command as (kind, argv): `office VERB ...` runs the
    office; anything else (the install's line) runs through bash. A word
    the Next line leaves for him to fill (`--lane LANE`) is left out: the
    verb asks it, by key."""
    import shlex
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
    import office_bale as ob
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
    import office_drop as odrop
    names = [p["name"] for p in projects or []]
    out = []
    for d in groups.get("drops") or []:
        resolved = odrop.resolve_project(d.get("project"), names) if names else None
        for_whom = resolved or (f"for {d['project']!r}, no project of this office" if d.get("project") else "no project")
        out.append(item(f"Send out the drop \"{d['heading']}\" ({for_whom})", ["start", "--drop", d["rel"]]))
    return out


def sitting_item_words(s, names):
    """The home screen's words for a read-only sitting out: the key that
    ends it, then what is known of it, each after a semicolon: out under an
    older doctrine (0.33.0), where it stands, from its folder's standing
    (0.43.0), and last an older sitting on its folder (0.43.0)."""
    import office_bale as ob
    where = "the office" if s["label"] == ob.OFFICE_LABEL else s["label"]
    words = f"End the sitting {names.of(s['sid'])} ({where}), once it is over"
    if s.get("stale"):
        words += f"; it is {s['stale']}"
    if s.get("standing"):
        words += f"; {s['standing']}"
    # Last, as the brief says the item ends (0.43.0).
    if s.get("older"):
        words += f"; {ob.OLDER_SITTING_WORDS}"
    return words


def home_items(skew, founded, out, groups, projects, slips, behind, bundles, names, directories, now, sittings=(),
               meetings=(), cache=None):
    """The waiting list, in order: the Next line's move first (marked),
    then each meeting near now whose prep is still to send (0.26.0), each
    response in the downloads, each unopened bundle, each unsorted drop
    and the sort, the desk moves, the office out of step with the
    install, and last each read-only sitting a folder records and each
    meeting's prep that is out, which only he can say is over. A move
    already in the list is not repeated."""
    import office_bale as ob
    import office_meeting as om
    command, why = ob.next_move(skew, founded, out, groups, projects, slips, behind, cache)
    kind, argv = command_argv(command)
    items = []
    if skew == "behind" and argv == ["upgrade"]:
        items.append(item(f"Upgrade this office to the installed office-src: {why}", argv))
    elif skew in ("ahead", "unreadable") and argv == ["status"]:
        items.append(item(f"See what is out of step: {why}", argv))
    # A meeting near now (lib/office_meeting.py NEAR_BEFORE, NEAR_AFTER):
    # its prep, by key, never the Next line (a meeting is not a job).
    items += [item(f"Send the prep for {om.occurrence_words(m)}: it briefs you on what landed since the last one",
                   ["start", "--prep", m["key"]]) for m in meetings if m["state"] == "due"]
    items += response_items(out, names, directories, now)
    # A merge job waiting for its session, then the folders whose work landed
    # and is not delivered, newest landing first (0.41.0): read once, by
    # render_desk, into the desk's groups.
    items += [item(ob.merge_item_words(m), ["start", ob.folder_key(m["folder"]), "--merge"])
              for m in groups.get("merges") or [] if not m["landed"]]
    items += [item(ob.deliver_item_words(u), ["deliver", ob.folder_key(u["folder"])])
              for u in groups.get("undelivered") or []]
    items += [item(f"Start the planner's bundle {b['stem']} ({saved_words(b, now)})",
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
    # One out under an older doctrine says so (0.33.0), its stale key set
    # by home() from the folder's Sessions line; one that is not the newest
    # open on its folder says so (0.43.0, older), and where it stands when
    # its folder has a standing (0.43.0, standing), with a second key that
    # files a new one from the clipboard (office standing FOLDER).
    for s in sittings:
        items.append(item(sitting_item_words(s, names), ["land", s["sid"]]))
        if s.get("standing_key"):
            items.append(item(f"File where {names.of(s['sid'])} stands now, from the sitting's last standing block "
                              "on the clipboard", ["standing", s["standing_key"]]))
    items += [item(f"End the prep for {m['title']} once the meeting is over: land records it held and files what "
                   "arose", ["land", m["sid"]]) for m in meetings if m["state"] == "prep out"]
    # The Next line's move, first: an item above when it is one, else its
    # own line in the Next line's words. "office start new" and "office
    # desk" are the keys every screen has, so they are not repeated.
    nxt = next((i for i in items if i["argv"] == argv), None)
    if nxt is None and argv not in (["start", "new"], ["desk"]):
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
    ("o", "a new job, in your words", "office", ["start", "new"]),
    # The map (0.46.0): every project with its facts and its folders.
    ("a", "the map: every project and its folders", "office", ["map"]),
    # A planner sitting from his words (0.24.0): what he wants a planner
    # for, and nothing else; its folder is minted from his words, as the o
    # key's is (office start --planner offers the desk's folders by key).
    ("p", "a planner sitting, in your words", "office", ["start", "new", "--planner"]),
    # A meeting, said once in his words (0.26.0): when, and what it is about.
    ("m", "a meeting, in your words", "office", ["meeting"]),
    ("s", "send a session out", "office", ["start"]),
    ("l", "bring one back", "office", ["land"]),
    # Shown only while a session is out that was never worked (0.24.0), or a
    # bundle no session opened waits in the offer (0.41.0).
    ("w", "withdraw a session never worked, or a bundle", "office", ["withdraw"]),
    # Shown only while a folder on the desk records a session open where
    # probes run (0.44.0): the block on the clipboard, its run line saying
    # the rest (office probe reads the block first when no folder is named).
    ("r", "run the probe on the clipboard", "office", ["probe"]),
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


def item_keys(count):
    """The keys of the first count items (0.46.0): 1 to 9, then the
    lowercase letters no fixed key takes, then the capitals; one keypress
    each, as read_key reads them. None past the last of them."""
    import string
    taken = {k for k, *_ in FIXED_KEYS}
    keys = [str(n) for n in range(1, MAX_ITEMS + 1)]
    keys += [c for c in string.ascii_lowercase if c not in taken] + list(string.ascii_uppercase)
    return [keys[i] if i < len(keys) else None for i in range(count)]


def render_page(rows, items, out_count, desk_line=None, withdrawable=0, probe_ready=False, others=(),
                nowhere=None):
    """(lines, menu): the home screen below its heading lines, and the
    menu bin/office reads, one (key, kind, argv) per key. The l key shows
    only while a session is out, the w key only while one is out that can
    be withdrawn (withdrawable, a count: no response, no apply begun), and
    the r key (0.44.0) only while a folder on the desk records a session
    open where probes run (probe_ready). others (0.44.0) are the other
    offices on this machine, each (heading, lines, items), shown after
    this office's own sections; their items share the numbered keys.
    nowhere is the one line for the bundles no office scopes."""
    lines = ["Projects:"]
    width = max((len(label) for label, _ in rows), default=0)
    for label, words in rows:
        lines.append(f"  {label.ljust(width)}  {words}" if label else f"  {words}")
    if desk_line:
        lines += ["", desk_line]
    lines += ["", "Waiting on you:"]
    menu = []
    # Every item has a key (0.46.0): this office's, then each other
    # office's, numbered on from one another, 1 to 9 and then letters.
    keys = item_keys(len(items) + sum(len(theirs) for _, _, theirs in others))
    at = 0

    def keyed(it, mark=""):
        nonlocal at
        key = keys[at]
        at += 1
        if key is None:  # past every key a keypress can be: said, never silent
            return False
        lines.append(f"  [{key}] {it['label']}{mark}")
        menu.append((key, it["kind"], it["argv"]))
        return True

    if not items:
        lines.append("  nothing waits on you")
    for it in items:
        keyed(it, "  (next)" if it.get("next") else "")
    if nowhere:
        lines.append(f"  {nowhere}")
    for heading, said, theirs in others:
        lines += ["", f"{heading}:"]
        lines += [f"  {l}" for l in said]
        for it in theirs:
            keyed(it)
        if not said and not theirs:
            lines.append("  nothing waits on you there")
    if at > len([k for k in keys if k]):
        lines.append(f"  and {at - len([k for k in keys if k])} more than there are keys: office desk lists them")
    keys = []
    for key, words, kind, argv in FIXED_KEYS:
        if key == "l" and not out_count:
            continue
        if key == "w" and not withdrawable:
            continue
        if key == "r" and not probe_ready:
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


def home(rd, office_root, today, since, skew, founded, tz_name, directories, now, menu_file, machine_file=None):
    """The home screen's lines, and its menu written to menu_file. With
    machine_file (0.44.0), the other offices it lists get a section each
    after this office's own, and the bundle offer is cut by office."""
    import office_bale as ob
    import office_meeting as om
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
    try:
        cache = ob.bytecode_behind()
    except (OSError, oh.HelperError) as exc:
        debug(f"the install's bytecode cache could not be checked: {exc}")
        cache = None
    projects = ob.office_projects(office_root)
    every, _ = ob.open_anywhere(rd, office_root, rendering=True)
    sittings = [x for x in every if x["read_only"] and x["folders"]]
    doctrines = ob.Doctrines(office_root)
    older = ob.older_sittings(office_root, [(s["sid"], s["folders"]) for s in sittings])
    for s in sittings:
        s["stale"] = doctrines.older(s["sid"])
        s["older"] = s["sid"] in older
        s["standing"] = ob.standing_words(office_root, s["folders"], s["sid"])
        # The key that files a new standing (0.43.0): the sitting's folder on
        # the desk, by its number, offered beside the item.
        desk = [names.folders[r] for r in s["folders"] if r.startswith("desk/") and r in names.folders]
        # From the sitting's first turn (0.44.0), standing filed or not: a
        # turn that ends in no probe has no other way to the office.
        s["standing_key"] = ob.folder_key(desk[0]) if desk else None
    rows = project_rows(rd, office_root, names, now, tz, groups.get("reviews"))
    bundles = waiting_bundles(rd, office_root, directories, now) if directories else []
    others, nowhere, bundles = other_sections(rd, office_root, machine_file, directories, now, bundles)
    try:
        meetings = om.near(office_root, tz or dt.timezone.utc, now)
    except (OSError, ValueError, oh.HelperError) as exc:
        debug(f"the calendar could not be read for the meetings near now: {exc}")
        meetings = []
    items = home_items(skew, founded, out, groups, projects, ob.count_slips(office_root), behind, bundles, names,
                       directories, now, sittings, meetings, cache)
    # The out trays to open again (0.46.0): one per session out whose
    # response is not in the downloads and whose tray is still there.
    items += tray_items(every, names, directories, tray_root_of(machine_file))
    # The sessions out that were never worked: the w key's (office withdraw).
    try:
        offered, _, _ = ob.withdraw_view(rd, office_root, directories)
    except ob.BaleError as exc:
        debug(f"which sessions could be withdrawn could not be read: {exc}")
        offered = []
    # The r key (0.44.0): a folder on the desk records a session open where
    # probes run (office_bale.probe_folders' rule, from the same reading).
    probe_ready = any(r.startswith("desk/") for x in every for r in x["folders"])
    lines, menu = render_page(rows, items, len(out), desk_words(groups), len(offered) + len(bundles), probe_ready,
                              others, nowhere)
    if directories is None:
        lines.insert(lines.index("Waiting on you:") + 1,
                     "  (this machine's downloads are not set, so no response or bundle there is offered)")
    write_menu(menu_file, menu)
    return lines


# --- the out tray, opened again (0.46.0) -----------------------------------------------
#
# office start fills a session's out tray at OUT_TRAY/SID (machine.toml's
# out_tray, default ~/out-tray; SID-2 when the name is taken) and, since
# 0.46.0, keeps the opener it printed beside the tray, as SID.opener.txt,
# outside the tray so "attach every file in the out tray" stays true.
# office tray reads both back; it writes nothing.

OPENER_SUFFIX = ".opener.txt"


def tray_root_of(machine_file):
    """The out tray's root: machine.toml's out_tray, else ~/out-tray."""
    value = None
    if machine_file:
        try:
            value = oh.machine_string(machine_file, "out_tray")
        except (OSError, oh.HelperError) as exc:
            debug(f"out_tray in {machine_file} does not read, so the default is used: {exc}")
    return pathlib.Path(os.path.expanduser(value or "~/out-tray"))


def tray_dir(tray_root, sid):
    """The out tray start filled for sid: OUT_TRAY/SID, else the newest
    SID-N beside it; None when there is none."""
    root = pathlib.Path(tray_root)
    exact = root / sid
    if exact.is_dir():
        return exact
    others = [d for d in root.glob(f"{sid}-*") if d.is_dir() and d.name[len(sid) + 1:].isdigit()]
    return max(others, key=lambda d: int(d.name[len(sid) + 1:])) if others else None


def opener_copy(tray):
    """The copy of the opener kept beside a tray, or None."""
    path = pathlib.Path(tray).with_name(pathlib.Path(tray).name + OPENER_SUFFIX)
    return path if path.is_file() else None


def tray_items(every, names, directories, tray_root):
    """A home screen item per session out (one a folder records, or the
    in-tray's sort) whose response is not in the downloads and whose out
    tray is still there: its key runs office tray SID."""
    import office_bale as ob
    import office_sort as osort
    items = []
    for x in every:
        if not (x["folders"] or (x["label"] == ob.OFFICE_LABEL and osort.is_sort_sid(x["sid"]))):
            continue
        if not x["read_only"] and ob.browser_copies(directories or [], f"response-{x['sid']}.tar.gz"):
            continue
        if tray_dir(tray_root, x["sid"]) is None:
            continue
        items.append(item(f"Open the out tray for {names.of(x['sid'])} again (its files and opener)",
                          ["tray", x["sid"]]))
    return items


def tray_reading(rd, office_root, tray_root, sid=None, folder=None):
    """(sid, tray, opener copy or None) for office tray: the session named,
    the newest a folder records, or the newest session out from this
    office with a tray. Refuses (HelperError) when there is none."""
    import office_bale as ob
    if sid:
        tray = tray_dir(tray_root, sid)
        if tray is None:
            raise oh.HelperError(f"no out tray for {sid} in {tray_root} (office start fills one there; a tray "
                                 "moved or deleted is gone)")
        return sid, tray, opener_copy(tray)
    if folder:
        recorded = [s for s, _ in oh.folder_session_lines(pathlib.Path(office_root) / folder / "folder.md")]
        for s in reversed(recorded):
            tray = tray_dir(tray_root, s)
            if tray is not None:
                return s, tray, opener_copy(tray)
        raise oh.HelperError(f"{folder} records {'no session' if not recorded else 'no session with an out tray in ' + str(tray_root)}"
                             " (office start FOLDER sends one out)")
    every, problems = ob.open_anywhere(rd, office_root, rendering=True)
    for line in problems:
        debug(f"office tray could not read every repo: {line}")
    found = []
    for x in every:
        tray = tray_dir(tray_root, x["sid"])
        if tray is not None and (x["folders"] or x["label"] == ob.OFFICE_LABEL):
            found.append((tray.stat().st_mtime, x["sid"], tray))
    if not found:
        raise oh.HelperError(f"no session out from this office has an out tray in {tray_root} (office tray SID "
                             "opens an older session's)")
    _, s, tray = max(found)
    return s, tray, opener_copy(tray)


# --- office open's reading of his words -------------------------------------------------

def words_reading(text, project_names):
    """What office open makes of the occupant's words: the title (the first
    line, trimmed as a drop's heading is, kept ASCII), the line the slug is
    made from (the first line as typed), the goal (every line as one, kept
    ASCII) and the project, when exactly one of the office's projects is
    named in them as a word."""
    import office_drop as odrop
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
    import office_bale as ob
    return ob.parse_stamp(a.now) if a.now else dt.datetime.now(dt.timezone.utc)


def main(argv=None):
    import office_bale as ob
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
    p.add_argument("--machine-file", help="machine.toml: its offices get a section each (0.44.0)")
    p = sub.add_parser("elsewhere", help="the walk-in's sections for the other offices machine.toml lists (0.44.0)")
    p.add_argument("office"); p.add_argument("--machine-file", required=True)
    p.add_argument("--dir", action="append", default=[]); p.add_argument("--now")
    p = sub.add_parser("bundles", help="the bundles in the downloads no session opened: PATH, STEM, AGE, WORDS")
    p.add_argument("office"); p.add_argument("--dir", action="append", default=[]); p.add_argument("--now")
    p.add_argument("--machine-file", help="machine.toml: the offer cut by office (0.44.0)")
    p = sub.add_parser("withdraw-bundle", help="office withdraw --bundle STEM: rename every copy of the stem in the "
                                               "downloads to NAME.bale-bundle.declined (--check: the stem and the "
                                               "copies, or the refusal)")
    p.add_argument("office"); p.add_argument("--stem", required=True); p.add_argument("--dir", action="append", default=[])
    p.add_argument("--check", action="store_true"); p.add_argument("--now")
    p = sub.add_parser("tray", help="office tray (0.46.0): the out tray to open again: sid, path, files, opener")
    p.add_argument("office"); p.add_argument("--tray-root", required=True)
    p.add_argument("--sid"); p.add_argument("--folder")
    p = sub.add_parser("copies", help="every browser copy of a name in the downloads, newest first: PATH, AGE")
    p.add_argument("--name", required=True); p.add_argument("--dir", action="append", default=[])
    p.add_argument("--now")
    p = sub.add_parser("responses", help="of the sessions named, those whose response is in the downloads "
                                         "(0.44.0): SID<tab>PATH, the newest copy")
    p.add_argument("--dir", action="append", default=[]); p.add_argument("--sid", action="append", default=[])
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
        if a.cmd == "responses":
            for sid in a.sid:
                copies = ob.browser_copies(a.dir, f"response-{sid}.tar.gz")
                if copies:
                    print(f"{sid}\t{copies[0][0]}")
            return 0
        if a.cmd == "tray":
            rd = ob.Reader()
            if a.sid and a.folder:
                raise oh.HelperError("office tray takes a session or a folder, not both")
            sid, tray, opener = tray_reading(rd, a.office, pathlib.Path(os.path.expanduser(a.tray_root)), a.sid,
                                             a.folder)
            print(f"sid\t{sid}")
            print(f"path\t{tray}")
            for f in sorted(p.name for p in tray.iterdir() if p.is_file()):
                print(f"file\t{f}")
            print(f"opener\t{opener or ''}")
            return 0
        now = now_from(a)
        if a.cmd == "copies":
            for path, ns in ob.browser_copies(a.dir, a.name):
                print(f"{path}\t{age_words(dt.datetime.fromtimestamp(ns / 1e9, dt.timezone.utc), now)}")
            return 0
        rd = ob.Reader()
        if a.cmd == "elsewhere":
            # Nothing to read when no other office is listed: the walk-in
            # page reads no bundle of its own (the home screen does).
            if not other_offices(a.office, a.machine_file)[0]:
                return 0
            dirs = a.dir or oh.machine_downloads(a.machine_file) or []
            sections, nowhere, _ = other_sections(rd, a.office, a.machine_file, dirs, now)
            if nowhere:
                print(nowhere)
            for heading, said, theirs in sections:
                print(f"\n{heading}:")
                for line in said:
                    print(f"  {line}")
                for it in theirs:
                    print(f"  {it['label']}: {elsewhere_line(it)}")
                if not said and not theirs:
                    print("  nothing waits on you there")
            return 0
        if a.cmd == "bundles":
            waiting = waiting_bundles(rd, a.office, a.dir, now)
            if a.machine_file:
                # Cut by office (0.44.0): another office's, said on stderr.
                sections, nowhere, waiting = other_sections(rd, a.office, a.machine_file, a.dir, now, waiting)
                for heading, _, theirs in sections:
                    for it in theirs:
                        if it["argv"][1:2] == ["start"]:
                            log(f"not offered here: {it['label']}: {elsewhere_line(it)}")
                if nowhere:
                    log(nowhere)
            for b in waiting:
                words = " ".join((b["goal"] or "").split())
                age = age_words(b["at"], now) + (f"; {b['copies']} copies, the newest offered" if b["copies"] > 1 else "")
                print(f"{b['path']}\t{b['stem']}\t{age}\t{oh.ascii_escape(words)[0]}")
            return 0
        if a.cmd == "withdraw-bundle":
            # office withdraw --bundle STEM (0.41.0): --check names the copies
            # and refuses what cannot be withdrawn; without it, the rename.
            stem, found = withdraw_bundle_check(rd, a.office, a.dir, a.stem)
            if a.check:
                print(stem)
                for f in found:
                    print(f)
                return 0
            for line in withdraw_bundle(found):
                print(line)
            return 0
        dt.date.fromisoformat(a.today)
        if a.since:
            dt.date.fromisoformat(a.since)
        lines = home(rd, a.office, a.today, a.since, a.skew, a.founded == "yes", a.tz,
                     None if a.no_downloads else a.dir, now, a.menu_file, a.machine_file)
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
