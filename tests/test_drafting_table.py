"""Tests for the drafting table (blueprint session 4b, first half): the
space arriving in an office with the first verb that writes it, office
moves, the blueprint, rider and agenda verbs, office rulings and office
evidence, the desk's drafting-table gates and its last two groups, office
status's drafting-table and charter checks, the one-writer rule on every
script that mints a number or appends to a page, and office slip's title.

Every test works under its own temporary HOME. bale is never needed: the
one-writer rule reads a fake bale replaying home-office's captured status
line with a test's own open session, and office blueprint close packs with
office start's fake packing bale. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import json
import os
import pathlib
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, h  # noqa: E402
from test_read_side import FakeBale  # noqa: E402
from test_desk_verbs import Office, office_status_fixture, history_of, fields_of, terminal  # noqa: E402
from test_start import FakePackBale, tar_names  # noqa: E402

import office_drafting as od  # noqa: E402

SITTING = "2026-10-05-plan-sitting-001"
DT = "drafting-table"


def write_page(root, name, extra=""):
    """A drafting-table page as a sitting would leave it: the template,
    then its records."""
    p = pathlib.Path(root) / DT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(od.render_page(name) + extra)
    return p


def commit_as_session(o, sid, msg="a sitting's pages"):
    """Commit everything as bale commits a session's work."""
    o.e.git(o.root, "add", "-A")
    o.e.git(o.root, "commit", "-qm", f"[bale {sid}] {msg}")


# --- units ---------------------------------------------------------------------------

class TestUnits(unittest.TestCase):
    def test_a_title_from_a_numbered_list_line(self):
        # The case 2026-10-04-bale-src-slips-001 reported.
        self.assertEqual(od.clean_title("2. **A HOLD cause class (watch 15, confirmed)**"),
                         "A HOLD cause class (watch 15, confirmed)")
        for text, want in (("- *note* this", "note this"), ("10) plain", "plain"), ("a*b stays", "a*b stays"),
                           ("\n\n  * __x__ y\nsecond", "x y")):
            self.assertEqual(od.clean_title(text), want, text)

    def test_glob_touches(self):
        for glob, entry, want in (("bin/bale_pack.py", "bin", True), ("bin/bale_pack.py", "bin/bale_pack.py", True),
                                  ("bin/*.py", "bin/x.py", True), ("bin/*.py", "bin", True), ("bin/", "bin/x.py", True),
                                  ("docs/*.md", "bin", False), ("bin/x.py", "lib", False), ("lib/a.py", ".", True),
                                  ("lib/a.py", "", True), ("binx/a", "bin", False)):
            self.assertEqual(od.glob_touches(glob, entry), want, (glob, entry))

    def test_an_insertion_is_one_run_of_bytes_anywhere(self):
        old = b"head\n## Disposed\n"
        self.assertIsNone(h.insertion_problem(old, b"head\n## agenda 1 - x\n\n## Disposed\n"))
        self.assertIsNone(h.insertion_problem(old, old + b"tail\n"))
        self.assertIsNone(h.insertion_problem(old, old))
        self.assertIn("changed bytes", h.insertion_problem(old, b"HEAD\n## a\n## Disposed\n"))
        self.assertIn("cut to", h.insertion_problem(old, b"head\n"))

    def test_fenced_examples_are_never_records(self):
        t = od.Table(tempfile.mkdtemp())
        lines = od.render_page("riders.md").splitlines()
        self.assertEqual(od.rider_blocks(lines, 0, len(lines)), [])
        self.assertEqual(od.records(od.render_page("rulings.md").splitlines(), od.RULING_HEAD_RE, t._ruling), [])
        self.assertEqual(od.decomposition((REPO / "templates/blueprint.md").read_text().splitlines()), [])

    def test_the_move_grammar(self):
        t = od.Table(tempfile.mkdtemp())
        mv = od.parse_move('open "riders verbs" class=code size=small lane="office-src: bin/" after="folder 3" '
                           'after="agenda 7" candidate=yes', 4, t)
        self.assertEqual(mv["title"], "riders verbs")
        self.assertEqual(mv["keys"]["after"], ["folder 3", "agenda 7"])
        self.assertEqual(od.move_argv(mv), ["--title", "riders verbs", "--class", "code", "--size", "small", "--lane",
                                            "office-src: bin/", "--after", "folder 3", "--after", "agenda 7",
                                            "--candidate"])
        self.assertEqual(od.move_argv(od.parse_move('split folder 4 into="5, 6"', 1, t)),
                         ["folder 4", "--split", "5,6"])
        self.assertEqual(od.move_argv(od.parse_move('absorb folder 4 into=9', 1, t)),
                         ["folder 4", "--into", "folder 9"])
        self.assertEqual(od.move_argv(od.parse_move('gate folder 2 after="agenda 1" serializes-after=3', 1, t)),
                         ["after", "agenda 1", "serializes-after", "folder 3"])
        for bad, words in (('frob folder 1', "is not a move"), ('open size=small', "title first"),
                           ('retire folder 1', "says why"), ('gate folder 1', "at least one gate"),
                           ('close folder x', "folder N"), ('open "x" size=huge', "size is one of"),
                           ('open "x" colour=red', "not a key"), ('open "x', "quoting"),
                           ('open "x" blueprint=2026-01-01-none', "names no blueprint"),
                           ('open "x" line=2', "goes with blueprint="), ('split folder 1 into=2', "two or more")):
            with self.assertRaises(h.HelperError, msg=bad) as cm:
                od.parse_move(bad, 1, t)
            self.assertIn(words, str(cm.exception), bad)


FLOOR_PLAN = '''# Floor plan of this office. The office command finds an office by
# this file and reads it on every run. Only office upgrade writes
# migrated_to. The founding session sets the timezone; renovation
# sessions change the spaces; office projects add writes the
# [projects] table. Nothing else should change it.

[office]
name = "home-office"
built_from = "0.4.0"
migrated_to = "0.4.0"
built_at = "2026-09-30T23:39:47Z"
timezone = "America/Indianapolis"

[spaces.profile]
path = "profile.md"
hung = true
filed = false

[spaces.drawer]
path = "drawer"
hung = false
filed = false

# The projects this office scopes on this machine: a name and the path
# of its repo, absolute or ~-relative. office projects add writes them.

[projects.office-src]
path = "~/office-src"
rides = ["/home/occupant/nisaba-src/blueprints"]
'''


class TestArrivalInAFloorPlan(unittest.TestCase):
    """Arrival on a floor plan shaped as home-office's is (the probe's
    copy, cut short): the space goes after the last space, before the
    projects' comment, and nothing else changes."""

    def test_the_space_is_added_and_every_other_byte_kept(self):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, d, True)
        m = d / "manifest.toml"
        m.write_text(FLOOR_PLAN)
        self.assertTrue(od.add_space_to_floor_plan(m, od.catalog_entry()))
        text = m.read_text()
        block = ('\n[spaces.drafting-table]\npath = "drafting-table"\nhung = false\nfiled = ["drafting-table/rulings.md", '
                 '"drafting-table/evidence.md", "drafting-table/watch-log.md", "drafting-table/blueprints/*/close.md"]\n')
        at = FLOOR_PLAN.index("\n# The projects")
        self.assertEqual(text, FLOOR_PLAN[:at] + block + FLOOR_PLAN[at:])
        self.assertEqual(tomllib.loads(text)["spaces"]["drafting-table"]["filed"][-1], "drafting-table/blueprints/*/close.md")
        self.assertFalse(od.add_space_to_floor_plan(m, od.catalog_entry()))
        self.assertEqual(m.read_text(), text)

    def test_the_trigger_is_added_in_order(self):
        d = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, d, True)
        b = d / "bale.toml"
        b.write_text('# head\n\n[pack]\ninclude_group = "hung"\ninclude_group_triggers = ["desk", "drawer"]\n'
                     'include_group_pulls = ["profile.md"]\n')
        self.assertTrue(od.add_include_trigger(b, "drafting-table"))
        self.assertIn('include_group_triggers = ["desk", "drafting-table", "drawer"]\n', b.read_text())
        self.assertFalse(od.add_include_trigger(b, "drafting-table"))
        self.assertIsNone(od.add_include_trigger(d / "none.toml", "drafting-table"))


# --- the space arriving -----------------------------------------------------------------

class TestArrival(unittest.TestCase):
    def test_the_first_rider_brings_the_drafting_table_in_one_commit(self):
        o = Office(self)
        out = o.run("status").stdout
        self.assertIn("drafting:   none in this office; it arrives with the first verb that writes it", out)
        proc = o.run("rider", "add", "Name the sweep commit", "--source", "proposal 2026-10-04-x-001 #2",
                     "--rides", "bin/bale_apply.py")
        self.assertEqual(proc.stdout, "rider 1\n")
        self.assertIn("the drafting table arrives in this office", proc.stderr)
        files = o.e.git(o.root, "show", "--name-only", "--format=%s", "HEAD").split()
        self.assertEqual(o.e.git(o.root, "log", "-1", "--format=%s"), "office rider add: rider 1\n")
        self.assertEqual(sorted(f for f in files if "/" in f or "." in f),
                         ["bale.toml", "drafting-table/README.md", "drafting-table/riders.md", "floor-plan/manifest.toml"])
        o.clean()
        self.assertEqual((o.root / DT / "README.md").read_text(), (REPO / "templates/drafting-table-README.md").read_text())
        plan = tomllib.loads((o.root / "floor-plan/manifest.toml").read_text())["spaces"][DT]
        self.assertEqual(plan, {"path": DT, "hung": False, "filed": od.catalog_entry()["filed"]})
        self.assertIn(DT, tomllib.loads((o.root / "bale.toml").read_text())["pack"]["include_group_triggers"])
        status = o.run("status").stdout
        self.assertIn("hung items: bale.toml include group matches the floor plan", status)
        self.assertIn("drafting:   matches the install's catalog; 0 blueprint(s), 1 rider(s), 0 agenda item(s) open", status)
        self.assertIn("drafting-table/rulings.md, drafting-table/evidence.md", status)
        # The next write touches only its page.
        o.run("rider", "add", "Second", "--source", "notepad/2026-10-05.md")
        self.assertEqual(o.e.git(o.root, "show", "--name-only", "--format=", "HEAD").split(), ["drafting-table/riders.md"])

    def test_status_names_a_drafting_table_out_of_step_with_the_catalog(self):
        o = Office(self)
        (o.root / DT).mkdir()
        (o.root / DT / "notes.md").write_text("x\n")
        out = o.run("status").stdout
        self.assertIn("drafting:   3 problem(s) against the install's catalog:", out)
        self.assertIn("drafting-table/ exists but the floor plan does not list it", out)
        self.assertIn("drafting-table/README.md is missing", out)
        self.assertIn("drafting-table/notes.md is not a page the drafting table holds", out)


# --- riders ---------------------------------------------------------------------------

class TestRiders(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)
        self.o.open("one", "--size", "small")
        self.o.open("two", "--size", "small")

    def riders(self, *args):
        return self.o.run("riders", *args).stdout

    def test_add_carry_consumed_and_numbers_across_page_and_folders(self):
        o = self.o
        proposal = "- **What:** keep the sweep commit's name\n- **Why:** it is cited\n- **Scope hints:** bin/\n"
        self.assertEqual(o.run("rider", "add", "--source", "proposal 2026-10-04-x-001 #2", "--rides", "bin/*.py",
                               input=proposal).stdout, "rider 1\n")
        page = (o.root / DT / "riders.md").read_text()
        self.assertIn("### rider 1 - What: keep the sweep commit's name\n\n- source: proposal 2026-10-04-x-001 #2\n"
                      "- rides: bin/*.py\n- status: queued\n\n" + proposal + "\n- ", page)
        o.run("rider", "add", "For two", "--source", "folder 2", "--carrier", "2")
        self.assertIn("- rides: folder 2", (o.root / DT / "riders.md").read_text())
        o.run("rider", "carry", "rider 1", "--folder", "folder 2")
        self.assertEqual(o.e.git(o.root, "log", "-1", "--format=%s"), "office rider carry: rider 1 -> folder 2\n")
        page = (o.root / DT / "riders.md").read_text()
        self.assertIn("\n- rider 1 -> folder 2\n", page)
        self.assertNotIn("keep the sweep", page)
        two = o.text(next(p for p in (o.root / "desk").iterdir() if p.name.endswith("-two")).relative_to(o.root))
        riders = two.split("\n## Riders\n", 1)[1].split("\n## History\n", 1)[0]
        self.assertIn("### rider 1 - What: keep the sweep commit's name", riders)
        self.assertIn(proposal, riders)
        self.assertRegex(riders, r"- status: carried\n")
        self.assertRegex(riders, r"- \d{4}-\d\d-\d\d queued: office rider add\n- \d{4}-\d\d-\d\d carried: folder 2\n")
        self.assertEqual(history_of(two)[-1][1:], ("carried", "rider 1"))
        # Numbers count the page, its pointers and every folder.
        self.assertEqual(o.run("rider", "add", "Third", "--source", "folder 1").stdout, "rider 3\n")
        o.run("rider", "consumed", "1", "2026-10-06-sweep-001")
        two = o.text(next(p for p in (o.root / "desk").iterdir() if p.name.endswith("-two")).relative_to(o.root))
        self.assertRegex(two, r"- status: consumed\n")
        self.assertRegex(two, r"- \d{4}-\d\d-\d\d consumed: 2026-10-06-sweep-001\n")
        self.assertEqual(history_of(two)[-1][1:], ("consumed", "rider 1 at 2026-10-06-sweep-001"))
        out = self.riders()
        self.assertIn("rider 2  queued  For two  (rides folder 2; the riders page)", out)
        self.assertIn("rider 1 -> folder 2", out)
        self.assertIn("rider 1  consumed  What: keep the sweep commit's name  (rides bin/*.py; desk/", out)
        o.clean()

    def test_refusals_name_what_to_do(self):
        o = self.o
        o.run("rider", "add", "A", "--source", "folder 1")
        self.assertIn("is on the riders page, carried by no folder yet; office rider carry 1 --folder N",
                      o.run("rider", "consumed", "1", "2026-10-06-x-001", check=1).stderr)
        self.assertIn("no rider 9", o.run("rider", "carry", "9", "--folder", "1", check=1).stderr)
        o.run("close", "one")
        self.assertIn("no folder matching", o.run("rider", "carry", "1", "--folder", "one", check=1).stderr)
        self.assertIn("rider add needs --source", o.run("rider", "add", "B", check=1).stderr)
        self.assertIn("--rides and --carrier are two carriers",
                      o.run("rider", "add", "B", "--source", "x", "--rides", "a", "--carrier", "1", check=1).stderr)
        o.run("rider", "carry", "1", "--folder", "two")
        self.assertIn("already in desk/", o.run("rider", "carry", "1", "--folder", "two", check=1).stderr)
        o.run("rider", "consumed", "1", "2026-10-06-x-001")
        self.assertIn("already consumed", o.run("rider", "consumed", "1", "2026-10-07-x-001", check=1).stderr)
        self.assertIn("not a session id", o.run("rider", "consumed", "1", "bad-sid", check=1).stderr)

    def test_an_orphan_is_reported_and_consuming_it_in_the_cabinet_only_adds_lines(self):
        o = self.o
        o.run("rider", "add", "Left behind", "--source", "folder 1")
        o.run("rider", "carry", "1", "--folder", "two")
        o.run("close", "two")
        desk = o.run("desk").stdout
        self.assertIn("Orphaned riders (in a closed folder, never consumed):\n  rider 1  Left behind  (filing-cabinet/", desk)
        self.assertIn("1 orphaned rider(s), in a closed folder and never consumed: office riders --orphans", o.run().stdout)
        self.assertIn("rider 1  carried  Left behind", self.riders("--orphans"))
        name = next((o.root / "filing-cabinet").glob("*-two")).name
        before = (o.root / "filing-cabinet" / name / "folder.md").read_text()
        o.run("rider", "consumed", "1", "2026-10-06-late-001")
        after = (o.root / "filing-cabinet" / name / "folder.md").read_text()
        # Only lines added: every line before is still there, in order.
        b, a = before.splitlines(), after.splitlines()
        it = iter(a)
        self.assertTrue(all(any(x == y for y in it) for x in b))
        self.assertEqual(len(a), len(b) + 2)
        self.assertIn("- status: carried", after)  # the filed folder's status line is left as it was
        self.assertNotIn("Orphaned", o.run("desk").stdout)
        self.assertIn("no orphaned riders", self.riders("--orphans"))
        self.assertIn("folders:    ", o.run("status").stdout)
        self.assertNotIn("problem", o.run("status").stdout.split("folders:", 1)[1].split("\n", 1)[0])

    def test_on_a_terminal_rider_add_asks_and_explains(self):
        o = self.o
        env = dict(o.e.env)
        code, screen = terminal(env, str(o.root), [str(o.e.office_bin), "rider", "add"],
                                [("Title, in a few words (office rider add TITLE)", "?"),
                                 ("Title, in a few words (office rider add TITLE)", "Name the sweep"),
                                 ("Source: where it came from (--source)", "notepad/2026-10-05.md"),
                                 ("What carries it", "folder 2"),
                                 ("Its text, in a line", "")])
        self.assertEqual(code, 0, screen)
        self.assertIn("a rider is small work with a named carrier", " ".join(screen.lower().split()))
        page = (o.root / DT / "riders.md").read_text()
        self.assertIn("### rider 1 - Name the sweep\n\n- source: notepad/2026-10-05.md\n- rides: folder 2\n", page)

    def test_forecast_lists_the_queued_riders_a_pack_carries(self):
        o = self.o
        o.run("rider", "add", "Pack", "--source", "x", "--rides", "bin/bale_pack.py")
        o.run("rider", "add", "Docs", "--source", "x", "--rides", "docs/*.md")
        o.run("rider", "add", "Named", "--source", "x", "--carrier", "folder 1")
        out = self.riders("--forecast", "bin/", "lib/x.py")
        self.assertIn("rider 1  Pack  (rides bin/bale_pack.py; the forecast's bin/)", out)
        self.assertNotIn("Docs", out)
        self.assertNotIn("Named", out)
        self.assertIn("none: no queued rider", self.riders("--forecast", "share"))


# --- the agenda ---------------------------------------------------------------------------

class TestAgenda(unittest.TestCase):
    def test_numbers_never_reused_entries_above_disposed_and_the_check(self):
        o = Office(self)
        o.open("job")
        self.assertEqual(o.run("agenda", "add", "Where does a chat land?", "--source", "notepad/2026-10-05.md",
                               "--waiting", "folder 1").stdout, "agenda 1\n")
        page = (o.root / DT / "agenda.md").read_text()
        self.assertTrue(page.endswith("## agenda 1 - Where does a chat land?\n\n- source: notepad/2026-10-05.md\n"
                                      "- waiting: folder 1\n\n## Disposed\n"), page)
        # A sitting rules on it: the entry leaves, a dated line stays.
        p = o.root / DT / "agenda.md"
        p.write_text(page.split("## agenda 1")[0] + "## Disposed\n\n- 2026-10-05 agenda 1 -> ruling 2026-10-05-chats\n")
        commit_as_session(o, SITTING)
        self.assertEqual(o.run("agenda", "add", "--source", "folder 1", "--title", "Second",
                               input="The longer question,\nin two lines.\n").stdout, "agenda 2\n")
        text = p.read_text()
        self.assertLess(text.index("## agenda 2 - Second"), text.index("## Disposed"))
        self.assertIn("The longer question,\nin two lines.\n", text)
        o.clean()
        # An uncommitted hand edit is not this script's to commit.
        p.write_text(p.read_text().replace("Agenda", "AGENDA", 1))
        proc = o.run("agenda", "add", "Third", "--source", "x", check=1)
        self.assertIn("differs from its committed bytes other than by this entry", proc.stderr)
        self.assertIn("agenda add needs --source", o.run("agenda", "add", "x", check=1).stderr)


# --- blueprints -------------------------------------------------------------------------

class TestBlueprints(unittest.TestCase):
    def test_open_ratify_and_the_charter_check(self):
        o = Office(self)
        o.run("note", "the arc is ratified as assumed")
        page = next((o.root / "notepad").glob("*.md")).relative_to(o.root)
        out = o.run("blueprint", "open", "rider-verbs", "--title", "The rider verbs").stdout.strip()
        bid = out.split()[1]
        self.assertRegex(bid, r"^\d{4}-\d\d-\d\d-rider-verbs$")
        md = o.root / DT / "blueprints" / bid / "blueprint.md"
        text = md.read_text()
        self.assertTrue(text.startswith("# The rider verbs\n\n## Charter\n\n" + od.CHARTER_PLACEHOLDER + "\n"))
        self.assertRegex(text, r"## History\n\n- \d{4}-\d\d-\d\d drafted: office blueprint open\n$")
        self.assertIn("charter is empty", o.run("blueprint", "ratify", bid, "--sid", SITTING, check=1).stderr)
        md.write_text(text.replace(od.CHARTER_PLACEHOLDER, "Riders get verbs; done when they run."))
        o.e.git(o.root, "commit", "-qam", "the charter")
        self.assertIn("is not one in this office",
                      o.run("blueprint", "ratify", bid, "--words", "notepad/2026-01-01-none.md", check=1).stderr)
        self.assertIn("say where the ratifying words are", o.run("blueprint", "ratify", bid, check=1).stderr)
        o.run("blueprint", "ratify", bid, "--words", str(page))
        text = md.read_text()
        charter = text.split("## Charter\n", 1)[1].split("\n## ", 1)[0]
        self.assertRegex(charter, rf"Riders get verbs; done when they run.\n\n- ratified: \d{{4}}-\d\d-\d\d, words at {page}\n")
        self.assertRegex(text, rf"- \d{{4}}-\d\d-\d\d ratified: {page}\n$")
        self.assertEqual(o.e.git(o.root, "log", "-1", "--format=%s"), f"office blueprint ratify: {bid}\n")
        o.clean()
        self.assertIn("was ratified on", o.run("blueprint", "ratify", bid, "--sid", SITTING, check=1).stderr)
        self.assertIn("charters:   1 ratified charter(s), unchanged since ratification", o.run("status").stdout)
        # A later commit that changes the charter is named; so is an
        # uncommitted change.
        md.write_text(md.read_text().replace("done when they run", "done when they all run"))
        self.assertIn("uncommitted changes to the charter ratified in", o.run("status").stdout)
        o.e.git(o.root, "commit", "-qam", "a hand edit")
        out = o.run("status").stdout
        self.assertRegex(out, r"charters:   1 change\(s\) to ratified charters:\n  drafting-table/blueprints/\S+: commit "
                              r"[0-9a-f]{10} \(\d{4}-\d\d-\d\d\) changed the charter ratified in")
        # The decomposition and history stay live.
        self.assertIn("rider-verbs", o.run("blueprint", "open", "rider-verbs", check=1).stderr)

    def test_blueprint_close_sends_the_close_sitting_out_through_start(self):
        o = Office(self)
        fake = FakePackBale(o.e.tmp)
        o.e.env["PATH"] = fake.path(o.e.env["PATH"])
        bid = o.run("blueprint", "open", "arc", "--title", "An arc", "--charter", "Do the arc.").stdout.split()[1]
        member = o.open("member", "--blueprint", bid, "--size", "small")
        write_page(o.root, "rulings.md")
        o.e.git(o.root, "add", "-A"); o.e.git(o.root, "commit", "-qm", "rulings page")
        proc = o.run("blueprint", "close", bid)
        self.assertIn("When the response comes back: office land", proc.stdout)
        close = next(p for p in (o.root / "desk").iterdir() if p.name.endswith("-close-arc"))
        text = (close / "folder.md").read_text()
        self.assertEqual(text.splitlines()[0], f"# Close blueprint {bid}")
        self.assertIn(("source", f"blueprint {bid}"), fields_of(text))
        self.assertIn(("blueprint", bid), fields_of(text))
        cwd, argv = fake.packs()[-1]
        writes = [argv[i + 1] for i, a in enumerate(argv) if a == "--write"]
        includes = [argv[i + 1] for i, a in enumerate(argv) if a == "--include"]
        self.assertEqual(writes, [f"desk/{close.name}", "notepad", DT])
        self.assertEqual(includes, [f"desk/{close.name}", f"{DT}/blueprints/{bid}", member, f"{DT}/rulings.md"])
        tray = next((o.e.home / "out-tray").iterdir())
        self.assertIn("office-src-install/templates/close-report.md",
                      tar_names(tray / "context-office-src-install.tar.gz"))
        request = next(tray.glob("request-*.tar.gz"))
        with tarfile.open(request) as t:
            brief = t.extractfile("request-001/README.md").read().decode()
        self.assertIn(f"`drafting-table/blueprints/{bid}/close.md`", brief)
        self.assertIn(f"member folders: {member}", brief)
        (o.root / DT / "blueprints" / bid / "close.md").write_text("# Close\n")
        self.assertIn("is closed already", o.run("blueprint", "close", bid, check=1).stderr)


# --- desk moves ----------------------------------------------------------------------------

MOVES = '''
- [ ] 2026-10-05 open "the riders listing" class=code size=small lane="office-src: bin/" blueprint={bid} after="folder 1"
- [ ] 2026-10-05 open "an idea" candidate=yes
- [ ] 2026-10-05 gate folder 2 after="agenda 1" consumer="blueprint {bid}"
- [ ] 2026-10-05 queue folder 4
- [ ] 2026-10-05 retire folder 1 why="premise corrected"
'''


class TestMoves(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)
        o = self.o
        o.open("one", "--size", "small")
        o.open("two", "--size", "small")
        self.bid = o.run("blueprint", "open", "arc", "--title", "An arc", "--charter", "Do it.").stdout.split()[1]
        md = o.root / DT / "blueprints" / self.bid / "blueprint.md"
        md.write_text(md.read_text().replace("## Ordering", "- the riders listing\n- other work\n\n## Ordering"))
        o.run("agenda", "add", "A question", "--source", "folder 2")
        o.e.git(o.root, "commit", "-qam", "decomposition")

    def test_every_move_applied_ticked_and_committed_once(self):
        o = self.o
        write_page(o.root, "moves.md", MOVES.format(bid=self.bid))
        commit_as_session(o, SITTING)
        self.assertIn(f"5 desk move(s) pending (5 from `{SITTING}`): office moves applies them", o.run().stdout)
        desk = o.run("desk").stdout
        self.assertIn(f"Pending desk moves (5, 5 from `{SITTING}`; office moves applies them):", desk)
        self.assertRegex(desk, rf"  line \d+: 2026-10-05 retire folder 1 why=\"premise corrected\"  \(from `{SITTING}`\)")
        dry = o.run("moves", "--dry-run").stdout
        self.assertEqual(len(re.findall(r"^  line \d+: 2026-10-05 ", dry, re.M)), 5)
        o.clean()
        o.run("moves")
        o.clean()
        self.assertEqual(o.e.git(o.root, "log", "-1", "--format=%s"), "office moves: 5 desk move(s) from drafting-table/moves.md\n")
        self.assertEqual(o.e.git(o.root, "log", "-2", "--format=%s").splitlines()[1], f"[bale {SITTING}] a sitting's pages")
        page = (o.root / DT / "moves.md").read_text()
        for line, n in ((0, 3), (1, 4), (2, 2), (3, 4), (4, 1)):
            want = MOVES.format(bid=self.bid).strip().splitlines()[line].replace("- [ ]", "- [x]") + f" -> folder {n}"
            self.assertIn(want + "\n", page)
        bp = (o.root / DT / "blueprints" / self.bid / "blueprint.md").read_text()
        self.assertIn("- the riders listing -> folder 3\n- other work\n", bp)
        listing = o.text(next(p for p in (o.root / "desk").iterdir() if p.name.endswith("the-riders-listing")).relative_to(o.root))
        self.assertIn(("blueprint", self.bid), fields_of(listing))
        self.assertRegex(history_of(listing)[0][2], rf"^office moves: drafting-table/moves.md line \d+, decided 2026-10-05; "
                                                    rf"blueprint {self.bid}, decomposition line 1$")
        idea = o.text(next(p for p in (o.root / "desk").iterdir() if p.name.endswith("an-idea")).relative_to(o.root))
        self.assertEqual([v for _, v, _ in history_of(idea)], ["candidate", "queued"])
        self.assertIn(("status", "queued"), fields_of(idea))
        two = o.text(next(p for p in (o.root / "desk").iterdir() if p.name.endswith("-two")).relative_to(o.root))
        self.assertIn(("after", "agenda 1"), fields_of(two))
        self.assertEqual([x[1:] for x in history_of(two)[-2:]],
                         [("gated", "after agenda 1"), ("gated", f"consumer blueprint {self.bid}")])
        self.assertTrue(next((o.root / "filing-cabinet").glob("*-one")))
        self.assertIn("folders:    4 on the desk and in the filing cabinet; every status agrees", o.run("status").stdout)
        self.assertIn("no desk moves pending", o.run("moves").stderr)
        out = o.run("desk", "--blueprint", self.bid).stdout
        self.assertIn(f"blueprint {self.bid}: An arc (not ratified)", out)
        self.assertIn("waiting for folder 1 (retired: premise corrected)", out)
        self.assertIn("  line 2: other work", out)

    def test_a_line_that_does_not_read_refuses_before_anything_is_applied(self):
        o = self.o
        write_page(o.root, "moves.md", '\n- [ ] 2026-10-05 open "fine"\n- [ ] 2026-10-05 retire folder 1\n')
        commit_as_session(o, SITTING)
        proc = o.run("moves", check=1)
        self.assertRegex(proc.stderr, r"moves.md line \d+: retire says why")
        self.assertIn("nothing was applied", proc.stderr)
        o.clean()
        self.assertFalse(list((o.root / "desk").glob("*-fine")))
        self.assertIn("1 line(s) of drafting-table/moves.md do not read", o.run().stdout)

    def test_a_line_that_cannot_apply_stops_there_with_the_earlier_ones_committed(self):
        o = self.o
        write_page(o.root, "moves.md", '\n- [ ] 2026-10-05 open "fine"\n- [ ] 2026-10-05 queue folder 2\n'
                                       '- [ ] 2026-10-05 close folder 1\n')
        commit_as_session(o, SITTING)
        proc = o.run("moves", check=1)
        self.assertIn("folder 2 is queued, not a candidate", proc.stderr)
        self.assertRegex(proc.stderr, r"stopped at drafting-table/moves.md line \d+.*1 move\(s\) before it are applied")
        o.clean()
        page = (o.root / DT / "moves.md").read_text()
        self.assertIn('- [x] 2026-10-05 open "fine" -> folder 3\n- [ ] 2026-10-05 queue folder 2\n- [ ] 2026-10-05 close', page)
        self.assertFalse(list((o.root / "filing-cabinet").glob("*-one")))

    def test_the_one_writer_rule_holds_moves_and_the_minting_scripts(self):
        o = self.o
        write_page(o.root, "moves.md", '\n- [ ] 2026-10-05 open "fine"\n')
        commit_as_session(o, SITTING)
        (o.root / ".bale").mkdir()
        fake = FakeBale(o.e.tmp, {str(o.root): office_status_fixture(o.e.tmp, [SITTING], {SITTING: [DT, "notepad"]})})
        o.e.env["PATH"] = fake.path(o.e.env["PATH"])
        for args in (("moves",), ("rider", "add", "x", "--source", "y"), ("agenda", "add", "x", "--source", "y"),
                     ("blueprint", "open", "b"), ("blueprint", "ratify", self.bid, "--sid", SITTING)):
            proc = o.run(*args, check=1)
            self.assertIn(f"{SITTING} holds", proc.stderr, args)
            self.assertIn("the one-writer rule", proc.stderr, args)
        o.clean()
        # A session on one folder does not hold the riders page.
        fake2 = FakeBale(o.e.tmp, {str(o.root): office_status_fixture(o.e.tmp, [SITTING], {SITTING: ["desk/x"]})})
        o.e.env["PATH"] = fake2.path(o.e.env["PATH"])
        o.run("rider", "add", "x", "--source", "y")


# --- the desk's drafting-table gates -------------------------------------------------------

class TestDeskGates(unittest.TestCase):
    def test_blueprint_agenda_and_ruling_gates_resolve(self):
        o = Office(self)
        bid = o.run("blueprint", "open", "arc", "--title", "An arc").stdout.split()[1]
        o.run("agenda", "add", "Q", "--source", "x")
        o.open("on-arc", "--after", f"blueprint {bid}")
        o.open("on-agenda", "--after", "agenda 1")
        o.open("on-ruling", "--after", "ruling 2026-10-05-chats")
        o.open("on-nothing", "--after", "agenda 9")
        parked = o.run("desk").stdout.split("\nParked:\n", 1)[1]
        self.assertIn(f"waiting for blueprint {bid} (open, not ratified): An arc\n    folder 1  ", parked)
        self.assertIn("waiting for agenda 1 (awaiting a sitting): Q\n    folder 2  ", parked)
        self.assertIn("ERROR: folder 3: after ruling 2026-10-05-chats names no ruling in rulings.md", parked)
        self.assertIn("ERROR: folder 4: after agenda 9 names nothing on the agenda", parked)
        o.run()  # the walk-in records today
        # A sitting rules, files the ruling and closes the arc.
        write_page(o.root, "rulings.md", "\n## 2026-10-05-chats\n\n- ruled: 2026-10-05\n- source: x\n\n**Chats.** Yes.\n")
        ag = o.root / DT / "agenda.md"
        ag.write_text(ag.read_text().split("## agenda 1")[0] + "## Disposed\n\n- 2999-01-01 agenda 1 -> ruling 2026-10-05-chats\n")
        (o.root / DT / "blueprints" / bid / "close.md").write_text(f"# Close: An arc\n\n- blueprint: {bid}, closed 2999-01-01 by {SITTING}\n")
        out = o.run("desk").stdout
        ready = out.split("\nReady:\n", 1)[1].split("\n\n", 1)[0]
        for n in (1, 2, 3):
            self.assertIn(f"  folder {n}  ", ready)
        self.assertIn(f"gate cleared: blueprint {bid} closed 2999-01-01", ready)
        self.assertIn("gate cleared: agenda 1 ruled (ruling 2026-10-05-chats) 2999-01-01", ready)
        self.assertIn("ERROR: folder 4", out)


# --- rulings and evidence ------------------------------------------------------------------

RULINGS = f'''
## 2026-10-05-chat-lands-in-folder

- ruled: 2026-10-05
- source: light block {SITTING} [1]
- grounds: evidence 1, folder 1
- landed: folder 9

**A chat lands in its folder.** As transcript.md.

## 2026-10-06-chat-lands-elsewhere

- ruled: 2026-10-06
- source: 2026-10-06-sit-001
- supersedes: 2026-10-05-chat-lands-in-folder (scope: where only)

**A chat lands in the notepad.** Not the folder.

## 2026-10-07-chat-amend

- ruled: 2026-10-07
- amends: 2026-10-06-chat-lands-elsewhere
- source: 2026-10-06-sit-001 round 1

**Only long chats.** Short ones are noted.

## 2026-10-05-chat-lands-in-folder - derived - 2026-10-08

- into: office-src doctrine/OFFICE.md section 5
'''

EVIDENCE = f'''
## 1. The desk lied about order.

- filed: 2026-10-05 by {SITTING}
- from: 2026-10-04-friction-second-trip-001

It did.

## 1 - occurrence - 2026-10-06

- from: 2026-10-06-x-001
- attributed-to: planner

Again.

## 1 · occurrence — 2026-10-07

- from: 2026-10-07-x-001
- attributed-to: worker

## 2. Unsourced.

- filed: 2026-10-05

## 7 - occurrence - 2026-10-07

- attributed-to: nobody
'''


class TestLedgers(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)
        self.o.open("one")
        write_page(self.o.root, "rulings.md", RULINGS)
        write_page(self.o.root, "evidence.md", EVIDENCE)

    def test_rulings_list_render_and_check(self):
        o = self.o
        out = o.run("rulings").stdout
        self.assertIn("Rulings (2):", out)
        self.assertIn("ruling 2026-10-05-chat-lands-in-folder  A chat lands in its folder.  [superseded by "
                      "2026-10-06-chat-lands-elsewhere; derived into office-src doctrine/OFFICE.md section 5]", out)
        self.assertIn("ruling 2026-10-06-chat-lands-elsewhere  A chat lands in the notepad.  [amended 1x]", out)
        one = o.run("rulings", "ruling 2026-10-06-chat-lands-elsewhere").stdout
        self.assertIn("  amended by 2026-10-07-chat-amend (2026-10-07): Only long chats.", one)
        self.assertIn("  supersedes: 2026-10-05-chat-lands-in-folder (scope: where only)", one)
        first = o.run("rulings", "2026-10-05-chat-lands-in-folder").stdout
        self.assertIn("  superseded by ruling 2026-10-06-chat-lands-elsewhere (scope: where only)", first)
        self.assertIn("  derived into office-src doctrine/OFFICE.md section 5 (2026-10-08)", first)
        self.assertIn("is an amendment of", o.run("rulings", "2026-10-07-chat-amend", check=1).stderr)
        self.assertIn("no ruling 2026-01-01-x", o.run("rulings", "2026-01-01-x", check=1).stderr)
        proc = o.run("rulings", "--check", check=1)
        self.assertIn("1 citation(s) of", proc.stdout)
        self.assertRegex(proc.stdout, r"drafting-table/rulings.md:\d+: folder 9: no folder 9 on the desk")
        self.assertIn("session ids not checked: this office reads no registry", proc.stdout)

    def test_evidence_list_render_and_problems(self):
        o = self.o
        out = o.run("evidence").stdout
        self.assertIn(f"evidence 1. The desk lied about order.  (filed 2026-10-05 by {SITTING}; occurrences: planner 1, "
                      "worker 1)", out)
        self.assertIn("evidence 2 names no session", out)
        self.assertIn("points at evidence 7, which is not an entry", out)
        self.assertIn("attributed to 'nobody'", out)
        one = o.run("evidence", "evidence 1").stdout
        self.assertIn("  occurrences: planner 1, worker 1", one)
        self.assertIn("  2026-10-06 occurrence: from: 2026-10-06-x-001; attributed-to: planner. Again.", one)
        self.assertIn("no evidence 9", o.run("evidence", "9", check=1).stderr)


# --- office slip's title ------------------------------------------------------------------------

class TestSlipTitle(unittest.TestCase):
    def test_a_slip_from_a_numbered_list_is_titled_by_its_words(self):
        o = Office(self)
        text = "2. **A HOLD cause class (watch 15, confirmed).** bale stamps none."
        page = o.run("slip", "--about", "bale-src", text).stdout.strip()
        self.assertRegex(page, r"^suggestion-box/\d{4}-\d\d-\d\d-a-hold-cause-class-watch-15-confirmed\.md$")
        body = (o.root / page).read_text()
        self.assertTrue(body.startswith("# A HOLD cause class (watch 15, confirmed). bale stamps none.\n"), body)
        self.assertIn(text, body)  # the text stays as typed


# --- the catalog and the doctrine --------------------------------------------------------------

class TestCatalogAndDoctrine(unittest.TestCase):
    def test_the_verbs_are_built_and_the_doctrine_says_so(self):
        v = tomllib.loads((REPO / "share/verbs.toml").read_text())["verbs"]
        for name in ("moves", "blueprint-open", "blueprint-ratify", "blueprint-close", "rider-add", "rider-carry",
                     "rider-consumed", "riders", "agenda-add", "rulings", "evidence"):
            self.assertTrue(v[name]["built"], name)
        self.assertFalse(v["digest"]["built"])
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        for words in ("it arrives with the first verb that writes it", "No script mints a ruling or an evidence entry",
                      "`office rulings --check` resolves them all", "a rider in a closed folder that was never consumed "
                      "is an orphan", "a rider, an agenda item, a blueprint, a desk move applied"):
            self.assertIn(words, doctrine)

    def test_every_page_has_its_template_and_the_catalog_matches_the_pages(self):
        for name, template in od.PAGES.items():
            self.assertTrue((REPO / "templates" / template).is_file(), template)
        filed = tomllib.loads((REPO / "share/spaces.toml").read_text())["spaces"][DT]["filed"]
        for f in filed:
            if "*" not in f:
                self.assertIn(f.split("/", 1)[1], od.PAGES)


if __name__ == "__main__":
    unittest.main()
