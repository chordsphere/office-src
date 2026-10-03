#!/usr/bin/env python3
"""The office's read side: the reader over bale's records and its renderings.

The office reads bale's records in its projects' repos and renders them;
it never copies them (doctrine section 10). This module is the only place
the office talks to bale. It runs `bale` from the PATH in a project's
directory with stdin closed, reads the one JSON line a --json surface
prints, and returns plain data. It never reads .bale/. The reads write
nothing; the one thing that writes is office start, which, when the
occupant asks, runs bale's pack for a session and for the context that
rides beside it, and copies the tarballs bale made into an out tray.

share/bale-consumption.toml is the contract with bale: every verb and
flag called here (each call's argv is built from it), every JSON key
read (each read goes through Reader.key, which refuses a key the
manifest does not declare), and the bale version the reads were probed
on. A declared key that bale's line lacks is an error naming that
version, so a bale release that moves a key fails loudly here and in
the test suite, never silently on a walk-in.

Standard library only. The command line prints renderings on stdout,
logs to stderr with an [office] prefix, and exits 0 on success, 1 on a
refusal, 2 on a usage or internal error, and 3 when it rendered but at
least one project could not be read (the rendering says which and why).
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
CONSUMPTION = INSTALL / "share" / "bale-consumption.toml"
BALE_TIMEOUT = 60
# A pack copies a tree and runs bale's own checks; give it longer.
PACK_TIMEOUT = 600
# Attempts that carry a response tarball: the ones a trust ledger counts.
RESPONSE_COMMANDS = ("apply", "retry")
OUTBOX_RE = re.compile(r"^request-(.+)\.tar\.gz$")
# A project's release file, at any depth (VERSION, bin/VERSION).
VERSION_FILE = "VERSION"


class BaleError(Exception):
    """One read that could not be done, as one line a person can act on.

    kind: missing (no bale on PATH), path (the project directory is not
    there), refused (bale exited non-zero), output (not the JSON line the
    surface promises), key (a declared key bale's line lacks), undeclared
    (the office asked for a key its consumption manifest does not name:
    a defect in office-src)."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- the consumption manifest --------------------------------------------------

class Consumption:
    """share/bale-consumption.toml, read once."""

    def __init__(self, path=CONSUMPTION):
        data = oh.read_toml(path)
        try:
            self.floor = data["bale"]["floor"]
            oh.parse_version(self.floor)
            self.surfaces = data["surfaces"]
        except (KeyError, TypeError, oh.HelperError) as exc:
            raise oh.HelperError(f"{path}: not a consumption manifest ({exc})")
        self.path = path

    def surface(self, name):
        if name not in self.surfaces:
            raise BaleError("undeclared", f"bale surface {name!r} is not in {self.path.name}")
        return self.surfaces[name]

    def keys(self, name):
        return set(self.surface(name).get("keys", []))

    def argv(self, name, **values):
        """The argv for a surface, from its declaration: the fixed argv
        with {placeholders} filled, then each declared optional flag whose
        value was given, in the declared order."""
        s = self.surface(name)
        if not s.get("calls", True):
            raise BaleError("undeclared", f"the office never calls bale for {name!r}; it only reads its report")

        def fill(word):
            m = re.fullmatch(r"\{([a-z_]+)\}", word)
            if not m:
                return word
            if values.get(m.group(1)) is None:
                raise BaleError("undeclared", f"bale {name} needs a value for {word}")
            return str(values[m.group(1)])

        out = [fill(w) for w in s["argv"]]
        for flag, word in s.get("optional", []):
            key = word.strip("{}")
            if values.get(key) is not None:
                out += [flag, str(values[key])]
        # A list value: the flag once per element, in order.
        for flag, word in s.get("repeated", []):
            for v in values.get(word.strip("{}")) or []:
                out += [flag, str(v)]
        # A true value: the bare flag.
        for flag, word in s.get("switches", []):
            if values.get(word.strip("{}")):
                out.append(flag)
        return out


# --- the reader ------------------------------------------------------------------

class Reader:
    """Runs bale's JSON surfaces and hands back plain data.

    Calls are cached per (directory, argv) for the life of the reader, so
    one rendering asks bale each question once. `touched` collects every
    (surface, key) read, which the suite compares with the manifest."""

    def __init__(self, consumption=None, runner=subprocess.run):
        self.consumption = consumption or Consumption()
        self.runner = runner
        self.touched = set()
        self._cache = {}
        self._installed = None

    # The one door every key read goes through.
    def key(self, obj, surface, path):
        if path not in self.consumption.keys(surface):
            raise BaleError("undeclared", f"the office reads {surface} key {path!r}, which "
                            f"{self.consumption.path.name} does not declare (a defect in office-src)")
        self.touched.add((surface, path))
        name = path.rsplit(".", 1)[-1].removesuffix("[]")
        if not isinstance(obj, dict) or name not in obj:
            raise BaleError("key", f"bale's {surface} line has no key {path!r}; the office's reads were "
                            f"written against bale {self.consumption.floor} or later "
                            f"(installed: {self._installed or 'unknown'})")
        return obj[name]

    def bale(self):
        exe = shutil.which("bale")
        if exe is None:
            raise BaleError("missing", "bale is not on PATH; the read side runs bale's --json surfaces")
        return exe

    def invoke(self, surface, cwd=None, timeout=BALE_TIMEOUT, **values):
        """Run one declared surface with stdin closed; (proc, shown, where).
        Refuses when bale exits non-zero, carrying bale's last words."""
        argv = self.consumption.argv(surface, **values)
        where = str(cwd) if cwd is not None else os.getcwd()
        exe = self.bale()
        if cwd is not None and not pathlib.Path(cwd).is_dir():
            raise BaleError("path", f"no such directory on this machine: {cwd}")
        shown = "bale " + " ".join(argv)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        try:
            proc = self.runner([exe, *argv], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise BaleError("refused", f"{shown} in {where} did not finish in {timeout}s")
        except OSError as exc:
            raise BaleError("missing", f"could not run {exe}: {exc}")
        debug(f"{shown} in {where}: exit {proc.returncode}, {len(proc.stdout)} bytes on stdout")
        if proc.returncode != 0:
            why = next((l for l in reversed(proc.stderr.splitlines()) if l.strip()), "no message")
            raise BaleError("refused", f"{shown} refused in {where} (exit {proc.returncode}): {why}")
        return proc, shown, where

    def run(self, surface, cwd=None, **values):
        """Run one declared reading surface and return its parsed JSON
        line, asking bale each question once."""
        argv = self.consumption.argv(surface, **values)
        where = str(cwd) if cwd is not None else os.getcwd()
        cache_key = (where, tuple(argv))
        if cache_key in self._cache:
            return self._cache[cache_key]
        proc, shown, where = self.invoke(surface, cwd, **values)
        result = self.parse(surface, proc, shown, where)
        self._cache[cache_key] = result
        return result

    def pack(self, surface, cwd, **values):
        """Run one of the surfaces that make something (a session, a
        context tarball): never cached, since each run makes a new one.
        Returns (the report, bale's stderr lines)."""
        proc, shown, where = self.invoke(surface, cwd, timeout=PACK_TIMEOUT, **values)
        return self.parse(surface, proc, shown, where), proc.stderr.splitlines()

    def parse(self, surface, proc, shown, where):
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        spec = self.consumption.surface(surface)
        if spec.get("format") == "text":
            if not lines:
                raise BaleError("output", f"{shown} printed nothing in {where}")
            result = lines[-1]
        else:
            if not lines:
                raise BaleError("output", f"{shown} printed no JSON line in {where}")
            try:
                result = json.loads(lines[-1])
            except json.JSONDecodeError as exc:
                raise BaleError("output", f"{shown} in {where}: the last stdout line is not JSON ({exc})")
            want = spec.get("outcome")
            got = self.key(result, surface, "outcome")
            if want is not None and got != want:
                raise BaleError("output", f"{shown} in {where}: outcome {got!r}, the surface promises {want!r}")
        return result

    # --- what the renderings ask for ---------------------------------------

    def installed_version(self):
        """bale's version from `bale --version`, or raise."""
        line = self.run("version")
        m = re.match(self.consumption.surface("version")["pattern"], line)
        if not m:
            raise BaleError("output", f"bale --version printed {line!r}, not `bale X.Y.Z`")
        self._installed = m.group(1)
        return self._installed

    def status(self, cwd):
        return self.run("status", cwd)

    def open_sessions(self, cwd):
        """[(sid, read_only)] for the sessions open in the repo, oldest
        first; read_only from the recorded scope (an empty scope locks
        nothing and lands nothing)."""
        st = self.status(cwd)
        sids = self.key(st, "status", "sessions") or []
        scopes = self.key(st, "status", "scopes") or {}
        return [(sid, scopes.get(sid) == []) for sid in sids]

    def known_sids(self, cwd):
        """Every session id the repo's JSON surfaces name: the requests in
        its outbox and the open sessions. bale's aggregate names members
        of its anomaly counts only, so the outbox is the fullest list a
        --json surface carries (a slip for bale-src)."""
        st = self.status(cwd)
        out = set(self.key(st, "status", "sessions") or [])
        for name in self.key(st, "status", "outbox") or []:
            m = OUTBOX_RE.match(name)
            if m and oh.SID_RE.match(m.group(1)):
                out.add(m.group(1))
        return sorted(out)

    def dossier(self, cwd, sid):
        """One session's dossier, or None when bale's records hold no such
        session. A record bale could not parse is an error, not a miss."""
        d = self.run("dossier", cwd, sid=sid)
        if self.key(d, "dossier", "found"):
            return d
        if self.key(d, "dossier", "parse_failure"):
            raise BaleError("output", f"bale has a record for {sid} in {cwd} but could not parse it")
        if self.key(d, "dossier", "filtered_record_version"):
            raise BaleError("output", f"bale's record for {sid} in {cwd} is a newer record version than it reads")
        return None

    def aggregate(self, cwd, work_class=None):
        return self.run("stats", cwd, work_class=work_class)


# --- plain data from a dossier ---------------------------------------------------

def session_view(rd, d):
    """What the renderings show about one session, from its dossier."""
    rec = rd.key(d, "dossier", "record")
    lineage = rd.key(d, "dossier", "lineage")
    closure = rd.key(rec, "dossier", "record.closure")
    view = {
        "sid": rd.key(d, "dossier", "session_id"),
        "created": rd.key(rec, "dossier", "record.created_at"),
        "updated": rd.key(rec, "dossier", "record.updated_at"),
        "outcome": rd.key(rec, "dossier", "record.outcome"),
        "work_class": rd.key(rec, "dossier", "record.work_class"),
        "in_flight": rd.key(rec, "dossier", "record.in_flight"),
        "read_only": rd.key(rec, "dossier", "record.read_only"),
        "unlock_reason": rd.key(closure, "dossier", "record.closure.unlock_reason") if closure else None,
        "superseded_by": rd.key(lineage, "dossier", "lineage.superseded_by"),
        "attempts": [],
    }
    for a in rd.key(d, "dossier", "attempts") or []:
        validation = rd.key(a, "dossier", "attempts[].validation")
        clar = rd.key(a, "dossier", "attempts[].clarification")
        link = rd.key(a, "dossier", "attempts[].linkage")
        checks = []
        if validation:
            for c in rd.key(validation, "dossier", "attempts[].validation.checks") or []:
                checks.append({
                    "check": rd.key(c, "dossier", "attempts[].validation.checks[].check"),
                    "claim": rd.key(c, "dossier", "attempts[].validation.checks[].claim"),
                    "verdict": rd.key(c, "dossier", "attempts[].validation.checks[].verdict"),
                    "agreement": rd.key(c, "dossier", "attempts[].validation.checks[].agreement"),
                })
        view["attempts"].append({
            "at": rd.key(a, "dossier", "attempts[].at"),
            "command": rd.key(a, "dossier", "attempts[].command"),
            "outcome": rd.key(a, "dossier", "attempts[].outcome"),
            "change_paths": rd.key(a, "dossier", "attempts[].change_paths") or [],
            "state": rd.key(validation, "dossier", "attempts[].validation.state") if validation else None,
            "checks": checks,
            "rounds": rd.key(clar, "dossier", "attempts[].clarification.rounds") if clar else None,
            "linkage": (rd.key(link, "dossier", "attempts[].linkage.kind"),
                        rd.key(link, "dossier", "attempts[].linkage.point")) if link else None,
        })
    return view


def outcome_word(view):
    """The blueprint's words for where a session stands: applied, held,
    bailed, open, superseded; anything else bale says, as bale says it."""
    if view["superseded_by"]:
        return f"superseded by {view['superseded_by']}"
    o = view["outcome"]
    if view["in_flight"]:
        return "held" if o == "held" else ("open" if o in ("opened", "packed") else f"open ({o})")
    if o == "bailout":
        return "bailed"
    if o == "unlocked":
        reason = view["unlock_reason"]
        return "closed read-only" if reason == "closed-read-only" else f"unlocked ({reason or 'no reason recorded'})"
    return o


def response_attempts(view):
    return [a for a in view["attempts"] if a["command"] in RESPONSE_COMMANDS]


def day(stamp):
    return (stamp or "")[:10] or "?"


def parse_stamp(stamp):
    return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def describe_age(then, now):
    secs = max(0, int((now - then).total_seconds()))
    if secs < 3600:
        return f"{secs // 60}m"
    if secs < 86400:
        return f"{secs // 3600}h"
    return f"{secs // 86400}d"


def rate(num, den, bale_rate=None):
    """`0.89 (16 of 18)`, or `- (0 of 0)` on a zero denominator. When
    bale computed the rate, bale's number is the one shown."""
    if not den:
        return f"- ({num} of {den})"
    value = bale_rate if bale_rate is not None else num / den
    return f"{value:.2f} ({num} of {den})"


# --- projects and folders ----------------------------------------------------------

def office_projects(office_root):
    """The office's [projects] entries (None when it has no table)."""
    return oh.read_projects(oh.read_toml(pathlib.Path(office_root) / "floor-plan" / "manifest.toml"))


def no_projects_line(projects):
    if projects is None:
        return ("this office scopes no projects: its floor plan has no [projects] table "
                "(office projects add NAME PATH)")
    return "this office scopes no projects: its [projects] table lists none (office projects add NAME PATH)"


def readable(project):
    """The project's directory, or raise BaleError saying why it cannot
    be read. A path that is not on this machine is an error line: reading
    a project on another machine is an open question (seed Q-2)."""
    if project["problem"]:
        raise BaleError("path", project["problem"])
    if not project["resolved"].is_dir():
        raise BaleError("path", f"no such directory on this machine: {project['resolved']}")
    return project["resolved"]


def select(projects, name):
    if name is None:
        return projects
    chosen = [p for p in projects if p["name"] == name]
    if not chosen:
        raise oh.HelperError(f"no project named {name} in this office's [projects] "
                             f"(it lists: {', '.join(p['name'] for p in projects) or 'none'})")
    return chosen


def folders_naming(office_root):
    """sid -> the folders (desk/X, filing-cabinet/X) whose Sessions
    section names it."""
    out = {}
    for space in ("desk", "filing-cabinet"):
        for md in sorted((pathlib.Path(office_root) / space).glob("*/folder.md")):
            try:
                lines = oh.folder_session_lines(md)
            except (OSError, UnicodeDecodeError) as exc:
                # The desk names it under Cannot be read; one bad file
                # never takes the rest of the rendering down.
                debug(f"{space}/{md.parent.name}/folder.md cannot be read, so no session maps to it: {exc}")
                continue
            for sid, _ in lines:
                out.setdefault(sid, []).append(f"{space}/{md.parent.name}")
    return out


# --- the renderings ---------------------------------------------------------------------

def office_registry(office_root):
    """The office's own repo when bale keeps a registry there (a .bale/
    directory; an existence check, nothing inside is read), else None.
    An office nobody has packed a session from has none, and nothing in
    it can be open."""
    root = pathlib.Path(office_root)
    if (root / ".bale").is_dir():
        return root
    debug(f"no .bale/ in the office at {root}: bale keeps no registry there, so no session of its own is open")
    return None


# The office's own registry is read with the projects' and labeled so.
OFFICE_LABEL = "this office"


def in_flight(rd, office_root, now=None):
    """(lines, unreadable, flying): one line per open session in the
    projects the office scopes and in the office's own repo, each mapped
    to the folder that names its sid; flying is the set of folders
    (space/name) some open session is mapped to."""
    now = now or dt.datetime.now(dt.timezone.utc)
    projects = office_projects(office_root)
    naming = folders_naming(office_root)
    sources = [(p["name"], p) for p in projects or []]
    own = office_registry(office_root)
    if own is not None:
        sources.insert(0, (OFFICE_LABEL, {"problem": None, "resolved": own}))
    lines, bad, open_count, flying = [], 0, 0, set()
    if not projects:
        lines.append(no_projects_line(projects))
    for label, p in sources:
        try:
            cwd = readable(p)
            for sid, read_only in rd.open_sessions(cwd):
                open_count += 1
                folders = naming.get(sid, [])
                flying.update(folders)
                d = rd.dossier(cwd, sid)
                if d is None:
                    lines.append(f"{label}: {sid} open, with no record in bale's telemetry yet"
                                 f" -> {', '.join(folders) or 'no folder'}")
                    continue
                v = session_view(rd, d)
                state = "read-only" if read_only else outcome_word(v)
                age = describe_age(parse_stamp(v["created"]), now)
                lines.append(f"{label}: {sid} {state}, opened {age} ago"
                             f" -> {', '.join(folders) or 'no folder'}")
        except BaleError as exc:
            bad += 1
            lines.append(f"{label}: cannot read: {exc}")
    if open_count == 0 and bad == 0 and projects:
        lines.append(f"none: no session is open in the {len(projects)} project(s) this office scopes"
                     + (", or in the office itself" if own is not None else ""))
    elif open_count == 0 and bad == 0 and own is not None:
        lines.append("none: no session is open in the office itself")
    return lines, bad, flying


def render_in_flight(rd, office_root, now=None):
    """(lines, unreadable projects): the walk-in's In flight section.
    Short on purpose."""
    lines, bad, _ = in_flight(rd, office_root, now)
    return lines, bad


# --- the one-writer rule ---------------------------------------------------------

def forecast_holds(entry, target):
    """Does a forecast entry hold the target path? It does when it is
    the target or a directory above it (the whole tree included). An
    entry inside the target, a session scoped to one folder, does not:
    it cannot mint a number, and blocking every open for the life of a
    folder's session would be friction, not safety."""
    entry = entry.strip().strip("/")
    target = target.strip().strip("/")
    return entry in ("", ".") or entry == target or target.startswith(entry + "/")


def writers_holding(rd, office_root, targets):
    """[(sid, target, forecast)] for each session open in the office's own
    registry whose forecast holds a target: the sessions a script that
    mints a number must not run beside (the blueprint's section 5.4).
    [] when the office has no registry. Raises BaleError when it has one
    that cannot be read."""
    own = office_registry(office_root)
    if own is None:
        return []
    st = rd.status(own)
    sids = rd.key(st, "status", "sessions") or []
    scopes = rd.key(st, "status", "scopes") or {}
    out = []
    for sid in sids:
        forecast = scopes.get(sid) or []
        for target in targets:
            if any(forecast_holds(e, target) for e in forecast):
                out.append((sid, target, forecast))
                break
    return out


# --- the desk ----------------------------------------------------------------------
#
# What `office desk` renders (the blueprint's section 2.3), in order: In
# flight, Ready, Parked, Candidates. Orphaned riders and pending desk moves
# follow Candidates once the drafting-table verbs exist to read them.
# Every folder on the desk lands in exactly one group, and a folder whose
# facts the desk cannot place is shown with the reason, never dropped.

FOLDER_TEMPLATE = INSTALL / "templates" / "folder.md"
SIZE_RANK = {size: n for n, size in enumerate(oh.SIZES)}
NOT_YET = "not readable until the drafting-table verbs land"
SUCCESSOR_RE = re.compile(r"folders?\s+([\d,\s]+)")


def folder_line(f):
    """`folder N  NAME  next: ...  (sessions: N)`, the name alone for a
    folder with no number, and its size when it has one."""
    try:
        nxt, count = oh.folder_summary(f["path"], FOLDER_TEMPLATE)
    except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
        return f"{f['name']}  (folder.md could not be read: {exc})"
    head = f"folder {f['number']}  {f['name']}" if f.get("number") else f["name"]
    size = (f["fields"].get("size") or [None])[0]
    return f"{head}  next: {nxt}  (sessions: {count})" + (f"  {size}" if size else "")


def successors(f):
    """The folder numbers an absorbed or split folder's last state line
    points at."""
    last = f.get("last_state")
    m = SUCCESSOR_RE.search(last[2]) if last else None
    return [int(n) for n in re.findall(r"\d+", m.group(1))] if m else []


def gate_state(gate, by_number, seen=()):
    """Where a gate stands: (state, words, cleared) where state is met,
    wait, notyet or error; words name the gate's own status; cleared is
    the day a met folder gate cleared, when its History says."""
    kind, _, ref = gate.partition(" ")
    if kind != "folder":
        return "notyet", f"{gate}: {NOT_YET}", None
    n = int(ref)  # read_gates normalized it: `folder N`
    if n in seen:
        return "error", f"{gate} leads back to the folder that waits on it", None
    same = by_number.get(n, [])
    if not same:
        return "error", f"{gate} names no folder on the desk or in the filing cabinet", None
    if len(same) > 1:
        return "error", f"{gate} is minted twice ({', '.join(x['rel'] for x in same)})", None
    t = same[0]
    title = t.get("title") or t["name"]
    status = t["status"]
    last = t["last_state"]
    if status == "done":
        return "met", f"{gate} done", last[0] if last and last[1] == "done" else None
    if status is None and t["space"] == "filing-cabinet":
        return "met", f"{gate} filed", None
    if status in ("absorbed", "split"):
        nexts = successors(t)
        if not nexts:
            return "error", f"{gate} was {status}, and its History names no successor", None
        states = [gate_state(f"folder {m}", by_number, seen + (n,)) for m in nexts]
        for st in states:
            if st[0] != "met":
                return st[0], f"{gate} ({status} into " + ", ".join(f"folder {m}" for m in nexts) + f"): {st[1]}", None
        days = [st[2] for st in states if st[2]]
        return "met", f"{gate} {status}, and " + ", ".join(f"folder {m}" for m in nexts) + " done", max(days) if days else None
    if status == "retired":
        why = last[2] if last and last[1] == "retired" else "no reason recorded"
        return "wait", f"{gate} (retired: {why}); it will not clear by itself", None
    return "wait", f"{gate} ({status or 'no status line'}): {title}", None


def after_cycles(desk, by_number):
    """Cycles among the after gates of desk folders, each as the list of
    numbers around it."""
    graph = {}
    for f in desk:
        if f["problem"] or not f.get("number"):
            continue
        graph[f["number"]] = [int(g.split()[1]) for g in read_gates(f, "after", [])
                              if g.startswith("folder ")
                              and len(by_number.get(int(g.split()[1]), [])) == 1
                              and by_number[int(g.split()[1])][0]["space"] == "desk"]
    cycles, state = [], {}

    def visit(n, path):
        state[n] = "open"
        for m in graph.get(n, []):
            if state.get(m) == "open":
                cycles.append(path[path.index(m):] + [m])
            elif m not in state:
                visit(m, path + [m])
        state[n] = "done"

    for n in sorted(graph):
        if n not in state:
            visit(n, [n])
    return cycles


def ready_order(ready, errors):
    """Ready folders in order: by `serializes after` (when both are
    ready, the one named goes first), then size, small first, then
    number. A cycle among them is an error line, and its folders follow
    in size and number order."""
    def key(f):
        size = (f["fields"].get("size") or [None])[0]
        return (SIZE_RANK.get(size, len(SIZE_RANK)), f.get("number") or float("inf"), f["name"])
    by_n = {f["number"]: f for f in ready if f.get("number")}
    before = {id(f): set() for f in ready}
    for f in ready:
        for g in read_gates(f, "serializes after", []):
            kind, _, ref = g.partition(" ")
            if kind == "folder" and int(ref) in by_n and by_n[int(ref)] is not f:
                before[id(f)].add(id(by_n[int(ref)]))
    out, left = [], sorted(ready, key=key)
    while left:
        free = [f for f in left if not (before[id(f)] & {id(x) for x in left})]
        if not free:
            errors.append("ERROR: `serializes after` gates in a cycle among ready folders: "
                          + ", ".join(oh.cite(f) for f in left) + "; shown in size and number order")
            out += left
            break
        out.append(free[0])
        left.remove(free[0])
    return out


def read_gates(f, key, errors):
    """A folder's gates of one kind, normalized as office open writes
    them; a line that does not read as a gate is an error line, never a
    guess."""
    out = []
    for g in f["fields"].get(key, []):
        try:
            out.append(oh.normalize_field(key, g))
        except oh.HelperError as exc:
            errors.append(f"ERROR: {oh.cite(f)}: `{key}: {g}` does not read: {exc}")
    return out


def classify_desk(folders, flying, since):
    """The desk's groups from its folders: a dict of lists, plus the
    error lines the Ready group carries."""
    by_number = oh.folders_by_number(folders)
    desk = [f for f in folders if f["space"] == "desk"]
    groups = {"flying": [], "open": [], "ready": [], "parked": {}, "candidates": [], "no_status": [],
              "misplaced": [], "unreadable": [], "ready_errors": [], "cleared": {}}
    cyclic = {}
    for cycle in after_cycles(desk, by_number):
        words = "ERROR: after gates in a cycle: " + " -> ".join(f"folder {n}" for n in cycle)
        for n in cycle[:-1]:
            cyclic.setdefault(n, words)

    def park(heading, f, also=()):
        groups["parked"].setdefault(heading, []).append((f, [a for a in also if a != heading]))

    for f in desk:
        if f["problem"]:
            groups["unreadable"].append(f)
            continue
        if f["rel"] in flying:
            groups["flying"].append(f)
            continue
        status = f["status"]
        if status is None:
            groups["no_status"].append(f)
        elif status == "open":
            groups["open"].append(f)
        elif status == "candidate":
            groups["candidates"].append(f)
        elif status != "queued":
            groups["misplaced"].append(f)
        elif f.get("number") in cyclic:
            park(cyclic[f["number"]], f)
        else:
            waits, cleared = [], []
            me = (f["number"],) if f.get("number") else ()
            gates = {key: read_gates(f, key, waits) for key in ("after", "consumer", "serializes after")}
            for g in gates["after"]:
                state, words, day = gate_state(g, by_number, me)
                if state == "met":
                    if day and day >= since:
                        cleared.append(f"gate cleared: {words} {day}")
                elif state == "error":
                    waits.append(f"ERROR: {oh.cite(f)}: after {words}")
                elif state == "notyet":
                    waits.append(f"waiting for {words}")
                else:
                    waits.append(f"waiting for {words}")
            for g in gates["consumer"]:
                state, words, _ = gate_state(g, by_number, me)
                if state == "error":
                    waits.append(f"ERROR: {oh.cite(f)}: consumer {words}")
                elif state == "notyet":
                    waits.append(f"parked for its consumer, {words}")
                else:
                    waits.append(f"parked for its consumer, {words}")
            for g in gates["serializes after"]:
                kind, _, ref = g.partition(" ")
                same = by_number.get(int(ref), [])
                if not same:
                    waits.append(f"ERROR: {oh.cite(f)}: serializes after {g}, which names no folder")
                elif same[0]["status"] == "open" or same[0]["rel"] in flying:
                    waits.append(f"waiting for {g} to close: it is open, and this one serializes after it, "
                                 "never beside it")
            if waits:
                park(waits[0], f, waits[1:])
            else:
                groups["ready"].append(f)
                if cleared:
                    groups["cleared"][f["rel"]] = cleared
    groups["ready"] = ready_order(groups["ready"], groups["ready_errors"])
    return groups


def desk_lines(groups, flight_lines, walk_in=False, ready_limit=3):
    """The groups as the screen shows them. Full, for office desk; for
    the walk-in, In flight and the first ready folders."""
    lines = ["In flight:"]
    lines += [f"  {l}" for l in flight_lines]
    lines += [f"  {folder_line(f)}  [open, no session in flight]" for f in groups["open"]]
    parked = sum(len(v) for v in groups["parked"].values())
    errors = sum(1 for h in groups["parked"] if h.startswith("ERROR")) + len(groups["ready_errors"])
    on_desk = (len(groups["flying"]) + len(groups["open"]) + len(groups["ready"]) + parked + len(groups["candidates"])
               + len(groups["no_status"]) + len(groups["misplaced"]) + len(groups["unreadable"]))

    def ready_block(items):
        out = []
        for f in items:
            out.append(f"  {folder_line(f)}")
            out += [f"    {c}" for c in groups["cleared"].get(f["rel"], [])]
        return out

    if walk_in:
        counts = [f"{len(groups['ready'])} ready", f"{parked} parked",
                  f"{len(groups['candidates'])} candidate(s)"]
        if groups["flying"] or groups["open"]:
            counts.insert(0, f"{len(groups['flying']) + len(groups['open'])} open")
        if groups["no_status"]:
            counts.append(f"{len(groups['no_status'])} with no status line")
        lines += ["", "On the desk: " + ", ".join(counts) + " (office desk shows every group)"]
        if not on_desk:
            lines.append("  the desk is clear")
        elif groups["ready"]:
            lines += ready_block(groups["ready"][:ready_limit])
            if len(groups["ready"]) > ready_limit:
                lines.append(f"  and {len(groups['ready']) - ready_limit} more ready")
        else:
            lines.append("  nothing is ready")
        if errors:
            lines.append(f"  {errors} gate error(s): office desk names them")
        return lines
    if not on_desk:
        return lines + ["", "the desk is clear"]
    if groups["ready"] or groups["ready_errors"]:
        lines += ["", "Ready:"] + [f"  {e}" for e in groups["ready_errors"]] + ready_block(groups["ready"])
    if groups["parked"]:
        lines += ["", "Parked:"]
        for heading in sorted(groups["parked"], key=lambda h: (not h.startswith("ERROR"), h)):
            lines.append(f"  {heading}")
            for f, also in groups["parked"][heading]:
                lines.append(f"    {folder_line(f)}")
                lines += [f"      and {a}" for a in also]
    if groups["candidates"]:
        lines += ["", "Candidates:"] + [f"  {folder_line(f)}" for f in groups["candidates"]]
    # Orphaned riders and pending desk moves join here with the
    # drafting-table verbs.
    if groups["no_status"]:
        lines += ["", "No status line (folders from before the field block; the desk cannot order them):"]
        lines += [f"  {folder_line(f)}" for f in groups["no_status"]]
    if groups["misplaced"]:
        lines += ["", "On the desk with a filing-cabinet status (office status names each):"]
        lines += [f"  {folder_line(f)}  [status {f['status']}]" for f in groups["misplaced"]]
    if groups["unreadable"]:
        lines += ["", "Cannot be read:"] + [f"  {f['name']}  ({f['problem']})" for f in groups["unreadable"]]
    return lines


def render_desk(rd, office_root, today, since=None, walk_in=False, now=None):
    """(lines, unreadable projects): office desk, or the walk-in's two
    sections. since is the day of the previous walk-in (default today):
    a ready folder whose gate cleared on or after it says so."""
    flight, bad, flying = in_flight(rd, office_root, now)
    groups = classify_desk(oh.read_folders(office_root), flying, since or today)
    return desk_lines(groups, flight, walk_in=walk_in), bad


def locate(rd, projects, sid, statuses):
    """(project, dossier) for a sid: first the projects whose outbox or
    open list names it, then every readable project. (None, None) when
    no project's records hold it."""
    readable_projects = []
    for p in projects:
        try:
            cwd = readable(p)
        except BaleError:
            continue
        if p["name"] not in statuses:
            statuses[p["name"]] = rd.known_sids(cwd)
        readable_projects.append((p, cwd))
    ordered = ([pc for pc in readable_projects if sid in statuses[pc[0]["name"]]]
               + [pc for pc in readable_projects if sid not in statuses[pc[0]["name"]]])
    for p, cwd in ordered:
        d = rd.dossier(cwd, sid)
        if d is not None:
            return p, d
    return None, None


def render_folder_sessions(rd, office_root, folder_md):
    """(lines, unreadable): the folder's own Sessions lines, each followed
    by what bale's records say about the session. Nothing rendered here
    is written into the folder."""
    recorded = oh.folder_session_lines(folder_md)
    lines = [f"- {sid}" + (f": {words}" if words else "") for sid, words in recorded]
    if not recorded:
        return ["no session ids are recorded in this folder"], 0
    projects = office_projects(office_root)
    if not projects:
        return lines + [f"{no_projects_line(projects)}; no outcomes are rendered"], 0
    out, bad, found, missing = [], 0, 0, []
    statuses = {}
    try:
        rd.bale()
    except BaleError as exc:
        return lines + [f"  cannot read bale's records: {exc}"], 1
    for p in projects:
        try:
            readable(p)
        except BaleError as exc:
            bad += 1
            out.append(f"  {p['name']}: cannot read: {exc}")
    for (sid, words), line in zip(recorded, lines):
        out.append(line)
        try:
            p, d = locate(rd, projects, sid, statuses)
        except BaleError as exc:
            bad += 1
            out.append(f"    cannot read: {exc}")
            continue
        if d is None:
            missing.append(sid)
            out.append("    not in the records of any project this office scopes")
            continue
        found += 1
        v = session_view(rd, d)
        out.append(f"    {p['name']}: {outcome_word(v)}; opened {day(v['created'])}, last event "
                   f"{day(v['updated'])}; work class {v['work_class']}")
        responses = response_attempts(v)
        if not responses:
            out.append("    no response attempt yet")
        for n, a in enumerate(responses, 1):
            checks = a["checks"]
            tally = {}
            for c in checks:
                tally[c["agreement"]] = tally.get(c["agreement"], 0) + 1
            summary = ", ".join(f"{k} {tally[k]}" for k in sorted(tally)) or "no claims"
            out.append(f"    attempt {n}, {a['command']} {day(a['at'])}: {a['outcome']}, validation "
                       f"{a['state'] or 'not run'}; {len(checks)} claim(s): {summary}")
            for c in checks:
                out.append(f"      [{c['agreement']}] claim {c['claim']}, verdict {c['verdict']}: {c['check']}")
        rounds = [a["rounds"] for a in v["attempts"] if a["rounds"] is not None]
        links = [f"{a['linkage'][0]} {a['linkage'][1]}" for a in v["attempts"] if a["linkage"]]
        out.append(f"    exchange rounds: {rounds[-1] if rounds else 'none recorded'}"
                   + (f"; linkage: {', '.join(links)}" if links else ""))
    out.append(f"recorded in this folder: {len(recorded)} session id(s); found in bale's records: {found}"
               + (f"; not found: {', '.join(missing)}" if missing else ""))
    out.append("bale version per session: not on bale's dossier (a slip for bale-src)")
    return out, bad


def all_views(rd, cwd):
    """(views of every session the repo's surfaces name, sids with no
    record)."""
    views, unrecorded = [], []
    for sid in rd.known_sids(cwd):
        d = rd.dossier(cwd, sid)
        if d is None:
            unrecorded.append(sid)
        else:
            views.append(session_view(rd, d))
    return views, unrecorded


def render_ledger(rd, office_root, name=None):
    """(lines, unreadable): the trust ledger per project and work class.
    It renders the evidence; it holds no grant (seed Q-6 is open)."""
    projects = office_projects(office_root)
    if not projects:
        return [no_projects_line(projects)], 0
    lines, bad = [], 0
    for p in select(projects, name):
        try:
            cwd = readable(p)
            agg = rd.aggregate(cwd)
            classes = rd.key(agg, "stats", "classes") or {}
            views, unrecorded = all_views(rd, cwd)
            lines.append(f"{p['name']}: trust ledger per work class (renders the evidence; holds no grant)")
            if not classes:
                lines.append("  no classed sessions in bale's records yet")
            header = ("class", "sessions", "applied", "HOLD rate", "first-attempt PASS", "claim agreement", "bailouts")
            rows = [header]
            notes = []
            for cls, row in sorted(classes.items()):
                sessions = rd.key(row, "stats", "classes.*.sessions")
                held = rd.key(row, "stats", "classes.*.held_attempts")
                responses = rd.key(row, "stats", "classes.*.response_attempts")
                checks = rd.key(row, "stats", "classes.*.checks")
                agree = rd.key(row, "stats", "classes.*.checks_agree")
                na = rd.key(row, "stats", "classes.*.checks_na")
                bailed = rd.key(row, "stats", "classes.*.bailout_sessions")
                with_response = rd.key(row, "stats", "classes.*.sessions_with_response_attempt")
                applied = rd.key(rd.key(rd.aggregate(cwd, cls), "stats", "closure_mix"), "stats", "closure_mix.applied")
                members = [v for v in views if v["work_class"] == cls and not v["read_only"]]
                firsts = [response_attempts(v)[0] for v in members if response_attempts(v)]
                passed = sum(1 for a in firsts if a["outcome"] == "applied")
                counted_applied = sum(1 for v in members if v["outcome"] == "applied")
                rows.append((cls, str(sessions), str(applied),
                             rate(held, responses, rd.key(row, "stats", "classes.*.hold_rate")),
                             rate(passed, len(firsts)),
                             rate(agree, checks, rd.key(row, "stats", "classes.*.agreement_rate"))
                             + (f"; {na} n/a" if na else ""),
                             f"{bailed} of {with_response}"))
                if len(members) != sessions:
                    notes.append(f"{cls}: bale's aggregate counts {sessions} session(s); "
                                 f"{len(members)} dossier(s) found for it")
                if counted_applied != applied:
                    notes.append(f"{cls}: bale's closure mix counts {applied} applied; "
                                 f"the dossiers say {counted_applied}")
            widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
            if classes:
                for r in rows:
                    lines.append("  " + "  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip())
            lines += [f"  both counts, records beside records: {n}" for n in notes]
            if unrecorded:
                lines.append(f"  in the outbox with no record: {', '.join(unrecorded)}")
        except BaleError as exc:
            bad += 1
            lines.append(f"{p['name']}: cannot read: {exc}")
    return lines, bad


def landed_paths(a, path):
    """The attempt's change paths that are the path or under it."""
    return [c for c in a["change_paths"] if c == path or c.startswith(path + "/")]


def render_landed(rd, office_root, path, name=None):
    """(lines, unreadable): for each project, the latest applied session
    whose change set held the path (or a path under it)."""
    path = path.strip().removeprefix("./").rstrip("/")
    if not path or path.startswith("/"):
        raise oh.HelperError("--landed takes a path relative to the project's root, e.g. bin/office")
    projects = office_projects(office_root)
    if not projects:
        return [no_projects_line(projects)], 0
    lines, bad = [], 0
    for p in select(projects, name):
        try:
            cwd = readable(p)
            views, _ = all_views(rd, cwd)
            hits = []
            for v in views:
                for a in response_attempts(v):
                    if a["outcome"] == "applied" and landed_paths(a, path):
                        hits.append((a["at"], v, landed_paths(a, path)))
            if not hits:
                lines.append(f"{p['name']}: no applied session in bale's records landed {path}")
                continue
            hits.sort(key=lambda h: h[0])
            at, v, paths = hits[-1]
            under = "" if paths == [path] else f", {len(paths)} path(s) under it"
            lines.append(f"{p['name']}: {path} last landed by {v['sid']} (applied {day(at)}, "
                         f"{v['work_class']}{under}); {len(hits)} applied session(s) landed it in all")
        except BaleError as exc:
            bad += 1
            lines.append(f"{p['name']}: cannot read: {exc}")
    return lines, bad


def render_versions(rd, office_root, name=None):
    """(lines, unreadable): the version trail per project: the applied
    sessions whose change set held a VERSION file, oldest first, and the
    contract-doc epochs bale's aggregate keeps."""
    projects = office_projects(office_root)
    if not projects:
        return [no_projects_line(projects)], 0
    lines, bad = [], 0
    for p in select(projects, name):
        try:
            cwd = readable(p)
            views, _ = all_views(rd, cwd)
            lines.append(f"{p['name']}: version trail")
            releases = []
            for v in views:
                for a in response_attempts(v):
                    held = [c for c in a["change_paths"] if c.rsplit("/", 1)[-1] == VERSION_FILE]
                    if a["outcome"] == "applied" and held:
                        releases.append((a["at"], v["sid"], held))
            lines.append(f"  releases: applied sessions whose change set held a {VERSION_FILE} file")
            for at, sid, held in sorted(releases):
                lines.append(f"    {day(at)}  {sid}  {', '.join(held)}")
            if not releases:
                lines.append("    none in bale's records")
            lines.append("  contract-doc epochs: the bale docs each session was packed under")
            epochs = rd.key(rd.aggregate(cwd), "stats", "doc_epochs") or {}
            for digest, row in sorted(epochs.items(),
                                      key=lambda kv: rd.key(kv[1], "stats", "doc_epochs.*.first_created_at") or ""):
                lines.append(f"    {digest} from {day(rd.key(row, 'stats', 'doc_epochs.*.first_created_at'))}: "
                             f"{rd.key(row, 'stats', 'doc_epochs.*.sessions')} session(s), "
                             f"{rd.key(row, 'stats', 'doc_epochs.*.applied')} applied, "
                             f"{rd.key(row, 'stats', 'doc_epochs.*.in_flight')} in flight")
            if not epochs:
                lines.append("    none in bale's records")
            installed = rd.key(rd.status(cwd), "status", "version")
            lines.append(f"  bale now: {installed}; bale version per session: not on bale's dossier "
                         "(a slip for bale-src)")
        except BaleError as exc:
            bad += 1
            lines.append(f"{p['name']}: cannot read: {exc}")
    return lines, bad


def status_lines(rd, office_root):
    """(lines, 0): office status's bale and projects lines. A bale
    outside the manifest's range is a line, never a refusal."""
    cons = rd.consumption
    try:
        exe = rd.bale()
        v = rd.installed_version()
        if oh.compare_versions(v, cons.floor) >= 0:
            bale = (f"bale:       {v} at {exe}; within the read side's range "
                    f"(bale {cons.floor} or later, share/{cons.path.name})")
        else:
            bale = (f"bale:       {v} at {exe}; OUTSIDE the read side's range: its reads were written "
                    f"against bale {cons.floor} or later (share/{cons.path.name}); it may fail on a key")
    except BaleError as exc:
        bale = f"bale:       {exc}"
    except oh.HelperError as exc:
        bale = f"bale:       its version could not be compared: {exc}"
    lines = [bale]
    projects = office_projects(office_root)
    if not projects:
        lines.append(f"projects:   none; {no_projects_line(projects)}")
        return lines, 0
    problems = []
    for p in projects:
        ok, text = (False, p["problem"]) if p["problem"] else oh.check_project_dir(p["resolved"])
        if not ok:
            problems.append(f"  {p['name']}: {text}")
    lines.append(f"projects:   {len(projects)} in scope"
                 + (f"; {len(problems)} cannot be read" if problems else "; each is a repo bale runs in"))
    return lines + problems, 0


# --- sending a session out: office start -------------------------------------------
#
# The office runs bale's pack when the occupant asks (the ruling of
# sitting 2026-09-29-continue-plan-002, fourth page): it is the
# occupant's hands at the terminal. It never schedules, never dispatches
# to a model and never carries pastes. What it does here: checks the
# planned forecast against the sessions open where the pack will run,
# makes every context tarball that rides beside the request, packs the
# session, and gathers every file the occupant attaches into one out
# tray. Context packs come first, because they open nothing: a failure
# there leaves no session open.

# The constraint every project session an office packs carries
# (doctrine section 2), verbatim.
PROJECT_CONSTRAINT = "Office context informs this session but never lands in this project."


class StartError(Exception):
    """office start cannot go on, said as lines a person can act on."""

    def __init__(self, lines):
        super().__init__("\n".join(lines))
        self.lines = lines


def forecast_overlap(mine, theirs):
    """The entries of two forecasts that overlap: equal, or one a
    directory holding the other. None stands for the whole tree (a pack
    with no --write and no --include); [] overlaps nothing."""
    def norm(e):
        return e.strip().strip("/")
    if mine is None and theirs is None:
        return ["the whole tree"]
    if mine is None:
        return [norm(t) for t in theirs]
    if theirs is None:
        return [norm(m) for m in mine]
    out = []
    for m in mine:
        for t in theirs:
            a, b = norm(m), norm(t)
            if a in ("", ".") or b in ("", ".") or a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                out.append(a if len(a) >= len(b) else b)
    return sorted(set(out))


def open_overlaps(rd, cwd, mine):
    """[(sid, their forecast, overlapping entries)] for the sessions open
    in the repo at cwd whose recorded forecast overlaps mine. A repo bale
    has never run in has no registry and nothing open."""
    if not (pathlib.Path(cwd) / ".bale").is_dir():
        return []
    st = rd.status(cwd)
    scopes = rd.key(st, "status", "scopes") or {}
    out = []
    for sid in rd.key(st, "status", "sessions") or []:
        theirs = scopes.get(sid)
        if theirs == []:
            continue
        hit = forecast_overlap(mine, theirs)
        if hit:
            out.append((sid, theirs, hit))
    return out


def opener_lines(stderr_lines, spec):
    """The paste-ready opener bale prints between its scissor lines, the
    lines bale itself asks a person to copy; None when bale printed no
    such block. The --json report carries no opener (a slip for
    bale-src), so these markers, declared in the consumption manifest,
    are the one place it is found."""
    begin, end = spec["opener"]
    try:
        a = stderr_lines.index(begin)
        b = stderr_lines.index(end, a + 1)
    except ValueError:
        return None
    return stderr_lines[a + 1:b]


def git_top(path):
    """The top of the git work tree holding path, or None."""
    p = pathlib.Path(path)
    where = p if p.is_dir() else p.parent
    try:
        proc = subprocess.run(["git", "-C", str(where), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return pathlib.Path(proc.stdout.strip()).resolve() if proc.returncode == 0 else None


def ride_plan(path):
    """How one ride-along reaches the out tray: ("pack", directory,
    include or None) for a context pack run in that directory, or
    ("copy", path, None) for a file outside any repo, copied as it is.
    A directory outside git is packed from a scratch copy ("scratch"),
    so the office writes nothing into it; a path inside a repo is packed
    from the repo's top with --include, whose outbox .bale/ ignores."""
    p = pathlib.Path(path).resolve()
    if not p.exists():
        raise StartError([f"a declared ride-along is not on this machine: {path} "
                          "(office projects set changes what rides)"])
    top = git_top(p)
    if top is None:
        return ("copy", p, None) if p.is_file() else ("scratch", p, None)
    if p == top:
        return ("pack", top, None)
    return ("pack", top, str(p.relative_to(top)))


class Tray:
    """The out tray being filled: a staging directory beside its final
    place, renamed to the session id once the session is packed."""

    def __init__(self, root):
        self.root = pathlib.Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix=".filling-", dir=self.root))
        self.files = []

    def take(self, src, name=None):
        name = name or pathlib.Path(src).name
        stem, dot, ext = name.partition(".")
        n = 1
        while (self.dir / name).exists():
            n += 1
            name = f"{stem}-{n}{dot}{ext}"
        shutil.copy2(src, self.dir / name)
        self.files.append(name)
        log(f"out tray: {name}")
        return name

    def finish(self, sid):
        """Name the tray for the session. bale's ids are unique within
        one repo only, so a tray already named so (the same folder's
        session in another repo, the same day) gets the next free
        name rather than failing a session that is already open."""
        final, n = self.root / sid, 1
        while final.exists():
            n += 1
            final = self.root / f"{sid}-{n}"
        self.dir.rename(final)
        self.dir = final
        return final

    def discard(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def context_into_tray(rd, tray, directory, includes, what):
    """One context pack in directory, its tarball copied into the tray."""
    report, _ = rd.pack("context", directory, includes=includes or None)
    tarball = rd.key(report, "context", "tarball")
    name = tray.take(tarball, f"context-{rd.key(report, 'context', 'tree_name')}.tar.gz")
    return f"{name}: {what}"


def scratch_context(rd, tray, source, what):
    """A context pack of a directory outside git, made from a scratch
    copy under the same name, so nothing is written into the original
    (the install's doctrine directory among them)."""
    with tempfile.TemporaryDirectory(prefix="office-start-") as tmp:
        copy = pathlib.Path(tmp) / pathlib.Path(source).name
        shutil.copytree(source, copy, ignore=shutil.ignore_patterns(".bale", "__pycache__"))
        return context_into_tray(rd, tray, copy, None, what)


def start(rd, office_root, folder, where, project, goal, slug, includes, writes, read_only,
          brief, work_class, tray_root):
    """Pack a session for a folder and fill its out tray. Returns a dict:
    sid, tray, files, opener (lines, or None), carried (what each file
    is). Raises StartError with lines to print when it cannot go on."""
    office_root = pathlib.Path(office_root).resolve()
    manifest = oh.read_toml(office_root / "floor-plan" / "manifest.toml")
    projects = {p["name"]: p for p in oh.read_projects(manifest) or []}
    entry = None
    if project:
        entry = projects.get(project)
        if entry is None:
            raise StartError([f"no project named {project} in this office's [projects] "
                              f"(it lists: {', '.join(sorted(projects)) or 'none'})"])
        problems = [entry["problem"]] if entry["problem"] else []
        problems += entry["declaration_problems"]
        if problems:
            raise StartError([f"{project}: {p}" for p in problems])
    rd.bale()

    # Where the pack runs, and its forecast.
    if where == "office":
        pack_dir = office_root
        includes = [folder, *includes]
        if read_only:
            forecast = []
        else:
            writes = [folder] + (["notepad"] if (office_root / "notepad").is_dir() else []) + list(writes)
            forecast = writes
    else:
        pack_dir = entry["resolved"]
        ok, why = oh.check_project_dir(pack_dir)
        if not ok:
            raise StartError([f"{project} cannot be packed: {why}"])
        forecast = [] if read_only else (list(writes) or list(includes) or None)
    for p in (writes if not read_only else []):
        if not (pathlib.Path(pack_dir) / p).exists():
            raise StartError([f"--write {p}: no such path in {pack_dir}; a forecast names existing paths "
                              "(a directory covers new files under it)"])
    for p in includes:
        if not (pathlib.Path(pack_dir) / p).exists():
            raise StartError([f"--include {p}: no such path in {pack_dir}"])

    # The predictable refusal, said plainly before bale is asked: two
    # sessions whose forecasts overlap never run beside each other.
    naming = folders_naming(office_root)
    clash = open_overlaps(rd, pack_dir, forecast)
    if clash:
        label = "this office" if where == "office" else project
        lines = []
        for sid, theirs, hit in clash:
            folders = ", ".join(naming.get(sid, [])) or "no folder records it"
            lines.append(f"{sid} is open in {label} ({folders}); its forecast ({', '.join(theirs)}) "
                         f"overlaps this one at {', '.join(hit)}")
        if where == "office" and any("notepad" in h for _, _, h in clash):
            lines.append("office sessions take turns on the notepad: land or close the open one first "
                         "(bale apply its response, or bale unlock SID if it was abandoned), "
                         "or start this one --read-only")
        else:
            lines.append("land or close it first (bale apply its response, or bale unlock SID if it was "
                         "abandoned), or narrow this one's forecast with --write")
        raise StartError(lines)

    tray = Tray(tray_root)
    carried = []
    stage = "a context pack"
    try:
        # The doctrine, from a scratch copy: the install is never written.
        carried.append(scratch_context(rd, tray, INSTALL / "doctrine", "the doctrine (OFFICE.md and its checks)"))
        if where == "project":
            # The office's context rides beside the request, never inside
            # it: the folder and the hung items, named, because include
            # groups do not fire under --context.
            hung = [h for h in oh.space_paths(manifest, "hung") if (office_root / h).exists()]
            carried.append(context_into_tray(rd, tray, office_root, [folder, *hung],
                                              f"the office: {folder} and the hung items"))
        elif entry is not None:
            # An office session about a project reads the project's tree.
            carried.append(context_into_tray(rd, tray, entry["resolved"], None, f"{project}'s tree"))
        if entry is not None:
            grouped = {}
            for ride in entry["rides"]:
                kind, place, inc = ride_plan(oh.expand_project_path(ride))
                if kind == "copy":
                    carried.append(f"{tray.take(place)}: rides with {project} ({ride})")
                elif kind == "scratch":
                    carried.append(scratch_context(rd, tray, place, f"rides with {project} ({ride})"))
                else:
                    grouped.setdefault(place, []).append(inc)
            for place, incs in grouped.items():
                whole = None in incs
                carried.append(context_into_tray(rd, tray, place, None if whole else incs,
                                                  f"rides with {project} ({place}"
                                                  + ("" if whole else ": " + ", ".join(incs)) + ")"))
        # The session itself, last.
        stage = "the session's pack"
        spec = rd.consumption.surface("pack")
        report, stderr = rd.pack(
            "pack", pack_dir, goal=goal, slug=slug, includes=includes or None,
            writes=None if read_only else (forecast if where == "office" else (list(writes) or None)),
            constraints=[PROJECT_CONSTRAINT] if where == "project" else None,
            readme_file=str(pathlib.Path(brief).resolve()) if brief else None,
            no_readme=not brief, read_only=read_only, work_class=work_class)
    except BaleError as exc:
        tray.discard()
        raise StartError([f"{stage} failed, so no session was opened and no out tray was made: {exc}"])
    except StartError:
        tray.discard()
        raise
    except (OSError, shutil.Error) as exc:
        tray.discard()
        raise StartError([f"{stage} could not be put in the out tray, so no session was opened: {exc}"])
    sid = rd.key(report, "pack", "sid")
    if not isinstance(sid, str) or not oh.SID_RE.match(sid):
        raise StartError([f"bale packed, but its report's sid is not a session id: {sid!r}; "
                          f"what was gathered is in {tray.dir}"])
    try:
        name = tray.take(rd.key(report, "pack", "tarball"))
        final = tray.finish(sid)
    except (OSError, shutil.Error) as exc:
        raise StartError([f"session {sid} is open, but its out tray could not be finished: {exc}",
                          f"what was gathered is in {tray.dir}; the request is {rd.key(report, 'pack', 'tarball')}",
                          f"record the session in its folder with: office sessions {pathlib.Path(folder).name} {sid}"])
    carried.insert(0, f"{name}: the request ({'an office session' if where == 'office' else project + ' session'})")
    return {"sid": sid, "tray": str(final), "files": sorted(tray.files), "carried": carried,
            "opener": opener_lines(stderr, spec), "pack_dir": str(pack_dir)}


# --- command line --------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_bale.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("in-flight"); p.add_argument("office")
    p.add_argument("--now", help="an ISO timestamp to measure ages from (default: now)")
    p = sub.add_parser("folder-sessions"); p.add_argument("office"); p.add_argument("folder_md")
    p = sub.add_parser("ledger"); p.add_argument("office"); p.add_argument("--project")
    p = sub.add_parser("landed"); p.add_argument("office"); p.add_argument("path"); p.add_argument("--project")
    p = sub.add_parser("versions"); p.add_argument("office"); p.add_argument("--project")
    p = sub.add_parser("status-lines"); p.add_argument("office")
    p = sub.add_parser("desk"); p.add_argument("office"); p.add_argument("--today", required=True)
    p.add_argument("--since", help="the day of the previous walk-in (default: today)")
    p.add_argument("--walk-in", action="store_true", help="In flight and the first ready folders only")
    p = sub.add_parser("writers"); p.add_argument("office"); p.add_argument("paths", nargs="+")
    p = sub.add_parser("start", help="pack a session for a folder and fill its out tray; one JSON line on stdout")
    p.add_argument("office"); p.add_argument("folder", help="desk/NAME")
    p.add_argument("--where", choices=("office", "project"), required=True)
    p.add_argument("--project", default=None, help="the project it is on, or the one an office session is about")
    p.add_argument("--goal", required=True); p.add_argument("--slug", required=True)
    p.add_argument("--include", action="append", default=[]); p.add_argument("--write", action="append", default=[])
    p.add_argument("--read-only", action="store_true"); p.add_argument("--brief")
    p.add_argument("--work-class"); p.add_argument("--tray-root", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "start":
        try:
            result = start(Reader(), a.office, a.folder, a.where, a.project, a.goal, a.slug, a.include,
                           a.write, a.read_only, a.brief, a.work_class, a.tray_root)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, BaleError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        print(json.dumps(result))
        return 0
    try:
        rd = Reader()
        if a.cmd == "writers":
            # The one-writer rule: exit 3 and one line per session whose
            # forecast holds a path, 0 when none does or there is no
            # registry, 1 when the registry cannot be read.
            held = writers_holding(rd, a.office, a.paths)
            for sid, target, forecast in held:
                print(f"{sid} holds {target} (its forecast: {', '.join(forecast)})")
            return 3 if held else 0
        if a.cmd == "desk":
            for day in (a.today, a.since):
                if day is not None:
                    dt.date.fromisoformat(day)
            lines, bad = render_desk(rd, a.office, a.today, a.since, a.walk_in)
        elif a.cmd == "in-flight":
            now = parse_stamp(a.now) if a.now else None
            lines, bad = render_in_flight(rd, a.office, now)
        elif a.cmd == "folder-sessions":
            lines, bad = render_folder_sessions(rd, a.office, a.folder_md)
        elif a.cmd == "ledger":
            lines, bad = render_ledger(rd, a.office, a.project)
        elif a.cmd == "landed":
            lines, bad = render_landed(rd, a.office, a.path, a.project)
        elif a.cmd == "versions":
            lines, bad = render_versions(rd, a.office, a.project)
        else:
            lines, bad = status_lines(rd, a.office)
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except BaleError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError) as exc:
        log(f"error: {exc}")
        return 2
    for line in lines:
        print(line)
    # The lines already say which project could not be read and why;
    # the exit code tells the caller, which decides how loud to be.
    return 3 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
