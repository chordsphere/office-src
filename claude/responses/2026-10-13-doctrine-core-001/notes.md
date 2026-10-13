# Notes: 2026-10-13-doctrine-core-001, office-src 0.17.2

Three things, as the brief asked: the doctrine reads core-first, office
start carries a bundle bale did not open a new session for, and the
walk-in says when the detached suite did not pass. One of them turned out
different from the brief's diagnosis, and that is the first thing to read.

## The newly-open check: the brief's diagnosis was not the cause

The brief's guess was that the office looked for a session dated the
day of the start. It does not, and did not on 2026-10-12: since the
return trip, `open_bundle` reads `bale status --json`'s open set before
`bale open` and after it, and takes the one session that is new. Before
building anything I made the suite's fake bale mint a sid dated from a
bundle's stem, opened `2026-10-08-audience-line` on today's date, and the
unchanged code recorded it and filled the tray. So I probed.

What the probe established (paste-back, read-only, on your machine; the
facts this response relies on, per TARBALL.md 4.5):

- bale is 0.4.52; office-src's install is 0.17.1 at 1137373.
- `2026-10-08-audience-line-002` was minted on 2026-10-08 at 14:25 UTC by
  a real open of the bundle (its log: "pack clock ... the sid's date is
  this instant's date"; "opened from bundle '2026-10-08-audience-line'").
  Its id is dated 10-08 because it was opened on 10-08, not from the
  stem. There is no 2026-10-08-audience-line-001 in bale's records.
- On 2026-10-12 at 12:20 UTC, `2026-10-08-audience-line (1).bale-bundle`
  (your browser's second download, saved 08:19 local) went to `bale
  open` while 002 was still open. bale logged: "second desk: bundle
  2026-10-08-audience-line.bale-bundle matches the bundle open session
  2026-10-08-audience-line-002 was opened from; recording desk-2 on that
  session instead of opening a new one". The dossier shows it as an
  `open opened` attempt on 002. No sid was minted, so the open set did
  not move, so the office's diff found nothing new and it stopped before
  the tray.
- bale 0.4.52's `bale open --json` (since 0.4.48) says exactly this: its
  line's `outcome` is `opened` or `second-desk`, with `sid` (the minted or
  joined session), `tarball` (since 0.4.50 for a second desk; null when
  the request has left the outbox) and `opener` (the desk's paste text).
  Read from `format_open_json`'s docstring in your bale's
  bin/bale_report.py, which owns that key contract. No live line was
  captured; see Proposals.
- The office's own overlap refusal did not fire, so the bundle was most
  likely given by bare name (a name bale's search finds), which the
  office cannot read and leaves to `bale open --check`, and bale's check
  passes a second desk. I am inferring this; the probe did not capture
  your terminal.
- Your machine has no detached run yet: no `~/.local/state/office-src/suite`.

So the check already diffed the registry; what it could not see is a
second desk, because a second desk changes nothing in the open set. The
fix keeps the diff and adds what bale now says:

- From bale 0.4.50 (`[surfaces.open_json]`'s `since`), office start runs
  `bale open BUNDLE --json` and holds its line to the diff: `opened` must
  be the one session newly open; `second-desk` must name a session open
  before and after, with nothing newly open. A line the diff contradicts
  is refused in both words. The tarball is still held to the request
  `bale status` lists for that sid.
- A second desk is carried, not refused: the folder records the joined
  session as `- SID: a second desk on a session already open`, the tray
  carries that session's request and the context tarballs as for any
  start, the opener printed is the desk's, a warning says no new session
  was opened, and the first line says `Joined SID, already open, as a
  second desk for desk/NAME.` instead of `Packed`.
- Below 0.4.50 the office keeps the human report and the diff. A start
  that finds nothing newly open now says a second desk is the likely
  reason (bale 0.4.44 on) and that bale 0.4.50 names it.
- The version is this machine's `bale --version`, or a host's from the
  start's own round (`hosted_round(..., version=True)` adds it to the
  connection the start already makes; no extra connection).

This is a flagged deviation from the brief's mechanism. The brief said:
"find the session a bundle opened by diffing the registry ... never by
the day of the start and never by parsing .bale/". The diff stays and
nothing reads a day or .bale/. But on its own the diff cannot see the
live case, so I added a second --json surface. Ratify or correct.

Did the same diff serve the non-bundle start? No, and I did not add it.
`bale pack --json` reports the sid it minted, which is bale's declared
contract; a pack cannot be a second desk; and a diff around it would
cost a status read and add nothing.

The brief's test: `test_land.TestStartABundle.test_a_stem_dated_days_before_the_start`
opens bundles stemmed 2026-10-08 and 2026-10-01 today, through the human
report (bale 0.4.45) and through --json (0.4.52), and checks the sid is
bale's, newly open, recorded and in the tray. It passed on the code as it
stood, which is how I knew to probe. What fails without the fix is
`test_the_live_case_a_second_desk_is_joined_recorded_and_carried`: the
bundle opened on "2026-10-08" (the fake's clock, `FAKE_BALE_DAY`), its
`(1)` copy started days later by bare name. The suite's fake bale now
knows `open --json`, a second desk (matched on the bundle's content, not
its file name, as bale matches) and `--check` on one, and reports
`FAKE_BALE_VERSION`.

## The doctrine's core

doctrine/OFFICE.md opens with a reading card, the first 22 lines of the
file including the title and intro: a five-row table at the top of the
front sheet.

- A build session on a project: the card and front sheet, section 2,
  section 3, section 4 to the end of its list, and section 9.
- A work session in an office: the build row, plus section 5 for the
  spaces it writes, section 6 and section 15.
- The founding session: the work row, plus section 12.
- A sitting: the work row (its space the drafting table), plus the rest
  of section 4, section 7 and section 8.
- A session building office-src: the whole doc.

The two rows that differ from the brief's list are mine. The founding
session gets section 12 because that section says what the founding
session writes. A sitting gets section 8, "When to open a session",
because deciding that is a sitting's work. Strike either if you
disagree.

Counted from the file: a build session's prescribed read is now lines 1
to 199, through the PAST THE CORE banner, against 1,044 lines read whole
before. The file is 1,079 lines: 1,044 unchanged plus 35 added (the card,
three pointer blockquotes, the banner and its rules, and section 4's
continuation heading). That is under the sitting's 300 and under a
quarter. About 53 of the 199 lines are the front sheet's plain-language
prose, which a build session could skip. I kept it in the core rather
than split a second section, since it is what the occupant reads too.

How it moved, and one deviation to ratify:

- Above the banner, in reading order: the front sheet (card first), §2,
  §3, §4's opening and its list, §9. Below, in number order: §1, the rest
  of §4, §5 to §8, §10 to §15.
- **Section 4 sits in two places.** Its list (how a session is packed,
  and the doctrine tarball beside the request) is the build read. The
  rest (office start, land, the downloads, finishing, delivering) is
  120 lines a build session never needs. The rest sits past the banner
  under `## 4. How a session is packed, continued`. Nothing is
  renumbered, but a section is split, and the brief only said sections
  move. Keeping section 4 whole in the core would make the build read
  about 320 lines.
- Each moved section leaves a one-line pointer where it was (DOCS.md
  6.4's tombstone). The added lines are navigation, not doctrine.
- Words stay: validation.sh undoes the reorder (drops the card, pointers,
  banner and continuation heading, and puts the sections back in number
  order) and compares the result's sha256 with OFFICE.md as the request
  shipped it, e1ee4d0a…. It is byte-identical.
- The suite's doctrine readers split by heading text, never by line, as
  the brief guessed: test_office (TestText's space table, verb table,
  profile, the bale/office line), test_desk_verbs.TestCatalogAndDoctrine,
  test_return_trip, test_out_trip_to_host, test_project_on_host and
  test_audience_line's TestTheRecord, test_project_on_host's doctrine
  line, and test_watches_digest.TestDoctrineAndTemplates. All pass. The
  `split("## 4.")...split("## 5.")` readers now get core §4 through the
  continuation, a superset of what they read before. The card's first
  column is capitalized so the verb-table regex does not read it as
  verbs.
- `test_office.TestTheDoctrinesCore` (5 tests) pins the new shape: the
  card in the first 30 lines with its five rows, the headings above and
  below the banner in that order, a core under 300 lines and at most a
  quarter of the file, every section the build row names in the core,
  none of the spaces table, verb table, drafting table or upgrade rules
  in it, and the pointers. All five fail on the old doctrine.
- README.md's pointer at the doctrine resolves as before, and its
  inventory row now mentions the card.

Not changed, because the constraint forbids it: section 7's account of
the walk-in does not mention the new Suite line (it does mention the
Install line). See Proposals.

## The walk-in's Suite line

`lib/office_bale.py`: `install_source` is split out of `install_behind`.
It is the existing "does this office scope the install's own source"
test (INSTALLED's source: against the [projects] table, local projects
only). `suite_verdict` reads `latest/verdict` under
`$XDG_STATE_HOME/office-src/suite`, else `~/.local/state/...`, the
runner's `state_dir` exactly. `suite_verdict_words` decides what to say:

- OK says nothing.
- FAILED and BROKEN are said as written; the runner's line already
  names the log.
- RUNNING says nothing for an hour, then the line plus "still RUNNING
  after N hour(s), so the run has likely died: read …/run.log".
- Any other line is said as such, never taken for OK.
- No state directory, or no `latest`, says nothing.
- A run named with a verdict that cannot be read, or an empty one, is
  said, not skipped. That is one decision beyond the brief: the silent
  skip rule.

The walk-in's two install lines come from one reader call,
`install-lines` (it replaces `install-behind`, whose only caller was the
walk-in), so the walk-in spawns no extra process. The Suite line prints
right after the Install line, before the blank line. The Next line and
everything else are untouched; the end-to-end test compares the walk-in
with and without a FAILED verdict.

Tests: `test_third_trip.TestInstallBehindItsSource.test_the_suite_verdict_when_it_is_not_ok`
(real install, real walk-in; an unscoped source hears nothing; no run;
FAILED; OK; BROKEN; old RUNNING; the HOME fallback) and
`test_third_trip.TestTheSuiteVerdict` (units, and a pin holding the
reader to tests/runner.py's state directory and verdict shapes).

## Version

0.17.2, the sitting's guess. Additive: no migration, and no verb gains
a flag or a question. The start change makes start do what the doctrine
already promised for a bundle (record the session, fill the tray). The
Suite line only appears in an office that scopes office-src's own
source, and it surfaces the verdict 0.17.1's `--detach` already writes.
If you count the Suite line as a feature, rename the heading to 0.18.0;
nothing else depends on the number.

## Forecast, paths, things to look at

The forecast is the whole tree (`.`); no departures. Paths changed:
doctrine/OFFICE.md, lib/office_bale.py, bin/office (exec bit restored by
apply.sh), share/bale-consumption.toml, README.md, RELEASES.md, VERSION,
claude/context/front-sheet.md, tests/test_office.py, tests/test_land.py,
tests/test_start.py (the fake's `FAKE_BALE_DAY` and
`FAKE_BALE_VERSION`), tests/test_third_trip.py. The README's walk-in and
`--detach` paragraphs are user-facing docs edited along the way.

Look closely at `open_bundle` (lib/office_bale.py) and its error
wording. Also look at the decision to record a second desk in the folder
being started, even when another folder already records the session. I
record it with words because you asked to start this folder with this
bundle, and the walk-in and `office sessions` then show both folders.
The start's warning names any other folder that records the joined
session (`folders_naming`), so a re-start like 2026-10-12's would have
named 2026-10-08-audience-line.

## Validation, and the whole suite

In my sandbox (two cores, four jobs), I ran validation.sh against a
staging copy: the request's tree with `files/` laid over it, mode bits
stripped, `apply.sh` run, and no `.git`.

- Without `--slow`: every check passed. The fast tier plus this
  session's names ran 292 of the suite's 692 tests in 82.8 seconds of
  wall clock, under the 120-second budget, and the whole script took 85
  seconds.
- With `--slow`: the whole suite passed, 692 tests, OK. The script took
  21 minutes 36 seconds in all, so about 20 minutes for the suite.
- An earlier whole run in the working tree, before the last edits, was
  also 692 OK, in 20 minutes 32 seconds.
- One fix came after those whole runs. A later fast run caught my
  walk-in test comparing two walk-ins whose header clocks straddled a
  minute. The test now masks the clock and compares the whole walk-in
  minus the Suite line, which is stricter than before. The final bytes
  passed the fast path again in fresh staging: 292 tests, 80.9 seconds;
  that module's change is test-only.

On the unmodified tree, the session's assertions fail: the open_json
declaration, the doctrine's reassembled bytes, the 0.17.2 stamp, and the
fast tier, since the new names are not in the suite yet. The five
TestTheDoctrinesCore tests fail on the old doctrine. Both new start
tests pass on the old code. I wrote them first to see whether a
past-dated stem broke anything, and it did not; that is what sent me to
the probe. The live-case test is the one that fails without the fix.

`validation_will_run` lists the whole suite behind `--slow`, as
TARBALL.md 7.6 asks. bale apply cannot pass `--slow`, so the whole suite
runs only by hand in staging, or detached after landing. The after-land
line from 0.17.1 still applies:
`office projects set office-src --after-land ./install.sh --after-land "tests/run.sh --detach"`.
Once a detached run has written a verdict, the walk-in's Suite line will
tell you when it is not OK. Your machine has no detached run yet.

No light question blocks this session; one probe, answered.

## Proposals

- **What:** capture a live `bale open --json` line on a bale 0.4.52, for
  both `opened` and `second-desk`, into
  claude/fixtures/bale-0.4.52/open-json/, and replay it in the fake.
  **Why:** this session read the key contract from bale's docstring
  through a read-only probe and could not write a throwaway repo, so
  `[surfaces.open_json]` is the one surface the office reads without a
  capture. **Scope hints:** a file-based probe (TARBALL.md 4.4) under
  ./probe-output/; test_land's fake open.
- **What:** decide whether a bundle the office can read, whose forecast
  overlaps an open session that the same bundle opened, should be let
  through to bale as a second desk instead of refused in the office's
  own words (doctrine §4: "A session whose forecast overlaps one already
  open is refused before bale is asked"). **Why:** today a second desk
  reaches bale only by bare name. Given a path, the office refuses it as
  an overlap, which tells the occupant to land the very session the
  bundle would join. The office cannot tell which bundle opened a
  session without reading .bale/; `bale open --check --json`'s
  `rehearsal` key may say so (its contract was cut off in the probe's
  output). **Scope hints:** `bundle_precheck` and `overlap_lines`;
  doctrine §4. A planner's ruling first.
- **What:** one sentence in doctrine §7's walk-in paragraph for the Suite
  line, beside the Install line it sits under. **Why:** this session's
  constraint kept the doctrine's words fixed, so the walk-in now shows a
  line its doctrine does not name. **Scope hints:** OFFICE.md §7, past
  the core; TestTheDoctrinesCore is unaffected.

## Walkthrough

### What changed

- `doctrine/OFFICE.md` opens with a reading card at the top of its
  front sheet. It is a five-row table that names, for each kind of
  session, the sections it reads.
  - What a build session on a project reads sits above a PAST THE CORE
    banner, in reading order: the card, the front sheet, sections 2
    and 3, section 4 to the end of its list, and section 9. That is 199
    lines, against the 1,044 such a session read before.
  - Everything else sits below the banner in number order: section 1,
    the rest of section 4, sections 5 to 8 and 10 to 15.
  - No section is renumbered and no sentence changed. Each moved section
    leaves a one-line pointer where it was, and section 4's remainder
    carries a continuation heading under its own number.
- `office start --bundle` carries a bundle that bale takes as a second
  desk. A second desk is a bundle whose session is still open, so bale
  joins it instead of opening a new one.
  - From bale 0.4.50 it reads `bale open --json` and checks it against
    the open sessions before and after.
  - It records the joined session in the folder ("a second desk on a
    session already open"), fills the out tray with that session's
    request, and prints the desk's opener. It names any other folder
    that records the session, and its first line says `Joined` instead
    of `Packed`.
  - With an older bale, a start that finds nothing newly open names the
    second desk as the likely reason.
  - `share/bale-consumption.toml` declares the new surface, `open_json`.
- The walk-in shows one `Suite:` line, right after the header, when the
  latest `tests/run.sh --detach` verdict is FAILED, BROKEN or RUNNING
  for over an hour. It does so only in an office that scopes office-src's
  own source. The reader's `install-lines` gives the walk-in both its
  Install and Suite lines in one call.
- Tests:
  - `TestTheDoctrinesCore` (test_office) for the doctrine's shape;
  - four bundle starts in `test_land.TestStartABundle`, with the fake
    bale taught `open --json` and second desks;
  - the Suite line end to end and as units in test_third_trip.
- README, RELEASES (0.17.2), VERSION and the development record's front
  sheet follow.

### Why

- Most office-src workers read the whole doctrine, 1,044 lines, when a
  build session on a project needs about a fifth of it. The card says
  which fifth, and the banner keeps that fifth together at the top.
- On 2026-10-12 the audience-line bundle's browser copy was started
  while its session, opened on 2026-10-08, was still open.
  - bale recorded a second desk on that session and opened nothing.
  - The office saw no new session and made no tray, though the session
    was open and waiting.
  - The cause was the second desk, not a date: the office has always
    found the session by what opened, never by the day.
- The detached suite writes its verdict where nobody looks. The walk-in
  is where you already look.

### How to explain each piece

- **The card:** "find your row, read those sections, stop". A worker on
  a project reads 199 lines; a worker on office-src still reads it all.
- **The banner:** a line that says everything above it is the common
  read. The sections below are the same words, still under their
  numbers.
- **The second desk:** opening the same bundle twice gives a second chat
  on the same session, not a second session. The office now follows
  bale there instead of stopping.
- **The Suite line:** silence means the last full run passed, or never
  ran. A line means read the log it names.

### Questions a reviewer will ask

- **Did any doctrine words change?** No. validation.sh puts the
  sections back in number order, drops the card, pointers, banner and
  continuation heading, and gets the original file's sha256.
- **Why is section 4 in two places?** Its list (how a session is
  packed, and what the doctrine tarball beside the request is) is the
  build read; the other 120 lines are start and land mechanics. Kept
  whole, the core would be about 320 lines.
- **Why not just diff the registry, as the brief said?** It already
  did. A second desk changes nothing in the open set, so only bale's
  own `--json` line can say which session was joined. The diff stays as
  the cross-check.
- **What if your bale is older than 0.4.50?** Start behaves as before
  and, when nothing is newly open, says a second desk is the likely
  reason.
- **Why record the joined session in another folder?** You asked to
  start that folder with that bundle. The warning names the folder that
  already records the session.
- **Will the Suite line show in other offices?** No. It shows only
  where the office scopes the project the install came from, the same
  test as the Install line.

### A hand test

1. Read the top of `doctrine/OFFICE.md` in the install. The card should
   end by line 22, the PAST THE CORE banner should sit near line 193,
   and section 4's continuation should come after section 1, below it.
2. A second desk, in a scratch repo. Open any small bundle there with
   `office start` (it gets a sid, say SID). Then start a copy of the
   same bundle, saved as `NAME (1).bale-bundle`, for another folder,
   by bare name. Expect:
   - `Joined SID, already open, as a second desk for desk/...`;
   - an out tray holding `request-SID.tar.gz`;
   - an opener naming `SID@desk-2`;
   - a warning that names the first folder;
   - the second folder's Sessions line reading
     `- SID: a second desk on a session already open`.

   Then `bale unlock SID` in the scratch repo, if it was read-only, or
   land it as usual.
3. A bundle stemmed days ago: start one whose stem is dated a week back
   for a fresh folder. The folder should record the sid bale printed in
   `bale status`, dated today, and the tray should fill.
4. The verdict:
   1. Run `mkdir -p ~/.local/state/office-src/suite/x`.
   2. Run `echo "FAILED 2026-10-13T00:00:00Z: 1 of 692 tests failed, in 9s, at test; read /dev/null" > ~/.local/state/office-src/suite/x/verdict`.
   3. Run `ln -sfn x ~/.local/state/office-src/suite/latest`.
   4. Walk into home-office. Expect one `Suite: FAILED ...` line under
      the header and nothing else moved.
   5. Then `rm -r ~/.local/state/office-src/suite`, or let the first
      real `tests/run.sh --detach` replace `latest`.

## Delivery

- to: nobody: office-src has no audience

### Commit

Read the doctrine core-first, carry a second desk, show a failed suite

The office doctrine opens with a reading card that names, for each kind
of session, the sections it reads. What a build session on a project
reads now sits above a PAST THE CORE banner in reading order: 199 lines,
where it read all 1,044 before. Every other section sits below in number
order, with a pointer where it was. No section is renumbered and no
sentence changed; section 4 is split across the banner under its own
number.

office start no longer stops when a bundle's session is still open and
bale takes the bundle as a second desk on it instead of opening a
session. From bale 0.4.50 it reads bale open --json, checks it against
the open sessions before and after, and then:

- records the joined session in the folder;
- fills the out tray with that session's request;
- prints the desk's opener.

Older bales get a message naming the likely reason.

Walking into an office that scopes office-src's own source shows the
latest detached suite verdict in one line when it is not OK.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.
