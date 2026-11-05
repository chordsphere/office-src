# Notes: 2026-11-04-deliver-fixes-003 (office-src 0.47.0)

All four items are built, with one test class each, in tests/test_deliver_fixes.py.
Every changed path is inside the forecast. The occupant's delivery page for
folder 21, and the work repository's pull-request template, did not reach
this session, so item 3's cause is fixed from what the tree shows (decision 8),
not from the page. If the page arrives later, check it against decision 8
before taking the reader change in Proposal 1.

The whole suite ran once before shipping: 1346 tests, all passing, in 737 s of
wall clock on two CPUs (0.46.0: 1332 in 731 s; this release adds 14). validation.sh
was rehearsed twice. On the tree with the response applied, `--slow` passed
everything in 3 min 24 s, and the fast tier with this session's classes took 68 s of
its 120 s budget. On the unmodified tree, the pins and the fast run both fail.

## Decisions

1. **How the audience's changed files are listed.** `git diff -z
   --no-renames --name-status PARTED AUDIENCE`, as the sitting leaned. PARTED
   is the commit the parted/ copies come from: the merge base of the two
   sides, which is also the base git's own merge uses. For the branch kind
   that is not log_from (the last delivery's base, which the log reads from),
   because what land's merge brings in is what changed since the merge base.
   `--no-renames` gives a rename as a deletion plus an addition, so each
   path has one plain status. `-z` keeps every name whole: nothing is quoted
   and nothing is cut at a space or a newline. The list travels in the tar
   stream as `changed.list`. carry_materials reads it into the page and
   deletes it, so the folder never holds it.
2. **The copies.** `xargs -0` hands each name to a small copier
   (`_AUDIENCE_COPY`) that writes `git cat-file blob AUDIENCE:PATH`. A path
   that is not a blob there (deleted, or a submodule) gets no copy, and the
   page lists it all the same. If a copy fails, the materials refuse with
   exit 7 and nothing is written; nothing is skipped without a word. The
   copier holds no single quote, so it rides inside `_MATERIALS_SCRIPT`
   between single quotes. That keeps `shlex` off the module's import path
   (the suite holds every module to lazy heavy imports).
3. **The page's `- changed:` lines carry the status only when it says
   something.** A plain change is `- changed: PATH`; an addition or deletion
   gets ` (added)` or ` (deleted)` after it. A path that itself ends the way
   such words would (`notes (added)`) also gets ` (changed)` written after
   it, so the reader strips exactly one ending and every path reads back.
   read_merge_job returns `job["changed"]` as `[(path, how)]`; a page written
   before 0.47.0 reads with `[]`. A path whose name holds a line break would
   break its page line, so it is logged and left off the list, and its copy
   stays in audience/.
4. **The brief lists the other files too.** Beyond saying what audience/
   holds, the brief gets a `{{changed}}` list under the conflicting files,
   so the session sees the audience's other changes without opening
   merge.md. "Each file above" in the land paragraph became "each
   conflicting file", since the list above it now holds both kinds.
5. **Item 2's words** are the brief's pinned sentence, after "So", in the
   land paragraph. The paragraph above opens with the same rule: "The
   response ships each conflicting file whose resolution differs from the
   workbench's, as it should read after the merge, and nothing else". The
   old warning ("the audience's change to it is lost") is gone, because the
   new sentence says when leaving a file out is right.
6. **The refusal names the title's line**, since the title is what has no
   body under it. It is raised last in parse_delivery, after every Commit
   check, so a page that is wrong in its Commit sections still says that
   first (two existing tests pin that order). The mechanism is
   `office_helper.PageLineError` (a HelperError with `.line`) plus
   `page_line_words(page, exc)`, which deliver's plan, the helper's
   `delivery-words` and the two new readers below all use.
7. **Flagged widening: `office letterhead check --delivery` says every
   refusal deliver would make, not only the empty body.** The pin says the
   check "says the same". Agreeing with deliver on one refusal but not the
   others seemed worse than agreeing on all. A page deliver refuses is a hit:
   one `FILE:LINE: words` line (or `FILE: words` when the refusal has no
   line) on stdout, exit 1, and a stderr line saying the letterhead did not
   read those words. **Flagged addition: land's review says it too**
   (`delivery: office deliver refuses the words as filed: PAGE:LINE: ...`),
   right after land files the page. It refuses nothing. This is where the
   cause in decision 8 shows itself, one step before deliver.
8. **The cause, from the tree, since the page never came.** A build session
   writes the delivery in notes.md as a `## Delivery` section, one heading
   level down (`### Review`). templates/delivery.md also told it to keep a
   filled pull-request template's lines "as the repository holds them". A
   session that does both writes the template's `## Summary` at `##` in
   notes.md. `section_bounds` ends the Delivery section at the first `## `
   heading, so pages_from_notes stops right there. The page land files then
   has a Review with a title and nothing else, and the 0.35.0 reader never
   sees the rest. This matches the occupant's sentence ("the repository's
   template uses `##` headings, the same level as the delivery page's Review
   heading"), but only the page can confirm it. I did not change the reader.
   Running the Delivery section past a `## ` heading cannot tell a
   template's heading from the next notes.md section (`## Handbook`,
   `## Proposals`), and the pin is that nothing reaches the audience that
   did not before. So: templates/delivery.md, which rides with every build
   session, now says to write the template's headings one level down in
   notes.md, and the empty-body refusal catches any that slip through, at
   land and at deliver. The heading at fault would be the template's first
   `## ` heading inside the Review (`## Summary`, say). The test
   `test_a_templates_heading_kept_at_its_level_in_the_notes_ends_the_delivery_there`
   pins the mechanism. Proposal 1 has the reader fix.
9. **deliver_show is unchanged.** It prints the review's title and body as
   before. A Review with no body now refuses before the plan, so the show
   never meets one; a short body is still visible there.
10. **Item 4 with no project that has an audience exits 1 before the plan**
    (`die`), with the line to type. It does not offer an empty list or go
    on. A project with an audience but a declaration problem is still
    offered, and the plan refuses it by name as before. Each key reads
    `NAME (audience REMOTE)`, under "This office's projects with an
    audience:". The list comes from a new flag, `office_helper project-names
    --with-audience` (NAME<TAB>AUDIENCE), so no new helper call is added:
    the question already made one `project-names` call.
11. **Flagged: the doctrine's merge row in the verbs table changed too.**
    The brief named the merge paragraph and deliver's row. The merge row
    said "shipping each conflicting file as it should read after the merge
    and nothing else", which now contradicts the rule, so it says the new
    rule. It is past the banner; the core (lines 1 to 299) and the headings
    are byte for byte as they were, and validation.sh checks both hashes.
12. tests/test_deliver_merges.py's `test_the_brief_says_what_the_session_is`
    pinned the old sentence; it now reads the new one. Its other pins stand.

## Walkthrough

### What changed

- lib/office_deliver.py: `_MATERIALS_SCRIPT` lists every path the audience
  changed since the sides parted and copies the audience's version of each
  into audience/ (`_AUDIENCE_COPY`, `read_changed_list`). carry_materials
  returns that list. merge_job_lines writes it on merge.md as `- changed:`
  lines under the `- file:` lines (`changed_line`, `merge_page_text`).
  read_merge_job reads both lists apart (`job["changed"]`). merge_start
  hands the list to the brief. The land review says a delivery page deliver
  would refuse. `delivery-words` (what `letterhead check --delivery` uses)
  says such a page as a hit.
- lib/office_helper.py: parse_delivery refuses a Review with a title and no
  body, as `PageLineError` with the title's line; `page_line_words` says it
  as `PAGE:LINE: words`. `project-names --with-audience`.
- bin/office: deliver's question offers the projects with an audience
  alone, or says none has one; `letterhead check --delivery` passes a
  refusal through as a hit.
- templates/merge-brief.md: what audience/ holds, the list of the other
  changed files, and the shipping rule. templates/delivery.md: a template's
  headings go one level down in notes.md, and a body-less Review refuses.
- README.md, doctrine/OFFICE.md (past the banner), RELEASES.md, VERSION,
  the front sheet.

### Why

The occupant's three sentences of 2026-11-04 and 0.46.0's third proposal.
A merge session that sees only the conflicting file cannot see what the
audience did beside it. The brief's "ship every file in the list" made a
session ship a file unchanged, which bale refused. A Review cut short went
out with no body. Offering a project with no audience leads to a refusal
one step later.

### How to explain each piece

- The merge folder now shows everything the audience did since the two
  sides parted. The session still resolves only the conflicting files, and
  git's merge carries the rest exactly as before.
- Ship what you changed; a file you leave out stays as the workbench has
  it, and that is fine when the workbench was right.
- A review needs a body. The office now says which line of which page has
  only a title, before anything is made.
- deliver only offers projects it can deliver to.

### Questions a reviewer will ask

- *Does the merge commit change?* No. `_RESOLVED_SCRIPT` still takes only
  the `- file:` paths, and `test_a_clean_change_beside_the_conflict_is_copied_listed_and_carried_by_the_merge`
  shows land's merge carrying the clean file. The whole-loop test passes
  unchanged.
- *Can a big audience change bloat the office?* Yes. Every file the
  audience changed is copied into the folder and committed in the office
  until the merge lands (the copies leave with the job). See Proposal 2.
- *Why not fix the notes.md reader?* Decision 8.
- *Does anything new reach the audience?* No. Item 1 widens what the
  office copies into a folder, item 3 only refuses, and item 4 only narrows
  a question.

### A hand test

1. In a scratch office with a project that has an audience, make the
   audience change a file the workbench also changed, plus one it did not.
   Run `office deliver N --refresh`. Open `desk/N-.../merge/merge.md`: one
   `- file:` line and one `- changed:` line, and `merge/audience/` holds
   both files.
2. Write a delivery.md whose Review is a title alone. `office deliver N`
   refuses with `desk/...delivery.md:LINE: the Review has a title and no
   body; ...`, and LINE is the title's line. `office letterhead check
   --delivery desk/.../delivery.md` says the same line and exits 1.
3. Open a folder with no lane and run `office deliver N` on a terminal:
   only the projects with an audience are listed, each as `NAME (audience
   REMOTE)`.

## Delivery

### Commit

Carry the audience's side whole and refuse an empty review

When bringing the audience into the workbench conflicts, the merge's
materials now hold the audience's copy of every file it changed since the
two sides parted, and merge.md lists the files that did not conflict as
`- changed:` lines under the conflicting ones. The merge brief says to ship
every file whose resolution differs from the workbench's, since a file left
out keeps the workbench's version and bale admits no file shipped
unchanged.

A delivery whose Review has a title and no body is refused before anything
is made, naming the page and the title's line; letterhead check --delivery
and land's review say the same. Deliver's project question offers only the
projects with an audience, each with its audience named.

Release 0.47.0, additive.

### Review

Deliver fixes: the audience's side whole, the brief's shipping rule, an empty review refused

Look at the materials script in lib/office_deliver.py (the changed list and
the copies), parse_delivery's new refusal in lib/office_helper.py, and the
two templates. Try the hand test in the walkthrough: a merge with a clean
change beside the conflict, a title-only Review, and deliver's question on
a folder with no lane. The merge commit land makes, the 0.35.0 reading of a
template's headings inside the Review, and the doctrine's core are
deliberately untouched.

## Structure

- title: Deliver fixes (0.47.0): the audience's side whole, the brief's shipping rule, an empty review refused
- size: small
- goal: Deliver fixes (0.47.0): the merge job's materials carry the audience's copy of every file it changed since the sides parted, the merge brief says to ship every file whose resolution differs from the workbench's, a Review with a title and no body refuses the delivery naming the page and line, and deliver's question offers the projects with an audience alone

## Handbook

- the merge's materials carry the audience's copy of every file it changed since the sides parted (git diff -z --no-renames --name-status from the merge base), read into merge.md as `- changed:` lines and never kept as changed.list (office_deliver._MATERIALS_SCRIPT, read_changed_list)
- read_merge_job returns job["files"] (the conflicting files, the only ones land's merge takes from the session) and job["changed"] ([(path, how)], how added, changed or deleted)
- a delivery.md refusal that knows its line is office_helper.PageLineError, said as PAGE:LINE: words by office_helper.page_line_words
- parse_delivery raises the empty-body refusal last, after every Commit check
- in notes.md the Delivery section ends at the next `## ` heading (section_bounds), so a pull-request template's headings go one level down there
- office_helper project-names --with-audience prints NAME<TAB>AUDIENCE for each project with an audience; office deliver's question offers those alone

## Proposals

1. **What:** Once folder 21's delivery page and the work repository's
   template are in hand, confirm decision 8's cause. If it is the cause,
   let pages_from_notes run the Delivery section past a `## ` heading that
   is a line of the project's own pull-request template (office_letterhead
   reads those at the audience's base), keeping it at its level instead of
   promoting it. **Why:** the template guidance and the refusal stop the
   symptom, but a session that misses the guidance still gets a refusal
   rather than a delivered review. **Scope hints:**
   lib/office_helper.py pages_from_notes and section_bounds; land's
   file_pages would need the project's template lines, read where land_review
   reads them.
2. **What:** Cap or summarize the audience's side when it is large (for
   example, copy at most N files and list the rest on the page). **Why:**
   item 1 copies every file the audience changed into the folder and
   commits them in the office until the merge lands. A long-parted
   workbench behind a busy base could carry thousands of files into the
   office's history. **Scope hints:** `_MATERIALS_SCRIPT`'s copy step,
   merge_page_text; undo-bale reuses this machinery.
3. **What:** Check what bale does when a merge session's every resolution
   is the workbench's, so it ships no change at all. **Why:** the new rule
   allows an empty response, and `_RESOLVED_SCRIPT` needs bale's
   `applied/SID` tag to make the merge commit. Whether bale tags an empty
   landing is not in this request's BALE_HELP.md, and a merge that never
   gets made would stall the folder. **Scope hints:** a probe in a bale
   install; then make_resolved_merge's exit 13 path, or the brief's
   sentence.
