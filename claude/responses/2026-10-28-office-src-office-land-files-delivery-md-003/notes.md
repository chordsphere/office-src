# Notes: 2026-10-28-office-src-office-land-files-delivery-md-003

office-src 0.35.0: a delivery.md that `office land` filed now delivers as
it stands, folder 6's included, with no hand edit and no migration. Two
changes, one on each side of the page, plus a third the first one
surfaced (decision 2: a pre-existing bug where a filled pull-request
template cut the Review short), their tests and the record.

## What I decided, for you to ratify

1. **Deliver reads the words that leave, not the page.** This is the fix
   that carries folder 6. The letterhead check at deliver (and land's
   review, which says it reads "as office deliver reads them") now reads
   delivery.md through `office_helper.delivery_leaving_text`: the `to:`
   line above the first section and every line of each Commit and Review
   section are kept at their own line numbers; every other line is
   blanked. So a hit is still named `desk/N/delivery.md:LINE`, exactly as
   before, and the existing test that pins `delivery.md:15: phrasing`
   passes unchanged. What is no longer read: the `# Delivery:` heading,
   land's filing comment, prose above the first section (a hand-written
   page keeps the template's paragraph) and any section parse_delivery
   ignores. None of those reach the audience: commit messages come from
   the Commit sections and the review's title and body from the Review
   section, and that's all parse_delivery hands deliver. Both readers
   share one section splitter (`delivery_sections`), so the words sent
   and the words checked cannot drift apart.
   I chose this over the narrower fix (excuse only the filing comment's
   exact shape) because the filed page's heading carries the folder's
   title, which is the occupant's goal text and can hold a letterhead hit
   of its own (an em dash in a title, say) without anything of it ever
   leaving. "Should pass as it stands" holds for the whole class that
   way. It also means the goal's other half, no session id in any word
   that leaves, is enforced on exactly those words: a sid in a Commit
   body, the Review, or the `to:` line is still refused at its line.
2. **A section now runs to the next Commit or Review heading.** This
   one I didn't go looking for. test_clean_delivery's template test
   failed under (1): a Review filled from a pull-request template with
   `## Summary of changes:` / `## Key takeaways:` headings. parse_delivery
   split on every `## ` line, so those headings started sections of
   their own and were dropped: the review's body stopped at the first
   template heading, and everything under it never left. The old
   whole-page letterhead read those lines anyway, which hid the loss;
   reading only what leaves exposed it. The way design and test both
   intend it (the 0.26.0 template exemption, notes.md's `### Summary`
   promoted to `## Summary` matching the template's own line), those lines
   are the review's words. So a Commit or Review section now ends only
   at the next Commit or Review heading; a `## ` heading of another name
   inside one is its words, sent and checked. A section of another name
   *before* the first Commit or Review is still never read. Visible
   effect: a filled template now actually reaches the review URL's body.
   It changes parse_delivery's behavior for a page that put some other
   `## ` section after its Review expecting it ignored. I found no such
   page in the suite, and the template never suggests one, but it's the
   call I'd most like you to look at. If folder 6's Review was filled
   from m10-api's template and had such headings, its review body was
   being cut short too; this fixes that as a side effect.
3. **Lines not read are said, not skipped.** deliver adds one line under
   "letterhead on the diff and the words: clean": `desk/N/delivery.md:
   the to: line and the Commit and Review sections are read, the words
   that leave; its K other line(s) (...) stay in the office and are not
   read`. Only when K > 0. Land's review already says "as office deliver
   reads them", so it gains no line.
4. **The filed page names no session.** `file_pages` now writes
   `<!-- filed by office land from the build session's notes.md -->` on
   delivery.md (new `filing_note`). walkthrough.md keeps the session id:
   it stays in the office and the existing pin expects it. Belt and
   braces with (1): a page filed from now on reads clean even under a
   hand `office letterhead check --words` on the whole file.
5. **`--words` by hand stays a whole-file read.** The check module is
   generic and imports nothing of the office on purpose, and a flag that
   reads a file differently by its name would be magic. The consequence:
   on a page filed before 0.35.0 (folder 6's), the hand check still
   names the comment's session id while deliver does not. README says
   so beside the example. A proposal below if you want it closed.
6. **0.35.0, additive.** No migration: old pages deliver as they stand,
   and nothing in an office needs rewriting.

## Why no probe

The goal names the refused line and the occurrence (folder 6, the
filing comment, as a bale mark), and the fix doesn't depend on folder 6's
bytes: deliver no longer reads any line of the page outside the to: line
and the two sections, whatever is there. What I could not check from
here is whether folder 6's Commit or Review words hold a hit of their
own; if they do, deliver will name it at its line, which is the
letterhead working. The hand test below is the check against the real
page.

## Paths, and the forecast

The request forecasts `.`, so every path is inside it: lib/office_helper.py,
lib/office_deliver.py, templates/delivery.md, doctrine/OFFICE.md,
README.md, RELEASES.md, VERSION, claude/context/front-sheet.md, and the
new tests/test_delivery_words.py. Nothing of the office context
(work-office's folder, the handbook) lands; the tests build their pages
from the suite's own WORDS and NOTES.

## Things you should know

- The template's paragraph (templates/delivery.md) now says what the
  check reads; it rides with every build session, so the next session's
  Delivery section will be written knowing the heading isn't read.
- `delivery_leaving_text` and parse_delivery share `delivery_sections`
  (Commit and Review headings named case-insensitively, each section to
  the next of them), so the two can't disagree about which lines are
  Commit or Review. A test asserts parse_delivery returns the same
  delivery from the blanked text as from the page.
- **Two whole-module failures that aren't this session's**, both failing
  identically on the unchanged tree:
  test_office's `TestTheDoctrinesCore.test_the_core_holds_the_build_read_in_reading_order`
  (the doctrine's core is 301 lines against the pin's 300; both my
  doctrine edits are past the banner) and test_answer_review's
  `TestTheRecord.test_the_doctrine_the_readme_and_the_release_say_it`
  (RELEASES.md on the base has no `## 0.33.0` entry at all: 0.34.0 is
  followed directly by 0.32.0). Neither is in the fast tier. I left both
  modules out of validation.sh's `--slow` list rather than claim a
  failure the change didn't cause; test_office's text rules still run in
  the fast tier. Both proposed below.
- A `paths:` line inside a Commit section is still read. It doesn't
  leave, but it's inside the section and harmless; I didn't carve it out.

## Validation, as it ran here

The request carries the suite, its fakes and fixtures, so I ran it in
this sandbox (python 3.13, git 2.43), on the change and on the unchanged
tree.

- The new module, 11 tests, passes on the change; on the unchanged tree
  all 11 fail (5 on the missing names, 6 on behavior: the old page
  refused at line 3, the filed page naming its session, land's review
  saying it would refuse, the template's lines cut from the Review).
- The touched modules whole (test_delivery_words, test_audience_line,
  test_clean_delivery, test_suite_clock, test_land, test_three_gaps,
  test_walkthrough_tidy, plus test_office and test_answer_review): every
  test passed but the two pre-existing failures above.
- validation.sh, run in a rehearsed staging copy (the request's tree,
  `files/` over it, apply.sh, the manifest as `.bale-manifest.json`):
  every check passed, both claims agree; the fast tier took 63.4 s of
  its 120 s (365 tests). With `--slow`, the seven modules whole passed
  too (3 min 19 s). One earlier rehearsal ran 137.9 s and failed the
  budget, but only because a whole-suite run was competing for the
  machine beside it.
- On the unchanged tree the script's three session checks fail, as they
  should (the filed page names its session; 0.34.0 in VERSION; the new
  module missing).

## Proposals

- **What:** restore RELEASES.md's 0.33.0 entry. **Why:** it is missing
  on the tree this session started from, so test_answer_review's record
  pin errors on any whole run, and the release history skips a version.
  The 0.33.0 session's notes (claude/responses/2026-10-28-m10-sitting-fixes-001/notes.md)
  are where its words would come from; I didn't reconstruct them, since
  that release's words are the occupant's to ratify. **Scope hints:**
  RELEASES.md between 0.34.0 and 0.32.0; probably lost in 0.34.0's
  landing.
- **What:** bring the doctrine's core back under its 300-line pin, or
  move the pin. **Why:** test_office's TestTheDoctrinesCore fails on the
  base tree (301), so a whole run of test_office is red regardless of
  the change under review. **Scope hints:** doctrine/OFFICE.md above the
  PAST THE CORE banner (0.34.0's additions are the likely place); the
  pin in tests/test_office.py.

- **What:** `office letterhead check --delivery FILE`: read a delivery.md
  as deliver reads it (office_deliver.delivery_words), so a hand check of
  a folder's words agrees with deliver on a page filed before 0.35.0.
  **Why:** today the README's own example (`--words desk/N/delivery.md`)
  names the old filing comment's session id on folder 6's page, which
  deliver no longer refuses; two answers to one question is the kind of
  thing that sends you to a hand edit anyway. **Scope hints:**
  lib/office_deliver.py `check_in_project` already takes words_text, so
  it is the flag's parse and one call; bin/office's usage text.
- **What:** a delivery branch named from a folder slug that ends in
  three digits (`2026-10-27-fix-issue-123`) matches the session-id mark.
  **Why:** I read the marks list for this goal and noticed the branch
  name is the folder's slug, which leaves; deliver doesn't check the
  branch name today, so such a branch would push a word the letterhead
  would refuse anywhere else. Not this goal's, and maybe never hit.
  **Scope hints:** lib/office_deliver.py plan's branch default; the
  marks pattern in share/letterhead.toml.

## Walkthrough

### What changed

- **`office deliver` reads the words that leave** (lib/office_helper.py
  `delivery_leaving_text`, `LEAVING_SECTIONS`; lib/office_deliver.py
  `delivery_words`, `unread_line`, `plan`'s step 8, `land_review`).
- **A section runs to the next Commit or Review heading**, so a filled
  pull-request template's `## ` headings stay in the Review
  (lib/office_helper.py `delivery_sections`, shared by `parse_delivery`).
- **The page `office land` files names no session** (lib/office_helper.py
  `filing_note`, `file_pages`).
- templates/delivery.md says which lines the check reads; doctrine/OFFICE.md
  (land's filing, deliver's check), README.md (deliver's words, the hand
  check's difference, the filed pages, the module table), RELEASES.md
  0.35.0, VERSION, the front sheet's Recent changes line.
- tests/test_delivery_words.py (new, 11 tests in four classes).

### Why

On 2026-10-27 folder 6 of the work office could not deliver: the page
office land filed carried a comment naming the build session, a session
id is one of bale's marks, and deliver's letterhead read the whole page,
so it refused a line that was never going to leave. The only way through
was a hand edit of the folder's paper.

### How to explain each piece

- The read: "deliver checks what goes out: the commit messages and the
  review, plus the to: line. The page's title and the office's own note
  under it stay home, so they aren't held to the letterhead."
- The note: "office land still marks the page as filed by it, but no
  longer writes which session; the folder's Sessions list says that."
- The sections: "if your repo's pull-request template has headings, the
  ones you fill into the Review now go out with it; before, the review
  stopped at the first one."

### Questions a reviewer will ask

- *Could something now leave unchecked?* Only lines parse_delivery
  ignores, and those never become a commit or the review. The commits
  are also read again after they're made (`read_commits`), as before.
- *Why not drop the filing comment entirely?* It's useful paper: it
  tells the occupant the page was filed, not written by hand, and that a
  later landing will rewrite it.
- *Does folder 6 need anything?* No. Its page delivers as it stands; the
  old comment simply isn't read.
- *Could the section change send something that used to stay home?* Only
  a `## ` section of another name placed after a Commit or Review; it now
  joins that section. Before the first Commit or Review, nothing changes.

### A hand test

1. Install 0.35.0 (`office upgrade` in the work office brings nothing to
   do; the install is what changed).
2. In the work office: `office deliver 6`. It shows the delivery with
   "letterhead on the diff and the words: clean" and, under it, the line
   saying delivery.md's 2 other line(s) are not read. Answer as you
   would; nothing about the page was edited.
3. `office letterhead check --words desk/6-.../delivery.md` still names
   line 3 (the old comment): that's the hand check reading the file
   whole, as README now says.
4. On the next landing of any build session into a folder, open its
   delivery.md: the comment reads "filed by office land from the build
   session's notes.md", and the hand check of step 3 is clean on it.

## Delivery

- to: nobody

### Commit

Deliver reads the words that leave; a filed delivery.md delivers as is

office deliver's letterhead check, and office land's review with it, now
reads what of delivery.md leaves: its to: line and its Commit and Review
sections, each hit named at its own line of the page. The page's
heading, the comment office land files under it and anything else above
the first section stay in the office, unread, and deliver says how many such lines it
left. A page filed before this release, whose comment names the session
it came from, delivers with no edit.

A delivery.md section runs to the next Commit or Review heading, so a
pull-request template's own headings filled into the Review stay in the
review's body; before, the first such heading ended it.

office land's comment on delivery.md no longer names the session; the
walkthrough's still does.

Release 0.35.0, additive.

### Review

Deliver reads the words that leave (0.35.0)

What to look at: lib/office_helper.py delivery_sections, which
parse_delivery and delivery_leaving_text now share, and
lib/office_deliver.py plan's step 8 and land_review.

What to try by hand: the walkthrough's hand test, on the folder whose
delivery this was found on.

Deliberately untouched: office letterhead check --words still reads a
file whole (proposed: a --delivery flag); the marks list; no migration,
since old pages deliver as they stand.

## Structure

- title: Deliver reads the words that leave; a filed delivery.md delivers as is
- size: small
- goal: office deliver's letterhead check reads what of delivery.md leaves (its to: line, Commit and Review sections, each running to the next of them), so a delivery.md office land filed delivers as it stands, and office land's comment on delivery.md names no session

## Handbook

### office-src

- office deliver's letterhead check and office land's review read a folder's delivery.md through office_helper.delivery_leaving_text (via office_deliver.delivery_words): the to: line above the first section and every line of Commit and Review sections, at their own line numbers; the heading, land's filing comment, prose above the first section and other sections are blanked and counted, and deliver says the count (office_deliver.unread_line).
- office land's filing comment on delivery.md names no session since 0.35.0 (office_helper.filing_note); walkthrough.md's still does. `office letterhead check --words` reads a file whole, so on a page filed before 0.35.0 it still names the old comment's session id where deliver does not.
- delivery.md's sections are read once, by office_helper.delivery_sections, for parse_delivery and the letterhead alike: each Commit or Review section runs to the next Commit or Review heading, so a filled pull-request template's `## ` headings stay in the Review (before 0.35.0 they cut it short and their lines never left).
- tests/test_delivery_words.py holds 0.35.0's tests (11, in four classes).

#### Front sheet

office-src 0.35.0 lets a folder whose delivery.md `office land` filed
deliver as it stands. Land used to file the page under a comment naming
the session it came from, and since a session id is one of bale's marks,
`office deliver`'s letterhead refused it, so a landed folder needed a hand
edit before it could leave. Now deliver, and land's review with it, read
only the words that leave: the page's `to:` line and its Commit and
Review sections, each hit still named at its line of the page; the
heading, land's comment and anything else above the first section stay
in the office, and deliver says how many lines it did not read. A
section runs to the next Commit or Review heading, so a filled
pull-request template's own headings stay in the Review and leave with
it. Land's comment on delivery.md no longer names the session. A hand `office letterhead check --words` still
reads a file whole. Additive: no migration.
