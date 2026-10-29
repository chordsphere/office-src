# notes: 2026-10-29-wave-one-release-005

office-src 0.38.0, the release that closes wave 1. Everything the brief
asked for is here, inside the forecast; nothing was probed and nothing
was asked. The four release paragraphs are in RELEASES.md as their
archived notes hold them, every stale line the four workers listed is
made true, deliver's question prints the plan's `branch_why` and
`joined`, `office letterhead check` passes `--added`, and a wrapped fact
is filed whole.

## The four paragraphs, compared before anything was written

Each fence in the brief was compared with its session's archived
`claude/responses/SID/notes.md`, `### Release paragraph`, before the entry
was written: all four are equal byte for byte once the blank line above
and below each section is set aside, so there was nothing to ask. The
entry was then assembled by copying the archived bytes, never retyped,
and validation.sh holds it to them: each archived notes.md by its sha256
in the request, each paragraph by its own sha256 and size, and the four
as one block, in order, one blank line apart, between exactly one
opening paragraph and one closing paragraph of mine. tests/test_land.py
TestTheWaveOneRecord holds the same in the suite, read from the archives
in the tree rather than from pinned hashes.

## Decisions to ratify

- **The branch line's layout** (the brief left it to me). One line,
  `branch:   NAME[ (HOW)], from BASE (WHY)`: 0.34.0's parenthesis after
  the name stays where it was, so the adoption's fixed sentence and the
  plain `adding to the branch on the audience` read as before, and
  `branch_why` follows the base, as the brief's example has it. When the
  plan has `joined`, its folder and day replace the plain continuing
  words (`(adding to the branch desk/6-x delivered to on 2026-10-28)`),
  and since the plan's `branch_why` already ends with the same news
  (`; desk/6-x delivered to it on DAY, so this delivery continues on
  it`), deliver_show cuts that exact suffix off, so the line says it
  once. The `[office] the delivery branch is ...` log line keeps the
  whole sentence. One wart: the slug rule's why carries its own
  parenthesis when the clone's branch was passed over (`(the folder's
  slug (the clone's branch is main, the base))`). I left it rather than
  rewrite the plan's words on the screen; a later session can reword
  `slug_branch` if it grates.
- **`--added` with `--on PROJECT` is refused by name**, not carried.
  `office letterhead check --on` runs lib/office_deliver.py's `check`
  subcommand, which takes no `--added` (its `check_in_project` does), and
  that module is outside this forecast. Dropping the flag silently would
  be the worse bug, so bin/office dies with `--added reads a tree on this
  machine, not --on PROJECT yet: run it in the project's clone (office
  letterhead check --added PATH)`. The fix is two lines; it is a
  Proposal below and a `deferred` entry.
- **The doctrine core's budget.** The core was 299 lines against a pin of
  under 300, with no paragraph that reflows shorter. Two lines were
  added (section 4's bullet grew from ten lines to eleven; the front
  sheet's probe sentence by one), and two were paid for by rewriting two
  one-word tail lines: principle 5 now ends `new spaces arrive when work
  asks for them.` (was `when real work asks for\n   them.`), and
  boundary 2 ends `even when a session read them for the work.` (was `to
  do the\n   work.`). The banner is still at line 299 and every heading is
  as it was. Read those two if the wording matters to you.
- **The brief's "section 1 (line 64 on)"** is the probe sentence on the
  doctrine's front sheet, which is where line 64 is, in the core. Section
  1 proper sits past the banner and says nothing about the probe. I
  followed the line, per the name-wins rule's spirit, and flag it.
- **A Sort's continuation lines stay verbatim.** parse_sort now keeps an
  indented line under a field line among `field_lines`, so the drop's
  page gets the fact as the session wrote it, and joins it onto the fact
  above for filing. A continuation above `facts:` still makes the
  section a problem (`its field lines are not ...`), as it did before,
  since no other field is meant to wrap; and `facts: none` followed by a
  continuation is the existing `facts: says none, and fact lines follow
  it` problem.
- **Two `office help` lines** (bin/office, the occupant's verb list) still
  said `a branch named from the folder` and the probe's output `back
  whole and the block on the clipboard`; I changed their words (the mask,
  `a branch chosen by one rule`) since they were stale in the same way.
  Text only.
- **Left as it is:** deliver_show's closing line `letterhead on the diff
  and the words: clean` now slightly undersells (the check reads the
  lines the squash adds, not the diff whole). The brief pins deliver_show's
  two new lines as its only change, so I did not touch it; it is a
  Proposal.

## Facts already filed cut off (item 5)

Not rewritten here: the handbook is append-only and is the office's,
not this repo's. Read the way office land read a Handbook section before
0.38.0 (each `- ` line alone), these archived notes give office-src's
chapter a fact cut off at its first line. Whether each was filed depends
on land having found that response, which I cannot see from here, so
take this as the list to look for, by first words:

Each is quoted as its first line reads, so as the chapter should hold it:

- From 2026-10-28-m10-land-flags-005 (0.37.0), five, as the sort-facts
  worker found:
  - "office land passes bale's two accepts (--accept-checkpoint-change,"
  - "bale 0.4.56 refuses a changed checkpoint with"
  - "RELEASES.md's 0.33.0 entry is pinned by sha256"
  - "A probe's paste may come back with CRLF line ends (WSL's clipboard)."
  - "The suite's machine rule (test_suite_clock"
- From 2026-10-29-probe-mask-002, six:
  - "office probe's mask lives in lib/office_probe.py alone: mask_text"
  - "office_host.run_probe writes each chunk of stdout with"
  - "The probe result JSON carries masked, {"url": N, "token": M};"
  - "The mask's secret runs to the last @ of the authority, as"
  - "The block's own closing bale clipboard step copies the raw block"
  - "The suite's text rule (tests/test_office.py OFFICE_SPECIFIC) refuses"
- From 2026-10-29-sessions-read-004, six:
  - "office sessions FOLDER reads projects lazily (lib/office_bale.py"
  - "render_folder_sessions' second value is the count of uncertain misses"
  - "A dossier BaleError whose kind is in PROJECT_WIDE_KINDS (missing, path,"
  - "The hosted dossier batch for office sessions rides each host's first"
  - "In the suite, a project directory the fake bale (tests/fakes/replay_bale.py)"
  - "tests/test_land.py TestTheReleasesMatchTheFrontSheet holds RELEASES.md's"

(Backticks in the originals are dropped above; the chapter's lines keep
whatever the notes had.)

deliver-adds' and sort-facts' own facts are one line each, so nothing of
theirs. With 0.38.0 installed, refiling any of these three responses
adds the whole fact beside the cut-off one (the keys differ); mending
the chapter by hand once, cut-off line out and whole line in, is the
cleaner fix. The release's closing paragraph and the front sheet's Known
problems say both.

## Where each listed stale line went

- deliver-adds: README's deliver summary, fetch bullet (rules 3 and 4,
  and the rename-by-`--adopt` sentence), words bullet (`- branch:`),
  squash bullet (added lines, the told line, the cleanup list),
  shown-whole bullet (the branch line), land's review, the letterhead
  check (cleanup list, `--added`), `office projects` (`branch_prefix` in
  a clause: read, set by no verb yet), the layout rows of
  office_deliver.py, office_letterhead.py and letterhead.toml; the
  doctrine's deliver paragraph (added lines; the branch rule; rules 3 and
  4), the letterhead paragraph (cleanup), the deliver and letterhead
  check rows; bin/office usage_deliver (`--branch`'s default, `--adopt`,
  and the paragraph that still said `or another folder's`) and
  usage_letterhead_check.
- probe-mask: README's "Run a worker's probe" and its details (the line
  by line stdout, the count's masked clause, the worker's suggested
  paragraph, bettered a little), the module table row; the doctrine's
  front sheet sentence and verb table row; usage_probe (the worker's text,
  with `never shown or copied` softened, since the block's own `bale
  clipboard` copy is not masked).
- sort-facts: the doctrine's section 4 bullet, landing paragraph,
  Handbook paragraph and the one clock beside Calendar; README's land
  details; templates/drop-brief.md. tests/test_drop.py pins only the
  fenced Sort format, which is untouched (tests/test_sort.py
  `test_the_briefs_carry_the_doctrines_sort_format` too).
- sessions-read: cmd_sessions' exit-3 line (the wording the worker
  suggested), README's sessions paragraph, the doctrine's section 10
  line. The same die at bin/office line 7683 (`office projects`
  renderings) is not the sessions verb and still fires as before, so it
  keeps its words.

## Places to look closely

- bin/office deliver_show: `json_read` now reads the branch line's seven
  fields in one call (the old code made three plan_field calls).
  `${why%"; $jfolder delivered to it on $jday, so this delivery
  continues on it"}` removes only that exact suffix; the pattern is
  quoted, so a folder name with glob characters cannot widen it.
- lib/office_sort.py `list_items`: a continuation must be directly under
  an item or another continuation; a blank line, a fence or any
  unindented line closes the item. A nested `  - sub` list is two spaces
  and words, so it joins the parent fact, which is what the brief's
  "two or more spaces" asks.

## Validation, as run here

- The untouched request tree (0.37.0 and the four landings): whole suite,
  `tests/run.sh`, OK, 1111 tests.
- This tree: whole suite, `tests/run.sh`, OK, 1124 tests. That run took a
  copy before the last edits (the two `office help` lines' words, and two
  long doctrine and README lines split, no word changed); on the final
  tree the fast tier, the five touched modules whole, and test_office and
  test_suite_clock whole (the doctrine core and the text rules) all
  passed after them.
- `tests/run.sh --fast` with this session's classes, on the final tree:
  OK, 379 tests, 86 to 90 s of the tier's 120 s budget, in a sandbox with
  plenty of cores. If your machine is slower and the budget bites, the
  whole-module names are the expensive part; drop
  `test_audience_line.TestABranchAnotherFolderDeliveredTo`, which only
  re-runs an assertion I moved.
- validation.sh rehearsed in a staging copy (the request tree, files/
  over it, apply.sh run): PASS with `--slow`, every claim `[agree]`; the
  fast tier took 85.7 s, the five touched modules whole 200 tests OK. On the untouched tree, the session's
  assertions fail as they should (the paragraphs, VERSION and the
  front sheet line), and the RELEASES.md tail and the doctrine checks
  pass on both, since they guard what must not move.

## Proposals

- **What:** `office letterhead check --on PROJECT --added`.
  **Why:** the module takes `--added` and `check_in_project` passes it,
  but lib/office_deliver.py's `check` subcommand has no `--added`
  argument, so bin/office refuses the pair today.
  **Scope hints:** lib/office_deliver.py `main`, the `check` parser and
  its call (`added=a.added`); bin/office's refusal comes out, and
  usage_letterhead_check and README lose `nor with --on yet`.
- **What:** deliver_show's last line reads `letterhead on the lines it
  adds and the words: clean` (or similar).
  **Why:** since deliver-adds the check reads the squash's added lines,
  and the screen line still says `the diff`.
  **Scope hints:** bin/office deliver_show's embedded Python, one string;
  test_audience_line and test_clean_delivery assert the old words in a
  few places.
- **What:** the sort brief could say a fact may wrap and is filed whole.
  **Why:** templates/sort-brief.md says write facts bare and nothing
  about wrapping, which is now safe; it was outside this forecast.
  **Scope hints:** one clause after its bare sentence;
  tests/test_sort.py `TestTheSortBriefSaysWriteFactsBare` pins the
  sentence that is there, so add after it.

## Walkthrough

### What changed

- RELEASES.md: the 0.38.0 entry, four sessions' paragraphs as written,
  with an opening and a closing paragraph; VERSION 0.38.0; the front
  sheet's 0.38.0 line, its What it does and Known problems.
- README.md, doctrine/OFFICE.md, bin/office's usage texts and
  templates/drop-brief.md: what deliver, probe, land's filing, the
  letterhead check and office sessions do now.
- bin/office: deliver's question names the rule that chose the branch,
  and the folder whose branch it continues; `office letterhead check
  --added`; office sessions' stop line.
- lib/office_sort.py: a fact that wraps is read whole.

### Why

Wave 1's four sessions each changed one corner of the tool and, by
design, left the docs and the version for one release afterwards, so
they could run side by side. This is that release. The screen lines show
what the plan already knew, and the wrapped fact closes a loss the
sort-facts worker found in the office's own handbook.

### How to explain each piece

- The release notes: four paragraphs written by the sessions that made
  the changes, copied exactly, between a short note of what the release
  is and a short note of what this last session added.
- The branch line: before pushing, deliver now says why the branch has
  the name it has, and when it is a branch another job already
  delivered to, which job and when.
- `--added` on the hand check: the same reading deliver does, so you can
  ask the question deliver will ask before you deliver.
- The wrapped fact: a fact written over two lines used to be cut at the
  first; now it is filed whole. What was cut before stays cut, by hand to
  mend.

### Questions a reviewer will ask

- Were the four paragraphs retyped? No. They were copied from the
  archived notes and checked by hash, and a test compares them on every
  run.
- Why is `--on` refused with `--added`? The part that runs the check in
  a project's repo does not take the flag yet; refusing says so, where
  dropping it would check something else than asked.
- Does the wrapped-fact join change anything already filed? No. Old
  lines stay; a refiling of an old response adds the whole fact beside
  the cut-off one.

### A hand test

1. In an office with a project that has an audience and a
   `branch_prefix = "feature/"` in its floor plan entry, write `-
   branch: results-view` under delivery.md's `- to:` line and run
   `office deliver N` without `--yes`: the branch line reads
   `feature/results-view, from main (delivery.md's branch line names
   results-view, behind PROJECT's branch prefix feature/)`. Answer n.
2. In a clone with a file that already holds an em dash on some line,
   change another line, `git add` it, and run `office letterhead check
   --added`: exit 0, and one line saying the file already had it.
3. Land a response whose Handbook fact wraps onto an indented line, and
   read the chapter: one line, the whole fact.

## Delivery

- to: nobody

### Commit

office-src 0.38.0: wave 1 released, and three small changes

Rolls the four side-by-side changes of the last round into one release:
their release paragraphs as written, and every line of README.md, the
doctrine, the usage texts and the drop brief that they left out of
date. Three behavior changes ride with it. office deliver's question
says which rule chose the branch and, on a branch another folder
delivered to, which folder and when. office letterhead check takes
--added, reading the lines a range or the index adds, as deliver does.
And office land files a handbook fact that wraps onto indented lines
whole, where it filed only the first line before; lines filed cut off
stay as they are.

### Review

office-src 0.38.0: wave 1 released

What to look at: the 0.38.0 entry in RELEASES.md (the four middle
paragraphs are copied, and a test holds them to their source), the
branch line in bin/office deliver_show, the --added pass-through in
office letterhead check, and list_items in lib/office_sort.py.

What to try by hand: deliver without --yes on a project with a branch
prefix and read the branch line; run office letterhead check --added on
a staged change to a file that already held a refused character; land a
response with a wrapped handbook fact and read the chapter.

Deliberately untouched: --added through --on PROJECT, the branch prefix
flag, and facts already filed cut off.

## Structure

- title: office-src 0.38.0, closing wave 1
- size: medium
- goal: Release office-src 0.38.0 closing wave 1: the four landed sessions' release paragraphs in RELEASES.md verbatim, every doc line they left stale made true, deliver's question naming the rule that chose the branch, --added through office letterhead check, and a wrapped handbook fact filed whole

## Handbook

### office-src

- RELEASES.md's 0.38.0 entry carries wave 1's four release paragraphs byte for byte from their archived notes.md, and tests/test_land.py TestTheWaveOneRecord compares them on every run, so an edit inside those four paragraphs fails the suite.
- The doctrine's core sits at 299 lines against tests/test_office.py's pin of under 300, with no paragraph that reflows shorter: a line added above the PAST THE CORE banner has to be paid for by rewording another.
- bin/office deliver_show reads the branch line's fields in one json_read and prints branch_why after the base; it strips branch_why's joined clause so the folder and day are said once, in the parenthesis after the name.
- office letterhead check --added refuses --on PROJECT by name because lib/office_deliver.py's check subcommand has no --added argument, though check_in_project takes added=.
- lib/office_sort.py list_items is the one reader of `- ` items with continuation lines (two or more spaces, outside a fence, directly under an item); parse_handbook uses it, and parse_sort joins continuations onto the fact above while keeping them verbatim in field_lines.
- Handbook facts filed before 0.38.0 from wrapped facts are cut off at their first line in office-src's chapter (five from 0.37.0's session, six each from the probe-mask and sessions-read sessions), and refiling those responses adds the whole fact beside each.

#### Front sheet

office-src is at 0.38.0, which closes wave 1 of the plan begun on
2026-10-27. office deliver reads only the lines a delivery adds, refuses
words that name a cleanup, chooses its branch by one rule and says which
rule on the question, continues on a branch another folder delivered
to, and refuses work another folder already delivered. office probe
masks a credential in a URL and a GitHub token on the screen and the
clipboard. office land files a handbook fact bare and, now, whole when
it wraps. office sessions reads past a project it cannot read. `office
letterhead check --added` reads what a range or the index adds. Still
open: `--added` through `--on PROJECT`, a verb to set a project's branch
prefix, the refresh of a hosted clone and the squash-merged review
deliver cannot see, and the facts filed cut off before 0.38.0, which
are yours to mend by hand once if you want to.
