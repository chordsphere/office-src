# Notes: 2026-10-22-helper-imports-003 (office-src 0.28.0)

A small helper call (`office_helper vercmp`, as `bin/office pylib` runs it,
with the run's bytecode cache) went from 85 ms of CPU to 42 in this
sandbox: a cut of 50 percent, past the brief's aim of 40 where it was 60.
The whole suite went from 1,245 seconds to 866 (914 tests then,
919 now: none dropped, five added), the fast tier from 85.4 seconds to
64.1. Three whole runs: the unchanged tree, a first try at the changed
tree, and the shipped code; after the last only the record's numbers
were filled in and one test's expectation reordered, and the fast tier
ran again on the final bytes (Run results).

This sandbox is slower than suite-time's: the same 0.27.0 tree took
1,245 seconds here where it took 822 there, and the fast tier 85.4 where
it took 59.6. So the brief's numbers (a call at 40 ms, the suite at 660
seconds) do not read directly here; the brief says they are a projection.
Read as shares: the helper call is half what it was, the suite 30
percent less, the fast tier 25 percent less. On a sandbox of
suite-time's speed the same shares would read about 30 ms a
call and 570 seconds for the suite.

Nothing the occupant sees changes. Every verb's output, exit code and
side effects are as they were; the suite is the net, and the two
mechanisms that could have changed what a helper prints (the
one-subcommand parser, the lazy patterns) were checked byte for byte
against the unchanged tree besides (section 3 and Tests).

The pre-flight check said it fits. No probe and no light block: the tree
and the brief answered everything. Every changed path is inside the
forecast. No compaction.

This is the re-attempt (`corrects` names the first response), after a
HOLD on the occupant's machine: section 6 says what held and what
changed, which is one test and one validation check, not the code.

## What I measured first

At the shipped tree (0.27.0), in this sandbox (two cores, Python
3.13.16), before any change. The runner's own words:

- Whole suite: "[run] the suite, side by side: 26 jobs, 914 tests, 1245s"
  and "[run] OK (914 tests run)". `time`: real 20m46.7s, user 33m27.7s,
  sys 6m30.5s.
- Fast tier: "[run] the fast tier took 85.4s of wall clock, 348 of the
  suite's 914 tests; its budget is 120s", "[run] OK (348 tests run)".

Each module's start, as `pylib` runs it (`python3 -B -P -c '<runpy>'`),
with a bytecode cache seeded the way tests/runner.py seeds one, the
median of 15 runs, wall clock (the machine was idle; the CPU column of
the final table is the steadier measure):

| module | wall ms | over `python3 -c pass` (18.9 ms) |
|---|---:|---:|
| office_helper | 82.5 | +63.6 |
| office_bale | 110.5 | +91.6 |
| office_drafting | 91.5 | +72.6 |
| office_sort | 89.3 | +70.3 |
| office_drop | 89.6 | +70.7 |
| office_door | 83.9 | +65.0 |
| office_host | 50.5 | +31.6 |
| office_letterhead | 46.9 | +28.0 |

(`--version` was the argument, which every module refuses: an argparse
error, so this table holds the full parser build and the usage line;
it is the same call before and after and the shares hold. The real small
call is in Run results.)

Where a call's time went, by `-X importtime` and by timing the parts in
one process:

- Imports were most of it: office_helper 46 ms, office_bale 71 ms with
  the cache (`import` alone, no main). The standard modules every module
  pulled in at the top cost, in ms: argparse 13 (re 11 inside it, enum
  7), tomllib 8.5, office_host 6.6 (hashlib 3, tarfile, tempfile,
  threading, shutil, subprocess, shlex), subprocess 5.6, site 5.4,
  pathlib 5.4, tarfile 3.1, shutil 3.1, json 2. And office_bale imported
  six sibling modules at its top (office_drafting, office_door,
  office_host, office_drop, office_sort, office_meeting), each with its
  own standard modules, so `office_bale status-lines` loaded the same
  code as a start.
- The patterns a module compiles at its top: 28 in office_helper, 5.4 ms;
  30 in office_drafting, 9.2 ms; 25 in office_meeting, 4.6 ms. A call
  uses a few of them.
- argparse's set-up: office_helper built 53 subparsers before reading
  which one the call named, about 6 ms; office_bale 30, about 9 ms.
- The interpreter itself, `python3 -B -P -c pass`: 17 to 19 ms wall, of
  which `site` is about 5 (with `-S`, 11 to 13 ms).

An strace of `tests/run.sh test_sort --jobs 1` (18 tests) counted the
helper calls per office command, by the nearest `bin/office` ancestor of
each `pylib` python3 (the worker's method; my parser is the session's
scratch tool, not shipped):

| verb | commands | helper calls | per command | modules |
|---|---:|---:|---:|---|
| land | 3 | 134 | 44.7 | helper 93, bale 19, sort 11, drafting 5, watches 3, door 2, deliver 1 |
| start | 7 | 80 | 11.4 | helper 54, bale 16, drop 5, door 2, sort 2, drafting 1 |
| open | 6 | 58 | 9.7 | helper 52, bale 6 |
| drop | 9 | 54 | 6.0 | helper 36, drop 18 |
| walk-in | 3 | 30 | 10.0 | helper 24, bale 6 |
| moves | 3 | 26 | 8.7 | helper 18, sort 5, bale 3 |
| status | 1 | 17 | 17.0 | helper 12, drafting, drop, sort, bale, deliver 1 each |
| survey | 4 | 16 | 4.0 | helper 12, bale 4 |
| the rest | 11 | 33 | 3.0 | projects, close, blueprint, init, sessions, desk |
| all | 47 | 448 | 9.5 | helper 327, bale 58, drop 24, sort 21, drafting 8, door 5, watches 3, deliver 2 |

448 is the count suite-time's worker found at 0.27.0. office_helper is
73 percent of the calls, which is why it got the most attention.
Besides the helpers, the module started git 187 times, the fake bale
and the runner's own python3 110, and bash and the coreutils about 600.

## What changed, in the order it paid

### 1. Imports where they are used

Every lib/ module imported its heavy standard modules and its sibling
modules at the top. Now a function imports what it uses where it
starts, and the top of a module holds what every call needs: argparse,
datetime, os, pathlib, re, sys, and office_helper (office_bale keeps
office_host too: 24 of its functions read hosted projects through it,
and office_host is now cheap to load). The modules moved: subprocess,
tarfile, tempfile, tomllib, json, shlex, hashlib, threading, zoneinfo,
urllib; and the siblings office_drafting, office_door, office_drop,
office_sort, office_meeting, office_bale, office_watches,
office_letterhead and (in office_helper and office_probe) office_host.
shutil and fnmatch were moved too, though argparse loads shutil and
pathlib loads fnmatch, so a call pays for them regardless.

I did this with a tool over the syntax tree, not by hand: for each
name, every top-level function or method whose body reads it gets the
import as its first statement after its docstring, and the top-level
import goes; a use the tool cannot move (a module-level statement, a
class body, a decorator, a default argument, a function that also binds
the name) stops it and is named. That is how the exceptions above were
found: office_watches and office_digest name the drafting table's pages
from office_drafting's constants at the top, office_deliver builds its
error class on office_bale's, and `Reader.__init__`'s default argument
was `subprocess.run`. pyflakes over lib/ reports what it reported
before (four f-strings with no placeholders) and nothing new. Three
places needed a hand:

- `office_bale.Reader.__init__(self, consumption=None, runner=None)`:
  the default was `runner=subprocess.run`, which imported subprocess
  the moment the module loaded. It is `runner if runner is not None
  else subprocess.run` now, with the import there. Every caller passes
  a runner or nothing, so nothing changes for them.
- Four `except (..., ValueError, tomllib.TOMLDecodeError)` clauses in
  the mains of office_digest, office_drafting and office_watches named
  tomllib for nothing: TOMLDecodeError is a ValueError, and the clause
  already caught ValueError. tomllib is gone from them, with a comment.
  Same exceptions caught, same message (the class name printed is the
  exception's own).
- `office_meeting.gather_prep` read office_sort through office_planner's
  module attribute (`op.osort.chapter_rel`), which is a function-level
  import in office_planner now; it imports office_sort itself.

A dispatcher's imports are in its branches, not at its top:
office_bale's main imports json in the `start` and `withdraw` branches
and office_drafting in `start-riders`, office_drafting's dispatch
imports json in `blueprint-close-plan` and `moves-plan`, office_drop's
in `list`, office_sort's imports office_drop in `pending`,
office_letterhead's imports json for `--rules-json` and `--words-json`.
office_probe's main keeps json at its top (every branch reads or writes
a plan), and the mains of office_digest, office_watches and office_home
keep office_bale (they read bale).

Two unused top-level imports went with the rest: office_drafting's
subprocess and office_sort's datetime and json (pyflakes named them
before this session too).

### 2. Patterns compiled when first used

`office_helper.LazyPattern(pattern, flags=0)`: holds the arguments,
compiles on the first attribute read and answers for the compiled
pattern after (match, search, fullmatch, sub, findall, finditer, split,
pattern, flags, groupindex: whatever `re.Pattern` has, through
`__getattr__`). Every pattern at the top of a module that imports
office_helper is one now, 112 of them in 10 modules, converted by a
tool over the syntax tree (module-level `re.compile(` only, inside
tuples too: office_drafting's CITE_RES and MASTER_FORMS, office_meeting's
SERIES_PATTERNS). office_host and office_letterhead import nothing of
the office and keep `re.compile` for their three.

What this cannot do: a LazyPattern is not a `re.Pattern`, so `re.sub(X,
...)` with X a LazyPattern would refuse (`re` compiles its first argument
and takes only a string or a compiled pattern). lib/ never hands a
module-level pattern to a `re` function (I grepped for `re.<fn>(NAME`,
for `isinstance(..., re.Pattern)` and for a pattern's `.pattern` used to
build another; none), and tests use them through their methods only.
The test that holds the modules to the rule says so in its name.

### 3. One subcommand's parser

office_helper and office_bale built every subcommand's parser (53 and
30) on every call, then read which one the call named. Now:

- `office_helper.subcommand_named(argv)` is the first argument when
  there is one and it is not a flag, else None.
- `build_parser(only=None)` in each module builds the parser as before,
  but through `oh.OneSubcommand(sub, only)` when `only` is given: its
  `add_parser(name, **kwargs)` builds the named subcommand's parser and
  returns a `SkippedParser` for every other, an object that takes every
  call a parser takes (add_argument, set_defaults,
  add_mutually_exclusive_group, the group's add_argument) and keeps
  nothing. It records every name, and `build_parser` sets the
  subparsers action's metavar to `{name,name,...}` from them, which is
  the string argparse would have formatted from the choices; so the
  usage line reads the same. It returns `(parser, found)`.
- `main` builds for the named subcommand; when `found` is False (an
  unknown name) it builds the whole parser and lets argparse refuse as
  it did; a call with no argument or a flag first (`-h`) builds the
  whole parser too.

The 53 lines that define office_helper's subparsers and the 30 that
define office_bale's are as they were but for `sub.add_parser(` read
`add(`; the dispatch code is untouched. I compared both modules'
command-line surface byte for byte against the unchanged tree (stdout,
stderr and exit code) for 33 argument vectors: no argument, `-h`,
`--help`, `--version`, an unknown subcommand with and without
arguments, a subcommand with too few, the right, too many and unknown
arguments, a subcommand's `-h`, a mutually exclusive group with both
and neither, and the subcommands that need no office. All the same.
The one case that could have differed is "unrecognized arguments" after
a valid subcommand, whose usage line lists every subcommand: the
metavar keeps it.

I did this for the two modules where it costs (0.12 ms a subparser: 6
and 9 ms); office_drafting has 19 subparsers and is 8 of 448 calls,
the rest have 2 to 9. The pattern is there to take if a module grows.

### 4. `-S` in `pylib`

`python3 -B -P -S -c '<runpy>'` in bin/office. lib/ is standard library
only, so nothing it imports is lost; the test suite ran whole under it.
What `-S` saves is site's own work and its search of site-packages,
about 5 ms on `python3 -c pass` (18.9 to 11.2 here), and about 2.5 ms
on a real helper call, since most of what site imports (os, codecs,
encodings) the module imports anyway.

The one qualification, said in bin/office's comment and in RELEASES.md:
zoneinfo is the one standard module that can reach site-packages. On a
machine with no system zoneinfo directory (`/usr/share/zoneinfo` and
the three others `zoneinfo.TZPATH` names), Python falls back to the
`tzdata` package from site-packages, which `-S` hides. There the
office's zone names would not resolve and the dates and times would be
UTC, said under OFFICE_DEBUG, exactly as they already are for a name
that does not resolve (`office_home.zone`, `office_meeting.zone`,
`office_watches.zone` all catch it). WSL Ubuntu and every Linux I know
ship the directory; this sandbox does. I judged this safe and left `-S`
in. If the occupant's machine lacks `/usr/share/zoneinfo`, `ls
/usr/share/zoneinfo | head -3` would show it in a second, and the fix
is the system tzdata package, not the Python one.

### 5. Smaller things

- **A timing the suite pinned, loosened** (tests/test_drop.py
  `TestTheRideAlong`): the test dropped two pages and expected `office
  start` to name them by name, on the comment "two dropped in the same
  minute go by name". The fast tier on the final bytes caught the two
  straddling a minute once (the test failed, the only failure in any
  run; `office_drop.drops` orders by the dropped stamp, then by name,
  and is unchanged). The test now orders its expectation the way
  `drops` does, from each page's own stamp. The brief allows tests/
  "where a test pins an import or a timing"; this is one.
- The comment above `pylib` in bin/office says what `-S` does and does
  not do; the one above `-B` is as it was.
- README's Layout rows for bin/office and lib/office_helper.py name
  `pylib`'s flags and the two classes every module's start leans on.

### 6. The hold, and the re-attempt

The first response was held by its own validation on the occupant's
machine: two of the new tests, and the matching validation check, said
`urllib`, `urllib.parse` and `threading` were loaded by a small helper
call and by `import office_helper`. They were, and not by lib/: his
Python is older than this sandbox's 3.13 (3.11 or 3.12, by the
symptoms), and there `pathlib` itself imports `urllib.parse` (with
`ipaddress`), and `runpy`'s `importlib.util` imports `threading`; 3.13
dropped both. My check listed the heavy modules by name and assumed the
kept imports (argparse, datetime, os, pathlib, re, sys, and pylib's
runpy) loaded none of them, which was true of the interpreter I ran and
not of his. The code is as it was; the two lines that moved are the
test's and the check's. Reproduced here under python3.11 and 3.12
(both are installed in this sandbox beside 3.13): the same two failures,
the same three names.

The fix measures instead of listing: the test reads, once per class,
what `import argparse, datetime, os, pathlib, re, runpy, shutil, sys`
loads on the interpreter it runs under (`KEPT`, the baseline), and holds
a module to the heavy modules it loads beyond that; the small-call test
and validation.sh's check do the same. `TestTheHelpersStart` passes
under python3.11, 3.12 and 3.13 here; the fast tier passed whole under
3.11 (61.7 s), and so did the whole suite (838 s, 919 tests; Run
results). The
command-line parity check of section 3 ran under 3.11 too: all the same.

One consequence for his numbers, not for the code: on his Python a
helper call carries `urllib.parse` and `threading` from pathlib and
runpy, about 2 ms more than here per call, and nothing in lib/ can shed
them. The share of the cut holds; the floor is a little higher.

## Tests

- **New, 5**, in tests/test_suite_clock.py, class `TestTheHelpersStart`
  (in the fast tier with the rest of the module; 2.2 s in all here, most
  of it the fifteen interpreters the first test starts):
  - every lib/ module imports none of the heavy standard modules at the
    top (`-X importtime` over `import MODULE`, less what the kept imports
    and runpy load on this interpreter: the baseline, read once), against
    a `HEAVY` list and a `HEAVY_AT_TOP` table that is empty today, and
    only the siblings `SIBLINGS_AT_TOP` names (office_helper for most;
    the four exceptions with their reasons);
  - a small call run as bin/office runs it (`office_helper vercmp`)
    loads none of them, no site and no office_host, and a call that
    reads TOML (`stamp`) loads tomllib;
  - a LazyPattern compiles on first use and answers for the pattern,
    and no module that imports office_helper compiles a pattern at its
    top (office_host and office_letterhead must);
  - a call that names its subcommand builds one parser whose usage
    equals the whole parser's, an unknown name is not found,
    `subcommand_named` reads argv as described, and a SkippedParser
    swallows what a parser takes;
  - `pylib`'s line carries `-S`, and a module run through it sees
    `sys.flags.no_site`, no `site` module and no `-packages` path.
  All five fail on the unchanged tree (checked on a copy: the three
  about imports, the small call and `-S` fail outright there, and the
  two about LazyPattern and build_parser fail on the missing names).
- **Changed, 1:** test_drop's ride-along test orders its two drops by
  stamp, then name (section 5). **None dropped or merged.** 914 at
  0.27.0 are all there by id; discover finds 919 and the runner's plan
  matches it.

## Run results (worker's sandbox, two cores, the same sandbox throughout)

| run | tests | result | wall clock |
|---|---|---|---|
| whole suite, 0.27.0 as shipped | 914 | "[run] OK (914 tests run)" | "1245s" (real 20m46.7s; user 33m27.7s, sys 6m30.5s) |
| fast tier, 0.27.0 | 348 | OK | "the fast tier took 85.4s of wall clock, 348 of the suite's 914 tests" |
| fast tier, first try at 0.28.0 (two of the new tests still naming shutil and fnmatch as heavy, which argparse and pathlib load) | 352 | 350 pass; the two new tests failed on their own lists (fixed) | "68.6s" |
| whole suite, first try at 0.28.0 (VERSION bumped; office_drafting's dispatch still importing json at its top, and the two per-module tests not yet one) | 920 | "[run] OK (920 tests run)" | "904s" (real 15m6.0s; user 23m35s, sys 5m47s) |
| fast tier, 0.28.0 final bytes, first run | 353 | 352 pass; test_drop's ride-along test failed on its minute straddle (section 5; fixed) | "65.2s" |
| fast tier, 0.28.0 final bytes | 353 | "[run] OK (353 tests run)" | "the fast tier took 64.1s of wall clock, 353 of the suite's 919 tests" |
| whole suite, 0.28.0 final code (the shipped lib/, bin/office and test_suite_clock.py; after it only the record's numbers were filled in and test_drop's expectation reordered) | 919 | "[run] OK (919 tests run)" | "866s" (real 14m27.5s; user 22m40s, sys 5m30s) |
| fast tier, 0.28.0 re-attempt, python3.11 on the PATH | 353 | "[run] OK (353 tests run)" | "the fast tier took 61.7s of wall clock" |
| whole suite, 0.28.0 re-attempt, python3.11 on the PATH | 919 | "[run] OK (919 tests run)" | "838s" (real 14m0.1s; user 21m42s, sys 5m39s) |

The small helper call, `office_helper vercmp 0.1.0 0.2.0`, as `pylib`
runs it with the run's cache, 31 runs each, the machine idle:

| tree | flags | wall median | wall min | CPU median (user+sys) | CPU over the interpreter |
|---|---|---:|---:|---:|---:|
| 0.27.0 | -B -P | 85.6 ms | 75.1 | 85.1 | +67.7 |
| 0.28.0 | -B -P | 45.2 | 43.3 | 44.7 | +26.8 |
| 0.28.0 | -B -P -S | 42.8 | 40.7 | 42.3 | +29.6 |

(`python3 -c pass` is 17.4 ms of CPU with -B -P and 12.7 with -S.) What
is left of the 42 ms: the interpreter 12.7, then the modules every call
needs: re with enum and functools about 8, pathlib with glob and fnmatch
about 6, argparse with gettext, shutil and locale about 8, os 3, datetime
0.4; then office_helper's own body about 2, the one subparser, the
read. The floor for a module that uses argparse and pathlib is near.

Each module's import alone (`import MODULE`, no main), before and after,
CPU median of 15, with the cache:

| module | 0.27.0, `-B -P` | 0.28.0, `-B -P` | 0.28.0, `-B -P -S` | cut |
|---|---:|---:|---:|---:|
| `python3 -c pass`, for scale | 16.0 | 16.0 | 11.1 | |
| office_bale | 86.6 | 46.1 | 37.5 | 57% |
| office_deliver | 98.9 | 41.7 | 40.6 | 59% |
| office_digest | 91.0 | 36.9 | 38.1 | 58% |
| office_door | 65.6 | 36.2 | 34.8 | 47% |
| office_drafting | 73.0 | 36.9 | 41.4 | 43% |
| office_drop | 74.4 | 37.1 | 34.1 | 54% |
| office_helper | 68.0 | 35.7 | 33.3 | 51% |
| office_home | 85.4 | 35.0 | 35.5 | 58% |
| office_host | 50.4 | 30.3 | 30.1 | 40% |
| office_letterhead | 40.3 | 31.7 | 30.1 | 25% |
| office_meeting | 86.9 | 35.2 | 35.3 | 59% |
| office_planner | 96.4 | 35.0 | 33.8 | 65% |
| office_probe | 92.2 | 35.4 | 34.3 | 63% |
| office_sort | 78.0 | 37.4 | 33.1 | 58% |
| office_watches | 91.0 | 37.9 | 34.7 | 62% |

(CPU ms, user plus system, the median of 15 fresh interpreters each; a
few cells sit a millisecond or two off their neighbours, which is the
machine, not the code. The import is most of a call: what a real call
adds is the parser and the read.)

Under strace, `tests/run.sh test_sort --jobs 1` at the final tree: the
same 47 office commands and the same 448 helper calls, by verb and by
module, as at 0.27.0 (the same programs started, in the same counts: git
187, the fake bale and the runner's python3 109, the coreutils as
before), and the helper processes took 79.3 s of the module's run under
strace where they took 135.0 (the module 2m04 where it was 2m59). Under
strace a call reads 141 to 264 ms by verb now, 221 to 419 before; the
ratio is the measure, not the number.

Where the time goes by test file: summed test time, the final run
against 0.27.0's (a test counted under the file that defines it; four
jobs share two cores, so a test's time includes waiting for a core):

| test file | tests before | seconds before | tests after | seconds after | change |
|---|---:|---:|---:|---:|---:|
| test_land | 49 | 482.2 | 49 | 336.7 | -30% |
| test_return_trip | 31 | 341.0 | 31 | 235.5 | -31% |
| test_probe | 43 | 323.9 | 43 | 220.8 | -32% |
| test_third_trip | 34 | 303.5 | 34 | 222.3 | -27% |
| test_desk_verbs | 53 | 297.9 | 53 | 195.2 | -34% |
| test_audience_line | 35 | 292.5 | 35 | 212.9 | -27% |
| test_front_door | 38 | 274.1 | 38 | 184.8 | -33% |
| test_second_trip | 35 | 240.9 | 35 | 161.7 | -33% |
| test_drafting_table | 27 | 233.9 | 27 | 157.9 | -32% |
| test_start | 42 | 227.3 | 42 | 159.7 | -30% |
| test_founding_door | 23 | 223.9 | 23 | 151.8 | -32% |
| test_planner_from_words | 27 | 221.2 | 27 | 143.0 | -35% |
| test_office | 119 | 220.7 | 119 | 158.6 | -28% |
| test_drop | 32 | 189.8 | 32 | 128.5 | -32% |
| test_out_trip_to_host | 42 | 177.7 | 42 | 129.1 | -27% |
| test_watches_digest | 47 | 145.0 | 47 | 99.7 | -31% |
| test_sort | 18 | 124.3 | 18 | 85.6 | -31% |
| test_meetings_view | 22 | 102.1 | 22 | 69.7 | -32% |
| test_project_on_host | 41 | 95.6 | 41 | 70.8 | -26% |
| test_one_door | 15 | 91.1 | 15 | 58.8 | -35% |
| test_read_side | 52 | 85.0 | 52 | 66.1 | -22% |
| test_clean_delivery | 19 | 83.2 | 19 | 57.8 | -31% |
| test_home_screen | 14 | 77.5 | 14 | 58.8 | -24% |
| test_suite_clock | 44 | 16.7 | 49 | 20.5 | +22% |
| test_filed_append_only | 12 | 0.7 | 12 | 0.6 | -6% |
| all | 914 | 4871.8 | 919 | 3387.0 | -30% |

validation.sh, rehearsed twice:

- On a staged copy (the request's tree, files/ over it, apply.sh's
  chmod, the manifest beside it for the epilogue), every check passed
  and every claim agreed with its verdict. The fast tier with this
  session's tests named after it (`test_suite_clock.TestTheHelpersStart
  test_drop.TestTheRideAlong`) was "OK (356 tests run)" in 69 s, under
  its 120 s budget (the re-attempt's rehearsal; under python3.11 the
  same check's Python ran clean too). The script took 1 min 11 s in all;
  the whole suite is
  behind `--slow`, claimed pass on the final run above.
- On the request's tree, unchanged, the ten assertions that test this
  change fail, as they should: the release (four: VERSION, RELEASES, the
  front sheet, README), `-S` in pylib, the top-level imports, the lazy
  patterns, the one-subcommand parser, the small call's loaded modules,
  and the fast tier, which stops before running on the class names it
  does not know. The syntax check and the exec bit pass on both,
  deliberately.

## Where the time goes now, and the second proposal

After this session the suite is still CPU-bound (28.2 CPU-minutes in
a 14.5-minute run). The helpers are cheaper, not fewer: a start
still makes about 11 calls, a land about 45, `office status` 17, each
now about 42 ms here where it was 85, so `office status` spends about
0.7 s in helpers where it spent 1.4 (on the occupant's machine, where
it took 1.6 s in all, expect roughly half of that back).

The brief's second proposal, fewer helper starts per command, is
conditional on these numbers. What they say: the time still matters.
The helpers are still about two thirds of test_sort's time under strace
(79 of 124 s), and of a call's 42 ms about 35 is the interpreter and the
modules every call needs (re, pathlib, argparse, os), paid on every call
however little it reads. A start's 11 calls are about 0.5 s of helpers
here, a land's 45 about 1.9 s, `office status`'s 17 about 0.7 s; the
rest of those commands is bash, git and bale (test_sort started git 187
times to the helpers' 448). Batching the side-by-side reads into one
call per command would return most of those seconds: a land to about
0.3 s of helpers, a status to about 0.1, and the suite by roughly
another third if the 448 calls became one or two per command. On the
occupant's machine, where `office status` took 1.6 s, this session
brings it to about 1.0 by my estimate, and batching would bring it near
0.4. It is a larger change than this one (the reads sit between bash
logic in bin/office's start and land paths), so it stays a proposal
below, with the numbers; the brief's "only if the time still matters"
reads yes to me.

Two things I did not do, and why:

- Replace runpy in `pylib` with a direct loader (importlib.machinery,
  exec of the code object). runpy showed 4 ms in `-X importtime`, but
  nearly all of it is os and importlib.util, which the modules import
  anyway; the real call measured the same both ways (49.9 against 50.4
  ms, within noise). Not worth a hand-rolled loader.
- Avoid argparse's own loads (shutil and locale, about 4.6 ms): argparse
  reads the terminal's width through shutil on every `add_argument` and
  translates its strings through gettext, which loads locale. A fixed
  formatter width would change `--help`'s output. Left alone.

## Decisions to ratify

1. **`-S` is in**, with the zoneinfo qualification (section 4). If the
   sitting would rather see the occupant's machine first, the probe is
   one line (`ls /usr/share/zoneinfo | head -3`), and `-S` is one flag
   to take out.
2. **LazyPattern as the rule for every module-level pattern** in the
   modules that import office_helper (section 2), held by a test. The
   alternative, compiling in each function, would have touched every
   use site.
3. **The one-subcommand parser in office_helper and office_bale only**
   (section 3).
4. **The three hand edits** in section 1 (`Reader.__init__`'s default,
   the TOMLDecodeError tuples, `gather_prep`'s import).
5. **shutil and fnmatch moved into functions too**, though argparse and
   pathlib load them anyway: the rule "heavy modules where used" is
   simpler to state and hold without two exceptions, and it costs
   nothing. The test's HEAVY list leaves them out, since a check on them
   would always fail.

## Paths outside the forecast

None. Every changed path is under the request's `resolved_scope`
(README.md, RELEASES.md, VERSION, bin, claude, lib, tests). Nothing
under doctrine/, share/, templates/, migrations/ or install.sh changed;
the doctrine states nothing about the helpers' start.

## Proposals

- **What:** fewer helper starts per `office land` (and `office start`):
  batch the side-by-side reads one command makes into one helper call
  where they sit next to each other in bin/office.
  **Why:** measured above. A land makes about 45 helper calls, a start
  about 11, `office status` 17; at 42 ms each here, that is 1.9, 0.5
  and 0.7 s of helpers, and about 35 of each call's 42 ms is the
  interpreter and the modules every call needs, paid per call. Batching
  would return most of a land's 1.9 s and a status's 0.7, and the suite
  roughly another third (the helpers are still two thirds of test_sort's
  time under strace). The brief made this conditional on these numbers:
  they say the time still matters, for the occupant's land and status
  and for the suite.
  **Scope hints:** bin/office's land and status paths (the `helper`
  calls that read the same folder.md or manifest in a row); a helper
  subcommand that answers several questions in one JSON line. Larger
  than this session.
- **What:** the `python3 -c 'import json,sys; ...'` one-liners in
  bin/office (46 lines of them, mostly the fields `office start`,
  `office land` and `office moves` read back from a helper's JSON line)
  could run with `-S -B -P` too, or each group of them be one read.
  **Why:** each is an interpreter start (17 ms here, 12 with `-S`) plus
  json; a start runs four to six of them on one JSON blob. Small, and
  the same family as the first proposal; noted so the numbers are in
  one place.
  **Scope hints:** bin/office `start` and `land`; out of this session's
  `pylib` scope, so untouched.

## Handbook

### office-src

- each lib/ module imports its heavy standard modules (subprocess, tarfile, tempfile, tomllib, json, shlex, hashlib, threading, zoneinfo, urllib) and its sibling modules in the functions that use them; the top holds argparse, datetime, os, pathlib, re, sys and office_helper (office_bale keeps office_host; office_watches and office_digest keep office_drafting; office_deliver keeps office_host and office_bale), and tests/test_suite_clock.py TestTheHelpersStart holds every module to it
- a pattern at the top of a module that imports office_helper is an office_helper.LazyPattern, compiled on first use; office_host and office_letterhead keep re.compile
- office_helper and office_bale build only the named subcommand's parser (office_helper.OneSubcommand, SkippedParser, subcommand_named; each module's build_parser(only)); a call with no subcommand, a flag or an unknown name builds the whole parser
- bin/office pylib starts Python with -B -P -S; lib/ needs nothing of site-packages, and zoneinfo's tzdata fallback is the one standard module that would (the zone falls back to UTC, said under OFFICE_DEBUG)
- tests/test_suite_clock.py TestTheHelpersStart counts a module's heavy imports beyond what the kept imports and runpy load on the running Python (KEPT, read once as the baseline): before 3.13, pathlib loads urllib.parse and runpy loads threading on their own
- a helper call (bin/office pylib) costs about 42 ms of CPU in the worker's sandbox where it cost 85 (about 30 where 60 in suite-time's); office status makes 17, a start about 11, a land about 45

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.28.0
the Python helpers every `office` command starts take about half the
time they did: a small call went from 85 ms to 42 in the worker's
sandbox, and `office status` makes 17 of them, a start about 11, a land
about 45, so your commands return sooner and the suite runs in about
30 percent less time (866 seconds there where 0.27.0's took 1,245,
every test kept). Nothing you use changes. The helpers still start
once per read, and most of a call is now Python starting; fewer helper
starts per command is the next lever, and the numbers say it is worth
taking.

## Walkthrough

### What changed

- **Each lib/ module imports its heavy standard modules and its sibling
  modules where they are used** (all fifteen lib/ modules; the top of
  each holds argparse, datetime, os, pathlib, re, sys and
  office_helper, with the four exceptions tests/test_suite_clock.py
  `SIBLINGS_AT_TOP` names).
- **Patterns compile on first use** (lib/office_helper.py `LazyPattern`;
  every module-level pattern in the eleven modules that import
  office_helper).
- **One subcommand's parser** (lib/office_helper.py `OneSubcommand`,
  `SkippedParser`, `subcommand_named`, `build_parser`;
  lib/office_bale.py `build_parser`; both mains).
- **`-S` in `pylib`** (bin/office `pylib` and its comment).
- **Three small hand edits** (lib/office_bale.py `Reader.__init__`'s
  `runner` default; the `except` tuples in lib/office_digest.py,
  lib/office_drafting.py and lib/office_watches.py;
  lib/office_meeting.py `gather_prep`'s import of office_sort).
- **A pinned timing loosened** (tests/test_drop.py `TestTheRideAlong`).
- **The re-attempt** (tests/test_suite_clock.py `KEPT`, `heavy_in`;
  validation.sh's small-call check): the heavy modules are counted
  beyond what the kept imports load on the running Python.
- **Tests:** tests/test_suite_clock.py `TestTheHelpersStart`, five tests.
- **The record:** README (Layout and Tests), RELEASES 0.28.0, VERSION,
  the development record's front sheet (The suite's clock, Recent
  changes).

### Why

Your words of 2026-10-12, still in force: "The biggest barrier to this
is honestly the extended time that using office allots to me". The
after-the-arc sitting closed the helpers' imports on a measurement of
`office help`, which starts no Python; suite-time's worker measured the
helpers themselves (about 60 ms a call, three quarters of it importing,
25 to 35 calls per start or land) and the sitting reopened the item on
those numbers, aimed at a call at 40 ms. This session is that: the
helpers start light, and every command you run starts several of them.

### How to explain each piece

- **Imports where used:** each helper used to load every library it
  might need the moment it started, including the ones for running
  programs, reading archives and talking to other machines, whether or
  not the call needed them. Now each piece of work loads what it uses
  when it runs.
- **Patterns on first use:** the text patterns a helper knows (what a
  folder line looks like, what a session id looks like) were all
  prepared at start; now each is prepared the first time it is used.
- **One subcommand's parser:** a helper used to build the command-line
  description of all its 53 subcommands before reading which one you
  asked for; now it builds the one you asked for, and the whole set
  only when it has to show you help or refuse a name.
- **`-S`:** Python starts without looking for add-on packages, which
  the office never installs or uses.

### Questions a reviewer will ask

- *Does anything change for me?* No. Every verb prints what it printed
  and exits as it exited; the suite checks that, and the two helpers
  whose command lines were restructured were compared byte for byte
  against the old ones.
- *Why do timings in the notes not match the brief's 60 and 40 ms?*
  The worker's sandbox was slower than the last session's (the same
  0.27.0 suite took 1,245 seconds here, 822 there). Read the shares: a
  call is half what it was, which on the last session's sandbox would
  be about 30 ms where it was 60.
- *What is `-S`'s risk?* A machine with no system time-zone directory
  would see the office's dates in UTC, with a debug line saying why; on
  Linux and WSL the directory is there. `ls /usr/share/zoneinfo | head
  -3` shows it.
- *Did any test go?* No. 914 then, 919 now; discover and the runner's
  plan agree.
- *Why was the first response held?* Its new test listed the heavy
  modules by name and did not expect your Python's `pathlib` and `runpy`
  to load two of them (`urllib.parse`, `threading`) on their own, as
  they do before 3.13. The test now measures that baseline on the Python
  it runs under. Nothing in lib/ changed between the two responses.
- *Is the suite at 660 seconds?* Not here: this sandbox is half again
  slower than the one that number was projected on. Here it went from
  1,245 to 866 (30 percent); the same share on that sandbox reads
  about 570, under the 660 the brief projected.

### A hand test

Run these on your WSL terminal, one line at a time.

1. After this lands, `office land` runs `./install.sh` for office-src and
   starts the detached suite. When it ends, `cat
   ~/.local/state/office-src/suite/latest/verdict` should read `OK
   <time>: 919 tests passed in <N>s`, with N below 0.27.0's by roughly a
   fifth to a quarter.
2. `time office status` in any office: compare with the 1.611 s the
   sitting's probe measured on 2026-10-22; expect roughly half of the
   helpers' share back (my estimate: about 1.0 s).
3. `grep -n 'python3 -B -P -S' ~/office-src/bin/office` shows `pylib`'s
   line; `ls /usr/share/zoneinfo | head -3` shows your machine has the
   zone directory `-S` leaves zoneinfo reading.

## Delivery

- to: nobody: office-src has no audience

### Commit

Cut the helpers' start-up: imports where they are used, -S in pylib

Every office command starts several Python helpers (office status 17, a
start about 11, a land about 45), and each spent three quarters of its
time importing standard modules and sibling modules the call never
used. Each lib/ module now imports its heavy standard modules and its
siblings in the functions that use them; the patterns at a module's
top are office_helper.LazyPatterns, compiled on first use;
office_helper and office_bale build only the parser of the subcommand a
call names (OneSubcommand), with the usage line kept whole through the
action's metavar; and bin/office's pylib starts Python with -S, since
lib/ is standard library only (zoneinfo's tzdata fallback is the one
standard module that would reach site-packages, and the zone falls back
to UTC as it did).

Every verb's output, exit code and side effects are as they were; the
suite is the net, and the two restructured command lines were compared
byte for byte. In the worker's two-core sandbox a small helper call went
from 85 ms of CPU to 42, the whole suite from 1,245 seconds to
866 and the fast tier from 85.4 to 64.1, with every test
kept and five added (tests/test_suite_clock.py TestTheHelpersStart).

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.

## Structure

- title: The helpers' start
- size: medium
- goal: Cut the office's Python helpers' start-up, measured before and after in one sandbox, every verb's behaviour unchanged
