# Notes: 2026-10-22-suite-time-002 (office-src 0.27.0)

The whole suite in my sandbox went from 1,146 seconds to 822, and the
fast tier from 66.2 seconds to 59.6. That is a cut of 28 percent. The
suite had 906 tests then and has 914 now: none dropped, none merged,
eight added. Three whole runs as the changes came together took 828,
788 and 822 seconds. The last ran on the shipped code; after it only
the release notes' numbers were filled in, and the record tests that
read those pages ran again (Run results).

The brief's aim was 928 to 700 seconds in session 4's sandbox, a cut of
25 percent. My sandbox is slower than session 4's: the same 0.26.0 tree
took 1,146 seconds here, not 928. So I did not reach 700 seconds here.
The same cut on session 4's sandbox would read about 666 seconds. Where
the rest of the time goes, and what would reach further, is the section
after the run results.

Nothing the occupant uses changes. The survey reads the PATH and
`/.dockerenv` exactly as before unless a new variable is set, and only
the suite sets it.

The pre-flight check said it fits. No probe and no light block: the
tree and the brief answered everything. Every changed path is inside
the forecast.

## What I measured first

At the shipped tree (0.26.0), in this sandbox (two cores, Python
3.13.16), before any change. The runner's own words:

- Whole suite: "[run] the suite, side by side: 26 jobs, 906 tests,
  1146s" and "[run] OK (906 tests run)". `time`: real 19m7.5s, user
  31m34.3s, sys 5m31.2s.
- Fast tier: "[run] the fast tier took 66.2s of wall clock, 343 of the
  suite's 906 tests; its budget is 120s". (The brief's 345 was session
  4's count; the runner says 343 at 0.26.0.)

Three things the measurement said, and they shaped the work.

1. **The suite is CPU-bound, not waiting.** 37 CPU-minutes in 19
   wall-minutes is 1.94 of 2 cores busy the whole run. Sleeps and pty
   timeouts are not where the time is. What costs is processes: every
   command a test runs starts bash, git, and Python helpers.
2. **Most of it is setUp building the same world again.** By the case
   class each test descends from, LandCase's 202 tests took 2,403 of
   the 4,423 test-seconds (54 percent), StartCase 287, AudienceCase 175,
   WatchCase 122, HostedCase 77. LandCase's setUp alone (office init,
   found, a project added, a folder opened, a fake bale) took 2.1 s with
   the machine idle, before the test ran a command of its own.
3. **A fake bale call cost 3 to 6 interpreter starts' worth.** The land
   fake was 476 lines of script text formatted into each test's tree. A
   script is never cached, so every call compiled it again, imported
   tarfile, tempfile and the rest, then started the interpreter a second
   time (`os.execv`) to hand `--version` and `status` to the packing
   fake, which compiled its own 142 lines. Timed alone: `bale --version`
   84 ms, `bale status --json` 82 ms, against 15 ms for `python3 -c pass`.

An strace of `tests/run.sh test_sort` (18 tests) at 0.26.0 counted, per
program started: 586 calls of the office's Python helpers (`pylib`), 410
git calls, 70 office commands, and about 65 fake bale calls. The helper
calls were most of the time (more on them below).

## What changed, in the order it paid

### 1. A case's world, built once per job (a lever the brief did not name: flagged, for ratification)

`kept_setup(test, key, build)` in tests/test_office.py. The first test of
a key in a job builds the world into `test.e`, an Env at a fixed place in
the job's temporary directory. What it left (the directory, and the
attributes the build set on the test) is kept as a template. Every later
test of that key gets a copy of the directory at the same path, plus
deep copies of those attributes. Same path matters: the office's
manifest, the git repos and the fake bale's state hold absolute paths,
and they all still hold.

- Each test still starts from exactly the world its setUp describes,
  untouched by any other test. The copy is made before the test and
  removed by the test's cleanup, as the Env's directory always was.
- A world built on an earlier day (local or UTC) is built again, since
  folder and out-tray names carry the day.
- Used by: LandCase, StartCase, AudienceCase (keyed by `hosted`),
  HostedCase (`hosted_world` takes an `e` now), WatchCase (keyed by its
  projects and registry), the plain `Office` of test_desk_verbs (used
  by test_desk_verbs, test_drafting_table, test_watches_digest,
  test_filed_append_only), and `built_office` for the ten test_office
  classes whose setUp was `Env` plus `office init`.
- `Env(test, at=PATH)` is the one new knob on Env: a directory it makes
  rather than a new temporary one.

This was the biggest lever. Neither of the brief's two named levers
could reach the aim alone, so I took it as the brief allows ("Any other
lever your measurement turns up is yours to take inside the forecast,
flagged"). It is a deviation: please ratify or correct.

Its one risk, said plainly. Tests of one key in one job now share a path
in turn. A process a test leaves running after it ends could write into
the next test's copy. I found none in the suite: every after-land
action and every fake runs in the foreground. Before, such a process
would have written into a removed directory instead. Three whole runs
ran with it, and no test failed on it.

### 2. The tests' fake bales as fixed modules

tests/fakes/, four modules:

| module | was | what it fakes |
|---|---|---|
| pack_bale.py | `FAKE_PACK_BALE` in test_start.py | pack, status, --version |
| land_bale.py | `FAKE_LAND_BALE` in test_land.py | apply, retry, unlock, the dossier, relay, open, open --check; hands the rest to pack_bale |
| replay_bale.py | `FAKE_BALE` in test_read_side.py | replays captured lines by argv and directory |
| small_bales.py | `OLD_BALE`, `INSTALL_BALE`, `ASKING_BALE` | the old host's bale, a release install's bale, the bale that asks |

- The `bale` a test puts on its PATH is written by `fake_program(path,
  module, function, config)` in tests/test_office.py: a program of a
  few lines that inserts tests/fakes/ on sys.path, imports the module
  and calls it with the test's config (the paths the old `.format()`
  filled in). Its shebang is the suite's own interpreter with `-S`,
  since no fake uses site packages.
- The runner compiles tests/fakes/ into its bytecode cache with lib/ and
  tests/ (`seed_bytecode`), so the fake's code is compiled once per run.
- The land fake calls the packing fake in its own process (`packed()`
  catches its output where it used to start a subprocess) instead of
  starting the interpreter again. Each verb imports what it uses where
  it starts, so `--version`, `status` and the dossier load only json, os,
  pathlib and sys.
- Behaviour is the script's, line for line: the bodies were moved, not
  rewritten. The only logic change is rider 2 below.

Timed alone with the run's cache, in ms per call:

| call | 0.26.0 | 0.27.0 |
|---|---:|---:|
| land fake `--version` | 84 | 24 |
| land fake `status --json` | 82 | 22 |
| land fake `stats --sid X --json` | 47 | 23 |
| pack fake `--version` | 47 | 22 |
| read fake `status --json` | 27 to 30 | 24 to 29 |
| `python3 -c pass`, for scale | 12 to 15 | |

`RELAY_BALE` (test_audience_line) stays a bash script. It is a
ten-line wrapper in front of the land fake that reads stdin, and bash
starts in 2 ms. I did not move the fake ssh either: it is not a bale,
the brief named bales, and HostedCase's tests were 77 of 4,423 seconds.

### 3. The survey's remaining machine reads made steerable

The tree said which reads 2026-10-13-suite-machine-reads-005 left: its
`SOURCE_ALLOWED` named them, and its notes proposed exactly this. They
were:

- The Tools facts: `command -v` then `TOOL --version` for bale, git,
  python3, R, quarto and node, over the machine's PATH.
- `bale on_path`, `bale install` and `office-src on_path`: which bale
  and which office the PATH runs.
- The container marker, `/.dockerenv`.

During the suite these reached the real machine. On the occupant's WSL
machine every `office init` and `office start` searched the Windows
directories on the PATH for R, quarto and node. A test with no fake
bale on its PATH ran his real bale for its version, and every test
recorded his installed office. Here they also cost a fake bale call,
and a `python3 --version`, per survey.

What I did, in bin/office:

- `survey_which NAME`: looks only in the directories
  `OFFICE_SURVEY_PATH` lists when it is set; `""` lists none, so every
  tool is "not found" and nothing runs. Unset, it is `command -v` as
  before. The program it finds is the one `tool_version` runs.
- `container_marker`: the file `OFFICE_CONTAINER_MARKER` names; `""`
  means none; unset, `/.dockerenv`.

The pattern is `OFFICE_DESKTOP_PATH`'s, applied twice. Env and
`runner.SURVEY_VARS` set both to `""` for every test and job. In the
source rule, the two old allowances (the `command -v "$t"` in
`tool_version` and `command -v office`) are replaced by one for
`survey_which`'s own line.

What I left, and why. The survey's other reads are hostname,
`/etc/os-release`, `uname`, `$SHELL`, `/etc/timezone`, `date` and
`/proc/mounts`. They are kernel and file reads of this machine and run
no program of it. None reaches Windows: on WSL, `/proc/mounts` lists the
drvfs mounts but reads nothing through them. No test asserts their
values, and recording them is the survey's purpose. Steering them would
add knobs with nothing to protect.

### 4. Rider: `on_a_terminal` starts its program with SIGINT at its default

tests/test_start.py `on_a_terminal`: the child resets SIGINT and SIGQUIT
to their defaults before `execve`, as `run_on_a_pty` has since 0.26.0.
The docstring says why. New test:
`test_start.TestTheTerminalHelperOnATerminal`. It ignores both signals
in the test's own process, as a background start does, and checks that
the program sees them at their defaults. It fails with the reset taken
out (checked on a copy).

### 5. Rider: test_land's probe paths taken from each fixture's cwd

The land fake's swaps now read the old root from the capture's own
`cwd` (`cap["cwd"]`). That covers apply's clarification, outside, drift,
hold and applied captures, relay, both unlock captures and both open
captures. The hold capture's downloads directory is `dl/` beside its cwd
(`probe_downloads`). No test file or fake names `/tmp/office-probe.*`
now, so the suite rule's `ALLOWED` entry for test_land is gone. That was
the largest allowance, as 2026-10-12-suite-clock-001 said it would be.
The rule's own example test keeps its case, with the allowance written
in the test.

### 6. Smaller things, each needed by the above

- **`test_files()`** in test_suite_clock reads tests/fakes/ too. A fake
  runs under the test's Env, so the rule against reading the machine
  binds it.
- **test_meetings_view's record test** pinned VERSION to exactly
  "0.26.0", so any later release failed it. It now asks for 0.26.0 or
  later, as every other session's record test does. It failed my first
  "after" run, and only that test (below).
- **test_front_door's TourCase comment** said init's survey asked bale
  its version. It no longer does; the comment now says the walk-in did.

## Tests

- **New, 8.**
  - test_suite_clock: `TestTheSurveysDoors`, 4 tests: the Env's view, a
    tool found only where the door looks (and run from there), the
    container marker, and gather_facts reading through its doors only.
    Plus 1 for the fakes compiled into the run's cache and a fake
    program's exit and config.
  - test_office.TestStatusAndSurvey, 2: under the Env the survey records
    every tool "not found" and runs none, even a recording bale first on
    the PATH; pointed at a directory, it records what is there by path.
    And the container class from the steerable marker.
  - test_start.TestTheTerminalHelperOnATerminal, 1, terminal (rider 1).
- **Changed:** the runner's job-environment test (the survey's two
  variables, whatever the caller set), the allowance example test, and
  test_meetings_view's record test.
- **None dropped or merged.** 906 tests at 0.26.0 are all still there,
  by id. Discover finds 914, and the runner's plan matches it.
- The new test_suite_clock tests are in the fast tier with the rest of
  the module. They cost 1.7 s of test time in all, 1.6 of it the cache
  test compiling the tree once.

## Run results (worker's sandbox, two cores, the same sandbox throughout)

| run | tests | result | wall clock |
|---|---|---|---|
| whole suite, 0.26.0 as shipped | 906 | "[run] OK (906 tests run)" | "1146s" (real 19m7.5s; user 31m34s, sys 5m31s) |
| fast tier, 0.26.0 | 343 | OK | "the fast tier took 66.2s of wall clock" |
| whole suite, first try at 0.27.0 (VERSION not yet bumped; test_office's classes not yet on a kept world) | 914 | "[run] OK (914 tests run)" | "828s" (real 13m49s; user 23m7s, sys 3m57s) |
| whole suite, 0.27.0 with VERSION bumped | 914 | 913 pass; "test_meetings_view failed": its record test pinned 0.26.0 (fixed, above) | "788s" (real 13m9s; user 22m2s, sys 3m46s) |
| fast tier, 0.27.0 | 348 | OK | "the fast tier took 59.6s of wall clock, 348 of the suite's 914 tests" |
| whole suite, 0.27.0 final bytes (the shipped files/) | 914 | "[run] OK (914 tests run)" | "822s" (real 13m43.6s; user 22m49s, sys 4m1s) |

validation.sh, rehearsed twice:

- On a staged copy (the request's tree, files/ over it, apply.sh's chmod),
  every check passed. The fast tier with this session's tests named after
  it was "376 of the suite's 914 tests" in 86.6 s, under its 120 s budget.
  The script took 1 min 27 s in all; the whole suite is behind `--slow`.
- On the request's tree, unchanged, the seven assertions that test this
  change fail, as they should: the release, the fake modules, the probe
  paths, the survey's doors, the rider, the kept worlds, and the syntax
  check, which finds no tests/fakes/ there. One passes on both: "the
  survey reads the PATH as before when unset". That one is deliberate. It
  is the brief's "the office's behaviour for the occupant does not change
  at all", checked as behaviour, so it must hold before and after.
- The record tests that read RELEASES.md, README.md and the front sheet
  (test_suite_clock, test_office, test_audience_line and
  test_meetings_view's) ran again on the filled-in pages, in that
  fast-tier run. They passed.

The serial lane went from 552.5 s to 365.6 s (359.9 in the 788 s run).
It is not the floor of a run, before or after.

Where the time goes by test file: summed test time, the final 822 s run
against 0.26.0's (a test counted under the file that defines it; four
jobs share two cores, so a test's time includes waiting for a core):

| test file | tests before | seconds before | tests after | seconds after | change |
|---|---:|---:|---:|---:|---:|
| test_land | 49 | 507.5 | 49 | 311.2 | -39% |
| test_probe | 43 | 337.4 | 43 | 210.7 | -38% |
| test_return_trip | 31 | 311.2 | 31 | 220.5 | -29% |
| test_audience_line | 35 | 296.0 | 35 | 195.0 | -34% |
| test_third_trip | 34 | 264.0 | 34 | 199.6 | -24% |
| test_desk_verbs | 53 | 241.0 | 53 | 196.3 | -19% |
| test_start | 41 | 226.5 | 42 | 147.2 | -35% |
| test_front_door | 38 | 219.1 | 38 | 177.2 | -19% |
| test_second_trip | 35 | 217.5 | 35 | 165.7 | -24% |
| test_planner_from_words | 27 | 209.7 | 27 | 150.6 | -28% |
| test_office | 117 | 207.3 | 119 | 146.9 | -29% |
| test_drafting_table | 27 | 172.4 | 27 | 156.2 | -9% |
| test_drop | 32 | 162.2 | 32 | 126.6 | -22% |
| test_out_trip_to_host | 42 | 160.4 | 42 | 115.0 | -28% |
| test_founding_door | 23 | 150.2 | 23 | 149.4 | -1% |
| test_watches_digest | 47 | 149.9 | 47 | 93.4 | -38% |
| test_sort | 18 | 107.9 | 18 | 83.0 | -23% |
| test_one_door | 15 | 97.6 | 15 | 66.1 | -32% |
| test_project_on_host | 41 | 97.0 | 41 | 64.2 | -34% |
| test_meetings_view | 22 | 83.3 | 22 | 68.6 | -18% |
| test_home_screen | 14 | 75.1 | 14 | 55.5 | -26% |
| test_clean_delivery | 19 | 59.5 | 19 | 57.1 | -4% |
| test_read_side | 52 | 57.3 | 52 | 56.5 | -1% |
| test_suite_clock | 39 | 12.1 | 44 | 13.8 | +14% |
| test_filed_append_only | 12 | 0.4 | 12 | 0.5 | +7% |
| all | 906 | 4422.6 | 914 | 3226.7 | -27% |

The runner had no earlier run's times on either side ("no earlier run's
times here"), so both runs started their jobs in the same order.

## Where the rest of the time goes, and what would reach 700 here

After this session the suite is still CPU-bound (26.8 CPU-minutes in a
13.7-minute run). I ran an strace of `tests/run.sh test_sort` again at the
final tree:

- Helper calls fell from 586 to 448: the setUp's share of them is now
  paid once.
- Under strace, the helper processes were 83.5 of the module's 109
  seconds. They are now about three quarters of what is left.

Each helper call is `python3 -B -P -c 'import runpy ...'` on one of
lib/'s modules. Timed alone with the run's bytecode cache:

| module | interpreter | import | import only |
|---|---:|---:|---:|
| office_helper | 12.3 ms | 47.9 ms | +35.5 ms |
| office_bale | 12.3 ms | 59.8 ms | +47.5 ms |
| office_drafting | 11.6 ms | 52.9 ms | +41.3 ms |
| office_sort | 12.3 ms | 57.4 ms | +45.1 ms |

So a helper call costs about 60 ms, three quarters of it importing. Most
of the import is standard modules: argparse 8.4 ms, re 6.4, tomllib 5.5,
subprocess 4.3, site 4.4, office_host 4.4, pathlib 3.7, tarfile 2.2,
shutil 2.1 (`-X importtime`, office_helper).

That is the queued proposal the sitting closed: "Importing the office's
heavy standard modules only where used". The sitting closed it on
`office help`, 0.024 s. But `office help` starts no Python at all (an
strace of it here: bash and five coreutils), so it could not see this
cost. A test of `office start` or `office land` runs
25 to 35 helper calls, and the occupant's own commands pay the same:
`office status` took 1.611 s on his machine in the sitting's probe.

The brief keeps the item out of this session, so I did not touch lib/'s
imports. It is the first proposal below, with these numbers.

My estimate of what it would reach: helpers are about three quarters of
what is left. If lazy imports and `-S` (site, 4.4 ms) cut 15 to 20 ms of
each call's 60, the suite drops by a fifth to a quarter again. That is
roughly 620 to 660 s in this sandbox, under 700 here, and 500 to 540 on a
sandbox of session 4's speed. That is a projection, not a measurement.

## Decisions to ratify

1. **Kept worlds** (section 1 above). A lever the brief did not name,
   and the largest one.
2. **`-S` in the fake programs' shebang.** It saves about 5 ms a call,
   and no fake imports anything outside the standard library. If the
   suite's interpreter path has whitespace, the program falls back to
   `/usr/bin/env python3`.
3. **The land fake's packs in its own process.** Its output is the
   packing fake's own, caught and passed on as the subprocess's was;
   argparse's refusals (SystemExit) are caught as an exit code.
4. **Which survey reads I steered and which I left** (section 3).
5. **I did not add the new survey and rider tests to fast-tier.toml.**
   test_suite_clock's new tests are there as part of the module.
   validation.sh names the others on its own command line, as the
   tier's header asks.

## Paths outside the forecast

None. Every changed path is under the request's `resolved_scope`
(README.md, RELEASES.md, VERSION, bin, claude, tests). Nothing under lib/
or doctrine/ changed. lib/ needed no seam: the survey is in bin/office.
The doctrine states no suite times or tiers.

## Proposals

- **What:** reopen "importing the office's heavy standard modules only
  where used", scoped to the Python helpers bin/office starts (`pylib`).
  Do the imports per subcommand in office_helper, office_bale,
  office_drafting and office_sort, and consider `-S` in `pylib`.
  **Why:** measured above. A helper call is about 60 ms, 45 of them
  importing, and a test runs 25 to 35 of them. The sitting's closing
  measurement was `office help`, which runs no helper. The same cost is
  in the occupant's `office status` (1.6 s) and every start and land.
  **Scope hints:** lib/*.py top-level imports and argparse set-up;
  bin/office `pylib`. Measure with `-X importtime` and the run's cache,
  as above. The suite is the regression net, and it now runs in about
  13 minutes here.
- **What:** fewer helper starts per office command: batch the reads one
  command makes into one helper call where they sit side by side.
  **Why:** a test makes 25 to 35 helper calls through a handful of
  office commands, so each command starts several, at about 60 ms each.
  **Scope hints:** bin/office's start and land paths. Larger than the
  first proposal; only after it, if the time still matters.

## Handbook

### office-src

- the suite builds each case's world once per job: tests/test_office.py kept_setup(test, key, build) copies the first test's directory and attributes for every later test of the key, at the same path; Env(test, at=PATH) makes the world's place
- the fake bales are modules in tests/fakes/ (pack_bale, land_bale, replay_bale, small_bales); a test's bale is the program tests/test_office.py fake_program writes, and the runner compiles tests/fakes/ into its bytecode cache
- the survey looks for tools, and for the bale and office on the PATH, only in OFFICE_SURVEY_PATH's directories when it is set (bin/office survey_which), and takes its container marker from OFFICE_CONTAINER_MARKER (container_marker); every Env and job sets both to ""
- tests/test_start.py on_a_terminal starts its program with SIGINT and SIGQUIT at their defaults, as tests/test_front_door.py run_on_a_pty does
- a helper call (bin/office pylib) costs about 60 ms in the suite's sandbox, 45 of them importing; it is now most of the suite's time

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.27.0
its test suite takes about 28 percent less time: in the worker's
sandbox the whole suite went from 1,146 to 822 seconds, with every
test kept. Expect the detached run after each landing to finish about
that much sooner on your machine. Its tests no longer run anything of
your machine's: the surveys they make no longer look up your R, node,
bale or office. Nothing you use changes. Most of what is left is the office's own Python
helpers starting up, which a later session can cut.

## Walkthrough

### What changed

- **Each kind of test world is built once per run of a test file, then
  copied for every test** (tests/test_office.py `kept_setup`,
  `built_office`, `Env(at=)`; the cases in test_land, test_start,
  test_audience_line, test_project_on_host, test_watches_digest,
  test_desk_verbs and test_office).
- **The fake bales are modules** (tests/fakes/, new: pack_bale.py,
  land_bale.py, replay_bale.py, small_bales.py; tests/test_office.py
  `fake_program`; tests/runner.py `seed_bytecode`). The script texts are
  gone from test_start, test_land, test_read_side, test_project_on_host
  and test_out_trip_to_host.
- **The survey's last reads of the machine are steerable** (bin/office
  `survey_which`, `container_marker`, `tool_version`, `gather_facts`;
  tests/test_office.py `Env`; tests/runner.py `SURVEY_VARS`,
  `isolated_env`; tests/test_suite_clock.py `SOURCE_ALLOWED`).
- **Rider 1** (tests/test_start.py `on_a_terminal`).
- **Rider 2** (tests/fakes/land_bale.py; tests/test_suite_clock.py
  `ALLOWED`).
- **The record:** README (Layout and Tests), RELEASES 0.27.0, VERSION,
  the development record's front sheet; test_meetings_view's record test
  reads "0.26.0 or later".

### Why

Your words of 2026-10-12, still in force: "The biggest barrier to this
is honestly the extended time that using office allots to me", and
"tackle this time inefficiency first". The after-the-arc sitting found
the time in the suite: 517 to 805 seconds on your machine over four
releases, paid twice in every session and again after every landing. It
sent this session to cut it, with the two queued levers and two riders.

### How to explain each piece

- **Worlds built once:** most tests begin by making a small office, a
  project and a folder. That used to happen again for every test; now
  each run of a test file makes it once and gives every test a fresh copy
  of it.
- **Fake bales as modules:** the tests use a stand-in for bale. It used
  to be rewritten and recompiled for every test and every call; now it
  is ordinary code that is compiled once.
- **The survey's reads:** the survey records what tools your machine
  has. During tests it now looks nowhere, so the tests never run your
  programs or search Windows' folders.
- **The riders:** two test helpers made consistent with their siblings,
  so Ctrl-C in a terminal test behaves as it does for you, and so no test
  file names a directory from the machine a probe ran on.

### Questions a reviewer will ask

- *Does anything change for me?* No. The survey reads what it read; the
  new variables are only the suite's.
- *Could one test's leftovers leak into another now?* Each test gets its
  own fresh copy, removed after it, at the same place in turn. Only a
  process a test left running could write into the next copy, and the
  suite starts none.
- *Did any test go?* No. 906 then, 914 now; discover and the runner's
  plan agree.
- *Why not 700 seconds?* This sandbox runs the old suite in 1,146
  seconds, not 928, so 700 would be a 39 percent cut. The cut here is
  28 percent, beyond the brief's 25. What is left is mostly the
  office's helpers importing Python modules: a measured proposal, kept out
  of this session by the brief.

### A hand test

Run these on your WSL terminal, one line at a time.

1. After this lands, `office land` runs `./install.sh` for office-src and
   starts the detached suite. If you want to start one yourself,
   `cd ~/office-src && tests/run.sh --detach`.
2. When it ends, `cat ~/.local/state/office-src/suite/latest/verdict`. It
   should read `OK <time>: 914 tests passed in <N>s` with N about a
   quarter below 0.26.0's 805 seconds (roughly 560 to 620 on your machine,
   my estimate).
3. To see the survey's steering, in any office (nothing is committed):
   `OFFICE_SURVEY_PATH= office survey --no-commit` should list every tool
   as "not found" in floor-plan/survey.md, and a plain `office survey
   --no-commit` right after should list them as before, by their paths.

## Delivery

- to: nobody: office-src has no audience

### Commit

Cut the test suite's time: worlds built once, fake bales as modules

The suite spent most of its time rebuilding the same office, project and
folder before every test, and recompiling the fake bale on every call. A
case's world is now built once per test file's run and copied, at the
same path, for each test; the fake bales are modules under tests/fakes/
that the runner's bytecode cache holds, run through a three-line program,
and the land fake hands its packs to the packing fake in its own process.

The survey's last reads of the machine are steerable: the tools it
records, the bale and office on the PATH (OFFICE_SURVEY_PATH) and the
container marker (OFFICE_CONTAINER_MARKER). Unset, nothing changes; the
suite sets both empty. on_a_terminal starts its program with SIGINT at
its default, and the land fake takes each capture's paths from the
capture.

In the worker's two-core sandbox the whole suite went from 1,146 to
822 seconds and the fast tier from 66.2 to 59.6, with every test kept
and eight added.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.

## Structure

- title: The suite's time
- size: medium
- goal: Cut the office-src suite's time where it goes, measured before and after in one sandbox
