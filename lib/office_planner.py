#!/usr/bin/env python3
"""A planner sitting from the occupant's words (0.24.0): what it concerns,
and what the office gathers for it.

The occupant says what he wants a planner for, in his words, and a
read-only sitting goes out (office start --planner; the home screen's p
key). His words are its goal; nothing else is asked of him but the
project, and only when his words name none and what rides depends on it
(the office itself is an answer). The office chooses what rides from what
it knows, so the planner can answer him without asking for files.

Beside what every sitting carries (the hung items, the drafting table with
the digest first, the unsorted drops) and the sitting's own folder, whole,
it gathers, in this order (doctrine section 4, continued):

1. for each project his words concern, its handbook chapter;
2. the folder.md of each folder on the desk on those projects (for the
   office itself, the folders whose lane names none of its projects);
3. what landed on those projects since the last sitting, as the office
   holds it: the walkthrough.md of each folder (on the desk or in the
   filing cabinet) that office land filed or rewrote since the commit that
   filed the last sitting's page, newest first; never bale's telemetry
   (PLANNER.md section 3: digest over dump);
4. the last sitting's notepad pages (the latest sitting's page and its
   continuations, SLUG-2.md and on).

A sitting's include set is its reads (PLANNER.md section 6), so the office
says what rides and why, one line each, in the sitting's brief (the
request's README.md, which the planner reads before anything it carries)
and on the screen. The set stays inside bale pack's caps: when it would
not, it leaves out the oldest of what landed first, one page at a time,
and says so, never silently.

The command line:

    office_planner.py concerns OFFICE --text-file FILE
        what his words concern and the goal they make: goal<tab>TEXT, then
        concern<tab>NAME for each project they name (the floor plan's
        order), then ask<tab>yes|no: whether, with none named, the answer
        would change what rides (no when only one answer is possible, or
        every answer gathers the same pages)
    office_planner.py gather OFFICE --folder REL (--about NAME... | --office)
                             --text-file FILE --brief-out FILE --includes-out FILE
                             [--day DAY] [--concern-why TEXT]
        the include paths into --includes-out (one per line, beside what
        office start ships for every sitting), the brief into --brief-out,
        and the ride lines on stdout, one per line, PATH<tab>WHY; a page
        left out for bale's caps is said on stderr

Standard library only. Logs on stderr with an [office] prefix; exits 0 on
success, 1 on a refusal, 2 on an internal error.
"""

import argparse
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_drafting as od  # noqa: E402
import office_drop as odrop  # noqa: E402
import office_sort as osort  # noqa: E402
import office_watches as ow  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = INSTALL / "templates"
BRIEF_TEMPLATE = "sitting-brief.md"
# The concern that is the office itself, as he answers it ("the office").
OFFICE = "office"
# bale pack's soft caps (bale help pack: 10,000 files, 100.0 MB), past
# which bale stops to ask. What the office gathers, with the rest of the
# sitting's pack, stays under this budget, a tenth below them.
BUDGET_FILES = 9_000
BUDGET_BYTES = 90_000_000
# The kinds of what is gathered, in the order they ride.
KINDS = ("chapter", "folder", "landed", "sitting")


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


# --- what his words concern ------------------------------------------------------------

def project_names(root):
    """The floor plan's projects, by name, in its order; [] when it lists
    none or cannot be read (said under OFFICE_DEBUG)."""
    try:
        manifest = oh.read_toml(pathlib.Path(root) / "floor-plan" / "manifest.toml")
        return [p["name"] for p in oh.read_projects(manifest) or []]
    except (OSError, oh.HelperError) as exc:
        debug(f"the floor plan's projects could not be read: {exc}")
        return []


def named_in(text, names):
    """Every project of names his words name as a word, in names' order:
    the reading office open makes of one project (lib/office_home.py
    words_reading), for as many as he names."""
    return [n for n in names if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", text, re.I)]


def goal_of(text):
    """His words as one line, kept ASCII: the sitting's goal, as office
    open makes a folder's goal (every line as one, a line without its own
    stop joined with a semicolon), a leading dash or list marker left off
    since bale reads a goal first."""
    said = [" ".join(l.split()) for l in odrop.normalize_text(text).splitlines() if l.strip()]
    if not said:
        raise oh.HelperError("the words are empty")
    goal = oh.ascii_escape(" ".join(l if l[-1] in ".!?;:," or i == len(said) - 1 else l + ";"
                                    for i, l in enumerate(said)))[0]
    return goal.lstrip("-*+ ").strip() or goal


# --- the folders and what landed -------------------------------------------------------

def folder_project(f, names):
    """The project a folder's lane names, when it is one of names, else None."""
    p = oh.lane_project((f.get("fields", {}).get("lane") or [""])[0])
    return p if p in names else None


def concerns_folder(f, concerns, names):
    """Whether a folder is on one of the concerns: its lane's project, or,
    for the office itself, a lane that names none of the office's."""
    p = folder_project(f, names)
    return p in concerns if p else OFFICE in concerns


def git(root, *args):
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        debug(f"git {' '.join(args)} in {root}: {proc.stderr.strip()}")
        return None
    return proc.stdout


def last_sitting(root):
    """(sitting, pages, filing) for the latest sitting whose page the
    notepad holds, by the commit that filed it (the digest's window,
    lib/office_digest.py): the page's name, the sitting's pages that are
    there now (sitting_pages), and that filing (when, page, commit,
    subject, key); (None, [], None) when no sitting's page is filed yet."""
    filings = ow.sitting_filings(root) or []
    if not filings:
        return None, [], None
    pages = sitting_pages(root, filings[-1][1])
    return pathlib.PurePosixPath(pages[0] if pages else filings[-1][1]).stem, pages, filings[-1]


def sitting_pages(root, page):
    """A sitting's pages in the notepad, the page first and then its
    continuations in their order: a sitting that outlives its first page
    continues on SLUG-2.md, SLUG-3.md (the brief's own words, and the
    development record's rule), so a page SLUG-N.md whose SLUG.md is there
    belongs to that sitting, whichever of them was filed last."""
    root = pathlib.Path(root)
    stem = pathlib.PurePosixPath(page).stem
    m = re.match(r"^(.*)-(\d+)$", stem)
    base = m.group(1) if m and (root / "notepad" / f"{m.group(1)}.md").is_file() else stem
    found = []
    for p in (root / "notepad").glob(f"{base}*.md"):
        if p.stem == base:
            found.append((0, p.name))
        else:
            n = re.fullmatch(re.escape(base) + r"-(\d+)", p.stem)
            if n:
                found.append((int(n.group(1)), p.name))
    return [f"notepad/{name}" for _, name in sorted(found)]


def walkthroughs_filed(root, base):
    """{folder name: when} for every folder whose walkthrough.md was filed
    or rewritten since the commit base (all history when base is None),
    the latest filing each. A folder that only moved (closed, reopened)
    is a rename to git, never a filing, so it is not counted again."""
    args = ["log", "--format=C%x09%cI", "--name-status", "-M", "--diff-filter=AM"]
    if base:
        args.append(f"{base}..HEAD")
    out = git(root, *args, "--", "desk", "filing-cabinet")
    seen, when = {}, None
    for line in (out or "").splitlines():
        if line.startswith("C\t"):
            when = line.split("\t", 1)[1]
            continue
        parts = line.split("\t")
        if len(parts) < 2 or when is None:
            continue
        bits = parts[-1].split("/")
        if len(bits) == 3 and bits[2] == "walkthrough.md":
            seen.setdefault(bits[1], when)  # the log is newest first
    return seen


# --- the gathering -----------------------------------------------------------------------

def entry(path, why, kind, at=None):
    return {"path": path, "why": why, "kind": kind, "at": at}


def gather(root, concerns, own=None, names=None):
    """The pages gathered for a sitting on the concerns (projects by name,
    and OFFICE for the office itself), in the pinned order (the module's
    docstring), each an entry dict: path (relative to the office), why,
    kind and, for what landed, when. own is the sitting's own folder
    (space/name), which rides whole and is not gathered again."""
    root = pathlib.Path(root)
    names = project_names(root) if names is None else names
    out = []
    for p in concerns:
        if p == OFFICE:
            continue
        rel = osort.chapter_rel(p)
        if (root / rel).is_file():
            out.append(entry(rel, f"{p}'s handbook chapter: what the office knows of {p} that its repo does not say",
                             "chapter"))
    folders = [f for f in oh.read_folders(root) if f["problem"] is None]
    where = lambda f: folder_project(f, names) or "the office"  # noqa: E731
    for f in folders:
        if f["space"] != "desk" or f["rel"] == own or not concerns_folder(f, concerns, names):
            continue
        title = f.get("title") or f["name"]
        out.append(entry(f"{f['rel']}/folder.md",
                         f"{oh.cite(f)}, {title}: on the desk, {f.get('status') or 'no status line'}, on {where(f)}",
                         "folder"))
    sitting, pages, filing = last_sitting(root)
    filed = walkthroughs_filed(root, filing[2] if filing else None)
    landed = []
    for f in folders:
        when = filed.get(f["name"])
        if when is None or not concerns_folder(f, concerns, names) or not (f["path"].parent / "walkthrough.md").is_file():
            continue
        since = "since the last sitting" if filing else "(no sitting's page is filed yet, so everything counts)"
        landed.append(entry(f"{f['rel']}/walkthrough.md",
                            f"what landed on {where(f)} {since}: {oh.cite(f)}'s walkthrough, filed {when[:10]}",
                            "landed", when))
    out += sorted(landed, key=lambda e: e["at"], reverse=True)
    for page in pages:
        out.append(entry(page, f"the last sitting's words ({sitting}), filed {filing[0].date().isoformat()}",
                         "sitting"))
    return out


def weight(root, paths):
    """(files, bytes) of the paths under root, a directory counted whole;
    a path that is not there weighs nothing."""
    files = size = 0
    root = pathlib.Path(root)
    for rel in paths:
        p = root / rel
        if p.is_file():
            files, size = files + 1, size + p.stat().st_size
        elif p.is_dir():
            for q in p.rglob("*"):
                if q.is_file():
                    files, size = files + 1, size + q.stat().st_size
    return files, size


def fit(root, entries, base, budget=(BUDGET_FILES, BUDGET_BYTES)):
    """(kept, left) for entries alongside the rest of the pack, base its
    (files, bytes): while the whole is over the budget, the oldest of what
    landed is left out first, one page at a time. Nothing else is ever
    left out: a set still over the budget then is said by the caller, and
    bale's own caps speak for themselves."""
    kept = list(entries)
    left = []
    while True:
        files, size = weight(root, [e["path"] for e in kept])
        if base[0] + files <= budget[0] and base[1] + size <= budget[1]:
            return kept, left
        landed = [e for e in kept if e["kind"] == "landed"]
        if not landed:
            return kept, left
        oldest = min(landed, key=lambda e: e["at"])
        kept.remove(oldest)
        left.append(oldest)


def every_sitting_carries(root, own):
    """What rides with every sitting the office sends, beside what it
    gathers: (paths, ride lines) for the brief's list and the budget."""
    root = pathlib.Path(root)
    lines, paths = [], []
    if own:
        lines.append((f"{own}/", "the sitting's own folder, whole: what was asked, and the sessions it records"))
        paths.append(own)
    lines.append((f"{od.SPACE}/", "the drafting table, its digest.md first: written just before the pack, every line "
                                  "computed then (doctrine section 5)"))
    paths.append(od.SPACE)
    try:
        manifest = oh.read_toml(root / "floor-plan" / "manifest.toml")
        hung = [h for h in oh.space_paths(manifest, "hung") if (root / h).exists()]
    except (OSError, oh.HelperError) as exc:
        debug(f"the hung items could not be read: {exc}")
        hung = []
    if hung:
        lines.append((", ".join(hung), "the hung items every session in the office carries (doctrine section 6)"))
        paths += hung
    try:
        drops = [d["rel"] for d in odrop.unsorted(root)]
    except (OSError, oh.HelperError) as exc:
        debug(f"the in-tray could not be read: {exc}")
        drops = []
    if drops:
        lines.append((f"{odrop.SPACE}/ ({len(drops)} page(s))",
                      "the unsorted drops, as every session carries them; a sitting reads them and owes no Sort"))
        paths += drops
    return paths, lines


def concern_words(concerns):
    named = [c for c in concerns if c != OFFICE]
    words = ", ".join(named)
    if OFFICE in concerns:
        words = (words + ", and " if words else "") + "the office itself"
    return words or "the office itself"


def render_brief(words, concerns, folder, folder_words, day, rides, left, why=""):
    """The sitting's brief, from the install's templates/sitting-brief.md:
    his words verbatim as a quoted block, what they concern and how that
    was found, and what rides, one line each, with anything left out for
    bale's caps said after it."""
    said = odrop.normalize_text(words).strip("\n").splitlines()
    quoted = "\n".join(f"> {l.rstrip()}" if l.strip() else ">" for l in said)
    ride_lines = [f"- {path}: {why_}" for path, why_ in rides]
    ride_lines += [f"- left out for bale's caps: {e['path']} ({e['why']})" for e in left]
    template = (TEMPLATES / BRIEF_TEMPLATE).read_text(encoding="utf-8")
    return oh.render_template(template, {
        "day": day, "folder": folder, "folder_words": folder_words, "words": quoted,
        "concerns": concern_words(concerns) + (f" ({why})" if why else ""),
        "rides": "\n".join(ride_lines),
    })


def would_ask(root, names):
    """Whether, with no project named in his words, asking which one would
    change what rides: never when the office scopes none, and not when
    every answer (each project, and the office itself) gathers the same."""
    if not names:
        return False
    sets = {tuple(e["path"] for e in gather(root, [c], names=names)) for c in [*names, OFFICE]}
    return len(sets) > 1


# --- the command line --------------------------------------------------------------------

def read_words(path):
    return pathlib.Path(path).read_bytes().decode("utf-8", "surrogateescape")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_planner.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("concerns", help="what his words concern: goal, concern NAME..., ask yes|no")
    p.add_argument("office"); p.add_argument("--text-file", required=True)
    p = sub.add_parser("gather", help="the sitting's includes, its brief, and the ride lines on stdout")
    p.add_argument("office"); p.add_argument("--folder", required=True)
    p.add_argument("--about", action="append", default=[])
    p.add_argument("--office", dest="itself", action="store_true", help="the sitting concerns the office itself")
    p.add_argument("--text-file", required=True); p.add_argument("--brief-out", required=True)
    p.add_argument("--includes-out", required=True); p.add_argument("--day", default="")
    p.add_argument("--folder-words", default=""); p.add_argument("--concern-why", default="")
    a = ap.parse_args(argv)
    try:
        root = pathlib.Path(a.office)
        names = project_names(root)
        text = read_words(a.text_file)
        if a.cmd == "concerns":
            print(f"goal\t{goal_of(text)}")
            named = named_in(text, names)
            for n in named:
                print(f"concern\t{n}")
            print(f"ask\t{'yes' if not named and would_ask(root, names) else 'no'}")
            return 0
        goal_of(text)  # empty words refuse here, before anything is written
        concerns = [*a.about, *([OFFICE] if a.itself else [])]
        for c in a.about:
            if c not in names:
                raise oh.HelperError(f"--about {c}: no such project in this office (it scopes: "
                                     f"{', '.join(names) or 'none'})")
        if not concerns:
            concerns = [OFFICE]
        gathered = gather(root, concerns, a.folder, names)
        base_paths, always = every_sitting_carries(root, a.folder)
        kept, left = fit(root, gathered, weight(root, base_paths))
        for e in left:
            log(f"left out of this sitting for bale's caps: {e['path']} ({e['why']}); the oldest of what landed goes "
                "first")
        files, size = weight(root, base_paths + [e["path"] for e in kept])
        if files > BUDGET_FILES or size > BUDGET_BYTES:
            log(f"what rides is {files} file(s), {size} byte(s), still past the office's budget for bale's caps "
                f"({BUDGET_FILES} files, {BUDGET_BYTES} bytes) with nothing left that landed: bale's own caps say "
                "what they say")
        rides = always + [(e["path"], e["why"]) for e in kept]
        pathlib.Path(a.includes_out).write_text("".join(e["path"] + "\n" for e in kept), encoding="utf-8")
        brief = render_brief(text, concerns, a.folder, a.folder_words or a.folder, a.day, rides, left,
                             a.concern_why)
        pathlib.Path(a.brief_out).write_text(brief, encoding="utf-8")
        for path, why in rides:
            print(f"{path}\t{why}")
        return 0
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        log(f"error: {exc.__class__.__name__}: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
