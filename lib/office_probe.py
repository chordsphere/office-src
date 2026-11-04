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

What run hands back is masked (0.38.0): a credential written into a URL,
`scheme://user:SECRET@host`, reaches the screen, the result's block (and
so the clipboard) and the result's words as `scheme://user:xxx@host`, and
so does a GitHub token in one of its own shapes (ghp_, gho_, ghu_, ghs_,
ghr_, github_pat_), as `ghp_xxx`; the words say how many were masked. A
probe printed `git remote -v` in a project whose remote URL held a
personal access token, and it went to chat, the clipboard and the
probe's record (2026-10-28). The mask is defense in depth, not a promise:
a probe should not print a remote URL with a credential in it in the first
place (git remote -v, git config --get remote.NAME.url), and a token of
any other shape printed bare is not caught. The block's stderr is masked
on the screen too (0.43.0: a git fetch against a remote with a credential
in it prints the URL there), shown and never kept; the fallback's
probe-output/ files and the block's own closing clipboard step (bale
clipboard, run inside the block) are not masked.

A block that calls `office-on PROJECT ...` (0.34.0) spans the office and
the projects it names: it runs in the office root, under the folder's
session open in the office or in one of those projects, and each
office-on call runs its command where that project lives. The M10
walkthrough's planner sitting (2026-10-27) needed the work office's
folder and the hosted repo in one probe, and ran six by hand. A reach is
read from a call alone (0.45.0): the bare word office-on where a command
begins, never its name in a string, a comment, a heredoc or an echo's
text (calls_of); and the call's words reach the project's shell as the
block's shell gave them, each quoted (run_on), so `office-on PROJECT bash
-c SCRIPT` runs SCRIPT whole there.

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
# The run line (0.44.0): one more comment line a sitting may write in the
# block's purpose header, pinned to the byte (doctrine section 4,
# continued), so one copy of the block runs it with bare `office probe`:
#   # office: probe FOLDER [--project NAME] [--sid SID]
# FOLDER as office probe takes it (its name, a unique part, or a folder's
# number), the two flags as office probe's own. It is a comment, shown with
# the header and never run.
RUN_LINE_PREFIX = "# office: probe "
RUN_LINE_RE = oh.LazyPattern(r"^# office: probe (\S+)((?: --(?:project|sid) \S+)*)$")
RUN_FLAG_RE = oh.LazyPattern(r" --(project|sid) (\S+)")
# The helper a spanning block calls (0.34.0): `office-on PROJECT COMMAND...`
# names a project the block reaches. A reach is read from a call alone
# (0.45.0, calls_of): the bare word `office-on` where a command begins,
# never from the name inside a string, a comment, a heredoc's body or an
# echo's text (a regex over the text counted those, so `echo "office-on
# alpha"` made a block a spanning one, 2026-11-03). The project is the
# bare word after it, in this shape; a variable there names nothing.
ON_HELPER = "office-on"
ON_NAME_RE = oh.LazyPattern(r"[A-Za-z0-9_][A-Za-z0-9_-]*")
# The words after which the next word still begins a command, as bash
# reads them: a reserved word that takes a command, or `NAME=value` set
# for the one command (`if office-on alpha test -e x; then`,
# `LC_ALL=C office-on alpha git log`).
COMMAND_WORDS = frozenset(("if", "then", "elif", "else", "while", "until", "do", "!", "time"))
ASSIGNMENT_RE = oh.LazyPattern(r"[A-Za-z_][A-Za-z0-9_]*\+?=")
# The exit code office-on gives when the project cannot be reached at all
# (a host that stopped answering), told apart from the command's own.
EXIT_ON_UNREACHED = 97
# The mask (0.38.0). A credential in a URL: the scheme, `://`, the user
# part (kept: it says whose credential it was; it may hold %40 and stops
# at the first colon), then the secret, which runs to the last `@` before
# the authority ends (whitespace, / ? #, a quote or a bracket). The last
# `@`, not the first, because that is where a URL's host starts
# (urllib.parse reads it so) and a password with a bare `@` in it is
# still hidden whole. A URL with no password (https://user@host,
# ssh://git@host:22/x) and a port (https://host:8443/x) do not match.
MASK = "xxx"
URL_CREDENTIAL_RE = oh.LazyPattern(
    r"(?P<head>\b[A-Za-z][A-Za-z0-9+.-]*://[^\s/?#@:\"'<>`\[\]]*:)(?P<secret>[^\s/?#\"'<>`\[\]]+)(?=@)")
# A GitHub token in one of its own shapes, bare or as a URL's user part
# (https://ghp_...@github.com): the prefix kept, the rest masked. The
# lengths are the shortest GitHub issues (36 after ghp_ and its kin, 82
# after github_pat_), less some margin, so a short name that merely starts
# so is left alone.
GITHUB_TOKEN_RE = oh.LazyPattern(
    r"(?<![A-Za-z0-9_])(?P<head>gh[pousr]_|github_pat_)(?P<secret>[A-Za-z0-9_]{30,})(?![A-Za-z0-9_])")


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


def run_line(header):
    """(line, {folder, project, sid}) from the block's purpose header: the
    first `# office: probe FOLDER [--project NAME] [--sid SID]` line
    (0.44.0), its parts as written (project and sid None when left out);
    (None, None) when the header carries none. Raises ProbeError, naming
    the line, for one that begins like it and does not read, or names a
    flag twice, so the occupant is told rather than the line passed over."""
    for line in header:
        if not line.startswith(RUN_LINE_PREFIX.rstrip()):
            continue
        text = line.rstrip()
        m = RUN_LINE_RE.match(text)
        if not m:
            raise ProbeError([f"the block's run line does not read: {text!r} is not `{RUN_LINE_PREFIX}FOLDER "
                              "[--project NAME] [--sid SID]`; nothing ran (office probe FOLDER runs it by hand)"])
        got = {"folder": m.group(1), "project": None, "sid": None}
        for flag, value in RUN_FLAG_RE.findall(m.group(2)):
            if got[flag] is not None:
                raise ProbeError([f"the block's run line names --{flag} twice: {text!r}; nothing ran"])
            got[flag] = value
        return text, got
    return None, None


def calls_of(text):
    """The `office-on` calls in a block's text (0.45.0), in order, one
    (line number, project) pair per call: the project is the bare word
    after the helper's name when it is one (ON_NAME_RE), None when it is
    not (a variable, a quoted word, no word at all). A call is the bare
    word `office-on` where a command begins: at a line's start, or after
    `;`, `|`, `||`, `&&`, `&`, `(`, `{`, `$(` or a backtick, or after a
    word that takes a command (COMMAND_WORDS) or a `NAME=value` word; read
    through bash's quoting (single and double quotes, a backslash, a
    line continuation), its comments (`#` at a word's start to the line's
    end) and its heredocs (`<<WORD` to the line that is WORD; `<<-` strips
    tabs), so the name inside a string, a comment, a heredoc's body or an
    echo's text is text, not a call, and `\\office-on` or `'office-on'` is
    not the bare name. A plain scan, not a shell: it reads enough of bash
    to tell a call from text (a case pattern's `)` begins a command too),
    and a shape it does not read (a command inside `${...}`, an alias)
    reads as text."""
    calls = []
    # The contexts open at this point in the text: a command list (where
    # a word may begin a command) or a double-quoted string, innermost
    # last; a string appends to the word of the command list under it.
    stack = [_command_list(None)]
    heredocs = []  # (delimiter, strips tabs), for the next line's end
    i, n, line_no = 0, len(text), 1

    def end_word(cmd):
        """A word of the command list ends here: what it was, in bash's
        reading of the words before it, decides what the next one is."""
        if not cmd["in_word"]:
            return
        word, bare = "".join(cmd["word"]), cmd["bare"]
        cmd["word"], cmd["in_word"], cmd["bare"] = [], False, True
        if cmd["heredoc"] is not None:
            heredocs.append((word, cmd["heredoc"]))
            cmd["heredoc"] = None
        elif cmd["after_on"]:
            calls.append((cmd["on_line"], word if bare and ON_NAME_RE.fullmatch(word) else None))
            cmd["after_on"] = False
        elif cmd["at_start"]:
            if bare and word == ON_HELPER:
                cmd["after_on"], cmd["on_line"], cmd["at_start"] = True, line_no, False
            elif not ((bare and word in COMMAND_WORDS) or ASSIGNMENT_RE.match(word)):
                # A quoted value is still an assignment (`X="a b" office-on
                # alpha ls`); a quoted reserved word is not one.
                cmd["at_start"] = False

    def separator(cmd):
        """`;`, `|`, `&` or a line's end: the command ends, a new one may
        begin; a call that reached the end with no project named one."""
        end_word(cmd)
        if cmd["after_on"]:
            calls.append((cmd["on_line"], None))
            cmd["after_on"] = False
        cmd["at_start"] = True

    while i < n:
        ctx, c = stack[-1], text[i]
        if ctx["kind"] == "dq":
            cmd = ctx["cmd"]
            if c == "\\" and i + 1 < n:
                cmd["word"].append(text[i + 1])
                line_no += text[i + 1] == "\n"
                i += 2
            elif c == '"':
                stack.pop()
                i += 1
            elif c == "$" and text[i + 1:i + 2] == "(":
                stack.append(_command_list(")"))
                i += 2
            elif c == "`":
                stack.append(_command_list("`"))
                i += 1
            else:
                cmd["word"].append(c)
                line_no += c == "\n"
                i += 1
            continue
        cmd = ctx
        if c in " \t":
            end_word(cmd)
            i += 1
        elif c == "\n":
            separator(cmd)
            i += 1
            line_no += 1
            while heredocs:
                delimiter, strips_tabs = heredocs.pop(0)
                while i < n:
                    end = text.find("\n", i)
                    end = n if end < 0 else end
                    line = text[i:end]
                    i = end + 1
                    line_no += 1
                    if (line.lstrip("\t") if strips_tabs else line) == delimiter:
                        break
        elif c == "\\":
            if i + 1 < n:
                if text[i + 1] == "\n":
                    line_no += 1  # a line continuation: the word goes on
                else:
                    cmd["word"].append(text[i + 1])
                    cmd["in_word"], cmd["bare"] = True, False
            i += 2
        elif c == "'":
            close = text.find("'", i + 1)
            close = n if close < 0 else close
            cmd["word"].extend(text[i + 1:close])
            cmd["in_word"], cmd["bare"] = True, False
            line_no += text.count("\n", i, close)
            i = close + 1
        elif c == '"':
            cmd["in_word"], cmd["bare"] = True, False
            stack.append({"kind": "dq", "cmd": cmd})
            i += 1
        elif c == "$" and text[i + 1:i + 2] == "(":
            cmd["in_word"], cmd["bare"] = True, False
            stack.append(_command_list(")"))
            i += 2
        elif c == "`":
            if cmd["closer"] == "`":
                end_word(cmd)
                stack.pop()
            else:
                cmd["in_word"], cmd["bare"] = True, False
                stack.append(_command_list("`"))
            i += 1
        elif c == "#" and not cmd["in_word"]:
            end = text.find("\n", i)
            i = n if end < 0 else end
        elif c in ";|&":
            separator(cmd)
            i += 1
        elif c == "(":
            end_word(cmd)
            stack.append(_command_list(")"))
            i += 1
        elif c == ")":
            end_word(cmd)
            if cmd["closer"] == ")" and len(stack) > 1:
                stack.pop()
                if stack[-1]["kind"] == "cmd" and not stack[-1]["in_word"]:
                    # A subshell stood where a command begins; inside a word
                    # (`x=$(...)`) the word's end decides.
                    stack[-1]["at_start"] = False
            else:
                # One that closes nothing opened here ends a case pattern
                # (`a) office-on alpha ls;;`), and a command begins.
                cmd["at_start"] = True
            i += 1
        elif c in "{}" and not cmd["in_word"] and (i + 1 >= n or text[i + 1] in " \t\n;"):
            # The reserved words: `{` opens a group where a command begins,
            # `}` closes one.
            cmd["at_start"] = c == "{"
            i += 1
        elif c == "<" and text[i:i + 3] != "<<<" and text[i:i + 2] == "<<":
            end_word(cmd)
            strips_tabs = text[i + 2:i + 3] == "-"
            cmd["heredoc"] = strips_tabs
            i += 3 if strips_tabs else 2
        elif c in "<>":
            end_word(cmd)
            i += 1
            while i < n and text[i] in "<>&":
                i += 1
        else:
            cmd["word"].append(c)
            cmd["in_word"] = True
            i += 1
    for ctx in reversed(stack):
        if ctx["kind"] == "cmd":
            separator(ctx)
    return calls


def _command_list(closer):
    """A command list the reader is inside: what closes it (`)`, a
    backtick, or None for the block itself), whether the next word begins
    a command, the word being read and whether it is bare so far, whether
    the last word was office-on (the next names the project), and whether
    the next word is a heredoc's delimiter."""
    return {"kind": "cmd", "closer": closer, "at_start": True, "word": [], "in_word": False, "bare": True,
            "after_on": False, "on_line": 0, "heredoc": None}


def reaches_of(lines):
    """The projects a block reaches with `office-on PROJECT ...` (0.34.0),
    in order of first call, read from its calls alone (calls_of, 0.45.0):
    a header may say what the helper is for, and a string, a heredoc or
    an echo may hold its name, without naming a project."""
    out = []
    for _, name in calls_of("\n".join(lines)):
        if name is not None and name not in out:
            out.append(name)
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
    """The one line that says what came back, and, when the mask replaced
    anything (result["masked"], from mask_text, on stdout; and since 0.43.0
    result["masked_stderr"], on stderr), how many it replaced, saying which
    stream when stderr's mask replaced any."""
    out, err = result.get("masked"), result.get("masked_stderr")
    if not any((err or {}).values()):
        return _came_back_words(result) + masked_words(out)
    return _came_back_words(result) + stream_masks_words(out, err)


def _came_back_words(result):
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


# --- the mask (0.38.0) ---------------------------------------------------------------------

def no_masks():
    """The mask's counts when it has replaced nothing: credentials in URLs,
    and bare GitHub tokens."""
    return {"url": 0, "token": 0}


def mask_text(text):
    """text with every credential in a URL (`scheme://user:SECRET@host`,
    the user part kept) and every GitHub token in one of its own shapes
    replaced by xxx, and the counts of each it replaced: (text, {"url": N,
    "token": M}). A secret that already reads xxx is left and not counted.
    Neither pattern crosses a line end, so a line is masked, never split,
    joined or dropped, and the block's line count and its trailer are what
    the probe printed. The URL form is masked first, so a token that is a
    URL's password counts once, as the URL's.

    Defense in depth, not a promise: a probe should never print a remote
    URL with a credential in it (git remote -v, git config --get
    remote.NAME.url), and a token of any other shape printed bare, outside
    a URL, is not caught."""
    counts = no_masks()

    def replace(kind):
        def one(m):
            if m.group("secret") == MASK:
                return m.group(0)
            counts[kind] += 1
            return m.group("head") + MASK
        return one

    text = URL_CREDENTIAL_RE.sub(replace("url"), text)
    text = GITHUB_TOKEN_RE.sub(replace("token"), text)
    return text, counts


def add_masks(total, more):
    """Add the counts more to total, in place, and return total."""
    for kind, n in more.items():
        total[kind] = total.get(kind, 0) + n
    return total


def mask_parts(masked):
    """What a mask replaced, as phrases: ['1 credential in a URL', '2
    GitHub tokens'], [] for nothing."""
    masked = masked or {}
    urls, tokens = masked.get("url", 0), masked.get("token", 0)
    parts = []
    if urls:
        parts.append(f"{urls} credential in a URL" if urls == 1 else f"{urls} credentials in URLs")
    if tokens:
        parts.append(f"{tokens} GitHub token" if tokens == 1 else f"{tokens} GitHub tokens")
    return parts


def stream_masks_words(out, err):
    """The end of the count's line when stderr's mask replaced anything
    (0.43.0), naming the stream of each: '; 1 credential in a URL on stdout
    and 1 GitHub token on stderr were masked (xxx stands for each)'."""
    said = [f"{' and '.join(mask_parts(m))} on {name}" for name, m in (("stdout", out), ("stderr", err))
            if mask_parts(m)]
    total = sum(sum((m or {}).values()) for m in (out, err))
    one = total == 1
    return f"; {' and '.join(said)} {'was' if one else 'were'} masked ({MASK} stands for {'it' if one else 'each'})"


def masked_words(masked):
    """The end of the count's line when the mask replaced anything, in
    plain words ('; 1 credential in a URL was masked (xxx stands for
    it)'); '' when it replaced nothing, or there are no counts."""
    masked = masked or {}
    urls, tokens = masked.get("url", 0), masked.get("token", 0)
    parts = []
    if urls:
        parts.append(f"{urls} credential in a URL" if urls == 1 else f"{urls} credentials in URLs")
    if tokens:
        parts.append(f"{tokens} GitHub token" if tokens == 1 else f"{tokens} GitHub tokens")
    if not parts:
        return ""
    one = urls + tokens == 1
    return f"; {' and '.join(parts)} {'was' if one else 'were'} masked ({MASK} stands for {'it' if one else 'each'})"


class MaskedScreen:
    """A writer for office_host.run_probe's screen that masks what the
    block prints before it reaches the real one (the terminal's stdout,
    as bytes). run_probe writes each chunk of the block's stdout as it
    comes, 4096 bytes at a time, and flushes after each: this holds a
    partial line back until its line end arrives, so a credential split
    between two reads is still caught, and writes each whole line through
    mask_text. A line with no line end yet is shown when its end arrives
    or the block ends (close). Bytes that are not UTF-8 pass through as
    they came. counts adds up what was masked on the screen."""

    def __init__(self, screen):
        self.screen = screen
        self.held = bytearray()
        self.counts = no_masks()

    def write(self, chunk):
        chunk = bytes(chunk)
        end = chunk.rfind(b"\n")
        if end < 0:
            self.held += chunk
            return len(chunk)
        lines = bytes(self.held) + chunk[:end + 1]
        self.held = bytearray(chunk[end + 1:])
        self._show(lines)
        return len(chunk)

    def flush(self):
        """Flush the real screen. A partial line stays held: showing it
        now could show half of a credential the next read completes."""
        self.screen.flush()

    def close(self):
        """Show the partial line held back, masked, and flush: the block
        has ended. The real screen is not closed."""
        if self.held:
            held, self.held = bytes(self.held), bytearray()
            self._show(held)
        self.screen.flush()

    def _show(self, data):
        text, counts = mask_text(data.decode("utf-8", "surrogateescape"))
        add_masks(self.counts, counts)
        self.screen.write(text.encode("utf-8", "surrogateescape"))


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


def newest_first(sittings, recorded):
    """The sittings, the one the folder recorded last first (0.43.0): when
    two are open on one folder the newer is the successor, and an older one
    is probably over (the gaps of 2026-10-28, A13), so a probe asked which
    sitting it is for offers the newest first."""
    return sorted(sittings, key=lambda s: recorded.index(s) if s in recorded else -1, reverse=True)


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


def soft_sid(sid, pool, name, words):
    """The run line's --sid (0.44.0) when it is one of the sessions the
    probe could be for, else None, said in one line: the office then reads
    the session as it does without one."""
    if sid is None or sid in pool:
        return sid
    log(f"the block's run line names --sid {sid}, which is not a session {name} records that is open {words} "
        f"(open and recorded: {', '.join(pool) or 'none'}); the session is read as without it")
    return None


def plan(office_root, folder_rel, project, block_file, sid=None, rd=None, sid_soft=False):
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
        return plan_spanning(office_root, folder_rel, project, block, sid, rd, sid_soft)
    place, label, words = where_it_runs(office_root, project)
    md = pathlib.Path(office_root) / folder_rel / "folder.md"
    folder = oh.parse_folder(md.read_text(encoding="utf-8"))
    recorded = list(dict.fromkeys(folder["sids"]))
    name = pathlib.Path(folder_rel).name
    # The sessions open where it runs, and whether probe-output/ is there
    # already: on a host, both in one connection (the reach).
    there_already = False
    read_only_here = set()
    try:
        if label == OFFICE:
            registry = ob.office_registry(office_root)
            opened = rd.open_sessions(registry) if registry is not None else []
            open_here = [s for s, _ in opened]
            read_only_here = {s for s, ro in opened if ro}
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
    # A probe of the office for a folder with several sittings open there
    # offers the newest first (0.43.0), the other sessions as before.
    candidates = ([s for s in candidates if s not in read_only_here]
                  + newest_first([s for s in candidates if s in read_only_here], recorded))
    # The folder's read-only sittings open in the office (0.33.0), for a
    # probe of a project: read only when the folder records a session that
    # is not open there, so a folder whose sessions are all the project's
    # costs no read of the office's registry.
    sittings = []
    if label != OFFICE and any(s not in open_here for s in recorded):
        try:
            sittings = newest_first(open_sittings(office_root, [s for s in recorded if s not in open_here], rd),
                                    recorded)
        except ob.BaleError as exc:
            raise ProbeError([f"the office: its open sittings could not be read, so the office cannot say whether "
                              f"this probe is for one of {name}'s: {exc}; nothing ran"])
    pool = candidates + [s for s in sittings if s not in candidates]
    if sid_soft:
        sid = soft_sid(sid, pool, name, words)
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


def plan_spanning(office_root, folder_rel, project, block, sid, rd, sid_soft=False):
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
    sittings = newest_first([s for s, read_only in open_office if read_only and s in recorded], recorded)
    candidates = [s for s in recorded if s in open_in_projects or (s in office_sids and s not in sittings)]
    pool = candidates + [s for s in sittings if s not in candidates]
    if sid_soft:
        sid = soft_sid(sid, pool, name, f"in the office or in {', '.join(block['reaches'])}")
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
    """What `office-on PROJECT COMMAND...` does (0.34.0): the words, each
    quoted for a shell (shlex.join, 0.45.0) as one line, run where the
    project lives through office_host (in its directory on this machine;
    through its shell, in its path, on a host), stdin closed. The words
    reach the project's shell as the block's shell gave them: `bash -c
    SCRIPT` runs SCRIPT whole, a word with a space in it stays one word,
    and a quote or a `$` in a word arrives as it was left (before 0.45.0
    the words were joined with spaces and the project's shell split them
    again, so `bash -c 'echo one; echo two'` ran `bash -c echo one` and
    then `echo two`, 2026-11-03). Returns (exit code, stdout, stderr); a
    project the plan does not reach, or that cannot be reached, is a
    ProbeError."""
    import shlex
    import office_host as ohost
    reaches = plan_data.get("reaches") or {}
    if project not in reaches:
        raise ProbeError([f"{ON_HELPER} {project}: not a project this probe reaches (its block names: "
                          f"{', '.join(reaches) or 'none'}); a name is read from the block before it runs, so "
                          "name each project literally, never through a variable"])
    if not any(word.strip() for word in words):
        raise ProbeError([f"{ON_HELPER} {project}: no command given"])
    command = shlex.join(words)
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


def run(plan_data, block_file, tray_root, screen=None, plan_file=None, err_screen=None):
    """Run the block where the plan says, then read what came back and
    carry the fallback's directory. Returns the result: code, stopped
    (the office's backstop stopped it), found, closed, block (lines),
    count, trailer, words (the count's line), masked (what the mask
    replaced: {"url": N, "token": M}), carried (the out tray path, or
    None), carry_problem. A block that spans (plan reaches, with
    plan_file) gets the office-on helper first on its PATH, written beside
    the plan for this run.

    Everything run hands back is masked (mask_text, 0.38.0): the block's
    stdout reaches screen (this terminal's stdout when None) through a
    MaskedScreen, line by line as it streams, and the text run_probe kept
    is masked the same way before the block is read out of it, so the
    result's block, which bin/office copies to the clipboard, holds no
    credential the mask knows. A spanning block's office-on output comes
    back on the same stream and is masked with it. The block's stderr
    reaches err_screen (this terminal's stderr when None) through a
    MaskedScreen of its own (0.43.0), shown and never kept; the count's
    line says what each stream's mask replaced. A fallback's probe-output/
    files are carried unread, and are not masked."""
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
    masked_screen = MaskedScreen(screen if screen is not None else sys.stdout.buffer)
    # The block's stderr through a mask of its own (0.43.0): a git fetch
    # against a remote with a credential in it prints the URL there. It is
    # shown, never kept or copied.
    masked_err = MaskedScreen(err_screen if err_screen is not None else sys.stderr.buffer)
    try:
        code, text, stopped = ohost.run_probe(place, block["text"], screen=masked_screen, env=env,
                                              err_screen=masked_err)
    except ohost.HostError as exc:
        raise ProbeError([f"{plan_data['project']}: {exc}; the block did not run to its end, and nothing was carried"])
    finally:
        # A last line with no line end is shown now, masked, however the
        # run ended.
        masked_screen.close()
        masked_err.close()
    text, masked = mask_text(text)
    if masked != masked_screen.counts:
        # The two masks read the same bytes, decoded two ways; a difference
        # is a bug to see, never to pass over.
        log(f"warning: the mask counted {masked} in the kept output but {masked_screen.counts} on the screen; "
            "the block handed back is the kept output's, masked")
    out = dict(read_output(text), masked=masked, masked_stderr=masked_err.counts)
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
    q = sub.add_parser("run-line", help="the block's run line (0.44.0): line, folder, project and sid, KEY<tab>VALUE; "
                                        "nothing when it carries none")
    q.add_argument("block")
    q = sub.add_parser("has-block", help="exit 0 when the text holds a PROBE BEGIN line, 3 when it holds none")
    q.add_argument("block")
    q = sub.add_parser("on", help="office-on PROJECT COMMAND...: one command where the project lives (0.34.0); "
                                  "its line is `on --plan FILE -- PROJECT COMMAND...`, read by on_main, not here")
    q = sub.add_parser("plan", help="the block read, where it runs and its session: one JSON line (exit 5: several "
                                    "sessions open, printed one per line)")
    q.add_argument("office"); q.add_argument("folder", help="desk/NAME")
    q.add_argument("--project", required=True, help="a project the office scopes, or office")
    q.add_argument("--block", required=True); q.add_argument("--sid")
    q.add_argument("--sid-soft", action="store_true", help="--sid came from the block's run line: one that is not "
                                                           "open is said and read past (0.44.0)")
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

        if a.cmd == "run-line":
            line, got = run_line(read_block(pathlib.Path(a.block).read_text(encoding="utf-8", errors="replace"))["header"])
            if line is not None:
                print(f"line\t{line}")
                for key in ("folder", "project", "sid"):
                    print(f"{key}\t{got[key] or ''}")
            return 0
        if a.cmd == "has-block":
            text = pathlib.Path(a.block).read_text(encoding="utf-8", errors="replace")
            return 0 if BEGIN_WORD in text else 3
        if a.cmd == "plan":
            try:
                print(json.dumps(plan(a.office, a.folder, a.project, a.block, a.sid, sid_soft=a.sid_soft)))
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
