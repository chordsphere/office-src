"""Tests for office-src 0.47.0: deliver fixes, three things met delivering
and merging, and one proposal of 0.46.0's. One class per item:

1. The merge's materials carry the audience's side whole: audience/ holds
   the audience's copy of every file it changed since the sides parted,
   the conflicting ones among them, and the job's page lists every other
   one as a `- changed:` line (` (added)`, ` (deleted)`) under the
   conflicting files' `- file:` lines, read back apart by
   office_deliver.read_merge_job; parted/ and workbench/ stay the
   conflicting files'. The merge commit office land makes is unchanged:
   git's merge carries the files the audience changed cleanly.
2. The merge brief says to ship every file whose resolution differs from
   the workbench's (bale admits no file shipped unchanged), and what
   audience/ holds now; the doctrine and the README say it too.
3. A Review with a title and no body refuses the delivery before anything
   is made, naming the page and the title's line; `office letterhead
   check --delivery` and land's review say the same; a filled template's
   `## ` headings in the body still deliver whole (0.35.0). The cause the
   office can see in its own tree: a build session that keeps a
   template's `## ` heading at its own level in notes.md ends the
   Delivery section there, and the page office land files has a title
   and no body.
4. office deliver's question offers the projects with an audience alone,
   each with its audience named, and with none says so and names `office
   projects set NAME --audience REMOTE`.

The worlds are the suite's own: tests/test_deliver_merges.py's MergeCase
(a bare repo for the audience, a workbench clone with one session landed
the way bale lands one), tests/test_audience_line.py's AudienceCase and
tests/test_land.py's LandCase. Every project, file and reviewer here is
invented. The terminal class runs in the serial lane. Run with the rest of
the suite:

    tests/run.sh test_deliver_fixes
"""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_audience_line import AudienceCase, WORDS, SID, git  # noqa: E402
from test_deliver_merges import MergeCase, SID_M, DAY  # noqa: E402
from test_land import LandCase  # noqa: E402
from test_start import on_a_terminal, git_repo  # noqa: E402

import office_deliver as odl  # noqa: E402
import office_helper as oh  # noqa: E402


def flat(text):
    """Text with its wrapping undone, for a sentence a test pins."""
    return " ".join(text.replace("\r\n", "\n").split())


# --- 1. the audience's side whole ----------------------------------------------------------------

class TestTheMaterialsCarryTheAudiencesSideWhole(MergeCase):
    """MergeCase's audience changes src/a.py (the line the landed session
    changed, so it conflicts) and README.md (a file the workbench never
    touched, so it merges cleanly)."""

    def test_a_clean_change_beside_the_conflict_is_copied_listed_and_carried_by_the_merge(self):
        tip = self.conflict_on_the_audience()
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("copy of every other file it changed since they parted, 1 listed on merge.md",
                      flat(proc.stderr))
        m = self.merge_dir()
        # The audience's side whole: its copy of the clean file beside the
        # conflicting one's; parted/ and workbench/ are the conflict's alone.
        self.assertEqual((m / "audience" / "README.md").read_text(), "hello, readers\n")
        self.assertEqual((m / "audience" / "src" / "a.py").read_text(), "x = 5\n")
        self.assertFalse((m / "parted" / "README.md").exists())
        self.assertFalse((m / "workbench" / "README.md").exists())
        self.assertFalse((m / odl.MATERIALS_CHANGED).exists(), "the list is read into the page, never kept")
        # The page: the two lists apart, read back apart.
        page = (m / "merge.md").read_text()
        self.assertIn("- file: src/a.py\n- changed: README.md\n", page)
        job = self.job()
        self.assertEqual((job["files"], job["changed"]), (["src/a.py"], [("README.md", "changed")]))
        self.office_clean()
        # The merge commit is as before: the session ships the conflicting
        # file, and git's merge carries the clean one.
        self.land_the_merge_session({"src/a.py": "x = 5\ny = 3\n"})
        was, lines = self.land_merge()
        self.assertTrue(was, lines)
        self.assertEqual(self.clone_ref("HEAD^2"), tip)
        self.assertEqual((self.clone / "README.md").read_text(), "hello, readers\n")
        self.assertEqual((self.clone / "src" / "a.py").read_text(), "x = 5\ny = 3\n")
        self.assertFalse(self.merge_dir().exists())

    def test_added_and_deleted_files_and_names_with_spaces(self):
        self.coworker({"src/a.py": "x = 5\n", "docs/a guide.md": "read me\n"}, "Change a, add a guide")
        cow = self.e.tmp / "cow"
        git(cow, "rm", "-q", "README.md", env=self.e.env)
        git(cow, "commit", "-qm", "Drop the readme", env=self.e.env)
        git(cow, "push", "-q", "origin", "main", env=self.e.env)
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        m = self.merge_dir()
        self.assertEqual((m / "audience" / "docs" / "a guide.md").read_text(), "read me\n")
        self.assertFalse((m / "audience" / "README.md").exists(), "a deleted file is a line, not a file")
        self.assertEqual(sorted(self.job()["changed"]), [("README.md", "deleted"), ("docs/a guide.md", "added")])
        page = (m / "merge.md").read_text()
        self.assertIn("- changed: README.md (deleted)\n", page)
        self.assertIn("- changed: docs/a guide.md (added)\n", page)
        log = (m / "log.txt").read_text()
        self.assertIn("Drop the readme", log)
        self.assertIn("Change a, add a guide", log)

    def test_the_page_reads_every_path_back_and_a_page_from_before_reads_no_changed(self):
        job = {"project": "proj", "audience": "origin", "kind": "base", "branch": "main", "tip": "a" * 40,
               "workbench": "b" * 40, "parted": "c" * 40, "day": DAY, "files": ["src/a.py"], "session": None,
               "changed": [("notes (added)", "changed"), ("x (deleted)", "added"), ("plain.md", "changed"),
                           ("gone.md", "deleted")]}
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "merge").mkdir()
            page = odl.merge_page_path(d)
            page.write_text(odl.merge_page_text(job))
            text = page.read_text()
            self.assertIn("- changed: notes (added) (changed)\n", text)
            self.assertIn("- changed: plain.md\n", text)
            self.assertEqual(odl.read_merge_job(d)["changed"], job["changed"])
            # A page written before 0.47.0 has no changed lines, and reads.
            page.write_text("\n".join(l for l in text.splitlines() if not l.startswith("- changed:")) + "\n")
            self.assertEqual(odl.read_merge_job(d)["changed"], [])

    def test_the_changed_list_reads_gits_name_status_and_refuses_what_it_does_not_know(self):
        self.assertEqual(odl.read_changed_list(b"M\0a b.py\0A\0new\0D\0old\0T\0link\0"),
                         [("a b.py", "changed"), ("new", "added"), ("old", "deleted"), ("link", "changed")])
        self.assertEqual(odl.read_changed_list(b""), [])
        with self.assertRaises(odl.DeliverError) as cm:
            odl.read_changed_list(b"R100\0a\0")
        self.assertIn("a status the office does not read", cm.exception.lines[0])


class TestTheAudiencesSideComesThroughAHostsShell(MergeCase):
    hosted = True

    def test_the_copies_and_the_list_arrive_through_the_shell(self):
        self.conflict_on_the_audience()
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertEqual((self.merge_dir() / "audience" / "README.md").read_text(), "hello, readers\n")
        self.assertEqual(self.job()["changed"], [("README.md", "changed")])


# --- 2. the merge brief's sentence -----------------------------------------------------------------

SHIP = ("ship every file whose resolution differs from the workbench's; a file you leave out keeps the "
        "workbench's version, and that is right when the workbench's version is the resolution (bale admits no "
        "file shipped unchanged)")


class TestTheMergeBriefSaysWhatToShip(MergeCase):
    def test_the_brief_the_session_gets(self):
        self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        with self.e.this_process():
            out = self.e.tmp / "brief.md"
            odl.merge_start(self.root, self.name, out)
        text = flat(out.read_text())
        self.assertIn(SHIP, text)
        self.assertIn("The response ships each conflicting file whose resolution differs from the workbench's, as "
                      "it should read after the merge, and nothing else", text)
        self.assertNotIn("ship every file in the list", text)
        self.assertNotIn("the audience's change to it is lost", text)
        # What audience/ holds now, and the other files named.
        self.assertIn("- audience/: origin/main's copy of every file it changed since the two sides parted", text)
        self.assertIn("which did not conflict and which git's merge carries as they are: - README.md ##", text)
        self.assertNotIn("{{", text)

    def test_the_template_the_doctrine_and_the_readme(self):
        template = flat((REPO / "templates" / "merge-brief.md").read_text())
        self.assertIn(SHIP, template)
        self.assertEqual(template.count("ship every file whose resolution differs from the workbench's"), 1)
        doctrine = flat((REPO / "doctrine" / "OFFICE.md").read_text())
        self.assertIn("ships every conflicting file whose resolution differs from the workbench's, as it should "
                      "read after the merge, and nothing else, since a file it leaves out keeps the workbench's "
                      "version and bale admits no file shipped unchanged (0.47.0)", doctrine)
        self.assertNotIn("ships each conflicting file as it should read after the merge and nothing", doctrine)
        readme = flat((REPO / "README.md").read_text())
        self.assertIn("ships every conflicting file whose resolution differs from the workbench's", readme)
        self.assertNotIn("ships each conflicting file as it should read after the merge", readme)


# --- 3. a Review with a title and no body ------------------------------------------------------------

NO_BODY = ("the Review has a title and no body; the body is what the review's readers see, so write it under the "
           "title (a blank line between)")
TITLE_ONLY = WORDS.split("## Review", 1)[0] + "## Review\n\nHealth route for the API\n"
TEMPLATE_BODY = WORDS.replace("One route and its test.", "## Summary\n\nOne route and its test.\n\n## Testing\n\n"
                              "Open /health.")


def title_line(page):
    return next(n for n, l in enumerate(page.splitlines(), 1) if l == "Health route for the API")


class TestAReviewWithNoBodyAsAUnit(unittest.TestCase):
    def test_the_refusal_knows_its_line(self):
        with self.assertRaises(oh.PageLineError) as cm:
            oh.parse_delivery(TITLE_ONLY)
        self.assertEqual(cm.exception.line, title_line(TITLE_ONLY))
        self.assertEqual(oh.page_line_words("desk/x/delivery.md", cm.exception),
                         f"desk/x/delivery.md:{title_line(TITLE_ONLY)}: {NO_BODY}")
        # Blank lines after the title are no body either.
        with self.assertRaises(oh.PageLineError):
            oh.parse_delivery(TITLE_ONLY + "\n\n   \n")
        # A page wrong in its Commit sections says that first, as before.
        with self.assertRaises(oh.HelperError) as cm:
            oh.parse_delivery("# D\n\n## Review\n\nTitle\n")
        self.assertNotIsInstance(cm.exception, oh.PageLineError)
        self.assertIn("no Commit section", str(cm.exception))

    def test_a_templates_headings_in_the_body_are_the_body(self):
        review = oh.parse_delivery(TEMPLATE_BODY)["review"]
        self.assertEqual(review["title"], "Health route for the API")
        self.assertTrue(review["body"].startswith("## Summary\n\nOne route and its test.\n\n## Testing\n\nOpen /health."),
                        review["body"])

    def test_a_templates_heading_kept_at_its_level_in_the_notes_ends_the_delivery_there(self):
        """The cause the office's own tree shows (lib/office_helper.py
        section_bounds, pages_from_notes): in notes.md the Delivery section
        is a `## ` section, so a template's `## Summary` kept at its own
        level ends it, and the page office land files is a title with no
        body, which deliver now refuses by its line. One level down, as
        templates/delivery.md says, it is the body."""
        notes = ("# Notes\n\n## Delivery\n\n- to: Pat Reviewer\n\n### Commit\n\nAdd the health route\n\nIts code.\n\n"
                 "### Review\n\nHealth route for the API\n\n{h} Summary\n\nOne route and its test.\n\n## Handbook\n\n"
                 "- a fact\n")
        cut = oh.pages_from_notes(notes.format(h="##"))["delivery"]
        self.assertEqual(cut[-1], "Health route for the API")
        with tempfile.TemporaryDirectory() as d:
            [(_, _, page)] = [x for x in oh.file_pages(d, {"walkthrough": None, "delivery": cut}, SID, "health route")
                              if x[0] == "delivery"]
            with self.assertRaises(oh.PageLineError) as cm:
                oh.parse_delivery(page.read_text())
            self.assertEqual(cm.exception.line, title_line(page.read_text()))
        whole = oh.pages_from_notes(notes.format(h="###"))["delivery"]
        body = oh.parse_delivery("\n".join(whole) + "\n")["review"]["body"]
        self.assertEqual(body, "## Summary\n\nOne route and its test.")
        self.assertNotIn("a fact", body)
        template = flat((REPO / "templates" / "delivery.md").read_text())
        self.assertIn("In notes.md the template's own headings go one level down too (its `## Summary` written "
                      "`### Summary`)", template)


class TestAReviewWithNoBodyRefusesTheDelivery(AudienceCase):
    def test_deliver_refuses_naming_the_page_and_line_and_nothing_leaves(self):
        before = self.audience_refs()
        self.write_words(TITLE_ONLY)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"{self.folder}/delivery.md:{title_line(TITLE_ONLY)}: {NO_BODY}", flat(proc.stderr))
        self.assertNotIn("commit 1:", proc.stdout)
        self.assertEqual(self.audience_refs(), before)
        self.assertNotIn("delivered:", self.folder_md())
        # office letterhead check --delivery says the same, as a hit.
        page = self.root / self.folder / "delivery.md"
        check = self.run_office("letterhead", "check", "--delivery", str(page))
        self.assertEqual(check.returncode, 1, check.stdout + check.stderr)
        self.assertEqual(check.stdout.splitlines(), [f"{page}:{title_line(TITLE_ONLY)}: {NO_BODY}"])
        self.assertIn("so the letterhead did not read their words", flat(check.stderr))
        # And land's review, which reads the page right after it is filed.
        with self.e.this_process():
            lines = odl.land_review(self.root, "proj", SID, self.folder)
        self.assertIn(f"delivery: office deliver refuses the words as filed: {self.folder}/delivery.md:"
                      f"{title_line(TITLE_ONLY)}: {NO_BODY}", lines)

    def test_a_filled_templates_headings_deliver_whole_and_are_shown(self):
        self.write_words(TEMPLATE_BODY)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("    review: Health route for the API\n      ## Summary\n      \n      One route and its test.\n"
                      "      \n      ## Testing\n      \n      Open /health. The pullsheet code is untouched.\n", proc.stdout)
        page = self.root / self.folder / "delivery.md"
        check = self.run_office("letterhead", "check", "--delivery", str(page))
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        with self.e.this_process():
            lines = odl.land_review(self.root, "proj", SID, self.folder)
        self.assertFalse([l for l in lines if l.startswith("delivery: ")], lines)


# --- 4. deliver's question offers the projects with an audience --------------------------------------

class TestDeliversQuestionOffersTheProjectsWithAnAudience(AudienceCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_only_those_with_an_audience_each_named(self):
        quiet = git_repo(self.e.tmp / "quiet")
        self.run_office("projects", "add", "quiet", str(quiet), check=0)
        bare = self.run_office("open", "no lane here", check=0).stdout.strip()
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver", bare.split("/")[1]], self.root,
                                   self.e.env, [(b"work is on, by its key", "1")])
        screen = flat(seen)
        self.assertIn("This office's projects with an audience: [1] proj (audience origin)", screen)
        self.assertNotIn("quiet", screen)
        self.assertNotIn("[2]", screen)
        # The answer is kept as the lane, as 0.46.0 keeps it; the plan then
        # refuses for its own reason (no session landed for that folder).
        self.assertIn("- lane: proj\n", (self.root / bare / "folder.md").read_text())
        self.assertEqual(code, 1, seen)


class TestDeliversQuestionWithNoAudienceAnywhere(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_it_says_so_and_names_the_line(self):
        bare = self.e.run("open", "no lane here", cwd=self.root, check=0).stdout.strip()
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver", bare.split("/")[1]], self.root,
                                   self.e.env, [])
        self.assertEqual(code, 1, seen)
        screen = flat(seen)
        self.assertIn(f"none of this office's projects has an audience, so {bare}'s work has nowhere to be "
                      "delivered: office projects set NAME --audience REMOTE gives project NAME one", screen)
        self.assertNotIn("work is on, by its key", screen)


if __name__ == "__main__":
    unittest.main()
