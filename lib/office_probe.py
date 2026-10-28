#!/usr/bin/env python3
"""office probe: a worker's probe block, run where a folder's project lives.

A worker that needs a fact from the occupant's environment returns a probe
block (TARBALL.md section 4): a self-contained bash script with a purpose
header, its output between `=== PROBE BEGIN SLUG ===` and `=== PROBE END
SLUG ===`, an integrity trailer counting the lines between them. For a
project on a host the block must run where the repo is, inside a container
behind ssh; before 0.18.0 the occupant did that by hand. The office is his
hands at the terminal (doctrine section 1), so office probe runs it:

  plan   read the block (refused by name when it has no PROBE BEGIN line,
         or its purpose header does not say it is read-only), find where
         the folder's project lives (its place: a directory here, or a
         path through a host's shell; the office root for the office
         itself) and the folder's session open there, or its read-only
         sitting open in the office (0.33.0: a sitting's probe of a
         project's repo runs there, under the sitting's id), and check
         nothing is already at probe-output/ there. One reach of a host,
         and the plan is a JSON line for bin/office, which shows the
         header and asks once before anything runs.
  on     (0.34.0) what `office-on PROJECT COMMAND` runs inside a block
         that spans the office and a project's host: the one command
         where that project lives, through its shell on a host, stdin
         closed, its output back on this stream. office probe writes the
         office-on helper for one run and puts it on the block's PATH.
  run    run the block there, stdin closed (office_host.run_probe), its
         output to this terminal whole; read the block back out of it
         (the lines between the sentinels, and whether the integrity
         trailer's count matches them); carry a probe-output/ the run left
         (the file-based fallback, TARBALL.md 4.4) to the session's out
         tray, ~/out-tray/SID/probe-output/, and remove it where it ran.
         The result is a JSON file for bin/office, which copies the block
         to the clipboard with the office's own clipboard command and
         writes the folder's History line, `- DATE probe: SID, N lines`.

A block that calls `office-on PROJECT ...` (0.34.0) spans the office and
the projects it names: it runs in the office root, under the folder's
session open in the office or in one of those projects, and each
office-on call runs its command where that project lives. The M10
walkthrough's planner sitting (2026-10-27) needed the work office's
folder and the hosted repo in one probe, and ran six by hand.

bale is read only for the sessions open where the project lives (bale
status --json, through office_bale's reader), and the shell is run only
through office_host. Standard library only. Logs to stderr with an
[office] prefix; exits 0 on success, 1 on a refusal (the lines say why),
2 on a usage or internal error, and 5 when plan needs to be told which of
several open sessions the probe is for (they are printed, one per line).
"""

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

OFFICE = "office"
OUTPUT_DIR = "probe-output"
# The sentinels and the trailer of the block's output (TARBALL.md 4.2; the
# crafter's skeleton prints them so).
BEGIN_LINE_RE = oh.LazyPattern(r"^=+ PROBE BEGIN\b")
END_LINE_RE = oh.LazyPattern(r"^=+ PROBE END\b")
TRAILER_RE = oh.LazyPattern(r"^--- integrity: (\d+) lines? ---$")
# The block's own words, read from its text.
BEGIN_WORD = "PROBE BEGIN"
HEADER_SLUG_RE = oh.LazyPattern(r"^#\s*PROBE\s+([a-z0-9][a-z0-9-]*)\s*:", re.I)
TEXT_SLUG_RE = oh.LazyPattern(r"PROBE BEGIN ([a-z0-9][a-z0-9-]*)")
READ_ONLY_RE = oh.LazyPattern(r"\bread[- ]only\b", re.I)
NOT_READ_ONLY_RE = oh.LazyPattern(r"\bnot\s+read[- ]only\b", re.I)
EXIT_ASK_SID = 5
# The helper a spanning block calls (0.34.0): `office-on PROJECT COMMAND...`
# on a line that is not a comment names a project the block reaches.
ON_HELPER = "office-on"
REACH_RE = oh.LazyPattern(r"(?<![\w./-])office-on\s+([A-Za-z0-9_][A-Za-z0-9_-]*)")
# The exit code office-on gives when the project cannot be reached at all
# (a host that stopped answering), told apart from the command's own.
EXIT_ON_UNREACHED = 97


class ProbeError(Exception):
    """office probe cannot go on, said as lines a person can act on."""

    def __init__(self, lines):
        super().__init__("\n".join(lines))
        self.lines = list(lines)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- the block ---------------------------------------------------------------------------

def read_block(text):
    """The block as it runs, its purpose header and its slug, from the
    text the occupant gave (a file, stdin or the clipboard): line ends
    made LF, a chat's code fence around it dropped, blank lines at either
    end dropped. Raises ProbeError, naming why, for a block the office
    does not run: one with no PROBE BEGIN line (not a probe block), one
    with no purpose header (the comment lines before its first blank
    line, TARBALL.md 4.2), and one whose header does not say it is
    read-only. The office runs nothing the occupant has not seen, and a
    probe that writes is the fallback's, which says so in its header."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    def trim(ls):
        while ls and not ls[0].strip():
            ls = ls[1:]
        while ls and not ls[-1].strip():
            ls = ls[:-1]
        return ls

    lines = trim(lines)
    if lines and lines[0].lstrip().startswith("```"):
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        lines = trim(lines)
    if not lines:
        raise ProbeError(["the block is empty: nothing to run"])
    if not any(BEGIN_WORD in line for line in lines):
        raise ProbeError([f"the block has no {BEGIN_WORD} line, so it is not a probe block (TARBALL.md 4.2: its "
                          "output is bracketed by PROBE BEGIN and PROBE END lines); nothing ran"])
    header = []
    for line in lines:
        if not line.strip():
            break
        if line.startswith("#!"):
            continue
        if not line.lstrip().startswith("#"):
            break
        header.append(line)
    if not header:
        raise ProbeError(["the block has no purpose header (the comment lines before its first blank line, saying "
                          "what it asks, why, that it is read-only, and its bound: TARBALL.md 4.2), so there is "
                          "nothing to show before it runs; nothing ran"])
    says = [line for line in header if READ_ONLY_RE.search(line)]
    if not says or any(NOT_READ_ONLY_RE.search(line) for line in header):
        raise ProbeError(["the block's purpose header does not say it is read-only, so the office does not run it "
                          "(TARBALL.md 4.2: a probe confirms in its header that it is read-only; one that writes "
                          "is the file-based fallback, which says where it writes); nothing ran"])
    slug = None
    for line in header:
        m = HEADER_SLUG_RE.match(line)
        if m:
            slug = m.group(1).lower()
            break
    if slug is None:
        m = TEXT_SLUG_RE.search("\n".join(lines))
        slug = m.group(1) if m else None
    return {"text": "\n".join(lines) + "\n", "header": header, "slug": slug, "reaches": reaches_of(lines)}


def reaches_of(lines):
    """The projects a block reaches with `office-on PROJECT ...` (0.34.0),
    in order of first call, read from the lines that are not comments: a
    header may say what the helper is for without naming a project."""
    out = []
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        for m in REACH_RE.finditer(line):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


def read_output(text):
    """What came back between the sentinels of the block's output: found
    (a PROBE BEGIN line), closed (a PROBE END line after it), block (the
    lines from PROBE BEGIN to PROBE END, both included), count (the
    output lines between them, the trailer aside) and trailer (the count
    the integrity trailer gives, or None when there is none)."""
    lines = text.replace("\r\n", "\n").split("\n")
    begin = next((i for i, line in enumerate(lines) if BEGIN_LINE_RE.match(line)), None)
    if begin is None:
        return {"found": False, "closed": False, "block": [], "count": 0, "trailer": None}
    end = next((i for i in range(begin + 1, len(lines)) if END_LINE_RE.match(lines[i])), None)
    if end is None:
        return {"found": True, "closed": False, "block": lines[begin:], "count": 0, "trailer": None}
    body = lines[begin + 1:end]
    trailer = None
    if body:
        m = TRAILER_RE.match(body[-1])
        if m:
            trailer = int(m.group(1))
            body = body[:-1]
    return {"found": True, "closed": True, "block": lines[begin:end + 1], "count": len(body), "trailer": trailer}


def count_words(result):
    """The one line that says what came back."""
    if not result["found"]:
        return "no probe block came back: its output has no PROBE BEGIN line"
    if not result["closed"]:
        return ("the block came back unclosed: a PROBE BEGIN line and no PROBE END after it, so it is not a block a "
                "worker can trust (the output above is all there is)")
    n = result["count"]
    if result["trailer"] is None:
        return f"{n} line(s) came back between PROBE BEGIN and PROBE END; there is no integrity trailer to check them by"
    if result["trailer"] == n:
        return f"{n} line(s) came back between PROBE BEGIN and PROBE END, and the integrity trailer's count matches"
    return (f"{n} line(s) came back between PROBE BEGIN and PROBE END, but the integrity trailer says "
            f"{result['trailer']}: the block is not whole")


# --- where it runs, and for which session ------------------------------------------------

def place_record(place):
    """A Place as plain data, for the plan."""
    return {"path": place.path, "host": place.host, "shell": place.shell, "connect": place.connect,
            "name": place.name}


def place_from(record):
    import office_host as ohost
    if record.get("host"):
        return ohost.Place(record["path"], record["host"], record["shell"], record["connect"], record.get("name"))
    return ohost.Place(record["path"], name=record.get("name"))


def lane_of(office_root, folder_rel):
    """The project the folder's lane names, when the office scopes it, else
    None (a lane is `project: paths`)."""
    import office_bale as ob
    md = pathlib.Path(office_root) / folder_rel / "folder.md"
    folder = oh.parse_folder(md.read_text(encoding="utf-8"))
    projects = ob.office_projects(office_root) or []
    return ob.lane_project(folder, [p["name"] for p in projects])


def where_it_runs(office_root, project):
    """(Place, label, words) for the project, or the office root for the
    office itself. Raises ProbeError for a project the office does not
    scope or cannot read."""
    import office_bale as ob
    import office_host as ohost
    if project == OFFICE:
        return ohost.Place(str(pathlib.Path(office_root).resolve()), name=OFFICE), OFFICE, "in the office root"
    projects = ob.office_projects(office_root)
    if not projects:
        raise ProbeError([ob.no_projects_line(projects)])
    try:
        entry = ob.select(projects, project)[0]
    except oh.HelperError as exc:
        raise ProbeError([f"--project {project}: {exc}; or --project office, for the office itself"])
    try:
        where = ob.readable(entry)
    except ob.BaleError as exc:
        raise ProbeError([f"{project}: cannot be reached: {exc}"])
    place = where if isinstance(where, ohost.Place) else ohost.Place(str(where), name=project)
    words = (f"in {place.path} on {place.host} (through {project}'s shell)" if place.hosted
             else f"in {place.path} ({project}'s repo)")
    return place, project, words


def open_sittings(office_root, recorded, rd):
    """The sessions in `recorded` open in the office's own registry as
    read-only sittings (0.33.0), oldest first: [] when the office has no
    registry. A sitting is open in the office, never in a project, so a
    probe it asks for a project's repo is found here. Raises BaleError when
    the registry cannot be read."""
    import office_bale as ob
    registry = ob.office_registry(office_root)
    if registry is None or not recorded:
        return []
    return [s for s, read_only in rd.open_sessions(registry) if read_only and s in recorded]


def choose_session(candidates, sittings, slug, sid=None):
    """The session a probe is for, from the folder's recorded sessions open
    where it runs (candidates) and its read-only sittings open in the
    office (sittings, 0.33.0): --sid when given and one of them (None when
    it is not, for the caller to refuse); else the one the block's slug
    names; else today's rule for the project's sessions, the one open there
    when there is one; else the one sitting when there is no session there.
    Raises AskSid with them all when nothing says which."""
    pool = candidates + [s for s in sittings if s not in candidates]
    if sid is not None:
        return sid if sid in pool else None
    by_slug = [s for s in pool if slug and re.fullmatch(rf"\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(slug)}-\d{{3}}", s)]
    if len(by_slug) == 1:
        return by_slug[0]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates and len(sittings) == 1:
        return sittings[0]
    raise AskSid(pool, sittings=[s for s in pool if s in sittings and s not in candidates])


def plan(office_root, folder_rel, project, block_file, sid=None, rd=None):
    """Everything office probe settles before it asks: the block read, where
    it runs, and the session it is for. The session is the folder's
    recorded session open where the project lives (bale status there);
    with several, the one the block's slug names, else --sid; with none,
    the probe is refused, since a probe is a session's and the office keeps
    its output under that session. A read-only sitting the folder records,
    open in the office's own registry, is a session a probe of a project
    can be for too (0.33.0): the block runs in the project's repo, under
    the sitting's id, and its output is kept in the sitting's out tray.
    Returns the plan, or raises ProbeError; raises AskSid with the
    candidates when several are open and nothing says which."""
    import office_bale as ob
    import office_host as ohost
    rd = rd or ob.Reader()
    block = read_block(pathlib.Path(block_file).read_text(encoding="utf-8", errors="replace"))
    if block["reaches"]:
        return plan_spanning(office_root, folder_rel, project, block, sid, rd)
    place, label, words = where_it_runs(office_root, project)
    md = pathlib.Path(office_root) / folder_rel / "folder.md"
    folder = oh.parse_folder(md.read_text(encoding="utf-8"))
    recorded = list(dict.fromkeys(folder["sids"]))
    name = pathlib.Path(folder_rel).name
    # The sessions open where it runs, and whether probe-output/ is there
    # already: on a host, both in one connection (the reach).
    there_already = False
    try:
        if label == OFFICE:
            registry = ob.office_registry(office_root)
            open_here = [s for s, _ in rd.open_sessions(registry)] if registry is not None else []
            there_already = (pathlib.Path(place.path) / OUTPUT_DIR).exists()
        elif place.hosted:
            _, runs = rd.prefetch(place, [("status", {})],
                                  extra=[["sh", "-c", ohost.MISSING_SCRIPT, "office-paths", OUTPUT_DIR]])
            open_here = [s for s, _ in rd.open_sessions(place)]
            if runs and runs[0].returncode == 0:
                there_already = OUTPUT_DIR not in runs[0].stdout.split()
            else:
                there_already = ohost.dir_there(place, OUTPUT_DIR)
        else:
            open_here = [s for s, _ in rd.open_sessions(place.path)] if (pathlib.Path(place.path) / ".bale").is_dir() \
                else []
            there_already = (pathlib.Path(place.path) / OUTPUT_DIR).exists()
    except ob.BaleError as exc:
        raise ProbeError([f"{label}: the sessions open there could not be read, so the office cannot say which "
                          f"session this probe is for: {exc}; nothing ran"])
    except ohost.HostError as exc:
        raise ProbeError([f"{label}: {exc}; nothing ran"])
    candidates = [s for s in recorded if s in open_here]
    # The folder's read-only sittings open in the office (0.33.0), for a
    # probe of a project: read only when the folder records a session that
    # is not open there, so a folder whose sessions are all the project's
    # costs no read of the office's registry.
    sittings = []
    if label != OFFICE and any(s not in open_here for s in recorded):
        try:
            sittings = open_sittings(office_root, [s for s in recorded if s not in open_here], rd)
        except ob.BaleError as exc:
            raise ProbeError([f"the office: its open sittings could not be read, so the office cannot say whether "
                              f"this probe is for one of {name}'s: {exc}; nothing ran"])
    pool = candidates + [s for s in sittings if s not in candidates]
    if not pool and sid is None:
        raise ProbeError([f"{name} records no session open {words} (it records: {', '.join(recorded) or 'none'}; "
                          f"open there: {', '.join(open_here) or 'none'}; and no read-only sitting of its is open "
                          "in the office), and a probe is a session's: its output is kept under that session's "
                          "out tray. Nothing ran; a folder's session goes out through office start"])
    # Raises AskSid, for the caller to ask, when several could be meant.
    chosen = choose_session(candidates, sittings, block["slug"], sid)
    if chosen is None:
        raise ProbeError([f"--sid {sid}: not a session {name} records that is open {words} or a read-only sitting "
                          f"of its open in the office (open and recorded: {', '.join(pool) or 'none'})"])
    if there_already:
        raise ProbeError([f"{OUTPUT_DIR}/ is already {words}, from an earlier run, so a fallback probe's output "
                          f"could not be told from it; nothing ran. Carry or remove it first (it is not the repo's)"])
    return {"folder": folder_rel, "name": name, "sid": chosen, "project": label, "where": words,
            "place": place_record(place), "header": block["header"], "slug": block["slug"],
            "lines": block["text"].count("\n"), "sitting": chosen in sittings and chosen not in candidates,
            "reaches": {}}


def plan_spanning(office_root, folder_rel, project, block, sid, rd):
    """The plan for a block that spans the office and the projects it
    names with office-on (0.34.0): it runs in the office root, so --project
    is office or not given; every project named must be one the office
    scopes and can reach (one connection each, which also reads the
    sessions open there); the session is chosen from the folder's sessions
    open in the office (a read-only sitting, or an office session) and in
    any project reached, by the same rule as a probe of one place, so a
    planner sitting's probe is found without --sid when it is the one.
    probe-output/ must not be in the office root already."""
    import office_bale as ob
    import office_host as ohost
    label = OFFICE
    if project not in (None, OFFICE):
        raise ProbeError([f"the block calls {ON_HELPER} for {', '.join(block['reaches'])}, so it runs in the office root "
                          f"and reaches each of them through its shell; --project {project} does not fit it (give "
                          f"--project office, or leave it out); nothing ran"])
    md = pathlib.Path(office_root) / folder_rel / "folder.md"
    folder = oh.parse_folder(md.read_text(encoding="utf-8"))
    recorded = list(dict.fromkeys(folder["sids"]))
    name = pathlib.Path(folder_rel).name
    root_place = ohost.Place(str(pathlib.Path(office_root).resolve()), name=OFFICE)
    reaches, reach_words, open_in_projects = {}, [], []
    for reached in block["reaches"]:
        try:
            place, _, words = where_it_runs(office_root, reached)
        except ProbeError as exc:
            raise ProbeError([f"{ON_HELPER} {reached}: {exc.lines[0]}; nothing ran", *exc.lines[1:]])
        try:
            # The sessions open there: for a hosted project, the one
            # connection that also proves the host answers.
            if place.hosted or (pathlib.Path(place.path) / ".bale").is_dir():
                open_in_projects += [s for s, _ in rd.open_sessions(place if place.hosted else place.path)
                                     if s not in open_in_projects]
        except ob.BaleError as exc:
            raise ProbeError([f"{reached}: {exc}; nothing ran"])
        except ohost.HostError as exc:
            raise ProbeError([f"{reached}: {exc}; nothing ran"])
        reaches[reached] = place_record(place)
        reach_words.append(f"{reached} {words} with {ON_HELPER} {reached}")
    where = "in the office root, reaching " + "; ".join(reach_words)
    try:
        registry = ob.office_registry(office_root)
        open_office = rd.open_sessions(registry) if registry is not None else []
    except ob.BaleError as exc:
        raise ProbeError([f"the office: its open sessions could not be read, so the office cannot say which session "
                          f"this probe is for: {exc}; nothing ran"])
    office_sids = [s for s, _ in open_office]
    sittings = [s for s, read_only in open_office if read_only and s in recorded]
    candidates = [s for s in recorded if s in open_in_projects or (s in office_sids and s not in sittings)]
    pool = candidates + [s for s in sittings if s not in candidates]
    if not pool and sid is None:
        raise ProbeError([f"{name} records no session open in the office or in {', '.join(block['reaches'])} (it records: "
                          f"{', '.join(recorded) or 'none'}; open: {', '.join(office_sids + open_in_projects) or 'none'}), "
                          "and a probe is a session's: its output is kept under that session's out tray. Nothing ran; a "
                          "folder's session goes out through office start"])
    chosen = choose_session(candidates, sittings, block["slug"], sid)
    if chosen is None:
        raise ProbeError([f"--sid {sid}: not a session {name} records that is open in the office or in "
                          f"{', '.join(block['reaches'])} (open and recorded: {', '.join(pool) or 'none'})"])
    if (pathlib.Path(root_place.path) / OUTPUT_DIR).exists():
        raise ProbeError([f"{OUTPUT_DIR}/ is already in the office root, from an earlier run, so a fallback probe's "
                          "output could not be told from it; nothing ran. Carry or remove it first"])
    return {"folder": folder_rel, "name": name, "sid": chosen, "project": label, "where": where,
            "place": place_record(root_place), "header": block["header"], "slug": block["slug"],
            "lines": block["text"].count("\n"), "sitting": chosen in sittings and chosen not in candidates,
            "reaches": reaches}


class AskSid(Exception):
    """Several sessions a probe could be for, and nothing says which: the
    candidates, and which of them are read-only sittings open in the
    office (0.33.0), so the question can say so."""

    def __init__(self, candidates, sittings=()):
        super().__init__(", ".join(candidates))
        self.candidates = candidates
        self.sittings = list(sittings)


# --- the run ------------------------------------------------------------------------------

def tray_dest(tray_root, sid):
    """Where a carried probe-output/ goes in the session's out tray:
    probe-output/, or probe-output-2/, -3/ when an earlier probe of the
    session left one there."""
    base = pathlib.Path(tray_root) / sid
    dest = base / OUTPUT_DIR
    n = 2
    while dest.exists():
        dest = base / f"{OUTPUT_DIR}-{n}"
        n += 1
    return dest


ON_HELPER_TEXT = """#!/usr/bin/env bash
# office-on PROJECT COMMAND...: run one shell command where PROJECT lives,
# through its shell on a host, stdin closed, its output on this stream and
# its exit code returned (97: the project could not be reached). Written by
# office probe for one run of a block that spans the office and a project's
# host; the block's own header promises it is read-only.
exec {python} -I -B -P -S {module} on --plan {plan} -- "$@"
"""


def write_on_helper(directory, plan_file):
    """Write the office-on helper (0.34.0) into directory, for one run of a
    spanning block, and return its directory for the block's PATH."""
    import shlex
    import stat
    d = pathlib.Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    path = d / ON_HELPER
    path.write_text(ON_HELPER_TEXT.format(python=shlex.quote(sys.executable),
                                          module=shlex.quote(str(pathlib.Path(__file__).resolve())),
                                          plan=shlex.quote(str(pathlib.Path(plan_file).resolve()))), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return d


def run_on(plan_data, project, words):
    """What `office-on PROJECT COMMAND...` does (0.34.0): the words, joined
    with spaces as a shell line, run where the project lives through
    office_host (in its directory on this machine; through its shell, in
    its path, on a host), stdin closed. Returns (exit code, stdout,
    stderr); a project the plan does not reach, or that cannot be
    reached, is a ProbeError."""
    import office_host as ohost
    reaches = plan_data.get("reaches") or {}
    if project not in reaches:
        raise ProbeError([f"{ON_HELPER} {project}: not a project this probe reaches (its block names: "
                          f"{', '.join(reaches) or 'none'}); a name is read from the block before it runs, so "
                          "name each project literally, never through a variable"])
    command = " ".join(words).strip()
    if not command:
        raise ProbeError([f"{ON_HELPER} {project}: no command given"])
    place = place_from(reaches[project])
    try:
        run_ = ohost.run_in(place, ["bash", "-c", command], timeout=ohost.TRANSFER_TIMEOUT)
    except ohost.HostError as exc:
        raise ProbeError([f"{ON_HELPER} {project}: {exc}"])
    # Through a shell the streams come back line by line, their last
    # newline not kept (office_host._split_calls): each ends in one here,
    # as a command's output does, so the block's next line starts fresh.
    out = run_.stdout if not run_.stdout or run_.stdout.endswith("\n") else run_.stdout + "\n"
    err = run_.stderr if not run_.stderr or run_.stderr.endswith("\n") else run_.stderr + "\n"
    return run_.returncode, out, err


def run(plan_data, block_file, tray_root, screen=None, plan_file=None):
    """Run the block where the plan says, then read what came back and
    carry the fallback's directory. Returns the result: code, stopped
    (the office's backstop stopped it), found, closed, block (lines),
    count, trailer, words (the count's line), carried (the out tray
    path, or None), carry_problem. A block that spans (plan reaches, with
    plan_file) gets the office-on helper first on its PATH, written beside
    the plan for this run."""
    import os
    import office_host as ohost
    place = place_from(plan_data["place"])
    block = read_block(pathlib.Path(block_file).read_text(encoding="utf-8", errors="replace"))
    env = None
    if plan_data.get("reaches"):
        if plan_file is None:
            raise ProbeError([f"a block that calls {ON_HELPER} needs its plan as a file, for the helper to read"])
        helper_dir = write_on_helper(pathlib.Path(plan_file).resolve().parent / "bin", plan_file)
        env = {"PATH": f"{helper_dir}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}"}
        log(f"{ON_HELPER} is on the block's PATH for {', '.join(plan_data['reaches'])}: each call runs its command "
            "where that project lives, stdin closed")
    log(f"running the probe {plan_data['where']}, stdin closed; its output follows, whole")
    try:
        code, text, stopped = ohost.run_probe(place, block["text"], screen=screen, env=env)
    except ohost.HostError as exc:
        raise ProbeError([f"{plan_data['project']}: {exc}; the block did not run to its end, and nothing was carried"])
    out = read_output(text)
    result = dict(out, code=code, stopped=stopped, words=count_words(out), carried=None, carry_problem=None,
                  carried_files=0)
    if stopped:
        log(f"the block ran past the office's backstop of {ohost.probe_timeout()}s and was stopped "
            f"({ohost.PROBE_TIMEOUT_ENV}=<seconds> gives it longer)")
    try:
        left = ohost.dir_there(place, OUTPUT_DIR)
    except ohost.HostError as exc:
        left = None
        result["carry_problem"] = f"whether the run left {OUTPUT_DIR}/ {plan_data['where']} could not be read: {exc}"
    if left:
        dest = tray_dest(tray_root, plan_data["sid"])
        try:
            n = ohost.carry_dir_here(place, OUTPUT_DIR, dest)
        except (ohost.HostError, OSError) as exc:
            result["carry_problem"] = (f"the run left {OUTPUT_DIR}/ {plan_data['where']}, and it could not be "
                                       f"carried to {dest}: {exc}; it is left where it is")
        else:
            result["carried"], result["carried_files"] = str(dest), n
            try:
                ohost.remove_dir_there(place, OUTPUT_DIR)
            except (ohost.HostError, OSError) as exc:
                result["carry_problem"] = (f"{OUTPUT_DIR}/ was carried to {dest}, but could not be removed "
                                           f"{plan_data['where']}: {exc}; remove it there by hand")
    return result


# --- the command line ---------------------------------------------------------------------

def on_main(argv):
    """`on --plan FILE -- PROJECT COMMAND...`, the office-on helper's line
    (0.34.0), read by hand so a command's own flags (git log --format=%s)
    are never taken for this program's. Exits with the command's code,
    EXIT_ON_UNREACHED when the project cannot be reached, 2 for a line
    that does not read."""
    import json
    argv = list(argv)
    if len(argv) < 4 or argv[0] != "--plan" or argv[2] != "--":
        log(f"error: {ON_HELPER} is run as `on --plan FILE -- PROJECT COMMAND...`, not {' '.join(argv)!r}")
        return 2
    plan_file, project, words = argv[1], argv[3], argv[4:]
    try:
        data = json.loads(pathlib.Path(plan_file).read_text(encoding="utf-8"))
        code, out, err = run_on(data, project, words)
    except ProbeError as exc:
        for line in exc.lines:
            log(f"error: {line}")
        return EXIT_ON_UNREACHED
    except (OSError, json.JSONDecodeError) as exc:
        log(f"error: {ON_HELPER}: the plan could not be read: {exc}")
        return 2
    sys.stdout.write(out)
    sys.stdout.flush()
    sys.stderr.write(err)
    return code


def main(argv=None):
    import json
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["on"]:
        return on_main(argv[1:])
    p = argparse.ArgumentParser(prog="office_probe.py", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("lane", help="the project the folder's lane names, when the office scopes it; else nothing")
    q.add_argument("office"); q.add_argument("folder", help="desk/NAME")
    q = sub.add_parser("check", help="read a block as office probe would; its header lines, or why it is refused")
    q.add_argument("block")
    q = sub.add_parser("reaches", help="the projects a block reaches with office-on, one per line (0.34.0)")
    q.add_argument("block")
    q = sub.add_parser("on", help="office-on PROJECT COMMAND...: one command where the project lives (0.34.0); "
                                  "its line is `on --plan FILE -- PROJECT COMMAND...`, read by on_main, not here")
    q = sub.add_parser("plan", help="the block read, where it runs and its session: one JSON line (exit 5: several "
                                    "sessions open, printed one per line)")
    q.add_argument("office"); q.add_argument("folder", help="desk/NAME")
    q.add_argument("--project", required=True, help="a project the office scopes, or office")
    q.add_argument("--block", required=True); q.add_argument("--sid")
    q = sub.add_parser("run", help="run the block as planned; the result as JSON into --result")
    q.add_argument("--plan", required=True); q.add_argument("--block", required=True)
    q.add_argument("--tray-root", required=True); q.add_argument("--result", required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == "lane":
            print(lane_of(a.office, a.folder) or "")
            return 0
        if a.cmd == "check":
            for line in read_block(pathlib.Path(a.block).read_text(encoding="utf-8", errors="replace"))["header"]:
                print(line)
            return 0
        if a.cmd == "reaches":
            for name in read_block(pathlib.Path(a.block).read_text(encoding="utf-8", errors="replace"))["reaches"]:
                print(name)
            return 0

        if a.cmd == "plan":
            try:
                print(json.dumps(plan(a.office, a.folder, a.project, a.block, a.sid)))
            except AskSid as exc:
                # One per line: the id, a tab, and its words for the key.
                for s in exc.candidates:
                    print(f"{s}\t{s}, a read-only sitting open in the office" if s in exc.sittings else f"{s}\t{s}")
                return EXIT_ASK_SID
            return 0
        if a.cmd == "run":
            data = json.loads(pathlib.Path(a.plan).read_text(encoding="utf-8"))
            result = run(data, a.block, a.tray_root, plan_file=a.plan)
            pathlib.Path(a.result).write_text(json.dumps(result) + "\n", encoding="utf-8")
            return 0
    except ProbeError as exc:
        for line in exc.lines:
            log(f"error: {line}")
        return 1
    except (oh.HelperError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        log(f"error: {exc}")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
