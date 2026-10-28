"""Tests for office-src 0.35.0: a delivery.md that office land filed
delivers as it stands.

Before 0.35.0 office land filed delivery.md under a comment naming the
session the page came from ("filed by office land from SID's notes.md"),
a session id is one of bale's marks, and office deliver's letterhead
check read the page whole, so it refused that line and a landed folder
could not deliver without a hand edit (found 2026-10-27).

1. office deliver, and office land's review with it, read the words that
   leave: delivery.md's `to:` line and its Commit and Review sections,
   each hit named at its own line of the page; the heading, land's
   comment, prose above the first section and any other section stay in
   the office, unread and said so (office_helper.delivery_leaving_text,
   office_deliver.delivery_words). A page filed before 0.35.0 delivers
   with its old comment as it is.
2. The comment office land files on delivery.md names no session
   (office_helper.filing_note); walkthrough.md's still names it.

The suite makes no network call: a bare repo on this machine is the
audience, and the fake land bale answers bale's verbs. Run with the rest
of the suite:

    tests/run.sh test_delivery_words
"""

import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_land import LandCase, response_tarball  # noqa: E402
from test_audience_line import AudienceCase, NOTES, SID, WORDS, git  # noqa: E402

import office_deliver as odl  # noqa: E402
import office_helper as oh  # noqa: E402
import office_letterhead as olh  # noqa: E402

RULES = REPO / "share" / "letterhead.toml"
# The comment office land wrote under a filed delivery.md's heading before
# 0.35.0, word for word (lib/office_helper.py file_pages at 0.34.0).
OLD_NOTE = "<!-- filed by office land from {sid}'s notes.md -->"


def filed_before(words=WORDS, sid=SID):
    """delivery.md as office land filed it before 0.35.0: the heading, a
    blank line, the comment naming the session, a blank line, the body."""
    head, body = words.split("\n", 1)
    return "\n".join([head, "", OLD_NOTE.format(sid=sid), "", body.lstrip("\n")])


def install_rules(with_letterhead=True):
    """The install's list, and the letterhead's three characters as an
    office with a letterhead refuses them."""
    rules = olh.load_rules_toml(RULES)
    if with_letterhead:
        d = pathlib.Path(tempfile.mkdtemp(prefix="office-test-letterhead-"))
        rules = olh.apply_letterhead(rules, d)
    return rules


def hits(text, label="delivery.md"):
    return olh.render(olh.hits_in_text(text, olh.compile_rules(install_rules()), label))


# --- 1. the words that leave ---------------------------------------------------------------------

class TestTheWordsThatLeave(unittest.TestCase):
    def test_a_page_filed_before_this_release_has_its_one_mark_outside_the_words(self):
        page = filed_before()
        self.assertEqual(page.splitlines()[2], OLD_NOTE.format(sid=SID))
        # Read whole, as deliver read it before 0.35.0: the comment's
        # session id is refused, at line 3, and nothing else.
        whole = hits(page)
        self.assertEqual(len(whole), 1, whole)
        self.assertTrue(whole[0].startswith("delivery.md:3: marks: "), whole)
        # Read as deliver reads it now: the same length, the heading and
        # the comment blank, every line that leaves where it was.
        text, unread = oh.delivery_leaving_text(page)
        self.assertEqual(unread, 2)
        self.assertEqual(len(text.splitlines()), len(page.splitlines()))
        self.assertTrue(text.endswith("\n"))
        for n, (was, now) in enumerate(zip(page.splitlines(), text.splitlines()), 1):
            self.assertEqual(now, "" if n in (1, 3) else was, n)
        self.assertEqual(hits(text), [])
        # parse_delivery reads the same delivery from either.
        self.assertEqual(oh.parse_delivery(text), oh.parse_delivery(page))

    def test_a_mark_in_the_words_that_leave_is_still_named_at_its_line(self):
        page = filed_before(WORDS.replace("One route and its test.", f"One route, from {SID}."))
        text, _ = oh.delivery_leaving_text(page)
        found = hits(text)
        line = next(n for n, l in enumerate(page.splitlines(), 1) if l.startswith("One route, from"))
        self.assertEqual(len(found), 1, found)
        self.assertTrue(found[0].startswith(f"delivery.md:{line}: marks: "), found)
        # In a Commit body, and on the to: line, alike.
        page = filed_before(WORDS.replace("ok, and the test covers it.", f"ok ({SID}).")
                            .replace("- to: Pat Reviewer", f"- to: Pat {SID}"))
        text, _ = oh.delivery_leaving_text(page)
        self.assertEqual([h.split(": ")[0] for h in hits(text)], ["delivery.md:5", "delivery.md:11"])

    def test_prose_above_the_first_commit_or_review_stays_in_the_office(self):
        page = ("# Delivery: x — y\n\nWritten by hand, with a note: in summary, this.\n\n- to: Pat\n\n"
                "## Notes\n\nIn summary, a note.\n\n"
                "## Commit\n\nSubject\n\nBody.\n\n"
                "## review\n\nTitle\n\n### What to try\n\nBody.\n")
        text, unread = oh.delivery_leaving_text(page)
        self.assertEqual(unread, 4)  # the heading, the prose, `## Notes` and its line
        kept = [l for l in text.splitlines() if l.strip()]
        self.assertEqual(kept, ["- to: Pat", "## Commit", "Subject", "Body.", "## review", "Title",
                                "### What to try", "Body."])
        self.assertEqual(hits(text), [])
        self.assertEqual(len(hits(page)), 3, hits(page))
        # A page without a trailing newline keeps its shape.
        self.assertFalse(oh.delivery_leaving_text("## Commit\n\nS")[0].endswith("\n"))

    def test_a_pull_request_templates_headings_in_the_review_are_its_words(self):
        """A `## ` heading of another name inside the Review (a filled
        pull-request template's) runs on to the next Commit or Review
        heading: parse_delivery sends those lines, and the letterhead reads
        them. Before 0.35.0 the heading cut the Review short, its lines
        never left, and the review's body went out empty."""
        page = WORDS.replace("One route and its test.", "## Summary of changes:\n\nOne route, from " + SID
                             + ".\n\n## Key takeaways:\n\nNone.")
        review = oh.parse_delivery(page)["review"]
        self.assertEqual(review["title"], "Health route for the API")
        self.assertEqual(review["body"], "## Summary of changes:\n\nOne route, from " + SID
                         + ".\n\n## Key takeaways:\n\nNone. The pullsheet code is untouched.")
        text, unread = oh.delivery_leaving_text(page)
        self.assertEqual(unread, 1)  # the heading alone
        line = next(n for n, l in enumerate(page.splitlines(), 1) if l.startswith("One route, from"))
        self.assertEqual([h.split(": ")[0] for h in hits(text)], [f"delivery.md:{line}"])
        # A Review before the Commit ends at it, and each keeps its own words.
        swapped = ("## Review\n\nTitle\n\n## Summary\n\nWhy.\n\n## Commit\n\nSubject\n\nBody.\n")
        words = oh.parse_delivery(swapped)
        self.assertEqual(words["review"]["body"], "## Summary\n\nWhy.")
        self.assertEqual(words["commits"][0], {"subject": "Subject", "body": "Body.", "paths": None})

    def test_the_template_written_as_is_reads_only_its_two_sections(self):
        page = (REPO / "templates" / "delivery.md").read_text()
        text, unread = oh.delivery_leaving_text(page)
        self.assertGreater(unread, 10)
        self.assertNotIn("letterhead check", text)
        self.assertIn("## Commit\n\nThe subject, one line", text)
        self.assertIn("## Review\n\nThe title, one line", text)
        self.assertIn("\n- to: {{to}}\n", text)

    def test_delivery_words_labels_the_page_by_its_path_and_says_what_it_left(self):
        with tempfile.TemporaryDirectory() as d:
            md = pathlib.Path(d) / "delivery.md"
            md.write_text(filed_before())
            (label, text), unread = odl.delivery_words(md)
            self.assertEqual((label, unread), (str(md), 2))
            self.assertEqual(text, oh.delivery_leaving_text(md.read_text())[0])
            (label, _), _ = odl.delivery_words(md, label="desk/7-x/delivery.md")
            self.assertEqual(label, "desk/7-x/delivery.md")
        line = odl.unread_line("desk/7-x/delivery.md", 2)
        self.assertTrue(line.startswith("desk/7-x/delivery.md: the to: line and the Commit and Review sections "
                                        "are read, the words that leave; its 2 other line(s)"), line)


# --- 2. the page office land files ---------------------------------------------------------------

class TestThePageLandFiles(unittest.TestCase):
    def test_delivery_md_names_no_session_and_the_walkthrough_still_does(self):
        sid = "2026-10-27-fix-login-002"
        pages = oh.pages_from_notes(NOTES)
        with tempfile.TemporaryDirectory() as d:
            out = oh.file_pages(d, pages, sid, "fix-login")
            self.assertEqual([(k, s) for k, s, _ in out], [("walkthrough", "filed"), ("delivery", "filed")])
            dl = (pathlib.Path(d) / "delivery.md").read_text()
            wt = (pathlib.Path(d) / "walkthrough.md").read_text()
        self.assertTrue(dl.startswith("# Delivery: fix-login\n\n<!-- filed by office land from the build session's "
                                      "notes.md -->\n\n- to: Pat Reviewer\n"), dl)
        self.assertNotIn(sid, dl)
        # Read whole, as office letterhead check --words reads it by hand,
        # the page holds no line any letterhead refuses.
        self.assertEqual(hits(dl), [])
        self.assertEqual(oh.parse_delivery(dl)["review"]["title"], "Health route for the API")
        self.assertIn(f"<!-- filed by office land from {sid}'s notes.md -->", wt)
        self.assertEqual(oh.filing_note("walkthrough", sid), f"<!-- filed by office land from {sid}'s notes.md -->")
        self.assertNotRegex(oh.filing_note("delivery", sid), r"\d{4}-\d{2}-\d{2}")


# --- 3. office deliver and office land's review, end to end -------------------------------------

class TestDeliverReadsTheWordsThatLeave(AudienceCase):
    def test_a_page_filed_before_this_release_delivers_as_it_stands(self):
        before = self.audience_refs()
        page = filed_before()
        self.write_words(page)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Delivered: health-route is on origin for proj", proc.stdout)
        self.assertIn("letterhead on the diff and the words: clean", proc.stdout)
        self.assertIn(f"{self.folder}/delivery.md: the to: line and the Commit and Review sections are read, the "
                      "words that leave; its 2 other line(s)", proc.stdout)
        self.assertEqual(sorted(set(self.audience_refs()) - set(before)), ["refs/heads/health-route"])
        # The page is as it was: no hand edit, and none by the office.
        self.assertEqual((self.root / self.folder / "delivery.md").read_text(), page)
        # No session id in any word that left.
        pushed = git(self.audience, "log", "--format=%B", "health-route", env=self.e.env)
        self.assertNotIn(SID, pushed)
        self.assertEqual(hits(pushed, "pushed"), [])

    def test_a_session_id_in_the_review_is_refused_at_its_line_with_nothing_pushed(self):
        before = self.audience_refs()
        page = filed_before(WORDS.replace("One route and its test.", f"One route and its test ({SID})."))
        self.write_words(page)
        line = next(n for n, l in enumerate(page.splitlines(), 1) if SID in l and not l.startswith("<!--"))
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"delivery.md:{line}: marks: ", proc.stdout)
        self.assertNotIn("delivery.md:3:", proc.stdout)
        self.assertIn("the letterhead refuses 1 line(s)", proc.stderr)
        self.assertEqual(self.audience_refs(), before)


class TestTheReviewAtLandReadsTheWordsThatLeave(LandCase):
    def give_alpha_an_audience(self):
        audience = self.e.tmp / "alpha-audience.git"
        git(self.e.tmp, "init", "-q", "--bare", str(audience), env=self.e.env)
        git(self.proj, "remote", "add", "origin", str(audience), env=self.e.env)
        self.run_office("projects", "set", "alpha", "--audience", "origin", "--author", "Pat <pat@example.org>",
                        "--base", "main", check=0)

    def test_the_page_land_files_now_reads_clean_at_land(self):
        self.give_alpha_an_audience()
        # A page land files now: its review reads it clean.
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes=NOTES)
        proc = self.run_office("land", sid, "--leave-open", "--response", str(tb), check=0)
        said = proc.stdout + proc.stderr
        self.assertIn("the folder's pages: walkthrough.md filed; delivery.md filed", said)
        self.assertNotIn(sid, (self.root / self.folder / "delivery.md").read_text())
        self.assertIn(f"letterhead: {sid}'s landing is clean for delivery: the change it landed and the delivery "
                      "words, as office deliver reads them", said)

    def test_a_page_filed_before_this_release_reads_clean_at_land(self):
        # A page filed before 0.35.0, left as it is by a landing whose
        # notes carry no Delivery section.
        self.give_alpha_an_audience()
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        page = filed_before(sid=SID)
        (self.root / self.folder / "delivery.md").write_text(page)
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", "a page filed before")
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes="# Notes\n\nOnly notes.\n")
        proc = self.run_office("land", sid, "--leave-open", "--response", str(tb), check=0)
        self.assertIn("carries no walkthrough or delivery section", proc.stderr)
        said = proc.stdout + proc.stderr
        self.assertIn(f"letterhead: {sid}'s landing is clean for delivery: the change it landed and the delivery "
                      "words", said)
        self.assertNotIn("would refuse", said)
        self.assertEqual((self.root / self.folder / "delivery.md").read_text(), page)


if __name__ == "__main__":
    unittest.main()
