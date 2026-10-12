#!/usr/bin/env python3
"""The letterhead check: what leaves the office for an audience is read first.

Doctrine section 2 names the letterhead as the guard on what leaves the
office. This module is that guard made mechanical: it reads a set of
text files and names every line that holds something the letterhead
refuses, as `file:line: what`. The list it refuses is share/letterhead.toml
(names of models, vendors and products; tell-tale phrasing an assistant
writes; bale's own marks) plus, when the office has letterhead/forbidden.txt,
each non-blank, non-comment line of it as a fixed string.

What it reads, in order of what it was told:

  --range A..B   the files the range changed, at B's version, and the
                 range's commit messages
  (a dirty tree) the files the working tree changed, as they are
  --all          the whole tree (git's tracked and untracked files,
                 or every file when the directory is not a git repo,
                 which the check says)
  --words FILE   a text checked as it is (a delivery's words), any
                 number of times

Binary files are skipped by their name (the suffixes the rules list) and
by a NUL byte in their first bytes; OFFICE_DEBUG=1 names every file read
and every one skipped. Exit 1 with a hit, 0 clean, 2 when the check
itself could not run.

This file imports nothing of the office, on purpose: office
letterhead-check runs it on a tree here, and on a hosted project's tree
through the project's shell, where the module travels as the program
python3 reads from stdin and the rules travel as one JSON argument
(--rules-json). Standard library only.
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

RULE_SECTIONS = ("names", "phrasing", "marks")
# A line longer than this is read for hits in full, but a match is
# reported with the line cut short, so a minified file does not flood
# the screen.
SHOWN = 100
NUL_PROBE = 8192


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: letterhead: {msg}", file=sys.stderr)


class CheckError(Exception):
    """The check could not run: said in one line, exit 2."""


def load_rules_toml(path):
    """The rules as share/letterhead.toml holds them, as the JSON shape
    the check reads: patterns per section, forbidden strings (none here)
    and the binary suffixes."""
    import tomllib  # Python 3.11+; the office's floor
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    rules = {}
    for section in RULE_SECTIONS:
        patterns = (data.get(section) or {}).get("patterns")
        if not isinstance(patterns, list) or not all(isinstance(p, str) and p for p in patterns):
            raise CheckError(f"{path}: [{section}] patterns is not a list of non-empty strings")
        rules[section] = list(patterns)
    suffixes = (data.get("binary") or {}).get("suffixes") or []
    if not all(isinstance(s, str) and s.startswith(".") for s in suffixes):
        raise CheckError(f"{path}: [binary] suffixes is not a list of suffixes")
    rules["binary"] = [s.lower() for s in suffixes]
    rules["forbidden"] = []
    return rules


def forbidden_lines(text):
    """The fixed strings letterhead/forbidden.txt holds: each non-blank
    line that does not start with #, stripped."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def compile_rules(rules):
    """[(kind, pattern text, compiled)] in the order hits are reported:
    the office's forbidden strings first (the occupant's own words), then
    names, phrasing and marks. A pattern that does not compile is the
    check's error, never a silent skip."""
    out = []
    for text in rules.get("forbidden") or []:
        out.append(("forbidden", text, re.compile(re.escape(text), re.I)))
    for section in RULE_SECTIONS:
        for pat in rules.get(section) or []:
            try:
                out.append((section, pat, re.compile(pat, re.I)))
            except re.error as exc:
                raise CheckError(f"[{section}] pattern {pat!r} does not compile: {exc}")
    return out


def hits_in_text(text, compiled, label):
    """Every hit in a text: (label, line number, kind, what matched, the
    line, shown short)."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, _, rx in compiled:
            m = rx.search(line)
            if m:
                shown = line.strip()
                if len(shown) > SHOWN:
                    shown = shown[:SHOWN] + "..."
                out.append((label, n, kind, m.group(0), shown))
    return out


def looks_binary(data):
    return b"\0" in data[:NUL_PROBE]


def binary_by_name(name, suffixes):
    low = name.lower()
    return any(low.endswith(s) for s in suffixes)


# --- what to read -----------------------------------------------------------------------

def git(cwd, *args, check=True, binary=False):
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=not binary, timeout=120,
                              env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CheckError(f"git {' '.join(args)} in {cwd}: {exc}")
    if check and proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace") if binary else proc.stderr
        raise CheckError(f"git {' '.join(args)} in {cwd} failed: {err.strip() or proc.returncode}")
    return proc


def is_git_tree(cwd):
    return git(cwd, "rev-parse", "--is-inside-work-tree", check=False).stdout.strip() == "true"


def range_ends(spec):
    a, sep, b = spec.partition("..")
    if not sep or not a or not b or ".." in b:
        raise CheckError(f"--range takes A..B, two commits, not {spec!r}")
    return a, b


def changed_in_range(cwd, a, b):
    """(paths at b's version, [(sha, message)]) for a range."""
    out = git(cwd, "diff", "--name-only", "--diff-filter=ACMRT", "-z", a, b).stdout
    paths = [p for p in out.split("\0") if p]
    log = git(cwd, "log", "--format=%H%x00%B%x1e", f"{a}..{b}").stdout
    messages = []
    for rec in log.split("\x1e"):
        if not rec.strip():
            continue
        sha, _, body = rec.lstrip("\n").partition("\0")
        messages.append((sha.strip(), body))
    return paths, messages


def changed_in_tree(cwd):
    """The paths a dirty tree changed (staged or not, and untracked),
    deleted ones aside, relative to cwd's top."""
    out = git(cwd, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    paths = []
    items = out.split("\0")
    i = 0
    while i < len(items):
        item = items[i]
        i += 1
        if not item:
            continue
        code, path = item[:2], item[3:]
        if "R" in code or "C" in code:
            # A rename or copy carries the old name next; the new one
            # is what is there.
            i += 1
        if "D" in code:
            # Deleted in the index or in the working tree: nothing to read.
            continue
        paths.append(path)
    return paths


def whole_tree(cwd, in_git):
    if in_git:
        out = git(cwd, "ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout
        return sorted(p for p in out.split("\0") if p)
    paths = []
    for root, dirs, files in os.walk(cwd):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for f in sorted(files):
            paths.append(os.path.relpath(os.path.join(root, f), cwd))
    return paths


def read_file(cwd, path, at=None):
    """The file's text, or None for a binary one (said under debug): at a
    commit through git, else from the tree."""
    if at is not None:
        proc = git(cwd, "show", f"{at}:{path}", check=False, binary=True)
        if proc.returncode != 0:
            why = proc.stderr.decode("utf-8", "replace").strip().splitlines()
            debug(f"{path} at {at}: not readable ({why[-1] if why else proc.returncode}); skipped")
            return None
        data = proc.stdout
    else:
        p = pathlib.Path(cwd) / path
        if not p.is_file():
            debug(f"{path}: not a file; skipped")
            return None
        try:
            data = p.read_bytes()
        except OSError as exc:
            debug(f"{path}: cannot be read ({exc}); skipped")
            return None
    if looks_binary(data):
        debug(f"{path}: binary (a NUL byte); skipped")
        return None
    return data.decode("utf-8", "replace")


def check(cwd, rules, scope_all=False, range_spec=None, words=()):
    """Run the check. Returns (hits, lines told): hits as hits_in_text
    gives them, told as the lines the check says about what it read."""
    cwd = str(pathlib.Path(cwd).resolve())
    compiled = compile_rules(rules)
    suffixes = rules.get("binary") or []
    told, hits, read = [], [], 0
    in_git = is_git_tree(cwd)
    top = cwd
    if in_git:
        top = git(cwd, "rev-parse", "--show-toplevel").stdout.strip() or cwd
    at = None
    if range_spec:
        if not in_git:
            raise CheckError(f"--range needs a git repo, and {cwd} is not in one")
        a, b = range_ends(range_spec)
        paths, messages = changed_in_range(top, a, b)
        at = b
        told.append(f"the files {range_spec} changed ({len(paths)}), at {b}'s version, and its {len(messages)} commit message(s)")
        for sha, body in messages:
            hits += hits_in_text(body, compiled, f"commit {sha[:12]}")
    elif scope_all or not in_git:
        paths = whole_tree(top, in_git)
        told.append(f"the whole tree, {len(paths)} file(s)" + ("" if in_git else f" (not a git repo, so the changed set cannot be told: {cwd})"))
    else:
        paths = changed_in_tree(top)
        if paths:
            told.append(f"the files the working tree changed ({len(paths)}), as they are")
        else:
            told.append("nothing changed in the working tree, so no file was read (--all reads the whole tree)")
    for path in paths:
        if binary_by_name(path, suffixes):
            debug(f"{path}: binary by name; skipped")
            continue
        text = read_file(top, path, at)
        if text is None:
            continue
        read += 1
        debug(f"read {path}" + (f" at {at}" if at else ""))
        hits += hits_in_text(text, compiled, path)
    for w in words:
        try:
            text = pathlib.Path(w).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise CheckError(f"--words {w}: {exc}")
        read += 1
        debug(f"read the words in {w}")
        hits += hits_in_text(text, compiled, str(w))
    told.append(f"{read} file(s) read")
    return hits, told


def render(hits):
    return [f"{label}:{n}: {kind}: {what!r} in: {shown}" for label, n, kind, what, shown in hits]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_letterhead.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("directory", nargs="?", default=".", help="the tree to check (default: here)")
    ap.add_argument("--all", action="store_true", help="the whole tree, not only what changed")
    ap.add_argument("--range", dest="range_spec", help="A..B: the files the range changed and its commit messages")
    ap.add_argument("--words", action="append", default=[], help="a text checked as it is (repeatable)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--rules", help="share/letterhead.toml, or a file of its shape")
    g.add_argument("--rules-json", help="the rules as one JSON object (how they travel to a host)")
    ap.add_argument("--forbidden", action="append", default=[],
                    help="a forbidden.txt: its non-blank, non-comment lines as fixed strings (repeatable)")
    a = ap.parse_args(argv)
    try:
        if a.rules_json:
            try:
                rules = json.loads(a.rules_json)
            except json.JSONDecodeError as exc:
                raise CheckError(f"--rules-json is not JSON: {exc}")
        elif a.rules:
            rules = load_rules_toml(a.rules)
        else:
            here = pathlib.Path(__file__).resolve().parent.parent / "share" / "letterhead.toml"
            if not here.is_file():
                raise CheckError("no rules: give --rules FILE or --rules-json JSON (the install's share/letterhead.toml)")
            rules = load_rules_toml(here)
        rules.setdefault("forbidden", [])
        for f in a.forbidden:
            try:
                rules["forbidden"] += forbidden_lines(pathlib.Path(f).read_text(encoding="utf-8", errors="replace"))
            except OSError as exc:
                raise CheckError(f"--forbidden {f}: {exc}")
        hits, told = check(a.directory, rules, a.all, a.range_spec, a.words)
    except CheckError as exc:
        print(f"[office] error: letterhead: {exc}", file=sys.stderr)
        return 2
    for line in render(hits):
        print(line)
    for line in told:
        print(f"[office] letterhead: {line}", file=sys.stderr)
    files = len({h[0] for h in hits})
    if hits:
        print(f"[office] letterhead: {len(hits)} hit(s) in {files} file(s); nothing with a hit leaves the office", file=sys.stderr)
        return 1
    print("[office] letterhead: clean", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
