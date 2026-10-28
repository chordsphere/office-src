# Notes: 2026-10-27-m10-tidy-002, office-src 0.32.0 (the M10 tidy)

All four items are built as the brief pins them, each with its tests, the
doctrine and README in their own voice, and an additive release, 0.32.0.
Three things to look at on review: one path outside the forecast, the
two probe rounds behind the 0.31.0 numbers, and a test I could not run
whole here.

## Outside the forecast: claude/context/front-sheet.md

`tests/test_suite_clock.py` `TestTheRecord` (in the fast tier) asserts
`- {VERSION} (session` in the development record's front sheet. Bumping
VERSION to 0.32.0 without a line there fails validation, so the goal
needed the file. The brief's forecast and the request's context do not
name it, which I take as an oversight: every 0.x release has added its
line. I read it whole through the second probe (79,071 bytes, sha256
a8bf5c8c...ea17, matching the probe's), and the only change is one new
entry at the top of Recent changes, in the sheet's own shape. Please
admit it at apply. It is listed in `forecast_departures` too.

## What the probes established

- First probe: it ran in /home/chordsphere/work-office, not office-src
  (`office probe 22` resolved there, or it was run from there), so its
  repo and front-sheet sections answered for the wrong repo. Its suite
  record is per machine and stands: the newest detached run,
  20261026T133535Z, `OK 958 tests passed in 245s, at ec8d5c43c573`; the
  run before it, 942 tests in 250s.
- Second probe, run against /home/chordsphere/office-src by path:
  ec8d5c43c573 is HEAD, `[bale sweep 2026-10-26-office-tidy-001]`, and its
  VERSION is 0.31.0. So the 958-test run is 0.31.0's after-land run, and
  958 is 0.30.0's 942 plus test_tidy.py's 16, which I also counted from
  the tree. The working copy holds three untracked telemetry files and
  nothing else.
- The verdict says "with uncommitted changes". That is those untracked
  telemetry files, not a changed source tree.

The 0.31.0 entry now reads: "Tests: tests/test_tidy.py, 16 tests, one
class per item; and the record's pins. The whole suite, run detached
after the landing, passed its 958 tests in 245 seconds on the occupant's
machine, where 0.30.0's run passed 942 in 250." I took "the record's
pins" to be the existing phrase (the TestTheRecord classes), not a third
placeholder.

## What I ran, and what I could not

The request carries no `claude/fixtures/` (the captured bale output every
fake bale replays) and no `migrations/`, so about 80 tests fail in my
sandbox on the tree exactly as 0.31.0 shipped. I judged the change by
failure sets instead: the fast tier plus test_clean_delivery, test_drop
and test_walkthrough_tidy, run on the shipped tree and on the changed one
(the front sheet in both), give identical failure sets. Every one of the
16 new tests passes here. All but one fail on the 0.31.0 code; the
exception is a deliberate negative check (`test_anything_else_is_a_message`).
validation.sh's session assertions pass on the change and fail on 0.31.0.
So the fast-tier claim is predicted, not observed whole. Its wall time
here was 70 s against the 120 s budget, with the fixture tests failing
early; with them passing it will be longer, and I have no number for
your machine.

## Decisions to ratify

- Item 1, which lines count as a box: a task-list item, `-`, `*`, `+`,
  `1.` or `1)` then `[ ]`, `[x]` or `[X]` followed by a space or the end
  of the line (`CHECKBOX_RE`). Only the line's own first box is folded;
  `[xx]`, `[y]` and `-[x]` are not boxes. The fold happens in one place,
  `template_key`, used for the template's lines, for each line of the
  words, and for the "N line(s) are the template's" count.
- Item 2, the dates: the first commit at now, each after it one second
  later, written as `@SECONDS +HHMM` at this machine's offset for that
  instant, which is what git itself would have stamped. With four
  commits the last is three seconds in the future; I judged that
  harmless. The question's one line reads "N commits leave in this
  delivery, dated a second apart, oldest first; one commit per delivery
  is the usual shape (one Commit section in delivery.md)". It is said
  before the commits, in deliver_show. A commit's date line says
  "committed X" too only if a hook made the two dates differ.
- Item 3: the check is in bin/office (`drop_office_command`, awk), since
  lib/office_drop.py is outside the forecast and `took` counts blank
  lines too. Only a clipboard text is asked about. A file or stdin is
  never asked, even on a terminal, as the brief says. A no exits 0 and
  writes nothing, as deliver's "n stops here" does. `office` alone (the
  walk-in) is not counted as a command line: the brief pins
  "begins with `office `", and a lone word is too likely to be a
  message.
- Item 4's tests live in a new module, tests/test_walkthrough_tidy.py,
  since no verb owns RELEASES.md. The name avoids "m10" plus an
  underscore: the suite's OFFICE_SPECIFIC list refuses that string
  anywhere in office-src's own text, the module's own docstring and the
  release note included. Its count of 0.31.0's tests reads test_tidy.py's
  ten 0.31.0 classes by name from the source, so a test added there
  later does not break it.

## Proposals

- **What**: the remaining seven sessions of the sitting's plan should
  forecast claude/context/front-sheet.md and carry it in context.
  **Why**: every release bumps VERSION, and test_suite_clock's
  TestTheRecord needs the matching front-sheet line. This session found
  that only at validation time and needed a second probe round to read
  the file. **Scope hints**: the bundles for m10-sitting-fixes onward,
  all of which bump VERSION.
- **What**: a request on office-src whose worker should run the suite
  should carry claude/fixtures/ and migrations/ as context. **Why**:
  without them about 80 tests fail in the worker's sandbox, and a worker
  can only compare failure sets. **Scope hints**: the include list
  office start builds for an office-src session.
- **What**: after a no, `office drop` could offer to read the clipboard
  again once the occupant has copied the message, rather than ending.
  **Why**: the usual next step is to copy the message and run the verb
  again; one key could save that. **Scope hints**: bin/office cmd_drop,
  after the new question; small.

## Walkthrough

### What changed

- lib/office_letterhead.py: `template_key` and `CHECKBOX_RE`. A line
  is compared with a pull-request template's lines right-stripped and
  with a checklist box read as empty. `pr_template_lines`,
  `hits_in_text` and the check's "line(s) are the template's" count all
  use it.
- lib/office_deliver.py: `commit_dates` (one date per commit, a second
  apart) and `commits_line` (the one line before several commits).
  `commit_words` passes each date to git as GIT_AUTHOR_DATE and
  GIT_COMMITTER_DATE. `read_commits` reads back each commit's author and
  committer date. The plan carries `commits_line`.
- bin/office: `deliver_show` prints the line and each commit's date, and
  deliver's help says so. `drop_office_command` and `cmd_drop` ask about
  a clipboard holding one office command line (`--anyway` the twin), and
  say it in the took line for a file or stdin. The drop's usage says it.
- doctrine/OFFICE.md and README.md: each verb's behavior where it is
  described (the template exemption, deliver's commits, the In-tray
  paragraph).
- RELEASES.md: the 0.32.0 entry. The 0.31.0 entry's two placeholders are
  filled.
- VERSION 0.32.0. claude/context/front-sheet.md gets its 0.32.0 line.
- tests: test_clean_delivery.py (two classes), test_drop.py (two),
  test_walkthrough_tidy.py (new; two). 16 tests; the suite holds 974.

### Why

- The M10 walkthrough's item 14: a ticked `- [x] I have updated the
  documentation accordingly.` refused a delivery as the occupant's
  writing, though it is the template's line with its box ticked.
- Item 15: m10-ui's main showed four commits made in one second. A
  reader notices that, and the report asked for deliver to say so before
  it asks.
- The in-tray drop of 2026-10-27 09:58 holds only
  `office drop --project m10-api`: the clipboard held the command, not
  the message, and the drop took it silently.
- The 0.31.0 note shipped with SUITE_NEW and SUITE_LINE unfilled.

### How to explain each piece

- The checkbox: ticking a box in the repository's own checklist is
  filling in the template, not writing new words, so it stays exempt.
  Write anything after the box and it is your line again.
- The dates: a delivery of several commits now reads as a sequence, a
  second apart in the order they were made. deliver also tells you, before
  you say yes, that one commit is the usual shape.
- The drop: if what you are about to drop is a single `office ...`
  command, it was almost certainly the wrong thing on the clipboard, so
  the drop asks first and defaults to no. Piped or from a file, it never
  asks; it just says so.
- The release note: two words the last session forgot to fill in, now
  filled from the test file and the suite's own record.

### Questions a reviewer will ask

- Does the checkbox fold weaken the letterhead? Only for lines that are
  the template's apart from the box. The phrasing rule and the three
  characters are lifted for those, as before. Names, bale's marks and
  the forbidden list still read every line, and any word added after the
  box puts the line back under every rule.
- Why not one commit always? The brief keeps which commits are made as
  it was. delivery.md's Commit sections decide, and the question now says
  how many leave.
- Are future-dated commits a problem? At most a few seconds, one per
  commit after the first.
- Why does a no not exit 1? Declining is the occupant's choice, not a
  failure, as with deliver's "n".

### A hand test

1. In a scratch office with a project whose repo has
   `.github/pull_request_template.md` holding
   `- [ ] I have updated the documentation accordingly.`, write
   `- [x] I have updated the documentation accordingly.` in a words file
   and run `office letterhead check PATH --words FILE`. The line is not
   named.
2. Copy `office drop --project x` to the clipboard and run `office drop`.
   It asks "Drop it anyway? (--anyway) (y/n) [n]". Press return: nothing
   is dropped and the in-tray is unchanged.
3. On the next real delivery with two Commit sections, read the
   question: one line says 2 commits leave, and each commit shows a
   `dated` line a second after the one before.

## Delivery

- to: nobody

### Commit

Tidy four small things the M10 walkthrough found (0.32.0)

A ticked box in a repository's pull-request template is the template's
line, so the letterhead's exemption holds whatever the box holds; words
added after the box are held as before. A delivery of several commits
dates them a second apart, oldest first, shows each date and says how
many leave before it asks. office drop asks once when the clipboard holds
a single office command line instead of a message (--anyway skips the
question), and says so for a file or stdin. The 0.31.0 release note's two
unfilled placeholders now give its tests and the suite's run. Additive,
no migration; 16 tests added.

### Review

Tidy four small things from the M10 walkthrough (0.32.0)

Look at lib/office_letterhead.py template_key, lib/office_deliver.py
commit_dates and commits_line, and bin/office cmd_drop. By hand: tick a
template's checkbox in a delivery's words and run the letterhead check,
and drop an office command line from the clipboard. Untouched: which
commits a delivery makes, and everything else in deliver, the letterhead
and the drop.

## Structure

- title: Tidy four small things the M10 walkthrough found
- size: small
- goal: Tidy four small things the M10 walkthrough found: the letterhead's checkbox exemption, the delivery commits' one timestamp, a drop that is an office command line, and the 0.31.0 release note's placeholders

## Handbook

### office-src

- office_letterhead.template_key is how a line is compared with a pull-request template's lines: right-stripped, and a checklist box (CHECKBOX_RE: `-`, `*`, `+`, `1.` or `1)` then `[ ]`, `[x]` or `[X]`) read as empty; pr_template_lines, hits_in_text and check's kept count all key by it
- office_deliver.commit_dates(count, now) dates a delivery's commits a second apart as `@SECONDS +HHMM` at the machine's offset; commit_words passes them as GIT_AUTHOR_DATE and GIT_COMMITTER_DATE; read_commits returns date and committed (%aI, %cI); the plan's commits_line (office_deliver.commits_line, "" for one commit) is printed by bin/office deliver_show before the commits
- bin/office drop_office_command FILE (awk) prints the text's one line when it is one non-blank line beginning `office `; cmd_drop asks about it only when the text came from the clipboard (--anyway the twin) and says it in the took line otherwise
- tests/test_office.py OFFICE_SPECIFIC refuses the string m10 followed by an underscore anywhere in office-src's own text, test modules' contents included, so no test module is named with it
- every release's VERSION bump needs a `- VERSION (session SID)` line under Recent changes in claude/context/front-sheet.md (tests/test_suite_clock.py TestTheRecord, in the fast tier); a request that bumps VERSION should forecast and carry the front sheet
- a worker without claude/fixtures/ (the fake bales' captured lines) and migrations/ in its request sees about 80 tests fail on an unchanged tree; compare failure sets before and after rather than reading the run as a verdict
- the detached suite's verdicts are under ~/.local/state/office-src/suite/RUN/verdict on the occupant's machine: 0.30.0's run, 942 tests in 250 s; 0.31.0's, 958 in 245 s (20261026T133535Z, at ec8d5c43c573)
- RELEASES.md's 0.32.0 entry: tests/test_walkthrough_tidy.py holds the release-note and record pins; the suite holds 974 tests

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.32.0
it has had the first of eight sessions planned from the M10
walkthrough's friction: four small fixes. A ticked box in a repository's
pull-request template no longer refuses a delivery, since ticking the
template's own checklist is not your writing. A delivery of several
commits now dates them a second apart, in order, instead of all in one
second, shows each date, and says before it asks how many commits leave
(one per delivery is the usual shape). `office drop` asks once, defaulting
to no, when the clipboard holds a single office command instead of the
message you meant to drop (`--anyway` skips the question). The 0.31.0
release note's two blanks are filled in. The next of the eight is
m10-sitting-fixes.

## Sort

### 2026-10-27-office-drop-project-m10-api.md

- project: office-src
- folder: 22
- goal: Tidy four small things the M10 walkthrough found: the letterhead's checkbox exemption, the delivery commits' one timestamp, a drop that is an office command line, and the 0.31.0 release note's placeholders
- size: small
- tell: the occupant: this drop held only the command line office drop --project m10-api, not a message; if a message for m10-api was meant, drop it again from where it came
- facts: none
