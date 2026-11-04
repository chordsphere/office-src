"""Tests for office-src 0.46.0: folders and projects.

One class per item of the brief (2026-11-04-folders-and-projects-002), a
unit class beside a verb class where the item has a unit worth pinning:

1. office map: every project with its facts, what rides with it and what
   runs after it lands, every folder under the project its lane names
   with its state, the office's own folders, one project, one folder's
   whole record ending with the lines that change it; it writes nothing;
2. office folder N: the one writer of a folder's fields after office open
   (a replaced line, the provisional list, a re-scoped History line, one
   commit), refusing a project the office does not scope, a size it does
   not take and a write the one-writer rule keeps out;
3. a lane asked once is kept: office start's question becomes the lane;
   an office lane settles where, piped too; a flag typed writes nothing;
4. the bundle offer shows the newest nine and one line for the rest, and
   a bundle start on a terminal prints at most twelve [office] lines
   before the opener, the last saying what to do next;
5. office projects set asks only what its flags imply (--edit walks
   everything; piped it refuses), --path re-points a clone, and
   --branch-prefix writes the audience line's fifth key;
6. a bundle a paused project's session opened leaves the offer;
7. every home-screen item has a key, past nine too;
8. office tray opens a session's out tray again and prints its opener.

The worlds are the suite's own: tests/test_land.py's LandCase (an office
scoping alpha, its fake bale, folder 1 on the desk with its lane on
alpha). Every project and folder here is invented. The terminal classes
run in the serial lane. Run with the rest of the suite:

    tests/run.sh test_folders_and_projects
"""

import os
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_start import on_a_terminal, git_repo, recording_windows, imitate_wsl  # noqa: E402
from test_land import LandCase, bundle_file  # noqa: E402
from test_home_screen import home, waiting, bundle_argv, downloads_set  # noqa: E402

import office_helper as oh  # noqa: E402
import office_home as hs  # noqa: E402


def flat(text):
    """A screen's text with its wrapping undone, for a line a test pins."""
    return " ".join(text.replace("\r\n", "\n").split())


class FoldersCase(LandCase):
    def md(self, rel=None):
        return (self.root / (rel or self.folder) / "folder.md").read_text()

    def head(self):
        return self.e.git(self.root, "rev-parse", "HEAD").strip()


# --- 1. one map -----------------------------------------------------------------------------

class TestTheProjectFactsAsAUnit(unittest.TestCase):
    def test_here_or_a_host_the_audience_line_and_paused(self):
        import office_map as om
        p = {"name": "alpha", "path": "~/alpha", "host": None, "problem": None, "audience": None, "paused": False}
        self.assertEqual(om.project_facts_line(p), "here (~/alpha); no audience")
        p.update(host="me@box", audience="origin", author="Pat <p@x.org>", base="main", branch_prefix="feature/",
                 paused=True)
        self.assertEqual(om.project_facts_line(p),
                         "on me@box (~/alpha); audience origin, author Pat <p@x.org>, base main, branch_prefix "
                         "feature/; paused (office projects set alpha --unpaused)")


class TestTheMap(FoldersCase):
    def test_every_project_its_facts_and_its_folders_then_the_office(self):
        git_repo(self.e.tmp / "beta", {"README.md": "beta\n"})
        self.run_office("projects", "add", "beta", str(self.e.tmp / "beta"), check=0)
        self.run_office("open", "tidy-notes", "--title", "Tidy the notes", check=0)
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        before = self.head()
        out = self.run_office("map", check=0).stdout
        self.assertIn(f"alpha\n  here ({self.proj}); no audience\n  after it lands: touch AFTER-LAND-RAN\n", out)
        self.assertRegex(out, rf"\n  folder 1  fix-login  in flight: {sid}, out since \d{{4}}-\d\d-\d\d, ")
        self.assertIn("beta\n  here (", out)
        self.assertIn("\n  no folder\n", out)
        self.assertIn("the office\n  folder 2  Tidy the notes  ready\n", out)
        self.assertLess(out.index("alpha\n"), out.index("beta\n"))
        self.assertLess(out.index("beta\n"), out.index("the office\n"))
        self.assertEqual(self.head(), before, "the map writes nothing")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "")
        # One project's section alone.
        only = self.run_office("map", "beta", check=0).stdout
        self.assertTrue(only.startswith("beta\n"), only)
        self.assertNotIn("alpha", only)

    def test_newest_number_first_and_a_closed_folder_says_so(self):
        second = self.run_office("open", "fix-signup", "--lane", "alpha", check=0).stdout.strip()
        self.run_office("close", second.split("/")[1], check=0)
        out = self.run_office("map", "alpha", check=0).stdout
        self.assertIn("  folder 2  fix-signup  closed, done\n  folder 1  fix-login  ready\n", out)

    def test_one_folders_record_ends_with_the_lines_that_change_it(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        out = self.run_office("map", "1", check=0).stdout
        self.assertTrue(out.startswith(f"folder 1  fix-login  ({self.folder})\n"), out)
        for heading in ("Fields:", "Sessions:", "Riders:", "Deliveries and reviews:", "Standing:", "Next:"):
            self.assertIn(f"\n{heading}\n", out)
        self.assertIn("  lane: alpha: src\n", out)
        self.assertIn(f"- {sid}", out)
        self.assertRegex(out, rf"\n  office land {sid} +brings the session back once its response is in your "
                              "downloads\n")
        self.assertRegex(out, rf"\n  office tray {sid} +opens its out tray again and prints its opener\n")
        tail = out.rstrip("\n").splitlines()
        self.assertRegex(tail[-1], r"^  office folder 1 --class code +bale's work class: ")
        self.assertIn("  office folder 1 --lane alpha", out)
        self.assertIn("  office folder 1 --in-office", out)
        self.assertIn("  office folder 1 --title fix-login", out)

    def test_a_name_that_is_neither_refuses_naming_the_projects(self):
        proc = self.run_office("map", "nowhere", check=1)
        self.assertIn("office map nowhere: no project or folder by that name (projects: alpha)", proc.stderr)


# --- 2. a folder's fields, edited by one verb -------------------------------------------------

class TestTheFieldWriterAsAUnit(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.md = self.tmp / "folder.md"
        self.md.write_text("# Fix it\n\n- number: 4\n- status: queued\n- size: small\n- provisional: title, size, goal\n"
                           "\n## Riders\n\n## History\n\n- 2026-11-01 queued: office open\n")

    def test_replaced_written_where_the_block_puts_it_and_provisional_taken_off(self):
        done = oh.folder_edit(self.md, [("size", "medium"), ("lane", "alpha"), ("title", "Fix it now")], "2026-11-04")
        self.assertEqual(done, [("size", "small", "medium"), ("lane", None, "alpha"), ("title", "Fix it", "Fix it now")])
        text = self.md.read_text()
        self.assertTrue(text.startswith("# Fix it now\n\n- number: 4\n- status: queued\n- size: medium\n- lane: alpha\n"
                                        "- provisional: goal\n"), text)
        self.assertIn("- 2026-11-04 re-scoped: size from small to medium (office folder)\n", text)
        self.assertIn("- 2026-11-04 re-scoped: lane from none to alpha (office folder)\n", text)
        self.assertIn("- 2026-11-04 re-scoped: title from Fix it to Fix it now (office folder)\n", text)

    def test_the_same_value_changes_nothing_and_the_office_lane_is_two_words(self):
        self.assertEqual(oh.folder_edit(self.md, [("size", "small")], "2026-11-04"),
                         [])
        self.assertEqual(oh.folder_edit(self.md, [("lane", "The  Office")], "2026-11-04"),
                         [("lane", None, "the office")])
        self.assertTrue(oh.lane_is_office("the office"))
        self.assertIsNone(oh.lane_project("the office"), "no project is ever named by the office's lane")

    def test_a_value_the_field_does_not_take_writes_nothing(self):
        before = self.md.read_text()
        with self.assertRaises(oh.HelperError):
            oh.folder_edit(self.md, [("title", "New"), ("size", "huge")], "2026-11-04")
        self.assertEqual(self.md.read_text(), before)
        with self.assertRaises(oh.HelperError):
            oh.folder_edit(self.md, [("status", "done")], "2026-11-04")


class TestOfficeFolder(FoldersCase):
    def test_each_flag_its_line_its_history_and_one_commit(self):
        proc = self.run_office("folder", "1", "--title", "Fix the login", "--size", "medium",
                               "--goal", "Fix the redirect", check=0)
        self.assertIn(f"[office] {self.folder}: title from fix-login to Fix the login", proc.stderr)
        self.assertIn(f"[office] {self.folder}: size from none to medium", proc.stderr)
        self.assertIn(f"[office] {self.folder}: goal from none to Fix the redirect", proc.stderr)
        md = self.md()
        self.assertTrue(md.startswith("# Fix the login\n"))
        self.assertIn("- size: medium\n", md)
        self.assertIn("re-scoped: goal from none to Fix the redirect (office folder)", md)
        self.assertEqual(self.subjects(1), [f"office folder: {self.name} re-scoped: title, size, goal"])
        self.assertEqual(self.e.git(self.root, "show", "--name-only", "--format=", "HEAD").split(),
                         [f"{self.folder}/folder.md"])

    def test_alone_it_prints_the_fields_and_the_lines_that_change_each(self):
        out = self.run_office("folder", "1", check=0).stdout
        self.assertIn("Fields:\n  lane: alpha: src\n  title: fix-login\n", out)
        self.assertIn("  status: queued (open, close and reopen write it)\n", out)
        self.assertIn("The lines that change each:\n", out)
        self.assertRegex(out, r"\n  office folder 1 --size small +sizes it: small, medium, high\n")

    def test_in_office_a_lane_it_does_not_scope_a_size_it_does_not_take(self):
        proc = self.run_office("folder", "1", "--lane", "nowhere", check=1)
        self.assertIn("--lane nowhere: no such project in this office (it scopes: alpha; --in-office says the work "
                      "is the office's own); nothing was written", proc.stderr)
        proc = self.run_office("folder", "1", "--size", "huge", check=1)
        self.assertIn("nothing was written", proc.stderr)
        proc = self.run_office("folder", "1", "--in-office", "--lane", "alpha", check=1)
        self.assertIn("--lane and --in-office are two lanes; give one", proc.stderr)
        self.run_office("folder", "1", "--in-office", check=0)
        self.assertIn("- lane: the office\n", self.md())
        self.assertIn("re-scoped: lane from alpha: src to the office (office folder)", self.md())

    def test_a_folder_in_the_filing_cabinet_is_edited_the_same_way(self):
        self.run_office("close", self.name, check=0)
        self.run_office("folder", "1", "--title", "Fixed login", check=0)
        md = (self.root / "filing-cabinet" / self.name / "folder.md").read_text()
        self.assertTrue(md.startswith("# Fixed login\n"))
        self.assertIn("- status: done\n", md)

    def test_a_session_out_on_another_project_is_said_never_refused(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        proc = self.run_office("folder", "1", "--in-office", check=0)
        self.assertIn(f"{sid} is out on alpha for {self.folder}; it lands there as packed, whatever the lane says now",
                      proc.stderr)

    def test_an_office_session_holding_the_folder_keeps_the_write_out(self):
        self.run_office("open", "office-job", "--title", "Office job", check=0)
        self.run_office("start", "office-job", "--in-office", "--goal", "g", "--write", "desk", check=0)
        before = self.md()
        proc = self.run_office("folder", "1", "--size", "high", check=1)
        self.assertIn("holds desk/", proc.stderr)
        self.assertIn("so office folder writes nothing beside it (the one-writer rule)", proc.stderr)
        self.assertEqual(self.md(), before)


# --- 3. the lane asked once, then kept ---------------------------------------------------------

class TestTheOfficeLaneSettlesWhere(FoldersCase):
    def test_piped_start_takes_the_office_from_the_lane_and_a_flag_writes_nothing(self):
        self.run_office("open", "no-lane", check=0)
        self.run_office("folder", "no-lane", "--in-office", check=0)
        proc = self.run_office("start", "no-lane", "--goal", "g", check=0)
        self.assertIn("from the folder: the work lands in the office, as the folder's lane says (--on PROJECT sends "
                      "it to a project instead)", proc.stderr)
        self.assertRegex(proc.stdout, r"Packed \S+-office-001 for desk/")
        self.run_office("open", "other", check=0)
        md = self.root / "desk" / [d for d in os.listdir(self.root / "desk") if d.endswith("-other")][0] / "folder.md"
        self.run_office("start", "other", "--on", "alpha", "--goal", "g", "--write", "docs", check=0)
        self.assertNotIn("- lane:", md.read_text(), "a flag typed wins for its run and writes nothing")

    def test_the_probes_lane_reads_the_office(self):
        import office_probe as op
        self.run_office("open", "no-lane", check=0)
        rel = "desk/" + [d for d in os.listdir(self.root / "desk") if d.endswith("-no-lane")][0]
        self.assertIsNone(op.lane_of(str(self.root), rel))
        self.run_office("folder", "no-lane", "--in-office", check=0)
        self.assertEqual(op.lane_of(str(self.root), rel), "office")


class TestTheLaneAskedOnceOnATerminal(FoldersCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_starts_question_becomes_the_lane_and_is_not_asked_again(self):
        rel = self.run_office("open", "no-lane", check=0).stdout.strip()
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "no-lane", "--goal", "g"], self.root,
                                   self.e.env, [(b"Where the work lands, by its key", "1")])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"{rel}'s lane is alpha now, so this is not asked again (office folder 2 --lane says "
                      "otherwise)", flat(seen))
        md = (self.root / rel / "folder.md").read_text()
        self.assertIn("- lane: alpha\n", md)
        self.assertIn("re-scoped: lane from none to alpha (office folder)", md)
        # The first session is still out on the whole of alpha, so this one
        # stops at bale's overlap; what matters is that nothing was asked.
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "no-lane", "--goal", "again", "--write",
                                          "docs"], self.root, self.e.env, [])
        self.assertNotIn("Where the work lands, by its key", seen)
        self.assertIn("from the folder: the work lands on alpha", flat(seen))


# --- 4. the bundle offer and start's screen ------------------------------------------------------

class TestStartsScreenOnATerminal(FoldersCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_a_bundle_start_that_asks_nothing_prints_twelve_office_lines_at_most(self):
        downloads_set(self)
        brief = "# Brief\n\n--- LANDS alpha, a new folder ---\n"
        bundle_file(self.downloads, "2026-11-04-screen", bundle_argv("screen-pass"), brief=brief)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [])
        self.assertEqual(code, 0, seen)
        before = seen.replace("\r\n", "\n").split("--8<-- session opener --8<--")[0]
        said = [l for l in before.splitlines() if l.startswith("[office] ")]
        self.assertLessEqual(len(said), 12, "\n".join(said))
        self.assertTrue(said[-1].startswith("[office] next: attach every file in the out tray ("), said[-1])
        self.assertIn("(office tray 2026-11-04-screen-pass-001 opens the tray and prints the opener again)", said[-1])
        self.assertTrue(any(l.startswith("[office] from the downloads: ") for l in said))
        self.assertFalse([l for l in said if l.startswith("[office] out tray: ")])
        self.assertRegex(before, r"\nOut tray: \S+2026-11-04-screen-pass-001\n")
        self.assertEqual(len(re.findall(r"session opener --8<--", seen)), 2, "the opener is printed once")

    def test_the_offer_shows_the_newest_nine_and_one_line_for_the_rest(self):
        downloads_set(self)
        now = __import__("time").time()
        for n in range(11):
            b = bundle_file(self.downloads, f"2026-11-04-b{n:02d}", bundle_argv(f"b{n:02d}"))
            os.utime(b, (now - 3600 * (11 - n), now - 3600 * (11 - n)))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env,
                                   [(b"The bundle to start, by its key", ""), (b"Which job, by its key", "1"),
                                    (b"What the session is to do", "g")])
        screen = flat(seen)
        self.assertIn("[9] 2026-11-04-b02,", screen)
        self.assertNotIn("[10]", screen)
        self.assertIn("and 2 more, oldest first: office start --bundle FILE starts one by name, office withdraw "
                      "--bundle STEM takes one out of the offer", screen)
        self.assertLess(screen.index("[9] "), screen.index("and 2 more"))


class TestStartsLinesPiped(FoldersCase):
    def test_piped_the_record_keeps_every_line_and_the_next_line_ends_it(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", check=0)
        self.assertIn("[office] out tray: request-", proc.stderr)
        self.assertIn("[office] next: attach every file in the out tray (", proc.stderr)
        self.assertIn("it is printed below", proc.stderr)
        self.assertNotIn("Attach every file", proc.stdout)


# --- 5. office projects set asks only what the flags imply ----------------------------------------

class TestProjectsSetAsksOnlyWhatItsFlagsImply(FoldersCase):
    def test_piped_a_flag_changes_its_group_alone(self):
        self.run_office("projects", "set", "alpha", "--ride", str(self.proj / "docs"), check=0)
        plan = (self.root / "floor-plan/manifest.toml").read_text()
        self.assertIn('after_land = ["touch AFTER-LAND-RAN"]', plan)
        self.assertIn("rides = [", plan)

    def test_edit_piped_refuses(self):
        proc = self.run_office("projects", "set", "alpha", "--edit", check=1)
        self.assertIn("--edit walks every group by asking, and piped input is never asked", proc.stderr)

    def test_path_repoints_the_clone_and_leaves_the_old_one(self):
        other = git_repo(self.e.tmp / "alpha-2", {"src/a.py": "a\n"}) or self.e.tmp / "alpha-2"
        proc = self.run_office("projects", "set", "alpha", "--path", str(other), "--prepare", check=0)
        self.assertIn(f"alpha's clone is now {other}; it was {self.proj}, which is left exactly as it is", proc.stderr)
        self.assertIn(f'path = "{other}"', (self.root / "floor-plan/manifest.toml").read_text())
        self.assertTrue((self.proj / "src/a.py").is_file())
        self.assertEqual(self.subjects(1), ["office projects: set alpha"])
        proc = self.run_office("projects", "set", "alpha", "--path", str(self.e.tmp / "nowhere"), check=1)
        self.assertIn("does not check", proc.stderr)
        self.assertIn(f'path = "{other}"', (self.root / "floor-plan/manifest.toml").read_text())

    def test_branch_prefix_goes_with_an_audience_and_the_listing_shows_it(self):
        proc = self.run_office("projects", "set", "alpha", "--branch-prefix", "feature/", check=1)
        self.assertIn("alpha has no audience; --branch-prefix", proc.stderr)
        self.e.git(self.proj, "remote", "add", "origin", "https://example.invalid/alpha.git")
        self.run_office("projects", "set", "alpha", "--audience", "origin", "--author", "Pat Example <pat@example.org>",
                        "--branch-prefix", "feature/", check=0)
        self.assertIn('branch_prefix = "feature/"', (self.root / "floor-plan/manifest.toml").read_text())
        self.assertIn("branch prefix: feature/", self.run_office("projects", check=0).stdout)
        self.run_office("projects", "set", "alpha", "--no-branch-prefix", check=0)
        self.assertNotIn("branch_prefix", (self.root / "floor-plan/manifest.toml").read_text())


class TestProjectsSetOnATerminal(FoldersCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_a_flag_on_a_terminal_asks_nothing_else(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "set", "alpha", "--no-after-land"],
                                   self.root, self.e.env, [])
        self.assertEqual(code, 0, seen)
        for asked in ("Keep alpha on this machine?", "Keep alpha without an audience?", "Keep what"):
            self.assertNotIn(asked, seen)
        self.assertNotIn("after_land", (self.root / "floor-plan/manifest.toml").read_text())

    def test_edit_walks_every_group(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "set", "alpha", "--edit"], self.root,
                                   self.e.env, [(b"Keep alpha on this machine?", ""),
                                                (b"Keep alpha without an audience?", ""),
                                                (b"A path whose context rides beside every alpha session", ""),
                                                (b"Keep what runs after alpha lands", "")])
        self.assertEqual(code, 0, seen)
        self.assertIn("nothing changed for alpha", seen)


# --- 6. a bundle opened on a paused project --------------------------------------------------------

class TestABundleOpenedOnAPausedProject(FoldersCase):
    def test_it_leaves_the_offer_and_the_paused_line_says_so(self):
        b = bundle_file(self.downloads, "2026-11-04-paused", bundle_argv("paused-pass"))
        self.run_office("start", "fix-login", "--bundle", str(b), "--on", "alpha", check=0)
        proc = self.run_office("projects", "set", "alpha", "--paused", check=0)
        self.assertIn("(one thing is still read: which of its sessions a bundle in your downloads opened, so that "
                      "bundle leaves the offer)", proc.stdout)
        self.assertEqual(waiting(self), [])
        out, _ = home(self)
        self.assertNotIn("Start the planner's bundle 2026-11-04-paused", out)


# --- 7. a home screen past nine keys --------------------------------------------------------------

class TestEveryItemHasAKey(unittest.TestCase):
    def test_nine_digits_then_the_letters_no_fixed_key_takes(self):
        keys = hs.item_keys(14)
        fixed = {k for k, *_ in hs.FIXED_KEYS}
        self.assertEqual(keys[:9], [str(n) for n in range(1, 10)])
        self.assertEqual(keys[9:], ["b", "c", "e", "f", "g"])
        self.assertFalse(set(keys) & fixed)
        self.assertIn("a", fixed)

    def test_the_page_keys_every_item_and_says_no_more_line(self):
        items = [hs.item(f"Thing {n}", ["note", str(n)]) for n in range(12)]
        lines, menu = hs.render_page([("alpha", "nothing landed yet")], items, 0)
        text = "\n".join(lines)
        self.assertIn("  [9] Thing 8", text)
        self.assertIn("  [b] Thing 9", text)
        self.assertIn("  [e] Thing 11", text)
        self.assertNotIn("more:", text)
        self.assertIn(("e", "office", ["note", "11"]), menu)
        self.assertIn(("a", "office", ["map"]), menu)
        self.assertIn("[a] the map: every project and its folders", text)


# --- 8. the out tray, opened again -----------------------------------------------------------------

class TestTheTray(FoldersCase):
    def test_it_prints_the_path_the_files_and_the_opener_kept_beside_the_tray(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        tray = self.e.home / "out-tray" / sid
        self.assertTrue((self.e.home / "out-tray" / f"{sid}.opener.txt").is_file())
        before = self.head()
        for args in ((), ("1",), (sid,)):
            out = self.run_office("tray", *args, check=0).stdout
            self.assertTrue(out.startswith(f"Out tray for {sid}: {tray}\n"), out)
            self.assertIn(f"\n  request-{sid}.tar.gz\n", out)
            self.assertIn(f"This message opens bale session {sid}.", out)
            self.assertNotIn(".opener.txt", out.split("--8<--")[0], "the copy is beside the tray, not in it")
        self.assertEqual(self.head(), before, "the tray writes nothing")

    def test_what_it_refuses(self):
        proc = self.run_office("tray", check=1)
        self.assertIn("no session out from this office has an out tray in", proc.stderr)
        proc = self.run_office("tray", "2026-11-04-nothing-001", check=1)
        self.assertIn("no out tray for 2026-11-04-nothing-001 in", proc.stderr)

    def test_the_home_screen_offers_it_while_the_response_is_not_in_the_downloads(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        out, menu = home(self, "--machine-file", str(self.e.home / ".config/office-src/machine.toml"))
        self.assertIn("Open the out tray for folder 1, fix-login again (its files and opener)", out)
        self.assertTrue(any(m[1:] == ["office", "tray", sid] for m in menu), menu)


class TestTheTrayOnATerminal(FoldersCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_it_opens_the_tray_as_start_does(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        windows, calls = recording_windows(self.e.tmp / "windows")
        shell = self.e.tmp / "shell"
        shell.write_text(f'#!/bin/sh\n"$@"; s=$?\nn=0\nwhile [ $n -lt 30 ] && '
                         f'! grep -q "^explorer.exe" {calls} 2>/dev/null; do sleep 0.1; n=$((n + 1)); done\nexit $s\n')
        shell.chmod(0o755)
        env = dict(imitate_wsl(self.e, windows), OFFICE_DESKTOP_PATH=str(windows))
        code, seen = on_a_terminal(self, [str(shell), str(self.e.office_bin), "tray"], self.root, env, [])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"opened the out tray with {windows / 'explorer.exe'}", seen)
        self.assertIn(f"explorer.exe . (in {os.path.realpath(self.e.home / 'out-tray' / sid)})",
                      calls.read_text())


if __name__ == "__main__":
    unittest.main()
