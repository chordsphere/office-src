#!/usr/bin/env python3
"""office digest: the sitting-open page, drafting-table/digest.md.

A sitting opens on one page, not on the ledgers (the drafting-table
blueprint's section 3.1). Every section is computed when the page is
written, from bale's records (through office_bale's reader and the
--json surfaces share/bale-consumption.toml declares), from git, and
from the drafting table and the desk; nothing on it is a hand list, and
a number that can go stale is computed here, never written down
(doctrine section 13). The page is overwritten on every run and never
edited by hand, like the survey.

The seven sections, in order: versions per project; since the last
sitting; the watches (office watches check's own lines, never
recorded); the standing lines; the desk (in flight, the first five
ready, parked by gate); the agenda (open items, oldest first); the open
blueprints.

When the last sitting was. A sitting's words are filed as a notepad
page named for it (notepad/DATE-SLUG.md, office start files it from the
brief of a session the sitting authored; the sitting's later pages are
SID-2.md, SID-3.md). The window opens at the commit that filed the
latest such page, which is when that sitting's words reached the office,
and the page says so, naming the page and the commit, so a reader can
disagree. An office with no sitting's page yet has a window that opens
at its first commit.

Sessions since then, per place (the office's own registry and each
project): bale's commit subjects since the window's start, in the shape
the consumption manifest declares (a slip for bale-src: the shape is a
convention), name the sessions that landed, were swept or committed
anything; with the sessions open now, those are the sessions whose
dossiers are read, and each one's outcome and times come from its
dossier, never from the subject.

Standard library only. The command line writes the page, prints it on
stdout, logs to stderr with an [office] prefix, and exits 0 when it
wrote the page, 3 when it wrote it but a place could not be read (the
page says which), 1 on a refusal and 2 on an internal error.
"""

import argparse
import datetime as dt
import os
import pathlib
import subprocess
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_drafting as od  # noqa: E402
import office_bale as ob  # noqa: E402
import office_watches as ow  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
PAGE = f"{od.SPACE}/digest.md"
READY_SHOWN = 5
# A long window (an office with no sitting's page, or a project that
# landed a great deal) reads at most this many dossiers per place, and
# says how many it left unread.
DOSSIER_CAP = 60
OUTCOME_WORDS = {"applied": "applied", "held": "held", "bailout": "bailed", "reverted": "reverted"}


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


def git(root, *args):
    """git's stdout in root, or None when git refuses (not a repo, no
    such commit)."""
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        debug(f"git {' '.join(args)} in {root}: {proc.stderr.strip()}")
        return None
    return proc.stdout


# --- the window ------------------------------------------------------------------------

def window(root):
    """The window's start: a dict with when (aware), base (the commit the
    office is compared against), and words saying how it was found."""
    filings = ow.sitting_filings(root)
    if filings:
        when, page, sha, subject, _ = filings[-1]
        return {"when": when, "base": sha, "filings": filings,
                "words": (f"since {when.isoformat()}, when {page} was filed by commit {sha[:7]} "
                          f"(\"{subject}\"): the latest sitting's page in the notepad, by the commit that "
                          "filed it. A later filing moves the window; a sitting that files no page does not.")}
    first = git(root, "log", "--reverse", "--format=%H%x09%cI", "--max-parents=0")
    if first:
        sha, when = first.splitlines()[0].split("\t")
        when = dt.datetime.fromisoformat(when)
        return {"when": when, "base": None, "filings": filings or [],
                "words": (f"since {when.isoformat()}, the office's first commit: no sitting's page "
                          "(notepad/DATE-SLUG.md) is filed in this office yet, so everything counts.")}
    return {"when": None, "base": None, "filings": [],
            "words": "since the beginning: this office is not a git repo with commits, so no window could be read."}


# --- sections ----------------------------------------------------------------------------

def versions(rd, root, here):
    out = ["## Versions", ""]
    try:
        manifest = oh.read_toml(pathlib.Path(root) / "floor-plan" / "manifest.toml")
        stamp = oh.office_stamp(manifest)["migrated_to"]
    except (oh.HelperError, OSError) as exc:
        stamp = f"unreadable ({exc})"
    install = (INSTALL / "VERSION").read_text(encoding="utf-8").strip()
    out.append(f"- office: migrated to office-src {stamp}; office-src {install} installed here")
    try:
        out.append(f"- bale: {rd.installed_version()} installed (the read side's floor is bale "
                   f"{rd.consumption.floor})")
    except ob.BaleError as exc:
        out.append(f"- bale: {exc}")
    for label, p in here:
        if label == ob.OFFICE_LABEL:
            continue
        try:
            cwd = ob.readable(p)
            out.append(f"- {label}: {release(rd, cwd)}; {epoch(rd, cwd)}")
        except ob.BaleError as exc:
            out.append(f"- {label}: cannot read: {exc}")
    out.append("- the bale version each session ran under: not on bale's dossier (a slip for bale-src)")
    return out


def release(rd, cwd):
    """The project's latest release: the last commit that changed a
    VERSION file, the version it wrote, and the session that wrote it."""
    text = git(cwd, "log", "-1", "--format=%H%x09%cI%x09%s", "--name-only", "--", ob.VERSION_FILE,
               f"*/{ob.VERSION_FILE}")
    if not text or not text.strip():
        return f"no commit has changed a {ob.VERSION_FILE} file"
    lines = [l for l in text.splitlines() if l.strip()]
    sha, when, subject = lines[0].split("\t", 2)
    path = next((l for l in lines[1:] if l.rsplit("/", 1)[-1] == ob.VERSION_FILE), ob.VERSION_FILE)
    shown = git(cwd, "show", f"{sha}:{path}")
    version = shown.strip().splitlines()[0] if shown and shown.strip() else "(removed)"
    found = rd.consumption.subject_sid(subject)
    by = f"by {found[1]}" if found and found[0] == "work" else f"in commit {sha[:7]}"
    return f"release {version} ({path}) landed {by} on {when[:10]}"


def epoch(rd, cwd):
    agg = rd.aggregate(cwd)
    epochs = rd.key(agg, "stats", "doc_epochs") or {}
    # bale keys an epoch by the digest of the contract docs its sessions
    # were packed under; "unstamped" holds sessions with no stamp yet
    # (packed and still open, say), which is no epoch to report.
    stamped = [(rd.key(row, "stats", "doc_epochs.*.first_created_at") or "", digest, row)
               for digest, row in epochs.items() if digest != "unstamped"]
    waiting = epochs.get("unstamped")
    tail = (f"; {rd.key(waiting, 'stats', 'doc_epochs.*.sessions')} session(s) not stamped yet"
            if waiting is not None else "")
    if not stamped:
        return "no session in bale's records is stamped with bale's contract docs yet" + tail
    first, digest, row = max(stamped)
    return (f"the latest sessions were packed under bale's contract docs {digest}, since {ob.day(first)} "
            f"({rd.key(row, 'stats', 'doc_epochs.*.sessions')} session(s); {len(stamped)} epoch(s) in all)"
            + tail)


def sessions_since(rd, root, label, p, start):
    """One line per place: what landed, held, bailed or closed since the
    window's start, and what is open now, from the dossiers."""
    try:
        cwd = ob.readable(p)
        open_now = rd.open_sessions(cwd)
    except ob.BaleError as exc:
        return f"- {label}: cannot read: {exc}", True
    sids = {sid for sid, _ in open_now}
    if start is not None:
        subjects = git(cwd, "log", f"--since={start.isoformat()}", "--format=%s")
    else:
        subjects = git(cwd, "log", "--format=%s")
    for s in (subjects or "").splitlines():
        found = rd.consumption.subject_sid(s)
        if found:
            sids.add(found[1])
    ordered = sorted(sids)
    skipped = ordered[DOSSIER_CAP:]
    groups = {"applied": [], "held": [], "bailed": [], "reverted": [], "closed": []}
    try:
        for sid in ordered[:DOSSIER_CAP]:
            d = rd.dossier(cwd, sid)
            if d is None:
                continue
            v = ob.session_view(rd, d)
            seen = set()
            for a in v["attempts"]:
                if start is not None and ob.parse_stamp(a["at"]) < start:
                    continue
                o = a["outcome"]
                if o in OUTCOME_WORDS:
                    word = OUTCOME_WORDS[o]
                    if word not in seen:
                        groups[word].append(sid)
                        seen.add(word)
                elif a["command"] not in ("pack", "open") and not v["in_flight"] and "closed" not in seen:
                    groups["closed"].append(f"{sid} ({ob.outcome_word(v)})")
                    seen.add("closed")
    except ob.BaleError as exc:
        return f"- {label}: cannot read: {exc}", True
    parts = []
    for word in ("applied", "held", "bailed", "reverted", "closed"):
        if groups[word]:
            parts.append(f"{word if word != 'closed' else 'closed otherwise'} {', '.join(groups[word])}")
    flying = [f"{sid}{' (read-only)' if ro else ''}" for sid, ro in open_now]
    parts.append("still open " + (", ".join(flying) if flying else "none"))
    if len(parts) == 1 and not any(groups.values()):
        parts.insert(0, "nothing landed, held, bailed or closed")
    line = f"- {label}: " + "; ".join(parts)
    if skipped:
        line += f"; and {len(skipped)} more session(s) bale's commits name, not read (the window is long)"
    return line, False


def base_lines(root, base, rel):
    """A page's lines at the base commit, [] when it had none there."""
    if base is None:
        return []
    text = git(root, "show", f"{base}:{rel}")
    return text.splitlines() if text is not None else []


def base_folders(root, base):
    """{(space, name)} of the folders at the base commit."""
    if base is None:
        return set()
    text = git(root, "ls-tree", "-r", "--name-only", base, "--", "desk", "filing-cabinet") or ""
    out = set()
    for line in text.splitlines():
        parts = line.split("/")
        if len(parts) == 3 and parts[2] == "folder.md":
            out.add((parts[0], parts[1]))
    return out


def folders_moved(root, base):
    then = base_folders(root, base)
    then_desk = {n for s, n in then if s == "desk"}
    then_cab = {n for s, n in then if s == "filing-cabinet"}
    now = [f for f in oh.read_folders(root)]
    out = {"opened": [], "closed": [], "born done": [], "reopened": []}
    for f in now:
        name, cite = f["name"], (oh.cite(f) if not f["problem"] else f["name"])
        shown = cite if cite == name else f"{cite} ({name})"
        status = f.get("status") or "no status line"
        if f["space"] == "desk":
            if name in then_cab:
                out["reopened"].append(shown)
            elif name not in then_desk:
                out["opened"].append(f"{shown}, {status}")
        else:
            if name in then_desk:
                out["closed"].append(f"{shown}, {status}")
            elif name not in then_cab:
                out["born done"].append(f"{shown}, {status}")
    parts = [f"{k} {'; '.join(v)}" for k, v in out.items() if v]
    return "- folders: " + ("; ".join(parts) if parts else "none opened, closed or reopened")


def drafting_added(root, base):
    """What the sittings and the scripts added to the drafting table
    since the base: counted by record, base against now."""
    t = od.Table(root)
    page = lambda name: base_lines(root, base, f"{od.SPACE}/{name}")  # noqa: E731
    ruling_key = lambda r: (r["id"], r["kind"], r.get("day"), r["line"])  # noqa: E731
    before = {ruling_key(r) for r in od.records(page("rulings.md"), od.RULING_HEAD_RE, od.Table._ruling)}
    rulings = [r for r in t.rulings() if r["kind"] != "unreadable" and ruling_key(r) not in before]
    ev_key = lambda r: (r["number"], r["kind"], r.get("day"), r["line"])  # noqa: E731
    ev_before = {ev_key(r) for r in od.evidence_records(page("evidence.md"))}
    evidence = [r for r in t.evidence() if r["kind"] != "unreadable" and ev_key(r) not in ev_before]
    log_before = {e[:4] for e in ow.events(page("watch-log.md"))[0]}
    log_now = ow.events(od.read_lines(pathlib.Path(root) / ow.LOG))[0]
    log_new = [e for e in log_now if e[:4] not in log_before]
    riders_before = od.rider_numbers(page("riders.md"))
    riders_now = {r["number"] for r in t.riders()} | set(t.pointers())
    entries_b, disposed_b = od.agenda_records(page("agenda.md"))
    entries_n, disposed_n = t.agenda()
    agenda_new = sorted((set(entries_n) | set(disposed_n)) - set(entries_b) - set(disposed_b))
    disposed_new = sorted(set(disposed_n) - set(disposed_b))
    tree = (git(root, "ls-tree", "-r", "--name-only", base, "--", od.BLUEPRINTS) or "") if base else ""
    bp_then = {l.split("/")[2] for l in tree.splitlines() if l.endswith("/blueprint.md")}
    closed_then = {l.split("/")[2] for l in tree.splitlines() if l.endswith("/close.md")}
    bps = t.blueprints()
    words = []
    kinds = {}
    for r in rulings:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    words.append("rulings: " + (", ".join(f"{n} {k}(s)" for k, n in sorted(kinds.items())) or "none"))
    words.append(f"evidence records: {len(evidence)}" + (" (" + ", ".join(
        f"{r['kind']} {r['number']}" for r in evidence) + ")" if evidence else ""))
    verbs = {}
    for e in log_new:
        verbs[e[2]] = verbs.get(e[2], 0) + 1
    words.append("watch-log records: " + (", ".join(f"{n} {v}" for v, n in sorted(verbs.items())) or "none"))
    new_riders = sorted(riders_now - riders_before)
    words.append(f"riders: {len(new_riders)}" + (f" (rider {', '.join(map(str, new_riders))})" if new_riders else ""))
    words.append(f"agenda items: {len(agenda_new)} added, {len(disposed_new)} disposed")
    opened = sorted(set(bps) - bp_then)
    closed = sorted(b for b, f in bps.items() if f["closed"] and b not in closed_then)
    words.append(f"blueprints: {len(opened)} opened, {len(closed)} closed")
    return "- drafting table: " + "; ".join(words)


def since_section(rd, root, here, win):
    out = ["## Since the last sitting", "", f"The window: {win['words']}", ""]
    bad = False
    sources = here if here else []
    if not sources:
        out.append("- sessions: this office reads no bale registry (bale keeps none in it, and it scopes no "
                   "projects)")
    for label, p in sources:
        line, broke = sessions_since(rd, root, label, p, win["when"])
        out.append(line)
        bad = bad or broke
    out.append(folders_moved(root, win["base"]))
    out.append(drafting_added(root, win["base"]))
    return out, bad


def watch_sections(result):
    out = ["## Watches", ""]
    lines = result["watch_lines"] or (
        [f"no watches register in this office yet: only a sitting writes watches, on {ow.REGISTER}"]
        if not result["page"] else [f"{ow.REGISTER} holds no open watch"])
    out += [f"- {l}" for l in lines]
    flagged = [f"W{n}" for n, c in sorted(result["eyes"].items()) if c >= ow.EYE_SITTINGS]
    if flagged:
        out.append(f"- unlooked-at for {ow.EYE_SITTINGS} sittings or more: {', '.join(flagged)}")
    out += [f"- does not read: {p}" for p in result["problems"]]
    out += ["", "## Standing lines", ""]
    out += [f"- {l}" for l in result["standing_lines"]] or ["- none"]
    return out


def desk_section(rd, root, today):
    out = ["## The desk", ""]
    flight, bad, flying = ob.in_flight(rd, root)
    table = od.Table(root)
    groups = ob.classify_desk(oh.read_folders(root), flying, today, table)
    out.append("In flight:")
    out += [f"- {l}" for l in flight]
    out += [f"- {ob.folder_line(f)}  [open, no session in flight]" for f in groups["open"]]
    out += ["", f"Ready ({len(groups['ready'])}; the first {READY_SHOWN} in the desk's order):"]
    out += [f"- {e}" for e in groups["ready_errors"]]
    out += [f"- {ob.folder_line(f)}" for f in groups["ready"][:READY_SHOWN]] or ["- none"]
    if len(groups["ready"]) > READY_SHOWN:
        out.append(f"- and {len(groups['ready']) - READY_SHOWN} more (office desk)")
    out += ["", "Parked, by gate:"]
    if not groups["parked"]:
        out.append("- none")
    for heading in sorted(groups["parked"], key=lambda h: (not h.startswith("ERROR"), h)):
        out.append(f"- {heading}")
        out += [f"  - {ob.folder_line(f)}" for f, _ in groups["parked"][heading]]
    if groups["candidates"]:
        out += ["", f"Candidates: {len(groups['candidates'])} (office desk lists them)"]
    return out, bad > 0


def agenda_section(root):
    out = ["## The agenda", ""]
    entries, disposed = od.Table(root).agenda()
    open_items = [entries[n] for n in sorted(entries) if n not in disposed]
    if not (pathlib.Path(root) / od.SPACE / "agenda.md").is_file():
        return out + ["- no agenda in this office yet (office agenda add puts a question on it)"]
    if not open_items:
        return out + ["- nothing awaits a sitting"]
    for e in open_items:
        extra = []
        if od.first(e["fields"], "source"):
            extra.append(f"source {od.first(e['fields'], 'source')}")
        if od.first(e["fields"], "waiting"):
            extra.append(f"waiting {od.first(e['fields'], 'waiting')}")
        out.append(f"- agenda {e['number']} - {e['title']}" + (f" ({'; '.join(extra)})" if extra else ""))
    return out


def blueprints_section(root):
    out = ["## Open blueprints", ""]
    t = od.Table(root)
    shown = 0
    by_rel = {f["rel"]: f for f in t.folders()}
    for bid, b in t.blueprints().items():
        if b["closed"]:
            continue
        shown += 1
        state = f"ratified {b['ratified'][0]}" if b["ratified"] else "not ratified"
        members = []
        for rel in od.blueprint_members(t, bid):
            f = by_rel.get(rel)
            if f is None or f["problem"]:
                members.append(f"{rel} (cannot be read)")
            else:
                members.append(f"{oh.cite(f)} {f.get('status') or 'no status line'}")
        open_lines = sum(1 for d in b["decomposition"] if d["folder"] is None)
        tail = (f"; {open_lines} decomposition line(s) with no folder yet" if open_lines else "")
        out.append(f"- blueprint {bid}: {b['title']} ({state}); members: "
                   + (", ".join(members) if members else "none yet") + tail)
    if not shown:
        out.append("- none")
    return out


# --- the page -------------------------------------------------------------------------------

def render(rd, root, now, tz_name):
    """(text, bad): the whole page, and whether a place could not be
    read. Each section stands alone: one that fails says why on the page
    and the rest are still written."""
    root = pathlib.Path(root)
    tz = ow.zone(tz_name)
    today = now.astimezone(tz).date().isoformat()
    name = "(unnamed)"
    try:
        name = oh.read_toml(root / "floor-plan" / "manifest.toml").get("office", {}).get("name", name)
    except (oh.HelperError, OSError) as exc:
        debug(f"the floor plan could not be read for the office's name: {exc}")
    win = window(root)
    here = ow.places(root)
    bad = False
    out = ["# Digest", "",
           "Written by office digest and overwritten on every run, the way the survey is. Never edit by hand;",
           "run office digest again instead. Every line is computed when the page is written, from bale's",
           "records, git, the desk and the drafting table; nothing here is a source to cite (cite the",
           "session id, the folder, the ruling), and no number on it is written down anywhere else.", "",
           f"- written_at: {now.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
           f" ({now.astimezone(tz).strftime('%Y-%m-%d %H:%M')} {tz_name})",
           f"- office: {name}", ""]

    def section(fn, *args):
        nonlocal bad
        try:
            got = fn(*args)
        except (ob.BaleError, oh.HelperError, OSError, ValueError, tomllib.TOMLDecodeError) as exc:
            bad = True
            return [f"## {fn.__name__.replace('_', ' ')}", "", f"- could not be written: {exc}"]
        if isinstance(got, tuple):
            lines, broke = got
            bad = bad or broke
            return lines
        return got

    out += section(versions, rd, root, here) + [""]
    out += section(since_section, rd, root, here, win) + [""]
    try:
        result = ow.check(rd, root, tz_name, filings=win["filings"])
        bad = bad or bool(result["bad"])
        out += watch_sections(result) + [""]
    except (oh.HelperError, OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        bad = True
        out += ["## Watches", "", f"- could not be checked: {exc}", "", "## Standing lines", "",
                "- could not be computed (the watches' error above)", ""]
    out += section(desk_section, rd, root, today) + [""]
    out += section(agenda_section, root) + [""]
    out += section(blueprints_section, root)
    text = oh.ascii_escape("\n".join(out).rstrip("\n") + "\n")[0]
    return text, bad


def write(root, text):
    """Write the page, the drafting table arriving first when it has not
    (the digest is a verb that writes it). Returns (changed, words)."""
    changed, words = od.arrive(root)
    p = pathlib.Path(root) / PAGE
    old = p.read_bytes() if p.is_file() else None
    p.write_text(text, encoding="ascii")
    if old != text.encode("ascii"):
        changed.append(PAGE)
    return sorted(set(changed)), words


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_digest.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("root")
    ap.add_argument("--tz", required=True, help="the office's timezone")
    ap.add_argument("--now", help="an ISO timestamp to write the page as of (default: now)")
    ap.add_argument("--changed", help="write the paths changed here, one per line")
    ap.add_argument("--print", action="store_true", help="print the page on stdout")
    a = ap.parse_args(argv)
    try:
        now = dt.datetime.fromisoformat(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
        if now.tzinfo is None:
            raise ValueError(f"--now {a.now} names no offset")
        text, bad = render(ob.Reader(), a.root, now, a.tz)
        changed, words = write(a.root, text)
        for w in words:
            log(w)
        if a.changed:
            pathlib.Path(a.changed).write_text("".join(c + "\n" for c in changed), encoding="utf-8")
        if a.print:
            sys.stdout.write(text)
        return 3 if bad else 0
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        log(f"error: {exc.__class__.__name__}: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
