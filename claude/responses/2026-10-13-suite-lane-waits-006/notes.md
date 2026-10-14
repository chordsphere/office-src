# Notes: 2026-10-13-suite-lane-waits-006 (office-src 0.21.0)

The suite waits less, and no test checks less. Three changes do it:

- The runner compiles the office's modules and the tests once per run,
  into a bytecode cache it hands to every job. `bin/office` runs its
  Python modules through a small launcher, `pylib`, so even the module it
  starts with comes from that cache.
- The serial lane holds only the 52 tests that drive a terminal. It held
  85, and 33 of them drove none.
- Jobs start longest first when the runner knows the last run's times.
  Without them it runs as it does today.

The rider is fixed too. `office start` now writes the digest before a
sitting it sends out from a bundle named by a bare name. When it cannot
read a bundle's pack line at all, it says so in one line. VERSION is
0.21.0. The numbers are below, above the two pages.

The pre-flight check said the goal fits, with room to spare. I sent no
probe and no light block: the tree and the brief answered everything. One
changed path is outside the forecast, the front sheet (below).

## What the ledger said, against the tree and my runs

- **85 tests in the serial lane: confirmed.** The runner's plan holds
  exactly 85. But 33 of them drive no terminal. They sat in the lane
  only because their class held one test that does.
- **332 tests in the fast tier at 0.20.1: confirmed.** My first run
  counted 332, in 95.1 s, and a second took 98.3 s.
- **About 7.4 s a test in the lane:** 11.2 s here (955.7 s for 85 tests).
  This sandbox is slower than your machine, by about 1.35 times on the
  fast tier (95.1 s here, against 70.9 s there at 0.18.0 with fewer tests).
- **"The floor of every whole run": true on your machine, not quite
  here.** With two cores, the baseline's lane ended at 956 s and the
  whole run at 1712 s. The four jobs at a time share two cores, so total
  CPU is the floor here. On a machine with four or more cores, the lane
  is the floor, as the workers said. Both changes below cut both.

## What the waiting was

It was work, not waiting. I timed terminal tests alone on a quiet machine.
Wall clock matched CPU time within a few percent: the return trip's
terminal test took 26.5 s of wall clock and 26.3 s of CPU, the tour's
play test 15.0 and 14.9. Nothing in `bin/office` or `lib/` sleeps, and
the pty drivers return the moment the child's output ends. The one
deliberate wait is the imitated-WSL test's three seconds. That wait is
how long the test watches for `explorer.exe` to run. Shortening it would
shorten what the test checks, so I left it.

The work itself was mostly Python compiling the office's own code again
on every call. `bin/office` runs its helpers with `python3 -B`, so nothing
is ever written beside an install, and nothing compiled was ever read
back either. A plain `office_helper` call took about 104 ms; 90 ms of it
was compiling `office_helper.py` (3,249 lines) and `office_host.py`, then
importing. An `office_bale` call compiled six modules. One `office relay`
test made 68 such calls. With the cache, a helper call takes about 62 ms,
and most of what is left is the standard library's own imports.

## Decisions to ratify

1. **The bytecode cache, and `pylib` in `bin/office`.**
   - The runner compiles `lib/*.py` and `tests/*.py` into
     `<scratch>/pycache` at the start of every run (`seed_bytecode`,
     about 0.6 s). It gives every job `PYTHONPYCACHEPREFIX` pointing
     there. Each `Env` passes it on to the commands its test runs, but
     only under the runner.
   - A cache prefix is the only place Python looks for compiled code
     once one is set, standard library included. So the runner also
     links in the interpreter's own compiled standard library, and the
     modules it loaded at startup (site's). Without that, every
     `import json` would compile from source, and the cache would slow
     the suite down.
   - `bin/office`'s eleven helper calls (`helper`, `reader`, `door` and
     the rest, and the letterhead check) now go through `pylib`. It runs
     the module as its script would: `__name__` is `__main__`,
     `sys.argv[0]` is its path, `lib/` is first on `sys.path`, and with
     `-P` the current directory is not on it. But it loads the file as a
     module, so its compiled code comes from the cache. A script run by
     path is always compiled from source. A test pins that behaviour,
     including a decoy `json.py` in the current directory.
   - Nothing changes in your everyday use. There is no cache, `-B` still
     writes nothing, and the modules compile as they always did.
   - What I did not do: drop `-B`, which would write `__pycache__/` into
     the install and into bale's staging; or make the helpers import
     lazily, which would restructure production code for a test
     concern. That second one is a proposal below.
   - A tree with no `lib/` gets no cache. The runner's own tests run it
     on tiny repos with no `lib/`, where a cache saves nothing and costs
     about half a second a run.
2. **The lane holds only tests that drive a terminal.** Seven classes
   held both kinds. I split each in place, in three parts:
   - `XCase` holds the setUp and the helpers, moved verbatim.
   - `X` keeps its name and the tests that drive no terminal, now without
     `serial_group`.
   - `XOnATerminal` holds the terminal tests, marked serial.

   So 33 test ids did not change, and 9 did (the terminal ones, listed
   below). The existing rule, "the serial group is exactly the classes
   that drive a terminal," holds unchanged at class level. A new test
   holds the lane to tests that drive a terminal at method level, so the
   lane cannot fill up again by accident. I chose a split over
   per-method marking because per-method marking would have changed
   that existing rule's assertion.
3. **The last run's times live where they already were.** I made no new
   file. The runner reads `logs/times.tsv` from the newest finished
   detached run (verdict OK or FAILED) under the state directory,
   `~/.local/state/office-src/suite/`. The `--detach` after every
   landing already writes that file.
   - Each job weighs the sum of its tests' times. A test timed in
     another job counts at that job's time; this covers the tests that
     just moved out of the lane. A test never timed counts at the median.
   - The serial lane is weighed like any job, so it starts first only
     when it is the longest.
   - The run prints one line saying which order it took, and `--plan`
     lists the jobs in that order.
   - With no finished run (a first run, a fresh HOME, bale's sandbox)
     the order is exactly as before.
   - A job cannot see the times, since each job has a state directory
     of its own. The suite's rule against reading the machine
     (`tests/test_suite_clock.py`) is unchanged and passes. A new test
     shows that a job's state directory holds no run even when the
     caller's does.
4. **The rider: why the digest was not written.** In `start()`
   (lib/office_bale.py), a sitting is `where == "office" and forecast ==
   []`. For a bundle, the forecast comes from the bundle's stored pack
   line, which the office reads only when the bundle is a file it can
   open. A bundle named by a bare name is bale's to find, through its
   search and the downloads. So the office set the forecast to None,
   never saw a sitting, and skipped the digest. It printed nothing about
   the digest, only that it could not read the bundle's forecast. Every
   other way the digest can be left (the drafting table held, bale's
   registry unreadable, the digest failing) prints a warning. So this is
   the one silent path, and the likely cause on 2026-10-13. I did not
   probe for it: the code shows it, and the fix covers the case either
   way. The hand test shows which line your start prints.
   - The fix: bale's own rehearsal (`bale open --check`, which office
     start already runs first) says where it found the bundle. Start now
     reads the pack line there, but only to tell whether the bundle is a
     sitting. Every other check reads the bundle where it was named, as
     before, so the second-desk overlap logic of 0.18.0 is untouched.
     bale is still given the name it was given.
   - When even that file's pack line does not read, start says one line
     and leaves the page: "the office cannot read the pack line of the
     bundle NAME (why), so it cannot tell whether it sends out a sitting:
     it leaves drafting-table/digest.md as it was, written TIME; office
     digest writes it". I chose saying over writing, because writing the
     digest for an office session that is not a sitting would add a
     commit nobody asked for.
5. **VERSION 0.21.0, not 0.20.2.** The runner's behaviour changes, and
   so does what `office start` prints. Additive, no migration.

## Tests moved between tiers

None. The fast tier (tests/fast-tier.toml) is unchanged. It names none of
the split classes, and no entry point's id moved.

## Tests moved between classes (and so out of, or within, the lane)

Every body is byte for byte as it was. validation.sh proves it by hashing
every test method the request carried and finding each one again.

Out of the serial lane into their module's job, same ids (33):

- test_drafting_table.TestRiders: test_add_carry_consumed_and_numbers_across_page_and_folders,
  test_refusals_name_what_to_do, test_an_orphan_is_reported_and_consuming_it_in_the_cabinet_only_adds_lines,
  test_forecast_lists_the_queued_riders_a_pack_carries
- test_front_door.TestInitProjects: test_the_flag_twin_adds_each_and_stdout_stays_the_next_line,
  test_a_project_that_does_not_check_builds_nothing, test_piped_it_asks_nothing
- test_read_side.TestProjectsVerb: test_listing_with_no_table_says_so,
  test_add_with_flags_commits_only_the_floor_plan, test_add_takes_words_too,
  test_piped_add_never_asks_and_names_the_flags, test_add_explains_what_it_does_not_know,
  test_a_missing_project_is_reported_not_dropped, test_a_name_narrows_only_a_rendering
- test_second_trip.TestWhatRides: test_piped_everything_declared_rides,
  test_leave_out_keeps_one_home_this_once, test_no_rides_and_a_name_that_rides_nowhere,
  test_a_bundle_may_leave_one_out_too
- test_second_trip.TestWhereFromTheBundle: test_the_default_is_the_place_holding_every_path,
  test_paths_no_one_place_holds_are_refused_naming_each,
  test_sent_where_its_paths_are_not_it_is_refused_before_bale
- test_start.TestSlip: test_a_slip_is_its_own_page_committed_alone,
  test_piped_text_and_no_about_is_never_asked, test_a_slip_works_unfounded_and_under_skew,
  test_the_office_stays_ascii_and_the_name_has_no_escape, test_the_same_words_twice_make_two_pages,
  test_refusals
- test_start.TestDeclarations: test_set_and_clear_keep_every_other_byte, test_refusals,
  test_a_declaration_that_does_not_read_is_reported_not_fatal,
  test_the_verb_with_flags_commits_only_the_floor_plan, test_add_takes_the_declarations_in_one_commit,
  test_piped_set_names_the_flags_it_needed

Still in the lane, new class name (9):

- test_drafting_table.TestRiders -> TestRidersOnATerminal: test_on_a_terminal_rider_add_asks_and_explains
- test_front_door.TestInitProjects -> TestInitProjectsOnATerminal: test_on_a_terminal_it_asks_until_a_plain_return,
  test_projects_add_checks_the_path_before_asking_more, test_no_projects_skips_the_question_on_a_terminal
- test_read_side.TestProjectsVerb -> TestProjectsVerbOnATerminal: test_the_wizard_asks_on_a_terminal
- test_second_trip.TestWhatRides -> TestWhatRidesOnATerminal: test_on_a_terminal_it_shows_what_rides_and_asks
- test_second_trip.TestWhereFromTheBundle -> TestWhereFromTheBundleOnATerminal:
  test_on_a_terminal_a_plain_return_opens_it_where_its_paths_are
- test_start.TestSlip -> TestSlipOnATerminal: test_on_a_terminal_it_asks_what_it_is_about
- test_start.TestDeclarations -> TestDeclarationsOnATerminal: test_the_wizard_asks_on_a_terminal

## New tests (16; the suite goes from 795 to 811)

- **test_suite_clock, 10, all in the fast tier with the rest of the module.**
  - The order jobs start in, 6 tests: with no run, as before; the newest
    finished run's times are read and RUNNING and BROKEN runs skipped;
    longest first, with the median and moved-test cases; `run.sh --plan`
    and a real run follow the order and say so; a job never sees the
    times; the README and front sheet say how.
  - The cache, 4 tests: compiled where the interpreter looks, with the
    standard library linked; read, and written by nothing that runs,
    `office help` included; every job gets the run's cache and never
    the caller's; `pylib` runs a module as its script would.
  - Their cost in the tier is about 2 s of test time.
- **test_third_trip, 1, in the fast tier:** every test in the serial lane
  drives a terminal. It fails on the request's tree, naming the 33.
- **test_land, 5, not in the tier:** TestABundledSittingOpensOnTheDigest.
  Each runs a real start, about 9 s, so validation.sh names the class on
  its own command line instead.
  - A read-only bundle given by path gets the digest. This passed before
    too; it guards the readable-bundle path, which always worked.
  - A bare name bale's search finds gets the digest, written before the
    pack. This fails on the request's tree.
  - An unreadable pack line gets the one line, with the page's
    `written_at`. This fails on the request's tree.
  - A bundle that is no sitting gets neither.
  - The units.

## Run results (worker's sandbox, two cores, 4 jobs at a time)

| run | tree | earlier times | tests | result | wall clock | CPU (user+sys) |
|---|---|---|---|---|---|---|
| fast tier | request | none | 332 | OK, twice | 95.1 s, 98.3 s | 168 s |
| fast tier | this response | none | 343 | OK, three times | 67.1 s, 68.7 s, 65.8 s | 112 s |
| fast tier | this response | this tree's last whole run | 343 | OK | 61.1 s | |
| validation.sh, staging copy (the request's tree, files/ and apply.sh) | this response | none | 348 (the tier and the rider's five) | every check PASS, the whole suite SKIP behind --slow | 79 s in all; the tier 79.2 s | |
| validation.sh | request | none | | the five session assertions that test the change FAIL, as they should; the byte-for-byte and exec-bit guards PASS on both trees, since they guard what must not change | | |
| whole suite, detached | request | none | 795 | OK; the lane's 85 tests in 955.7 s | 1712 s | |
| whole suite, detached | this response | none | 811 | OK; the lane's 52 tests in 384.3 s | 1051 s | |
| whole suite, detached | this response | the run above | 811 | OK; the lane in 369.6 s | 1009 s | |

How to read them:

- **The 60-second aim.** With no earlier times, which is what bale's
  sandbox has at apply, the tier takes 66 to 69 s here. With them it
  takes 61. The floor here is CPU: the tier's work fell from 168 to 112
  CPU-seconds, and on two cores that is 56 s even if the jobs packed
  perfectly. So in this sandbox the floor is about 56 s, and the order
  from the last run's times gets within 5 s of it. At your machine's
  ratio (about 1.35 times this sandbox), expect about 50 s at apply and
  45 after a detached run. So 60 is the right aim for your machine,
  with about 10 s of room for the next two sessions' tests. Going
  further would need the proposals below.
- **The whole suite with the last run's times** saved another 42 s
  here (1051 to 1009). The gain is small in a sandbox where the cores
  are saturated, and larger where the tail is idle cores waiting on one
  long job.
- **The baseline whole run is slightly inflated.** It shared the machine
  with about five minutes of my test runs. The lane is the cleaner
  comparison, and it shrank by 60%.
- **The whole suite's number that counts is yours:** the detached run
  after landing. Expect it well under the 923 s of 0.20.1: the lane is
  less than half what it was, and every job is cheaper.

## Paths outside the forecast

- `claude/context/front-sheet.md`. The suite's own record test
  (test_suite_clock.TestTheRecord) requires a `- VERSION (session` line
  on the front sheet, so moving VERSION to 0.21.0 requires this file.
  Its "The suite's clock" section is also where the next worker reads
  how the suite runs. I added a 0.21.0 entry and one bullet there.

## Proposals

- **What:** make `office_helper.py` import its heavy standard modules
  (tarfile, argparse, subprocess, tomllib) only where they are used.
  **Why:** with the cache, a helper call is about 62 ms, and about 45 ms
  of it is standard-library imports at startup. The office makes dozens
  of these calls per command, in everyday use too, where there is no
  cache. **Scope hints:** lib/office_helper.py and lib/office_host.py.
  Measure with `python3 -X importtime`.
- **What:** the fake bales as fixed modules taking their paths from the
  environment, rather than scripts formatted per test.
  **Why:** one relay test starts the fake about 30 times, each a fresh
  compile of a few hundred lines, which no cache can serve while each
  test writes a different script. **Scope hints:** FAKE_PACK_BALE
  (tests/test_start.py) and FAKE_LAND_BALE (tests/test_land.py).

## Handbook

### office-src

- the test runner keeps no times file of its own: it orders jobs by the newest finished detached run's logs/times.tsv under ~/.local/state/office-src/suite/
- the serial lane is for tests that drive a pseudo-terminal only; a class holding both kinds is split into X (no serial_group) and XOnATerminal
- bin/office runs lib/ modules through pylib; the test runner's bytecode cache (PYTHONPYCACHEPREFIX) is the only cache, and everyday use has none

## Walkthrough

### What changed

- **A bytecode cache per run** (tests/runner.py: `seed_bytecode`,
  `run_cache`, `isolated_env`; tests/test_office.py: `Env`). The runner
  compiles the office's modules and the tests once into its scratch
  directory, and every job, and every command a test runs, reads from it.
- **`pylib` in bin/office.** Each Python helper runs as a module, so the
  cache serves even the first one. With no cache, as in everyday use,
  nothing changes.
- **The serial lane holds only terminal tests.** Seven classes were split
  (tests/test_drafting_table.py, test_front_door.py, test_read_side.py,
  test_second_trip.py, test_start.py). The 33 tests that drive no
  terminal run beside the other jobs. A new test keeps the lane honest.
- **The longest jobs start first** (tests/runner.py: `last_times`,
  `job_weights`, `order`) when the last detached run's times are there,
  and as before when they are not. One line says which.
- **The digest before a bundled sitting** (lib/office_bale.py `start`,
  `bundle_read_only`, `digest_left_line`; bin/office
  `check_start_bundle`). A bare-named bundle is read where bale found it.
  An unreadable one gets one line instead of silence.
- **The record:** README (the Tests section, office start's digest),
  RELEASES 0.21.0, doctrine section 4, the front sheet, and VERSION.

### Why

You asked to tackle the time first. The fast tier runs inside bale's two
minutes at every apply, and the next two sessions will add tests to it.
The whole suite holds your machine for about fifteen minutes after every
landing. Both were spending most of their time compiling the same Python
over and over, and the lane was running 33 tests one at a time that never
needed to be. The digest fix closes a silent skip: a sitting went out on
a page three landings old, and nothing said so.

### How to explain each piece

- **The cache** is like keeping a translated copy of a book instead of
  translating it again every time you open it. The runner makes the copy
  at the start of a run and throws it away at the end. Your own use of
  `office` never makes one.
- **The lane** is the one queue where tests run single file, because they
  type at a pretend terminal. It was full of tests that don't, which made
  every whole run wait on them.
- **The order** is packing the biggest boxes first, so no big box is left
  for the end.
- **The digest fix:** start used to ask "is this a sitting?" by reading
  the bundle. A bundle given by bare name couldn't be read, so the answer
  was "don't know", treated as "no", silently. Now it reads the copy bale
  found, and if it still can't tell, it says so.

### Questions a reviewer will ask

- *Did any test get weaker?* No. Every test method the request carried is
  still there, byte for byte (validation.sh hashes all 795). 33 changed
  class membership only, 9 changed class name only, and 16 are new.
- *Does anything change for me day to day?* `office` behaves the same.
  `office start` now writes the digest before a sitting from a bare-named
  bundle, and prints one line in the rare case it can't tell.
- *Where are the "last run's times" kept? Can a test read them?* In the
  newest finished detached run's directory, under
  `~/.local/state/office-src/suite/`, where they already were. No test can
  read them: every job gets a state directory of its own.
- *What if there are no times, as in bale's sandbox?* The order is exactly
  as before, and the run says so.
- *Why not 60 s in the worker's sandbox?* It is a two-core box running flat
  out. The tier there is 66 to 69 s with no history and 61 s with it. On
  your machine expect around 50 s.

### A hand test

1. In ~/office-src, after this lands, run `./install.sh`. Then run
   `tests/run.sh --fast` and read its last line: `[run] the fast tier took
   N s of wall clock, 343 of the suite's 811 tests; its budget is 120s`.
   Expect N at or under 60. A line near the top says "no earlier run's
   times here" or "jobs start longest first".
2. Let `office land`'s after-land action start the detached suite (or run
   `tests/run.sh --detach`). When it ends, run
   `cat ~/.local/state/office-src/suite/latest/verdict`. It should read
   `OK <time>: 811 tests passed in <N>s, ...`, with N well under 923.
   Walking in shows no `Suite:` line.
3. The next sitting from a bundle: give the bundle by bare name, as you
   would from the downloads. Start prints `wrote the digest for the
   sitting (drafting-table/digest.md)`, and `git log -4 --format=%s` in
   the office shows `office start: digest` below (older than) the
   `office sessions: ...` line. If instead
   it prints a line beginning "the office cannot read the pack line of
   the bundle", the bundle's pack line is one the office does not read.
   Tell the next session which bundle it was.

## Delivery

- to: nobody: office-src has no audience

### Commit

Cut the test suite's waiting time and write the digest before every sitting

The suite spent most of its time compiling the office's Python again on
every helper call, since the command runs it with -B and never reads
compiled code back. The runner now compiles lib/ and tests/ once per run
into a bytecode cache in its scratch directory and hands it to every job,
and the command runs its Python modules as modules, so the cache serves
even the first. In everyday use there is no cache and nothing changes.

The serial lane, the one job whose tests run one after another, now holds
only the 52 tests that drive a terminal. Seven classes held both kinds;
each is split, the 33 other tests beside the other jobs, every test body
as it was. When the last detached run's times are there, the runner
starts the longest jobs first; without them it runs as before, and says
which.

office start skipped the digest before a sitting sent out from a bundle
named by a bare name, without a word, since it could not read the
bundle's pack line. It now reads it where bale's rehearsal found the
bundle, and when it cannot read a pack line at all it says so in one
line.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.
