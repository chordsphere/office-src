"""Tests for office-src 0.48.0: office ask, the quick path.

One class per item of the brief (2026-11-05-m10-ask-001):

1. the ask sent (office ask): the tray's files, the brief's words, the
   opener's words, no bale verb run, the project asked only when the
   words name none (piped refused, on a terminal by key);
2. the block filed (office ask --learned): the notepad page, the
   chapter's facts with the ask's name, the Q&A lines after the answer,
   a bad block refused by name, a block for no ask out refused,
   --learned none, and the sittings' window that leaves an ask's page out;
3. bare office ask on a terminal with a LEARNED block on the clipboard
   files it, and asks its question when the clipboard holds anything else;
4. the walk-in, office status and the home screen show an ask out;
5. the editor's opt-out: machine.toml's editor = "" against VISUAL set,
   and editor = "CMD" over VISUAL;
6. bare_fact on the ask's name;
7. office tray on an ask's tray;
8. the doctrine, the README, the catalog and the release say it.

The world is tests/test_land.py's LandCase: an office scoping alpha, with a
fake bale whose every call is logged, so "no bale verb ran" is the logs
unchanged. The questions, facts and names are invented. The terminal
classes run in the serial lane. Run with the rest of the suite:

    tests/run.sh test_ask
"""

import json
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env  # noqa: E402
from test_land import LandCase  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_answer_review import KEEP, an_editor  # noqa: E402

import office_ask as oa  # noqa: E402
import office_helper as oh  # noqa: E402
import office_home as hs  # noqa: E402
import office_sort as osort  # noqa: E402

QUESTION = "Does the alpha picklist endpoint cache its options?"
SID_SHAPE = re.compile(r"\b\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*-\d{3}\b")


def flat(text):
    return " ".join(text.split())


def learned(name, answer="No: every call reads the schema.", handbook=None, qa=None, extra=""):
    """A LEARNED block in the brief's shape, inside a four-backtick fence."""
    parts = [f"--- LEARNED BEGIN {name} ---", "", "## Answer", "", answer, ""]
    if handbook:
        parts += ["## Handbook", ""]
        for project, facts in handbook.items():
            parts += [f"### {project}", "", *[f"- {f}" for f in facts], ""]
    if qa:
        parts += ["## Questions and answers", "", *qa, ""]
    parts += [extra] if extra else []
    parts += ["--- LEARNED END ---"]
    return "Here is what I learned:\n\n````\n" + "\n".join(parts) + "\n````\n"


class AskCase(LandCase):
    """LandCase's office, the out tray at its default (~/out-tray)."""

    def setUp(self):
        super().setUp()
        self.tray_root = self.e.home / "out-tray"
        self.machine = self.e.home / ".config" / "office-src" / "machine.toml"

    def bale_logs(self):
        return [p.read_text() if p.is_file() else None for p in (self.fake.calls, self.fake.dir / "pack-calls.jsonl")]

    def ask(self, *args, check=0):
        return self.run_office("ask", *args, check=check)

    def sent(self, words=QUESTION, *flags):
        proc = self.ask("--words", words, *flags)
        name = re.search(r"^Out tray: \S+/(ask-\S+)$", proc.stdout, re.M).group(1)
        return name, proc

    def file_text(self, text, *more, check=0):
        path = self.e.tmp / "learned.txt"
        path.write_text(text)
        return self.ask("--learned", str(path), *more, check=check)


# --- 1. the ask sent -------------------------------------------------------------------------

class TestTheAskSent(AskCase):
    def test_piped_it_writes_the_tray_and_runs_no_bale(self):
        before, head = self.bale_logs(), self.subjects(1)
        proc = self.ask("--words", QUESTION)
        name = re.search(r"^Out tray: \S+/(ask-\S+)$", proc.stdout, re.M).group(1)
        self.assertRegex(name, r"^ask-\d{4}-\d{2}-\d{2}-does-the-alpha-picklist-endpoint-cache$")
        self.assertIn("your words name alpha, one of this office's projects: the ask is on it", proc.stderr)
        tray = self.tray_root / name
        self.assertEqual(sorted(p.name for p in tray.iterdir()), ["OFFICE.md", "ask-brief.md", "profile.md"])
        self.assertEqual((tray / "OFFICE.md").read_bytes(), (REPO / "doctrine/OFFICE.md").read_bytes())
        self.assertEqual((tray / "profile.md").read_bytes(), (self.root / "profile.md").read_bytes())
        brief = (tray / "ask-brief.md").read_text()
        said = flat(brief)
        self.assertIn(f"> {QUESTION}\n", brief)
        self.assertIn("It is on alpha, one of this office's projects.", said)
        self.assertIn("Office context informs this answer but never lands in a project.", said)
        self.assertIn("    office letterhead check FILE\n", brief)
        self.assertIn(f"--- LEARNED BEGIN {name} ---", brief)
        self.assertIn("No handbook chapter for alpha rides", said)
        self.assertIn("no Sort for a drop", said)
        # The opener: printed between its own lines, kept beside the tray,
        # no session id and no bale line in it.
        opener = re.search(r"--8<-- ask opener --8<--\n(.*)\n--8<-- end ask opener --8<--", proc.stdout, re.S).group(1)
        self.assertEqual((self.tray_root / f"{name}.opener.txt").read_text(), opener + "\n")
        self.assertIn(f"office ask {name}:", opener)
        self.assertIn("Read ask-brief.md first", opener)
        self.assertIsNone(SID_SHAPE.search(opener))
        self.assertNotIn("bale", opener)
        self.assertIn(f"office tray {name} opens the tray and prints the opener again", proc.stderr)
        self.assertIn("run office ask --learned", proc.stderr)
        record = json.loads((self.tray_root / f"{name}.ask.json").read_text())
        self.assertEqual((record["project"], record["words"], record["office"]),
                         ("alpha", QUESTION, str(self.root.resolve())))
        # No bale verb ran, and nothing was written or committed in the office.
        self.assertEqual(self.bale_logs(), before)
        self.assertEqual(self.subjects(1), head)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_the_chapter_and_the_letterhead_ride_when_the_office_has_them(self):
        (self.root / "handbook").mkdir(exist_ok=True)
        (self.root / "handbook/alpha.md").write_text("# alpha\n\n## Front sheet\n\nx\n\n## Facts\n")
        (self.root / "letterhead").mkdir(exist_ok=True)
        (self.root / "letterhead/voice.md").write_text("# Voice\n\n## In the occupant's words\n\nShort.\n")
        (self.root / "letterhead/forbidden.txt").write_text("# list\n")
        name, _ = self.sent()
        tray = self.tray_root / name
        self.assertEqual(sorted(p.name for p in tray.iterdir()),
                         ["OFFICE.md", "ask-brief.md", "handbook-alpha.md", "letterhead-forbidden.txt",
                          "letterhead-voice.md", "profile.md"])
        brief = flat((tray / "ask-brief.md").read_text())
        self.assertIn("Read the handbook chapter before you answer", brief)
        self.assertIn("alpha declares no audience, so nothing here is written for one.", brief)

    def test_the_voice_page_words_ride_in_the_brief_for_a_project_with_an_audience(self):
        project = {"name": "alpha", "audience": "origin"}
        with self.e.this_process():
            (self.root / "letterhead").mkdir(exist_ok=True)
            self.assertIn("The voice page is missing", oa.voice_words(self.root, project))
            (self.root / "letterhead/voice.md").write_text((REPO / "templates/letterhead-voice.md").read_text())
            self.assertIn("The voice page holds no words of his yet", oa.voice_words(self.root, project))
            (self.root / "letterhead/voice.md").write_text("# Voice\n\n## In the occupant's words\n\nPlain words.\nNo hype.\n")
            words = oa.voice_words(self.root, project)
        self.assertIn("alpha has an audience (origin): before you write anything for it, read the letterhead's "
                      "voice page", words)
        self.assertTrue(words.endswith("> Plain words.\n> No hype."), words)
        self.assertEqual(oa.voice_words(self.root, None),
                         "The office itself has no audience, so nothing here is written for one.")

    def test_the_project_is_asked_only_when_the_words_name_none(self):
        proc = self.ask("--words", "Why does the nightly job skip Sundays?", check=1)
        self.assertIn("say what the question is on: --project NAME (alpha) or --in-office", proc.stderr)
        self.assertFalse(self.tray_root.exists())
        name, proc = self.sent("Why does the nightly job skip Sundays?", "--in-office")
        self.assertIn("It is on the office itself, no project.", flat((self.tray_root / name / "ask-brief.md").read_text()))
        self.assertNotIn("your words name", proc.stderr)
        name, _ = self.sent("Why does the nightly job skip Sundays?", "--project", "alpha")
        self.assertTrue(name.endswith("-2"), name)
        self.assertEqual(json.loads((self.tray_root / f"{name}.ask.json").read_text())["project"], "alpha")
        proc = self.ask("--words", "x", "--project", "beta", check=1)
        self.assertIn("--project beta: none of this office's projects (alpha", proc.stderr)
        proc = self.ask("--words", "x", "--project", "alpha", "--in-office", check=1)
        self.assertIn("--project and --in-office are two answers", proc.stderr)
        proc = self.ask(check=1)
        self.assertIn("office ask takes the question in your words: --words TEXT", proc.stderr)
        # Words after ask are the question, as office note's are.
        proc = self.run_office("ask", "does", "alpha", "cache?", check=0)
        self.assertRegex(proc.stdout, r"Out tray: \S+/ask-\d{4}-\d{2}-\d{2}-does-alpha-cache\n")


class TestTheAskOnATerminal(AskCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_the_words_then_the_project_by_key_and_nothing_else(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "ask"], self.root, self.e.env, [
            (b"Your question, in your own words (--words) [several lines", "Why does the nightly job skip Sundays?\n"),
            (KEEP, ""),
            (b"What the question is on, by its key (--project NAME or --in-office)", "1"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("This office's projects:", seen)
        name = re.search(r"Out tray: \S+/(ask-\S+)\r?\n", seen).group(1)
        record = json.loads((self.tray_root / f"{name}.ask.json").read_text())
        self.assertEqual((record["project"], record["words"]), ("alpha", "Why does the nightly job skip Sundays?"))
        # Words that name the project: nothing but the words is asked.
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "ask"], self.root, self.e.env, [
            (b"Your question, in your own words (--words) [several lines", f"{QUESTION}\n"),
            (KEEP, ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("What the question is on", seen)


# --- 2. the block filed ----------------------------------------------------------------------

class TestTheBlockFiled(AskCase):
    def test_the_page_the_facts_and_the_answers_each_said_and_the_tray_gone(self):
        name, _ = self.sent()
        before = self.bale_logs()
        text = learned(name, answer="No: every call reads the schema.\n\n```\nGET /picklist\n```",
                       handbook={"alpha": [f"the endpoint reads the schema's enum ({name})",
                                           "2026-11-05: options are never cached"]},
                       qa=["- 2026-11-05 is it urgent? yes, a coworker is blocked"])
        proc = self.file_text(text)
        page = self.root / oa.page_rel(name)
        self.assertEqual(oa.page_rel(name), f"notepad/{name[4:14]}-ask-{name[15:]}.md")
        body = page.read_text()
        words_at, answer_at, qa_at = (body.index(QUESTION), body.index("No: every call reads the schema."),
                                      body.index("- 2026-11-05 is it urgent?"))
        self.assertTrue(words_at < answer_at < qa_at, body)
        self.assertTrue(body.startswith(f"# {name[4:14]}: ask {name}, on alpha\n"), body[:80])
        self.assertIn("```\nGET /picklist\n```\n", body)
        self.assertIn("\n## Questions and answers\n\n- 2026-11-05 is it urgent? yes, a coworker is blocked\n", body)
        chapter = (self.root / "handbook/alpha.md").read_text()
        self.assertRegex(chapter, rf"- \d{{4}}-\d{{2}}-\d{{2}}: the endpoint reads the schema's enum \({name}\)\n")
        self.assertRegex(chapter, rf"- \d{{4}}-\d{{2}}-\d{{2}}: options are never cached \({name}\)\n")
        self.assertNotIn(f"({name}) ({name})", chapter)
        self.assertEqual(osort.chapter_problems(self.root / "handbook/alpha.md"), [])
        err = flat(proc.stderr)
        self.assertIn("the handbook arrives in this office", err)
        self.assertIn(f"handbook/alpha.md: 2 fact(s) from {name}", err)
        self.assertIn("came with a date or the ask's name of their own, dropped before filing, since office ask "
                      "adds both", err)
        self.assertIn("1 question(s) and answer(s), after the answer", err)
        self.assertIn(f"filed {name} from file learned.txt as {oa.page_rel(name)}; its out tray is gone", err)
        # Two commits, each passing the notepad's append check; the tray, its
        # opener's copy and its record gone; no bale verb ran.
        self.assertEqual(self.subjects(2), [f"office ask: {name}'s questions and answers",
                                            f"office ask: filed {name} (its page and facts)"])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertFalse(any(self.tray_root.iterdir()), list(self.tray_root.iterdir()))
        self.assertEqual(self.bale_logs(), before)
        # Filed twice: refused by name, nothing written.
        proc = self.file_text(text, check=1)
        self.assertIn(f"{name} is filed already, as {oa.page_rel(name)}", proc.stderr)

    def test_a_block_with_only_an_answer_files_the_page_alone(self):
        name, _ = self.sent()
        proc = self.file_text(learned(name))
        self.assertIn("no Handbook section, so no fact is filed", proc.stderr)
        self.assertIn("no Questions and answers section", proc.stderr)
        self.assertFalse((self.root / "handbook/alpha.md").exists())
        self.assertEqual(self.subjects(1), [f"office ask: filed {name} (its page and facts)"])

    def test_a_block_that_does_not_read_is_refused_by_name_and_nothing_is_written(self):
        name, _ = self.sent()
        cases = (
            (learned(name).replace("## Answer", "## Reply"), "`## Reply` is no section of an ask's block"),
            (learned(name, extra="## Sort\n\n### x.md\n"), "`## Sort` is no section of an ask's block"),
            (learned(name, handbook={"beta": ["a fact"]}), "`### beta` is none of this office's projects (alpha)"),
            (learned(name, handbook={"alpha": ["a fact"]}).replace("- a fact", "#### Front sheet\n\nwords"),
             "a Front sheet is a session's to write"),
            (learned(name, handbook={"alpha": ["a fact"]}).replace("- a fact", "a fact"), "each fact is a `- ` line"),
            (learned(name, qa=["- no date here? no"]), "each line under `## Questions and answers` is `- DATE"),
            (learned(name).replace("No: every call reads the schema.", ""), "`## Answer` is empty"),
            (learned(name).replace("--- LEARNED END ---", ""), "a LEARNED BEGIN line with no --- LEARNED END ---"),
            (learned(name).replace(name, "2026-11-05-fix-login-001"), "not `--- LEARNED BEGIN ask-DATE-SLUG ---`"),
            ("just chat\n", "no LEARNED block"),
        )
        for text, why in cases:
            proc = self.file_text(text, check=1)
            self.assertIn(why, proc.stderr, text)
            self.assertIn("nothing was filed from file learned.txt", proc.stderr)
        self.assertFalse((self.root / oa.page_rel(name)).exists())
        self.assertTrue((self.tray_root / name).is_dir())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_a_block_for_no_ask_out_is_refused(self):
        name, _ = self.sent()
        proc = self.file_text(learned("ask-2026-01-01-never-sent"), check=1)
        self.assertIn(f"ask-2026-01-01-never-sent is not an ask out from this office (out: {name})", proc.stderr)
        # Another office's ask, in the same tray root, is not this office's.
        other = self.e.init("other")
        self.e.found(other)
        proc = self.e.run("ask", "--learned", str(self.e.tmp / "learned.txt"), cwd=other, check=1)
        self.assertIn("is not an ask out from this office (out: none)", proc.stderr)
        proc = self.e.run("ask", "--learned", "-", cwd=self.root, input=learned(name), check=0)
        self.assertIn(f"filed {name} from stdin", proc.stderr)

    def test_the_learned_none_ends_it_with_the_page_alone(self):
        name, _ = self.sent()
        proc = self.ask("--learned", "none", check=0)
        self.assertIn(f"ended {name} with nothing filed", proc.stderr)
        body = (self.root / oa.page_rel(name)).read_text()
        self.assertIn(QUESTION, body)
        self.assertIn("with nothing filed (office ask --learned none)", body)
        self.assertEqual(self.subjects(1), [f"office ask: ended {name} with nothing filed"])
        self.assertFalse((self.tray_root / name).exists())
        proc = self.ask("--learned", "none", check=1)
        self.assertIn("no ask is out from this office", proc.stderr)
        first, _ = self.sent()
        second, _ = self.sent()
        proc = self.ask("--learned", "none", check=1)
        self.assertIn(f"several asks are out ({first}, {second}): name one", proc.stderr)
        self.ask("--learned", "none", second, check=0)
        self.assertTrue((self.tray_root / first).is_dir())

    def test_a_fence_around_the_block_and_inside_the_answer_reads_and_the_last_block_counts(self):
        name = "ask-2026-11-05-q"
        text = ("chat\n" + learned(name, answer="first") + "\nmore\n    "
                + learned(name, answer="Use:\n\n```\n## not a heading\n```", qa=["- 2026-11-05 a? b"]).replace("\n", "\r\n    "))
        b = oa.read_block(text, ["alpha"])
        self.assertEqual(b["name"], name)
        self.assertEqual(b["answer"], ["Use:", "", "```", "## not a heading", "```"])
        self.assertEqual(b["qa"], ["- 2026-11-05 a? b"])
        self.assertEqual(oa.name_of(text), name)
        self.assertIsNone(oa.name_of("nothing"))

    def test_the_sittings_window_leaves_an_asks_page_out(self):
        import office_watches as ow
        name, _ = self.sent()
        self.file_text(learned(name))
        with self.e.this_process():
            pages = [f[1] for f in ow.sitting_filings(self.root) or []]
        self.assertNotIn(oa.page_rel(name), pages)
        self.assertTrue(oh.SITTING_PAGE_RE.match(oa.page_rel(name)))


# --- 3. bare office ask, a block on the clipboard ---------------------------------------------

class TestBareAskFilesTheClipboard(AskCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def clipboard(self, text):
        clip = self.e.tmp / "clipboard.txt"
        clip.write_text(text)
        self.machine.parent.mkdir(parents=True, exist_ok=True)
        self.machine.write_text(f'paste_command = "cat {clip}"\n')

    def test_a_block_naming_an_ask_out_is_filed_without_a_question(self):
        name, _ = self.sent()
        self.clipboard(learned(name, handbook={"alpha": ["a bare fact"]}))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "ask"], self.root, self.e.env, [])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"the clipboard holds {name}'s LEARNED block, an ask out from this office: filing it", flat(seen))
        self.assertNotIn("Your question", seen)
        self.assertTrue((self.root / oa.page_rel(name)).is_file())
        self.assertIn(f"a bare fact ({name})", (self.root / "handbook/alpha.md").read_text())

    def test_anything_else_on_the_clipboard_and_the_question_is_asked(self):
        self.sent()
        self.clipboard(learned("ask-2026-01-01-not-out") + "\n")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "ask"], self.root, self.e.env, [
            (b"Your question, in your own words (--words) [several lines", f"{QUESTION}\n"),
            (KEEP, ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertEqual(len(list(self.tray_root.glob("ask-*.ask.json"))), 2)


# --- 4. the walk-in, office status and the home screen ---------------------------------------

class TestAnAskOutIsShown(AskCase):
    def test_the_walk_in_and_status_say_it_and_stop_once_it_is_filed(self):
        name, _ = self.sent()
        page = self.e.run(cwd=self.root, check=0).stdout   # office alone, piped: the walk-in's page
        self.assertIn("Asks out (a quick question each, answered in a chat; office ask --learned files its block):", page)
        self.assertIn(f"  {name} (alpha), asked ", page)
        self.assertIn(f"office tray {name} opens its tray again", page)
        status = self.run_office("status", check=None).stdout
        self.assertIn(f"asks:       1 out: {name} (alpha); office ask --learned files each one's LEARNED block",
                      status)
        self.file_text(learned(name))
        self.assertNotIn("Asks out", self.e.run(cwd=self.root, check=0).stdout)
        self.assertNotIn("asks:", self.run_office("status", check=None).stdout)

    def test_the_home_screen_offers_the_filing_key_and_names_the_tray_verb(self):
        name, _ = self.sent()
        with self.e.this_process():
            items = hs.ask_items(self.root, self.tray_root)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["argv"], ["ask", "--learned"])
        self.assertEqual(items[0]["label"], f"File what {name} learned (alpha): its LEARNED block, from the "
                                            f"clipboard (office tray {name} opens its tray again)")
        keys = {k: (words, argv) for k, words, _, argv in hs.FIXED_KEYS}
        self.assertEqual(keys["i"], ("a quick question, in your words, answered in a chat", ["ask"]))
        lines, menu = hs.render_page([("alpha", "nothing landed yet")], items, 0)
        self.assertIn("[i] a quick question, in your words, answered in a chat", "\n".join(lines))
        self.assertIn(("1", "office", ["ask", "--learned"]), menu)


# --- 5. the editor's opt-out ------------------------------------------------------------------

class TestTheEditorsOptOut(AskCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def machine_toml(self, line):
        self.machine.parent.mkdir(parents=True, exist_ok=True)
        self.machine.write_text(line + "\n")

    def test_editor_empty_keeps_the_answer_at_the_prompt_though_visual_is_set(self):
        editor, seed = an_editor(self.e.tmp, "Not these words\\n")
        self.e.env.update(VISUAL=str(editor), EDITOR=str(editor), TERM="xterm")
        self.machine_toml('editor = ""')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "ask", "--in-office"], self.root, self.e.env, [
            (b"Your question, in your own words (--words) [several lines", "Why the Sundays?\n"),
            (KEEP, ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertFalse(seed.exists())
        self.assertNotIn("taking your answer in", seen)
        self.assertIn("Your answer, as it stands:", seen)

    def test_editor_cmd_takes_the_answer_over_visual(self):
        editor, seed = an_editor(self.e.tmp, "Why the Sundays?\\n")
        self.e.env.update(VISUAL="false", EDITOR="false", TERM="xterm")
        self.machine_toml(f'editor = "{editor} --wait"')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "ask", "--in-office"], self.root, self.e.env, [])
        self.assertEqual(code, 0, seen)
        self.assertTrue(seed.exists())
        self.assertIn(f"taking your answer in {editor} --wait (machine.toml's editor;", flat(seen))
        self.assertNotIn("false exited", seen)
        name = re.search(r"Out tray: \S+/(ask-\S+)\r?\n", seen).group(1)
        self.assertEqual(json.loads((self.tray_root / f"{name}.ask.json").read_text())["words"], "Why the Sundays?")


class TestTheEditorsWords(unittest.TestCase):
    def test_review_help_the_log_line_and_the_helper_say_it(self):
        text = (REPO / "bin/office").read_text()
        help_line = next(l for l in text.splitlines() if l.startswith("REVIEW_HELP="))
        self.assertIn('editor = \\"\\" keeps every answer here at the prompt', help_line)
        self.assertIn('editor = \\"CMD\\" takes it in CMD over VISUAL and EDITOR', help_line)
        self.assertIn('editor = \\"\\" in $MACHINE_FILE keeps it at the prompt', text)
        e = Env(self)
        machine = e.tmp / "machine.toml"
        with e.this_process():
            self.assertIsNone(oh.machine_string(machine, oh.EDITOR_KEY))
            machine.write_text('editor = ""\n')
            self.assertEqual(oh.machine_string(machine, oh.EDITOR_KEY), "")


# --- 6. bare_fact on the ask's name -----------------------------------------------------------

class TestBareFactOnTheAsksName(unittest.TestCase):
    def test_the_asks_name_and_its_slug_are_dropped_and_another_asks_kept(self):
        ask = "ask-2026-11-05-picklist-endpoint"
        self.assertEqual(osort.bare_fact(f"reads the enum ({ask})", ask), "reads the enum")
        self.assertEqual(osort.bare_fact("2026-11-05: reads the enum (picklist-endpoint)", ask), "reads the enum")
        self.assertEqual(osort.bare_fact(f"reads the enum ({ask}) ({ask})", ask), "reads the enum")
        self.assertEqual(osort.bare_fact("reads the enum (ask-2026-11-01-other)", ask),
                         "reads the enum (ask-2026-11-01-other)")
        self.assertEqual(osort.bare_fact(f"reads the enum ({ask})", "2026-11-05-fix-login-001"),
                         f"reads the enum ({ask})")
        line = osort.fact_line("2026-11-05", f"reads the enum ({ask})", ask)
        self.assertEqual(line, f"- 2026-11-05: reads the enum ({ask})")
        self.assertEqual(osort.fact_key(line), ("reads the enum", ask))
        self.assertTrue(osort.FACT_LINE_RE.match(line))


# --- 7. office tray on an ask's tray ----------------------------------------------------------

class TestTheTrayOfAnAsk(AskCase):
    def test_by_name_and_bare_it_opens_and_prints_the_opener_and_a_filed_ask_has_none(self):
        name, _ = self.sent()
        for args in ((name,), ()):
            proc = self.run_office("tray", *args, check=0)
            self.assertIn(f"Out tray for {name}: {self.tray_root / name}\n", proc.stdout)
            self.assertIn("  ask-brief.md\n", proc.stdout)
            self.assertIn("--8<-- ask opener --8<--\noffice ask " + name, proc.stdout)
            self.assertIn("run office ask --learned", proc.stderr)
        self.file_text(learned(name))
        proc = self.run_office("tray", name, check=1)
        self.assertIn(f"no out tray for {name}", proc.stderr)


# --- 8. the record ----------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_doctrine_the_readme_the_catalog_and_the_release_say_it(self):
        doctrine = (REPO / "doctrine/OFFICE.md").read_text()
        lines = doctrine.splitlines()
        self.assertTrue(lines[298].startswith("> **PAST THE CORE.**"))
        core, past = "\n".join(lines[:299]), flat("\n".join(lines[299:]))
        self.assertTrue("office ask" in core, "the doctrine's core names office ask")
        when = past.split("## 8. When to open a session", 1)[1].split("## 10.", 1)[0]
        self.assertIn("office ask", when)
        self.assertIn("--- LEARNED BEGIN", when)
        verbs = past.split("## 7. Verbs", 1)[1].split("## 8.", 1)[0]
        self.assertIn("| ask | script (0.48.0):", verbs)
        readme = flat((REPO / "README.md").read_text())
        self.assertIn("| `office ask` |", readme)
        self.assertIn('`editor = ""`', readme)
        catalog = oh.read_toml(REPO / "share/verbs.toml")["verbs"]["ask"]
        self.assertEqual((catalog["kind"], catalog["surface"], catalog["writes"], catalog["lands"]),
                         ("script", "occupant", ["notepad", "handbook"], ["notepad", "handbook"]))
        releases = (REPO / "RELEASES.md").read_text()
        entry = releases.split("## 0.48.0", 1)[1].split("\n## ", 1)[0]
        self.assertIn("tests/test_ask.py", entry)
        # The release that shipped the ask, or a later one (0.49.0: an equal
        # pin failed at the next release).
        version = tuple(int(n) for n in (REPO / "VERSION").read_text().strip().split("."))
        self.assertGreaterEqual(version, (0, 48, 0))

    def test_the_template_names_invented_projects_and_its_placeholders_are_filled(self):
        text = (REPO / "templates/ask-brief.md").read_text()
        self.assertIn("### alpha", text)
        e = Env(self)
        root = e.tmp / "office"
        (root / "floor-plan").mkdir(parents=True)
        (root / "floor-plan/manifest.toml").write_text('[office]\nname = "t"\n')
        words = e.tmp / "w"
        words.write_text("Why?\n")
        with e.this_process():
            got = oa.send(root, e.tmp / "trays", "Why?", "why", "2026-11-05", "09:00")
        brief = (pathlib.Path(got["tray"]) / "ask-brief.md").read_text()
        self.assertNotIn("{{", brief)
        self.assertEqual(got["files"], ["ask-brief.md", "OFFICE.md"])


if __name__ == "__main__":
    unittest.main()
