# Notes: the suite's clock (office-src 0.17.1)

Session 2026-10-12-suite-clock-001. What landed: `tests/run.sh --fast`,
a fast tier defined once in `tests/fast-tier.toml` and held to the suite
and to `bin/office`'s dispatcher before it runs; `tests/run.sh --detach`,
the whole suite in the background with a one-line verdict file outside
the repo; a HOME and TMPDIR of its own for every job the runner starts;
per-test times in every run; and the rule that no test reads the machine,
with `tests/test_suite_clock.py` as its self-check. No verb changed; no
test was deleted. 0.17.1, not 0.18.0: nothing in `bin/office`, `lib/` or
`share/` moved, and nothing in an office does (the sitting's guess holds).

## The numbers, measured here

All in this sandbox: two cores, Python 3.13, 4 jobs at a time, the
request's tree (which leaves out `claude/context/sittings/`, so the two
development-record pins fail here and only here; see below).

| run | tests | wall clock | result |
|---|---|---|---|
| the whole suite before (the request's tree, the old runner) | 657 | 1,112 s (18.5 min) | 655 pass; the 2 sittings pins fail |
| the whole suite after (`validation.sh --slow`'s second half) | 679 | 1,061 s (17.7 min) | 677 pass; the 2 sittings pins fail |
| the fast tier alone (`tests/run.sh --fast`) | 280 | 54.9 s | 278 pass; the 2 sittings pins fail |
| this session's validation.sh: the tier plus 11 names for what I changed | 291 | 90.9 s and 91.4 s (two runs) | 289 pass; the 2 sittings pins fail |
| the whole suite detached (`tests/run.sh --detach`, a git checkout of the result) | 679 | 1,082 s, at nice 10, beside my other work | its one line: `FAILED 2026-10-12T19:50:22Z: 2 of 679 tests failed, in 1082s, at 69170260225b; read .../run.log`, the 2 being the sittings pins; the copy removed, the child gone |

The suite's count in tests: 657 before, as the last worker reported and
as the runner's own plan counts it; 679 after (22 new, all in
`tests/test_suite_clock.py`). The tier is 280 of the 679; this session's
validation adds 11 names (291 tests).

On the occupant's machine. A read-only probe cannot time the suite, so
this is reasoning, flagged: the best office-src apply of the last six
took 7.5 minutes from "running validation.sh" to the relay copied, and
that held the whole suite plus bale's prompts; here the whole suite alone
takes about 18. So that machine is at least 2.5 times this sandbox, and the
tier with this session's additions should take about 35 to 40 seconds
there. validation.sh prints the number and fails past 120, and so does
`--fast` itself; if the first apply shows it near the line, the tier
needs trimming, not the budget raising.

The sittings pins. `test_office.TestDevelopmentRecord` checks the
planner's pages byte for byte; the request did not carry them (the brief
says why), so here two of its three tests fail, before and after alike.
I kept the class in the tier on purpose: it costs nothing and guards the
record. Where the pages are, it passes.

## Where the minutes go

Each test's time, from the whole run here (times.tsv, now written beside
every run's logs). The numbers are under contention (4 jobs on 2 cores),
so each is about twice a quiet test's; the shape is what matters.

- 248 of the 678 tests then (37%) take under half a second each, 10
  seconds together: units, catalogs, text rules. They cost nothing.
- The other 430 take the rest, 4,079 seconds: median 6.7 s, the top
  tenth over 19 s. These are the tests that build an office in a scratch
  HOME and run `office` and git (and the fake bale, the fake ssh) again
  and again. The sitting's guess is right: the minutes are process
  spawns, `bin/office` and git, test after test, not one slow test.
- One exception was pure Python: `test_third_trip`'s plan test parsed
  every test file once per test in the suite, 113 seconds for one test,
  the slowest in the suite. It now reads them once (about a second) and
  asserts the same.
- By module (one job each, seconds of test time, tests): the serial
  terminal lane 549 (74; about 7.4 s a test, the pty tests' waits),
  test_land 437 (38), test_return_trip 354 (32), test_third_trip 348 (23,
  of which 113 was the plan test), test_audience_line 340 (32),
  test_desk_verbs 330 (49), test_office 239 (111), test_front_door 221
  (28), test_watches_digest 202 (47), test_out_trip_to_host 199 (37),
  test_start 179 (23), test_drafting_table 173 (22), test_second_trip 171
  (26), test_founding_door 167 (21), test_project_on_host 118 (38),
  test_read_side 56 (44), test_filed_append_only 0.4 (12).
- The wall clock of a whole run is bounded below by its longest lane, the
  serial terminal lane (9 to 10 minutes here), whatever the job count: a
  proposal below.

## The fast tier: what it holds and why

`tests/fast-tier.toml`, 280 tests:

- One entry point per verb `bin/office`'s `main()` dispatches, and the
  walk-in (34 entries, 31 distinct tests): for each, the cheapest test
  that types the verb and does its main work, a happy path where one
  costs seconds (start packs and fills the tray, land lands and runs the
  after-land actions, deliver crosses to the audience), a refusal only
  where nothing cheaper exists (found). Shared where one test runs
  several (close and reopen; agenda, blueprint and digest). I spread them
  across modules so no one job carries most of them.
- Every test that took under half a second in the whole run, by class
  where the whole class is that cheap: 219 more tests, about ten
  seconds together.
- `test_suite_clock` whole, `test_third_trip.TestTheRunner` (the
  runner's own tests, cheap now), `test_office.TestDevelopmentRecord`:
  30 tests.
- 31 + 219 + 30 = 280.

The verbs, not `share/verbs.toml`'s catalog: the catalog lists session
kinds (founding, work, build) that are not commands, and leaves out
help, version and the walk-in. The dispatcher is what a person types.

How it cannot drift. `tests/run.sh --fast` (and `--fast --plan`) loads
the whole suite's plan and stops with exit 2, before running anything,
when a name in the file is no test, class or module of the suite, when a
verb the dispatcher knows has no entry point, or when the file names a
verb the dispatcher does not have. Its plan is then held to `unittest
discover`'s count of the same ids, the way the whole plan already was.
`test_suite_clock.TestTheFastTier` checks the same in every run and
also that each entry-point test's own source calls the command with its
verb (through `run`, `run_office`, an Office's `run`, a helper named for
the verb, or an argv). That last check is static: a test that names the
verb in a call and never reaches it would pass. A run-time check is in
`deferred`.

How a session adds what it touched: on its own command line, never in
the file: `tests/run.sh --fast test_land.TestLandWhichSession
test_x.TestY.test_z` (a module, a class or a test).

## Isolation: the rule, the self-check, and what it found

- Env (tests/test_office.py) now gives each test its own TMPDIR
  (`self.e.tmpdir`) and names its downloads (`self.e.downloads`, inside
  its HOME; the Windows homes scan stays off), beside the HOME and
  XDG_CONFIG_HOME it already gave. `Env.this_process()` lends the Env's
  whole environment (git identity included) and temp directory to a
  helper the test calls in-process.
- The runner gives every job, and `--serial`, its own HOME, TMPDIR, XDG
  directories and empty git config under one scratch directory it
  removes after, and drops the caller's `OFFICE_` and `XDG_` settings.
  It deliberately gives no git identity: a test that commits in-process
  without its Env then fails here, in the sandbox, instead of borrowing
  the occupant's. It found one: `test_land`'s record test, whose
  in-process `take_record_out` committed under the machine's identity.
  It now runs under `this_process()`.
- `test_suite_clock.TestNoTestReadsTheMachine` fails the suite on any
  test file naming the machine's temporary directory (as an absolute
  path), `expanduser`, `Path.home(`, `$HOME`, `gettempdir(` or HOME read
  from the environment, outside `class Env`. Its ALLOWED list, each with
  its reason, and an allowance that stops matching fails too:
  `test_land`'s `/tmp/office-probe.*` strings (paths a probe's bale
  printed, kept verbatim in the fixtures; the fake bale swaps them out of
  the text it replays and nothing reads them); `test_out_trip_to_host`'s
  fake upgrade.sh (`$HOME/.local/bin`, `${TMPDIR:-/tmp}`: run by the fake
  ssh with the fake host's HOME and TMPDIR); `test_return_trip`'s
  after-land action `echo "$HOME"` (run on the fake host, to prove it got
  the host's HOME) and its `"$HOME"` shell-text expectations (text,
  never expanded). Its own patterns bracket a letter (`/t[m]p`), as
  share/letterhead.toml does, so the file obeys itself.

The brief's list, judged:

- test_audience_line lines 554 and 839: real reads of the machine's /tmp
  (and racy beside another deliver in a parallel job). Now they look in
  their Env's TMPDIR, which deliver's temporary files now use; same
  assertion, nothing left behind.
- line 768 `/tmp/audience.git`: a string, never read; changed to a path
  under the Env anyway, since the rule cannot tell, and the assertion (a
  local path has no review URL) is unchanged.
- test_land's `/tmp/office-probe.*`: fixture text, allowed with its
  reason.
- test_out_trip_to_host line 437: script text for the fake host, allowed.
- test_read_side line 464: `expanduser` against the real HOME; now
  `~/x` is checked to expand to the Env's HOME under `this_process()`.
- test_return_trip's downloads tests: the candidates test was already
  steered (home and env passed); the downloads-key test's
  `~/Downloads` default was expanded against the real HOME. The class now
  runs under an Env and checks the default against the Env's HOME.
- Two more the brief did not list: test_start's declaration tests named
  `/tmp` as a ride path (a contradiction check and a several-lines check;
  not reads, but the rule cannot tell): now a path under the Env.
- Two the isolation found, not the scan: the tour's terminal tests made
  their own `tmpdir` under the Env with the name Env now uses, so they
  now take Env's (same emptiness checks); and the scratch directory I
  first named after each job leaked the job's name into paths, which
  `test_audience_line`'s push-guard test caught (it asserts "audience" is
  absent from git's stderr, which printed a path). Job directories are
  `j1`, `j2`... now.

## The detached run

`tests/run.sh --detach` copies the tree (no .git, .bale or caches) into
`~/.local/state/office-src/suite/<UTC stamp>-<pid>/tree` (or under
`$XDG_STATE_HOME`), writes `verdict` as `RUNNING since ...`, starts the
copy's runner with `--detached-child` in a new session, stdin from
/dev/null and its output to `run.log` beside the verdict, and prints one
line naming both, returning at once. The child restores SIGINT (an
after-land action started from a background job would otherwise make the
interrupt test fail for that reason), runs at nice 10, runs the whole
suite with its logs in `logs/`, replaces `verdict` with one line (`OK`,
`FAILED` with the count and the log to read, or `BROKEN`), removes the
copy and keeps the ten newest runs. `latest` points at the newest.

The line for home-office's after-land actions, to run once in the
office, as the occupant (the flag replaces the list, so it names
`./install.sh` too; that is the action the help's own example gives
office-src, and I could not read home-office's floor plan, so check
`office projects office-src` first and, if it lists anything else, name
each in this line, in order):

    office projects set office-src --after-land ./install.sh --after-land "tests/run.sh --detach"

Order: the install first, the suite second. A failed install stops the
rest and says so, which is the louder problem; the suite tests the repo,
not the install. On a terminal, `set` asks whether to keep where the
project is and its other declarations; a plain return keeps each.

## Files touched outside tests/, the front sheet, RELEASES.md and VERSION

- README.md: its Tests section describes `--fast`, `--detach`, the tier
  file, the budget and the per-job isolation, and the foreground advice
  now names `--detach`. A user-facing doc edited along the way; nothing
  else in it moved. `test_suite_clock.TestTheRecord` reads it.

All 16 paths are inside the forecast (the request's `resolved_scope` is
the whole tree); no departures.

## For review

- `tests/runner.py` is the bulk. The whole-suite path is unchanged in
  shape (plan, discover check, jobs, summary); new are `isolated_env`,
  `TimedResult` and `times.tsv`, the tier functions (`load_tier`,
  `dispatcher_verbs`, `tier_problems`, `tier_ids`), `fast()`, and the
  detached pair (`detach`, `detached_child`). The summary's lines and the
  exit codes are as before; the start line now says where each job's
  HOME and TMPDIR are.
- `dispatcher_verbs` reads `bin/office`'s `main()` case arms by pattern.
  If `main()` changes shape, `--fast` stops with "cannot be read" rather
  than running an empty tier.
- The tier's entry points are mine to defend: each is listed in the file
  with its verb. Where I could have picked a cheaper refusal I took the
  happy path when it cost a few seconds more.
- `this_process()` patches os.environ with the Env's whole env (PATH
  included, as the test has it): a helper called in-process sees what a
  command run through the Env sees.

## Proposals

- **What:** the walk-in reports the latest detached verdict for office-src
  when it is not OK (`FAILED ...` or a `RUNNING` older than an hour),
  one line, read from `${XDG_STATE_HOME:-~/.local/state}/office-src/suite/latest/verdict`.
  **Why:** the detached run's verdict is only as good as someone reading
  it, and the walk-in is where the occupant already looks; out of this
  session's scope by the brief. **Scope hints:** `bin/office` walk_in,
  a helper to read one line; only for the project whose repo is
  office-src's own source (the walk-in knows it: it says when the
  install is behind the source).
- **What:** order the runner's jobs by the last run's `times.tsv` rather
  than by source size. **Why:** the longest-first schedule is only as good
  as its guess; source size put test_office's cheap units ahead of
  test_land's slow lands. A recorded time is a better guess, and the
  file now exists after every run. **Scope hints:** `tests/runner.py`
  `order()`; read the previous run's file when `--logs` names a kept
  directory, or keep a copy under the state directory.
- **What:** look at the serial terminal lane's waits. **Why:** 74 tests at
  about 7.4 s each, 9 to 10 minutes, and it bounds every whole run's wall
  clock however many cores there are; the pty helpers' read loops and
  timeouts are the likely place. **Scope hints:** the terminal helpers in
  test_start (`on_a_terminal`) and test_front_door, only after measuring.
- **What:** take `test_land`'s probe paths from each fixture's own `cwd`
  rather than naming them. **Why:** it would retire the largest allowance
  in the rule's list. **Scope hints:** the fake land bale's `swap` calls
  in test_land.py.
- **What, for bale-src's own sitting:** `bale apply` has no way to run
  `validation.sh --slow`. **Why:** TARBALL.md 7.6 tells a session to put
  slow checks behind `--slow`, and nothing in bale's apply or retry ever
  passes it (BALE_HELP.md: `--verbose` streams output, nothing forwards an
  argument), so a slow check runs only when the operator runs the script
  by hand in staging. With `--detach` after land, office-src no longer
  needs it; a project without such a run does. This sits beside the
  slips already on that list (validation's duration stamped; a private
  HOME and TMPDIR for validation in the apply sandbox, which this
  session's per-job isolation does for office-src's suite alone).

## Walkthrough

### What changed

- `tests/run.sh --fast` runs the fast tier: 280 of the suite's 679 tests,
  named in `tests/fast-tier.toml`. It prints its wall time and fails past
  120 seconds. A session names what it touched after `--fast`.
- `tests/run.sh --detach` runs the whole suite in the background from a
  copy of the tree and returns at once with one line naming its verdict
  file under `~/.local/state/office-src/suite/`.
- Every job the runner starts gets a HOME and TMPDIR of its own, and every
  run writes each test's time to `times.tsv` beside its logs.
- `tests/test_suite_clock.py` (22 tests) fails the suite on any test file
  that reaches for the machine's own temporary directory or home outside
  Env, and checks the tier, the runner's isolation, the budget and the
  detached run.
- Env gives each test a TMPDIR and downloads of its own and can lend its
  environment to an in-process call; eight tests that leaned on the
  machine now use it. One slow test (the runner's plan test) went from
  113 seconds to about one.
- The front sheet has a section on the suite's clock for the next worker;
  README's Tests section, RELEASES.md and VERSION (0.17.1) follow.

### Why

The apply was the most expensive step of every office-src session: 7.5 to
98.6 minutes over the last six landings against bale's two minutes, and
two of those six held on tests that read the occupant's machine (a /tmp
log gone after a WSL restart, a downloads scan of real directories). The
tier brings validation under two minutes; the detached run keeps the
whole suite running after every landing without holding the terminal;
the isolation and its self-check make the machine-reading class of HOLD
fail in the worker's sandbox first.

### How to explain each piece

- The tier: one file says which tests run at apply. It has a test for
  every command the tool knows, plus the near-free checks. The runner
  refuses to run a tier that names a missing test or misses a command,
  so it cannot quietly rot.
- The budget: the two minutes are written in the file and checked by the
  runner, so every later session's validation gets the check by calling
  `--fast`.
- The detached run: after a landing the whole suite runs on a copy, in the
  background, at low priority, and leaves a one-line verdict to read.
- The isolation: every test, and every batch of tests, gets its own home
  and temporary directory; a test file that names the real ones fails a
  test.

### Questions a reviewer will ask

- *Does validation still run every test?* No: the tier, 280 of 679, plus
  what the session touched. Every test still runs after every landing,
  detached, and in the worker's sandbox before it ships (notes.md
  reports it); `--slow` runs it from validation by hand.
- *What stops the tier going stale?* `--fast` checks every name against
  the suite and every command against the dispatcher before running, and
  stops with exit 2 when either is off; a test in the suite checks the
  same.
- *What if the tier creeps past two minutes?* `--fast` fails and says so,
  pointing at `times.tsv`, the per-test times of that very run.
- *Will the background run slow my machine?* It runs at a lower priority
  (nice 10), four jobs at a time, for as long as the whole suite takes
  (about 7 minutes or less on the occupant's machine, by the reasoning
  above).
- *What if the machine sleeps or restarts mid-run?* The verdict stays
  `RUNNING since ...`, with the time it started; the next landing starts a
  new run and `latest` moves to it.
- *Why is there an allow list in the rule?* A few lines are text a fake
  host runs under its own HOME, or paths recorded in fixtures; each
  allowance says why, and one that stops matching fails the test.

### A hand test

1. After the landing, in the office-src checkout: `tests/run.sh --fast`.
   Read its last line: `[run] the fast tier took N s of wall clock, 280 of
   the suite's 679 tests; its budget is 120s`. N should be well under 120
   (about 30 to 40 by my estimate).
2. `tests/run.sh --detach`. It should print one line and give the prompt
   back at once. Then `cat ~/.local/state/office-src/suite/latest/verdict`
   says `RUNNING since ...`; `ps -o pid,ni,args -p PID` (the pid from the
   line) shows it at nice 10.
3. About seven minutes later, the same `cat` says `OK ...: 679 tests
   passed in N s, at <commit>`, and `run.log` beside it ends with the
   runner's summary. The copy (`tree/` beside it) is gone.
4. Add the after-land line (above), and on the next landing of office-src
   watch `office land` end with `ran (exit 0): tests/run.sh --detach`
   right away rather than minutes later.

## Delivery

- to: nobody: office-src has no audience

### Commit

Give the suite a two-minute fast tier and a detached full run

Validation now runs a fast tier, named once in tests/fast-tier.toml: a
test for every command the dispatcher knows, plus the checks that cost
under half a second. The runner refuses a tier that names a missing test
or misses a command, prints the tier's wall time and fails past two
minutes. tests/run.sh --detach runs the whole suite in the background
from a copy of the tree and leaves a one-line verdict under
~/.local/state/office-src/suite/; it is meant as an after-land action.

Every job the runner starts gets its own HOME and TMPDIR, every run
records each test's time, and a new test fails the suite on any test file
that reaches for the machine's own home or temporary directory outside
Env. Eight tests that did now use their Env, and the runner's plan test
stops re-reading every test file for each test.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.
