"""The fake bale for office land's and office start's bundle tests, as a
fixed module (0.27.0; until then a script text in tests/test_land.py,
formatted and written into every test's tree, compiled again on every
call, and handing its pack, status and --version on to a second script
by starting the interpreter again).

pack, status and --version go to the packing fake (pack_bale.py), in this
process; this adds apply and retry (the walkthrough's merge, a HOLD, a
base-drift and an out-of-forecast refusal, a clarification, a bailout),
unlock, the dossier (stats --sid, answered since 0.55.0 only in the repo
that packed the session), relay's re-emitted block, open and open
--check, and handoff (0.52.0), each printing lines the return-trip probe (and the later probes
named where they are used) captured from a real bale, kept verbatim with
their sha256 in the development record's fixtures, with the session id
and the paths swapped in; on a terminal it asks what the real one asks,
where the real one asks it. Its own state sits in the same state file as
the packing fake's, under "land"; every call is recorded as one JSON line
[cwd, argv, stdin is a terminal] in the calls file.

The directory each capture was made in is the capture's own cwd, read
from the fixture as it swaps (0.27.0), so no probe's path is named here.

A test never runs this file. tests/test_land.py FakeLandBale writes a
program named bale in the test's own tree (tests/test_office.py
fake_program) that imports this module and calls main with the test's
config: {"fixtures": the land fixtures, "miss": the dossier of no
session, "state": file, "calls": file, "pack": the packing fake's own
config}. FAKE_BALE_VERSION, FAKE_BALE_SEARCH, FAKE_BALE_UNLOCK_FAILS and
FAKE_BALE_OUTBOX_GONE steer it from the test's environment, as before;
FAKE_BALE_RECORD_GONE (a session id) makes handoff find no record of that
bailed session (0.52.0).

The bailout and the handoff are not captures: no real bailout existed on
the occupant's machine to capture. They are built from bale 0.4.56's code
as the probes handoff-ground and handoff-tail of sitting
2026-11-06-office-src-plan-sitting-001 read it (cmd_handoff in bin/bale)
and from bale help apply's words for a bailout: apply closes the session
and names bale handoff; handoff refuses a detached HEAD, anything but a
bailout and a bailout without handoff.md, inherits the goal from the
bailed session's request record (here its request in the outbox, the
fake's record of it) and its recorded forecast, runs pack's gate, mints
the bailout's slug on the day with the next counter, writes the request
(handoff.md first) and opens the session, and reports format_summary_block's
rows on stdout with no opener.
"""

import json
import os
import pathlib
import sys

import pack_bale


class Packed:
    """What the packing fake did in this process: its exit code and what
    it printed, as a finished subprocess would carry them."""

    def __init__(self, returncode, stdout, stderr):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def packed(pack_cfg, args):
    """Run the packing fake on args in this process, its output caught."""
    import contextlib
    import io
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = pack_bale.main(pack_cfg, args)
        except SystemExit as exc:  # argparse refusing a flag exits, as bale's own parser would
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return Packed(code, out.getvalue(), err.getvalue())


def probe_downloads(cap):
    """The downloads directory of the probe that captured cap: dl/ beside
    the throwaway repo it ran in."""
    return str(pathlib.PurePosixPath(cap["cwd"]).parent / "dl")


def main(cfg, argv):
    FIX = pathlib.Path(cfg["fixtures"])
    UNLOCK_FIX = FIX.parent / "unlock"
    MISS = pathlib.Path(cfg["miss"])
    STATE = pathlib.Path(cfg["state"])
    CALLS = pathlib.Path(cfg["calls"])
    FAKE_VERSION = tuple(int(x) for x in os.environ.get("FAKE_BALE_VERSION", "0.4.45").split("."))
    cwd = os.path.realpath(os.getcwd())
    with CALLS.open("a", encoding="utf-8") as log:
        log.write(json.dumps([cwd, argv, sys.stdin.isatty()]) + "\n")
    def fx(label):
        return json.loads((FIX / (label + ".json")).read_text(encoding="utf-8"))
    def load():
        s = json.loads(STATE.read_text()) if STATE.is_file() else {"repos": {}, "fail": []}
        s.setdefault("land", {"base": {}, "attempts": {}, "held": [], "clar": {}, "packed": {}, "unlocked": []})
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
        return pack_bale.main(cfg["pack"], argv)

    # Past the hand-on, each verb loads the modules it uses, where it starts:
    # a dossier or a relay costs no more than the interpreter and json.
    state = load()
    L = state["land"]
    repo = state["repos"].setdefault(cwd, {"sessions": [], "scopes": {}, "outbox": []})

    def pack(args):
        """The packing fake packs; this stamps each committed forecast file's
        HEAD bytes, as bale's base-drift stamp does."""
        before = set(repo["sessions"])
        p = packed(cfg["pack"], args)
        s = load()
        r = s["repos"].get(cwd, {"sessions": []})
        new = [x for x in r["sessions"] if x not in before]
        if p.returncode == 0 and new:
            sid = new[0]
            scope = r["scopes"][sid] or []
            files = git("ls-files", check=False).stdout.split()
            s["land"]["base"][sid] = {f: head_sha(f) for f in files if scope and under(f, scope)}
            s["land"]["packed"][sid] = cwd
            save(s)
        return p, new

    if argv[0] == "pack":
        import hashlib, subprocess
        p, _ = pack(argv)
        sys.stdout.write(p.stdout); sys.stderr.write(p.stderr)
        sys.exit(p.returncode)

    def attempt(sid, command, outcome, paths, vstate):
        s = load()
        s["land"]["attempts"].setdefault(sid, []).append(
            {"command": command, "outcome": outcome, "change_paths": paths, "state": vstate})
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
        import hashlib, re, shutil, subprocess, tarfile, tempfile
        verb = argv[0]
        # bale's two accepts (0.37.0), before the tarball as office land
        # places them: a moved base admitted per path, the checkpoint
        # switch recorded (this fake keeps no checkpoint to refuse).
        rest, accept_change, accept_drift = argv[1:], False, []
        while rest and rest[0].startswith("--"):
            if rest[0] == "--accept-checkpoint-change":
                accept_change, rest = True, rest[1:]
            elif rest[0] == "--accept-base-drift" and len(rest) > 1:
                accept_drift.append(rest[1]); rest = rest[2:]
            else:
                print("fake bale: built for bale " + verb + " [the two accepts] TARBALL only", file=sys.stderr)
                sys.exit(97)
        # A checkpoint that changed since the pack (0.37.0): bale's
        # provenance gate refuses before staging, on stderr, recording no
        # attempt, unless the accept is given. Not a capture: bale's own
        # words are format_checkpoint_stamp_refusal's, read in the probe of
        # session 2026-10-28-m10-land-flags-005; this line stands in.
        changed = os.environ.get("FAKE_BALE_CHECKPOINT_CHANGED")
        if len(rest) != 1:
            print("fake bale: built for bale " + verb + " [the two accepts] TARBALL only", file=sys.stderr); sys.exit(97)
        tb = resolve(rest[0], "tarball")
        if tb is None:
            missing(rest[0], "tarball")
        with tarfile.open(tb) as t:
            names = t.getnames()
            mname = next(n for n in names if re.fullmatch(r"response-\d{3}/manifest\.json", n))
            m = json.loads(t.extractfile(mname).read())
            top = mname.split("/")[0]
            tmp = tempfile.mkdtemp(prefix="fake-bale-apply-")
            t.extractall(tmp)
        sid = m["responds_to"]
        if sid not in repo["sessions"]:
            print("[bale] error: " + tb.name + " answers " + sid + ", which is not open here", file=sys.stderr); sys.exit(1)
        held = sid in L["held"]
        if changed == sid and not accept_change:
            print("[bale] error: [REJECT] blind checkpoint changed since pack for " + sid
                  + " (fake); re-run with --accept-checkpoint-change", file=sys.stderr)
            sys.exit(1)
        if verb == "apply" and held:
            print("[bale] error: " + sid + " is held; bale retry <tarball> runs a corrected response", file=sys.stderr); sys.exit(1)
        if verb == "retry" and not held:
            print("[bale] error: " + sid + " is not held; bale apply runs its response", file=sys.stderr); sys.exit(1)
        if m["response_kind"] == "clarification":
            cap = fx("apply-clar")
            say(swap(cap["stdout"], "2026-10-03-probe-clar-001", sid, cap["cwd"], cwd))
            s = load(); s["land"]["clar"][sid] = m["questions"]; save(s)
            sys.exit(0)
        if m["response_kind"] == "bailout":
            # A bailout (0.52.0, not a capture; the module's docstring says
            # what it is built from): an attempt with outcome bailout, the
            # session closed, its request record kept, and bale's next step,
            # bale handoff, named.
            s = load()
            r = s["repos"][cwd]
            r["sessions"].remove(sid)
            s["land"].setdefault("bailed", {})[sid] = r["scopes"].pop(sid, None)
            s["land"]["attempts"].setdefault(sid, []).append(
                {"command": verb, "outcome": "bailout", "change_paths": [], "state": None})
            save(s)
            say(["[bale] " + sid + ": bailout response (handoff.md: " + str(len(names)) + " member(s) read)",
                 "[bale] closed session " + sid + " (bailout); its request record is kept for the handoff",
                 "", "  next step: bale handoff '" + tb.name + "' packs the fresh session the handoff asks for"])
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
                say(swap(cap["stdout"], "2026-10-03-probe-outside-001", sid, cap["cwd"], cwd,
                         [("docs/outside.md", ", ".join(outside)), ("write forecast: notes", "write forecast: " + ", ".join(scope)),
                          ("response-" + "2026-10-03-probe-outside-001", "response-" + sid)]))
                attempt(sid, verb, "scope-drift-refused", paths, None)
                sys.exit(1)
        base = L["base"].get(sid, {})
        moved = [p for p in paths if p in base and head_sha(p) != base[p] and p not in accept_drift]
        if moved:
            cap = fx("apply-drift")
            say(swap(cap["stdout"], "2026-10-03-probe-drift-001", sid, cap["cwd"], cwd,
                     # bale's re-run line: one flag per moved path, and the
                     # verb and tarball this call had.
                     [("--accept-base-drift 'notes/job/folder.md'",
                       " ".join("--accept-base-drift '" + p + "'" for p in moved)),
                      ("bale apply 'response-" + sid + ".tar.gz'", "bale " + verb + " '" + tb.name + "'"),
                      ("notes/job/folder.md", ", ".join(moved))]))
            attempt(sid, verb, "base-drift-refused", paths, None)
            sys.exit(1)
        v = subprocess.run(["bash", str(pathlib.Path(tmp) / top / "validation.sh")], cwd=str(pathlib.Path(tmp) / top),
                           capture_output=True, text=True)
        if v.returncode != 0:
            cap = fx("apply-hold")
            say(swap(cap["stdout"], "2026-10-03-probe-hold-001", sid, cap["cwd"], cwd,
                     [(probe_downloads(cap), str(tb.parent))]))
            attempt(sid, verb, "held", paths, "HOLD")
            sys.exit(1)
        cap = fx("apply-applied")
        lines = swap(cap["stdout"], "2026-10-03-probe-applied-001", sid, cap["cwd"], cwd)
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
        if paths:
            git("add", "--", *paths)
            git("commit", "-q", "-m", "[bale " + sid + "] " + m["summary"], "--", *paths)
        else:
            # An empty changes[] lands as bale 0.4.56 lands it (0.51.0, the
            # probe empty-landing of 2026-11-06): its apply makes the session
            # commit and the merge with plumbing (commit-tree), which never
            # refuses an unchanged tree, and tags applied/SID with no check
            # on the change; here, one commit with no change, tagged.
            git("commit", "-q", "--allow-empty", "-m", "[bale " + sid + "] " + m["summary"])
        git("tag", "applied/" + sid)
        attempt(sid, verb, "applied", paths, "PASS")
        say(lines[at:])
        sys.exit(0)

    if argv[0] == "unlock":
        import subprocess
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
        old_sid = "2026-10-04-probe-unlock-json-001"
        if sid not in repo["sessions"]:
            cap = json.loads((UNLOCK_FIX / "unlock-ro-again.json").read_text(encoding="utf-8"))
            say(swap(cap["stderr"], old_sid, sid, cap["cwd"], cwd), err=True); sys.exit(1)
        if os.environ.get("FAKE_BALE_UNLOCK_FAILS") == sid:
            print("[bale] error: unlock " + sid + ": refused for the test", file=sys.stderr); sys.exit(1)
        s = load()
        r = s["repos"][cwd]
        reason = given or ("closed-read-only" if r["scopes"].get(sid) == [] else "abandoned")
        r["sessions"].remove(sid); r["scopes"].pop(sid, None)
        s["land"]["unlocked"].append(sid)
        s["land"].setdefault("unlock_reasons", {})[sid] = reason
        save(s)
        rec = pathlib.Path(cwd) / ("cla" + "ude") / "telemetry" / (sid + ".json")
        rec.parent.mkdir(parents=True, exist_ok=True)
        rec.write_text(json.dumps({"session_id": sid, "outcome": "unlocked"}) + "\n")
        git("add", "--", str(rec.relative_to(cwd)))
        git("commit", "-q", "-m", "[bale sweep " + sid + "] " + reason, "--", str(rec.relative_to(cwd)))
        sha = git("rev-parse", "--short", "HEAD").stdout.strip()
        cap = json.loads((UNLOCK_FIX / "unlock-ro-json.json").read_text(encoding="utf-8"))
        extra = [("dcd55ba", sha), ("closed-read-only", reason)]
        say(swap(cap["stderr"], old_sid, sid, cap["cwd"], cwd, extra), err=True)
        say(swap(cap["stdout"], old_sid, sid, cap["cwd"], cwd, extra))
        sys.exit(0)

    if argv[:2] == ["stats", "--sid"] and argv[3:] == ["--json"]:
        sid = argv[2]
        # Only the repo that packed the sid holds its record (0.55.0), as a
        # real bale keeps its records per repo: asked anywhere else, the
        # dossier of no session. Before 0.55.0 any repo answered, so no test
        # could tell "still open in alpha" from "in the office".
        if sid not in L["packed"] or os.path.realpath(L["packed"][sid]) != cwd:
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
        rec["closure"] = ({"category": "bailout" if rec["outcome"] == "bailout" else "applied", "unlock_reason": None}
                          if not is_open else None)
        if sid in L["unlocked"]:
            why = L.get("unlock_reasons", {}).get(sid, "closed-read-only")
            rec.update(outcome="unlocked", in_flight=False, read_only=why == "closed-read-only",
                       closure={"category": "unlocked", "unlock_reason": why})
        attempts = [dict(pack_a)]
        stem = L.get("stems", {}).get(sid)
        if stem is not None:
            attempts[0]["bundle"] = {"stem": stem, "brief_sha256": None, "checkpoint_sha256": None,
                                     "manifest_sha256": None}
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
        say(swap(cap["stdout"], "2026-10-03-probe-clar-001", sid, cap["cwd"], cwd))
        say(swap(cap["stderr"], "2026-10-03-probe-clar-001", sid, cap["cwd"], cwd), err=True)
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

    if argv[0] == "handoff":
        import datetime, hashlib, io, re, subprocess, tarfile
        if len(argv) != 2:
            print("fake bale: built for bale handoff TARBALL only", file=sys.stderr); sys.exit(97)
        if git("symbolic-ref", "-q", "HEAD", check=False).returncode != 0:
            print("[bale] error: bale handoff refuses a detached HEAD: it stamps the checked-out branch as the new "
                  "session's integration target; check a branch out first", file=sys.stderr); sys.exit(1)
        tb = resolve(argv[1], "tarball")
        if tb is None:
            missing(argv[1], "tarball")
        with tarfile.open(tb) as t:
            names = t.getnames()
            mname = next(n for n in names if re.fullmatch(r"response-\d{3}/manifest\.json", n))
            m = json.loads(t.extractfile(mname).read())
            hname = mname.split("/")[0] + "/handoff.md"
            handoff_md = t.extractfile(hname).read() if hname in names else None
        if m.get("response_kind") != "bailout":
            print("[bale] error: bale handoff is for bailout responses only (" + tb.name + " is response_kind="
                  + str(m.get("response_kind")) + ")", file=sys.stderr); sys.exit(1)
        if handoff_md is None:
            print("[bale] error: " + tb.name + " is a bailout without handoff.md", file=sys.stderr); sys.exit(1)
        parent = m["responds_to"]
        record = pathlib.Path(cwd) / ".bale" / "outbox" / ("request-" + parent + ".tar.gz")
        if not record.is_file() or os.environ.get("FAKE_BALE_RECORD_GONE") == parent:
            print("[bale] error: cannot inherit goal: request manifest not found at " + cwd + "/.bale/sessions/"
                  + parent + "/manifest.json", file=sys.stderr); sys.exit(1)
        with tarfile.open(record) as t:
            pm = json.loads(t.extractfile("request-001/manifest.json").read())
        forecast = L.get("bailed", {}).get(parent)
        if forecast is None:
            forecast = pm.get("resolved_scope") or ["."]
        for s_ in repo["sessions"]:
            theirs = repo["scopes"].get(s_) or ["."]
            if repo["scopes"].get(s_) == [] or forecast == []:
                continue
            pairs = [(a, b) for a in forecast for b in theirs if meets(a, b)]
            if pairs:
                print("[bale] error: forecast overlaps open session " + s_ + " ("
                      + ", ".join(a + " ~ " + b for a, b in pairs) + "); narrow with --write, apply the open "
                      "session's response, or unlock it", file=sys.stderr); sys.exit(1)
        slug = re.fullmatch(r"\d{4}-\d{2}-\d{2}-(.+)-\d{3}", parent).group(1)
        day = pack_bale.minting_day()
        n = 1 + sum(1 for s_ in repo["outbox"] if s_.startswith("request-" + day + "-" + slug + "-"))
        sid = day + "-" + slug + "-" + format(n, "03d")
        outbox = pathlib.Path(cwd) / ".bale" / "outbox"
        out = outbox / ("request-" + sid + ".tar.gz")
        packed_at = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
        manifest = {"session_id": sid, "goal": pm["goal"], "constraints": [], "out_of_scope": [],
                    "resolved_scope": forecast, "readme": None, "context_included": ["context/handoff.md"],
                    "depends_on": {"previous_response": parent, "previous_probe": None, "superseded_session": None},
                    "provenance": {"packed_at": packed_at, "work_class": pm.get("work_class", "mixed")}}
        with tarfile.open(out, "w:gz") as t:
            for rel, data in (("request-001/manifest.json", json.dumps(manifest).encode()),
                              ("request-001/context/handoff.md", handoff_md)):
                info = tarfile.TarInfo(rel); info.size = len(data)
                t.addfile(info, io.BytesIO(data))
        s = load()
        r = s["repos"][cwd]
        r["sessions"].append(sid); r["scopes"][sid] = forecast; r["outbox"].append(out.name)
        files = git("ls-files", check=False).stdout.split()
        s["land"]["base"][sid] = {f: head_sha(f) for f in files if under(f, forecast)}
        s["land"]["packed"][sid] = cwd
        s["land"].setdefault("handed_off", {})[sid] = parent
        save(s)
        print("[bale] handoff from bailout " + parent + " -> new session " + sid, file=sys.stderr)
        print("[bale] wrote " + str(out), file=sys.stderr)
        say(["", "  session id:     " + sid, "  tarball:        " + str(out),
             "  inherited:      goal and write forecast of " + parent,
             "  context:        1 file(s) (handoff.md)", "  depends_on:     " + parent, "",
             "Send the tarball to the agent. When the response comes back,", "run: bale apply <response-tarball>"])
        sys.exit(0)

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
        shown = {"path": str(b.resolve()), "sha256": hashlib.sha256(b.read_bytes()).hexdigest(),
                  "stem": b.name[:-len(".bale-bundle")]}
        members = {"brief": hashlib.sha256(brief).hexdigest() if brief is not None else None, "checkpoint": None}
        # A bundle's identity is its manifest and its brief, not its file name:
        # a browser's "NAME (1)" copy is the same bundle.
        return manifest, brief, hashlib.sha256(raw + (brief or b"")).hexdigest(), shown, members

    if argv[:1] == ["open"] and "--check" in argv:
        import hashlib, tarfile
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
        desk = [x for x in repo["sessions"] if L.get("opened_from", {}).get(x) == check_id]
        if desk:
            n = L.get("desks", {}).get(desk[0], 1) + 1
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
        import hashlib, re, subprocess, tarfile, tempfile
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
        L.setdefault("opened_from", {}); L.setdefault("desks", {})
        joined = [x for x in repo["sessions"] if L["opened_from"].get(x) == identity]
        if joined:
            sid = joined[0]
            s = load(); desks = s["land"].setdefault("desks", {}); n = desks.get(sid, 1) + 1; desks[sid] = n; save(s)
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
        s = load(); s["land"].setdefault("opened_from", {})[sid] = identity
        # The bundle's stem, as bale's records keep it on the pack attempt
        # (attempts[].bundle.stem; the home screen reads it, 0.22.0).
        s["land"].setdefault("stems", {})[sid] = shown["stem"]; save(s)
        label = "open-brief" if brief is not None else "open-ro-bare"
        cap = fx(label)
        old_sid = "2026-10-03-probe-open-brief-001" if brief is not None else "2026-10-03-probe-open-ro-001"
        old_goal = re.search(r"^Goal, verbatim from the request manifest: (.*)$", "\n".join(cap["stdout"]), re.M).group(1)
        old_bundle = [l for l in cap["stdout"] if l.startswith("[bale] opening planner bundle ")][0][len("[bale] opening planner bundle "):]
        lines = swap(cap["stdout"], old_sid, sid, cap["cwd"], cwd, [(old_goal, bundle["pack_argv"][0]), (old_bundle, str(b))])
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
