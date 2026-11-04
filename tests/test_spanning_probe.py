"""Tests for office-src 0.45.0: the spanning probe's two defects, reported
by the occupant on 2026-11-03.

1. A reach is read from a call alone. `office-on PROJECT` counts as a
   reach only where it is a command's first word (a line's start, or after
   `$(`, a backtick, `|`, `||`, `&&`, `;`, `(` or `{`), never inside a
   string, a comment, a heredoc's body or an echo's text, and never as
   part of another word. A block whose only mention of the helper is text
   is a plain block, run where the folder's lane says.
2. The words reach the project's shell as the block's shell gave them:
   run_on quotes each word, so `office-on PROJECT bash -c SCRIPT` runs
   SCRIPT whole where the project lives, a word with a space stays one
   word, and a quote or a `$` arrives as the occupant's shell left it; on
   a host the quoted line goes through the project's shell as before.

The suite makes no network call and runs no real ssh or bale: the host is
the fake ssh of tests/test_project_on_host.py, bale the fake of
tests/test_land.py, and the blocks name invented projects. Run with the
rest of the suite:

    tests/run.sh test_spanning_probe
"""

import json
import os
import pathlib
import subprocess
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_out_trip_to_host import HostedStartCase  # noqa: E402
from test_probe import ProbeCase  # noqa: E402
from test_project_on_host import HOST  # noqa: E402

import office_probe as op  # noqa: E402


def block_of(body, slug="fix-login"):
    """A probe block in the crafter's shape whose probe() body is the
    given lines, as written and unindented, so a heredoc's delimiter line
    is its own (tests/test_probe.py's probe_block echoes its lines; this
    one runs them): a shebang, a read-only purpose header, the body, the
    sentinels and the integrity trailer."""
    header = [f"# PROBE {slug}: what the block says, as its lines run.",
              "# Why: the session needs it; office-on PROJECT reaches a project when a line calls it.",
              "# Read-only: writes nothing anywhere; stdout is the only output.",
              "# Bound: probe() gets 10 seconds of wall clock."]
    out = ["#!/usr/bin/env bash", *header, "", "probe() {", *body, "}",
           'out="$(probe 2>&1)"', f'echo "=== PROBE BEGIN {slug} ==="', 'printf "%s\\n" "$out"',
           "printf -- '--- integrity: %s lines ---\\n' \"$(printf '%s\\n' \"$out\" | wc -l)\"",
           f'echo "=== PROBE END {slug} ==="']
    return "\n".join(out) + "\n"


# --- 1. a reach is a call ------------------------------------------------------------------------

class TestAReachIsACall(ProbeCase):
    """Item 1: the helper's name in text names no project; a call does."""

    def test_the_name_in_text_is_not_a_call(self):
        text = [
            'echo "office-on alpha"',                 # an echo's string
            "echo 'office-on beta'",                  # a single-quoted string
            "echo office-on gamma",                   # an echo's bare text: not the command's first word
            "# office-on delta",                      # a comment line
            "ls # office-on epsilon",                 # a comment after a command
            "cat <<EOF", "office-on zeta ls", "EOF",  # a heredoc's body
            "cat <<-'END'", "\toffice-on eta ls", "\tEND",
            "./office-on theta ls",                   # part of another word
            "my-office-on iota; office-on-x kappa",
            "'office-on' lambda ls",                  # a quoted first word is not the bare name
            "\\office-on mu ls",
            '"if" office-on omicron ls',                # a quoted reserved word takes no command
            "x=$(ls) echo office-on pi",               # an assignment prefix, then echo's text
            'echo "a', "office-on nu ls", 'b"',       # a string over several lines
            "echo one \\", "  office-on xi ls",       # a continued line: not a command's first word
        ]
        self.assertEqual(op.reaches_of(text), [])
        self.assertEqual(op.calls_of("\n".join(text)), [])
        b = op.read_block(block_of(text))
        self.assertEqual(b["reaches"], [])

    def test_a_call_is_read_where_a_command_begins(self):
        cases = {
            "office-on alpha ls": ["alpha"],
            "  office-on alpha ls": ["alpha"],
            "true && office-on alpha true": ["alpha"],
            "false || office-on alpha true": ["alpha"],
            "echo x; office-on alpha ls": ["alpha"],
            "office-on alpha ls | wc -l": ["alpha"],
            "ls | office-on alpha wc -l": ["alpha"],
            "( office-on alpha ls )": ["alpha"],
            "{ office-on alpha ls; }": ["alpha"],
            'head="$(office-on alpha git rev-parse HEAD)"': ["alpha"],
            "head=`office-on alpha git rev-parse HEAD`": ["alpha"],
            "echo \"$(office-on alpha ls) $(office-on beta ls)\"": ["alpha", "beta"],
            "diff <(office-on alpha ls) <(office-on beta ls)": ["alpha", "beta"],
            "if office-on alpha test -e x; then office-on beta ls; fi": ["alpha", "beta"],
            "LC_ALL=C office-on alpha git log -n 1": ["alpha"],
            'X="a b" office-on alpha ls': ["alpha"],
            "x=$(office-on alpha ls) office-on beta ls": ["alpha", "beta"],
            "(office-on alpha ls) && office-on beta ls": ["alpha", "beta"],
            "! office-on alpha test -e x": ["alpha"],
            "office-on alpha ls &\noffice-on beta ls": ["alpha", "beta"],
            "case $x in a) office-on alpha ls;; esac": ["alpha"],
            "cat <<EOF\noffice-on zeta ls\nEOF\noffice-on alpha ls": ["alpha"],
            "x=1; office-on a-b 'ls' ; office-on a-b 'ls'; office-on c_d ls\necho not-office-on z\n  # office-on z":
                ["a-b", "c_d"],
        }
        for text, want in cases.items():
            self.assertEqual(op.reaches_of(text.split("\n")), want, text)
        # The call's line is read with it; a call whose project is not a
        # bare name (a variable, a quoted word, nothing) names none.
        self.assertEqual(op.calls_of("ls\noffice-on alpha ls\nx=$(office-on beta ls)\n"), [(2, "alpha"), (3, "beta")])
        self.assertEqual(op.calls_of('office-on "$P" ls\noffice-on $P ls\noffice-on; ls\noffice-on'),
                         [(1, None), (2, None), (3, None), (4, None)])
        self.assertEqual(op.reaches_of(['office-on "$P" ls']), [])

    def test_a_block_that_only_echoes_the_name_runs_as_a_plain_block(self):
        self.block.write_text(block_of(['echo "office-on alpha"', "echo office-on alpha", 'echo "cwd: $(pwd -P)"']))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        # Where the lane says, alpha's repo, with no helper on the PATH.
        self.assertIn("lane names alpha", proc.stderr)
        self.assertIn(f"cwd: {os.path.realpath(self.proj)}", proc.stdout)
        self.assertIn("office-on alpha\noffice-on alpha\n", proc.stdout)
        self.assertNotIn("office-on is on the block's PATH", proc.stderr)
        self.assertNotIn("runs in the office root", proc.stderr)
        self.assertEqual(self.run_office("probe", "fix-login", str(self.block), "--yes", "--project", "alpha",
                                         check=0).returncode, 0)
        self.assertEqual(subprocess.run([sys.executable, "-B", str(op.__file__), "reaches", str(self.block)],
                                        capture_output=True, text=True).stdout, "")
        self.assertEqual(len(self.history()), 2)

    def test_a_call_after_and_and_or_inside_a_substitution_reaches_the_project(self):
        self.block.write_text(block_of(["true && office-on alpha true", 'echo "and exit: $?"',
                                        'echo "tree: $(office-on alpha git rev-parse --is-inside-work-tree)"',
                                        'echo "cwd: $(pwd -P)"']))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertIn("the block calls office-on for alpha, so it runs in the office root", proc.stderr)
        self.assertIn("office-on is on the block's PATH for alpha", proc.stderr)
        self.assertIn("and exit: 0\ntree: true\n", proc.stdout)
        self.assertIn(f"cwd: {os.path.realpath(self.root)}", proc.stdout)
        self.assertEqual(subprocess.run([sys.executable, "-B", str(op.__file__), "reaches", str(self.block)],
                                        capture_output=True, text=True).stdout, "alpha\n")

    def test_a_heredoc_body_naming_it_does_not_reach(self):
        self.block.write_text(block_of(["cat <<EOF", "office-on alpha git status", "EOF", 'echo "cwd: $(pwd -P)"']))
        self.assertEqual(op.read_block(self.block.read_text())["reaches"], [])
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertIn("lane names alpha", proc.stderr)
        self.assertIn(f"office-on alpha git status\ncwd: {os.path.realpath(self.proj)}", proc.stdout)
        self.assertNotIn("office-on is on the block's PATH", proc.stderr)
        # A project the office does not scope, named only in text, refuses
        # nothing: the block is plain.
        self.block.write_text(block_of(['echo "office-on nowhere ls"', 'echo "cwd: $(pwd -P)"']))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertNotIn("nowhere", proc.stderr)
        self.assertIn(f"cwd: {os.path.realpath(self.proj)}", proc.stdout)


# --- 2. the words arrive as given ------------------------------------------------------------------

class TestTheWordsArriveAsGiven(ProbeCase):
    """Item 2: run_on quotes each word on the way to the project's shell."""

    def plan_reaching(self, where):
        return {"reaches": {"alpha": {"path": str(where), "host": None, "shell": None, "connect": None,
                                      "name": "alpha"}}}

    def test_run_on_quotes_the_words_as_a_unit(self):
        plan = self.plan_reaching(self.proj)
        self.assertEqual(op.run_on(plan, "alpha", ["bash", "-c", "echo one; echo two"]), (0, "one\ntwo\n", ""))
        self.assertEqual(op.run_on(plan, "alpha", ["echo", "a b"]), (0, "a b\n", ""))
        self.assertEqual(op.run_on(plan, "alpha", ["echo", "$NAME", "it's", '"q"']), (0, "$NAME it's \"q\"\n", ""))
        self.assertEqual(op.run_on(plan, "alpha", ["sh", "-c", "exit 3"])[0], 3)
        # One quoted word is one command's name now, not a shell line.
        code, out, err = op.run_on(plan, "alpha", ["pwd -P; git status"])
        self.assertEqual((code, out), (127, ""))
        self.assertIn("pwd -P; git status", err)
        with self.assertRaises(op.ProbeError) as cm:
            op.run_on(plan, "alpha", ["", " "])
        self.assertIn("no command given", cm.exception.lines[0])

    def test_bash_c_runs_the_script_whole_where_the_project_lives(self):
        self.block.write_text(block_of(["office-on alpha bash -c 'echo one; echo two; pwd -P'", 'echo "exit: $?"',
                                        'echo "cwd: $(pwd -P)"']))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertIn("office-on is on the block's PATH for alpha", proc.stderr)
        self.assertIn(f"one\ntwo\n{os.path.realpath(self.proj)}\nexit: 0\ncwd: {os.path.realpath(self.root)}",
                      proc.stdout)

    def test_a_word_with_a_space_a_quote_or_a_dollar_arrives_as_left(self):
        self.block.write_text(block_of(['office-on alpha echo "a b"', "office-on alpha echo '$NAME' \"it's\"",
                                        'office-on alpha printf "%s|%s\\n" "two words" one',
                                        'office-on alpha git log --format=%s -n 1']))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertIn("a b\n$NAME it's\ntwo words|one\ninit\n", proc.stdout)

    def test_the_helper_hands_its_words_on_as_given(self):
        plan = self.e.tmp / "plan.json"
        plan.write_text(json.dumps(self.plan_reaching(self.proj)))
        d = op.write_on_helper(self.e.tmp / "bin", plan)
        env = dict(self.e.env, PATH=f"{d}{os.pathsep}{self.e.env['PATH']}")
        proc = subprocess.run(["office-on", "alpha", "bash", "-c", "echo one; echo two"], env=env,
                              capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (0, "one\ntwo\n"), proc.stderr)
        proc = subprocess.run(["office-on", "alpha", "echo", "a b", "$x"], env=env, capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (0, "a b $x\n"), proc.stderr)


class TestTheWordsArriveAsGivenOnAHost(HostedStartCase):
    """Item 2 on a host: the quoted line goes through the project's shell
    as office_host.run_in sends an argv, and the fake shell runs it whole."""

    def test_the_hosted_call_runs_its_script_whole(self):
        self.only_far()
        (self.ssh.host_dir(HOST) / "path").write_text(f"{self.fake.dir}:/usr/bin:/bin\n")
        sid = self.start(self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        block = self.e.tmp / "probe.sh"
        block.write_text(block_of(["office-on far bash -c 'echo one; echo two; pwd -P'", 'echo "exit: $?"',
                                   'office-on far echo "a b" \'$NAME\'', 'echo "cwd: $(pwd -P)"']))
        proc = self.run_office("probe", self.name, str(block), "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"reaching far in {self.proj} on {HOST} (through far's shell) with office-on far", proc.stderr)
        self.assertIn(f"one\ntwo\n{os.path.realpath(self.proj)}\nexit: 0\na b $NAME\ncwd: {os.path.realpath(self.root)}",
                      proc.stdout)
        self.assertIn(f"for {sid} (desk/{self.name})", proc.stderr)
        calls = self.ssh.connections()
        self.assertTrue(all(c[0] == HOST for c in calls), calls)
        # The script went through the shell inside one quoted word of a
        # `bash -c` argv, the way run_in sends every argv: whole, and never
        # as words of the shell's own line.
        script = "echo one; echo two; pwd -P"
        self.assertTrue(any(script in c[-1] and f"bash -c {script}" not in c[-1] for c in calls),
                        [c[-1][:160] for c in calls])
        self.assertTrue(any("bash -c " in c[-1] and script in c[-1] for c in calls))
        self.assertEqual(self.ssh.left_on(HOST), [])


if __name__ == "__main__":
    unittest.main()
