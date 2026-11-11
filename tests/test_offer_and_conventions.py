"""Tests for 0.57.0, offer-and-conventions: a planner's bundle offered and
answered the same by either door, told from the one a session was opened
from by its brief's hash and not by its stem alone; office land filing a
session's settled `#### Conventions` as its project's chapter's
`## Conventions`, after the occupant's answer; office status naming a
project with an audience whose chapter settles none; and bare office
probe reading the folders and the preps in one helper call.

bale is never needed: the fake bale of tests/test_land.py packs, opens
(recording each bundle's stem and its brief's hash, as bale does),
applies and keeps the open sessions. The terminal tests drive a
pseudo-terminal and run in the serial lane. Run with the rest of the suite:

    tests/run.sh test_offer_and_conventions
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_land import LandCase, bundle_file, response_tarball  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_home_screen import home  # noqa: E402
from test_sort import NOTES_TAIL, small_office  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)
import office_home as hs  # noqa: E402
import office_sort as osort  # noqa: E402

STEM = "2026-11-06-plan-sitting"   # one stem, two different bundles: the occupant's case
SLUG = "plan-sitting"
LANDS = "--- LANDS alpha, folder 1 ---"


def argv_for(slug, goal=None, write="src"):
    return [goal or f"Do the {slug} work", "--slug", slug, "--write", write, "--constraint", ob.PROJECT_CONSTRAINT]


def brief_for(words, lands=True):
    return f"# Brief: {words}\n\n{words}\n" + (f"\n{LANDS}\n" if lands else "")


def age(path, seconds):
    """Set a file's times `seconds` into the past, so the newest is known."""
    then = time.time() - seconds
    os.utime(path, (then, then))


def waiting(case):
    """The offer's rows (PATH, STEM, AGE, WORDS), as bare start and the home
    screen read them (office_home.py bundles)."""
    proc = subprocess.run([sys.executable, "-B", str(REPO / "lib" / "office_home.py"), "bundles", str(case.root),
                           "--dir", str(case.downloads)], env=case.e.env, capture_output=True, text=True, timeout=120)
    case.assertEqual(proc.returncode, 0, proc.stderr)
    return [l.split("\t") for l in proc.stdout.splitlines()]


def flat(text):
    return " ".join(text.replace("\r\n", "\n").split())


class OfferCase(LandCase):
    def machine(self):
        """machine.toml: this world's downloads, and a clipboard a file."""
        clip = self.e.tmp / "clipboard.txt"
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'downloads = ["{self.downloads}"]\nclipboard_command = "tee {clip}"\n'
                                          f'paste_command = "cat {clip}"\n')
        return clip

    def open_the_first(self):
        """A session opened from STEM.bale-bundle, the first of the slug's
        bundles, piped, as the fourth sitting was; returns its file."""
        first = bundle_file(self.downloads, STEM, argv_for(SLUG, "The fourth sitting", write="docs"),
                            brief=brief_for("the fourth sitting"))
        age(first, 5 * 86400)
        self.machine()
        self.run_office("start", "fix-login", "--on", "alpha", f"{STEM}.bale-bundle", check=0)
        self.assertEqual(waiting(self), [], "the bundle a session was opened from is not offered")
        return first


# --- the reading, in this process ---------------------------------------------------------------

class TestSameBundle(unittest.TestCase):
    A, B = "a" * 64, "b" * 64

    def test_the_stem_and_the_brief_both_say(self):
        b = {"stem": STEM, "brief_sha256": self.A}
        self.assertTrue(hs.same_bundle(b, STEM, self.A))
        self.assertTrue(hs.same_bundle(b, f"{STEM} (1)", self.A), "a browser's copy is the same bundle")
        self.assertFalse(hs.same_bundle(b, STEM, self.B), "another brief under the stem is another bundle")
        self.assertFalse(hs.same_bundle(b, "2026-11-06-other", self.A))

    def test_a_record_with_no_hash_is_read_by_its_stem_as_before(self):
        self.assertTrue(hs.same_bundle({"stem": STEM, "brief_sha256": self.A}, STEM, None))
        self.assertTrue(hs.same_bundle({"stem": STEM, "brief_sha256": None}, STEM, None))
        # A record that holds a hash, against a file that carries no brief:
        # not the bundle that record was opened from.
        self.assertFalse(hs.same_bundle({"stem": STEM, "brief_sha256": None}, STEM, self.A))


class TestTheBundleFileSaysItsBriefsHash(LandCase):
    def test_it_is_the_one_bundle_json_names(self):
        import hashlib
        b = bundle_file(self.downloads, STEM, argv_for(SLUG), brief="# Brief\n")
        self.assertEqual(ob.bundle_brief_sha256(b), hashlib.sha256(b"# Brief\n").hexdigest())
        self.assertIsNone(ob.bundle_brief_sha256(bundle_file(self.downloads, "2026-11-06-bare", argv_for("bare"))))
        self.assertIsNone(ob.bundle_brief_sha256(self.downloads / "no-such.bale-bundle"))

    def test_the_fake_records_what_bale_records(self):
        """The suite's fake writes the brief's hash on the dossier's bundle
        record, equal to the bundle file's own, as the probe of 2026-11-11
        read bale 0.4.56 doing for both sittings."""
        b = bundle_file(self.downloads, STEM, argv_for(SLUG), brief=brief_for("one"))
        self.downloads_known()
        self.run_office("start", "fix-login", "--on", "alpha", f"{STEM}.bale-bundle", check=0)
        with self.e.this_process():
            rd = ob.Reader()
            sid, = [s for s in rd.known_sids(str(self.proj)) if SLUG in s]
            records = ob.bundle_records(rd, rd.dossier(str(self.proj), sid))
        self.assertEqual(records, [(STEM, ob.bundle_brief_sha256(b))])
        self.assertIsNotNone(records[0][1])


# --- which bundles wait, read as bare start and the home screen read them -----------------------

class TestWhichBundlesWait(OfferCase):
    def test_a_different_bundle_under_an_opened_stem_is_offered(self):
        """The occupant's case as it happened: a session opened from STEM,
        then a different bundle of the same slug saved beside it four days
        later, which his browser named STEM (1). It waits, as its newest
        copy; the bundle the session was opened from still does not."""
        self.open_the_first()
        second = bundle_file(self.downloads, f"{STEM} (1)", argv_for(SLUG, "The fifth sitting"),
                             brief=brief_for("the fifth sitting"))
        rows = waiting(self)
        self.assertEqual([(r[0], r[1]) for r in rows], [(str(second.resolve()), STEM)])
        self.assertEqual(rows[0][3], "The fifth sitting")
        self.assertIn("2 copies, the newest offered", rows[0][2])
        # And the home screen, which reads the same list, offers it by key.
        out, menu = home(self)
        self.assertRegex(out, rf"\[\d\] Start the planner's bundle {re.escape(STEM)} \(saved just now")
        self.assertIn(["office", "start", "--bundle", str(second.resolve())], [m[1:] for m in menu])

    def test_a_different_bundle_saved_over_the_stem_itself_is_offered(self):
        first = self.open_the_first()
        first.unlink()
        bundle_file(self.downloads, STEM, argv_for(SLUG, "The fifth sitting"), brief=brief_for("the fifth sitting"))
        self.assertEqual([r[1] for r in waiting(self)], [STEM])

    def test_a_true_copy_of_an_opened_bundle_is_still_left_out(self):
        first = self.open_the_first()
        copy = self.downloads / f"{STEM} (1).bale-bundle"
        copy.write_bytes(first.read_bytes())
        self.assertEqual(waiting(self), [], "the same brief under NAME (1) is the bundle a session opened")
        first.unlink()
        self.assertEqual(waiting(self), [], "the copy alone is still the opened bundle")

    def test_a_bundle_with_no_brief_is_read_by_its_stem_as_before(self):
        """A record with no brief hash (here a bundle that carries no brief)
        is matched by its stem alone, the cautious reading: a different
        bundle with no brief under that stem stays out, as at 0.56.0."""
        bundle_file(self.downloads, STEM, argv_for(SLUG, "No brief"))
        self.downloads_known()
        self.run_office("start", "fix-login", "--on", "alpha", f"{STEM}.bale-bundle", check=0)
        bundle_file(self.downloads, f"{STEM} (1)", argv_for(SLUG, "Still no brief"))
        self.assertEqual(waiting(self), [])

    def test_withdraw_reads_it_the_same_way(self):
        """office withdraw --bundle STEM refuses the bundle a session opened
        and takes a different one saved under its stem."""
        self.open_the_first()
        proc = self.run_office("withdraw", "--bundle", STEM, "--yes", check=None)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn(f"{STEM} was opened by ", proc.stderr)
        bundle_file(self.downloads, f"{STEM} (1)", argv_for(SLUG, "The fifth sitting"),
                    brief=brief_for("the fifth sitting"))
        proc = self.run_office("withdraw", "--bundle", STEM, "--yes", check=None)
        self.assertNotIn("was opened by", proc.stderr)


# --- either door, on a terminal ------------------------------------------------------------------

class TestEitherDoorOnATerminal(OfferCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def lands_lines(self, seen, stem):
        """What a start said it took from a bundle's brief, the stem and the
        slug written STEM and SLUG, so two doors' lines can be compared."""
        lines = [l.strip() for l in seen.replace("\r\n", "\n").splitlines()
                 if "LANDS line" in l or l.strip().startswith("[office] from the bundle")]
        return [l.replace(stem, "STEM") for l in lines]

    def test_a_key_picked_from_several_reads_its_lands_line(self):
        """Three bundles wait; the one picked by its key carries a LANDS line
        naming a folder on the desk, so neither the folder nor where the
        work lands is asked, as `office start --bundle STEM` asks neither."""
        self.machine()
        for n, stem in enumerate(["2026-11-11-a-docs", "2026-11-11-b-tidy"]):
            age(bundle_file(self.downloads, stem, argv_for(stem[11:], write="docs")), 3600 * (n + 2))
        picked = bundle_file(self.downloads, "2026-11-11-c-fix", argv_for("c-fix"), brief=brief_for("the fix"))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"(--bundle STEM) [return skips]:", "1"),
        ])
        self.assertEqual(code, 0, seen)
        screen = flat(seen)
        self.assertIn("[1] 2026-11-11-c-fix, saved just now: Do the c-fix work", screen)
        self.assertIn("[3] 2026-11-11-b-tidy", screen)
        self.assertIn("(its LANDS line); neither question is asked", screen)
        self.assertNotIn("Which job", seen)
        self.assertNotIn("Where the work lands", seen)
        self.assertRegex(seen, rf"Packed \S+-c-fix-001 for desk/{re.escape(self.name)}\.")
        by_key = self.lands_lines(seen, "2026-11-11-c-fix")
        self.assertTrue(by_key, seen)
        # The same bundle named at the other door, in a world of its own:
        # the same answers from its brief, and no question either.
        twin = bundle_file(self.downloads, "2026-11-11-d-fix", argv_for("d-fix", write="docs"),
                           brief=brief_for("the fix"))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "--bundle", "2026-11-11-d-fix"],
                                   self.root, self.e.env, [])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("Which job", seen)
        self.assertNotIn("Where the work lands", seen)
        self.assertEqual(self.lands_lines(seen, "2026-11-11-d-fix"), by_key)
        del picked, twin

    def test_the_occupants_case_bare_start_offers_the_newer_and_asks_no_folder(self):
        """As it happened on 2026-11-11: the fourth sitting opened from STEM;
        the fifth's bundle, another brief, saved beside it as STEM (1). Bare
        start offers it (another bundle waits too, so it is by key), and the
        key sends it asking nothing, as --bundle STEM did."""
        self.open_the_first()
        second = bundle_file(self.downloads, f"{STEM} (1)", argv_for(SLUG, "The fifth sitting"),
                             brief=brief_for("the fifth sitting"))
        age(bundle_file(self.downloads, "2026-11-10-other", argv_for("other", write="docs")), 86400)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"(--bundle STEM) [return skips]:", "1"),
        ])
        self.assertEqual(code, 0, seen)
        screen = flat(seen)
        self.assertIn(f"[1] {STEM}, saved just now; 2 copies, the newest offered: The fifth sitting", screen)
        self.assertIn(f"starting the planner's bundle {second.name}", screen)
        self.assertIn("(its LANDS line); neither question is asked", screen)
        self.assertNotIn("Which job", seen)
        # A second session of the slug (its count is bale's: a day turned
        # between the two opens starts it again, so it is not pinned).
        self.assertRegex(seen, rf"Packed \S+-{SLUG}-\d{{3}} for desk/{re.escape(self.name)}\.")

    def test_the_other_door_says_the_copies_are_two_bundles(self):
        """office start --bundle STEM takes the newest copy, as at 0.56.0, and
        now says when the copies it left carry another brief."""
        self.open_the_first()
        bundle_file(self.downloads, f"{STEM} (1)", argv_for(SLUG, "The fifth sitting"),
                    brief=brief_for("the fifth sitting"))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "--bundle", STEM], self.root,
                                   self.e.env, [])
        self.assertEqual(code, 0, seen)
        screen = flat(seen)
        self.assertIn(f"took the newest, {self.downloads.resolve() / (STEM + ' (1).bale-bundle')}", screen)
        self.assertIn(f"not every copy is the same bundle: {STEM}.bale-bundle carries another brief than "
                      "the one taken", screen)
        self.assertNotIn("Which job", seen)


# --- 2. office land files a session's settled conventions -----------------------------------------

SID = "2026-11-11-fix-login-001"
LATER = "2026-11-12-fix-login-002"
ANSWER = "## Questions and answers\n\n- 2026-11-11 Commit style for alpha? Conventional Commits, as CONTRIBUTING says\n"
OLD_CHAPTER = ("# alpha\n\n## Front sheet\n\nalpha is the web app.\n\n## Facts\n\n"
               f"- 2026-10-01: the api answers on port 8080 ({SID[:11]}old-job-001)\n")


def handbook(*parts, facts=("- the login page is static",)):
    """A notes.md Handbook section for alpha: its facts, then each part."""
    return "## Handbook\n\n### alpha\n\n" + "".join(f + "\n" for f in facts) + "\n" + "\n".join(parts)


CONVENTIONS = "#### Conventions\n\n- commits are Conventional Commits\n- one pull request per feature, from main\n"
FRONT = "#### Front sheet\n\nalpha is the web app the team logs in to.\n"


class TestTheNotesParts(unittest.TestCase):
    def test_conventions_before_or_after_the_front_sheet_are_neither_facts_nor_sheet(self):
        for parts in ((FRONT, CONVENTIONS), (CONVENTIONS, FRONT)):
            n = osort.parse_notes(handbook(*parts))
            self.assertEqual(n["handbook"], [("alpha", ["the login page is static"],
                                              ["alpha is the web app the team logs in to."])], parts)
            self.assertEqual(n["conventions"], [("alpha", ["commits are Conventional Commits",
                                                           "one pull request per feature, from main"], 0)])

    def test_a_notes_without_the_part_reads_as_at_0_56_0(self):
        notes = handbook(FRONT + "\n#### Not a part\n\nstill the sheet\n")
        n = osort.parse_notes(notes)
        self.assertEqual(n["handbook"], [("alpha", ["the login page is static"],
                                          ["alpha is the web app the team logs in to.", "", "#### Not a part", "",
                                           "still the sheet"])])
        self.assertEqual(n["conventions"], [])
        self.assertIsNone(osort.parse_notes("## Walkthrough\n\nx\n")["conventions"])

    def test_a_wrapped_convention_is_one_and_prose_is_counted_out(self):
        part = "#### Conventions\n\nWe settled these.\n\n- a convention that\n  wraps\n- another\n"
        (_, items, other), = osort.parse_notes(handbook(part))["conventions"]
        self.assertEqual((items, other), (["a convention that wraps", "another"], 1))


class TestConventionsFiled(unittest.TestCase):
    """file_notes on a small office written by hand: no bale, no command."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.root = small_office(self.tmp / "office")
        self.path = self.root / "handbook/alpha.md"

    def land(self, notes, sid=SID):
        said, changed = osort.file_notes(self.root, notes, sid, "2026-11-11", None, ["alpha"])
        return "\n".join(said), changed

    def section(self):
        text = self.path.read_text()
        return text.split("## Conventions\n", 1)[1].split("\n## ", 1)[0].strip("\n").splitlines()

    def test_a_chapter_made_from_the_template_has_its_place_filled(self):
        said, changed = self.land(ANSWER + "\n" + handbook(CONVENTIONS))
        self.assertIn("handbook/alpha.md", changed)
        self.assertEqual(self.section(), ["- commits are Conventional Commits",
                                          "- one pull request per feature, from main"])
        self.assertNotIn(osort.NONE_SETTLED, self.path.read_text())
        self.assertIn(f"Handbook: handbook/alpha.md: the conventions, replaced whole by {SID}'s (2)", said)
        self.assertNotIn("no longer settled", said, "None settled yet. is no convention")
        text = self.path.read_text()
        self.assertLess(text.index("## Front sheet"), text.index("## Conventions"))
        self.assertLess(text.index("## Conventions"), text.index("## Facts"))
        self.assertIn(f": the login page is static ({SID})", text, "the facts are filed as ever")
        self.assertEqual(osort.chapter_problems(self.path), [])

    def test_a_chapter_made_before_0_56_0_gains_the_section_between_sheet_and_facts(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text(OLD_CHAPTER)
        osort.handbook_arrive(self.root)
        said, _ = self.land(ANSWER + "\n" + handbook(CONVENTIONS, facts=()))
        text = self.path.read_text()
        self.assertEqual(text, "# alpha\n\n## Front sheet\n\nalpha is the web app.\n\n## Conventions\n\n"
                               "- commits are Conventional Commits\n- one pull request per feature, from main\n\n"
                               "## Facts\n\n" + OLD_CHAPTER.split("## Facts\n\n", 1)[1])
        self.assertIn("the section is new in this chapter", said)
        self.assertEqual(osort.chapter_problems(self.path), [])

    def test_replaced_whole_and_each_line_that_left_is_named(self):
        self.land(ANSWER + "\n" + handbook(CONVENTIONS))
        said, _ = self.land(ANSWER + "\n" + handbook("#### Conventions\n\n- commits are Conventional Commits\n"
                                                     "- reviews name the ticket\n"), sid=LATER)
        self.assertEqual(self.section(), ["- commits are Conventional Commits", "- reviews name the ticket"])
        self.assertIn(f"the conventions, replaced whole by {LATER}'s (2)", said)
        self.assertIn(f"handbook/alpha.md: no longer settled, since {LATER}'s set does not carry it: - one pull "
                      "request per feature, from main", said)
        self.assertNotIn("no longer settled, since " + LATER + "'s set does not carry it: - commits", said)

    def test_filed_again_the_same_lines_are_said_and_left(self):
        self.land(ANSWER + "\n" + handbook(CONVENTIONS))
        before = self.path.read_bytes()
        said, changed = self.land(ANSWER + "\n" + handbook(CONVENTIONS, facts=()))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(changed, [])
        self.assertIn(f"the conventions already read as {SID}'s, left as they are", said)

    def test_without_an_answer_it_is_said_and_left_and_the_rest_is_filed(self):
        said, changed = self.land(handbook(CONVENTIONS, FRONT))
        self.assertIn("#### Conventions is not filed: " + SID + "'s notes record no answer of the occupant's", said)
        self.assertEqual(self.section(), [osort.NONE_SETTLED])
        text = self.path.read_text()
        self.assertIn("alpha is the web app the team logs in to.", text)
        self.assertIn(f": the login page is static ({SID})", text)
        # An empty answers section is no answer either.
        said, _ = self.land("## Questions and answers\n\nnone this time\n\n" + handbook(CONVENTIONS, facts=()))
        self.assertIn("is not filed", said)
        self.assertEqual(self.section(), [osort.NONE_SETTLED])

    def test_a_part_with_no_line_never_empties_a_settled_section(self):
        self.land(ANSWER + "\n" + handbook(CONVENTIONS))
        before = self.path.read_bytes()
        said, changed = self.land(ANSWER + "\n" + handbook("#### Conventions\n\nNone this time.\n", facts=()),
                                  sid=LATER)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(changed, [])
        self.assertIn("#### Conventions holds no `- ` line, so nothing of it is filed", said)
        self.assertIn("1 line(s) that are not `- ` lines were left out", said)

    def test_each_on_one_line_and_ascii(self):
        self.land(ANSWER + "\n" + handbook("#### Conventions\n\n- the review's title says café\n"
                                           "- a long one that\n    wraps\n- a long one that wraps\n"))
        self.assertEqual(self.section(), ["- the review's title says caf\\xe9", "- a long one that wraps"])
        self.path.read_text(encoding="ascii")

    def test_status_reads_the_chapter_clean_absent_unsettled_or_settled(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text(OLD_CHAPTER)
        self.assertEqual(osort.chapter_problems(self.path), [])
        self.path.write_text(osort.render_chapter("alpha"))
        self.assertEqual(osort.chapter_problems(self.path), [])
        self.land(ANSWER + "\n" + handbook(CONVENTIONS))
        self.assertEqual(osort.chapter_problems(self.path), [])
        self.assertEqual(osort.settled_conventions(self.path), ["- commits are Conventional Commits",
                                                                "- one pull request per feature, from main"])


class TestLandFilesTheConventions(LandCase):
    def test_a_build_sessions_answer_and_its_conventions_land_in_the_chapter(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        notes = "# Notes\n\n" + ANSWER + "\n" + handbook(FRONT, CONVENTIONS) + NOTES_TAIL
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes=notes)
        proc = self.run_office("land", sid, "--ratified", "--leave-open", "--response", str(tb), check=0)
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertIn(f"Handbook: handbook/alpha.md: the conventions, replaced whole by {sid}'s (2)",
                      " ".join(proc.stderr.split()))
        chapter = (self.root / "handbook/alpha.md").read_text()
        self.assertIn("## Conventions\n\n- commits are Conventional Commits\n- one pull request per feature, from "
                      "main\n\n## Facts", chapter)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        status = self.run_office("status", check=0).stdout
        self.assertIn("handbook:   matches the install's catalog; 1 chapter(s)", status)


# --- 3. office status names a project with an audience and none settled ---------------------------

class TestStatusNamesAProjectWithNoneSettled(LandCase):
    def give_alpha_an_audience(self):
        audience = self.e.tmp / "alpha-audience.git"
        subprocess.run(["git", "init", "-q", "--bare", str(audience)], env=self.e.env, check=True)
        subprocess.run(["git", "-C", str(self.proj), "remote", "add", "origin", str(audience)], env=self.e.env,
                       check=True)
        self.run_office("projects", "set", "alpha", "--audience", "origin", "--author", "Pat <pat@example.org>",
                        "--base", "main", check=0)

    def status(self):
        proc = self.run_office("status", check=None)
        return proc.returncode, proc.stdout, [l for l in proc.stdout.splitlines() if l.startswith("conventions:")]

    def chapter(self, text):
        """The chapter, written by hand in a handbook that has arrived as
        office land brings it."""
        with self.e.this_process():
            osort.handbook_arrive(self.root)
        (self.root / "handbook/alpha.md").write_text(text)
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", "the chapter, by hand")

    def test_no_line_without_an_audience(self):
        code, out, lines = self.status()
        self.assertEqual(lines, [], out)

    def test_one_line_for_each_way_none_is_settled_and_none_once_one_is(self):
        self.give_alpha_an_audience()
        code, out, lines = self.status()
        self.assertEqual(lines, ["conventions: alpha has none settled (handbook/alpha.md is not written yet): a "
                                 "session asks you and office land files your answer, or you write them in "
                                 "handbook/alpha.md under ## Conventions, one `- ` line each"], out)
        before_code, before = code, [l for l in out.splitlines() if not l.startswith("conventions:")]
        self.chapter(OLD_CHAPTER)
        code, out, lines = self.status()
        self.assertEqual(len(lines), 1, out)
        self.assertIn("(handbook/alpha.md has no ## Conventions section)", lines[0])
        self.assertIn("handbook:   matches the install's catalog; 1 chapter(s)", out, "a line, never a problem")
        self.assertEqual(code, before_code)
        self.chapter(osort.render_chapter("alpha"))
        code, out, lines = self.status()
        self.assertEqual(len(lines), 1, out)
        self.assertIn("(handbook/alpha.md reads None settled yet.)", lines[0])
        self.assertIn("handbook:   matches the install's catalog; 1 chapter(s)", out)
        self.assertEqual(code, before_code)
        self.chapter(osort.render_chapter("alpha").replace(osort.NONE_SETTLED, "We will settle them soon."))
        _, out, lines = self.status()
        self.assertIn("(handbook/alpha.md's ## Conventions holds no `- ` line)", lines[0])
        self.chapter(osort.render_chapter("alpha").replace(osort.NONE_SETTLED, "- commits are Conventional Commits"))
        code, out, lines = self.status()
        self.assertEqual(lines, [], out)
        self.assertEqual(code, before_code)
        # Every other line status prints is as it was with none settled.
        self.assertEqual(len([l for l in out.splitlines() if not l.startswith("conventions:")]), len(before))


# --- 4. bare office probe reads the folders and the preps in one helper call ------------------------

class TestBareProbeIsOneHelperCall(LandCase):
    """A python3 on the test's PATH ahead of the real one logs every
    interpreter the command starts (tests/test_land.py TestFewerHelperStarts)."""

    def setUp(self):
        super().setUp()
        self.log = self.e.tmp / "python3-starts.log"
        real = sys.executable
        self.assertTrue(real and not re.search(r"\s", real), real)
        shim = self.e.desktop / "python3"
        shim.write_text("#!/bin/bash\n# The suite's own: logs this start, then runs the real python3.\n"
                        f"printf '%s\\n' \"$*\" >> {str(self.log)!r}\nexec {real} \"$@\"\n")
        shim.chmod(0o755)
        self.sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        from test_probe import probe_block
        self.block = probe_block()

    def test_the_folders_and_the_preps_are_one_read_and_the_lines_are_as_before(self):
        self.log.write_text("")
        proc = self.run_office("probe", "-", "--yes", input=self.block, check=0)
        helpers = [l for l in self.log.read_text().splitlines() if "runpy.run_module" in l]
        reads = [l for l in helpers if "probe-folders" in l or "preps-out" in l]
        self.assertEqual(len(reads), 1, "\n".join(helpers))
        self.assertIn(" batch ", reads[0])
        self.assertIn("bale:probe-folders", reads[0])
        self.assertIn("probe:preps-out", reads[0])
        self.assertIn(f"desk/{self.name} records the one session open, {self.sid} (on alpha), so the probe is its "
                      "(office probe FOLDER names another)", " ".join(proc.stderr.split()))
        self.assertIn("=== PROBE BEGIN fix-login ===", proc.stdout)


# --- the release ----------------------------------------------------------------------------------

class TestTheRelease(unittest.TestCase):
    def test_the_record_names_this_release(self):
        """The release the front sheet names for this session, never
        VERSION's, which moves on with every release."""
        sheet = (REPO / ("cla" + "ude") / "context" / "front-sheet.md").read_text()
        version = re.search(r"^- (\d+\.\d+\.\d+) \(session 2026-11-11-offer-and-conventions-001\)", sheet,
                            re.M).group(1)
        releases = (REPO / "RELEASES.md").read_text()
        entry = releases.split(f"\n## {version}\n", 1)[1].split("\n## ", 1)[0]
        self.assertTrue(entry.lstrip().startswith("Additive: no migration, nothing stored changes, nothing to do in "
                                                  "any\noffice."), entry[:120])
        for words in ("brief_sha256", "#### Conventions", "conventions:", "probe_bare_session"):
            self.assertIn(words, entry)


if __name__ == "__main__":
    unittest.main()
