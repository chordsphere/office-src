"""Tests for the desk's verbs: folder numbers, statuses, gates and History
in office open, close, reopen and sessions; the desk's groups; the
one-writer rule for the number open mints; the wizards; office status's
folder and filed-page checks; and office init refusing a defective
install.

Every test works under its own temporary HOME. bale is never needed: the
one-writer rule and the office's own In flight line read a fake bale on
the PATH (test_read_side's), replaying the probe's captured lines, or a
status line derived from one (below, where it is used). Run with the
rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import json
import os
import pathlib
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, PATCH, h  # noqa: E402
from test_read_side import FIXTURES, OPEN_WORKER, FakeBale, fixture_records, path_without_bale  # noqa: E402

import office_bale as ob  # noqa: E402

TEMPLATE = (REPO / "templates" / "folder.md").read_text()


def fields_of(text):
    """The field block's (key, value) lines, in order."""
    head = text.split("\n## ", 1)[0]
    return re.findall(r"^- ([a-z ]+): (.*)$", head, re.M)


def history_of(text):
    return re.findall(r"^- (\d{4}-\d{2}-\d{2}) ([a-z-]+): (.*)$", text.split("\n## History\n", 1)[1], re.M)


def sessions_of(text):
    return text.split("\n## Sessions\n", 1)[1].split("\n## ", 1)[0]


class Office:
    """A founded office, and the verbs run in it with stdin piped."""

    def __init__(self, test, **kw):
        self.e = Env(test)
        self.root = self.e.init(**kw)
        self.e.found(self.root)
        self.test = test

    def run(self, *args, check=0, **kw):
        return self.e.run(*args, cwd=self.root, check=check, **kw)

    def open(self, *args):
        return self.run("open", *args).stdout.strip()

    def text(self, rel):
        return (self.root / rel / "folder.md").read_text()

    def clean(self):
        self.test.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")


def terminal(env, cwd, argv, steps, limit=20):
    """Run the office command on a terminal. steps is a list of (prompt,
    answer): wait until the prompt shows, then type the answer. Returns
    (exit code, everything the terminal showed)."""
    pid, fd = pty.fork()
    if pid == 0:
        try:
            os.chdir(cwd)
            os.execve(argv[0], argv, env)
        finally:
            os._exit(127)
    seen = b""

    def read_until(marker, start):
        nonlocal seen
        deadline = time.time() + limit
        while seen.find(marker, start) < 0 and time.time() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    return False
                if not chunk:
                    return False
                seen += chunk
        return seen.find(marker, start) >= 0

    start = 0
    for prompt, answer in steps:
        if not read_until(prompt.encode(), start):
            break
        start = seen.find(prompt.encode(), start) + len(prompt)
        os.write(fd, answer.encode() + b"\n")
    read_until(b"\x00never shown", 0)
    _, status = os.waitpid(pid, 0)
    os.close(fd)
    return os.waitstatus_to_exitcode(status), seen.decode("utf-8", "replace")


# --- the template and the fields ------------------------------------------------------

class TestTemplate(unittest.TestCase):
    def test_an_unset_field_line_is_dropped_and_a_list_renders_one_line_each(self):
        out = h.render_template("# {{title}}\n\n- number: {{number}}\n- size: {{size}}\n- after: {{after}}\n\n- {{history}}\n",
                                {"title": "t", "number": "4", "after": ["folder 1", "agenda 2"],
                                 "history": "2026-09-30 queued: office open"})
        self.assertEqual(out, "# t\n\n- number: 4\n- after: folder 1\n- after: agenda 2\n\n- 2026-09-30 queued: office open\n")

    def test_any_other_placeholder_still_needs_its_value(self):
        with self.assertRaises(h.HelperError):
            h.render_template("# {{title}}\n", {})
        with self.assertRaises(h.HelperError):
            h.render_template("# {{title}}\n", {"title": ["a", "b"]})
        self.assertEqual(h.render_template("x{{a}}y\n", {"a": ""}), "xy\n")

    def test_the_folder_template_shows_the_whole_block_in_the_blueprints_order(self):
        keys = re.findall(r"^- ([a-z ]+): \{\{([a-z_]+)\}\}$", TEMPLATE.split("\n## ", 1)[0], re.M)
        self.assertEqual([k for k, _ in keys], list(h.FIELD_KEYS))
        bare = h.render_template(TEMPLATE, {"title": "t", "history": "2026-09-30 queued: office open"})
        self.assertEqual(fields_of(bare), [])
        self.assertNotIn("{{", bare)

    def test_the_cli_takes_a_repeated_key_as_a_list(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "t.md").write_text("- after: {{after}}\n- size: {{size}}\n")
        proc = subprocess.run([sys.executable, str(REPO / "lib/office_helper.py"), "render-template", str(tmp / "t.md"),
                               "after=folder 1", "after=folder 2", "size="], capture_output=True, text=True)
        self.assertEqual(proc.stdout, "- after: folder 1\n- after: folder 2\n")


class TestFields(unittest.TestCase):
    def test_closed_vocabularies(self):
        self.assertEqual(h.normalize_field("size", "Small"), "small")
        self.assertEqual(h.normalize_field("class", "contract-doc"), "contract-doc")
        for key, bad, words in (("size", "huge", "small, medium, high"), ("class", "prose", "code, doc"),
                                ("status", "parked", "candidate"), ("sid", "x-1", "session id")):
            with self.assertRaises(h.HelperError) as cm:
                h.normalize_field(key, bad)
            self.assertIn(words, str(cm.exception))

    def test_gates_take_the_citation_grammar_and_a_bare_number_is_a_folder(self):
        for given, want in (("140", "folder 140"), ("#7", "folder 7"), ("folder  12", "folder 12"),
                            ("agenda 7", "agenda 7"), ("ruling 2026-10-02-riders-home", "ruling 2026-10-02-riders-home"),
                            ("blueprint 2026-09-29-drafting-table", "blueprint 2026-09-29-drafting-table")):
            self.assertEqual(h.normalize_field("after", given), want)
        self.assertEqual(h.normalize_field("consumer", "blueprint 2026-10-01-twine-courier"), "blueprint 2026-10-01-twine-courier")
        self.assertEqual(h.normalize_field("blueprint", "blueprint 2026-09-29-drafting-table"), "2026-09-29-drafting-table")
        for key, bad in (("after", "rider 3"), ("serializes after", "agenda 7"), ("consumer", "agenda 1"),
                         ("linked", "ruling 2026-01-01-x"), ("blueprint", "drafting table")):
            with self.assertRaises(h.HelperError):
                h.normalize_field(key, bad)

    def test_every_field_and_question_has_its_explanation(self):
        for key in h.FIELD_KEYS + ("title", "sid"):
            self.assertIn(key, h.FIELD_HELP)
            self.assertTrue(h.FIELD_HELP[key].isascii(), key)

    def test_the_history_verbs_and_the_state_machine(self):
        self.assertEqual(set(h.STATE_VERBS.values()), set(h.STATUSES))
        self.assertTrue(set(h.STATE_VERBS) <= set(h.HISTORY_VERBS))
        for verb in ("queued", "opened", "ratified", "gated", "cleared", "grown", "re-scoped", "corrected",
                     "ruled", "carried", "consumed", "done", "absorbed", "split", "retired", "reopened", "note"):
            self.assertIn(verb, h.HISTORY_VERBS)


# --- office open -----------------------------------------------------------------

class TestOpen(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)

    def test_numbers_count_the_desk_and_the_cabinet_and_skip_folders_without_one(self):
        first = self.o.open("one")
        self.o.run("close", "one")
        # A folder from before numbers: never numbered, never rewritten.
        old = self.o.root / "filing-cabinet" / "2026-01-01-old"
        old.mkdir()
        (old / "folder.md").write_text("# old\n\n- status: done\n\n## History\n\n- 2026-01-01 done: office close\n")
        self.o.e.git(self.o.root, "add", "-A")
        self.o.e.git(self.o.root, "commit", "-qm", "an older folder")
        before = (old / "folder.md").read_bytes()
        second = self.o.open("two")
        self.assertIn("- number: 2\n", self.o.text(second))
        proc = self.o.run("open", "three", extra={"OFFICE_DEBUG": "1"})
        self.assertIn("- number: 3\n", self.o.text(proc.stdout.strip()))
        self.assertIn("never numbered", proc.stderr)
        self.assertIn("filing-cabinet/2026-01-01-old", proc.stderr)
        self.assertEqual((old / "folder.md").read_bytes(), before)
        self.assertEqual(pathlib.Path(first).name, f"{pathlib.Path(first).name[:10]}-one")
        self.o.clean()

    def test_a_number_line_that_does_not_read_refuses_to_mint(self):
        folder = self.o.open("one")
        f = self.o.root / folder / "folder.md"
        f.write_text(f.read_text().replace("- number: 1", "- number: 1a"))
        proc = self.o.run("open", "two", check=1)
        self.assertIn("number line is not a number", proc.stderr)
        self.assertFalse(list((self.o.root / "desk").glob("*-two")))

    def test_every_field_from_its_flag_in_the_blueprints_order(self):
        self.o.open("base")
        folder = self.o.open("job", "--title", "Fix the login", "--consumer", "blueprint 2026-10-01-twine-courier",
                             "--after", "1", "--after", "agenda 7", "--serializes-after", "folder 1",
                             "--size", "Small", "--class", "meta", "--lane", "office-src: share/, templates/",
                             "--source", "blueprint 2026-09-29-drafting-table", "--blueprint", "2026-09-29-drafting-table",
                             "--linked", "#1")
        text = self.o.text(folder)
        day = pathlib.Path(folder).name[:10]
        self.assertEqual(fields_of(text), [
            ("number", "2"), ("status", "queued"), ("queued", day), ("class", "meta"), ("size", "small"),
            ("lane", "office-src: share/, templates/"), ("source", "blueprint 2026-09-29-drafting-table"),
            ("blueprint", "2026-09-29-drafting-table"), ("linked", "folder 1"), ("after", "folder 1"),
            ("after", "agenda 7"), ("serializes after", "folder 1"),
            ("consumer", "blueprint 2026-10-01-twine-courier")])
        self.assertEqual(history_of(text), [(day, "queued", "office open")])
        self.assertTrue(text.startswith("# Fix the login\n"))

    def test_a_candidate_and_a_folder_born_done(self):
        cand = self.o.open("maybe", "--candidate")
        text = self.o.text(cand)
        day = pathlib.Path(cand).name[:10]
        self.assertIn("- status: candidate\n", text)
        self.assertEqual(history_of(text), [(day, "candidate", "office open --candidate")])
        born = self.o.open("in-sitting", "--filed", "--sid", "2026-09-30-desk-verbs-002")
        self.assertTrue(born.startswith("filing-cabinet/"), born)
        text = self.o.text(born)
        self.assertEqual(fields_of(text)[:2], [("number", "2"), ("status", "done")])
        self.assertIn("- 2026-09-30-desk-verbs-002\n", sessions_of(text))
        self.assertEqual(history_of(text), [(day, "done", "office open --filed, done at 2026-09-30-desk-verbs-002")])
        self.o.clean()

    def test_piped_never_asks_and_names_the_flag(self):
        for args, words in ((("--size", "small"), "--title TITLE"),
                            (("job", "--size", "huge"), "--size: size is one of small, medium, high"),
                            (("job", "--after", "rider 3"), "--after: after takes folder N"),
                            (("job", "--filed"), "--filed needs --sid SID"),
                            (("job", "--sid", "2026-09-30-x-001"), "--sid goes with --filed"),
                            (("job", "--candidate", "--filed", "--sid", "2026-09-30-x-001"), "give one"),
                            (("job", "--colour", "red"), "does not know --colour")):
            proc = self.o.run("open", *args, check=1)
            self.assertIn(words, proc.stderr, args)
        self.assertEqual(list((self.o.root / "desk").iterdir()), [self.o.root / "desk" / ".keep"])

    def test_the_slug_comes_from_the_title_when_none_is_given(self):
        folder = self.o.open("--title", "Write the wizard docs for every verb that asks a question")
        self.assertRegex(folder, r"^desk/\d{4}-\d{2}-\d{2}-write-the-wizard-docs-for-every-verb$")

    def test_a_title_is_one_ascii_line_and_the_slug_comes_from_the_words(self):
        folder = self.o.open("--title", "Caf\u00e9 one\n- status: done\n## History")
        text = self.o.text(folder)
        self.assertTrue(text.startswith("# Caf\\xe9 one - status: done ## History\n\n- number: 1\n"), text[:80])
        self.assertEqual([k for k, _ in fields_of(text)], ["number", "status", "queued"])
        self.assertRegex(folder, r"-caf-one-status-done-history$")
        self.assertIn("every status agrees", self.o.run("status").stdout)

    def test_help_explains_every_field(self):
        out = self.o.run("open", "--help").stdout
        for key in ("size", "lane", "source", "class", "after", "serializes after", "consumer", "linked", "blueprint"):
            self.assertIn(f"  {key}: ", out)


class TestWizards(unittest.TestCase):
    """Doctrine section 7: on a terminal a verb asks for what it was not
    given, every question names its flag twin, ? explains, and an answer
    the field does not take is explained and asked again."""

    def setUp(self):
        self.o = Office(self)
        self.env = dict(self.o.e.env)
        self.bin = str(self.o.e.office_bin)

    def test_open_in_four_answers(self):
        code, seen = terminal(self.env, self.o.root, [self.bin, "open"],
                              [("(--title):", "Fix the login"), ("(--size) [return skips]:", "small"),
                               ("(--lane) [return skips]:", "office-src: bin/"),
                               ("(--source) [return skips]:", "notepad/2026-09-30.md")])
        self.assertEqual(code, 0, seen)
        for question in ("Title, in a few words (--title):", "(--size) [return skips]:",
                         "(--lane) [return skips]:", "(--source) [return skips]:"):
            self.assertIn(question, seen)
        folder = next((self.o.root / "desk").glob("*-fix-the-login"))
        self.assertEqual([k for k, _ in fields_of((folder / "folder.md").read_text())],
                         ["number", "status", "queued", "size", "lane", "source"])

    def test_returns_skip_and_question_marks_explain(self):
        code, seen = terminal(self.env, self.o.root, [self.bin, "open", "job", "--size", "huge"],
                              [("(--title) [job]:", ""), ("(--size) [return skips]:", "?"),
                               ("(--size) [return skips]:", "medium"), ("(--lane) [return skips]:", ""),
                               ("(--source) [return skips]:", "")])
        self.assertEqual(code, 0, seen)
        self.assertIn("--size 'huge': size is one of small, medium, high", seen)
        self.assertIn("the desk puts small jobs first", seen.lower())
        self.assertIn("Title, in a few words (--title) [job]:", seen)
        folder = next((self.o.root / "desk").glob("*-job"))
        self.assertEqual([k for k, _ in fields_of((folder / "folder.md").read_text())],
                         ["number", "status", "queued", "size"])

    def test_a_flag_given_is_never_asked(self):
        code, seen = terminal(self.env, self.o.root,
                              [self.bin, "open", "job", "--title", "T", "--size", "small", "--lane", "x: y",
                               "--source", "a person"], [])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("(--", seen)

    def test_close_and_init_ask_the_same_way(self):
        self.o.open("job")
        code, seen = terminal(self.env, self.o.root, [self.bin, "close"], [("(office close FOLDER):", "folder 1")])
        self.assertEqual(code, 0, seen)
        self.assertIn("folder 1  ", seen)
        self.assertIn("(office close FOLDER):", seen)
        self.assertTrue(list((self.o.root / "filing-cabinet").glob("*-job")))
        code, seen = terminal(self.env, self.o.e.home, [self.bin, "init"],
                              [("(--path):", "?"), ("(--path):", str(self.o.e.home / "second")),
                               ("[second]:", "")])
        self.assertEqual(code, 0, seen)
        self.assertIn("(--path):", seen)
        self.assertIn("It becomes its own git", seen)
        self.assertIn("Name for the office (--name) [second]:", seen)
        self.assertTrue((self.o.e.home / "second" / "floor-plan" / "manifest.toml").is_file())


# --- close, reopen, sessions -------------------------------------------------------

class TestCloseAndReopen(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)
        for slug in ("one", "two", "three", "four"):
            self.o.open(slug)
        self.day = next((self.o.root / "desk").glob("*-one")).name[:10]

    def test_into_absorbs_and_the_successor_points_back(self):
        self.o.run("close", "two", "--into", "1")
        filed = self.o.text(next((self.o.root / "filing-cabinet").glob("*-two")).relative_to(self.o.root))
        self.assertIn("- status: absorbed\n", filed)
        self.assertEqual(history_of(filed)[-1], (self.day, "absorbed", "into folder 1"))
        one = self.o.text(next((self.o.root / "desk").glob("*-one")).relative_to(self.o.root))
        self.assertEqual(history_of(one)[-1][1:], ("note", f"absorbed folder 2 ({self.day}-two)"))
        self.assertIn("- status: queued\n", one)
        self.o.clean()
        self.assertIn("(absorbed: into folder 1)", self.o.e.git(self.o.root, "log", "-1", "--format=%s"))

    def test_split_and_retired(self):
        self.o.run("close", "one", "--split", "3,4")
        filed = self.o.text(next((self.o.root / "filing-cabinet").glob("*-one")).relative_to(self.o.root))
        self.assertEqual(history_of(filed)[-1], (self.day, "split", "into folders 3, 4"))
        for slug in ("three", "four"):
            text = self.o.text(next((self.o.root / "desk").glob(f"*-{slug}")).relative_to(self.o.root))
            self.assertEqual(history_of(text)[-1][1:], ("note", f"split from folder 1 ({self.day}-one)"))
        self.o.run("close", "two", "--retired", "premise corrected")
        filed = self.o.text(next((self.o.root / "filing-cabinet").glob("*-two")).relative_to(self.o.root))
        self.assertEqual(history_of(filed)[-1], (self.day, "retired", "premise corrected"))
        self.assertIn("- status: retired\n", filed)
        self.o.clean()

    def test_refusals(self):
        for args, words in ((("one", "--into", "1"), "into itself"),
                            (("one", "--into", "9"), "no folder 9"),
                            (("one", "--split", "2"), "two or more"),
                            (("one", "--split", "2, 2"), "names folder 2 twice"),
                            (("one", "--into", "2", "--retired", "x"), "give one"),
                            ((), "name a folder")):
            proc = self.o.run("close", *args, check=1)
            self.assertIn(words, proc.stderr, args)
        self.o.clean()

    def test_reopen_writes_reopened_and_open_and_refuses_what_lives_elsewhere(self):
        self.o.run("close", "one")
        self.o.run("reopen", "folder 1")
        text = self.o.text(next((self.o.root / "desk").glob("*-one")).relative_to(self.o.root))
        self.assertIn("- status: open\n", text)
        self.assertEqual([v for _, v, _ in history_of(text)], ["queued", "done", "reopened"])
        self.o.run("close", "two", "--into", "3")
        proc = self.o.run("reopen", "two", check=1)
        self.assertIn("was absorbed", proc.stderr)
        self.o.clean()

    def test_a_successor_must_still_carry_work_and_a_failed_close_writes_nothing(self):
        self.o.run("close", "four", "--retired", "moot")
        proc = self.o.run("close", "one", "--into", "4", check=1)
        self.assertIn("folder 4 is retired itself", proc.stderr)
        two = next((self.o.root / "desk").glob("*-two"))
        (self.o.root / "filing-cabinet" / two.name).mkdir()
        before = (two / "folder.md").read_bytes()
        proc = self.o.run("close", "two", check=1)
        self.assertIn("nothing was written", proc.stderr)
        self.assertEqual((two / "folder.md").read_bytes(), before)

    def test_a_folder_is_named_by_its_number(self):
        self.o.run("close", "folder 3")
        self.assertTrue(list((self.o.root / "filing-cabinet").glob("*-three")))
        proc = self.o.run("close", "folder 3", check=1)
        self.assertIn("filing-cabinet", proc.stderr)


class TestSessionsOpen(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)
        self.folder = self.o.open("job")
        self.day = pathlib.Path(self.folder).name[:10]

    def test_the_first_sid_opens_a_queued_folder_and_the_next_does_not(self):
        report = '{"outcome": "packed", "sid": "2026-09-30-job-001"}\n'
        self.o.run("sessions", "job", "-", input=report)
        text = self.o.text(self.folder)
        self.assertIn("- status: open\n", text)
        self.assertEqual(history_of(text)[-1], (self.day, "opened", "2026-09-30-job-001"))
        self.o.run("sessions", "job", "2026-09-30-job-002")
        text = self.o.text(self.folder)
        self.assertEqual([v for _, v, _ in history_of(text)], ["queued", "opened"])
        self.o.clean()

    def test_a_filed_folder_keeps_its_status(self):
        self.o.run("close", "job")
        self.o.run("sessions", "job", "2026-09-30-job-001")
        text = (self.o.root / "filing-cabinet" / pathlib.Path(self.folder).name / "folder.md").read_text()
        self.assertIn("- status: done\n", text)
        self.assertNotIn("opened", text)

    def test_ratified_under_its_sid_with_and_without_an_exception(self):
        self.o.run("sessions", "job", "2026-09-30-job-001")
        self.o.run("sessions", "job", "2026-09-30-job-002")
        self.o.run("sessions", "job", "2026-09-30-job-001", "--ratified")
        self.o.run("sessions", "job", "-", "--ratified", "--except", "the slug rule, moved to folder 3",
                   input='{"sid": "2026-09-30-job-002"}\n')
        sessions = sessions_of(self.o.text(self.folder))
        self.assertIn(f"- 2026-09-30-job-001\n- 2026-09-30-job-001 ratified {self.day}\n- 2026-09-30-job-002\n"
                      f"- 2026-09-30-job-002 ratified {self.day}, except: the slug rule, moved to folder 3\n", sessions)
        proc = self.o.run("sessions", "job", "2026-09-30-job-001", "--ratified", check=1)
        self.assertIn("already ratified", proc.stderr)
        proc = self.o.run("sessions", "job", "2026-09-30-job-009", "--ratified", check=1)
        self.assertIn("record it first", proc.stderr)
        proc = self.o.run("sessions", "job", "--ratified", check=1)
        self.assertIn("--ratified needs the session", proc.stderr)
        self.assertIn("(sessions: 2)", self.o.run("desk").stdout)
        self.o.clean()


# --- the desk ----------------------------------------------------------------------

class TestDesk(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)

    def desk(self, *extra):
        return self.o.run("desk", *extra).stdout

    def section(self, out, name):
        return ("\n" + out).split(f"\n{name}:\n", 1)[1].split("\n\n", 1)[0]

    def test_ready_in_order_parked_under_its_gate_and_candidates(self):
        self.o.open("big", "--size", "high")
        self.o.open("mid", "--size", "medium")
        self.o.open("tiny", "--size", "small", "--serializes-after", "4")
        self.o.open("first", "--size", "high")
        self.o.open("after-first", "--after", "4")
        self.o.open("agenda-gate", "--after", "agenda 7")
        self.o.open("for-blueprint", "--consumer", "blueprint 2026-10-01-twine-courier")
        self.o.open("ghost", "--after", "99")
        self.o.open("idea", "--candidate")
        out = self.desk()
        ready = self.section(out, "Ready").splitlines()
        # 3 serializes after 4, so 4 goes first; otherwise small first, then number.
        self.assertEqual([l.split()[1] for l in ready], ["2", "1", "4", "3"], out)
        parked = self.section(out, "Parked")
        self.assertIn("ERROR: folder 8: after folder 99 names no folder on the desk or in the filing cabinet\n"
                      "    folder 8  ", parked)
        self.assertIn("waiting for folder 4 (queued): first\n    folder 5  ", parked)
        self.assertIn("waiting for agenda 7: not readable until the drafting-table verbs land\n    folder 6  ", parked)
        self.assertIn("parked for its consumer, blueprint 2026-10-01-twine-courier: not readable until the "
                      "drafting-table verbs land\n    folder 7  ", parked)
        self.assertIn("  folder 9  ", self.section(out, "Candidates"))
        for n in range(1, 10):
            self.assertEqual(len(re.findall(rf"^ +folder {n}  ", out, re.M)), 1, (n, out))

    def test_a_cycle_is_an_error_line_and_drops_no_folder(self):
        self.o.open("a", "--after", "2")
        self.o.open("b", "--after", "1")
        out = self.desk()
        self.assertIn("ERROR: after gates in a cycle: folder 1 -> folder 2 -> folder 1", out)
        self.assertRegex(out, r"\n    folder 1  ")
        self.assertRegex(out, r"\n    folder 2  ")

    def test_a_gate_clears_when_its_folder_is_done_and_says_so_since_the_last_walk_in(self):
        self.o.open("first")
        self.o.open("second", "--after", "1")
        self.o.open("third", "--after", "1")
        self.o.run("close", "third", "--into", "1")
        self.assertIn("waiting for folder 1 (queued)", self.desk())
        self.o.run()  # walking in records today
        self.o.run("close", "first")
        out = self.desk()
        day = next((self.o.root / "filing-cabinet").glob("*-first")).name[:10]
        self.assertIn(f"  folder 2  ", self.section(out, "Ready"))
        self.assertIn(f"    gate cleared: folder 1 done {day}", out)
        record = list((self.o.e.home / ".local/state/office-src/walk-ins").iterdir())
        self.assertEqual(len(record), 1)
        record[0].write_text("2999-01-01\n")
        self.assertNotIn("gate cleared", self.desk())

    def test_absorbed_and_split_gates_follow_their_successors(self):
        self.o.open("old")
        self.o.open("new")
        self.o.open("waits", "--after", "1")
        self.o.run("close", "old", "--into", "2")
        out = self.desk()
        self.assertIn("waiting for folder 1 (absorbed into folder 2): folder 2 (queued): new", out)
        self.o.run("close", "new")
        self.assertIn("  folder 3  ", self.section(self.desk(), "Ready"))

    def test_open_folders_and_folders_without_a_status_line(self):
        folder = self.o.open("job")
        self.o.run("sessions", "job", "2026-09-30-job-001")
        old = self.o.root / "desk" / "2026-01-01-old"
        old.mkdir()
        (old / "folder.md").write_text("# old\n\n## Next\n\n- Ship it.\n")
        out = self.desk()
        self.assertIn(f"  folder 1  {pathlib.Path(folder).name}  next: (not written yet)  (sessions: 1)  "
                      "[open, no session in flight]", self.section(out, "In flight"))
        self.assertIn("  2026-01-01-old  next: Ship it.  (sessions: 0)", out)

    def test_the_walk_in_shows_in_flight_and_the_first_three_ready(self):
        for slug in ("a", "b", "c", "d"):
            self.o.open(slug)
        self.o.open("e", "--after", "agenda 1")
        out = self.o.run().stdout
        desk = out.split("On the desk: ", 1)[1].split("\n\n", 1)[0]
        self.assertTrue(desk.startswith("4 ready, 1 parked, 0 candidate(s) (office desk shows every group)\n"), desk)
        self.assertEqual(len(re.findall(r"^  folder \d+  ", desk, re.M)), 3)
        self.assertIn("  and 1 more ready", desk)
        self.assertLess(out.index("In flight:"), out.index("On the desk:"))

    def test_an_unreadable_folder_or_gate_is_named_and_the_rest_still_renders(self):
        self.o.open("good")
        self.o.open("gated", "--after", "1")
        bad = self.o.root / "desk" / "2026-03-03-bad"
        bad.mkdir()
        (bad / "folder.md").write_bytes(b"# B\xff\n")
        f = next((self.o.root / "desk").glob("*-gated")) / "folder.md"
        f.write_text(f.read_text().replace("- after: folder 1", "- after: folder 1a"))
        out = self.desk()
        self.assertIn("Cannot be read:\n  2026-03-03-bad  (folder.md cannot be read (UnicodeDecodeError", out)
        self.assertIn("ERROR: folder 2: `after: folder 1a` does not read", out)
        self.assertIn("  folder 1  ", self.section(out, "Ready"))
        self.assertIn("1 ready", self.o.run().stdout)

    def test_an_empty_desk(self):
        self.assertIn("the desk is clear", self.desk())
        self.assertIn("  the desk is clear", self.o.run().stdout)


# --- office status's checks -------------------------------------------------------------

class TestStatusChecks(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)

    def status(self):
        return self.o.run("status").stdout

    def test_every_status_agrees_with_its_history(self):
        self.o.open("one")
        self.o.open("two")
        self.o.run("close", "two")
        self.assertIn("folders:    2 on the desk and in the filing cabinet; every status agrees with its History",
                      self.status())
        f = next((self.o.root / "desk").glob("*-one")) / "folder.md"
        f.write_text(f.read_text().replace("- status: queued", "- status: open"))
        g = next((self.o.root / "filing-cabinet").glob("*-two")) / "folder.md"
        g.write_text(g.read_text().replace("- number: 2", "- number: 1") + "- 2026-09-30 shelved: by hand\n")
        out = self.status()
        self.assertIn("folders:    3 problem(s) in 2 folders:", out)
        self.assertIn("folder 1 is minted twice", out)
        self.assertIn("status open, but its History's last state-changing line is", out)
        self.assertIn("History verb 'shelved' (2026-09-30) is not one of the set", out)

    def test_folders_from_before_the_field_block_are_counted_not_faulted(self):
        old = self.o.root / "desk" / "2026-01-01-old"
        old.mkdir()
        (old / "folder.md").write_text("# old\n")
        self.assertIn("every status agrees with its History; 1 with no status line, from before the field block",
                      self.status())

    def test_filed_pages_only_grow_at_their_end(self):
        self.o.run("note", "first line")
        self.o.run("note", "second line")
        self.assertIn("filed:      every commit to a filed page only appended at its end (notepad: 2 file(s), 3 commit(s))",
                      self.status())
        page = next((self.o.root / "notepad").glob("*.md"))
        page.write_text(page.read_text().replace("first line", "FIRST LINE"))
        out = self.status()
        self.assertIn(f"  uncommitted notepad/{page.name}: changed bytes already filed", out)
        self.o.e.git(self.o.root, "commit", "-qam", "a hand edit")
        sha = self.o.e.git(self.o.root, "rev-parse", "--short=10", "HEAD").strip()
        out = self.status()
        self.assertIn("filed:      1 change(s) to filed pages did more than append at the end (notepad):", out)
        self.assertIn(f"  {sha} ", out)
        self.assertIn(f"notepad/{page.name}: changed bytes already filed", out)

    def test_the_filing_cabinet_keeps_its_own_rule_and_a_part_filed_list_is_read(self):
        self.o.open("one")
        self.o.run("close", "one")
        self.o.run("sessions", "one", "2026-09-30-one-001")  # a line inside a filed folder
        manifest = self.o.root / "floor-plan/manifest.toml"
        manifest.write_text(manifest.read_text() + '\n[spaces.drafting-table]\npath = "drafting-table"\n'
                            'filed = ["drafting-table/rulings.md"]\n')
        rulings = self.o.root / "drafting-table" / "rulings.md"
        rulings.parent.mkdir()
        rulings.write_text("# Rulings\n\n## r1\n")
        self.o.e.git(self.o.root, "add", "-A")
        self.o.e.git(self.o.root, "commit", "-qm", "a table")
        rulings.write_text("# Rulings\n\n## r1, amended\n")
        self.o.e.git(self.o.root, "commit", "-qam", "amended in place")
        out = self.status()
        self.assertIn("drafting-table/rulings.md: changed bytes already filed", out)
        self.assertNotIn("filing-cabinet/", out.split("filed:", 1)[1].split("bale:", 1)[0])

    def test_status_reports_and_exits_zero(self):
        proc = self.o.run("status", check=0)
        self.assertIn("folders:", proc.stdout)
        self.assertIn("filed:", proc.stdout)


class TestInitRefusesADefectiveInstall(unittest.TestCase):
    def test_init_refuses_loudly_where_status_reports(self):
        e = Env(self)
        office = e.fake_install(PATCH)
        verbs = office.parent.parent / "share" / "verbs.toml"
        text = verbs.read_text(encoding="utf-8")
        verbs.write_text(text.replace('\nlands = ["desk/{folder}/folder.md"]\nattended = false\n',
                                      '\nlands = []\nattended = false\n'), encoding="utf-8")
        proc = e.run("init", str(e.home / "w"), bin_path=office)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("cleanup: an unattended session kind with no declared landing", proc.stderr)
        self.assertIn("refusing to build an office from a defective install", proc.stderr)
        self.assertFalse((e.home / "w").exists())
        verbs.write_text("[verbs\n")
        proc = e.run("init", str(e.home / "w"), bin_path=office)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("could not check the install's catalogs", proc.stderr)
        self.assertFalse((e.home / "w").exists())


# --- the one-writer rule, and the office's own registry -----------------------------

def office_status_fixture(tmp, sessions, scopes):
    """A fixture set for an office whose registry has open sessions: the
    status line the probe captured in a project, with sessions and scopes
    set to the test's (every key is a captured key; only the values are
    the test's), beside the probe's real dossier of OPEN_WORKER, so the
    In flight line has a real record to read. Kept in the test's temporary
    directory: the development record's fixtures are captured, never
    made."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="office-registry-", dir=tmp))
    for f, rec in fixture_records("office-src"):
        if rec["argv"] == ["status", "--json"]:
            line = json.loads(rec["stdout"][0])
            line["sessions"], line["scopes"] = sessions, scopes
            rec = dict(rec, stdout=[json.dumps(line)], stdout_sha256=[])
            (d / f.name).write_text(json.dumps(rec))
        elif rec["argv"] == ["stats", "--sid", OPEN_WORKER, "--json"]:
            shutil.copy(f, d / f.name)
    return d


class TestOneWriter(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)

    def bale(self, routes):
        fake = FakeBale(self.o.e.tmp, routes)
        self.o.e.env["PATH"] = fake.path(self.o.e.env["PATH"])
        return fake

    def test_no_registry_no_refusal_said_at_debug(self):
        fake = self.bale({})
        proc = self.o.run("open", "job", extra={"OFFICE_DEBUG": "1"})
        self.assertIn("no .bale/ in the office", proc.stderr)
        self.assertEqual(fake.argvs(), [])

    def test_a_session_whose_forecast_holds_the_desk_refuses_and_is_named(self):
        (self.o.root / ".bale").mkdir()
        self.bale({str(self.o.root): office_status_fixture(self.o.e.tmp, [OPEN_WORKER],
                                                           {OPEN_WORKER: ["desk", "notepad"]})})
        proc = self.o.run("open", "job", check=1)
        self.assertIn(f"{OPEN_WORKER} holds desk (its forecast: desk, notepad)", proc.stderr)
        self.assertIn("the one-writer rule", proc.stderr)
        self.assertFalse(list((self.o.root / "desk").glob("*-job")))
        # The cabinet is not held, so a folder born done may be filed.
        self.o.run("open", "done-job", "--filed", "--sid", "2026-09-30-x-001")

    def test_a_session_on_one_folder_or_read_only_does_not_hold_the_desk(self):
        (self.o.root / ".bale").mkdir()
        self.bale({str(self.o.root): office_status_fixture(
            self.o.e.tmp, [OPEN_WORKER, "2026-09-29-continue-plan-002"],
            {OPEN_WORKER: ["desk/2026-09-30-other", "notepad"], "2026-09-29-continue-plan-002": []})})
        self.o.run("open", "job")

    def test_an_unreadable_registry_is_said_and_does_not_stop_capture(self):
        (self.o.root / ".bale").mkdir()
        proc = self.o.run("open", "job", extra={"PATH": path_without_bale()})
        self.assertIn("minting without the one-writer check", proc.stderr)

    def test_forecast_holds(self):
        for entry, target, holds in (("desk", "desk", True), (".", "desk", True), ("", "filing-cabinet", True),
                                     ("desk/", "desk", True), ("desk/2026-x", "desk", False),
                                     ("notepad", "desk", False), ("desks", "desk", False)):
            self.assertEqual(ob.forecast_holds(entry, target), holds, (entry, target))

    def test_the_offices_own_sessions_are_in_flight(self):
        (self.o.root / ".bale").mkdir()
        self.bale({str(self.o.root): office_status_fixture(self.o.e.tmp, [OPEN_WORKER],
                                                           {OPEN_WORKER: ["desk/2026-09-30-x"]})})
        self.o.open("job")
        self.o.run("sessions", "job", OPEN_WORKER)
        out = self.o.run("desk").stdout
        flight = out.split("In flight:\n", 1)[1].split("\n\n", 1)[0]
        self.assertIn("this office scopes no projects", flight)
        self.assertRegex(flight, rf"this office: {OPEN_WORKER} open, opened \d+[mhd] ago -> desk/\S+-job")
        self.assertNotIn("Ready:", out)
        self.assertNotIn("the desk is clear", out)
        self.assertIn("On the desk: 1 open, 0 ready", self.o.run().stdout)


class TestAFolderFromBeforeNumbers(unittest.TestCase):
    """A folder 0.3.0 and 0.4.0 opened: a status and a queued line, a
    History, no number. Every verb serves it, the desk cites it by name,
    and nothing numbers it."""

    def test_every_verb_serves_it_and_nothing_numbers_it(self):
        o = Office(self)
        folder = o.root / "desk" / "2026-09-29-older"
        folder.mkdir()
        body = TEMPLATE.split("\n## Asked", 1)[1].rsplit("- {{history}}", 1)[0]
        (folder / "folder.md").write_text("# older\n\n- status: queued\n- queued: 2026-09-29\n\nOne job.\n\n## Asked"
                                          + body + "- 2026-09-29 queued: office open\n")
        o.e.git(o.root, "add", "-A")
        o.e.git(o.root, "commit", "-qm", "a 0.4.0 folder")
        self.assertIn("  2026-09-29-older  next: (not written yet)  (sessions: 0)",
                      o.run("desk").stdout.split("Ready:", 1)[1])
        new = o.open("newer")
        self.assertIn("- number: 1\n", o.text(new))
        o.run("sessions", "older", "2026-09-30-older-001")
        o.run("close", "older")
        o.run("reopen", "older")
        text = (folder / "folder.md").read_text()
        self.assertNotIn("- number:", text)
        self.assertEqual([v for _, v, _ in history_of(text)], ["queued", "opened", "done", "reopened"])
        self.assertIn("- status: open\n", text)
        self.assertIn("every status agrees with its History", o.run("status").stdout)
        o.clean()


class TestCatalogAndDoctrine(unittest.TestCase):
    def test_lands_name_the_folder_patterns_the_verbs_write(self):
        import tomllib
        v = tomllib.loads((REPO / "share/verbs.toml").read_text())["verbs"]
        self.assertEqual(v["open"]["lands"], ["desk/{folder}", "filing-cabinet/{folder}"])
        self.assertEqual(v["close"]["lands"], ["desk/{folder}", "filing-cabinet/{folder}"])
        self.assertEqual(v["reopen"]["lands"], ["filing-cabinet/{folder}", "desk/{folder}"])
        self.assertEqual(v["sessions"]["lands"], ["desk/{folder}/folder.md", "filing-cabinet/{folder}/folder.md"])

    def test_the_doctrine_says_what_the_verbs_now_do(self):
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        for words in ("one-writer rule", "nothing ever numbers it after the fact", "folder is opened in four answers",
                      "explains the field when the answer is `?`", "no folder is ever dropped from the desk",
                      "walks git's history of every filed page"):
            self.assertIn(words, doctrine)


if __name__ == "__main__":
    unittest.main()
