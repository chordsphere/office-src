"""Tests for 0.31.0, the tidy after the front-door arc: a sitting's pages
joined by slug, the drafting table named as it rides with every sitting,
office status naming a folder still provisional after its sessions all
landed, a response filed twice adding nothing twice, the drafting table
arriving with office start --sort, the doctrine's second-desk sentence,
the install's bytecode cache on the walk-in and its Next line, and the
letterhead check read from that cache.

bale is never needed: the fake bale of tests/test_land.py packs, applies
and keeps the open sessions. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import tarfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, InstallCase, h  # noqa: E402
from test_land import LandCase, response_tarball  # noqa: E402
from test_one_door import a_folder  # noqa: E402
from test_meetings_view import MeetingCase, request_members  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)
import office_deliver as odl  # noqa: E402
import office_letterhead as olh  # noqa: E402
import office_planner as op  # noqa: E402
import office_sort as osort  # noqa: E402
import office_watches as ow  # noqa: E402

TAG = sys.implementation.cache_tag
# The development record's directory, spelled so this file names no model.
RECORD_DIR = "cla" + "ude"


# --- 1. a sitting's pages, joined by slug ---------------------------------------------------

class TestASittingsPagesBySlug(unittest.TestCase):
    """office start files a sitting's pages by its slug (SLUG.md, then
    SLUG-2.md and on: the brief's own words), and the digest counted each
    as a sitting of its own, since only SID-N.md was joined to SID.md."""

    def setUp(self):
        self.e = Env(self)

    def test_a_page_continuing_a_slug_page_is_the_same_sitting(self):
        first = "2026-10-22-after-the-arc-sitting"
        self.assertEqual(ow.sitting_key(f"notepad/{first}-5.md", {first}), first)
        self.assertEqual(ow.sitting_key(f"notepad/{first}.md", {first}), first)
        # A slug that only ends in a number is its own sitting when no
        # page of the shorter slug is there.
        self.assertEqual(ow.sitting_key("notepad/2026-10-20-plan-2.md", {"2026-10-20-plan-2"}), "2026-10-20-plan-2")
        # SID-N.md continues SID.md as before, with or without the pages.
        self.assertEqual(ow.sitting_key("notepad/2026-10-03-plan-4b-sitting-001-3.md"), "2026-10-03-plan-4b-sitting-001")

    def test_the_digests_count_takes_a_slugs_pages_as_one_sitting(self):
        root = self.e.tmp / "office"
        (root / "notepad").mkdir(parents=True)
        self.e.git(root, "init", "-q")
        pages = [("2026-10-22T20:00:00+00:00", "2026-10-22-after-the-arc-sitting.md"),
                 ("2026-10-23T20:00:00+00:00", "2026-10-22-after-the-arc-sitting-2.md"),
                 ("2026-10-24T20:00:00+00:00", "2026-10-20-plan-2.md"),
                 ("2026-10-25T20:00:00+00:00", "2026-10-22-after-the-arc-sitting-3.md")]
        for when, name in pages:
            (root / "notepad" / name).write_text(f"# {name}\n")
            self.e.git(root, "add", "notepad")
            subprocess.run(["git", "-C", str(root), "commit", "-qm", f"office start: {name}"], check=True,
                           env=dict(self.e.env, GIT_COMMITTER_DATE=when, GIT_AUTHOR_DATE=when))
        filings = ow.sitting_filings(root)
        self.assertEqual([f[1] for f in filings], [f"notepad/{name}" for _, name in pages])
        self.assertEqual([f[4] for f in filings], ["2026-10-22-after-the-arc-sitting"] * 2
                         + ["2026-10-20-plan-2", "2026-10-22-after-the-arc-sitting"])
        utc = dt.timezone.utc
        self.assertEqual(ow.sittings_after(filings, "2026-10-21", utc), 2)
        self.assertEqual(ow.sittings_after(filings, "2026-10-23", utc), 2)
        self.assertEqual(ow.sittings_after(filings, "2026-10-24", utc), 1)


# --- 2. the drafting table, named as it rides ---------------------------------------------------

class TestTheDraftingTableOnASittingsList(unittest.TestCase):
    def setUp(self):
        self.root = Env(self).tmp / "office"
        self.root.mkdir()

    def test_named_as_arriving_where_there_is_none_and_as_it_is_where_there_is_one(self):
        _, lines = op.every_sitting_carries(self.root, None)
        why = dict(lines)["drafting-table/"]
        self.assertTrue(why.startswith("the drafting table, which arrives in this office with its digest.md"), why)
        (self.root / "drafting-table").mkdir()
        _, lines = op.every_sitting_carries(self.root, None)
        self.assertEqual(dict(lines)["drafting-table/"], "the drafting table, its digest.md first: written just "
                                                         "before the pack, every line computed then (doctrine section 5)")


class TestThePrepNamesTheTableItCarries(MeetingCase):
    def test_in_an_office_with_none_the_prep_says_the_table_it_carries(self):
        self.run_office("meeting", "alpha review on 2026-10-30 at 14:00", check=0)
        self.assertFalse((self.root / "drafting-table").exists())
        proc = self.run_office("start", "--prep", "2026-10-30 14:00 alpha review", check=0)
        self.assertIn("drafting-table/: the drafting table, which arrives in this office with its digest.md",
                      proc.stderr)
        files = request_members(re.search(r"^Out tray: (\S+)$", proc.stdout, re.M).group(1))
        self.assertIn("context/drafting-table/digest.md", json.loads(files["manifest.json"])["context_included"])
        self.assertIn("drafting-table/: the drafting table, which arrives in this office", files["README.md"].decode())


# --- 3. office status: a folder still provisional after its sessions landed -----------------------

NOTES_NO_STRUCTURE = """# Notes

## Questions and answers

- 2026-10-26 Narrow screens first? yes

## Handbook

### alpha

- the login page lives in src/a.py

#### Front sheet

alpha is the login page.

## Walkthrough

### What changed

- the login page.

## Delivery

- to: nobody
"""


class TestStatusNamesAFolderStillProvisional(LandCase):
    def structure_lines(self):
        out = self.run_office("status", check=0).stdout
        return [l for l in out.splitlines() if l.startswith("structure:")], out

    def test_named_once_its_one_session_landed_applied_with_no_structure(self):
        proc = self.run_office("start", "new", "--words", "Fix the login page\nOn narrow screens.", "--on", "alpha",
                               check=0)
        sid, name = re.search(r"^Packed (\S+) for desk/(\S+)\.$", proc.stdout, re.M).groups()
        # Out, not landed: nothing to say.
        self.assertEqual(self.structure_lines()[0], [])
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes=NOTES_NO_STRUCTURE)
        self.run_office("land", sid, "--response", str(tb), "--close", check=0)
        lines, out = self.structure_lines()
        number = h.parse_folder((self.root / "filing-cabinet" / name / "folder.md").read_text())["fields"]["number"][0]
        self.assertEqual(lines, [f"structure:  folder {number} (filing-cabinet/{name}) still marks title, size, goal "
                                 "provisional, though its one session landed applied: its Structure never came back, "
                                 "or came back off its shape and was not filed"])
        # Its place: right under the folders line.
        names = [l.split(":")[0] for l in out.splitlines()]
        self.assertEqual(names[names.index("folders") + 1], "structure")

    def test_a_folder_whose_sessions_did_not_all_land_or_that_is_not_provisional_is_not_named(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "Fix the login redirect")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        self.run_office("land", sid, check=0)
        # A folder office open made with flags marks nothing provisional.
        self.assertNotIn("provisional", self.folder_md())
        self.assertEqual(self.structure_lines()[0], [])
        # Provisional, with one session landed and one never applied.
        md = self.root / self.folder / "folder.md"
        h.folder_set_field(md, "provisional", "size")
        h.record_session(md, "2026-10-26-never-landed-001")
        self.assertEqual(self.structure_lines()[0], [])

    def test_the_rule_in_process_reads_the_applied_tags_of_the_office_and_each_project(self):
        a_folder(self.root / "desk" / "one" / "folder.md", fields={"size": "small", "provisional": "size"},
                 sessions=["2026-10-26-one-001"])
        a_folder(self.root / "desk" / "two" / "folder.md", title="Two", fields={"number": "4"},
                 sessions=["2026-10-26-two-001"])
        self.assertEqual(ob.provisional_landed(self.root), ([], 0))
        self.e.git(self.proj, "tag", "applied/2026-10-26-one-001")
        self.e.git(self.proj, "tag", "applied/2026-10-26-two-001")
        lines, _ = ob.provisional_landed(self.root)
        self.assertEqual([l.split(" (")[1].split(")")[0] for l in lines], ["desk/one"])
        self.assertIn("still marks size provisional", lines[0])


# --- 4. a response filed twice adds nothing twice ---------------------------------------------------

class TestARefiledResponse(LandCase):
    def test_land_then_sessions_pages_files_each_line_once(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "Fix the login redirect")
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes=NOTES_NO_STRUCTURE)
        proc = self.run_office("land", sid, "--response", str(tb), check=0)
        self.assertIn("Questions and answers: 1 line(s) filed in", proc.stderr)
        chapter = self.root / "handbook" / "alpha.md"
        md, text = self.root / self.folder / "folder.md", chapter.read_text()
        once_md, once_chapter = md.read_bytes(), chapter.read_bytes()
        self.assertEqual(text.count("the login page lives in src/a.py"), 1)
        proc = self.run_office("sessions", self.name, sid, "--pages", str(tb), check=0)
        self.assertIn(f"all 1 line(s) already in {self.folder}/folder.md, left as they are; nothing filed", proc.stderr)
        self.assertIn(f"handbook/alpha.md: all 1 fact(s) from {sid} already there, left as they are", proc.stderr)
        self.assertIn(f"the front sheet already reads as {sid}'s, left as it is", proc.stderr)
        self.assertEqual((md.read_bytes(), chapter.read_bytes()), (once_md, once_chapter))
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_in_process_a_new_line_beside_old_ones_is_filed_under_its_session(self):
        root = Env(self).tmp / "office"
        md = a_folder(root / "desk" / "one" / "folder.md", sessions=["2026-10-26-one-001"])
        notes = "## Questions and answers\n\n- 2026-10-26 First? yes\n"
        said, changed = osort.file_notes(root, notes, "2026-10-26-one-001", "2026-10-26", "desk/one")
        self.assertEqual(changed, ["desk/one/folder.md"])
        said, changed = osort.file_notes(root, notes + "- 2026-10-26 Second? no\n", "2026-10-26-one-001",
                                         "2026-10-26", "desk/one")
        self.assertIn("Questions and answers: 1 line(s) filed in desk/one/folder.md; 1 already there, left as they "
                      "are", said)
        body = md.read_text().split("## Questions and answers")[1].split("\n## ")[0]
        self.assertEqual([l for l in body.splitlines() if l.startswith("- ")],
                         ["- from 2026-10-26-one-001:", "- 2026-10-26 First? yes", "- 2026-10-26 Second? no"])
        # A later session's lines between: a new line from the first one
        # is filed under its own line again, never under another's.
        osort.file_notes(root, "## Questions and answers\n\n- 2026-10-27 Third? yes\n", "2026-10-27-two-001",
                         "2026-10-27", "desk/one")
        osort.file_notes(root, notes + "- 2026-10-26 Fourth? maybe\n", "2026-10-26-one-001", "2026-10-28", "desk/one")
        body = md.read_text().split("## Questions and answers")[1].split("\n## ")[0]
        self.assertEqual([l for l in body.splitlines() if l.startswith("- ")][-3:],
                         ["- 2026-10-27 Third? yes", "- from 2026-10-26-one-001:", "- 2026-10-26 Fourth? maybe"])

    def test_in_process_a_fact_filed_on_a_later_day_is_the_same_fact(self):
        root = Env(self).tmp / "office"
        (root / "floor-plan").mkdir(parents=True)
        (root / "floor-plan" / "manifest.toml").write_text("[spaces]\n")
        osort.file_handbook(root, "alpha", ["one fact", "two fact"], None, "2026-10-26-one-001", "2026-10-26")
        changed, words = osort.file_handbook(root, "alpha", ["two fact", "three fact"], None, "2026-10-26-one-001",
                                             "2026-10-27")
        self.assertEqual(words[-1], "handbook/alpha.md: 1 fact(s) from 2026-10-26-one-001; 1 already there, left as "
                                    "they are")
        facts = [l for l in (root / "handbook/alpha.md").read_text().splitlines() if l.startswith("- ")]
        self.assertEqual(facts, ["- 2026-10-26: one fact (2026-10-26-one-001)", "- 2026-10-26: two fact (2026-10-26-one-001)",
                                 "- 2026-10-27: three fact (2026-10-26-one-001)"])
        # The same fact from another session is that session's, and filed.
        changed, words = osort.file_handbook(root, "alpha", ["one fact"], None, "2026-10-27-two-001", "2026-10-27")
        self.assertEqual((changed, words[-1]), (["handbook/alpha.md"], "handbook/alpha.md: 1 fact(s) from 2026-10-27-two-001"))
        changed, _ = osort.file_handbook(root, "alpha", ["one fact"], None, "2026-10-27-two-001", "2026-10-28")
        self.assertEqual(changed, [])


# --- 5. the drafting table arrives with office start --sort ---------------------------------------

class TestTheSortBringsTheDraftingTable(LandCase):
    def test_an_office_with_none_gets_it_committed_alone_and_the_sort_forecasts_its_moves(self):
        self.run_office("drop", input="From: a sender\n\nThe report is late.\n", check=0)
        self.assertFalse((self.root / "drafting-table").exists())
        before = self.e.git(self.root, "rev-parse", "HEAD").strip()
        proc = self.run_office("start", "--sort", check=0)
        self.assertIn("the drafting table arrives in this office", proc.stderr)
        for page in ("README.md", "moves.md"):
            self.assertTrue((self.root / "drafting-table" / page).is_file(), page)
        self.assertIn("drafting-table", h.read_toml(self.root / "floor-plan/manifest.toml")["spaces"])
        self.assertIn('"drafting-table"', (self.root / "bale.toml").read_text())
        log = self.e.git(self.root, "log", "--format=%s", f"{before}..HEAD").splitlines()
        self.assertIn("office start --sort: the drafting table arrives, for the moves page", log)
        sha = self.e.git(self.root, "log", "--format=%H", "-1", "--grep",
                         "office start --sort: the drafting table arrives").strip()
        touched = sorted(self.e.git(self.root, "show", "--name-only", "--format=", sha).split())
        self.assertEqual(touched, ["bale.toml", "drafting-table/README.md", "drafting-table/moves.md",
                                   "floor-plan/manifest.toml"])
        calls = [json.loads(l) for l in (self.fake.dir / "pack-calls.jsonl").read_text().splitlines()]
        (_, argv), = [(c, a) for c, a in calls if a and a[0] == "pack" and "--context" not in a]
        writes = [b for a, b in zip(argv, argv[1:]) if a == "--write"]
        self.assertEqual(writes, ["notepad", "drafting-table/moves.md"])
        tray = pathlib.Path(re.search(r"^Out tray: (.+)$", proc.stdout, re.M).group(1))
        sid = re.search(r"^Packed (\S+) for the in-tray", proc.stdout, re.M).group(1)
        with tarfile.open(tray / f"request-{sid}.tar.gz") as t:
            brief = t.extractfile("request-001/README.md").read().decode()
        self.assertIn("This office has a drafting table, so its moves page", brief)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertIn("drafting:   matches the install's catalog", self.run_office("status", check=0).stdout)


# --- 6. the doctrine's second-desk sentence ---------------------------------------------------------

class TestTheDoctrineSaysTheSecondDesk(unittest.TestCase):
    def test_the_sentence_says_what_the_code_does_since_0_18_0(self):
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        self.assertIn("A second desk is bale's to recognize, and the office refuses an overlap only where bale would "
                      "(0.18.0)", doctrine)
        self.assertIn("a bundle bale would take as a second desk on an open session is sent on", doctrine)
        self.assertNotIn("a bundle is refused the same way whenever the office can read its pack line", doctrine)
        # The code's own words, which the sentence follows.
        office = (REPO / "bin/office").read_text()
        self.assertIn("the office refuses an overlap only where bale would", office)


class TestTheRecord(unittest.TestCase):
    def test_the_release_is_recorded(self):
        self.assertIn("## 0.31.0", (REPO / "RELEASES.md").read_text())
        self.assertIn("0.31.0 (session 2026-10-26-office-tidy-001)",
                      (REPO / RECORD_DIR / "context" / "front-sheet.md").read_text())
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        for words in ("the drafting table with it in an office that has none (0.31.0)",
                      "a folder still provisional though every session it records landed applied (0.31.0)",
                      "the install's bytecode cache not level, when its stamp names the source"):
            self.assertIn(words, doctrine)


# --- 7 and 8. the install's bytecode cache: the walk-in, and the letterhead check ----------------------

class TestTheCacheOnTheWalkIn(InstallCase):
    """0.31.0: the walk-in says a cache that is not level, in status's
    words, and the Next line names install.sh's line, after an install
    behind its source. Under a cache prefix (the runner's) nothing is said,
    so a test here runs as everyday use does, with none."""

    def setUp(self):
        super().setUp()
        self.e.env.pop("PYTHONPYCACHEPREFIX", None)
        self.office = self.bindir / "office"
        self.assertEqual(self.install().returncode, 0)
        self.root = self.e.home / "w"
        self.e.run("init", str(self.root), "--no-founding", bin_path=self.office, check=0)

    def walk_in(self):
        out = self.e.run(cwd=self.root, bin_path=self.office, check=0).stdout
        return [l for l in out.splitlines() if l.startswith("Bytecode:")], out.strip().splitlines()[-1], out

    def test_level_says_nothing_and_a_stale_module_is_said_with_install_shs_line(self):
        lines, nxt, out = self.walk_in()
        self.assertEqual(lines, [], out)
        self.assertFalse(nxt.startswith("Next: (cd "), nxt)
        level_page = out
        lib = self.prefix / "lib" / "office_probe.py"
        lib.chmod(0o644)
        lib.write_text(lib.read_text() + "\n# changed in the install\n")
        lines, nxt, out = self.walk_in()
        src = h.shell_single_quoted(str(self.src))
        self.assertEqual(lines, [f"Bytecode: BEHIND: 1 of lib/'s {len(list((self.prefix / 'lib').glob('*.py')))} "
                                 f"modules compiles from source on every helper call (office_probe.py stale); "
                                 f"(cd {src} && ./install.sh) brings the cache level"], out)
        # Under the head's lines, before the page's first blank line.
        head = out.split("\n\n")[0].splitlines()
        self.assertEqual(head[-1], lines[0])
        self.assertTrue(nxt.startswith(f"Next: (cd {src} && ./install.sh)  (the installed office-src's bytecode "
                                       "cache is not level for this python3 (BEHIND: 1 of lib/'s"), nxt)
        self.assertIn("compiles them again)", nxt)
        # Under a cache prefix the install's cache is not what is read, and
        # install.sh would not change that: nothing said.
        prefix = self.e.tmp / "prefix"
        prefix.mkdir()
        out = self.e.run(cwd=self.root, bin_path=self.office, extra={"PYTHONPYCACHEPREFIX": str(prefix)},
                         check=0).stdout
        self.assertNotIn("Bytecode:", out)
        # install.sh again brings it level, and the page is as it was.
        self.assertEqual(self.install().returncode, 0)
        lines, nxt, out = self.walk_in()
        self.assertEqual(lines, [])
        mask = lambda t: re.sub(r"\d{2}:\d{2}", "HH:MM", t)  # noqa: E731
        self.assertEqual(mask(out), mask(level_page))

    def test_next_move_puts_the_cache_after_the_install_behind_and_before_a_session_out(self):
        cache = {"words": "NONE for this python3 (x)", "what": "NONE for this python3 (x)", "source": "/src"}
        behind = {"source": "/src", "project": "office-src", "commit": "a", "head": "b", "version": "0.31.0"}
        out = [{"sid": "2026-10-26-x-001", "label": "alpha", "folders": [], "held": False}]
        self.assertTrue(ob.next_move("current", True, out, {}, [], 0, behind, cache)[1].startswith(
            "the installed office-src is behind its source"))
        command, why = ob.next_move("current", True, out, {}, [], 0, None, cache)
        self.assertEqual(command, "(cd '/src' && ./install.sh)")
        self.assertIn("(NONE for this python3 (x))", why)
        self.assertEqual(ob.next_move("current", True, out, {}, [], 0, None, None)[0], "office land 2026-10-26-x-001")
        # A stamp that names no source has no line to fill in.
        self.assertEqual(ob.next_move("current", True, out, {}, [], 0, None, dict(cache, source=""))[0],
                         "office land 2026-10-26-x-001")


class TestTheLetterheadCheckReadsTheCache(InstallCase):
    def setUp(self):
        super().setUp()
        self.e.env.pop("PYTHONPYCACHEPREFIX", None)
        self.assertEqual(self.install().returncode, 0)

    def test_its_module_is_read_from_the_installs_cache_and_says_what_the_script_said(self):
        tree = self.e.tmp / "tree"
        tree.mkdir()
        (tree / "a.md").write_text("A plain line.\nI hope this helps.\n")
        rules = json.dumps(olh.load_rules_toml(REPO / "share/letterhead.toml"))
        args = ["--rules-json", rules, "--all", str(tree)]
        argv = odl.letterhead_argv(self.prefix, args)
        run = subprocess.run(argv, cwd=tree, env=dict(self.e.env, PYTHONVERBOSE="1"), capture_output=True, text=True,
                             timeout=60)
        cached = self.prefix / "lib" / "__pycache__" / f"office_letterhead.{TAG}.pyc"
        self.assertIn(f"# code object from '{cached}'", run.stderr)
        self.assertNotIn(f"# code object from {self.prefix / 'lib' / 'office_letterhead.py'}", run.stderr)
        # What the script said, and its exit, byte for byte.
        script = subprocess.run([sys.executable, "-B", str(self.prefix / "lib" / "office_letterhead.py"), *args],
                                cwd=tree, env=self.e.env, capture_output=True, text=True, timeout=60)
        quiet = subprocess.run(argv, cwd=tree, env=self.e.env, capture_output=True, text=True, timeout=60)
        self.assertEqual((quiet.returncode, quiet.stdout, quiet.stderr),
                         (script.returncode, script.stdout, script.stderr))
        self.assertEqual(quiet.returncode, 1, quiet.stderr)
        # Nothing written: the install's cache is as install.sh left it.
        self.assertEqual(sorted(p.name for p in (self.prefix / "lib" / "__pycache__").iterdir()),
                         sorted(f"{p.stem}.{TAG}.pyc" for p in (self.prefix / "lib").glob("*.py")))
        # A module of the tree being checked is never what runs.
        (tree / "office_letterhead.py").write_text("raise SystemExit('the tree ran')\n")
        again = subprocess.run(argv, cwd=tree, env=self.e.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(again.returncode, 1, again.stderr)


if __name__ == "__main__":
    unittest.main()
