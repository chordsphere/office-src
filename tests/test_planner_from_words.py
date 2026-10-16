"""Tests for 0.24.0, a planner from his words: a read-only sitting sent out
from the occupant's words with the context the office gathers for it, the
in-tray's sort offered first when drops wait, the digest listing the
unsorted drops, a planner's bundle whose brief names where it lands, and a
session never worked withdrawn by key.

bale is never needed: the fake bale of tests/test_land.py packs, opens,
applies, unlocks and keeps the open sessions. The terminal tests drive a
pseudo-terminal and run in the serial lane. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import json
import pathlib
import re
import sys
import tarfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_land import LandCase, bundle_file, response_tarball  # noqa: E402
from test_start import on_a_terminal, opener_from  # noqa: E402
from test_one_door import a_folder  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)
import office_digest as odg  # noqa: E402
import office_home as hs  # noqa: E402
import office_planner as op  # noqa: E402

WORDS = "Plan the alpha release\nWhat goes first, and what can wait?"


def request_members(tray):
    """{name: bytes} of the request tarball in an out tray."""
    req = next(p for p in pathlib.Path(tray).iterdir() if p.name.startswith("request-"))
    out = {}
    with tarfile.open(req) as t:
        for m in t.getmembers():
            if m.isfile():
                out[m.name.split("/", 1)[1]] = t.extractfile(m).read()
    return out


def tray_of(stdout, sid):
    return re.search(r"^Out tray: (\S*" + re.escape(sid) + r")$", stdout, re.M).group(1)


# --- the pieces, in this process ------------------------------------------------------------

class TestTheReadings(unittest.TestCase):
    def setUp(self):
        self.tmp = Env(self).tmp

    def test_a_lands_line_is_kept_to_the_byte_and_read_where_ratifications_are(self):
        brief = "\n".join([
            "# Brief", "",
            "```", "--- LANDS beta, folder 2 ---", "```",
            "--- NOTEPAD PAGE BEGIN notepad/2026-10-15-sitting.md ---",
            "--- LANDS gamma, folder 3 ---",
            "--- NOTEPAD PAGE END ---",
            "--- LANDS alpha folder 4 ---",
            "--- LANDS alpha, folder 14 ---",
            "--- LANDS the office, a new folder ---", ""])
        mark, problems = h.brief_lands(brief)
        self.assertEqual(mark, {"place": "alpha", "folder": 14})
        self.assertEqual(len(problems), 2, problems)
        self.assertIn("--- LANDS alpha folder 4 ---", problems[0])
        self.assertIn("a second LANDS line", problems[1])
        self.assertEqual(h.brief_lands("--- LANDS the office, a new folder ---\n"),
                         ({"place": "office", "folder": "new"}, []))
        self.assertEqual(h.brief_lands("# Brief\n\nNothing.\n"), (None, []))
        # The RATIFIED lines are read the same way, unchanged by the shared reader.
        marks, _ = h.brief_ratifications("```\n--- RATIFIED 2026-10-15-a-001 ---\n```\n--- RATIFIED 2026-10-15-b-002 ---\n")
        self.assertEqual(marks, [("2026-10-15-b-002", None)])

    def test_his_words_make_one_goal_and_name_every_project_they_name(self):
        self.assertEqual(op.goal_of(WORDS), "Plan the alpha release; What goes first, and what can wait?")
        self.assertEqual(op.named_in("alpha and Beta, not alphabet or the beta-twos", ["alpha", "beta", "beta-two"]),
                         ["alpha", "beta"])
        with self.assertRaises(h.HelperError):
            op.goal_of("  \n ")

    def test_the_oldest_of_what_landed_is_left_out_first_and_nothing_else(self):
        root = self.tmp
        for name, size in (("a", 10), ("b", 10), ("c", 10)):
            (root / name).write_text("x" * size)
        entries = [op.entry("a", "chapter", "chapter"), op.entry("b", "old", "landed", "2026-10-01T00:00:00+00:00"),
                   op.entry("c", "new", "landed", "2026-10-02T00:00:00+00:00")]
        kept, left = op.fit(root, entries, (0, 0), budget=(10, 25))
        self.assertEqual([e["path"] for e in kept], ["a", "c"])
        self.assertEqual([e["path"] for e in left], ["b"])
        kept, left = op.fit(root, entries, (0, 0), budget=(1, 5))
        self.assertEqual([e["path"] for e in kept], ["a"])  # never a chapter: bale's caps speak for themselves
        self.assertEqual(len(left), 2)

    def test_the_digest_names_each_unsorted_drop_or_none(self):
        root = self.tmp / "office"
        root.mkdir()
        self.assertEqual(odg.in_tray_section(root), ["## The in-tray", "", "- none"])
        (root / "floor-plan").mkdir()
        (root / "floor-plan/manifest.toml").write_text('[projects.alpha]\npath = "/nowhere"\n')
        tray = root / "in-tray"
        tray.mkdir()
        page = "# Drop: {h}\n\n- dropped: 2026-10-14 09:0{n}\n- project: {p}\n- via: stdin\n- status: {s}\n\n## Text\n\nx\n"
        (tray / "2026-10-14-a.md").write_text(page.format(h="a", n=1, p="Alpha", s="unsorted"))
        (tray / "2026-10-14-b.md").write_text(page.format(h="b", n=2, p="the beta report", s="unsorted"))
        (tray / "2026-10-14-c.md").write_text(page.format(h="c", n=3, p="none given", s="unsorted"))
        (tray / "2026-10-14-d.md").write_text(page.format(h="d", n=4, p="alpha", s="sorted"))
        self.assertEqual(odg.in_tray_section(root), [
            "## The in-tray", "",
            "- 2026-10-14-a.md (project: alpha)",
            "- 2026-10-14-b.md (project: \"the beta report\", none of this office's)",
            "- 2026-10-14-c.md"])

    def test_the_home_screen_has_a_planner_key_and_a_withdraw_key_only_when_one_can_be(self):
        lines, menu = hs.render_page([], [], 1)
        self.assertIn(("p", "office", ["start", "new", "--planner"]), menu)
        self.assertNotIn("w", [k for k, _, _ in menu])
        lines, menu = hs.render_page([], [], 1, withdrawable=1)
        self.assertIn(("w", "office", ["withdraw"]), menu)
        self.assertIn("[w] withdraw a session never worked", "\n".join(lines))
        self.assertTrue(all(len(l) <= 80 for l in lines))


# --- what the office gathers -------------------------------------------------------------------

class TestTheGathering(LandCase):
    """An office scoping alpha, with a handbook chapter, folders on the desk
    on alpha and on the office, a sitting's page filed, and walkthroughs
    filed before and after it."""

    def commit(self, *paths, message="test"):
        self.e.git(self.root, "add", "--", *paths)
        self.e.git(self.root, "commit", "-qm", message, "--", *paths)

    def setUp(self):
        super().setUp()
        (self.root / "handbook").mkdir(exist_ok=True)
        (self.root / "handbook/alpha.md").write_text("# alpha\n\n## Front sheet\n\nalpha.\n\n## Facts\n")
        self.office_job = self.e.run("open", "tidy-desk", "--title", "Tidy the desk", cwd=self.root, check=0).stdout.strip()
        self.old = self.e.run("open", "old-job", "--title", "An old job", "--lane", "alpha", cwd=self.root,
                              check=0).stdout.strip()
        (self.root / self.old / "walkthrough.md").write_text("# Walkthrough\n\nold\n")
        self.commit("handbook", self.old, message="office land: the old pages")
        (self.root / "notepad").mkdir(exist_ok=True)
        (self.root / "notepad/2026-10-14-plan-sitting.md").write_text("# words\n")
        (self.root / "notepad/2026-10-14-plan-sitting-2.md").write_text("# words, continued\n")
        self.commit("notepad", message="office start: the sitting's words")
        (self.root / self.folder / "walkthrough.md").write_text("# Walkthrough\n\nnew\n")
        self.commit(self.folder, message="office land: the new pages")

    def test_the_set_and_its_order_for_a_project(self):
        got = op.gather(self.root, ["alpha"], own=None)
        self.assertEqual([(e["kind"], e["path"]) for e in got], [
            ("chapter", "handbook/alpha.md"),
            ("folder", f"{self.folder}/folder.md"),
            ("folder", f"{self.old}/folder.md"),
            ("landed", f"{self.folder}/walkthrough.md"),
            ("sitting", "notepad/2026-10-14-plan-sitting.md"),
            ("sitting", "notepad/2026-10-14-plan-sitting-2.md")])
        # The old walkthrough was filed before the last sitting's page: not since.
        self.assertNotIn(f"{self.old}/walkthrough.md", [e["path"] for e in got])
        # The sitting's own folder rides whole, so it is not gathered again.
        self.assertNotIn(f"{self.folder}/folder.md", [e["path"] for e in op.gather(self.root, ["alpha"], own=self.folder)])

    def test_the_office_itself_gathers_the_folders_that_name_no_project(self):
        got = [e["path"] for e in op.gather(self.root, [op.OFFICE])]
        self.assertIn(f"{self.office_job}/folder.md", got)
        self.assertNotIn(f"{self.folder}/folder.md", got)
        self.assertNotIn("handbook/alpha.md", got)
        self.assertTrue(op.would_ask(self.root, ["alpha"]))


# --- the sitting from his words, piped ----------------------------------------------------------

class TestPlannerFromWords(LandCase):
    def planner(self, *more, words=WORDS, check=0):
        return self.run_office("start", "new", "--planner", "--words", words, *more, check=check)

    def test_his_words_send_a_read_only_sitting_with_what_rides_said(self):
        (self.root / "handbook").mkdir(exist_ok=True)
        (self.root / "handbook/alpha.md").write_text("# alpha\n\n## Front sheet\n\nalpha.\n\n## Facts\n")
        self.e.git(self.root, "add", "handbook")
        self.e.git(self.root, "commit", "-qm", "chapter")
        proc = self.planner()
        m = re.search(r"^Packed (\S+) for desk/(\S+)\.$", proc.stdout, re.M)
        sid, name = m.group(1), m.group(2)
        self.assertTrue(sid.endswith("-sitting-001"), sid)
        md = (self.root / "desk" / name / "folder.md").read_text()
        self.assertIn("- lane: alpha\n", md)
        self.assertIn("- provisional: title, size, goal\n", md)
        self.assertIn("> Plan the alpha release\n", md)
        self.assertIn(f"- {sid}\n", md)
        self.assertIn("your words name alpha: what rides is gathered for it", proc.stderr)
        self.assertIn("What rides with the sitting, and why", proc.stderr)
        self.assertIn("handbook/alpha.md: alpha's handbook chapter", proc.stderr)
        self.assertIn(f"{self.folder}/folder.md: folder 1, ", proc.stderr)
        self.assertIn("A read-only sitting lands nothing; when it is over: office land", proc.stdout)
        files = request_members(tray_of(proc.stdout, sid))
        brief = files["README.md"].decode()
        self.assertIn("> Plan the alpha release\n> What goes first, and what can wait?\n", brief)
        self.assertIn("## What rides, and why", brief)
        self.assertIn("- handbook/alpha.md: alpha's handbook chapter", brief)
        manifest = json.loads(files["manifest.json"])
        self.assertEqual(manifest["goal"], "Plan the alpha release; What goes first, and what can wait?")
        self.assertEqual(manifest["resolved_scope"], [])
        shipped = set(manifest["context_included"])
        for path in ("context/handbook/alpha.md", f"context/{self.folder}/folder.md",
                     f"context/desk/{name}/folder.md", "context/drafting-table/digest.md"):
            self.assertIn(path, shipped)
        # No project's tree rides with a sitting from his words: what the office holds about it does.
        self.assertNotIn("context/src/a.py", shipped)

    def test_piped_it_asks_nothing_and_names_its_flags(self):
        desk = sorted(p.name for p in (self.root / "desk").iterdir())
        proc = self.run_office("start", "new", "--planner", check=1)
        self.assertIn("a planner sitting takes what you want it for, in your words: --words TEXT", proc.stderr)
        proc = self.planner(words="Plan the next quarter", check=1)
        self.assertIn("your words name none of this office's projects (alpha), and what rides depends on which: "
                      "--about PROJECT, or --in-office", proc.stderr)
        proc = self.run_office("start", "--planner", "--words", WORDS, check=1)
        self.assertIn("name the folder that records the sitting: office start new --planner", proc.stderr)
        proc = self.planner("--on", "alpha", check=1)
        self.assertIn("a planner sitting is packed in the office and lands nothing; --about alpha", proc.stderr)
        proc = self.run_office("start", self.name, "--about", "alpha", check=1)
        self.assertIn("--about says what a planner sitting concerns, so it goes with --planner", proc.stderr)
        self.assertEqual(sorted(p.name for p in (self.root / "desk").iterdir()), desk)
        # The flag twins send it: --in-office answers "the office itself".
        proc = self.planner("--in-office", words="Plan the next quarter")
        self.assertIn("Packed ", proc.stdout)

    def test_a_folder_on_the_desk_records_it_and_keeps_his_words(self):
        proc = self.run_office("start", self.name, "--planner", "--words", "Is the login fix the right order?",
                               "--about", "alpha", check=0)
        sid = re.search(r"^Packed (\S+) for desk/", proc.stdout, re.M).group(1)
        md = self.folder_md()
        self.assertIn(f"- {sid}\n", md)
        self.assertIn("for a planner sitting:\n\n> Is the login fix the right order?\n", md)
        self.assertIn(f"office start --planner: his words in {self.name}", self.subjects(6))


# --- the sort offered first ----------------------------------------------------------------------

class TestTheSortFirst(LandCase):
    def drop(self, text="Can you look at the alpha docs?"):
        self.run_office("drop", "--project", "alpha", input=text, check=0)

    def test_taken_the_sort_and_the_sitting_go_out_in_one_motion(self):
        self.drop()
        proc = self.run_office("start", "new", "--planner", "--words", WORDS, "--sort-first", check=0)
        packed = re.findall(r"^Packed (\S+) for (.+?)\.?$", proc.stdout, re.M)
        self.assertEqual(len(packed), 2, proc.stdout)
        self.assertIn("in-tray-sort", packed[0][0])
        self.assertTrue(packed[1][0].endswith("-sitting-001"))
        self.assertIn("sending the in-tray's sort out first (1 drop(s)), then the sitting", proc.stderr)
        self.assertIn("the sort's opener is not copied: the sitting's goes on the clipboard after it", proc.stderr)
        self.assertLess(proc.stdout.index(packed[0][0]), proc.stdout.index("Packed " + packed[1][0]))

    def test_piped_with_neither_flag_the_sitting_goes_alone_and_says_why(self):
        self.drop()
        proc = self.run_office("start", "new", "--planner", "--words", WORDS, check=0)
        self.assertEqual(len(re.findall(r"^Packed \S+ for ", proc.stdout, re.M)), 1)
        self.assertIn("1 unsorted drop(s) wait in the in-tray; piped, the sitting goes as it is and carries them "
                      "(--sort-first sends the in-tray's sort out first)", proc.stderr)
        proc = self.run_office("start", "new", "--planner", "--words", WORDS + " again", "--no-sort-first", check=0)
        self.assertIn("--no-sort-first: they ride with the sitting, and no sort goes first", proc.stderr)

    def test_a_sort_already_out_is_said_and_nothing_is_offered(self):
        self.drop()
        self.run_office("start", "--sort", check=0)
        proc = self.run_office("start", "new", "--planner", "--words", WORDS, "--sort-first", check=0)
        self.assertIn("and the in-tray's sort is out already", proc.stderr)
        self.assertEqual(len(re.findall(r"^Packed \S+ for ", proc.stdout, re.M)), 1)

    def test_not_a_sitting_not_offered(self):
        self.drop()
        proc = self.run_office("start", self.name, "--on", "alpha", "--goal", "g", check=0)
        self.assertNotIn("sort", " ".join(l for l in proc.stderr.splitlines() if "offer" in l))
        proc = self.run_office("start", self.name, "--on", "alpha", "--goal", "g", "--sort-first", check=1)
        self.assertIn("--sort-first and --no-sort-first answer the offer made before a sitting", proc.stderr)

    def test_the_digest_lists_the_drop(self):
        self.drop()
        page = self.run_office("digest").stdout  # 3: the fake bale has no stats here; the page is written
        section = page.split("## The in-tray\n\n", 1)[1].split("\n\n", 1)[0]
        self.assertRegex(section, r"^- \d{4}-\d{2}-\d{2}-can-you-look-at-the-alpha-docs\.md \(project: alpha\)$")


# --- a planner's bundle names where it lands ----------------------------------------------------

class TestBundleLands(LandCase):
    def bundle(self, lands, stem="2026-10-16-docs"):
        brief = f"# Brief\n\nTidy the docs.\n\n{lands}\n"
        return bundle_file(self.downloads, stem, ["Tidy the docs", "--slug", "docs", "--write", "docs",
                                                  "--constraint", ob.PROJECT_CONSTRAINT], brief=brief)

    def test_a_bundle_that_says_where_goes_out_asking_nothing(self):
        b = self.bundle("--- LANDS alpha, folder 1 ---")
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn(f"the bundle's brief says where it lands: on alpha, recorded in folder 1, ", proc.stderr)
        self.assertIn("(its LANDS line); neither question is asked", proc.stderr)
        sid = re.search(rf"^Packed (\S+) for desk/{re.escape(self.name)}\.$", proc.stdout, re.M).group(1)
        self.assertIn(f"- {sid}\n", self.folder_md())

    def test_a_new_folder_and_the_office(self):
        b = bundle_file(self.downloads, "2026-10-16-plan", ["Plan the docs", "--slug", "plan-docs", "--read-only"],
                        brief="# Brief\n\n--- LANDS the office, a new folder ---\n")
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn("the bundle's brief says where it lands: in the office, recorded in a new folder", proc.stderr)
        m = re.search(r"^Packed (\S+) for desk/(\S+)\.$", proc.stdout, re.M)
        md = (self.root / "desk" / m.group(2) / "folder.md").read_text()
        self.assertIn("# Plan the docs\n", md)

    def test_a_place_or_a_folder_the_office_does_not_hold_is_said_and_asked(self):
        b = self.bundle("--- LANDS gamma, folder 1 ---", stem="2026-10-16-g")
        proc = self.run_office("start", "--bundle", str(b), check=1)
        self.assertIn("says it lands on gamma, which this office does not scope (it scopes: alpha); where it lands "
                      "is asked", proc.stderr)
        self.assertIn("say where the work lands: --in-office, or --on PROJECT (alpha)", proc.stderr)
        b = self.bundle("--- LANDS alpha, folder 99 ---", stem="2026-10-16-h")
        proc = self.run_office("start", "--bundle", str(b), check=1)
        self.assertIn("names folder 99, which this office does not hold; which job is asked", proc.stderr)
        self.assertIn("name the folder: office start FOLDER", proc.stderr)

    def test_a_flag_still_sets_its_field(self):
        b = self.bundle("--- LANDS the office, folder 1 ---", stem="2026-10-16-f")
        proc = self.run_office("start", "--bundle", str(b), "--on", "alpha", check=0)
        self.assertIn("the bundle's brief says it lands in the office; --on alpha says otherwise, and stands", proc.stderr)
        self.assertIn("Packed ", proc.stdout)


# --- a session never worked, withdrawn ----------------------------------------------------------

class TestWithdraw(LandCase):
    def test_piped_it_is_named_and_needs_its_answer(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        proc = self.run_office("withdraw", check=1)
        self.assertIn("piped input is never asked: office withdraw FOLDER --yes withdraws it", proc.stderr)
        self.assertIn(f"Withdraw folder 1, ", proc.stderr)
        self.assertTrue(self.fake.is_open(self.proj, sid))
        proc = self.run_office("withdraw", self.name, "--yes", check=0)
        self.assertIn(f"Withdrawn: {sid} is closed in alpha, never worked; bale records it as abandoned.", proc.stdout)
        (_, argv, _), = self.fake.calls_of("unlock")
        self.assertEqual(argv, ["unlock", sid, "--reason", "abandoned", "--json"])
        self.assertFalse(self.fake.is_open(self.proj, sid))
        self.assertRegex(self.folder_md(), rf"(?m)^- \d{{4}}-\d{{2}}-\d{{2}} withdrawn: {sid}, never worked; closed in "
                                           r"bale by office withdraw \(abandoned\)$")
        self.assertIn(f"{self.folder} was opened for this session alone and records no other; it stays on the desk, "
                      f"and when its job is not to be done, this line closes it: office close {self.name} --retired",
                      proc.stderr)
        self.assertEqual(h.folder_check(self.root)[0], [])

    def test_a_response_waiting_or_an_apply_begun_is_never_offered(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        self.machine_downloads()
        response_tarball(self.e.downloads, sid, {"src/a.py": "x\n"})
        proc = self.run_office("withdraw", "--yes", check=1)
        self.assertIn("a response for it is in your downloads", proc.stderr)
        self.assertEqual(self.fake.calls_of("unlock"), [])
        proc = self.run_office("withdraw", self.name, "--yes", check=1)
        self.assertIn(f"{sid} (desk/{self.name}) cannot be withdrawn: a response for it is in your downloads", proc.stderr)

    def machine_downloads(self):
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'downloads = ["{self.e.downloads}"]\n')
        self.e.downloads.mkdir(parents=True, exist_ok=True)

    def test_held_by_bale_is_bales(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "x\n"}, validation="fail")
        self.run_office("land", sid, check=1)
        proc = self.run_office("withdraw", sid, "--yes", check=1)
        self.assertIn("cannot be withdrawn: bale has started to apply it", proc.stderr)


# --- on his terminal -------------------------------------------------------------------------------

class TestOnATerminal(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def clipboard(self):
        clip = self.e.tmp / "clipboard.txt"
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'downloads = ["{self.downloads}"]\nclipboard_command = "tee {clip}"\n'
                                          f'paste_command = "cat {clip}"\n')
        return clip

    def test_the_p_key_asks_his_words_and_nothing_else(self):
        self.clipboard()
        code, seen = on_a_terminal(self, [str(self.e.office_bin)], self.root, self.e.env, [
            (b"Your key: ", "p"),
            (b"What you want a planner for, in your own words (--words)", "Plan the alpha release"),
            (b"  > ", ""),
            (b"Return brings your home screen back; q leaves: ", "q"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("[p] a planner sitting, in your words", seen)
        self.assertIn("What rides with the sitting, and why", seen)
        self.assertRegex(seen, r"Packed \d{4}-\d{2}-\d{2}-plan-the-alpha-release-sitting-001 for desk/")
        for question in ("Which folder", "What the sitting concerns", "Title, in a few words", "(--size)", "(--goal)",
                         "Send the in-tray"):
            self.assertNotIn(question, seen)
        self.assertIn("the opener is on the clipboard", seen)

    def test_start_planner_offers_the_folder_by_key_and_the_project_only_when_it_matters(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "--planner"], self.root, self.e.env, [
            (b"in your own words (--words)", "Plan the next quarter"),
            (b"  > ", ""),
            (b"What the sitting concerns, by its key (--about PROJECT, or --in-office)", "1"),
            (b"Which folder, by its key; a plain return mints a new one", "1"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("[2] the office itself", seen)
        self.assertIn("[2] a new folder, from these words", seen)
        sid = re.search(rf"Packed (\S+) for desk/{re.escape(self.name)}\.", seen).group(1)
        self.assertIn(f"- {sid}\n", self.folder_md())

    def test_the_sort_is_offered_first_and_the_sittings_opener_is_the_copy_left(self):
        clip = self.clipboard()
        self.run_office("drop", "--project", "alpha", input="Can you look at the alpha docs?", check=0)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "new", "--planner"], self.root,
                                   self.e.env, [
            (b"in your own words (--words)", "Plan the alpha release"),
            (b"  > ", ""),
            (b"Send the in-tray's sort out first, then this sitting, by its key", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("1 unsorted drop(s) wait in the in-tray.", seen)
        packed = re.findall(r"Packed (\S+) for ", seen)
        self.assertEqual(len(packed), 2, seen)
        self.assertIn("in-tray-sort", packed[0])
        self.assertIn(f"Goal, verbatim from the request manifest: Plan the alpha release", clip.read_text())

    def test_bare_start_sends_a_bundle_that_says_where_without_a_question(self):
        self.clipboard()
        bundle_file(self.downloads, "2026-10-16-docs", ["Tidy the docs", "--slug", "docs", "--write", "docs",
                                                        "--constraint", ob.PROJECT_CONSTRAINT],
                    brief="# Brief\n\nTidy the docs.\n\n--- LANDS alpha, folder 1 ---\n")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"(--bundle FILE) [return skips]:", "1"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("(its LANDS line); neither question is asked", seen)
        self.assertNotIn("Which job", seen)
        self.assertNotIn("Where the work lands", seen)
        self.assertRegex(seen, rf"Packed \S+-docs-001 for desk/{re.escape(self.name)}\.")

    def test_the_w_key_names_the_session_and_asks_once(self):
        self.clipboard()
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        # The home screen shows the key while the session can be withdrawn
        # (a key is one keypress there; the pty helper types a line, so the
        # verb the key runs is driven on its own below).
        code, seen = on_a_terminal(self, [str(self.e.office_bin)], self.root, self.e.env, [(b"Your key: ", "q")])
        self.assertEqual(code, 0, seen)
        self.assertIn("[w] withdraw a session never worked", seen)
        self.assertNotIn(sid, seen, "the home screen names a session by its folder")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "withdraw"], self.root, self.e.env, [
            (b"Close it in bale, for good? It cannot be undone (--yes) [no]:", "yes"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Withdraw folder 1, fix-login: ", seen)
        self.assertIn(f"Withdrawn: {sid} is closed in alpha", seen)
        self.assertFalse(self.fake.is_open(self.proj, sid))
        # Declined, nothing is closed.
        sid = self.start(self.name, "--on", "alpha", "--goal", "again", "--write", "docs")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "withdraw"], self.root, self.e.env, [
            (b"Close it in bale, for good? It cannot be undone (--yes) [no]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"nothing was closed: {sid} stays out", seen)
        self.assertTrue(self.fake.is_open(self.proj, sid))


if __name__ == "__main__":
    unittest.main()
