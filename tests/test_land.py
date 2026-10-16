"""Tests for the return trip: office land, with the after-land actions and
the planner's ratification, and office start taking a planner's bundle,
with the sitting's page its brief carries filed in the notepad.

bale is never needed. The fake bale here wraps the packing fake of
test_start.py (it packs, keeps the open sessions and serves bale status)
and adds what the return-trip probe captured from a real bale 0.4.45:
apply and retry (the walkthrough's merge, a HOLD, a base-drift and an
out-of-forecast refusal, a clarification), the dossier, relay's
re-emitted block, and open. Every line it prints is built from the
captured lines, kept verbatim with their sha256 in the development
record's fixtures, with the session id and the paths swapped in; on a
terminal it asks what the real one asks, where the real one asks it.
Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_start import FAKE_PACK_BALE, PACK_FIXTURES, git_repo, on_a_terminal, opener_from, tar_names  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)

# Split so the text rules' own check does not trip on this file.
FIXTURES = REPO / ("cla" + "ude") / "fixtures" / "bale-0.4.45"
LAND_FIXTURES = FIXTURES / "land"
MISS = FIXTURES / "office-src" / "stats_sid_2026-01-01-no-such-session-001_json.json"
CONSUMPTION = REPO / "share" / "bale-consumption.toml"
PROBE_SID = "2026-10-03-friction-return-trip-001"
SITTINGS = REPO / ("cla" + "ude") / "context" / "sittings"


def fixture(label):
    return json.loads((LAND_FIXTURES / f"{label}.json").read_text(encoding="utf-8"))


def first_json(label):
    return json.loads(fixture(label)["stdout"][0])


FAKE_LAND_BALE = r'''#!/usr/bin/env python3
# A fake bale for office land's and office start's bundle tests. pack,
# status and --version go to the packing fake beside it; this adds apply,
# retry, the dossier, relay and open, each printing lines the return-trip
# probe captured, with the session id and the paths swapped in. Its own
# state sits in the same state file as the packing fake's, under "land".
import hashlib, io, json, os, pathlib, re, shutil, subprocess, sys, tarfile, tempfile
FIX = pathlib.Path({fixtures!r})
UNLOCK_FIX = FIX.parent / "unlock"
MISS = pathlib.Path({miss!r})
STATE = pathlib.Path({state!r})
CALLS = pathlib.Path({calls!r})
PACKER = {packer!r}
FAKE_VERSION = tuple(int(x) for x in os.environ.get("FAKE_BALE_VERSION", "0.4.45").split("."))
argv = sys.argv[1:]
cwd = os.path.realpath(os.getcwd())
with CALLS.open("a", encoding="utf-8") as log:
    log.write(json.dumps([cwd, argv, sys.stdin.isatty()]) + "\n")
def fx(label):
    return json.loads((FIX / (label + ".json")).read_text(encoding="utf-8"))
def load():
    s = json.loads(STATE.read_text()) if STATE.is_file() else {{"repos": {{}}, "fail": []}}
    s.setdefault("land", {{"base": {{}}, "attempts": {{}}, "held": [], "clar": {{}}, "packed": {{}}, "unlocked": []}})
    s["land"].setdefault("unlocked", [])
    return s
def save(s):
    STATE.write_text(json.dumps(s))
def say(lines, err=False):
    out = sys.stderr if err else sys.stdout
    for l in lines:
        print(l, file=out)
    out.flush()
def git(*a, check=True):
    return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True, check=check)
def head_sha(path):
    p = subprocess.run(["git", "-C", cwd, "show", "HEAD:" + path], capture_output=True)
    return hashlib.sha256(p.stdout).hexdigest() if p.returncode == 0 else None
def search():
    return [d for d in os.environ.get("FAKE_BALE_SEARCH", "").split(os.pathsep) if d]
def resolve(name, what):
    p = pathlib.Path(name)
    if p.is_absolute():
        return p if p.is_file() else None
    for d in [cwd] + search():
        if (pathlib.Path(d) / name).is_file():
            return pathlib.Path(d) / name
    return None
def missing(name, what):
    print("[bale] error: " + what + " not found: " + name, file=sys.stderr)
    print("  searched:", file=sys.stderr)
    print("    " + cwd + "  (cwd)", file=sys.stderr)
    for d in search():
        print("    " + d, file=sys.stderr)
    sys.exit(1)
def swap(lines, old_sid, sid, old_root, root, extra=()):
    out = []
    for l in lines:
        l = l.replace(old_sid, sid).replace(old_root, root)
        for a, b in extra:
            l = l.replace(a, b)
        out.append(l)
    return out
def under(path, scope):
    return any(e in ("", ".") or path == e.strip("/") or path.startswith(e.strip("/") + "/") for e in scope)

if not argv or argv[0] in ("--version", "status") or (argv[0] == "pack" and "--context" in argv):
    os.execv(sys.executable, [sys.executable, PACKER] + argv)

state = load()
L = state["land"]
repo = state["repos"].setdefault(cwd, {{"sessions": [], "scopes": {{}}, "outbox": []}})

def pack(args):
    """The packing fake packs; this stamps each committed forecast file's
    HEAD bytes, as bale's base-drift stamp does."""
    before = set(repo["sessions"])
    p = subprocess.run([sys.executable, PACKER] + args, capture_output=True, text=True)
    s = load()
    r = s["repos"].get(cwd, {{"sessions": []}})
    new = [x for x in r["sessions"] if x not in before]
    if p.returncode == 0 and new:
        sid = new[0]
        scope = r["scopes"][sid] or []
        files = git("ls-files", check=False).stdout.split()
        s["land"]["base"][sid] = {{f: head_sha(f) for f in files if scope and under(f, scope)}}
        s["land"]["packed"][sid] = cwd
        save(s)
    return p, new

if argv[0] == "pack":
    p, _ = pack(argv)
    sys.stdout.write(p.stdout); sys.stderr.write(p.stderr)
    sys.exit(p.returncode)

def attempt(sid, command, outcome, paths, vstate):
    s = load()
    s["land"]["attempts"].setdefault(sid, []).append(
        {{"command": command, "outcome": outcome, "change_paths": paths, "state": vstate}})
    if outcome == "held" and sid not in s["land"]["held"]:
        s["land"]["held"].append(sid)
    if outcome == "applied":
        r = s["repos"][cwd]
        r["sessions"].remove(sid); r["scopes"].pop(sid, None)
        r.setdefault("applied", []).append(sid)
        if sid in s["land"]["held"]:
            s["land"]["held"].remove(sid)
    save(s)

if argv[0] in ("apply", "retry"):
    verb = argv[0]
    if len(argv) != 2:
        print("fake bale: built for bale " + verb + " TARBALL only", file=sys.stderr); sys.exit(97)
    tb = resolve(argv[1], "tarball")
    if tb is None:
        missing(argv[1], "tarball")
    with tarfile.open(tb) as t:
        names = t.getnames()
        mname = next(n for n in names if re.fullmatch(r"response-\d{{3}}/manifest\.json", n))
        m = json.loads(t.extractfile(mname).read())
        top = mname.split("/")[0]
        tmp = tempfile.mkdtemp(prefix="fake-bale-apply-")
        t.extractall(tmp)
    sid = m["responds_to"]
    if sid not in repo["sessions"]:
        print("[bale] error: " + tb.name + " answers " + sid + ", which is not open here", file=sys.stderr); sys.exit(1)
    held = sid in L["held"]
    if verb == "apply" and held:
        print("[bale] error: " + sid + " is held; bale retry <tarball> runs a corrected response", file=sys.stderr); sys.exit(1)
    if verb == "retry" and not held:
        print("[bale] error: " + sid + " is not held; bale apply runs its response", file=sys.stderr); sys.exit(1)
    if m["response_kind"] == "clarification":
        cap = fx("apply-clar")
        say(swap(cap["stdout"], "2026-10-03-probe-clar-001", sid, "/tmp/office-probe.waUkTl/clar", cwd))
        s = load(); s["land"]["clar"][sid] = m["questions"]; save(s)
        sys.exit(0)
    scope = repo["scopes"][sid] or []
    paths = [c["path"] for c in m["changes"]]
    outside = [p for p in paths if not under(p, scope)]
    if outside:
        admitted = False
        if sys.stdin.isatty():
            say(["", "  " + str(len(outside)) + " changes[] path(s) lie outside session " + sid + "'s write forecast."])
            admitted = True
            for p in outside:
                sys.stdout.write("  admit " + p + "? [y/N] "); sys.stdout.flush()
                if sys.stdin.readline().strip().lower() not in ("y", "yes"):
                    admitted = False
        if not admitted:
            cap = fx("apply-outside")
            say(swap(cap["stdout"], "2026-10-03-probe-outside-001", sid, "/tmp/office-probe.waUkTl/outside", cwd,
                     [("docs/outside.md", ", ".join(outside)), ("write forecast: notes", "write forecast: " + ", ".join(scope)),
                      ("response-" + "2026-10-03-probe-outside-001", "response-" + sid)]))
            attempt(sid, verb, "scope-drift-refused", paths, None)
            sys.exit(1)
    base = L["base"].get(sid, {{}})
    moved = [p for p in paths if p in base and head_sha(p) != base[p]]
    if moved:
        cap = fx("apply-drift")
        say(swap(cap["stdout"], "2026-10-03-probe-drift-001", sid, "/tmp/office-probe.waUkTl/drift", cwd,
                 [("notes/job/folder.md", ", ".join(moved))]))
        attempt(sid, verb, "base-drift-refused", paths, None)
        sys.exit(1)
    v = subprocess.run(["bash", str(pathlib.Path(tmp) / top / "validation.sh")], cwd=str(pathlib.Path(tmp) / top),
                       capture_output=True, text=True)
    if v.returncode != 0:
        cap = fx("apply-hold")
        say(swap(cap["stdout"], "2026-10-03-probe-hold-001", sid, "/tmp/office-probe.waUkTl/hold", cwd,
                 [("/tmp/office-probe.waUkTl/dl", str(tb.parent))]))
        attempt(sid, verb, "held", paths, "HOLD")
        sys.exit(1)
    cap = fx("apply-applied")
    lines = swap(cap["stdout"], "2026-10-03-probe-applied-001", sid, "/tmp/office-probe.waUkTl/applied", cwd)
    at = lines.index("[bale] walkthrough action: merge")
    say(lines[:at])
    if sys.stdin.isatty():
        sys.stdout.write("  [Enter/m] merge into origin (default)   [r] revert — discard branch\n  > ")
        sys.stdout.flush()
        if sys.stdin.readline().strip() == "r":
            print("[bale] walkthrough action: revert")
            attempt(sid, verb, "reverted", paths, "PASS")
            sys.exit(1)
    for c in m["changes"]:
        src = pathlib.Path(tmp) / top / "files" / c["path"]
        dst = pathlib.Path(cwd) / c["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    git("add", "--", *paths)
    git("commit", "-q", "-m", "[bale " + sid + "] " + m["summary"], "--", *paths)
    git("tag", "applied/" + sid)
    attempt(sid, verb, "applied", paths, "PASS")
    say(lines[at:])
    sys.exit(0)

if argv[0] == "unlock":
    # bale unlock SID --json, as the second-trip probe captured it: the
    # session leaves the registry, its record is committed alone as the
    # sweep, the JSON line on stdout and the human lines on stderr. With
    # --reason R (office withdraw, 0.24.0: abandoned), the reason given
    # stands where bale would infer one, as bale help unlock says.
    given = None
    if len(argv) == 5 and argv[2] == "--reason" and argv[4] == "--json":
        given = argv[3]
    elif len(argv) != 3 or argv[2] != "--json":
        print("fake bale: built for bale unlock SID [--reason R] --json only", file=sys.stderr); sys.exit(97)
    sid = argv[1]
    old_sid, old_root = "2026-10-04-probe-unlock-json-001", "/tmp/office-probe.DPIe0v/repo"
    if sid not in repo["sessions"]:
        cap = json.loads((UNLOCK_FIX / "unlock-ro-again.json").read_text(encoding="utf-8"))
        say(swap(cap["stderr"], old_sid, sid, old_root, cwd), err=True); sys.exit(1)
    if os.environ.get("FAKE_BALE_UNLOCK_FAILS") == sid:
        print("[bale] error: unlock " + sid + ": refused for the test", file=sys.stderr); sys.exit(1)
    s = load()
    r = s["repos"][cwd]
    reason = given or ("closed-read-only" if r["scopes"].get(sid) == [] else "abandoned")
    r["sessions"].remove(sid); r["scopes"].pop(sid, None)
    s["land"]["unlocked"].append(sid)
    s["land"].setdefault("unlock_reasons", {{}})[sid] = reason
    save(s)
    rec = pathlib.Path(cwd) / ("cla" + "ude") / "telemetry" / (sid + ".json")
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(json.dumps({{"session_id": sid, "outcome": "unlocked"}}) + "\n")
    git("add", "--", str(rec.relative_to(cwd)))
    git("commit", "-q", "-m", "[bale sweep " + sid + "] " + reason, "--", str(rec.relative_to(cwd)))
    sha = git("rev-parse", "--short", "HEAD").stdout.strip()
    cap = json.loads((UNLOCK_FIX / "unlock-ro-json.json").read_text(encoding="utf-8"))
    extra = [("dcd55ba", sha), ("closed-read-only", reason)]
    say(swap(cap["stderr"], old_sid, sid, old_root, cwd, extra), err=True)
    say(swap(cap["stdout"], old_sid, sid, old_root, cwd, extra))
    sys.exit(0)

if argv[:2] == ["stats", "--sid"] and argv[3:] == ["--json"]:
    sid = argv[2]
    if sid not in L["packed"]:
        line = json.loads(json.loads(MISS.read_text())["stdout"][0])
        line["session_id"] = sid
        print(json.dumps(line)); sys.exit(0)
    tpl = json.loads(fx("dossier-hold")["stdout"][0])
    pack_a, apply_a = tpl["attempts"][0], tpl["attempts"][1]
    tries = L["attempts"].get(sid, [])
    is_open = sid in state["repos"][L["packed"][sid]]["sessions"]
    rec = dict(tpl["record"])
    rec["outcome"] = tries[-1]["outcome"] if tries else "opened"
    rec["in_flight"] = is_open
    rec["closure"] = {{"category": "applied", "unlock_reason": None}} if not is_open else None
    if sid in L["unlocked"]:
        why = L.get("unlock_reasons", {{}}).get(sid, "closed-read-only")
        rec.update(outcome="unlocked", in_flight=False, read_only=why == "closed-read-only",
                   closure={{"category": "unlocked", "unlock_reason": why}})
    attempts = [dict(pack_a)]
    stem = L.get("stems", {{}}).get(sid)
    if stem is not None:
        attempts[0]["bundle"] = {{"stem": stem, "brief_sha256": None, "checkpoint_sha256": None,
                                 "manifest_sha256": None}}
    for t in tries:
        a = dict(apply_a)
        a.update(command=t["command"], outcome=t["outcome"], change_paths=t["change_paths"],
                 validation=dict(apply_a["validation"], state=t["state"]) if t["state"] else None)
        attempts.append(a)
    tpl.update(session_id=sid, record=rec, attempts=attempts)
    print(json.dumps(tpl)); sys.exit(0)

if argv[0] == "relay" and len(argv) == 2:
    sid = argv[1]
    if sid not in L["clar"]:
        print("[bale] error: relay: " + sid + " has no recorded rounds", file=sys.stderr); sys.exit(1)
    cap = fx("relay-clar")
    say(swap(cap["stdout"], "2026-10-03-probe-clar-001", sid, "/tmp/office-probe.waUkTl/clar", cwd))
    say(swap(cap["stderr"], "2026-10-03-probe-clar-001", sid, "/tmp/office-probe.waUkTl/clar", cwd), err=True)
    sys.exit(0)

def bundle_forecast_of(pack_argv):
    """--write's paths, else --include's, else the whole tree; [] for
    --read-only: bale pack's reading of a forecast, enough for the fake."""
    writes, includes, flag, ro = [], [], None, False
    for w in pack_argv[1:]:
        if w.startswith("--"):
            flag = w
            ro = ro or w == "--read-only"
            continue
        if flag == "--write":
            writes.append(w)
        elif flag == "--include":
            includes.append(w)
        flag = flag if flag in ("--write", "--include") else None
    return [] if ro else (writes or includes or ["."])

def meets(a, b):
    a, b = a.strip("/"), b.strip("/")
    return a in ("", ".") or b in ("", ".") or a == b or a.startswith(b + "/") or b.startswith(a + "/")

# bale 0.4.52's open --json and open --check --json, as the fallback probe
# of session 2026-10-13-office-probe-002 captured them in a throwaway repo
# (fixtures/bale-0.4.52/open-json): each JSON line is the captured one with
# the session id, the bundle and the paths swapped in, and its stderr the
# captured lines, swapped the same way.
JFIX = FIX.parent.parent / "bale-0.4.52" / "open-json"
J_SID = "2026-10-13-office-probe-open-001"
J_BUNDLE = "TMP/dl/2026-10-13-office-probe-open.bale-bundle"
J_GOAL = "Probe: open a bundle with --json"
def jfx(label):
    return json.loads((JFIX / (label + ".json")).read_text(encoding="utf-8"))
def jline(label, **fields):
    line = json.loads(jfx(label)["stdout"][0])
    for k, v in fields.items():
        assert k in line, k
        line[k] = v
    return json.dumps(line)
def jswap(lines, sid, b, goal=None, desk=None, forecast=None):
    out = []
    for l in lines:
        l = l.replace(J_SID, sid).replace(J_BUNDLE, str(b)).replace("2026-10-13-office-probe-open.bale-bundle", b.name)
        l = l.replace("TMP/repo", cwd)
        if goal is not None:
            l = l.replace(J_GOAL, goal)
        if desk is not None:
            l = l.replace("desk-2", "desk-" + str(desk))
        if forecast is not None:
            l = l.replace("write forecast:     notes", "write forecast:     " + forecast)
        out.append(l)
    return out
def scissors(lines):
    a = lines.index("--8<-- session opener (copy everything between the scissor lines) --8<--")
    z = lines.index("--8<-- end session opener --8<--")
    return lines[a + 1:z]
def read_bundle(b):
    with tarfile.open(b) as t:
        raw = t.extractfile("bundle.json").read()
        manifest = json.loads(raw)
        brief = t.extractfile("brief.md").read() if "brief.md" in t.getnames() and manifest["members"]["brief"] else None
    shown = {{"path": str(b.resolve()), "sha256": hashlib.sha256(b.read_bytes()).hexdigest(),
              "stem": b.name[:-len(".bale-bundle")]}}
    members = {{"brief": hashlib.sha256(brief).hexdigest() if brief is not None else None, "checkpoint": None}}
    # A bundle's identity is its manifest and its brief, not its file name:
    # a browser's "NAME (1)" copy is the same bundle.
    return manifest, brief, hashlib.sha256(raw + (brief or b"")).hexdigest(), shown, members

if argv[:1] == ["open"] and "--check" in argv:
    # bale open --check BUNDLE, as the third-trip probe captured it on bale
    # 0.4.47: a name bale cannot find, a forecast path that is not there or
    # a forecast an open session holds refuses on stderr, exit 1; else the
    # rehearsal report on stdout, exit 0. With --json (0.18.0's office asks
    # it of bale 0.4.50 on), the 0.4.52 capture's one line on stdout,
    # outcome rehearsed or open-refused, and the report on stderr. It
    # writes nothing, here too.
    CHECK = FIX.parent.parent / "bale-0.4.47" / "open-check"
    def cfx(label):
        return json.loads((CHECK / (label + ".json")).read_text(encoding="utf-8"))
    rest = [w for w in argv[1:] if w != "--check"]
    as_json = "--json" in rest
    rest = [w for w in rest if w != "--json"]
    if len(rest) != 1 or (as_json and FAKE_VERSION < (0, 4, 48)):
        say(fx("open-extra-flags")["stderr"], err=True); sys.exit(2)
    def refused(reason, cause, shown=None, members=None):
        if as_json:
            print(jline("check-other", bundle=shown, members=members, reason=reason, cause=cause))
    b = resolve(rest[0], "bundle")
    if b is None:
        refused("not-found", "bundle not found: " + rest[0])
        missing(rest[0], "bundle")
    manifest, check_brief, check_id, shown, members = read_bundle(b)
    pack_argv = manifest["pack_argv"]
    old_b = "TMP/dl/2026-01-01-office-probe-ok.bale-bundle"
    forecast = bundle_forecast_of(pack_argv)
    # A bundle whose session is still open rehearses as a second desk
    # (bale 0.4.44 on): no gate runs, since an open would mint nothing.
    desk = [x for x in repo["sessions"] if L.get("opened_from", {{}}).get(x) == check_id]
    if desk:
        n = L.get("desks", {{}}).get(desk[0], 1) + 1
        lines = jswap(jfx("check-desk")["stderr"], desk[0], b, desk=n)
        if as_json:
            print(jline("check-desk", bundle=shown, members=members)); say(lines, err=True)
        else:
            say(lines)
        sys.exit(0)
    gone = [w for w in forecast if w not in (".", "") and not (pathlib.Path(cwd) / w).exists()]
    if gone:
        cap = cfx("check-nopath")
        err = [l.replace(": nope.", ": " + gone[0] + ".") for l in cap["stderr"]]
        refused("gate-refused", err[0][len("[bale] error: "):], shown, members)
        say([l.replace(old_b.replace("ok", "nopath"), str(b)) for l in cap["stdout"]], err=as_json)
        say(err, err=True); sys.exit(1)
    sup = pack_argv[pack_argv.index("--supersedes") + 1] if "--supersedes" in pack_argv else None
    held = [s for s in repo["sessions"] if s != sup and repo["scopes"].get(s) != []
            and any(meets(m, t) for m in forecast for t in (repo["scopes"].get(s) or ["."]))]
    if held:
        if as_json:
            cap = jfx("check-other")
            err = [l.replace(J_SID + " (notes ~ notes)", held[0] + " (" + ", ".join(forecast) + ")")
                   .replace("TMP/dl/2026-10-13-office-probe-other.bale-bundle", str(b)) for l in cap["stderr"]]
            refused("gate-refused", err[-1][len("[bale] error: "):], shown, members)
            say(err, err=True); sys.exit(1)
        cap = cfx("check-overlap")
        say([l.replace(old_b.replace("ok", "overlap"), str(b)) for l in cap["stdout"]])
        say([l.replace("2026-10-07-probe-proj-001 (src ~ src)", held[0] + " (" + ", ".join(forecast) + ")")
             for l in cap["stderr"]], err=True); sys.exit(1)
    if as_json:
        print(jline("check-fresh", bundle=shown, members=members))
        say(jswap(jfx("check-fresh")["stderr"], "", b, forecast=", ".join(forecast) if forecast else "none (read-only)"),
            err=True)
        sys.exit(0)
    cap = cfx("check-ro" if forecast == [] else "check-found")
    say([l.replace(old_b.replace("ok", "ro") if forecast == [] else old_b, str(b)).replace("TMP/proj", cwd)
         .replace("write forecast:     notes", "write forecast:     " + ", ".join(forecast)) for l in cap["stdout"]])
    sys.exit(0)

if argv[0] == "open":
    # bale open BUNDLE [--json]. --json (bale 0.4.48; a second desk's
    # tarball since 0.4.50) prints one JSON line on stdout, the 0.4.52
    # capture's with this session swapped in, and everything else on
    # stderr. A bundle whose identity matches the bundle an open session
    # was opened from is a second desk (bale 0.4.44 on): no session is
    # minted, a desk is counted on that session, and the opener is the
    # desk's, as the probe captured them.
    rest = argv[1:]
    as_json = "--json" in rest
    rest = [w for w in rest if w != "--json"]
    if len(rest) != 1 or (as_json and FAKE_VERSION < (0, 4, 48)):
        say(fx("open-extra-flags")["stderr"], err=True); sys.exit(2)
    b = resolve(rest[0], "bundle")
    if b is None:
        missing(rest[0], "bundle")
    bundle, brief, identity, shown, members = read_bundle(b)
    L.setdefault("opened_from", {{}}); L.setdefault("desks", {{}})
    joined = [x for x in repo["sessions"] if L["opened_from"].get(x) == identity]
    if joined:
        sid = joined[0]
        s = load(); desks = s["land"].setdefault("desks", {{}}); n = desks.get(sid, 1) + 1; desks[sid] = n; save(s)
        tb = pathlib.Path(cwd) / ".bale" / "outbox" / ("request-" + sid + ".tar.gz")
        lines = jswap(jfx("open-desk")["stderr"], sid, b, goal=bundle["pack_argv"][0], desk=n)
        opener = scissors(lines)
        if as_json:
            say(lines, err=True)
            tarball = str(tb) if tb.is_file() and not os.environ.get("FAKE_BALE_OUTBOX_GONE") else None
            print(jline("open-desk", sid=sid, tarball=tarball, opener="\n".join(opener) + "\n", bundle=shown,
                        members=members, desk="desk-" + str(n)))
        else:
            say(lines)
        sys.exit(0)
    tmp = tempfile.mkdtemp(prefix="bale-open-members-")
    args = ["pack"] + bundle["pack_argv"]
    if brief is not None:
        (pathlib.Path(tmp) / "brief.md").write_bytes(brief)
        args += ["--readme-file", str(pathlib.Path(tmp) / "brief.md")]
    else:
        args += ["--no-readme"]
    p, new = pack(args + ["--json"])
    if p.returncode != 0:
        sys.stderr.write(p.stderr); sys.exit(p.returncode)
    report = json.loads(p.stdout.splitlines()[-1])
    sid, tarball = report["sid"], report["tarball"]
    s = load(); s["land"].setdefault("opened_from", {{}})[sid] = identity
    # The bundle's stem, as bale's records keep it on the pack attempt
    # (attempts[].bundle.stem; the home screen reads it, 0.22.0).
    s["land"].setdefault("stems", {{}})[sid] = shown["stem"]; save(s)
    label = "open-brief" if brief is not None else "open-ro-bare"
    cap = fx(label)
    old_sid = "2026-10-03-probe-open-brief-001" if brief is not None else "2026-10-03-probe-open-ro-001"
    old_root = "/tmp/office-probe.waUkTl/openb" if brief is not None else "/tmp/office-probe.waUkTl/openro"
    old_goal = re.search(r"^Goal, verbatim from the request manifest: (.*)$", "\n".join(cap["stdout"]), re.M).group(1)
    old_bundle = [l for l in cap["stdout"] if l.startswith("[bale] opening planner bundle ")][0][len("[bale] opening planner bundle "):]
    lines = swap(cap["stdout"], old_sid, sid, old_root, cwd, [(old_goal, bundle["pack_argv"][0]), (old_bundle, str(b))])
    if as_json:
        say(lines, err=True)
        bale_dir = pathlib.Path(cwd) / ".bale"
        print(jline("open-opened", sid=sid, tarball=tarball, log=str(bale_dir / "logs" / (sid + ".log")),
                    session_dir=str(bale_dir / "sessions" / sid),
                    readme_path=str(pathlib.Path(tmp) / "brief.md") if brief is not None else None,
                    readme_heading=None if brief is None else (brief.decode().splitlines() or [None])[0],
                    readme_sha256=hashlib.sha256(brief).hexdigest() if brief is not None else None,
                    opener="\n".join(scissors(lines)) + "\n", bundle=shown, members=members))
    else:
        say(lines)
    sys.exit(0)

print("fake bale: not built for bale " + " ".join(argv), file=sys.stderr)
sys.exit(97)
'''


class FakeLandBale:
    """A directory holding the fake bale and the packing fake it wraps;
    their state and calls live beside them."""

    def __init__(self, tmp):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="fake-land-bale-", dir=tmp))
        self.state = self.dir / "state.json"
        self.calls = self.dir / "calls.jsonl"
        packer = self.dir / "packer.py"
        packer.write_text(FAKE_PACK_BALE.format(fixtures=str(PACK_FIXTURES), state=str(self.state),
                                                calls=str(self.dir / "pack-calls.jsonl")))
        script = self.dir / "bale"
        script.write_text(FAKE_LAND_BALE.format(fixtures=str(LAND_FIXTURES), miss=str(MISS), state=str(self.state),
                                                calls=str(self.calls), packer=str(packer)))
        script.chmod(0o755)

    def path(self, base):
        return f"{self.dir}{os.pathsep}{base}"

    def calls_of(self, verb):
        """(cwd, argv, stdin was a terminal) of each call of one bale verb.
        "open" is the opens; "open-check" is bale open --check, which
        office start runs before it writes anything for a bundle."""
        if not self.calls.is_file():
            return []
        out = [json.loads(l) for l in self.calls.read_text().splitlines()]
        kind = lambda a: "open-check" if a[:2] == ["open", "--check"] else a[0]  # noqa: E731
        return [c for c in out if c[1] and kind(c[1]) == verb]

    def land_state(self):
        return json.loads(self.state.read_text())["land"]

    def is_open(self, repo, sid):
        return sid in json.loads(self.state.read_text())["repos"][os.path.realpath(repo)]["sessions"]


def response_tarball(directory, sid, files=None, kind="normal", validation="pass", name=None, notes=None):
    """A response tarball the way a worker ships one: files ({path: text})
    modified or created, a validation.sh that passes or fails, and, since
    0.17.0, a notes.md when given (the folder's pages ride in it)."""
    nnn = sid[-3:]
    members, changes = {}, []
    if notes is not None:
        members["notes.md"] = notes.encode()
    for path, text in (files or {}).items():
        data = text.encode()
        members[f"files/{path}"] = data
        changes.append({"path": path, "action": "modified", "reason": "test", "size_bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
    m = {"session_id": sid, "responds_to": sid, "corrects": None, "response_kind": kind,
         "summary": "A test response.", "changes": changes, "deferred": [], "validation_will_run": [], "claims": {}}
    if kind == "clarification":
        m["questions"] = [{"question": "Which name?", "context": "naming", "default_assumption": "the first",
                           "why_blocked": "two names"}]
    members["manifest.json"] = json.dumps(m, indent=2).encode()
    members["apply.sh"] = b"#!/usr/bin/env bash\nexit 0\n"
    members["validation.sh"] = b"#!/usr/bin/env bash\nexit 0\n" if validation == "pass" else \
        b"#!/usr/bin/env bash\necho '[FAIL] the check'\nexit 1\n"
    path = pathlib.Path(directory) / (name or f"response-{sid}.tar.gz")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as t:
        for rel, data in members.items():
            info = tarfile.TarInfo(f"response-{nnn}/{rel}")
            info.size = len(data)
            info.mode = 0o755 if rel.endswith(".sh") else 0o644
            t.addfile(info, io.BytesIO(data))
    return path


def bundle_file(directory, stem, pack_argv, brief=None):
    """A synthetic planner bundle, in the shape the request's crafter
    writes one: bundle.json, and the brief as brief.md."""
    members = {}
    meta = {"bundle_format": 1, "pack_argv": pack_argv,
            "members": {"brief": None, "checkpoint": None}, "pre_answered": []}
    if brief is not None:
        data = brief.encode()
        members["brief.md"] = data
        meta["members"]["brief"] = {"path": "brief.md", "sha256": hashlib.sha256(data).hexdigest()}
    members["bundle.json"] = json.dumps(meta, indent=2).encode()
    path = pathlib.Path(directory) / f"{stem}.bale-bundle"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as t:
        for rel in ("bundle.json", "brief.md"):
            if rel in members:
                info = tarfile.TarInfo(rel)
                info.size = len(members[rel])
                t.addfile(info, io.BytesIO(members[rel]))
    return path


# --- the captured applies and opens themselves ------------------------------------------

class TestLandFixtures(unittest.TestCase):
    def setUp(self):
        self.data = tomllib.loads(CONSUMPTION.read_text())

    def test_every_line_is_the_one_the_probe_captured(self):
        files = sorted(LAND_FIXTURES.glob("*.json"))
        self.assertGreaterEqual(len(files), 40)
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(len(rec["stdout"]), len(rec["stdout_sha256"]), f.name)
            for line, sha in zip(rec["stdout"], rec["stdout_sha256"]):
                self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), sha, f.name)
            self.assertIn(f"probe of session {PROBE_SID}", rec["captured"], f.name)

    def test_the_office_passes_bale_no_answer(self):
        """apply and retry run with nothing that answers a question bale
        asks: no --no-interact, no admission, no acceptance."""
        for surface in ("apply", "retry"):
            spec = self.data["surfaces"][surface]
            self.assertEqual(spec["argv"], [surface, "{tarball}"])
            self.assertTrue(spec["interactive"])
            for group in ("optional", "repeated", "switches"):
                self.assertNotIn(group, spec, surface)
        self.assertEqual(self.data["surfaces"]["open"]["argv"], ["open", "{bundle}"])
        self.assertEqual(self.data["surfaces"]["relay"]["argv"], ["relay", "{sid}"])

    def test_the_verbs_are_the_ones_bales_help_names(self):
        self.assertIn("usage: bale apply [-h]", fixture("help-apply")["stdout"][0])
        self.assertTrue(fixture("help-apply")["stdout"][6].strip().endswith("[tarball]"))
        self.assertIn("tarball", fixture("help-retry")["stdout"][5])
        self.assertEqual(fixture("help-relay")["stdout"][0], "usage: bale relay [-h] sid [file]")
        self.assertTrue(fixture("help-open")["stdout"][0].endswith(" bundle"))
        self.assertNotIn("--json", " ".join(fixture("help-open")["stdout"]))

    def test_the_outcomes_the_office_words_are_bales(self):
        """Held to bale both ways: every outcome the office words is one
        bale's apply report names, and every one bale names that lands
        nothing is worded or shown as bale records it."""
        text = " ".join(line.strip() for line in fixture("help-apply")["stdout"])
        named = re.search(r"outcome \(([a-z| -]+)\)", text).group(1).replace("- ", "-").split("|")
        declared = self.data["surfaces"]["apply"]["outcomes"]
        self.assertEqual(sorted(set(declared) - set(named)), [])
        self.assertEqual(sorted(set(named) - set(declared)), ["clarification", "dry-run"])
        plan = {"sid": "s", "label": "x", "repo": "/r"}
        for outcome in declared + ["clarification", "refused"]:
            words, _ = ob.outcome_words(plan, outcome)
            self.assertNotIn("bale recorded", words, outcome)
        for label, outcome in (("dossier-applied", "applied"), ("dossier-hold", "held"),
                               ("dossier-drift", "base-drift-refused"), ("dossier-outside", "scope-drift-refused")):
            self.assertEqual(first_json(label)["attempts"][-1]["outcome"], outcome, label)

    def test_the_relay_blocks_come_from_between_bales_markers(self):
        spec = self.data["surfaces"]["apply"]
        applied = ob.relay_blocks(fixture("apply-applied")["stdout"], "2026-10-03-probe-applied-001", spec)
        self.assertEqual([to for to, _ in applied], ["planner"])
        self.assertTrue(applied[0][1][0].startswith("=== RELAY BEGIN 2026-10-03-probe-applied-001 to planner"))
        self.assertTrue(applied[0][1][-1].startswith("=== RELAY END"))
        self.assertIn("APPLIED", "\n".join(applied[0][1]))
        held = ob.relay_blocks(fixture("apply-hold")["stdout"], "2026-10-03-probe-hold-001", spec)
        self.assertEqual([to for to, _ in held], ["worker", "planner"])
        self.assertIn("bale retry", "\n".join(held[0][1]))
        # Under --json the same block is on stderr: why the office runs
        # apply plain and keeps its stdout.
        self.assertEqual(ob.relay_blocks(fixture("apply-appliedj")["stdout"], "2026-10-03-probe-appliedj-001", spec), [])
        self.assertEqual(len(ob.relay_blocks(fixture("apply-appliedj")["stderr"], "2026-10-03-probe-appliedj-001",
                                             spec)), 1)
        # Under a pseudo-terminal, stdout piped, the walkthrough still asks.
        split = fixture("ptyapply-split")
        self.assertIn("[Enter/m] merge into origin (default)", split["events"][0][1])
        self.assertEqual(split["events"][1][0], "sent")
        self.assertEqual(len(ob.relay_blocks(split["stdout"], "2026-10-03-probe-appliedpty-001", spec)), 1)

    def test_the_clarification_block_is_relays_stdout(self):
        rec = fixture("relay-clar")
        block = ob.exchange_block(rec["stdout"], "2026-10-03-probe-clar-001", self.data["surfaces"]["relay"])
        self.assertEqual(block, rec["stdout"])
        self.assertEqual(fixture("apply-clar")["exit"], 0)
        self.assertEqual(ob.relay_blocks(fixture("apply-clar")["stdout"], "2026-10-03-probe-clar-001",
                                         self.data["surfaces"]["apply"]), [])

    def test_base_drift_never_asks_and_the_packed_bytes_land(self):
        """The folder-record case: bale refuses a response whose base
        moved, on a terminal too, and lands it with nothing asked once the
        packed bytes are back."""
        self.assertEqual(fixture("apply-drift")["exit"], 1)
        self.assertIn("[BASE-DRIFT-REFUSED]", "\n".join(fixture("apply-drift")["stdout"]))
        for label in ("ptyapply-driftn", "ptyapply-drifty"):
            self.assertEqual([ch for ch, _ in fixture(label)["events"]], ["out"], label)
        self.assertEqual(fixture("apply-driftrestored")["exit"], 0)
        self.assertEqual(first_json("dossier-driftrestored")["record"]["outcome"], "applied")
        # bale cannot name a session before it packs it.
        self.assertIn("--dry-run and --json are not supported together", fixture("dry-1")["stderr"][0])

    def test_the_open_report_carries_the_tarball_and_the_opener(self):
        spec = self.data["surfaces"]["open"]
        for label, sid in (("open-brief", "2026-10-03-probe-open-brief-001"), ("open-ro-bare", "2026-10-03-probe-open-ro-001")):
            out = fixture(label)["stdout"]
            tb = [l[len(spec["tarball_line"]):] for l in out if l.startswith(spec["tarball_line"])]
            self.assertEqual(len(tb), 1, label)
            self.assertTrue(tb[0].endswith(f"/.bale/outbox/request-{sid}.tar.gz"), label)
            opener = ob.opener_lines(out, spec)
            self.assertTrue(opener, label)
            self.assertIn(f"session {sid}", "\n".join(fixture(label)["stdout"]))
        self.assertEqual(ob.opener_lines(fixture("open-brief")["stdout"], spec)[1],
                         "This message opens bale session 2026-10-03-probe-open-brief-001.")
        self.assertEqual(fixture("open-extra-flags")["exit"], 2)
        status = first_json("status-openb")
        self.assertEqual(status["sessions"], ["2026-10-03-probe-open-brief-001"])
        self.assertIn("request-2026-10-03-probe-open-brief-001.tar.gz", status["outbox"])

    def test_a_missing_name_says_where_bale_looked(self):
        for label in ("apply-missing", "open-missing"):
            err = fixture(label)["stderr"]
            self.assertTrue(err[0].startswith("[bale] error: "), label)
            self.assertEqual(err[1], "  searched:", label)

    def test_bare_apply_declines_piped(self):
        """Why office land names the tarball: bare apply asks y/N, and a
        piped run declines without asking."""
        rec = fixture("apply-noarg")
        self.assertEqual(rec["exit"], 1)
        self.assertIn("stdin is not a TTY", rec["stderr"][-1])


# --- a sitting's pages, from a brief ----------------------------------------------------

class TestSittingPages(unittest.TestCase):
    BRIEF = ("# Brief\n\n--- PAGE BEGIN ---\nold record\n--- PAGE END ---\n\n"
             "--- NOTEPAD PAGE BEGIN notepad/2026-10-05-some-sitting-001.md ---\n"
             "# Planner's words, café\n\n> as assumed\n--- NOTEPAD PAGE END ---\n"
             "--- NOTEPAD PAGE BEGIN notepad/2026-10-05-some-sitting-001-2.md ---\nsecond\n--- NOTEPAD PAGE END ---\n")

    def test_pages_are_the_lines_between_the_markers(self):
        pages, problems = h.sitting_pages(self.BRIEF)
        self.assertEqual(problems, [])
        self.assertEqual(pages, [("notepad/2026-10-05-some-sitting-001.md",
                                  b"# Planner's words, caf\\xe9\n\n> as assumed\n"),
                                 ("notepad/2026-10-05-some-sitting-001-2.md", b"second\n")])

    def test_bare_page_markers_are_never_pages(self):
        pages, problems = h.sitting_pages("--- PAGE BEGIN ---\nx\n--- PAGE END ---\n")
        self.assertEqual((pages, problems), ([], []))

    def test_what_does_not_pair_or_name_a_page_is_not_taken(self):
        for text, words in (("--- NOTEPAD PAGE BEGIN notepad/2026-10-05-x.md ---\nno end\n", "has no END"),
                            ("--- NOTEPAD PAGE END ---\n", "no BEGIN"),
                            ("--- NOTEPAD PAGE BEGIN notepad/sub/2026-10-05-x.md ---\nx\n--- NOTEPAD PAGE END ---\n",
                             "not a sitting's page"),
                            ("--- NOTEPAD PAGE BEGIN profile.md ---\nx\n--- NOTEPAD PAGE END ---\n", "not a sitting's page"),
                            ("--- NOTEPAD PAGE BEGIN notepad/2026-13-05-x.md ---\nx\n--- NOTEPAD PAGE END ---\n",
                             "not a date")):
            pages, problems = h.sitting_pages(text)
            self.assertEqual(pages, [], text)
            self.assertEqual(len(problems), 1, text)
            self.assertIn(words, problems[0], text)

    def test_filing_is_new_pages_only(self):
        with tempfile.TemporaryDirectory() as d:
            got = h.file_sitting_pages(d, self.BRIEF)
            self.assertEqual([s for s, _, _ in got], ["filed", "filed"])
            again = h.file_sitting_pages(d, self.BRIEF)
            self.assertEqual([s for s, _, _ in again], ["same", "same"])
            page = pathlib.Path(d, "notepad/2026-10-05-some-sitting-001-2.md")
            page.write_text("changed\n")
            third = h.file_sitting_pages(d, self.BRIEF)
            self.assertEqual([s for s, _, _ in third], ["same", "refused"])
            self.assertEqual(page.read_text(), "changed\n")


# --- office land -------------------------------------------------------------------------

class LandCase(unittest.TestCase):
    """An office scoping one project, alpha, with an after-land action;
    one folder on the desk, its lane on alpha. Responses arrive in a
    downloads directory bale searches."""

    def setUp(self):
        self.e = Env(self)
        self.fake = FakeLandBale(self.e.tmp)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir()
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.e.env["FAKE_BALE_SEARCH"] = str(self.downloads)
        self.root = self.e.init("home")
        self.e.found(self.root)
        self.proj = git_repo(self.e.tmp / "alpha", {"src/a.py": "a\n", "docs/d.md": "d\n", "README.md": "alpha\n"})
        self.e.run("projects", "add", "alpha", str(self.proj), "--after-land", "touch AFTER-LAND-RAN",
                   cwd=self.root, check=0)
        self.folder = self.e.run("open", "fix-login", "--lane", "alpha: src", "--class", "code",
                                 cwd=self.root, check=0).stdout.strip()
        self.name = self.folder.split("/")[1]

    def run_office(self, *args, check=None, **kw):
        return self.e.run(*args, cwd=self.root, check=check, **kw)

    def start(self, *args):
        proc = self.run_office("start", *args, check=0)
        return re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)

    def folder_md(self):
        return (self.root / self.folder / "folder.md").read_text()

    def subjects(self, n=6):
        return self.e.git(self.root, "log", f"-{n}", "--format=%s").splitlines()


class TestLandAProjectSession(LandCase):
    def test_one_command_lands_it_and_runs_the_after_land_actions(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        proc = self.run_office("land", check=0)
        self.assertIn(f"Landed: {sid} is applied in alpha (tag applied/{sid}).", proc.stdout)
        self.assertEqual((self.proj / "src/a.py").read_text(), "fixed\n")
        # bale ran in the project, by the tarball's name, which bale finds.
        (cwd, argv, _), = self.fake.calls_of("apply")
        self.assertEqual((cwd, argv), (os.path.realpath(self.proj), ["apply", f"response-{sid}.tar.gz"]))
        # Everything bale printed reached the occupant: the relay whole.
        self.assertIn(f"=== RELAY BEGIN {sid} to planner ===", proc.stdout)
        self.assertIn(f"=== RELAY END {sid} to planner ===", proc.stdout)
        self.assertTrue((self.proj / "AFTER-LAND-RAN").is_file())
        self.assertIn("after land (1 of 1)", proc.stderr)
        # Ratification is never asked at the landing (0.23.0), nor is a
        # line to record it offered: the planner's next brief carries it.
        self.assertNotIn("ratif", proc.stderr)  # the office's lines (bale's relay names itself on stdout)
        self.assertNotIn("ratified", self.folder_md())
        # Piped, the relay's copy is not made, and that is said.
        self.assertIn("the block for the planner is not on the clipboard: off a terminal", proc.stderr)
        self.assertFalse(self.fake.is_open(self.proj, sid))

    def test_ratified_by_flag_records_it_in_the_folder(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        self.run_office("land", sid, "--ratified", "--except", "the slug, moved to folder 2", check=0)
        self.assertIn(f"- {sid} ratified ", self.folder_md())
        self.assertIn(", except: the slug, moved to folder 2", self.folder_md())
        self.assertEqual(self.subjects(1), [f"office sessions: {sid} ratified in {self.name}"])

    def test_a_failing_after_land_action_is_loud_and_stops_the_rest(self):
        h.set_declarations(self.root / "floor-plan/manifest.toml", "alpha", None, ["false", "touch LATER"])
        self.e.git(self.root, "commit", "-qam", "declare")
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        proc = self.run_office("land", check=1)
        self.assertIn("Landed:", proc.stdout)
        self.assertIn("AFTER-LAND ACTION FAILED (exit 1): false", proc.stderr)
        self.assertIn(f"(cd '{self.proj}' && false)", proc.stderr)
        self.assertIn(f"(cd '{self.proj}' && touch LATER)", proc.stderr)
        self.assertFalse((self.proj / "LATER").exists())

    def test_a_response_file_names_its_own_session(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        path = response_tarball(self.e.tmp / "elsewhere", sid, {"src/a.py": "fixed\n"}, name="whatever.tar.gz")
        self.run_office("land", str(path), check=0)
        (_, argv, _), = self.fake.calls_of("apply")
        self.assertEqual(argv, ["apply", str(path.resolve())])
        # A relative path is read from where the occupant stands.
        sid2 = self.start("fix-login", "--on", "alpha", "--goal", "again", "--write", "docs")
        response_tarball(self.e.tmp / "elsewhere", sid2, {"docs/d.md": "x\n"})
        proc = self.e.run("land", "--response", f"response-{sid2}.tar.gz", cwd=self.e.tmp / "elsewhere",
                          extra={"OFFICE_ROOT": str(self.root)}, check=0)
        self.assertIn(f"Landed: {sid2}", proc.stdout)

    def test_the_folder_word_finds_the_session_out(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        self.assertIn(f"Landed: {sid}", self.run_office("land", "folder 1", check=0).stdout)

    def test_a_missing_response_says_where_bale_looked_and_lands_nothing(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        proc = self.run_office("land", check=1)
        self.assertIn(f"tarball not found: response-{sid}.tar.gz", proc.stderr)
        self.assertIn(str(self.downloads), proc.stderr)
        self.assertIn("Not landed:", proc.stdout)
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists())
        self.assertTrue(self.fake.is_open(self.proj, sid))


class TestLandShortOfApplied(LandCase):
    def test_a_hold_lands_nothing_and_names_the_next_line(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "broken\n"}, validation="fail")
        proc = self.run_office("land", "--ratified", check=1)
        self.assertIn(f"Held: bale held {sid} in alpha", proc.stdout)
        self.assertIn(f"=== RELAY BEGIN {sid} to worker ===", proc.stdout)
        self.assertIn(f"Next: office land {sid} --response FILE", proc.stdout)
        self.assertIn("nothing landed, so nothing is ratified", proc.stderr)
        self.assertNotIn("ratified", self.folder_md())
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists())
        self.assertEqual((self.proj / "src/a.py").read_text(), "a\n")
        # The corrected response must be named: a browser saved it beside
        # the held one under another name.
        proc = self.run_office("land", sid, check=1)
        self.assertIn(f"office land {sid} --response FILE", proc.stderr)
        fixed = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, name=f"response-{sid} (1).tar.gz")
        proc = self.run_office("land", "--response", str(fixed), check=0)
        (_, argv, _), = self.fake.calls_of("retry")
        self.assertEqual(argv, ["retry", str(fixed)])
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertTrue((self.proj / "AFTER-LAND-RAN").is_file())

    def test_a_clarification_hands_back_the_planners_block(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, kind="clarification")
        proc = self.run_office("land", check=0)
        self.assertIn("Questions: the worker asked before building", proc.stdout)
        self.assertIn(f"BALE EXCHANGE BEGIN {sid}\n", proc.stdout)
        self.assertIn("BALE EXCHANGE END\n", proc.stdout)
        self.assertIn(f"bale relay {sid}", proc.stdout)
        self.assertTrue(self.fake.is_open(self.proj, sid))
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists())

    def test_out_of_forecast_piped_is_bales_refusal_unanswered(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "x\n", "docs/d.md": "y\n"})
        proc = self.run_office("land", check=1)
        self.assertIn("[SCOPE-DRIFT-REFUSED]", proc.stdout)
        self.assertIn("Refused: bale refused", proc.stdout)
        self.assertIn("the office never runs it for you", proc.stdout)
        self.assertEqual(self.fake.land_state()["attempts"][sid][-1]["outcome"], "scope-drift-refused")
        (_, _, tty), = self.fake.calls_of("apply")
        self.assertFalse(tty)


class TestLandWhichSession(LandCase):
    def test_nothing_out_says_so(self):
        proc = self.run_office("land", check=1)
        self.assertIn("no session is out", proc.stderr)
        self.assertEqual(self.fake.calls_of("apply"), [])

    def test_several_out_piped_names_them_and_the_flag(self):
        a = self.start("fix-login", "--on", "alpha", "--goal", "g")
        other = self.run_office("open", "docs-job", "--lane", "alpha: docs", check=0).stdout.strip()
        b = self.start(other.split("/")[1], "--on", "alpha", "--goal", "g")
        proc = self.run_office("land", check=1)
        self.assertIn("2 sessions are out; name one: office land SID", proc.stderr)
        self.assertIn(a, proc.stderr)
        self.assertIn(b, proc.stderr)
        response_tarball(self.downloads, b, {"docs/d.md": "new\n"})
        self.assertIn(f"Landed: {b}", self.run_office("land", b, check=0).stdout)

    def test_a_read_only_sitting_is_never_the_session_out(self):
        """Bare land never picks a sitting (nothing in the office knows
        when one is over); named, land ends it (tests/test_second_trip.py)."""
        sid = self.start("fix-login", "--in-office", "--read-only", "--goal", "g")
        self.assertIn("no session is out", self.run_office("land", check=1).stderr)
        self.assertEqual(self.fake.calls_of("unlock"), [])
        self.assertIn(f"Ended: the sitting {sid}", self.run_office("land", sid, check=0).stdout)

    def test_flags_that_contradict(self):
        for args, words in ((("--ratified", "--not-now"), "contradict"), (("--except", "x"), "goes with --ratified"),
                            (("--loud",), "does not know --loud")):
            self.assertIn(words, self.run_office("land", *args, check=1).stderr, args)


class TestLandAnOfficeSession(LandCase):
    """The folder record: office start records an office session in the
    folder after packing, so the folder's bytes moved since the pack."""

    def packed_folder(self, sid):
        """folder.md as the worker was shown it: the bytes before office
        start's record."""
        commit = self.e.git(self.root, "log", "-1", "--format=%H", f"--grep=office sessions: {sid} in").strip()
        return self.e.git(self.root, "show", f"{commit}^:{self.folder}/folder.md")

    def test_the_record_is_never_lost_and_bale_never_refuses(self):
        sid = self.start("fix-login", "--in-office", "--goal", "Plan the fix")
        self.assertIn(f"- {sid}\n", self.folder_md())
        worker = self.packed_folder(sid).replace("What happens next, and who moves.", "The worker's next move.")
        page = f"notepad/{sid[:10]}-plan.md"
        response_tarball(self.downloads, sid, {f"{self.folder}/folder.md": worker, page: "words\n"})
        proc = self.run_office("land", check=0)
        self.assertIn(f"Landed: {sid} is applied in this office", proc.stdout)
        md = self.folder_md()
        self.assertIn("The worker's next move.", md)
        self.assertIn(f"- {sid}\n", md)
        self.assertIn("- status: open", md)
        self.assertEqual(md.count(f"opened: {sid}"), 1)
        self.assertEqual([a["outcome"] for a in self.fake.land_state()["attempts"][sid]], ["applied"])
        self.assertIn("is out while bale lands it", proc.stderr)
        self.assertIn(f"office land: {sid} recorded again in {self.name}", self.subjects())
        self.assertIn(f"office land: {sid} unrecorded in {self.name} while it lands", self.subjects())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists())

    def test_the_record_goes_back_as_the_office_wrote_it(self):
        """The record merges back onto the landed folder with its own
        lines, so the day the folder opened stays the day it opened; where
        the worker touched the same lines, it goes back as a new append."""
        sid = "2026-10-01-job-office-001"
        # The record's commits are made in this process, by the office's own
        # git calls: under the Env's identity and config, not the machine's.
        with self.e.this_process():
            for name, worker, merged in (("clean", ("Nothing yet.", "The worker's move."), True),
                                         ("overlap", ("- status: queued", "- status: candidate"), False)):
                root = git_repo(self.e.tmp / name, {"desk/job/folder.md": self.packed_folder_text()})
                md = root / "desk/job/folder.md"
                md.write_text(self.packed_folder_text().replace("- status: queued", "- status: open").replace(
                    "The ids of the sessions.\n", f"The ids of the sessions.\n\n- {sid}\n")
                    + f"- 2026-10-01 opened: {sid}\n")
                self.e.git(root, "commit", "-qam", f"office sessions: {sid} in job")
                plan = {"sid": sid, "office_session": True, "folders": ["desk/job"]}
                plan["record"] = dict(ob.folder_record(root, "desk/job", sid), folder="desk/job")
                self.assertTrue(plan["record"]["restorable"], name)
                ob.take_record_out(root, plan)
                self.assertEqual(md.read_text(), self.packed_folder_text(), name)
                md.write_text(self.packed_folder_text().replace(*worker))
                self.e.git(root, "commit", "-qam", f"[bale {sid}] landed")
                told = ob.put_record_back(root, plan, True, "2026-10-09")
                text = md.read_text()
                self.assertIn(f"\n- {sid}\n", text, name)
                self.assertIn("- status: open", text, name)
                if merged:
                    self.assertIn("merged back as they were", told[0])
                    self.assertIn(worker[1], text)
                    self.assertIn(f"- 2026-10-01 opened: {sid}\n", text)
                    self.assertNotIn("2026-10-09", text)
                else:
                    # The worker's candidate became open with the record's
                    # opened line: one state line, one History line.
                    self.assertNotIn("merged back", told[0])
                    self.assertIn(f"- 2026-10-09 opened: {sid}\n", text)
                    self.assertEqual(text.count("- status:"), 1)
                self.assertEqual(self.e.git(root, "log", "-1", "--format=%s").strip(),
                                 f"office land: {sid} recorded again in job", name)

    @staticmethod
    def packed_folder_text():
        return ("# Job\n\n- number: 1\n- status: queued\n\n## Sessions\n\nThe ids of the sessions.\n\n"
                "## Next\n\nNothing yet.\n\n## History\n\n- 2026-09-30 queued: office open\n")

    def test_a_response_that_leaves_the_folder_alone_keeps_the_record(self):
        sid = self.start("fix-login", "--in-office", "--goal", "g")
        response_tarball(self.downloads, sid, {f"notepad/{sid[:10]}-plan.md": "words\n"})
        self.run_office("land", check=0)
        self.assertIn(f"- {sid}\n", self.folder_md())

    def test_nothing_landed_puts_the_record_back_as_it_was(self):
        sid = self.start("fix-login", "--in-office", "--goal", "g")
        before = self.folder_md()
        response_tarball(self.downloads, sid, {f"{self.folder}/folder.md": self.packed_folder(sid)},
                         validation="fail")
        self.run_office("land", check=1)
        self.assertEqual(self.folder_md(), before)
        # The corrected response lands through bale retry, the same way.
        fixed = response_tarball(self.downloads, sid, {f"{self.folder}/folder.md": self.packed_folder(sid)
                                                       .replace("What happens next, and who moves.", "Done.")},
                                 name=f"response-{sid} (1).tar.gz")
        proc = self.run_office("land", "--response", str(fixed), check=0)
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertIn("Done.", self.folder_md())
        self.assertIn(f"- {sid}\n", self.folder_md())
        self.assertEqual([a["outcome"] for a in self.fake.land_state()["attempts"][sid]], ["held", "applied"])

    def test_a_folder_that_moved_again_is_left_to_bale_and_said_why(self):
        sid = self.start("fix-login", "--in-office", "--goal", "g")
        md = self.root / self.folder / "folder.md"
        md.write_text(md.read_text() + "\nAn edit after the record.\n")
        self.e.git(self.root, "commit", "-qam", "a hand edit")
        response_tarball(self.downloads, sid, {f"{self.folder}/folder.md": self.packed_folder(sid)})
        proc = self.run_office("land", check=1)
        self.assertIn("changed after the office recorded", proc.stderr)
        self.assertIn("Refused: bale refused", proc.stdout)
        self.assertIn("[BASE-DRIFT-REFUSED]", proc.stdout)
        self.assertIn("An edit after the record.", self.folder_md())
        self.assertIn(f"- {sid}\n", self.folder_md())


class TestLandOnATerminal(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane
    def test_bale_asks_and_only_the_occupant_answers(self):
        """bale's admission and its merge are asked by bale, on the
        occupant's terminal; the office asks nothing (0.23.0: not even
        about ratification)."""
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        clip = self.e.tmp / "clipboard.txt"
        (cfg / "machine.toml").write_text(f'clipboard_command = "tee {clip}"\npaste_command = "cat {clip}"\n')
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "x\n", "docs/d.md": "y\n"})
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "land"], self.root, self.e.env, [
            (b"admit docs/d.md? [y/N]", "y"),
            (b"merge into origin (default)", ""),
        ])
        self.assertEqual(code, 0, seen)
        (_, _, tty), = self.fake.calls_of("apply")
        self.assertTrue(tty)
        self.assertEqual((self.proj / "docs/d.md").read_text(), "y\n")
        self.assertNotIn("Did the planner ratify", seen)
        self.assertIn("the block for the planner is on the clipboard (tee", seen)
        self.assertTrue(clip.read_text().startswith(f"=== RELAY BEGIN {sid} to planner ==="))

    def test_several_out_are_asked_for(self):
        a = self.start("fix-login", "--on", "alpha", "--goal", "g")
        other = self.run_office("open", "docs-job", "--lane", "alpha: docs", check=0).stdout.strip()
        b = self.start(other.split("/")[1], "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, b, {"docs/d.md": "new\n"})
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "land", "--not-now"], self.root, self.e.env, [
            (b"Which session lands, by its key (office land SID)", "nope"),
            (b"a key from the list above (1 to 2)", "2"),
            (b"merge into origin (default)", ""),
        ])
        self.assertEqual(code, 0, seen)
        # 0.22.0: each named by its folder, never typed by its id.
        self.assertIn(f"[1] folder 1, fix-login (alpha)", seen)
        self.assertIn(f"[2] folder 2, docs-job (alpha)", seen)
        self.assertIn(f"Landed: {b}", seen)
        self.assertTrue(self.fake.is_open(self.proj, a))


# --- office start, taking a bundle ---------------------------------------------------------

SITTING_PAGE = "notepad/2026-10-05-some-sitting-001.md"


def brief_with_page(words="> as assumed"):
    return (f"# Brief\n\nThe session's brief.\n\n--- NOTEPAD PAGE BEGIN {SITTING_PAGE} ---\n"
            f"# Planner's words\n\n{words}\n--- NOTEPAD PAGE END ---\n\n"
            "--- PAGE BEGIN ---\nthe project's own record\n--- PAGE END ---\n")


class TestStartABundle(LandCase):
    def argv(self, slug="fix-from-bundle", write="src", constraint=True):
        out = ["Fix it, from a bundle", "--slug", slug, "--write", write]
        return out + (["--constraint", ob.PROJECT_CONSTRAINT] if constraint else [])

    def test_a_bundle_goes_out_through_the_same_door(self):
        bundle = bundle_file(self.e.tmp / "b", "2026-10-05-fix-from-bundle", self.argv(), brief_with_page())
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", str(bundle), check=0)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertRegex(sid, r"^\d{4}-\d{2}-\d{2}-fix-from-bundle-001$")
        (cwd, argv, tty), = self.fake.calls_of("open")
        self.assertEqual((cwd, argv, tty), (os.path.realpath(self.proj), ["open", str(bundle)], False))
        tray = pathlib.Path(re.search(r"^Out tray: (.*)$", proc.stdout, re.M).group(1))
        # Since 0.17.0 a build session also gets the install's two page
        # templates (context-office-src-install.tar.gz).
        self.assertEqual(sorted(p.name for p in tray.iterdir()),
                         sorted([f"request-{sid}.tar.gz", "context-doctrine.tar.gz", "context-home.tar.gz",
                                 "context-office-src-install.tar.gz"]))
        self.assertIn("from the bundle 2026-10-05-fix-from-bundle.bale-bundle", proc.stdout)
        self.assertIn(f"\n- {sid}\n", (self.root / self.folder / "folder.md").read_text())
        opener = opener_from(proc.stdout)
        self.assertEqual(opener[1], f"This message opens bale session {sid}.")
        self.assertEqual(opener[2], "Goal, verbatim from the request manifest: Fix it, from a bundle")
        self.assertIn(f"When the response comes back: office land {sid}", proc.stdout)
        # The sitting's page is filed, alone, ASCII; the bare markers are not.
        page = (self.root / SITTING_PAGE).read_text()
        self.assertEqual(page, "# Planner's words\n\n> as assumed\n")
        self.assertEqual(self.subjects(1), [f"office start: the sitting's words from {sid}'s brief"])
        self.assertEqual(self.e.git(self.root, "show", "--name-only", "--format=", "HEAD").split(), [SITTING_PAGE])
        self.assertEqual(sorted(p.name for p in (self.root / "notepad").glob("*.md")),
                         ["2026-10-05-some-sitting-001.md"])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # The goal was never asked, and nothing was added to the bundle.
        self.assertEqual([c for c in self.fake.calls_of("pack") if "--context" not in c[1]], [])

    # --- which session a bundle leaves open (0.17.2) ---------------------------------
    #
    # The live case (home-office, 2026-10-12; probe of session
    # 2026-10-13-doctrine-core-001): the audience-line bundle was opened on
    # 2026-10-08 as 2026-10-08-audience-line-002, and on 2026-10-12 its
    # browser copy "2026-10-08-audience-line (1).bale-bundle" went to bale
    # open again while that session was still open. bale 0.4.52 took it as
    # a second desk on the open session and minted nothing, so the open set
    # did not move, and office start said nothing was newly open and made
    # no tray.

    def started(self, proc):
        sid = re.search(r"^(?:Packed|Joined) (\d{4}-\d{2}-\d{2}-[a-z0-9-]+-\d{3})\b", proc.stdout, re.M).group(1)
        tray = pathlib.Path(re.search(r"^Out tray: (.*)$", proc.stdout, re.M).group(1))
        return sid, tray

    def test_a_stem_dated_days_before_the_start(self):
        """The sid is bale's, minted on its own clock, and found as the one
        session newly open: never by the day of the start, whatever the
        stem's date, with bale open's report and with its --json line."""
        for version, stem, write in (("0.4.45", "2026-10-08-audience-line", "src"),
                                     ("0.4.52", "2026-10-01-dated-before", "docs")):
            self.e.env["FAKE_BALE_VERSION"] = version
            folder = self.run_office("open", f"job-{write}", "--lane", f"alpha: {write}", check=0).stdout.strip()
            bundle = bundle_file(self.e.tmp / "b", stem, self.argv(slug=stem[11:], write=write))
            proc = self.run_office("start", folder.split("/")[1], "--on", "alpha", "--bundle", str(bundle), check=0)
            sid, tray = self.started(proc)
            self.assertTrue(proc.stdout.startswith(f"Packed {sid} for {folder}."), proc.stdout)
            self.assertTrue(self.fake.is_open(self.proj, sid), sid)
            self.assertIn(f"\n- {sid}\n", (self.root / folder / "folder.md").read_text())
            self.assertIn(f"request-{sid}.tar.gz", [p.name for p in tray.iterdir()])
            self.assertIn(f"bale session {sid}", opener_from(proc.stdout)[1])
            (_, argv, _) = self.fake.calls_of("open")[-1]
            self.assertEqual(argv, ["open", str(bundle)] + (["--json"] if version == "0.4.52" else []), version)

    def open_on_the_eighth(self, version="0.4.52"):
        """The audience-line bundle opened on 2026-10-08 by bare name from
        the downloads, recorded in folder fix-login; its browser copy saved
        days later. Returns (sid, the copy's name)."""
        self.e.env["FAKE_BALE_VERSION"] = version
        bundle_file(self.downloads, "2026-10-08-audience-line", self.argv(slug="audience-line"), brief_with_page())
        self.e.env["FAKE_BALE_DAY"] = "2026-10-08"
        sid, _ = self.started(self.run_office("start", "fix-login", "--on", "alpha",
                                              "2026-10-08-audience-line.bale-bundle", check=0))
        del self.e.env["FAKE_BALE_DAY"]
        self.assertEqual(sid, "2026-10-08-audience-line-001")
        copy = "2026-10-08-audience-line (1).bale-bundle"
        shutil.copy(self.downloads / "2026-10-08-audience-line.bale-bundle", self.downloads / copy)
        later = self.run_office("open", "audience-again", "--lane", "alpha: src", check=0).stdout.strip()
        return sid, copy, later

    def test_the_live_case_a_second_desk_is_joined_recorded_and_carried(self):
        sid, copy, later = self.open_on_the_eighth()
        proc = self.run_office("start", later.split("/")[1], "--on", "alpha", copy, check=0)
        got, tray = self.started(proc)
        self.assertEqual(got, sid)
        self.assertTrue(proc.stdout.startswith(f"Joined {sid}, already open, as a second desk for {later}."),
                        proc.stdout)
        self.assertIn("bale opened no new session", proc.stderr)
        self.assertIn(f"{self.folder} records it too", proc.stderr)
        self.assertIn("joined as a second desk: the session was already open", proc.stdout)
        self.assertEqual(json.loads(self.fake.state.read_text())["repos"][os.path.realpath(self.proj)]["sessions"],
                         [sid], "a second desk opens nothing")
        self.assertEqual(self.fake.land_state()["desks"][sid], 2)
        self.assertIn(f"\n- {sid}: a second desk on a session already open\n",
                      (self.root / later / "folder.md").read_text())
        self.assertIn(f"request-{sid}.tar.gz", [p.name for p in tray.iterdir()])
        opener = opener_from(proc.stdout)
        self.assertIn(f"{sid}@desk-2", "\n".join(opener))
        self.assertIn(f"bale session {sid}.", opener[1])
        self.assertIn(f"When the response comes back: office land {sid}", proc.stdout)
        (_, argv, _), = [c for c in self.fake.calls_of("open") if copy in c[1]]
        self.assertEqual(argv, ["open", copy, "--json"])

    def test_a_second_desk_whose_request_left_the_outbox_is_said(self):
        sid, copy, later = self.open_on_the_eighth()
        self.e.env["FAKE_BALE_OUTBOX_GONE"] = "1"
        proc = self.run_office("start", later.split("/")[1], "--on", "alpha", copy, check=1)
        self.assertIn(f"joined the open session {sid}", proc.stderr)
        self.assertIn("no request tarball for it in the outbox", proc.stderr)
        self.assertNotIn(f"- {sid}", (self.root / later / "folder.md").read_text())

    def test_below_open_json_the_second_desk_is_named_as_the_likely_reason(self):
        sid, copy, later = self.open_on_the_eighth(version="0.4.45")
        proc = self.run_office("start", later.split("/")[1], "--on", "alpha", copy, check=1)
        self.assertIn("bale status names 0 newly open session(s) (none)", proc.stderr)
        self.assertIn("joins it as a second desk instead of opening one (bale 0.4.44 on)", proc.stderr)
        self.assertIn("needs bale 0.4.50", proc.stderr)
        self.assertNotIn(f"- {sid}", (self.root / later / "folder.md").read_text())
        self.assertNotIn("Out tray:", proc.stdout)

    def test_a_bare_name_is_bales_to_find_and_the_page_files_once(self):
        bundle_file(self.downloads, "2026-10-05-fix-from-bundle", self.argv(), brief_with_page())
        self.run_office("start", "fix-login", "--on", "alpha", "2026-10-05-fix-from-bundle.bale-bundle", check=0)
        (_, argv, _), = self.fake.calls_of("open")
        self.assertEqual(argv, ["open", "2026-10-05-fix-from-bundle.bale-bundle"])
        head = self.e.git(self.root, "rev-parse", "HEAD")
        # The same page again: left as it is.
        bundle_file(self.downloads, "2026-10-05-again", self.argv("again", "docs"), brief_with_page())
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", "2026-10-05-again.bale-bundle",
                               check=0)
        self.assertIn("already filed with these words; left as it is", proc.stderr)
        self.assertNotIn("office start: the sitting's words", self.subjects(2)[0])
        del head
        # A different page at that path: refused loudly, never overwritten.
        bundle_file(self.downloads, "2026-10-05-third", self.argv("third", "README.md"), brief_with_page("> no"))
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", "2026-10-05-third.bale-bundle",
                               check=1)
        self.assertIn(f"NOT FILED: {SITTING_PAGE}: a different page is already filed there", proc.stderr)
        self.assertIn("the session is open and its tray is ready", proc.stderr)
        self.assertEqual((self.root / SITTING_PAGE).read_text(), "# Planner's words\n\n> as assumed\n")
        self.assertEqual(len(self.fake.calls_of("open")), 3)

    def test_a_brief_given_by_hand_files_its_page_too(self):
        brief = self.e.tmp / "brief.md"
        brief.write_text(brief_with_page())
        self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--brief", str(brief), check=0)
        self.assertTrue((self.root / SITTING_PAGE).is_file())

    def test_a_bundle_takes_none_of_the_pack_flags(self):
        bundle = bundle_file(self.e.tmp / "b", "2026-10-05-x", self.argv())
        for extra in (("--goal", "g"), ("--write", "src"), ("--slug", "s"), ("--read-only",), ("--brief", "x")):
            proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", str(bundle), *extra, check=1)
            self.assertIn("a bundle carries its own pack line", proc.stderr, extra)
        self.assertIn("no such file", self.run_office("start", "fix-login", "--on", "alpha", "--bundle",
                                                      str(self.e.tmp / "b/none.bale-bundle"), check=1).stderr)
        self.assertEqual(self.fake.calls_of("open"), [])

    def test_bales_refusal_reaches_the_occupant_and_nothing_is_recorded(self):
        # Since 0.13.0 bale open --check finds out first, so the refusal
        # comes before the survey, the tray or the session (the third trip).
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", "2026-01-01-none.bale-bundle",
                               check=1)
        self.assertIn("bale cannot open the bundle 2026-01-01-none.bale-bundle on alpha", proc.stderr)
        self.assertIn("start stopped before anything was written", proc.stderr)
        self.assertIn("bundle not found: 2026-01-01-none.bale-bundle", proc.stderr)
        self.assertIn(str(self.downloads), proc.stderr)
        self.assertNotIn("- status: open", (self.root / self.folder / "folder.md").read_text())
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head, "the survey was committed")
        self.assertEqual(self.fake.calls_of("open"), [])
        self.assertEqual(len(self.fake.calls_of("open-check")), 1)

    def test_what_the_office_notices_and_does_not_add(self):
        bundle = bundle_file(self.e.tmp / "b", "2026-10-05-bare", self.argv(constraint=False))
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", str(bundle), check=0)
        self.assertIn("does not carry the office's constraint", proc.stderr)
        office = bundle_file(self.e.tmp / "b", "2026-10-05-office", ["Plan", "--slug", "plan", "--write", "notepad"])
        proc = self.run_office("start", "fix-login", "--in-office", "--bundle", str(office), check=0)
        self.assertIn(f"does not name {self.folder}", proc.stderr)
        (cwd, _, _) = self.fake.calls_of("open")[-1]
        self.assertEqual(cwd, os.path.realpath(self.root))


# --- a sitting from a bundle opens on the digest (0.21.0) ----------------------------------
#
# The live case (2026-10-13, read from an office's git log and bale
# status): office start sent out one read-only sitting from a bundle and
# committed "office start: digest" before its pack, then sent out another
# and committed none, with no open session holding the drafting table.
# The one path that skipped it without a word, and so the likely cause: a
# bundle named by a bare name is bale's to find (its search, the
# downloads), so the office could not read its pack line, could not tell
# it was read-only, and left the digest alone.

class TestABundledSittingOpensOnTheDigest(LandCase):
    def sitting_argv(self, slug="plan-wave", *extra):
        return ["Plan the next wave", "--slug", slug, "--read-only", *extra]

    def digest_commits(self):
        return [s for s in self.e.git(self.root, "log", "--format=%s").splitlines() if s == "office start: digest"]

    def test_named_by_its_path(self):
        bundle = bundle_file(self.e.tmp / "b", "2026-10-13-plan-wave", self.sitting_argv(), brief_with_page())
        proc = self.run_office("start", "fix-login", "--in-office", "--bundle", str(bundle), check=0)
        self.assertEqual(len(self.digest_commits()), 1, self.subjects(8))
        self.assertIn("wrote the digest for the sitting (drafting-table/digest.md)", proc.stderr)
        self.assertTrue((self.root / "drafting-table" / "digest.md").is_file())

    def test_named_by_a_bare_name_bales_search_finds(self):
        bundle_file(self.downloads, "2026-10-13-plan-wave", self.sitting_argv(), brief_with_page())
        proc = self.run_office("start", "fix-login", "--in-office", "2026-10-13-plan-wave.bale-bundle", check=0)
        # bale was asked by the name it was given, as before; the office read
        # the pack line where bale's rehearsal found the bundle.
        (_, argv, _), = self.fake.calls_of("open")
        self.assertEqual(argv, ["open", "2026-10-13-plan-wave.bale-bundle"])
        self.assertIn(f"bale found it at {self.downloads / '2026-10-13-plan-wave.bale-bundle'}", proc.stderr)
        self.assertEqual(len(self.digest_commits()), 1, self.subjects(8))
        self.assertIn("wrote the digest for the sitting (drafting-table/digest.md)", proc.stderr)
        subjects = self.subjects(8)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertLess(subjects.index(f"office sessions: {sid} in {self.name}"),
                        subjects.index("office start: digest"), "the digest is written before the pack")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_a_pack_line_the_office_cannot_read_is_said_in_one_line(self):
        # A line the office's reading of bale's flags does not take (an
        # abbreviated flag) leaves it unable to tell a sitting: it says so,
        # names the page it left and its time, and the start goes on.
        self.run_office("digest", check=None)
        written = re.search(r"^- written_at: (\S+) \(", (self.root / "drafting-table" / "digest.md").read_text(),
                            re.M).group(1)
        before = len(self.digest_commits())
        bundle_file(self.downloads, "2026-10-13-plan-odd", ["Plan the next wave", "--slug", "plan-odd", "--read-o"],
                    brief_with_page())
        proc = self.run_office("start", "fix-login", "--in-office", "2026-10-13-plan-odd.bale-bundle", check=0)
        self.assertRegex(proc.stdout, r"^Packed \S+ for ", proc.stderr)
        lines = [l for l in proc.stderr.splitlines() if "it leaves drafting-table/digest.md" in l]
        self.assertEqual(lines, [f"[office] the office cannot read the pack line of the bundle "
                                 f"2026-10-13-plan-odd.bale-bundle (bale found it at "
                                 f"{self.downloads / '2026-10-13-plan-odd.bale-bundle'}, and its pack line there "
                                 f"does not read), so it cannot tell whether it sends out a sitting: it leaves "
                                 f"drafting-table/digest.md as it was, written {written}; office digest writes it"])
        self.assertEqual(len(self.digest_commits()), before)

    def test_a_bundle_that_is_no_sitting_gets_no_digest_and_no_line(self):
        bundle_file(self.downloads, "2026-10-13-office-work", ["Write it", "--slug", "office-work", "--write",
                                                                self.folder, "--write", "notepad"], brief_with_page())
        proc = self.run_office("start", "fix-login", "--in-office", "2026-10-13-office-work.bale-bundle", check=0)
        self.assertRegex(proc.stdout, r"^Packed \S+ for ", proc.stderr)
        self.assertEqual(self.digest_commits(), [])
        self.assertNotIn("digest", proc.stderr)

    def test_the_units(self):
        ro = bundle_file(self.e.tmp / "u", "ro", self.sitting_argv())
        rw = bundle_file(self.e.tmp / "u", "rw", ["Fix", "--slug", "fix", "--write", "src"])
        odd = bundle_file(self.e.tmp / "u", "odd", ["Fix", "--slug", "fix", "--read-o"])
        self.assertEqual([ob.bundle_read_only(b) for b in (ro, rw, odd, self.e.tmp / "u" / "none.bale-bundle", None)],
                         [True, False, None, None, None])
        self.assertIsNone(ob.digest_written_at(self.root))
        self.assertIn("it leaves drafting-table/digest.md unwritten, as it was; office digest writes it",
                      ob.digest_left_line(self.root, "x.bale-bundle", "why"))


if __name__ == "__main__":
    unittest.main()
