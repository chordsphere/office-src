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
         itself) and the folder's session open there, and check nothing
         is already at probe-output/ there. One reach of a host, and the
         plan is a JSON line for bin/office, which shows the header and
         asks once before anything runs.
  run    run the block there, stdin closed (office_host.run_probe), its
         output to this terminal whole; read the block back out of it
         (the lines between the sentinels, and whether the integrity
         trailer's count matches them); carry a probe-output/ the run left
         (the file-based fallback, TARBALL.md 4.4) to the session's out
         tray, ~/out-tray/SID/probe-output/, and remove it where it ran.
         The result is a JSON file for bin/office, which copies the block
         to the clipboard with the office's own clipboard command and
         writes the folder's History line, `- DATE probe: SID, N lines`.

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
    return {"text": "\n".join(lines) + "\n", "header": header, "slug": slug}


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


def plan(office_root, folder_rel, project, block_file, sid=None, rd=None):
    """Everything office probe settles before it asks: the block read, where
    it runs, and the session it is for. The session is the folder's
    recorded session open where the project lives (bale status there);
    with several, the one the block's slug names, else --sid; with none,
    the probe is refused, since a probe is a session's and the office keeps
    its output under that session. Returns the plan, or raises ProbeError;
    raises AskSid with the candidates when several are open and nothing
    says which."""
    import office_bale as ob
    import office_host as ohost
    rd = rd or ob.Reader()
    block = read_block(pathlib.Path(block_file).read_text(encoding="utf-8", errors="replace"))
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
    if sid is not None:
        if sid not in candidates:
            raise ProbeError([f"--sid {sid}: not a session {name} records that is open {words} (open there and "
                              f"recorded: {', '.join(candidates) or 'none'})"])
        chosen = sid
    elif len(candidates) == 1:
        chosen = candidates[0]
    elif not candidates:
        raise ProbeError([f"{name} records no session open {words} (it records: {', '.join(recorded) or 'none'}; "
                          f"open there: {', '.join(open_here) or 'none'}), and a probe is a session's: its output "
                          "is kept under that session's out tray. Nothing ran; a folder's session goes out "
                          "through office start"])
    else:
        by_slug = [s for s in candidates if block["slug"] and re.fullmatch(
            rf"\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(block['slug'])}-\d{{3}}", s)]
        if len(by_slug) == 1:
            chosen = by_slug[0]
        else:
            raise AskSid(candidates)
    if there_already:
        raise ProbeError([f"{OUTPUT_DIR}/ is already {words}, from an earlier run, so a fallback probe's output "
                          f"could not be told from it; nothing ran. Carry or remove it first (it is not the repo's)"])
    return {"folder": folder_rel, "name": name, "sid": chosen, "project": label, "where": words,
            "place": place_record(place), "header": block["header"], "slug": block["slug"],
            "lines": block["text"].count("\n")}


class AskSid(Exception):
    def __init__(self, candidates):
        super().__init__(", ".join(candidates))
        self.candidates = candidates


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


def run(plan_data, block_file, tray_root, screen=None):
    """Run the block where the plan says, then read what came back and
    carry the fallback's directory. Returns the result: code, stopped
    (the office's backstop stopped it), found, closed, block (lines),
    count, trailer, words (the count's line), carried (the out tray
    path, or None), carry_problem."""
    import office_host as ohost
    place = place_from(plan_data["place"])
    block = read_block(pathlib.Path(block_file).read_text(encoding="utf-8", errors="replace"))
    log(f"running the probe {plan_data['where']}, stdin closed; its output follows, whole")
    try:
        code, text, stopped = ohost.run_probe(place, block["text"], screen=screen)
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

def main(argv=None):
    import json
    p = argparse.ArgumentParser(prog="office_probe.py", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("lane", help="the project the folder's lane names, when the office scopes it; else nothing")
    q.add_argument("office"); q.add_argument("folder", help="desk/NAME")
    q = sub.add_parser("check", help="read a block as office probe would; its header lines, or why it is refused")
    q.add_argument("block")
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
        if a.cmd == "plan":
            try:
                print(json.dumps(plan(a.office, a.folder, a.project, a.block, a.sid)))
            except AskSid as exc:
                for s in exc.candidates:
                    print(s)
                return EXIT_ASK_SID
            return 0
        if a.cmd == "run":
            data = json.loads(pathlib.Path(a.plan).read_text(encoding="utf-8"))
            result = run(data, a.block, a.tray_root)
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
