#!/usr/bin/env python3
"""The letterhead check: what leaves the office for an audience is read first.

Doctrine section 2 names the letterhead as the guard on what leaves the
office. This module is that guard made mechanical: it reads a set of
text files and names every line that holds something the letterhead
refuses, as `file:line: what`. The list it refuses is share/letterhead.toml
(names of models, vendors and products; tell-tale phrasing an assistant
writes; bale's own marks) plus, when the office has letterhead/forbidden.txt,
each non-blank, non-comment line of it as a fixed string.

In an office that has a letterhead (0.25.0) three characters are refused
as well, by default, with no line in the office needed: the em dash
(U+2014), the en dash (U+2013) and the ellipsis (U+2026), each named by
its name in a refusal. The office's forbidden list lifts one with a line
`lift: em dash`, and every check that reads a lift says so. --letterhead
DIR is how the office hands its letterhead over; without it (a tree
checked outside any office) the characters are not refused.

A repository's own pull-request template is not the occupant's writing:
when words are checked in a git repo, each line of the words that is a
line of one of the repo's pull-request templates, as the repo holds it
(at HEAD, or --template-rev), is not held to the phrasing rule or to the
three characters (0.26.0). Names, bale's marks and the forbidden list
still read it, and a template line that was changed is an ordinary line. Which files are templates is read from the repo, by the
places git hosts look for one (PR_TEMPLATE_PLACES). A checklist line is
the template's whatever its box holds (0.32.0): `- [x]`, `- [X]` and
`- [ ]` read as one (template_key), and words added after the box make
it a changed line.

What it reads, in order of what it was told:

  --range A..B   the files the range changed, at B's version, and the
                 range's commit messages
  (a dirty tree) the files the working tree changed, as they are
  --all          the whole tree (git's tracked and untracked files,
                 or every file when the directory is not a git repo,
                 which the check says)
  --words FILE   a text checked as it is (a delivery's words), any
                 number of times
  --words-json   [[label, text], ...]: words that travel as one argument
                 (the check on a host reads no file of this machine)
  --files-only   with --range, the files alone, not the commit messages
                 (office land's review: bale's own messages never travel)
  --never PATH   a path never read, nor anything under it (repeatable;
                 bale's names, which a delivery never carries)

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
import os
import pathlib
import re
import sys

RULE_SECTIONS = ("names", "phrasing", "marks")
# What a line of a repository's own pull-request template, as the repo
# holds it, is not held to: the phrasing rule (0.25.0) and the three
# characters (0.26.0, the exception to session 3's decision 3), since its
# words are the repository's and a template the occupant cannot change
# would refuse every delivery that fills it.
TEMPLATE_EXEMPT_KINDS = ("phrasing", "character")

# The places git hosts look for a repository's pull-request template
# (GitHub, GitLab, Azure DevOps), as lower-case paths: a file whose
# directory and name match one of the single-file shapes, or any .md or
# .txt file directly inside one of the directories.
PR_TEMPLATE_DIRS = ("", ".github/", "docs/", ".azuredevops/", ".vsts/")
PR_TEMPLATE_NAMES = ("pull_request_template", "pull_request_template.md", "pull_request_template.txt")
PR_TEMPLATE_FOLDERS = tuple(f"{d}pull_request_template/" for d in PR_TEMPLATE_DIRS) + \
    tuple(f"{d}pull_request_template/branches/" for d in (".azuredevops/", ".vsts/")) + \
    (".gitlab/merge_request_templates/",)
LIFT_RE = re.compile(r"^\s*lift\s*:\s*(?P<name>.*?)\s*$", re.I)
# A checklist line's box (0.32.0): a task-list item, `- [ ] ...` (or `*`,
# `+`, `1.`, `1)`), whose box is empty, ticked `x` or `X`. A template's
# checklist is ticked when the words fill it, so a line is compared with
# the template's with the box's state folded: `- [x] Docs` is the
# template's `- [ ] Docs`, and what follows the box must still match.
CHECKBOX_RE = re.compile(r"^(?P<lead>\s*(?:[-*+]|\d+[.)])\s+)\[[ xX]\](?=\s|$)")
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
    chars = data.get("characters") or {}
    if not isinstance(chars, dict) or not all(isinstance(k, str) and isinstance(v, str) and len(v) == 1
                                              for k, v in chars.items()):
        raise CheckError(f"{path}: [characters] is not a table of names, each one character")
    # The catalog, applied only by apply_letterhead: an office with a
    # letterhead refuses them; a tree checked outside one does not.
    rules["character_catalog"] = [[name, char] for name, char in chars.items()]
    rules["characters"] = []
    rules["lifted"] = []
    return rules


def forbidden_lines(text):
    """The fixed strings letterhead/forbidden.txt holds: each non-blank
    line that does not start with # and is not a `lift:` line, stripped."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not LIFT_RE.match(line):
            out.append(line)
    return out


def lifts_in(text, catalog, where):
    """[(name, where:line)] for each `lift: NAME` line of a forbidden
    list. A name that is not one of the catalog's characters is the
    check's error, never a silent skip."""
    names = {n for n, _ in catalog}
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        m = LIFT_RE.match(line)
        if not m or line.lstrip().startswith("#"):
            continue
        name = " ".join(m.group("name").lower().split())
        if name not in names:
            raise CheckError(f"{where}:{n}: a lift names one of the characters the letterhead refuses by default "
                             f"({', '.join(sorted(names))}), not {m.group('name')!r}")
        out.append((name, f"{where}:{n}"))
    return out


def apply_letterhead(rules, letterhead_dir, shown=None):
    """The rules as an office's letterhead makes them: when the directory
    exists, its forbidden.txt's fixed strings (when it has one) and the
    catalog's characters, less the ones it lifts. Returns the rules; their
    "letterhead" key names the directory (None when the office has none),
    and "lifted" the lifts, each [name, where]."""
    rules.setdefault("forbidden", [])
    catalog = rules.get("character_catalog") or []
    d = pathlib.Path(letterhead_dir)
    shown = shown or str(d)
    if not d.is_dir():
        rules["letterhead"] = None
        rules["no_letterhead"] = shown
        rules["characters"] = []
        rules["lifted"] = []
        return rules
    rules["letterhead"] = shown
    lifted = []
    forbidden = d / "forbidden.txt"
    if forbidden.is_file():
        try:
            text = forbidden.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise CheckError(f"{forbidden}: {exc}")
        rules["forbidden"] = list(rules["forbidden"]) + forbidden_lines(text)
        lifted = lifts_in(text, catalog, f"{shown}/forbidden.txt")
    gone = {name for name, _ in lifted}
    rules["characters"] = [[name, char] for name, char in catalog if name not in gone]
    rules["lifted"] = [[name, where] for name, where in lifted]
    return rules


def char_label(name, char):
    return f"the {name} (U+{ord(char):04X})"


def compile_rules(rules):
    """[(kind, pattern text, compiled)] in the order hits are reported:
    the office's forbidden strings first (the occupant's own words), then
    names, phrasing and marks. A pattern that does not compile is the
    check's error, never a silent skip."""
    out = []
    for text in rules.get("forbidden") or []:
        out.append(("forbidden", text, re.compile(re.escape(text), re.I)))
    for name, char in rules.get("characters") or []:
        out.append(("character", char_label(name, char), re.compile(re.escape(char))))
    for section in RULE_SECTIONS:
        for pat in rules.get(section) or []:
            try:
                out.append((section, pat, re.compile(pat, re.I)))
            except re.error as exc:
                raise CheckError(f"[{section}] pattern {pat!r} does not compile: {exc}")
    return out


def template_key(line):
    """A line as it is compared with a pull-request template's lines:
    right-stripped, and, when it is a checklist line, its box read as
    empty whatever it holds (0.32.0), so a ticked line is the template's
    unticked one. Nothing else is folded."""
    line = line.rstrip()
    return CHECKBOX_RE.sub(lambda m: m.group("lead") + "[ ]", line, count=1)


def hits_in_text(text, compiled, label, exempt=None):
    """Every hit in a text: (label, line number, kind, what matched, the
    line, shown short). A character's hit names the character, not the
    match. A line in exempt (a pull-request template's line, as the repo
    holds it, keyed by template_key) is not held to the phrasing rule or
    to the three characters (0.26.0): it is the repository's, not the
    occupant's, whatever its checklist box holds (0.32.0). Names, bale's
    marks and the forbidden list still read it."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        templated = exempt is not None and template_key(line) in exempt
        for kind, what, rx in compiled:
            if templated and kind in TEMPLATE_EXEMPT_KINDS:
                continue
            m = rx.search(line)
            if m:
                shown = line.strip()
                if len(shown) > SHOWN:
                    shown = shown[:SHOWN] + "..."
                out.append((label, n, kind, what if kind == "character" else m.group(0), shown))
    return out


def is_pr_template(path):
    """Whether a repo path is one of the places git hosts read a
    pull-request template from."""
    low = path.lower()
    if any(low == d + n for d in PR_TEMPLATE_DIRS for n in PR_TEMPLATE_NAMES):
        return True
    for folder in PR_TEMPLATE_FOLDERS:
        if low.startswith(folder) and "/" not in low[len(folder):] and low.endswith((".md", ".txt")):
            return True
    return False


def pr_template_lines(top, rev):
    """(lines, paths, rev): every non-blank line of the repo's pull-request
    templates at rev (HEAD when rev does not resolve), each as template_key
    keys it (right-stripped, a checklist box read as empty), the
    templates' paths and the rev read. (set(), [], rev) when the repo has
    none, or nothing resolves (said under debug)."""
    proc = git(top, "ls-tree", "-r", "-z", "--name-only", rev, check=False)
    if proc.returncode != 0 and rev != "HEAD":
        debug(f"{rev} does not resolve in {top}; the pull-request templates are read at HEAD")
        rev = "HEAD"
        proc = git(top, "ls-tree", "-r", "-z", "--name-only", rev, check=False)
    if proc.returncode != 0:
        debug(f"no pull-request template read: {rev} does not resolve in {top}")
        return set(), [], rev
    paths = sorted(p for p in proc.stdout.split("\0") if p and is_pr_template(p))
    lines = set()
    for path in paths:
        text = read_file(top, path, rev)
        if text is None:
            continue
        lines.update(template_key(l) for l in text.splitlines() if l.strip())
    return lines, paths, rev


def looks_binary(data):
    return b"\0" in data[:NUL_PROBE]


def binary_by_name(name, suffixes):
    low = name.lower()
    return any(low.endswith(s) for s in suffixes)


# --- what to read -----------------------------------------------------------------------

def git(cwd, *args, check=True, binary=False):
    import subprocess
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


def never_read(path, never):
    """Whether a path is one of the never-read paths, or under one."""
    return any(path == n or path.startswith(n.rstrip("/") + "/") for n in never)


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


def check(cwd, rules, scope_all=False, range_spec=None, words=(), files_only=False, never=(),
          words_text=(), template_rev=None):
    """Run the check. Returns (hits, lines told): hits as hits_in_text
    gives them, told as the lines the check says about what it read.
    words are files, words_text (label, text) pairs; both are words, and
    in a git repo the lines of its pull-request templates at template_rev
    (HEAD when not given) are not held to the phrasing rule or the three
    characters there."""
    cwd = str(pathlib.Path(cwd).resolve())
    compiled = compile_rules(rules)
    suffixes = rules.get("binary") or []
    told, hits, read = [], [], 0
    for name, where in rules.get("lifted") or []:
        told.append(f"the letterhead lifts the {name} ({where}), so it is not refused")
    if rules.get("no_letterhead"):
        told.append(f"no letterhead here ({rules['no_letterhead']}), so the em dash, the en dash and the ellipsis "
                    "are not refused (an office's letterhead arrives with its first project given an audience)")
    if rules.get("letterhead") and rules.get("characters"):
        labels = [char_label(n, c) for n, c in rules["characters"]]
        told.append("the letterhead refuses " + (", ".join(labels[:-1]) + " and " if len(labels) > 1 else "")
                    + labels[-1] + f" by default ({rules['letterhead']})")
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
        if files_only:
            told.append(f"the files {range_spec} changed ({len(paths)}), at {b}'s version (not its commit messages)")
        else:
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
    skipped = [p for p in paths if never_read(p, never)]
    if skipped:
        told.append(f"{len(skipped)} file(s) of bale's never read: " + ", ".join(skipped[:6])
                    + (" ..." if len(skipped) > 6 else ""))
    for path in paths:
        if never_read(path, never):
            continue
        if binary_by_name(path, suffixes):
            debug(f"{path}: binary by name; skipped")
            continue
        text = read_file(top, path, at)
        if text is None:
            continue
        read += 1
        debug(f"read {path}" + (f" at {at}" if at else ""))
        hits += hits_in_text(text, compiled, path)
    texts = []
    for w in words:
        try:
            texts.append((str(w), pathlib.Path(w).read_text(encoding="utf-8", errors="replace")))
        except OSError as exc:
            raise CheckError(f"--words {w}: {exc}")
    texts += [(str(label), str(text)) for label, text in words_text]
    exempt, templates, rev = set(), [], template_rev or "HEAD"
    if texts and in_git:
        exempt, templates, rev = pr_template_lines(top, rev)
    for label, text in texts:
        read += 1
        debug(f"read the words in {label}")
        hits += hits_in_text(text, compiled, label, exempt if templates else None)
        if templates:
            kept = sum(1 for l in text.splitlines() if l.strip() and template_key(l) in exempt)
            told.append(f"{label}: {kept} line(s) are the repository's pull-request template's as it holds them "
                        f"({', '.join(templates)} at {rev[:12] if len(rev) == 40 else rev}), and are not held to the phrasing "
                        "rule or the three characters")
    told.append(f"{read} file(s) read")
    return hits, told


def render(hits):
    return [f"{label}:{n}: {kind}: {what if kind == 'character' else repr(what)} in: {shown}"
            for label, n, kind, what, shown in hits]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_letterhead.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("directory", nargs="?", default=".", help="the tree to check (default: here)")
    ap.add_argument("--all", action="store_true", help="the whole tree, not only what changed")
    ap.add_argument("--range", dest="range_spec", help="A..B: the files the range changed and its commit messages")
    ap.add_argument("--words", action="append", default=[], help="a text checked as it is (repeatable)")
    ap.add_argument("--words-json", help="[[label, text], ...]: words that travel as one argument")
    ap.add_argument("--template-rev", help="where the repo's pull-request templates are read (default: HEAD)")
    ap.add_argument("--files-only", action="store_true", help="with --range, not the commit messages")
    ap.add_argument("--never", action="append", default=[], help="a path never read, nor anything under it")
    ap.add_argument("--letterhead", help="the office's letterhead directory: its forbidden list, and the characters "
                                         "it refuses by default, less what it lifts")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--rules", help="share/letterhead.toml, or a file of its shape")
    g.add_argument("--rules-json", help="the rules as one JSON object (how they travel to a host)")
    ap.add_argument("--forbidden", action="append", default=[],
                    help="a forbidden.txt: its non-blank, non-comment lines as fixed strings (repeatable)")
    a = ap.parse_args(argv)
    try:
        if a.rules_json:
            import json
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
        if a.letterhead:
            apply_letterhead(rules, a.letterhead)
        for f in a.forbidden:
            try:
                rules["forbidden"] += forbidden_lines(pathlib.Path(f).read_text(encoding="utf-8", errors="replace"))
            except OSError as exc:
                raise CheckError(f"--forbidden {f}: {exc}")
        words_text = []
        if a.words_json:
            import json
            try:
                words_text = [(str(l), str(t)) for l, t in json.loads(a.words_json)]
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise CheckError(f"--words-json is not [[label, text], ...]: {exc}")
        hits, told = check(a.directory, rules, a.all, a.range_spec, a.words, a.files_only, a.never,
                           words_text, a.template_rev)
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
