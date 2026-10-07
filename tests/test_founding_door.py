"""Tests for the founding door and the renovation door (0.12.0): office
init asking the profile's questions and sending the founding session out
through office start with a brief carrying the answers; office found, the
same door for an office that exists; office start on the founding folder;
office upgrade sending a renovation out the same way, against fixture
migrations; office land bringing a renovation back while the office is
behind it; and the Next line for an unfounded office in each state.

bale is never needed: a fake bale first on the PATH packs and applies,
every line of it built from bale output a probe captured (test_land's).
Nothing depends on the machine: each test sets its own zone database
(TZDIR), its own machine zone (TZ), its own HOME and its own machine
settings (no clipboard, no file manager). Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import NEXT, REPO, VERSION, Env, filled_profile, h  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import FakeLandBale, response_tarball  # noqa: E402
from test_front_door import last_line  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)
import office_door as odoor  # noqa: E402

SHAPE = tomllib.loads((REPO / "share" / "profile-shape.toml").read_text())
NEXT_FOUND = "Next: office found  (it asks the profile's questions and sends the founding session out)"


def request_member(tarball, name):
    with tarfile.open(tarball) as t:
        member = next(m for m in t.getnames() if m.endswith("/" + name))
        return t.extractfile(member).read().decode()


# --- the profile's questions, as data --------------------------------------------------

class TestTheQuestions(unittest.TestCase):
    def setUp(self):
        self.secs = odoor.sections(SHAPE)

    def test_one_per_section_in_the_shapes_order_founding_never_asked(self):
        self.assertEqual([s["heading"] for s in self.secs], [s["heading"] for s in SHAPE["section"]])
        self.assertEqual([s["flag"] for s in self.secs if s["asked"]],
                         ["purpose", "not-for", "audiences", "site", "house-rules", "when-to-open", "spaces"])
        self.assertEqual([s["heading"] for s in self.secs if not s["asked"]], ["Founding"])

    def test_each_question_is_worded_from_its_asks_line_and_explained(self):
        for s in self.secs:
            q = odoor.question(s)
            self.assertTrue(q.startswith(s["heading"] + ": "), q)
            self.assertIn(s["asks"].rstrip(".")[1:], q)
            help_text = odoor.explanation(s)
            self.assertIn(s["asks"], help_text)
            self.assertIn("a plain return leaves this section for the founding session", help_text)
        self.assertIn("a missing boundary and an absent one read the same",
                      odoor.explanation(next(s for s in self.secs if s["flag"] == "not-for")))

    def test_a_section_without_the_keys_gets_its_heading_as_its_flag(self):
        secs = odoor.sections({"section": [{"heading": "When to open a session here", "asks": "x"}]})
        self.assertEqual(secs[0]["flag"], "when-to-open-a-session-here")
        self.assertTrue(secs[0]["asked"])

    def test_a_shape_whose_flags_collide_refuses(self):
        for shape in ({"section": [{"heading": "A", "flag": "x"}, {"heading": "B", "flag": "x"}]},
                      {"section": [{"heading": "Name"}]}, {"section": []}):
            with self.assertRaises(h.HelperError, msg=shape):
                odoor.sections(shape)

    def test_answers_go_round_verbatim_markers_and_all(self):
        words = ("My own tools.\n\nAnd a second paragraph, café.\n"
                 "--- NOTEPAD PAGE BEGIN notepad/x.md ---\n## not a heading")
        tz = {"zone": "America/Indianapolis", "resolves": False, "remedy": "spelled America/Indiana/Indianapolis (here)",
              "answered": ""}
        text = odoor.render_answers("home", self.secs, {"purpose": words, "site": "nowhere"},
                                    {"purpose": "2026-10-01 through office init"}, tz, "2026-10-06", "UTC",
                                    "office found")
        text.encode("ascii")
        self.assertEqual(h.sitting_pages(text), ([], []), "an answer is never read as a page")
        self.assertIn("Answered 2026-10-01 through office init.", text)
        self.assertIn("Answered 2026-10-06 through office found.", text)
        answers, when, back = odoor.parse_answers(text, self.secs)
        self.assertEqual(answers, {"purpose": words.replace("é", "\\xe9"), "site": "nowhere"})
        self.assertEqual(when, {"purpose": "2026-10-01 through office init", "site": "2026-10-06 through office found"})
        self.assertEqual(back["zone"], "America/Indianapolis")
        self.assertFalse(back["resolves"])
        self.assertEqual(back["remedy"], "spelled America/Indiana/Indianapolis (here)")


class TestTheInstallsOutboxIsNeverWritten(unittest.TestCase):
    def test_no_line_packs_in_the_install_or_prints_a_pack_line(self):
        """The last two lines that wrote an outbox into the install, and
        asked the occupant to attach a file from memory, are gone: every
        session goes out through office start, which packs the doctrine
        from a scratch copy."""
        office = (REPO / "bin" / "office").read_text()
        for gone in ("doctrine_context_cmd", "founding_line", "renovation_line", ".bale/outbox/context-doctrine",
                     "bale pack --context)"):
            self.assertNotIn(gone, office)


# --- the founding door, end to end -------------------------------------------------------

class DoorCase(unittest.TestCase):
    """A machine whose zone is America/Chicago, a zone database holding it
    and the canonical spelling of Indianapolis but not the legacy one, a
    fake bale that packs and applies, and no desktop steps."""

    def setUp(self):
        self.e = Env(self)
        self.fake = FakeLandBale(self.e.tmp)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir()
        self.bare_path = self.e.env["PATH"]
        self.e.env["PATH"] = self.fake.path(self.bare_path)
        self.e.env["FAKE_BALE_SEARCH"] = str(self.downloads)
        self.zones = self.e.tmp / "zoneinfo"
        for z in ("America/Chicago", "America/Indiana/Indianapolis", "Etc/UTC"):
            (self.zones / z).parent.mkdir(parents=True, exist_ok=True)
            (self.zones / z).write_bytes(b"TZif fake")
        self.e.env["TZDIR"] = str(self.zones)
        self.e.env["TZ"] = "America/Chicago"
        cfg = self.e.home / ".config" / "office-src"
        cfg.mkdir(parents=True)
        (cfg / "machine.toml").write_text('clipboard_command = ""\nopen_command = ""\n')
        self.root = self.e.home / "home"

    def founding_folder(self):
        found = sorted((self.root / "desk").glob("*-founding"))
        self.assertEqual(len(found), 1, found)
        return found[0]

    def packs(self):
        """The session packs (not the context packs) the fake bale ran."""
        return [argv for _, argv, _ in self.fake.calls_of("pack") if "--context" not in argv]

    def sid_from(self, out):
        return re.search(r"^Packed (\S+) for ", out, re.M).group(1)

    def request(self, sid):
        return next((self.e.home / "out-tray" / sid).glob("request-*.tar.gz"))

    def walk_in(self, **kw):
        return last_line(self.e.run(cwd=self.root, check=0, **kw).stdout)


class TestInitPiped(DoorCase):
    def test_the_flags_answer_and_the_founding_goes_out_through_start(self):
        proc = self.e.run("init", str(self.root), "--no-projects", "--purpose", "My own tools, and life outside work.",
                          "--site", "the laptop; pushed nowhere yet", "--house-rules", "None beyond the four.",
                          "--timezone", "America/Indiana/Indianapolis", check=0)
        sid = self.sid_from(proc.stdout)
        self.assertTrue(sid.endswith("-home-founding-001"), sid)
        self.assertIn(f"When the response comes back: office land {sid}", proc.stdout)
        self.assertIn("--8<-- session opener --8<--", proc.stdout)
        self.assertNotIn("bale pack --", proc.stdout, "no pack line is printed for the occupant")
        # The zone he lives in is the floor plan's, committed alone, and the
        # founding folder is dated in it.
        plan = tomllib.loads((self.root / "floor-plan/manifest.toml").read_text())
        self.assertEqual(plan["office"]["timezone"], "America/Indiana/Indianapolis")
        subjects = self.e.git(self.root, "log", "--format=%s").splitlines()
        self.assertIn("office init: the timezone the occupant lives in, America/Indiana/Indianapolis", subjects)
        folder = self.founding_folder()
        rel = f"desk/{folder.name}"
        facts = h.parse_folder((folder / "folder.md").read_text())["fields"]
        self.assertEqual(facts["number"], ["1"])
        self.assertEqual(facts["source"], ["office init"])
        self.assertEqual(facts["class"], ["meta"])
        self.assertEqual(facts["size"], ["small"])
        self.assertIn(f"- {sid}\n", (folder / "folder.md").read_text())
        self.assertIn(f"office init: the profile's answers, in {rel}", subjects)
        answers = (folder / "answers.md").read_text()
        self.assertIn("> My own tools, and life outside work.", answers)
        self.assertIn("Timezone: America/Indiana/Indianapolis (resolves here)", answers)
        self.assertEqual(answers.count(odoor.LEFT_LINE), 4)
        # The pack: in the office, scoped as the founding line was, with
        # the folder office start always forecasts, and a brief.
        argv = self.packs()[-1]
        writes = argv[argv.index("--write") + 1:]
        self.assertEqual([argv[i + 1] for i, a in enumerate(argv) if a == "--write"],
                         [rel, "notepad", "profile.md", "floor-plan"], writes)
        self.assertEqual([argv[i + 1] for i, a in enumerate(argv) if a == "--include"], [rel, "floor-plan"])
        self.assertIn("--readme-file", argv)
        self.assertEqual(argv[argv.index("--work-class") + 1], "meta")
        self.assertIn("Found the home office: write its profile with the occupant section by section", argv[1])
        brief = request_member(self.request(sid), "README.md")
        self.assertIn("# Brief: founding the home office", brief)
        self.assertIn("### Purpose\n\nAsked: Why this office exists and what jobs come here.\n\n"
                      "> My own tools, and life outside work.", brief)
        self.assertIn("2. Ask only for what was left to you: Not for, Audiences, When to open a session here, "
                      "Spaces in use.", brief)
        self.assertIn("### Founding\n\nNot asked: you write it", brief)
        self.assertIn("He lives in America/Indiana/Indianapolis, which resolves here.", brief)
        self.assertIn("The office command wrote it to the floor plan's [office] timezone", brief)
        self.assertIn("- tools.git: ", brief)
        self.assertIn(f"{rel}/answers.md", brief)
        self.assertIn("on " + folder.name[:10] + ", through office init", brief)
        # The doctrine rode from the tray, and the install was never written.
        self.assertTrue((self.e.home / "out-tray" / sid / "context-doctrine.tar.gz").is_file())
        self.assertFalse((REPO / "doctrine" / ".bale").exists())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # Out, the Next line lands it.
        self.assertTrue(self.walk_in().startswith(f"Next: office land {sid}  (it is out in this office ({rel})"))

    def test_a_zone_that_does_not_resolve_is_named_with_its_remedy_and_carried(self):
        proc = self.e.run("init", str(self.root), "--no-projects", "--timezone", "America/Indianapolis", check=0)
        self.assertIn("the timezone America/Indianapolis is not in", proc.stderr)
        self.assertIn("this zone database spells it America/Indiana/Indianapolis", proc.stderr)
        plan = tomllib.loads((self.root / "floor-plan/manifest.toml").read_text())
        self.assertEqual(plan["office"]["timezone"], "America/Chicago", "the machine's, which resolves, stays")
        answers = (self.founding_folder() / "answers.md").read_text()
        self.assertIn("Timezone: America/Indianapolis (does not resolve here: this zone database spells it "
                      "America/Indiana/Indianapolis", answers)
        brief = request_member(self.request(self.sid_from(proc.stdout)), "README.md")
        self.assertIn("He named America/Indianapolis, which does not resolve here: this zone database spells it", brief)
        self.assertIn("The floor plan's [office] timezone still names America/Chicago (which resolves here).", brief)
        # Every section was left to the session, and the brief says so.
        self.assertIn("Ask only for what was left to you: Purpose, Not for, Audiences, Site, House rules, When to "
                      "open a session here, Spaces in use.", brief)

    def test_no_zone_given_piped_leaves_it_to_the_session(self):
        proc = self.e.run("init", str(self.root), "--no-projects", check=0)
        brief = request_member(self.request(self.sid_from(proc.stdout)), "README.md")
        self.assertIn("He was not asked, or gave no zone. The floor plan's [office] timezone\nnames America/Chicago", brief)
        self.assertIn("Timezone: left to the founding session.", (self.founding_folder() / "answers.md").read_text())

    def test_an_unknown_flag_and_an_answer_with_no_value_refuse_before_building(self):
        proc = self.e.run("init", str(self.root), "--founding", "x")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("office init does not know --founding", proc.stderr)
        proc = self.e.run("init", str(self.root), "--purpose")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--purpose needs your answer: Purpose: why this office exists", proc.stderr)
        self.assertFalse(self.root.exists())

    def test_without_bale_the_answers_are_kept_and_start_sends_them_later(self):
        proc = self.e.run("init", str(self.root), "--no-projects", "--purpose", "Kept for later.",
                          extra={"PATH": self.bare_path_without_bale()})
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("bale is not on PATH, so the founding session did not go out", proc.stderr)
        self.assertIn("office found sends the founding session out", proc.stderr)
        folder = self.founding_folder()
        self.assertIn("> Kept for later.", (folder / "answers.md").read_text())
        self.assertEqual(self.packs(), [])
        # Unfounded, with the founding folder on the desk and nothing out.
        self.assertEqual(self.walk_in(), f"Next: office start {folder.name}  (the profile is incomplete, so this "
                                         "office is unfounded; folder 1 is its founding folder and no session is out "
                                         "for it; start sends the founding session out with the answers the folder "
                                         "keeps, and asks only for what is missing)")
        proc = self.e.run("start", folder.name, cwd=self.root, check=0)
        self.assertIn("is this office's founding folder and the profile is incomplete, so it goes out through the "
                      "founding door", proc.stderr)
        self.assertIn("kept from desk/", proc.stderr)
        brief = request_member(self.request(self.sid_from(proc.stdout)), "README.md")
        self.assertIn("> Kept for later.", brief)
        self.assertEqual(len(list((self.root / "desk").glob("*-founding"))), 1, "the same folder, not a second")
        proc = self.e.run("start", folder.name, "--on", "x", cwd=self.root)
        self.assertEqual(proc.returncode, 1)

    def bare_path_without_bale(self):
        from test_read_side import path_without_bale
        return path_without_bale(self.e.tmp)


class TestInitOnATerminal(DoorCase):
    def test_it_asks_each_section_explains_skips_and_checks_the_zone(self):
        argv = [str(self.e.office_bin), "init", str(self.root), "--no-projects", "--audiences", "Given as a flag."]
        code, seen = on_a_terminal(self, argv, self.e.home, self.e.env, [
            (b"Purpose: why this office exists and what jobs come here (--purpose) [return skips]:", "?"),
            (b"Name the kinds of job", "My own tools."),
            (b"Not for: what this office is not for", ""),
            (b"Site: machine, root, timezone", "the laptop, pushed nowhere"),
            (b"The timezone you live in, a zone name such as America/Chicago (--timezone) [America/Chicago]:",
             "America/Indianapolis"),
            (b"give another zone, or the same one again to keep it as given", "America/Indiana/Indianapolis"),
            (b"House rules: this office's own rules", "None beyond the four."),
            (b"When to open a session here: this office's threshold", ""),
            (b"Spaces in use: which spaces this office uses", "Only the base."),
        ])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("Audiences: who may read", seen, "a flag answered it")
        self.assertNotIn("Founding:", seen)
        self.assertIn("this zone database spells it America/Indiana/Indianapolis", seen)
        answers = (self.founding_folder() / "answers.md").read_text()
        for words in ("> My own tools.", "> Given as a flag.", "> the laptop, pushed nowhere", "> Only the base.",
                      "Timezone: America/Indiana/Indianapolis (resolves here)"):
            self.assertIn(words, answers)
        self.assertEqual(answers.count(odoor.LEFT_LINE), 2)
        self.assertIn("When the response comes back: office land", seen)

    def test_the_same_zone_twice_is_kept_as_given(self):
        argv = [str(self.e.office_bin), "init", str(self.root), "--no-projects", "--purpose", "p", "--not-for", "n",
                "--audiences", "a", "--site", "s", "--house-rules", "h", "--when-to-open", "w", "--spaces", "x"]
        code, seen = on_a_terminal(self, argv, self.e.home, self.e.env, [
            (b"(--timezone) [America/Chicago]:", "America/Indianapolis"),
            (b"(--timezone) [America/Indianapolis]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Timezone: America/Indianapolis (does not resolve here",
                      (self.founding_folder() / "answers.md").read_text())


class TestOfficeFound(DoorCase):
    def setUp(self):
        super().setUp()
        self.e.run("init", str(self.root), "--no-projects", "--no-founding", check=0)

    def test_an_office_built_with_no_founding_names_found_and_found_sends_it(self):
        self.assertEqual(self.walk_in(), "Next: office found  (the profile is incomplete, so this office is "
                                         "unfounded, and no founding folder is on the desk; found asks the profile's "
                                         "questions and sends the founding session out)")
        proc = self.e.run("found", "--purpose", "Found later.", cwd=self.root, check=0)
        folder = self.founding_folder()
        self.assertEqual(h.parse_folder((folder / "folder.md").read_text())["fields"]["source"], ["office found"])
        self.assertIn("Answered", (folder / "answers.md").read_text())
        self.assertIn("through office found.", (folder / "answers.md").read_text())
        sid = self.sid_from(proc.stdout)
        # Out: found and start refuse to send it twice, and name the landing.
        proc = self.e.run("found", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"the founding session {sid} is out for desk/{folder.name}; office land {sid} brings it back",
                      proc.stderr)
        proc = self.e.run("start", folder.name, cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"office land {sid}", proc.stderr)
        self.assertEqual(len(self.packs()), 1)

    def test_the_founding_session_lands_and_the_office_is_founded(self):
        proc = self.e.run("found", "--purpose", "p", cwd=self.root, check=0)
        sid = self.sid_from(proc.stdout)
        response_tarball(self.downloads, sid, {"profile.md": filled_profile("home"),
                                               f"notepad/{sid[:10]}-founding.md": "# His words\n"})
        out = self.e.run("land", "--not-now", cwd=self.root, check=0).stdout
        self.assertIn(f"Landed: {sid} is applied in this office", out)
        self.assertNotIn("UNFOUNDED", self.e.run(cwd=self.root, check=0).stdout)
        self.assertTrue(self.walk_in().startswith(f"Next: office start {self.founding_folder().name}  (folder 1 is "
                                                  "open and no session is out for it"))
        proc = self.e.run("found", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("this office is founded", proc.stderr)

    def test_found_takes_only_its_own_flags(self):
        for argv, words in ((["--frob", "x"], "office found does not know --frob"),
                            (["--founding", "x"], "office found does not know --founding"),
                            (["word"], "office found takes no word")):
            proc = self.e.run("found", *argv, cwd=self.root)
            self.assertEqual(proc.returncode, 1, argv)
            self.assertIn(words, proc.stderr)
        self.assertEqual(self.packs(), [])


# --- the Next line for an unfounded office, as a pure function --------------------------

def desk_folder(n, name, source=None):
    return {"name": name, "number": n, "fields": {"source": [source]} if source else {}, "rel": f"desk/{name}"}


class TestTheUnfoundedNextLine(unittest.TestCase):
    def groups(self, **kw):
        g = {"flying": [], "open": [], "ready": [], "parked": {}, "candidates": [], "no_status": [],
             "misplaced": [], "unreadable": []}
        g.update(kw)
        return g

    def test_each_state_names_a_command_that_works(self):
        mv = ob.next_move
        ready = desk_folder(2, "2026-10-06-fix")
        self.assertEqual(mv("current", False, [], self.groups(ready=[ready]), [], 0)[0], "office found")
        founding = desk_folder(1, "2026-10-06-founding", "office init")
        cmd, why = mv("current", False, [], self.groups(ready=[founding, ready]), [], 0)
        self.assertEqual(cmd, "office start 2026-10-06-founding")
        self.assertIn("folder 1 is its founding folder", why)
        # Opened by office found, and open (a session went and came back).
        again = desk_folder(3, "2026-10-07-founding", "office found")
        self.assertEqual(mv("current", False, [], self.groups(open=[again]), [], 0)[0],
                         "office start 2026-10-07-founding")
        out = [{"sid": "2026-10-06-home-founding-001", "label": ob.OFFICE_LABEL, "folders": [founding["rel"]],
                "held": False, "created": "x", "door": "founding"}]
        self.assertEqual(mv("current", False, out, self.groups(flying=[founding]), [], 0)[0],
                         "office land 2026-10-06-home-founding-001")
        # Founded, a founding folder is an ordinary folder.
        self.assertEqual(mv("current", True, [], self.groups(open=[founding]), [{"name": "a"}], 0)[0],
                         "office start 2026-10-06-founding")

    def test_behind_with_the_renovation_out_lands_it_first(self):
        reno = {"sid": "2026-10-06-upgrade-0-13-0-001", "label": ob.OFFICE_LABEL,
                "folders": ["desk/2026-10-06-upgrade-0-13-0"], "held": False, "created": "x", "door": "renovation"}
        other = dict(reno, sid="2026-10-06-x-001", door=None, folders=["desk/x"])
        cmd, why = ob.next_move("behind", True, [other, reno], self.groups(), [], 0)
        self.assertEqual(cmd, "office land 2026-10-06-upgrade-0-13-0-001")
        self.assertIn("once it lands, office upgrade checks it and stamps the office", why)
        self.assertEqual(ob.next_move("behind", True, [other], self.groups(), [], 0)[0], "office upgrade")


# --- the renovation door ------------------------------------------------------------------

RENOVATION = ('[landed]\npaths = ["calendar/plan.md"]\n')


class TestUpgradeSendsARenovation(DoorCase):
    def setUp(self):
        super().setUp()
        self.e.init("home", "--no-projects", "--no-founding")
        self.e.found(self.root)

    def install(self, extra=RENOVATION, kind="renovation"):
        return self.e.fake_install(NEXT, [(NEXT, kind, "Add the calendar space.", "Offices gain a calendar.", None,
                                           extra)])

    def stamp(self):
        return tomllib.loads((self.root / "floor-plan/manifest.toml").read_text())["office"]["migrated_to"]

    def test_it_goes_out_through_start_and_lands_and_the_rerun_stamps(self):
        office = self.install()
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office, check=0)
        self.assertIn("it goes out through office start", proc.stderr)
        sid = self.sid_from(proc.stdout)
        slug = "upgrade-" + NEXT.replace(".", "-")
        self.assertTrue(sid.endswith(f"-{slug}-001"), sid)
        self.assertEqual(self.stamp(), VERSION, "no session ever writes the stamp")
        folder = next((self.root / "desk").glob(f"*-{slug}"))
        facts = h.parse_folder((folder / "folder.md").read_text())["fields"]
        self.assertEqual(facts["source"], ["office upgrade"])
        argv = self.packs()[-1]
        # The whole office, as the printed pack line forecast.
        self.assertNotIn("--write", argv)
        self.assertNotIn("--include", argv)
        self.assertIn(f"Renovate this office for office-src {NEXT}: Add the calendar space. Done means these paths "
                      "exist: calendar/plan.md. Leave the version stamp alone", argv[1])
        brief = request_member(self.request(sid), "README.md")
        self.assertIn(f"- version: {NEXT}\n- summary: Offices gain a calendar.\n- goal: Add the calendar space.", brief)
        self.assertIn('```toml\n[landed]\npaths = ["calendar/plan.md"]\n```', brief)
        self.assertIn("- missing path: calendar/plan.md", brief)
        self.assertIn("It forecasts the whole office (the migration declares no narrower forecast).", brief)
        manifest = request_member(self.request(sid), "manifest.json")
        self.assertIn('"resolved_scope": ["."]', manifest)
        # Out: the Next line lands it, and a re-run never sends it twice.
        self.assertEqual(self.walk_in(bin_path=office).split("  (")[0], f"Next: office land {sid}")
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office, check=0)
        self.assertIn(f"the renovation session {sid} is out", proc.stderr)
        self.assertEqual(proc.stdout.strip().split("  (")[0], f"Next: office land {sid}")
        self.assertEqual(len(self.packs()), 1)
        # Every other verb that changes the office still refuses while behind.
        self.assertIn("run: office upgrade", self.e.run("open", "x", cwd=self.root, bin_path=office).stderr)
        # It lands while the office is behind, and the re-run stamps it.
        response_tarball(self.downloads, sid, {"calendar/plan.md": "# Plan\n"})
        proc = self.e.run("land", "--not-now", cwd=self.root, bin_path=office, check=0)
        self.assertIn("behind office-src", proc.stderr)
        self.assertIn("next: office upgrade", proc.stderr)
        self.assertEqual(self.walk_in(bin_path=office).split("  (")[0], "Next: office upgrade")
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office, check=0)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(self.stamp(), NEXT)
        self.assertIn(f"- {NEXT}: Offices gain a calendar. (renovation, checked)",
                      self.e.git(self.root, "log", "-1", "--format=%B"))
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_a_migration_that_declares_writes_forecasts_them(self):
        (self.root / "calendar").mkdir()
        (self.root / "calendar" / ".keep").write_text("")
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", "a calendar directory")
        office = self.install(RENOVATION.replace("[landed]", 'writes = ["calendar", "profile.md"]\n\n[landed]'))
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office, check=0)
        argv = self.packs()[-1]
        folder = "desk/" + next((self.root / "desk").glob("*-upgrade-*")).name
        self.assertEqual([argv[i + 1] for i, a in enumerate(argv) if a == "--write"],
                         [folder, "notepad", "calendar", "profile.md"])
        brief = request_member(self.request(self.sid_from(proc.stdout)), "README.md")
        self.assertIn("It forecasts calendar, profile.md (the migration declares it)", brief)

    def test_scripts_before_it_land_as_one_commit_first(self):
        from test_office import AFTER, MIGRATION_ADD_SPACE
        office = self.e.fake_install(AFTER, [
            (NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE),
            (AFTER, "renovation", "Write the new Budget section of the profile.", "Profiles gain a Budget section.",
             None, '[landed]\nprofile_sections = ["Budget"]\n'),
        ])
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office, check=0)
        self.assertEqual(self.stamp(), NEXT)
        self.assertIn(f"- {NEXT}: Adds a handbook.", self.e.git(self.root, "log", "--format=%B"))
        self.assertIn("the profile has these sections written: Budget", self.packs()[-1][1])
        self.assertIn("run office upgrade again", proc.stderr)

    def test_a_writes_list_that_names_no_path_in_the_office_refuses(self):
        for bad in ('writes = []\n', 'writes = ["."]\n', 'writes = ["../x"]\n'):
            office = self.install(bad + RENOVATION)
            proc = self.e.run("status", cwd=self.root, bin_path=office)
            self.assertEqual(proc.returncode, 1, bad)
            self.assertIn("writes", proc.stderr, bad)

    def test_no_bale_no_renovation_and_nothing_opened(self):
        from test_read_side import path_without_bale
        office = self.install()
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office, extra={"PATH": path_without_bale(self.e.tmp)})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("bale is not on PATH, so the renovation session cannot go out", proc.stderr)
        self.assertEqual(list((self.root / "desk").glob("*-upgrade-*")), [])


if __name__ == "__main__":
    unittest.main()
