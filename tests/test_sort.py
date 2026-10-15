"""Tests for the return of a sort (0.20.0): office land filing a session's
Sort, Questions and answers and Handbook sections; office moves applying
the in-tray's sorted drops; office open --goal and office start N sending
a folder out with its goal and brief; the handbook and its chapters; and
office start --sort, the standalone sort, out and back.

bale is never needed: the landing tests run the fake bale of
tests/test_land.py, whose every line is built from captured bale output.
Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import json
import os
import pathlib
import re
import shutil
import sys
import tarfile
import tempfile
import textwrap
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_land import LandCase, response_tarball  # noqa: E402
from test_start import tar_names  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)
import office_drop as odrop  # noqa: E402
import office_sort as osort  # noqa: E402

DOCTRINE = REPO / "doctrine" / "OFFICE.md"
TEMPLATES = REPO / "templates"
MESSAGE = "Could you look at the login page?\nIt shows an error on narrow screens.\n"
OTHER = "The invoices page is slow\nIt takes a minute to load.\n"
DAY_RE = r"\d{4}-\d{2}-\d{2}"


def fenced(text, after):
    """The first fenced block after the line holding `after`, dedented."""
    rest = text.split(after, 1)[1]
    m = re.search(r"^( *)```\n(.*?)^\1```$", rest, re.M | re.S)
    return textwrap.dedent(m.group(2))


def sort_block(name, project="alpha", folder="new", facts=("- facts: none",), brief="Fix the error on narrow screens.",
               goal="Fix the login page's error on narrow screens", tell="the sender, in reply: fixed in the next release"):
    lines = [f"### {name}", "", f"- project: {project}", f"- folder: {folder}", f"- goal: {goal}", "- size: small",
             f"- tell: {tell}", *facts]
    if brief is not None:
        lines += ["", "#### Brief", "", brief]
    return "\n".join(lines) + "\n"


# --- notes.md, read --------------------------------------------------------------------------

class TestTheNotes(unittest.TestCase):
    def test_the_three_sections_are_read_and_a_fenced_heading_is_never_one(self):
        notes = ("# Notes\n\n```\n## Sort\n\n### 2026-01-01-fake.md\n```\n\n## Sort\n\n"
                 + sort_block("2026-10-14-login.md", facts=("- facts:", "- the api serves it", "- on port 8080"))
                 + "\n## Questions and answers\n\n- 2026-10-14 Keep the old route? yes\nprose is left out\n"
                 + "\n## Handbook\n\n### alpha\n\n- one fact\n\n#### Front sheet\n\nalpha is the app.\n\n"
                 + "## Walkthrough\n\nx\n")
        n = osort.parse_notes(notes)
        (s,) = n["sorts"]
        self.assertEqual(s["problems"], [])
        self.assertEqual(s["name"], "2026-10-14-login.md")
        self.assertEqual(s["facts"], ["the api serves it", "on port 8080"])
        self.assertEqual(s["brief"], ["Fix the error on narrow screens."])
        self.assertEqual(s["field_lines"][-3:], ["- facts:", "- the api serves it", "- on port 8080"])
        self.assertEqual(n["qa"], ["- 2026-10-14 Keep the old route? yes"])
        self.assertEqual(n["qa_other"], 1)
        self.assertEqual(n["handbook"], [("alpha", ["one fact"], ["alpha is the app."])])
        self.assertEqual(osort.parse_notes("# Notes\n\n## Walkthrough\n\nx\n"),
                         {"sorts": None, "qa": None, "qa_other": 0, "handbook": None, "structure": None})

    def test_a_subsection_off_the_format_is_refused_with_why(self):
        def problems(block):
            (s,) = osort.parse_notes("## Sort\n\n" + block)["sorts"]
            return " ".join(s["problems"])
        self.assertIn("one each and in that order",
                      problems(sort_block("2026-10-14-a.md").replace("- size: small\n", "")))
        self.assertIn("needs a #### Brief", problems(sort_block("2026-10-14-a.md", brief=None)))
        self.assertEqual(problems(sort_block("2026-10-14-a.md", folder="7", brief=None)), "")
        self.assertEqual(problems(sort_block("2026-10-14-a.md", folder="folder 7", brief=None)), "")
        self.assertIn("folder: is new or a folder number", problems(sort_block("2026-10-14-a.md", folder="soon")))
        self.assertIn("does not name a drop's page", problems(sort_block("notes.md")))
        self.assertIn("facts: is none or fact lines", problems(sort_block("2026-10-14-a.md", facts=("- facts:",))))
        self.assertIn("says none", problems(sort_block("2026-10-14-a.md", facts=("- facts: none", "- x"))))
        (s,) = osort.parse_notes("## Sort\n\n" + sort_block("2026-10-14-a.md", facts=("- facts: one inline",)))["sorts"]
        self.assertEqual(s["facts"], ["one inline"])

    def test_the_sort_session_is_known_by_its_slug(self):
        self.assertTrue(osort.is_sort_sid(f"2026-10-14-{osort.SORT_SLUG}-001"))
        self.assertFalse(osort.is_sort_sid("2026-10-14-fix-login-001"))
        self.assertFalse(osort.is_sort_sid(None))


# --- the pinned blocks, held to the code that writes them -------------------------------------

class TestThePinnedBlocks(unittest.TestCase):
    def setUp(self):
        self.doctrine = DOCTRINE.read_text(encoding="ascii")
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_the_pages_sort_section_is_one_block_and_the_code_writes_it(self):
        core = fenced(self.doctrine, "`#### Brief` (values illustrative)")
        tray = fenced((TEMPLATES / "in-tray-README.md").read_text(), "status to sorted (values\nillustrative)")
        self.assertEqual(core, tray)
        # A drop's page, sorted by the code, ends in exactly that block.
        page, _ = odrop.render_page(MESSAGE, "alpha", "stdin", "2026-10-14 09:12")
        (self.tmp / "in-tray").mkdir()
        rel = "in-tray/2026-10-14-alpha-login-error.md"
        (self.tmp / rel).write_text(page)
        (s,) = osort.parse_notes("## Sort\n\n" + sort_block(
            "2026-10-14-alpha-login-error.md", brief="<the subsection's Brief, verbatim>"))["sorts"]
        state, got, _ = osort.file_sort(self.tmp, s, "2026-10-14-alpha-login-error-001", "2026-10-14")
        self.assertEqual((state, got), ("filed", rel))
        text = (self.tmp / rel).read_text()
        self.assertTrue(text.endswith("\n\n" + core), text)
        self.assertIn("- status: sorted\n", text)
        parsed = odrop.parse_page(text)
        self.assertEqual(parsed["problems"], [])
        self.assertEqual(parsed["text"], MESSAGE.rstrip("\n"))
        back = osort.page_sort(parsed["sort_lines"])
        self.assertEqual((back["sid"], back["fields"]["folder"], back["brief"], back["problems"]),
                         ("2026-10-14-alpha-login-error-001", "new", ["<the subsection's Brief, verbatim>"], []))
        # Sorted once: a second filing leaves the page as it is.
        state, _, words = osort.file_sort(self.tmp, s, "2026-10-15-other-001", "2026-10-15")
        self.assertEqual(state, "already")
        self.assertIn("sorted already", words)
        self.assertEqual((self.tmp / rel).read_text(), text)

    def test_the_chapter_is_one_block_and_the_code_writes_it(self):
        core = fenced(self.doctrine, "in two parts (values illustrative)")
        front = fenced((TEMPLATES / "handbook-README.md").read_text(), "in this shape (values illustrative)")
        self.assertEqual(core, front)
        path = self.tmp / "alpha.md"
        path.write_text(osort.render_chapter("alpha"))
        self.assertEqual(osort.chapter_problems(path), [])
        lines = core.splitlines()
        osort.set_front_sheet(path, [lines[4]])
        osort.append_facts(path, [osort.fact_line("2026-10-14", "the login page is served by the api's static route",
                                                  "2026-10-14-alpha-login-error-001")])
        self.assertEqual(path.read_text(), core)
        self.assertEqual(osort.chapter_problems(path), [])
        path.write_text(core.replace("(2026-10-14-alpha-login-error-001)", ""))
        self.assertIn("a Facts line is not", " ".join(osort.chapter_problems(path)))

    def test_the_briefs_carry_the_doctrines_sort_format(self):
        core = fenced(self.doctrine, "key on its own line, in this order")
        for name in ("drop-brief.md", "sort-brief.md"):
            self.assertEqual(fenced((TEMPLATES / name).read_text(), "in\nthis order (values illustrative)"), core, name)
        brief = (TEMPLATES / "sort-brief.md").read_text()
        for key in ("{{count}}", "{{drops}}", "{{desk}}", "{{moves}}"):
            self.assertIn(key, brief)


# --- the filing, in an office on disk ------------------------------------------------------------

class TestFiling(unittest.TestCase):
    """file_notes on a small office written by hand: no bale, no command."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        root = self.root = self.tmp / "office"
        (root / "floor-plan").mkdir(parents=True)
        (root / "floor-plan/manifest.toml").write_text(
            '[office]\nname = "t"\n\n[spaces.desk]\npath = "desk"\nhung = false\nfiled = false\n')
        (root / "bale.toml").write_text('[pack]\ninclude_group = "hung"\ninclude_group_triggers = ["desk"]\n'
                                        'include_group_pulls = ["profile.md"]\n')
        folder = root / "desk/2026-10-14-job"
        folder.mkdir(parents=True)
        (folder / "folder.md").write_text(h.render_template((TEMPLATES / "folder.md").read_text(), {
            "title": "job", "number": "1", "status": "open", "queued": "2026-10-14",
            "history": "2026-10-14 queued: office open"}))
        (folder / "drops").mkdir()
        page, _ = odrop.render_page(MESSAGE, "alpha", "stdin", "2026-10-14 09:12")
        (folder / "drops/2026-10-14-login.md").write_text(page)

    def test_sort_answers_and_facts_land_where_the_doctrine_says(self):
        notes = ("## Sort\n\n" + sort_block("2026-10-14-login.md", folder="1", brief=None,
                                            facts=("- facts:", "- the api serves the page"))
                 + sort_block("2026-10-14-gone.md")
                 + "\n## Questions and answers\n\n- 2026-10-14 Keep it? yes\n"
                 + "\n## Handbook\n\n### Alpha\n\n- port 8080\n\n#### Front sheet\n\nalpha is the app.\n"
                 + "\n### beta\n\n- not ours\n")
        said, changed = osort.file_notes(self.root, notes, "2026-10-14-job-001", "2026-10-15", "desk/2026-10-14-job",
                                         ["alpha"])
        text = "\n".join(said)
        self.assertIn("Sort: 2 subsection(s) in 2026-10-14-job-001's notes.md, 1 filed", text)
        self.assertIn("### 2026-10-14-gone.md names a page that is not in the in-tray or desk/2026-10-14-job/drops/",
                      text)
        self.assertIn("### beta is none of this office's projects (alpha)", text)
        md = (self.root / "desk/2026-10-14-job/folder.md").read_text()
        qa = md.split("## Questions and answers", 1)[1].split("\n## ", 1)[0]
        self.assertTrue(qa.endswith("dated.\n\n- from 2026-10-14-job-001:\n- 2026-10-14 Keep it? yes\n"), qa)
        nxt = md.split("## Next", 1)[1].split("\n## ", 1)[0]
        self.assertIn("- tell: the sender, in reply: fixed in the next release (drops/2026-10-14-login.md)\n", nxt)
        chapter = (self.root / "handbook/alpha.md").read_text()
        self.assertIn("## Front sheet\n\nalpha is the app.\n\n## Facts\n\n"
                      "- 2026-10-15: the api serves the page (2026-10-14-job-001)\n"
                      "- 2026-10-15: port 8080 (2026-10-14-job-001)\n", chapter)
        self.assertEqual((self.root / "handbook/README.md").read_text(),
                         (TEMPLATES / "handbook-README.md").read_text())
        plan = tomllib.loads((self.root / "floor-plan/manifest.toml").read_text())
        self.assertEqual(plan["spaces"]["handbook"], {"path": "handbook", "hung": ["handbook/README.md"],
                                                      "filed": False})
        pack = tomllib.loads((self.root / "bale.toml").read_text())["pack"]
        self.assertIn("handbook", pack["include_group_triggers"])
        self.assertIn("handbook/README.md", pack["include_group_pulls"])
        self.assertEqual(sorted(changed), sorted(["desk/2026-10-14-job/drops/2026-10-14-login.md",
                                                  "desk/2026-10-14-job/folder.md", "floor-plan/manifest.toml",
                                                  "bale.toml", "handbook/README.md", "handbook/alpha.md"]))
        self.assertEqual(osort.handbook_check(self.root), (["handbook:   matches the install's catalog; 1 chapter(s)"], 0))
        # A second filing of the same notes sorts nothing twice and adds the facts again, as a session would.
        said, _ = osort.file_notes(self.root, notes, "2026-10-14-job-001", "2026-10-15", "desk/2026-10-14-job", ["alpha"])
        self.assertIn("sorted already", "\n".join(said))

    def test_no_folder_files_no_answers_and_a_handbook_problem_is_named(self):
        said, changed = osort.file_notes(self.root, "## Questions and answers\n\n- 2026-10-14 a? b\n",
                                         "2026-10-14-in-tray-sort-001", "2026-10-14", None, ["alpha"])
        self.assertIn("no folder records 2026-10-14-in-tray-sort-001, so they are not filed", "\n".join(said))
        self.assertEqual(changed, [])
        self.assertEqual(osort.handbook_check(self.root)[1], 0)
        (self.root / "handbook").mkdir()
        (self.root / "handbook/alpha.md").write_text("# beta\n\n## Facts\n\nnot a fact\n")
        lines, problems = osort.handbook_check(self.root)
        self.assertGreaterEqual(problems, 4)
        self.assertIn("README.md is missing", "\n".join(lines))
        self.assertIn("its first line is not '# alpha'", "\n".join(lines))


# --- the Next line's sort rule, as a pure function ------------------------------------------------

class TestTheSortRule(unittest.TestCase):
    def test_a_drop_that_waited_and_a_pile_give_the_sort(self):
        alpha = [{"name": "alpha"}]
        stuck = {"rel": "in-tray/2026-10-10-x.md", "project": "the website"}
        fresh = {"rel": "in-tray/2026-10-12-y.md", "project": None}
        mine = {"rel": "in-tray/2026-10-13-z.md", "project": "alpha"}
        base = {"moves": (0, "", []), "ready": [], "flying": []}
        # Not waited: the drop rule's --lane line, as in 0.19.0.
        g = dict(base, drops=[stuck], drops_waited=set())
        self.assertTrue(ob.next_move("current", True, [], g, alpha, 0)[0].endswith("--lane LANE"))
        # Waited through a session: the sort's.
        g = dict(base, drops=[stuck, mine], drops_waited={stuck["rel"]})
        self.assertEqual(ob.next_move("current", True, [], g, alpha, 0)[0], f"office start --drop {mine['rel']}")
        g["drops"] = [stuck]
        cmd, why = ob.next_move("current", True, [], g, alpha, 0)
        self.assertEqual(cmd, "office start --sort")
        self.assertIn("a session has gone out since it was dropped", why)
        # Three unsorted with nothing ready; not when a folder is ready.
        many = [dict(fresh, rel=f"in-tray/2026-10-1{n}-p.md") for n in range(3)]
        g = dict(base, drops=many, drops_waited=set(), flying=[{"fields": {"lane": ["alpha"]}}])
        self.assertIsNone(ob.drop_move([mine], g, alpha))
        g["drops"] = many + [mine]
        self.assertEqual(ob.sort_move(g["drops"], g, alpha)[0], "office start --sort")
        self.assertIsNone(ob.sort_move(g["drops"], dict(g, ready=[{"name": "x"}]), alpha))
        # A session out wins, as for every rule after it.
        out = [{"sid": "s", "label": ob.OFFICE_LABEL, "folders": [], "held": False}]
        self.assertTrue(ob.next_move("current", True, out, g, alpha, 0)[0].startswith("office land s"))


# --- the doctrine and the declarations -----------------------------------------------------------

class TestDoctrineAndDeclarations(unittest.TestCase):
    def setUp(self):
        self.doctrine = DOCTRINE.read_text(encoding="ascii")

    def test_the_cores_new_bullet_is_twelve_lines_at_most(self):
        lines = self.doctrine.splitlines()
        banner = next(i for i, l in enumerate(lines) if l.startswith("> **PAST THE CORE.**"))
        start = next(i for i, l in enumerate(lines) if l.startswith("- A session writes what the office keeps"))
        end = next(i for i in range(start + 1, banner) if not lines[i].startswith("  "))
        self.assertLess(start, banner)
        self.assertLessEqual(end - start, 12)
        bullet = " ".join(" ".join(lines[start:end]).split())
        for words in ("`## Questions and answers`", "`- DATE question? answer`", "`## Handbook`", "`### PROJECT`",
                      "`office land` files it", "before it asks", "`tell:` lands on its folder's Next"):
            self.assertIn(words, bullet)

    def test_the_verbs_spaces_fields_and_templates_are_declared(self):
        verbs = tomllib.loads((REPO / "share/verbs.toml").read_text())["verbs"]
        self.assertEqual((verbs["sort"]["kind"], verbs["sort"]["built"]), ("office-session", True))
        self.assertIn("drafting-table/moves.md", verbs["sort"]["writes"])
        self.assertIn("in-tray", verbs["moves"]["writes"])
        for path in ("handbook", "in-tray"):
            self.assertIn(path, verbs["land"]["writes"])
        spaces = tomllib.loads((REPO / "share/spaces.toml").read_text())["spaces"]
        self.assertEqual(spaces["handbook"], {"path": "handbook", "hung": ["handbook/README.md"]})
        self.assertIn("| handbook/ | the private layer of documentation | no; arrives with the first fact filed | "
                      "front page | no |", self.doctrine)
        self.assertIn("| sort | office session: the standalone sort", self.doctrine)
        self.assertIn("goal", h.LATE_FIELDS)
        self.assertIn("goal", h.FIELD_HELP)
        self.assertEqual(h.normalize_field("goal", "  Fix   it "), "Fix it")
        for name in ("sort-brief.md", "handbook-README.md", "handbook-chapter.md"):
            self.assertTrue((TEMPLATES / name).is_file(), name)
        self.assertGreaterEqual(h.compare_versions((REPO / "VERSION").read_text().strip(), "0.20.0"), 0)
        releases = (REPO / "RELEASES.md").read_text()
        this = releases.split("## 0.20.0", 1)[1].split("## 0.19.0", 1)[0]
        for words in ("office start --sort", "office moves", "handbook", "--goal"):
            self.assertIn(words, this)
            self.assertIn(words, (REPO / "README.md").read_text())


# --- office open --goal, and office start N with a goal and a brief ------------------------------

class TestAFolderThatKnowsItsGoal(LandCase):
    def test_open_writes_the_goal_and_start_sends_it_and_the_brief(self):
        rel = self.run_office("open", "tidy", "--lane", "alpha: docs", "--source", "a person", "--goal",
                              "Tidy  the docs", check=0).stdout.strip()
        md = (self.root / rel / "folder.md").read_text()
        self.assertIn("- lane: alpha: docs\n- source: a person\n- goal: Tidy the docs\n\n", md)
        (self.root / rel / "brief.md").write_text("# Brief\n\nTidy what the docs say about login.\n")
        self.e.git(self.root, "add", "-A"); self.e.git(self.root, "commit", "-qm", "brief")
        proc = self.run_office("start", rel.split("/")[1], "--on", "alpha", check=0)
        self.assertIn("the goal is the folder's own: Tidy the docs", proc.stderr)
        self.assertIn(f"the session's brief is {rel}/brief.md", proc.stderr)
        calls = [json.loads(l) for l in (self.fake.dir / "pack-calls.jsonl").read_text().splitlines()]
        (cwd, argv), = [(c, a) for c, a in calls if a and a[0] == "pack" and "--context" not in a]
        self.assertEqual(argv[1], "Tidy the docs")
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        tray = pathlib.Path(re.search(r"^Out tray: (.+)$", proc.stdout, re.M).group(1))
        with tarfile.open(tray / f"request-{sid}.tar.gz") as t:
            self.assertEqual(t.extractfile("request-001/README.md").read().decode(),
                             "# Brief\n\nTidy what the docs say about login.\n")
        self.assertIn(f"- {sid}\n", md.replace(md, (self.root / rel / "folder.md").read_text()))


# --- office land files the notes and runs the moves -----------------------------------------------

NOTES_TAIL = "\n## Walkthrough\n\nWhat changed.\n\n## Delivery\n\n- to: Pat\n\n### Commit\n\nFix it\n"


class TestLandFilesTheNotes(LandCase):
    def test_a_build_sessions_sort_answers_and_facts_are_filed_and_its_drop_gets_a_folder(self):
        page = self.run_office("drop", "--project", "alpha", input=MESSAGE, check=0).stdout.strip()
        name = pathlib.Path(page).name
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        notes = ("# Notes\n\n## Sort\n\n" + sort_block(name, facts=("- facts:", "- the login page is static"))
                 + "\n## Questions and answers\n\n- 2026-10-14 Keep the old route? yes, until the next release\n"
                 + "\n## Handbook\n\n### alpha\n\n- the api answers on port 8080\n\n#### Front sheet\n\n"
                 + "alpha is the web app the team logs in to.\n" + NOTES_TAIL)
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes=notes)
        proc = self.run_office("land", sid, "--ratified", "--leave-open", "--response", str(tb), check=0)
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertIn(f"Sort: 1 subsection(s) in {sid}'s notes.md, 1 filed", proc.stderr)
        # The drop has a folder of its own, minted by office moves.
        (folder,) = [p for p in (self.root / "desk").iterdir() if p.name.endswith("-could-you-look-at-the-login-page")]
        md = (folder / "folder.md").read_text()
        for line in ("# Could you look at the login page?", "- number: 2", "- status: queued", "- size: small",
                     "- lane: alpha", "- source: drop", "- goal: Fix the login page's error on narrow screens"):
            self.assertIn(line + "\n", md)
        history = md.split("## History", 1)[1]
        self.assertRegex(history, rf"- {DAY_RE} queued: office moves: {re.escape(page)}, sorted by {sid}\n")
        self.assertRegex(history, rf"- {DAY_RE} dropped: drops/{re.escape(name)}, sorted by {sid}\n")
        self.assertIn(f"- tell: the sender, in reply: fixed in the next release (drops/{name})",
                      md.split("## Next", 1)[1])
        self.assertEqual((folder / "brief.md").read_text(), "Fix the error on narrow screens.\n")
        moved = (folder / "drops" / name).read_text()
        self.assertIn("- status: sorted\n", moved)
        self.assertRegex(moved, rf"\n## Sort\n\n- sorted: {DAY_RE}, by {sid}\n- project: alpha\n")
        self.assertFalse((self.root / page).exists())
        # The answers in the landed folder, the facts in the handbook.
        self.assertIn(f"- from {sid}:\n- 2026-10-14 Keep the old route? yes, until the next release\n",
                      self.folder_md())
        chapter = (self.root / "handbook/alpha.md").read_text()
        self.assertIn("## Front sheet\n\nalpha is the web app the team logs in to.\n", chapter)
        self.assertRegex(chapter, rf"- {DAY_RE}: the login page is static \({sid}\)\n- {DAY_RE}: the api answers on "
                                  rf"port 8080 \({sid}\)\n$")
        # Said before the after-land actions, which stay land's last lines.
        out = proc.stdout
        self.assertLess(out.index("Folders office moves minted:"), out.index("After land, in"))
        self.assertIn(f"folder 2  desk/{folder.name}  (from {page})", out)
        self.assertTrue(out.rstrip().endswith("ran (exit 0): touch AFTER-LAND-RAN"), out)
        subjects = self.subjects(10)
        self.assertIn(f"office land: {sid}'s notes filed (sort, answers, handbook)", subjects)
        self.assertIn("office moves: 1 desk move(s): 1 sorted drop(s) from the in-tray", subjects)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        status = self.run_office("status", check=0).stdout
        self.assertIn("handbook:   matches the install's catalog; 1 chapter(s)", status)
        self.assertIn("hung items: bale.toml include group matches the floor plan", status)
        self.assertIn("in-tray:    matches the install's catalog; 0 unsorted drop(s)", status)


# --- office moves and the sorted drops ---------------------------------------------------------------

class TestMovesAndTheSortedDrops(LandCase):
    def sorted_drop(self, text, sort):
        page = self.run_office("drop", input=text, check=0).stdout.strip()
        (s,) = osort.parse_notes("## Sort\n\n" + sort(pathlib.Path(page).name))["sorts"]
        state, _, words = osort.file_sort(self.root, s, "2026-10-14-by-hand-001", "2026-10-14")
        self.assertEqual(state, "filed", words)
        self.e.git(self.root, "commit", "-qam", "sorted, for the test")
        return page

    def test_what_cannot_move_is_said_and_stays_and_the_rest_go_on(self):
        lost = self.sorted_drop("Lost thing\n", lambda n: sort_block(n, project="the website"))
        cabinet = self.run_office("open", "done-job", "--size", "small", check=0).stdout.strip()
        self.run_office("close", "done-job", check=0)
        filed = self.sorted_drop("For the old job\n", lambda n: sort_block(n, folder="2", brief=None))
        into = self.sorted_drop("For the login job\n", lambda n: sort_block(n, folder="1", brief=None))
        desk = self.run_office("desk", check=0).stdout
        self.assertIn("Pending desk moves (3, 3 sorted drop(s) in the in-tray; office moves applies them):", desk)
        self.assertIn(f"  {into}: sorted by 2026-10-14-by-hand-001, into folder 1", desk)
        self.assertIn("3 desk move(s) pending (3 sorted drop(s) in the in-tray): office moves applies them",
                      self.run_office(check=0).stdout)
        self.assertEqual(self.run_office(check=0).stdout.strip().splitlines()[-1].split("  (")[0], "Next: office moves")
        proc = self.run_office("moves", check=0)
        self.assertIn(f"{lost} stays in the in-tray: ", proc.stderr)
        self.assertIn("which is none of this office's (alpha)", proc.stderr)
        self.assertIn(f"{filed} stays in the in-tray: its Sort names folder 2, which is in the filing cabinet",
                      proc.stderr)
        self.assertIn("2 sorted drop(s) stay in the in-tray", proc.stderr)
        self.assertTrue((self.root / lost).is_file() and (self.root / filed).is_file())
        self.assertFalse((self.root / into).exists())
        self.assertTrue((self.root / self.folder / "drops" / pathlib.Path(into).name).is_file())
        md = self.folder_md()
        self.assertIn("- goal: Fix the login page's error on narrow screens\n", md)
        self.assertRegex(md, rf"- {DAY_RE} dropped: drops/{re.escape(pathlib.Path(into).name)}, sorted by "
                             r"2026-10-14-by-hand-001\n")
        self.assertFalse((self.root / self.folder / "brief.md").exists())
        self.assertFalse((self.root / cabinet.replace("desk/", "filing-cabinet/") / "drops").exists())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_an_open_session_holding_the_in_tray_stops_that_move(self):
        page = self.sorted_drop("Held\n", lambda n: sort_block(n))
        (self.root / ".bale").mkdir(exist_ok=True)
        sid = "2026-10-14-tidy-office-001"
        state = json.loads(self.fake.state.read_text()) if self.fake.state.is_file() else {"repos": {}, "fail": []}
        state["repos"][os.path.realpath(self.root)] = {"sessions": [sid], "scopes": {sid: ["in-tray"]}, "outbox": []}
        self.fake.state.write_text(json.dumps(state))
        proc = self.run_office("moves", check=0)
        self.assertIn(f"{page} stays in the in-tray: {sid} holds in-tray", proc.stderr)
        self.assertTrue((self.root / page).is_file())
        self.assertEqual(sorted(p.name for p in (self.root / "desk").iterdir() if p.is_dir()), [self.name])


# --- office start --sort, out and back ------------------------------------------------------------------

class TestTheStandaloneSort(LandCase):
    def test_out_with_every_folder_and_back_with_its_sort_and_its_moves(self):
        # The hand test, small: a drafting table, two finished folders and
        # one queued beside another that closed, two drops nothing carried.
        self.run_office("blueprint", "open", "arc", "--title", "An arc", "--charter", "Do it.", check=0)
        for slug in ("old-one", "old-two", "audience-line"):
            self.run_office("open", slug, "--size", "small", check=0)
        lost = self.run_office("drop", input=OTHER, check=0).stdout.strip()
        mine = self.run_office("drop", "--project", "alpha", input=MESSAGE, check=0).stdout.strip()
        self.assertFalse((self.root / "drafting-table/moves.md").exists())
        proc = self.run_office("start", "--sort", check=0)
        sid = re.search(r"^Packed (\S+) for the in-tray", proc.stdout, re.M).group(1)
        self.assertRegex(sid, rf"^{DAY_RE}-in-tray-sort-001$")
        self.assertIn(f"When the response comes back: office land {sid}", proc.stdout)
        self.assertIn("office start --sort: the drafting table's moves page arrives", self.subjects(10))
        calls = [json.loads(l) for l in (self.fake.dir / "pack-calls.jsonl").read_text().splitlines()]
        (cwd, argv), = [(c, a) for c, a in calls if a and a[0] == "pack" and "--context" not in a]
        self.assertEqual(cwd, os.path.realpath(self.root))
        self.assertEqual(argv[1:4], [osort.SORT_GOAL, "--slug", osort.SORT_SLUG])
        pairs = [argv[i:i + 2] for i in range(len(argv) - 1)]
        writes = [b for a, b in pairs if a == "--write"]
        self.assertEqual(writes, ["notepad", "drafting-table/moves.md"])
        includes = [b for a, b in pairs if a == "--include"]
        self.assertEqual(sorted(i for i in includes if i.startswith("desk/")),
                         sorted(f"desk/{p.name}/folder.md" for p in (self.root / "desk").iterdir() if p.is_dir()))
        self.assertIn(lost, includes)
        self.assertIn(["--work-class", "meta"], pairs)
        tray = pathlib.Path(re.search(r"^Out tray: (.+)$", proc.stdout, re.M).group(1))
        with tarfile.open(tray / f"request-{sid}.tar.gz") as t:
            brief = t.extractfile("request-001/README.md").read().decode()
            names = t.getnames()
        self.assertNotIn(f"request-001/context/{self.folder}/drops", "\n".join(names))
        for rel in (lost, mine):
            text = (self.root / rel).read_text().rstrip("\n")
            self.assertIn(f"--- DROP BEGIN {rel} ---\n{text}\n--- DROP END ---", brief)
        self.assertIn("2 drop(s) in the in-tray", brief)
        self.assertIn("folder 1  " + self.name, brief)
        self.assertIn("`- [ ] DATE close folder N`", brief)
        # In flight as the in-tray's, and a second sort is refused.
        walk = self.run_office(check=0).stdout
        self.assertIn(f"{sid} ", walk)
        self.assertIn("-> the in-tray (the standalone sort)", walk)
        self.assertEqual(walk.strip().splitlines()[-1].split("  (")[0], f"Next: office land {sid}")
        again = self.run_office("start", "--sort", check=1)
        self.assertIn(f"a sort is out already: {sid}", again.stderr)
        # Back: the sort's notes, its moves page, a notepad page.
        day = sid[:10]
        moves = (self.root / "drafting-table/moves.md").read_text().rstrip("\n") + (
            f"\n- [ ] {day} close folder 2\n- [ ] {day} close folder 3\n"
            f"- [ ] {day} retire folder 4 why=\"queued beside folder 1, which carries its job\"\n")
        notes = ("# Notes\n\n## Sort\n\n" + sort_block(pathlib.Path(mine).name)
                 + sort_block(pathlib.Path(lost).name, project="none", folder="1", brief=None)
                 + "\n## Handbook\n\n### alpha\n\n- invoices load slowly\n")
        tb = response_tarball(self.downloads, sid, {"drafting-table/moves.md": moves, f"notepad/{day}-sort.md": "w\n"},
                              notes=notes)
        proc = self.run_office("land", "--response", str(tb), check=0)
        self.assertIn(f"Landed: {sid} is applied in this office", proc.stdout)
        # 0.23.0: land says nothing of ratification, folder or no folder.
        self.assertNotIn("ratif", proc.stderr)
        filing = sorted(p.name for p in (self.root / "filing-cabinet").iterdir() if p.is_dir())
        self.assertEqual(len(filing), 3, filing)
        desk = sorted(p.name for p in (self.root / "desk").iterdir() if p.is_dir())
        self.assertIn(self.name, desk)
        self.assertEqual(len(desk), 2, desk)
        self.assertTrue((self.root / self.folder / "drops" / pathlib.Path(lost).name).is_file())
        self.assertIn("Folders office moves minted:\n  folder 5  desk/", proc.stdout)
        self.assertRegex((self.root / "handbook/alpha.md").read_text(), rf"- {DAY_RE}: invoices load slowly \({sid}\)\n")
        page = (self.root / "drafting-table/moves.md").read_text()
        self.assertIn(f"- [x] {day} close folder 2 -> folder 2\n", page)
        self.assertIn(f"retire folder 4 why=\"queued beside folder 1, which carries its job\" -> folder 4\n", page)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertFalse(self.fake.is_open(self.root, sid))

    def test_a_sort_only_bale_found_is_filed_with_sessions_in_tray(self):
        page = self.run_office("drop", input=OTHER, check=0).stdout.strip()
        sid = re.search(r"^Packed (\S+) for the in-tray", self.run_office("start", "--sort", check=0).stdout,
                        re.M).group(1)
        elsewhere = self.e.tmp / "elsewhere"
        notes = "## Sort\n\n" + sort_block(pathlib.Path(page).name, project="none", folder="1", brief=None)
        tb = response_tarball(elsewhere, sid, {f"notepad/{sid[:10]}-sort.md": "w\n"}, notes=notes)
        proc = self.run_office("land", extra={"FAKE_BALE_SEARCH": str(elsewhere)}, check=0)
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertIn(f"office sessions --in-tray {sid} --pages FILE files them", proc.stderr)
        self.assertNotIn("## Sort", (self.root / page).read_text())
        proc = self.run_office("sessions", "--in-tray", sid, "--pages", str(tb), check=0)
        self.assertIn("1 filed", proc.stderr)
        self.assertIn("a sorted drop waits in the in-tray: office moves applies it", proc.stderr)
        self.run_office("moves", check=0)
        self.assertTrue((self.root / self.folder / "drops" / pathlib.Path(page).name).is_file())
        self.assertIn("--in-tray goes as", self.run_office("sessions", "--in-tray", sid, check=1).stderr)

    def test_the_refusals_write_nothing(self):
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", "--sort", check=1)
        self.assertIn("the in-tray holds no unsorted drop, so there is nothing to sort", proc.stderr)
        self.run_office("drop", input=OTHER, check=0)
        head = self.e.git(self.root, "rev-parse", "HEAD")
        for args in (("--sort", self.name), ("--sort", "--goal", "g"), ("--sort", "--in-office"),
                     ("--sort", "--drop", "x")):
            proc = self.run_office("start", *args, check=1)
            self.assertIn("it takes nothing else: office start --sort", proc.stderr, args)
        (self.root / ".bale").mkdir(exist_ok=True)
        sid = "2026-10-14-tidy-office-001"
        state = json.loads(self.fake.state.read_text()) if self.fake.state.is_file() else {"repos": {}, "fail": []}
        state["repos"][os.path.realpath(self.root)] = {"sessions": [sid], "scopes": {sid: ["in-tray"]}, "outbox": []}
        self.fake.state.write_text(json.dumps(state))
        proc = self.run_office("start", "--sort", check=1)
        self.assertIn(f"{sid} holds in-tray", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)


if __name__ == "__main__":
    unittest.main()
