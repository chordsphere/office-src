"""The fake bale that packs, for office start's tests, as a fixed module
(0.27.0; until then a script text in tests/test_start.py, formatted and
written into every test's tree and compiled again on every call).

Every line it prints is built from lines the out-and-in probe captured
from a real bale 0.4.45 (the development record's fixtures, bale-0.4.45/
pack/), with the session id, the paths and the goal swapped in. It keeps
the open sessions per directory in its own state file, never in .bale/
beyond the outbox, and refuses anything it was not built for with exit
97. It answers --version (FAKE_BALE_VERSION, else 0.4.45), status --json,
and pack --json (a session, or --context); every call is recorded as one
JSON line [cwd, argv] in the calls file.

A test never runs this file. tests/test_start.py FakePackBale writes a
program named bale in the test's own tree (tests/test_office.py
fake_program) that imports this module and calls main with the test's
config: {"fixtures": dir, "state": file, "calls": file}. The land fake
(land_bale.py) calls main in its own process for the verbs it hands on.
Only json, os, pathlib and sys load for every call; the rest load where a
pack needs them, so a --version or a status costs one interpreter start.
"""

import json
import os
import pathlib
import sys


def fx(fix, label):
    return json.loads((fix / (label + ".json")).read_text(encoding="utf-8"))


def load(state_file):
    return json.loads(state_file.read_text()) if state_file.is_file() else {"repos": {}, "fail": []}


def save(state_file, s):
    state_file.write_text(json.dumps(s))


def files_of(root, includes, context):
    """The files a pack of root carries: git's tracked and untracked
    files outside .bale/ (every file, outside git), narrowed to the
    includes, with bale.toml's include group's pulls when an include
    touches a trigger (never under --context)."""
    import subprocess
    root = pathlib.Path(root)
    git = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if git.returncode == 0:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "."],
                             capture_output=True, text=True).stdout.split()
    else:
        out = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()]
    out = [f for f in out if not f.startswith(".bale/") and "/.bale/" not in f]
    if includes:
        keep = list(includes)
        cfg = root / "bale.toml"
        if cfg.is_file() and not context:
            import tomllib
            pack = tomllib.loads(cfg.read_text()).get("pack", {})
            if pack.get("include_group") and any(i.split("/")[0] in pack.get("include_group_triggers", []) for i in includes):
                keep += pack.get("include_group_pulls", [])
        out = [f for f in out if any(f == i or f.startswith(i.rstrip("/") + "/") for i in keep)]
    return sorted(out), git.returncode == 0


def hit(x, y):
    x, y = x.strip("/"), y.strip("/")
    return x == "" or y == "" or x == y or x.startswith(y + "/") or y.startswith(x + "/")


def main(cfg, argv):
    fix, state_file, calls = pathlib.Path(cfg["fixtures"]), pathlib.Path(cfg["state"]), pathlib.Path(cfg["calls"])
    cwd = os.path.realpath(os.getcwd())
    with calls.open("a", encoding="utf-8") as log:
        log.write(json.dumps([cwd, argv]) + "\n")
    if argv == ["--version"]:
        print("bale " + os.environ.get("FAKE_BALE_VERSION", "0.4.45"))
        return 0
    state = load(state_file)
    repo = state["repos"].setdefault(cwd, {"sessions": [], "scopes": {}, "outbox": []})
    if argv == ["status", "--json"]:
        line = json.loads(fx(fix, "office-status")["stdout"][0])
        line["sid"] = repo["sessions"][0] if repo["sessions"] else None
        line["sessions"] = repo["sessions"]; line["scopes"] = repo["scopes"]; line["outbox"] = repo["outbox"]
        # The light pointer at applied history (0.22.0, the home screen): the
        # land fake appends each session it applies.
        applied = repo.get("applied") or []
        line["applied"] = {"count": len(applied), "latest": applied[-1] if applied else None}
        line["repo"]["root"] = cwd
        print(json.dumps(line))
        return 0
    if not argv or argv[0] != "pack":
        print("fake bale: not built for bale " + " ".join(argv), file=sys.stderr)
        return 97
    import argparse
    import datetime
    import io
    import re
    import tarfile
    ap = argparse.ArgumentParser(prog="bale pack")
    ap.add_argument("goal", nargs="?"); ap.add_argument("--context", action="store_true")
    ap.add_argument("--slug"); ap.add_argument("--include", action="append", default=[])
    ap.add_argument("--write", action="append", default=[]); ap.add_argument("--constraint", action="append", default=[])
    ap.add_argument("--readme-file"); ap.add_argument("--no-readme", action="store_true")
    ap.add_argument("--work-class"); ap.add_argument("--read-only", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    if not a.json:
        print("fake bale: built for --json packs only", file=sys.stderr)
        return 97
    outbox = pathlib.Path(cwd) / ".bale" / "outbox"
    if a.context:
        for flag in ("goal", "slug", "readme_file", "work_class"):
            if getattr(a, flag):
                print("fake bale: --context refuses a session-only flag", file=sys.stderr)
                return 2
        name = pathlib.Path(cwd).name
        files, git = files_of(cwd, a.include, a.context)
        outbox.mkdir(parents=True, exist_ok=True)
        tb = outbox / ("context-" + name + ".tar.gz")
        total = 0
        with tarfile.open(tb, "w:gz") as t:
            for f in files:
                t.add(pathlib.Path(cwd) / f, arcname=name + "/" + f); total += (pathlib.Path(cwd) / f).stat().st_size
        line = json.loads(fx(fix, "office-context-whole")["stdout"][0])
        line.update(tarball=str(tb), directory=cwd, tree_name=name, context_files=len(files), total_bytes=total, git=git)
        print(json.dumps(line, separators=(",", ":")))
        print("[bale] context pack of " + cwd + " — no session is opened", file=sys.stderr)
        return 0
    if not a.goal or not a.slug:
        print("[bale] error: piped, a goal and --slug are required", file=sys.stderr)
        return 1
    if not a.readme_file and not a.no_readme:
        print("[bale] error: no README prose; --no-readme acknowledges it", file=sys.stderr)
        return 1
    for p in a.write + a.include:
        if not (pathlib.Path(cwd) / p).exists():
            print("[bale] error: forecast or include names no existing path: " + p, file=sys.stderr)
            return 1
    mine = [] if a.read_only else (a.write or a.include or [""])
    for sid in repo["sessions"]:
        theirs = repo["scopes"][sid] or []
        pairs = [(m, t) for m in mine for t in theirs if hit(m, t)]
        if pairs:
            second = fx(fix, "office-second-pack")
            err = second["stderr"][-1]
            err = err.replace("2026-10-02-probe-office-work-001", sid).replace(
                "(notepad ~ notepad)", "(" + ", ".join(m + " ~ " + t for m, t in pairs) + ")")
            for l in second["stderr"][:-1]:
                print(l, file=sys.stderr)
            print(err, file=sys.stderr)
            return 1
    if "pack" in state["fail"]:
        print("[bale] error: the fake was told to refuse this pack", file=sys.stderr)
        return 1
    day = os.environ.get("FAKE_BALE_DAY") or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    n = 1 + sum(1 for s in repo["outbox"] if s.startswith("request-" + day + "-" + a.slug + "-"))
    sid = day + "-" + a.slug + "-" + format(n, "03d")
    outbox.mkdir(parents=True, exist_ok=True)
    tb = outbox / ("request-" + sid + ".tar.gz")
    files, _ = files_of(cwd, a.include, a.context)
    manifest = {"session_id": sid, "goal": a.goal, "constraints": a.constraint, "resolved_scope": mine if mine != [""] else ["."],
                "readme": {"path": "README.md"} if a.readme_file else None,
                "work_class": a.work_class or "mixed", "context_included": ["context/" + f for f in files]}
    with tarfile.open(tb, "w:gz") as t:
        data = json.dumps(manifest).encode()
        info = tarfile.TarInfo("request-001/manifest.json"); info.size = len(data)
        t.addfile(info, io.BytesIO(data))
        if a.readme_file:
            t.add(a.readme_file, arcname="request-001/README.md")
        for f in files:
            t.add(pathlib.Path(cwd) / f, arcname="request-001/context/" + f)
    repo["sessions"].append(sid); repo["scopes"][sid] = [] if a.read_only else mine; repo["outbox"].append(tb.name)
    save(state_file, state)
    label = "project-pack" if a.readme_file else "office-pack"
    cap = fx(fix, label)
    old = json.loads(cap["stdout"][0])
    line = dict(old)
    oldsid, oldroot = old["sid"], old["tarball"].split("/.bale/")[0]
    line.update(sid=sid, tarball=str(tb), log=cwd + "/.bale/logs/" + sid + ".log",
                session_dir=cwd + "/.bale/sessions/" + sid, context_files=len(files))
    print(json.dumps(line))
    oldgoal = re.search(r"Goal, verbatim from the request manifest: (.*)$", "\n".join(cap["stderr"]), re.M).group(1)
    for l in cap["stderr"]:
        l = l.replace(oldsid, sid).replace(oldroot, cwd)
        if l.startswith("Goal, verbatim from the request manifest: "):
            l = l.replace(oldgoal, a.goal)
        print(l, file=sys.stderr)
    return 0
