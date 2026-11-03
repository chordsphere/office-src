# Notes: m10-standing (office-src 0.43.0)

All eleven items of the brief shipped, so the seam it named was not
needed: items 1 to 7 and 9, and items 8, 10 and 11 too. Each has a class
(or two, where a terminal is involved) in the new tests/test_standing.py,
34 tests. The release is additive: VERSION 0.43.0, its RELEASES.md entry
first, the front sheet's Recent changes line, and the README and the
doctrine where a verb's behaviour changed. The doctrine changed past its
banner only: the core's 298 lines are byte for byte the 0.42.0 core
(validation.sh holds them to its sha256), and the banner stays at line
299.

The whole suite ran on the finished tree: 1253 tests, all OK, in 645 s
here (three jobs on two CPUs). The unchanged tree's suite was 1219 tests,
all OK, in 624 s. After that run one file changed, tests/test_standing.py
(its SittingCase now builds its world once per process through
kept_setup, which cut validation's fast run by about 20 s, and one
assertion was tightened, since the kept world's directory name holds the
word "standing"); test_standing ran whole again after it, 34 tests, OK.
validation.sh's fast run on a staging copy (the request's tree, this
response's files/ and apply.sh) took 83 s of the tier's 120: the tier and
ten of this session's classes, 388 tests. Its --slow run, the touched
modules whole (eighteen of them, the terminal classes in the serial lane,
790 tests), passed on the same copy; the whole script took 8 m 17 s with
it. On the unchanged tree the
new module does not parse (it is not there), the tier refuses the names it
cannot find, and every session assertion fails, as it should, but two:
the doctrine's core and its banner, which pin bytes this session must not
touch and so hold on both trees.

Every changed path is inside the write forecast (bin/office, lib, share,
templates, tests, README.md, RELEASES.md, VERSION, doctrine/OFFICE.md,
claude/context/front-sheet.md): the two new files are lib/office_standing.py
and tests/test_standing.py. Two existing tests changed beyond item 7's
harnesses, each because its pinned bytes changed by design: the prep's
record line (decision 13) and the probe module's docstring sentence that
said stderr is not masked (decision 21).

Where a cite and the tree disagreed: nothing material. The 0.42.0 line
numbers in "What is there now" matched the names beside them (home_items,
in_flight, end_sitting, run_probe, land_tail, carry_relays,
brief_marker_lines, mark_prep_out, and the three pty helpers) to within a
few lines.

## Decisions

1. **The verb is `office standing FOLDER [FILE | -]`, plumbing**, the
   sitting's own word, as the brief suggested. It lives in a new module,
   lib/office_standing.py, which reads, splits and writes the block and
   says it on the screens; bin/office's `file_standing` is the one filing
   step, shared by the verb and by office probe. share/verbs.toml declares
   it (`writes = lands = ["desk/{folder}/standing.md"]`), and probe's
   writes gain the same page.
2. **The block is checked a little harder than the brief's prose.** M,
   the step line's count, must equal the number of step lines; exactly one
   is `[>]`, and it must be the Nth. The step line's words need not repeat
   the `[>]` step's, since a sitting may say "step 4 of 7" in other words.
   Each line is read and kept with its blanks at either end dropped and
   CRLF made LF: a chat may indent a block, and a WSL clipboard ends lines
   with CR. So "verbatim" on the page means each line's text as printed,
   not its indentation. Flagged, since "kept to the byte" could be read
   more strictly.
3. **Off a terminal with neither FILE nor `-`, office standing refuses**
   and names the two. The brief says "given neither on a terminal, the
   clipboard", so I kept the clipboard to the terminal. office probe and
   office drop read the clipboard (or stdin) piped as well; if the
   occupant wants the same here, it is one line in cmd_standing.
4. **In office probe, the standing is taken out of the text before
   anything else reads it**, so none of its lines runs as part of the
   block or reads as an `office-on` call (a step that names `office-on
   alpha` would otherwise have made the block a spanning one). It is filed
   before the run question, so it is filed even when he answers N, and
   even when the probe block itself is then refused: the brief says
   "first". A standing that does not read is said (`the standing from the
   probe's text was not filed ...`) and the probe goes on. A STANDING
   BEGIN line with no END after it refuses the probe with nothing run,
   since where the probe's own lines end cannot be told.
5. **The home screen's second key shows only once the folder has a
   standing**, as the brief says ("a sitting with no standing filed shows
   as today"). The first standing then comes with a probe (most turns end
   in one) or by `office standing N`. The key's words: `File where folder
   N, TITLE stands now, from the sitting's last standing block on the
   clipboard`, and it runs `office standing N`. If the occupant would
   rather have the key from the first turn, it is one condition in
   office_home.home().
6. **The walk-in carries the step words inside the sitting's one In
   flight line**, after `(office land SID when the sitting is over)` and
   any doctrine words, and before the older-sitting words: `; step 4 of 7: words; waiting on you: words (as
   of DATE TIME)`. One line per session keeps every reader of those lines
   whole. The digest's In flight reads the same lines, so it shows the
   standing too; I took that as a gain, not a change to undo.
7. **office desk shows the standing under a folder's line** (`standing,
   SID's: step ...`) for folders listed by their folder line: open,
   ready, parked and candidates. A folder whose sitting is in flight is
   listed by its In flight line, which already carries the words, so it is
   not said twice. The walk-in's ready block does not show it, to keep the
   walk-in short.
8. **office land leaves standing.md exactly as it was** when it ends the
   sitting (the brief's call). It appends no `ended` line: the page keeps
   one writer, office standing, and the folder's History already says when
   the sitting ended. The screens name whose a page is when it is not the
   sitting the line is about (`(as of ..., filed by SID)`), which covers a
   successor still showing its predecessor's page.
9. **The ENDS line is read only for a bundle's start, and the end runs
   after the opener is on the clipboard**, as the sitting suggested, so a
   refusal of the end never costs the pack. `--end-predecessor` or
   `--keep-predecessor` on a start that is not a bundle is said and
   changes nothing. office_bale `ends_plan` (subcommand `start-ends`)
   reads the brief and, when the named session is a read-only sitting a
   folder records and is open, writes the plan office land's `land-end`
   ends it by; the same `end_sitting` does the work.
10. **The History line names office start, and the successor**:
    `ended: SID, a read-only sitting, closed by office start, succeeded by
    NEW`, committed as `office start: SID ended in NAME`. The brief said
    "in its words" (land's), but land's words say "closed by office land",
    which would be false here. end_sitting gained `by` and `successor`
    (land-end's `--by` and `--successor`), defaulting to land's own words,
    so every landing reads as before. A deviation; flagged.
11. **An ENDS line that does not lead to an end is one line each**: a
    line that does not read or a second one; the sitting the brief sends
    itself; not open where the office reads; open but not read-only (named
    with `office land SID`, which lands it); and read-only but recorded by
    no folder.
12. **The two-sittings words live in one reader both screens use**:
    office_bale `older_sittings` and `OLDER_SITTING_WORDS` ("an older
    sitting on this folder, probably over"). The newest is the one the
    folder's Sessions section records last, since office start appends
    each, and the ids order it when the folder cannot be read. The words
    come last on both screens, since the brief says the item "ends" with
    them; the walk-in marks its lines after reading every place, so the
    check costs no read of bale beyond the In flight lines' own (my first
    build read every place's status once more before the lines, which would
    have reached a host that does not answer twice). office probe
    orders its sittings the same way (`newest_first`), both in a sitting's
    probe of a project and in a probe of the office itself, so the key
    list offers the newest first.
13. **A prep's doctrine is rendered last on its record line**, after the
    arose and dropped lists: `prep out, SID; doctrine: SHORT [about:
    ...]`. That keeps the lists right after the id, so the existing held
    line assertions hold. One assertion had to change all the same:
    tests/test_meetings_view.py TestThePrepAndItsEnd read the `prep out`
    line byte for byte, and those bytes now carry the stamp by design; it
    reads the line with a pattern now. Only the walk-in compares it, as
    the brief asked; the home screen's prep item and office status do not
    (a Proposal).
14. **prep-brief.md says the sitting prints its standing, and that the
    office files it nowhere.** No folder records a prep, so neither office
    probe nor the home screen's key has a page to file it on. The brief
    asked both templates to say the occupant files it; for the prep that
    would be untrue. A deviation, with a Proposal for a prep's page.
15. **The ENDS line is in the sitting's brief too.** templates/sitting-brief.md
    now tells a sitting that a session it authors as its own successor
    carries `--- ENDS SID ---`, or the line would never be written. The
    brief asked only for the standing in the templates; this followed from
    item 9.
16. **run_probe reads stderr in a thread of its own**, stdout staying in
    the main loop as before, each copied to its own MaskedScreen as it
    comes. The order between the two streams on the screen is as near as
    two pipes allow (each stream's own order is exact). Given no
    err_screen, run_probe is what it was, stderr inherited, and its return
    is the same three values for every caller.
17. **The count's line names the streams only when stderr's mask
    replaced something**: `; 1 credential in a URL on stdout and 1 GitHub
    token on stderr were masked (xxx stands for each)`. Otherwise it is
    0.38.0's line, word for word.
18. **Piped, land prints every block for the planner with the office's
    tail under the marked line, just before the after-land actions'
    summary**, not inside carry_relays as the brief's scope hint had it
    (`print_relays_whole`, called only off a terminal). carry_relays runs
    last, after the summary, and four existing tests pin that what became
    of each after-land action stays land's last lines, with deliver's Next
    line after them on a project with an audience; my first build printed
    the block from carry_relays and broke all four. The tail is worked out
    first now (it never depended on the summary), the block is printed, then
    the summary, then the copy step, then Next. The relays are read once
    for both (`relays_read`), so land's one-line reads stay the four
    tests/test_land.py TestFewerHelperStarts counts. The tail is there on every
    applied landing (with no audience it is the folder line alone), so the
    marked block is too. A deviation in where, not in what; flagged.
19. **The tail's `reviews:` lines are read by the folder's name**, so a
    folder closed at land still finds its branches; gh absent, signed out
    or not answering gives no line (said under OFFICE_DEBUG), as the brief
    asked.
20. **The pty harnesses also kill on the path where a marker is never
    seen.** tests/test_start.py on_a_terminal used to fail its test there
    and leave the child running; it now kills it first. The helpers
    (`kill_hung`, `wait_briefly`) live in test_start.py, and
    test_desk_verbs.py imports them; they kill the child's whole process
    group, since pty.fork makes it a session leader. No test's body
    changed for item 7. The two tests that prove the kill each take about
    10 seconds, the harnesses' grace after the read ends, and run in the
    serial lane.
21. **tests/test_probe.py TestTheMaskIsSaid pinned 0.38.0's sentence
    "The block's stderr, the fallback's probe-output/ files and the block's
    own closing clipboard step ... are not masked".** Item 8 makes the
    first of those false, so the module's docstring says stderr is masked
    on the screen too and the other two are not, and the test now holds
    both halves of the new sentence. Its other assertions are as they were.

## Walkthrough

### What changed

- A new verb, `office standing FOLDER`, and its module,
  lib/office_standing.py: the sitting's standing block read to its shape
  and filed as desk/FOLDER/standing.md, replaced whole and committed alone.
- office probe takes a standing block out of the text it reads, files it,
  and runs the rest; its stderr now passes through the mask.
- The home screen's item for a sitting, the walk-in's In flight line and
  office desk say where the sitting stands, and when two sittings are open
  on one folder, which is the older.
- office start reads a brief's `--- ENDS SID ---` and ends that sitting
  after the successor is out, asked once.
- A prep's record line carries its doctrine, compared on the walk-in.
- office land, piped, prints the planner's block whole with the office's
  tail, and the tail names the folder's reviews.
- The suite's two pty harnesses kill a child that hangs.

### Why

The occupant lost his place in a sitting that ran twenty turns, and
twice a predecessor sitting stayed open beside its successor for a day
and he went back to the wrong one. The rest are the plan's queued
proposals: a credential on a probe's stderr, a tail nobody saw when land
ran piped, review state on that tail, and a terminal lane that hung on
one unanswered question.

### How to explain each piece

- The standing is the sitting's own words about where it is, in a fixed
  shape, so the office can read it and show it without asking. The office
  writes the page; the sitting only prints the block.
- The ENDS line is how a planner says "this sitting replaces that one",
  so the office ends the old one instead of leaving it open.
- The other pieces are small: a mask on stderr, a print when piped, one
  more line on the tail, a kill in two test helpers.

### Questions a reviewer will ask

- Why is the page written by the office and not by the sitting? A sitting
  lands nothing, and the page must be the office's paper for the screens
  to trust it.
- What if the sitting prints a bad block? It is refused by name and the
  page stays as it was; office probe still runs the probe.
- Can the end of a predecessor lose work? No: a sitting lands nothing, and
  the end runs only after the new session is open and its opener copied.
- Does a probe's stderr get kept now? No: it is masked on the screen,
  never kept or copied, as before.

### A hand test

1. Send a planner sitting (`office start --planner`). In its chat, have it
   print a probe block and a standing block in one fence; copy them.
2. `office probe`: one line says the standing was filed, then the probe
   runs as before. Walk in: the sitting's line ends with its step.
3. On the home screen, the sitting's item says the step and what waits on
   you, and a second key files a new standing from the clipboard; copy a
   later block and press it.
4. Have the sitting author its successor bundle with `--- ENDS SID ---`;
   send it with bare `office start`. After the opener, answer the
   question with a return: the old sitting ends, and its folder's History
   says by whom.

## Delivery

- to: the occupant

### Commit

Show where a sitting stands, and end its predecessor (0.43.0)

A sitting's standing block is filed on its folder as standing.md, by
office standing (new), by office probe when it rides with the probe block,
and by a home screen key; the home screen, the walk-in and office desk
show the step and what waits on the occupant. A brief's ENDS line has
office start end the sitting it succeeds, asked once, and the screens say
when two sittings are open on one folder. A meeting's prep record line
stamps its doctrine, compared on the walk-in. The probe's stderr is
masked. office land, piped, prints the planner's block with the office's
tail, and the tail names the folder's reviews. The terminal test helpers
kill a hung child.

### Review

Show where a sitting stands, and end its predecessor (0.43.0)

What to look at: lib/office_standing.py and bin/office file_standing,
the one filing step; cmd_probe's split before its check; office_bale
in_flight's words, older_sittings and ends_plan; office_home
sitting_item_words; start_end_predecessor, after the opener. What to try
by hand: the hand test in the folder's walkthrough, then a landing piped
into a file. Deliberately untouched: the light question block's format
(bale's), office ask, and bale's own clipboard copy of a probe block,
which is bale's to mask.

## Structure

- title: Show where a sitting stands, and end its predecessor (0.43.0)
- size: high
- goal: Show where a sitting stands (0.43.0): a standing block the sitting keeps current, filed on its folder by office standing, office probe and a home-screen key and shown on the home screen, the walk-in and the desk; office start ends the predecessor sitting a brief's ENDS line names and the screens say when two sittings are open on one folder; a prep's doctrine is stamped and compared; the probe's stderr is masked; land's tail on the planner's block is printed when land is piped and carries review state; the terminal test helpers kill a hung child

## Handbook

### Front sheet

office-src 0.43.0 shows where a sitting stands. The sitting prints a
standing block, and `office standing FOLDER` (new, plumbing), office probe
(from the same paste as the probe) or the home screen's key files it on
the folder as standing.md. The home screen, the walk-in and office desk
then show the step and what waits on the occupant. A planner's brief may
carry `--- ENDS SID ---`, and office start ends that sitting once the
successor is out (asked once; `--end-predecessor`, `--keep-predecessor`).
Two sittings open on one folder are said on the screens, the older named.
A prep's record line stamps its doctrine. The probe's stderr is masked.
office land, piped, prints the planner's block with the office's tail, and
the tail names the folder's reviews. Additive: no migration.

### Facts

- a sitting's standing block is read by lib/office_standing.py read_block (the last complete block in a text; each line's blanks at either end dropped) and filed as desk/FOLDER/standing.md by write, only through bin/office file_standing (office standing, office probe, the home screen's key)
- office probe takes every standing block out of its text (office_standing.split) before office_probe's check reads it, so a step naming office-on never makes the block a spanning one
- the screens' standing words are office_standing.words, read by office_bale.standing_words (In flight), desk_standing_lines (office desk) and office_home.sitting_item_words (the home screen)
- two read-only sittings open on one folder: office_bale.older_sittings, the newest being the one the folder's Sessions section records last; office_probe.newest_first orders the probe's choice the same way
- a brief's `--- ENDS SID ---` is office_helper.brief_ends, resolved by office_bale.ends_plan (the start-ends subcommand) and ended through land-end with `--by "office start" --successor NEW`
- a prep's record line ends its lists with `; doctrine: SHORT` (office_meeting.render_record); office_bale.Doctrines.older_stamp compares a stamp that is not a folder's
- office_host.run_probe given err_screen reads stderr in a thread to it; without it stderr is inherited, and its return is three values either way
- land's tail's `reviews:` lines are office_review.tail_lines (the tail-lines subcommand), one gh pr list for the project, matched by the folder's name
- tests/test_start.py kill_hung and wait_briefly are the pty harnesses' kill, used by on_a_terminal and tests/test_desk_verbs.py terminal
- tests/test_standing.py holds 0.43.0's tests (34, in 15 classes); the fast tier carries its verb entry, TestTheBlock and TestTheBriefsSayIt

## Proposals

- **What:** a page for a meeting's prep standing, such as
  calendar/standing-SID.md, filed by `office standing --prep` and shown on
  the home screen's prep item. **Why:** a prep can run as long as a
  sitting, and this session could file nothing for it: no folder records a
  prep (decision 14). **Scope hints:** lib/office_standing.py write takes
  a target path already; the calendar is the meeting's space, so the
  one-writer target is calendar/.
- **What:** compare a prep's doctrine on the home screen's `End the prep`
  item and in office status's doctrine lines, as a folder's sitting's is.
  **Why:** the record line carries the stamp now, and only the walk-in
  reads it (decision 13), so the home screen, where the occupant ends the
  prep, does not say it. **Scope hints:** office_home.home_items' prep
  items; office_bale.doctrine_lines; Doctrines.older_stamp.
- **What:** offer the home screen's standing key from the sitting's first
  turn, not only once a standing exists. **Why:** with the brief's rule
  (decision 5) the first standing must come through office probe or a
  typed `office standing N`; a turn that ends in no probe has no key yet.
  **Scope hints:** office_home.home(), the standing_key condition; one
  more item per sitting, so MAX_ITEMS may want a look.
