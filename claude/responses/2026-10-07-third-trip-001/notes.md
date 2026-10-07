# Notes: 2026-10-07-third-trip-001, the third trip (office-src 0.13.0)

The brief's seven items, built as one additive release, 0.13.0. The
pre-flight said they fit one session, so I didn't split them. Nothing
landed outside the forecast (the forecast is the whole repo).

Bottom line: a start that cannot get its session out now fails before it
writes anything, or ends on the one line that retries it. `office start`
asks `bale open --check` first, checks a new folder's title before any
other question, and offers the riders its pack carries. `office land`
runs watches check and closes the founding folder. The walk-in says when
the install is behind its source. A profile answer can be a paragraph.
The suite runs side by side. bale 0.4.47 changed nothing the office reads.

One contradiction, pushed back as you asked: the brief says bale is
0.4.46, but this request was packed by **0.4.47** (its manifest says so,
and so did the probe). I checked the bale that is installed.

## What the probe established

One paste-back probe ran before any code. You pasted it back whole: 442
lines, and the integrity count matched. Your console showed two UTF-8
characters as CP437 (`ΓÇö` for `—`, `┬º` for `§`); I restored them before
hashing the captured lines. In `~/office-src` and home-office it ran only
`bale status` / `bale stats`, git reads and `office version`. Everything
else ran in throwaway repos under one `/tmp/office-probe.*` directory,
which it removed. bale's `~/bale/user` was the same before and after.

- **bale 0.4.47** at `~/bale`; WSL2, TZ unset, Python 3.12.3. office-src
  0.12.0 installed at `6abdf51`, the source's HEAD (level). office-src
  holds this session open, forecasting `.`; home-office holds the sitting
  `2026-10-03-plan-4b-sitting-001` read-only, and its last commits are
  this bundle's start (the sitting's page filed, the session recorded in
  `2026-10-06-third-trip`). Each repo showed one uncommitted change; the
  probe didn't say which file, and none of this work depended on it.
- **The read surfaces**: every key the consumption manifest declares
  resolved in 0.4.47's lines, in office-src and home-office. That covers
  status, stats, `--work-class`, `--since`, both together, a dossier, a
  miss, and the `--since`-beside-`--sid` refusal, which is word for word
  the same. What 0.4.47 added is additive: a `clipboard` object on
  `status --json`; `message`, `open_sessions` and `reason` on
  `unlock --json`; and a JSON line on stdout when `unlock` refuses
  (`outcome: unlock-refused`, still exit 1 with the error on stderr). The
  dossier "additions" the diff showed are values that were null in the
  0.4.45 captures, not new keys.
- **The making surfaces**: pack `--json` and `--context --json` have the
  same keys. The opener's scissors are on stderr for pack and on stdout
  for open. open's `  tarball:        ` line is unchanged, and so are
  apply's `=== RELAY` markers and the three commit subject shapes.
- **`bale open --check`** (in bale's help since 0.4.45) answers item 7.
  - A missing bare name: exit 1, the refusal and every directory
    searched.
  - A found name, or an absolute path: exit 0, with a report whose first
    line names the path bale found and whose `wrote:` line says nothing.
  - A forecast path that doesn't exist, or a forecast overlapping an open
    session: exit 1, each refused in its gate's words.
  - Outside a repo: refused.
  - The repo's git status, `.bale/` listing and open sessions were
    identical before and after the checks.
- **One oddity the office doesn't read**: `stats --json --work-class
  meta` in office-src reported no class on 0.4.47, though office-src
  holds meta records (0.4.45 reported `meta` with 1 session). The office
  never asks the aggregate for a single work class. It's a question
  below.

The captures that matter are in `claude/fixtures/bale-0.4.47/`
(open-check/, unlock/, anywhere/), with a README saying what was checked.
The 0.4.45 captures stay the suite's floor.

## Decisions to ratify

1. **The Next-line order (item 5), as ruled.** The install behind its
   source comes right after the version cases and before a session out.
   The doctrine's Next-line paragraph, README's table and RELEASES.md say
   so. One line in the walk-in header, `Install: BEHIND: ...`, uses
   `office status`'s words exactly (a test compares the two). It shows
   only when the office scopes the install's source (home-office scopes
   office-src).
2. **`bale open --check`, not the open moved first (item 7).** It finds
   a bare name and runs every gate while writing nothing. So nothing else
   in start moved: the folder, the survey, the tray, then the open. It
   runs for every bundle, not only bare names, since it also catches gate
   refusals early. That costs one more bale call per bundle start. A
   bundle the office can read is still refused first in the office's own
   words (`bundle_precheck`: paths not in the tree, an overlap), as
   before.
3. **`new` with a bundle asks where first.** Then, for a project, comes
   the check, and only then the folder. A bundle that lands in the office
   is checked once its folder exists, because its forecast may name the
   folder. If that check fails, the retry line covers it.
4. **The retry line.** When start opened a folder through `new` and then
   fails, an EXIT trap prints the folder it opened (number and name) and
   one command line. That line carries the folder, where, the bundle as
   you gave it (or `--goal`, `--write` and the other flags you gave or
   answered), and `--leave-out`/`--no-rides` as answered. The trap clears
   once the session is out. Your case would have ended on: `office start
   2026-10-06-third-trip --on office-src 2026-10-07-third-trip.bale-bundle`.
5. **Title first.** `office open` checks the title before size, lane and
   source. Through `start new`, a folder already on the desk is offered as
   the one to start (`[yes]`). A plain `office open` asks for another
   title at once. A title given as a flag still refuses, as before.
6. **Riders at start (item 3).**
   - The flag twins are `--carry N` (repeatable) and `--carry none`. I
     avoided `--rider`/`--no-riders` because `--no-rides` (ride-alongs)
     already exists and the two would be easy to confuse.
   - On a terminal each matching rider is offered, default carry. Piped,
     none is carried and each match is named with its flag.
   - A named carry that fails stops the start before anything is packed.
     A carry you accepted at the offer only warns if it fails.
   - **A format extension**: a rides glob may name its project first, as
     a lane does (`office-src: bin/`). Then only a pack on that project
     carries it, and `office riders --forecast ... --project NAME` reads
     it so. Without the prefix, `bin/` would match any project's pack.
     `rider add --rides "office-src: bin/"` accepts it.
7. **Land (items 4 and 6).** The founding folder closes automatically,
   not on an offer, as the sitting leaned, using `office close`'s own code
   (History: `done: office land: the founding landed at SID, with the
   profile complete`). It closes after the ratification question. A
   profile still incomplete leaves the folder open, and land says so.
   Watches check runs through a new `office_watches.py check
   --fired-only`. It prints only fired lines, and nothing when there's no
   register. It never records and never fails a landing. Both sit before
   the after-land summary, so an install's outcome stays the last thing
   on screen.
8. **Paragraphs.** The prompt says `[several lines welcome; a blank line
   ends the answer, and return at once skips]`. Continuation lines keep
   their leading spaces.
9. **The runner.**
   - The serial group is named by a class attribute, `serial_group =
     "terminal"`, on 15 classes (12 existing, 3 new). A test holds the
     marks equal to an AST scan for classes that drive a pty.
   - It runs as one lane beside the modules, started first, not after
     them. On this container it was still the long pole.
   - Four jobs by default (`--jobs`, `OFFICE_TEST_JOBS`).
   - The plan is checked against discover's count before anything runs.
   - Module names select a subset, with each module's share of the serial
     group.
   - `--serial` is exactly `python3 -m unittest discover -s tests -v`.
10. **Fixtures**: only what the office newly calls went into
    `bale-0.4.47/`. Nothing moved, so the fake bales still replay 0.4.45
    for everything else. Replaying both versions would only double the
    captures.
11. **Tests changed beyond naming the serial group**, because the
    behaviour they pin changed:
    - `test_land.py`: the fake answers `open --check` from the 0.4.47
      captures, `calls_of` tells a check from an open, and a missing
      bundle is now refused before the survey.
    - `test_front_door.py`: a bare bundle's overlap is now the check's
      words.
    - `test_founding_door.py`: the terminal init types each answer as a
      paragraph, and a landed founding closes its folder, so the Next
      line no longer names it.

## Look closely on review

- `cmd_start` in `bin/office` is reordered for `new`, and the where
  question moved into `ask_where`. `offer_riders` and `start_retry_hint`
  read `cmd_start`'s locals through bash's dynamic scope; both say so in
  their comments.
- A pack forecasting a whole repo touches every bare-glob rider, so on a
  terminal every queued bare-glob rider is offered with default carry.
  The project prefix is the remedy; the front sheet names this.
- On this two-core container the serial lane took about 620 of the run's
  ~1000 seconds. On your machine the modules should finish well inside
  the serial lane, so the lane sets the time. I can't measure that from
  here (Proposals).

## Slips for bale-src

1. `bale unlock --help` still says it "performs no git operations",
   while its sweep commits the telemetry record. Stands on 0.4.47.
2. **No after-land hook on bale's side** — maybe answered already. `bale
   apply --help` (unchanged since 0.4.45) mentions "the post-apply hook
   confirmation", and `bale config hooks` lists project-layer hooks. So
   bale may already have the post-apply hook this slip asked for. I can't
   see from here whether a project can declare one and whether it runs on
   a hand `bale apply`. Not struck; a question for bale-src.
3. The `[bale SID]` commit subject is a convention, not a contract.
   Unchanged on 0.4.47; stands.
4. `stats --since` takes a day, not an instant. 0.4.47's help still says
   `YYYY-MM-DD`; stands.
5. New: `bale open --check` has no `--json`. The office reads the path
   bale found from the report's first line (a declared marker). A JSON
   line (outcome, path, gates, forecast) would make it data.
6. New, a question: on 0.4.47, `stats --json --work-class meta` in
   office-src reports no class, though it holds meta records (0.4.45:
   `meta`, 1 session). Intended?

The search-paths slip already in the box is partly met, not answered:
`open --check` lists the directories it searched, but only when it
refuses.

## Paths outside the forecast

None. The forecast is the whole repo.

## The suite

- **New:** `tests/run.sh` and `tests/runner.py`; `tests/test_third_trip.py`,
  29 tests (6 in the serial group). They cover:
  - the runner;
  - the 0.4.47 captures and the `open_check` surface;
  - start's check, the retry line through a real pty, and the title
    check;
  - riders at start, piped and on a terminal;
  - land's watches check and the founding folder;
  - the install behind its source, through a real `install.sh`;
  - a paragraph answer.
- **Changed:** the serial-group marks in eight modules, and the three
  test files in decision 11.
- **Runs, on this two-core container:**
  - **Before any change** (only the serial marks): 476 tests passed, side
    by side, in 866 s.
  - **First full run with the work**: 505 tests, two failures, both
    fixed. One was a comment in the consumption manifest naming the
    development record's directory, which the text rule forbids; the
    other was my own assertion's wording.
  - **This response's `validation.sh` in a staged copy**: it ran every
    test (505, all passing), but the run reported FAILED. The runner
    passed a relative `--logs` to jobs that run in `tests/`, so no job
    could write its result file. The runner said "broken" rather than
    passing silently, which is the point. The fix makes the path
    absolute, with a test that gives a relative one from another
    directory.
  - **The final run**, after the fix and the last help-text edits: this
    response's `validation.sh` in a fresh staged copy of the packed tree
    with the response applied. Every check passed (15 `[PASS]`), all
    505 tests passed side by side in 973 s, the one claim agrees, and
    nothing was written outside `.validation-logs/`. On this two-core
    container that is about 16 minutes; the founding door's notes put
    the one-process run at 17 to 23 minutes on containers like this one.
    I didn't time `--serial` here, so the real gain is yours to see on
    your machine.
  - **On the unmodified tree, with the suite skipped**: every
    session-specific assertion failed, as it should.
- The pty tests didn't flake here.

## Proposals

### Split the serial lane, if it is the long pole on your machine

- **What:** if a run on your machine shows the serial lane finishing well
  after the modules, split the serial group into two lanes by module. The
  wizards and terminal starts would go in one, the tour and land's
  terminal classes in the other. Each lane stays serial inside.
- **Why:** here the serial lane was ~620 s of a ~1000 s run. The modules
  share nothing, and the pty classes are serial only because one timing
  test flaked once; two lanes would still keep each pty test away from
  the others in its lane.
- **Scope hints:** `tests/runner.py` (`plan`, a second group name), and
  the marks. Only after a timing from your machine says it's worth it.

### Name a rider's project when the office scopes several

- **What:** have `office rider add` ask for the project, defaulting to
  the one a lane names, so new riders carry `project: glob`.
- **Why:** a bare glob matches any project's pack. This session made the
  prefix possible but left it optional, so existing riders keep working.
- **Scope hints:** `cmd_rider_add` in `bin/office`, `normalize_rides` in
  `lib/office_drafting.py`.
