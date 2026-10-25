# Notes: 2026-10-25-install-cache-001 (office-src 0.30.0)

install.sh now compiles lib/ into lib/__pycache__ as it installs, every
helper call reads that compiled code, `office status` says in one line
whether it is level with the sources, and a landing's three helper calls
for bale's apply are one (`office_bale land`). In everyday use, in this
sandbox (two cores, Python 3.13.17, each version run from an install its
own install.sh made, the suite's land world), `office status` took 0.30
seconds where it took 0.56, the walk-in 0.40 where 0.92, a start 1.6
where 2.8 and a land 1.3 where 2.9. Most of it is the cache: a small
helper call is 50 ms of CPU where it was 100, an office_bale call 60
where 210. The landing in one call is about 150 ms of a land's share. The
whole suite took 659 seconds where 0.29.0's took 658 here (924 tests
then, 942 now: none dropped, eighteen added), as expected, since the
runner already cached for itself.

Nothing the occupant sees changes but the one new `office status` line,
and `office status --help`'s sentence naming it (decision 6). The suite
is the net, and 21 commands were compared against the unchanged tree
besides, with a zone database and without one: identical but for that
line.

The pre-flight check said it fits, comfortably. No probe and no light
block: the tree, the brief and the survey answered everything. Every
changed path is inside the forecast. No compaction.

## The HOLD, and this re-attempt

This response corrects the first one for this session, which bale held
on your machine: validation's fast tier failed one test,
`test_watches_digest.TestDigest.test_watches_standing_desk_agenda_blueprints`,
with `9 != 10` on a commit count. Every other check passed, and the
tier ran in 22.7 s there, against about 75 here.

The test is not one this session touched, and nothing this session
changed is on its path: under the runner both trees run on the runner's
cache, and the digest neither installs nor lands. It runs `office digest`
twice and counts one commit for the second run. The digest page is
stamped to the second (`- written_at: ...T03:07:47Z`), so a second run
inside the same second writes the same bytes, office digest commits only
what changed, and there is nothing to commit. I confirmed that
mechanism here: the digest written three times with `--now` pinned
changed the page, then nothing at the same second, then the page again a
second later. On a machine three times faster than this sandbox, both
runs fit in one second often; here each takes about a second, so the
first response's rehearsals and its whole suite passed. It was a latent
race, which your faster machine surfaced, and the response that
brought the office its cache happened to be the first to be held on it.

The fix is the test's: before the second run it reads the first page's
`written_at` and waits the clock past that second (under a second; it
sleeps 50 ms at a time), so the second page differs by its stamp and the
commit it counts is real. What it checks is unchanged: the page is
overwritten, committed, and never records a firing. The office's
behaviour is unchanged too. I left the digest's stamp alone: a re-run
in the same second really has nothing new to say, and committing
nothing then is right. I could not force the old failure here (no
faketime, and the race needs both runs in one second), so the evidence
is the pinned-clock demonstration and the wait being sure by
construction; the fixed test passed five runs of five, about 8.7 s
each. No other test counts a commit across two runs of a second-stamped
page.

The corrected bytes: tests/test_watches_digest.py (the wait, and `import
time`) and RELEASES.md (one sentence saying so). Nothing else differs
from the held response but this manifest (`corrects`) and these notes.

## What I measured first

At the shipped tree (0.29.0), in this sandbox, before any change:

- Whole suite: "[run] the suite, side by side: 26 jobs, 924 tests, 658s"
  and "[run] OK (924 tests run)". `time`: real 11m3.8s, user 15m56.9s,
  sys 4m38.8s (helper-starts' sandbox gave 652 for the same tree; I ran
  two in-process test classes, under a second, while it ran).
- Fast tier, twice: "[run] OK (356 tests run)", "the fast tier took 76.9s
  of wall clock" and then 75.6. helper-starts' sandbox gave 56.0 for its
  358; this sandbox's whole suite agrees with its, so I compare shares
  within this sandbox, never across.

Everyday use, as the brief asked: an install made by the shipped
install.sh into a scratch prefix (no bytecode cache: none was written,
as before), and test_land's LandCase world (an office scoping one
project with a fake bale), the Env pointed at the install's bin/office
and with no PYTHONPYCACHEPREFIX. `office status` and the walk-in (piped:
the page) the median of 7, a start and a land once, per round; wall and
CPU (the children's user and system time). My harness is this session's
scratch, not shipped. In the first quiet hour, two rounds:

| command | 0.29.0, no cache, wall / CPU ms |
|---|---:|
| office status | 495 / 515 |
| office (the page) | 792 / 830 |
| office start | 2,397 / 2,400 |
| office land | 2,460 / 2,505 |

That is helper-starts' 0.29.0 no-cache column (530, 856, 2,598, 2,770)
within this sandbox's noise. The sandbox then slowed by about a fifth for
the rest of the session (no process of mine; the host's), so every
before-and-after number below comes from rounds run interleaved, old and
new in turn, and the after is never compared with a quieter before.

What a call costs, CPU, median of 15, from an install's lib/ (os.times'
10 ms resolution):

| call | with the install's cache | without |
|---|---:|---:|
| `office_helper vercmp` | 50 ms | 100 |
| `office_bale --help` | 60 | 210 |

helper-starts measured 43 and 98, 63 and 192.

## What changed

### 1. install.sh compiles lib/

After it copies the shipped parts into its staging directory and before
it moves the stage into place, install.sh removes any `__pycache__` the
copy carried (a plain `cp -a` of a working copy outside git can carry
one; `git archive` never does) and runs

    python3 -I -m compileall -q --invalidation-mode timestamp -d "$PREFIX/lib" "$STAGE/lib"

- **Where the cache lives: lib/__pycache__, beside the sources.** The
  interpreter finds it there with nothing set, so pylib, the batch's
  sibling imports and office_bale's own import of office_host all read
  it as they are. It is written in the stage, and a stage-relative
  cache survives the `mv` into place; a PYTHONPYCACHEPREFIX cache is
  keyed on each source's absolute path, so it would be written for the
  stage's path and miss at the install's. A prefix would also have to be
  exported by bin/office for every helper, and a prefix hides every
  other `__pycache__`, the standard library's included: the runner links
  the standard library's compiled code into its prefix for exactly that
  reason, and the install would have to as well.
- **A read-only install directory** reads the cache as a writable one
  does: the cache is written before the install takes its place, by the
  script that makes it, and no command writes it afterwards (`-B` stays).
  The test makes the whole install read-only and runs `office status`
  with PYTHONVERBOSE: every office module it imports comes from the
  install's lib/__pycache__, and the install's file list and times are
  unchanged after (in this sandbox I run as root, so read-only bits do
  not stop a write; the "nothing written" half is what holds the claim
  there). The cases left where a call compiles from source, as it does
  at 0.29.0, are a compile that failed at install time, a python3 other
  than the one install.sh ran (a Python upgrade: the cache is tagged
  cpython-312, a 3.13 reads cpython-313's), a source changed inside the
  install, and a PYTHONPYCACHEPREFIX in the environment; `office status`
  says each.
- **`-I`**: none of the caller's PYTHON* variables reach the compile. I
  found why it matters by trying it: with PYTHONPYCACHEPREFIX set (the
  suite sets it for every command a test runs), compileall writes into
  the prefix, not beside the sources, and the install gets nothing.
  PYTHONOPTIMIZE would compile `.opt-1` files the office never reads.
- **`--invalidation-mode timestamp`**: what the interpreter checks is
  each source's size and modification time, which `git archive | tar -x`
  and `cp -a` both keep (the commit's time, or the working copy's).
  Named explicitly because SOURCE_DATE_EPOCH, which `-I` does not
  ignore, would otherwise switch py_compile to checked hashes.
- **`-d "$PREFIX/lib"`**: the code objects name the install's path, not
  the stage's. The import system fixes a loaded module's file names up
  anyway; this keeps the bytes honest.
- **Quiet on success.** install.sh's output is unchanged when the
  compile succeeds: office land runs it for office-src as an after-land
  action, so its lines are part of what a land shows. A compile that
  fails is a warning naming what compileall said, and the install goes
  on (the brief's worst acceptable answer, said by status).

Installing takes about half a second longer here: 0.51 to 0.67 seconds
where it took 0.15 to 0.20.

### 2. office status's bytecode line

`office_helper bytecode-check INSTALL` (`bytecode_line`, `bytecode_state`,
`pyc_state`, `installed_source`) judges each `.py` under the install's
lib/ the way the import system would for the interpreter running it:
`importlib.util.cache_from_source` names the file it would read (its
cache tag, its optimization level, its cache prefix), then the magic
number, the flags, and the source's time and size, or for a checked hash
the source's hash. It prints one line and exits 0 when level, 3 when
not. It runs in status's one batch (the third call), so status is still
one helper start, and its line comes under the install's `source:` line:

    bytecode:   level with lib/'s 15 modules (cpython-312, in lib/__pycache__)
    bytecode:   BEHIND: 1 of lib/'s 15 modules compiles from source on every helper call (office_probe.py stale); (cd '/home/USER/office-src' && ./install.sh) brings the cache level
    bytecode:   NONE for this python3 (cpython-313; the install holds cpython-312's): all 15 of lib/'s modules compile from source on every helper call; (cd ... && ./install.sh) brings the cache level
    bytecode:   none read: this office-src runs from a working copy, not an install, so all 15 of lib/'s modules compile from source on every helper call

Under a cache prefix the line says so (the interpreter reads that cache
alone, never the install's), level or not. A check that cannot run at all
says `bytecode:   could not be checked`. It is a line, never a refusal,
and status still exits 0. I checked the Python-upgrade line for real:
the sandbox has /usr/bin/python3.12 beside its 3.13, and the check run by
3.12 against a 3.13-compiled install prints the NONE line naming
cpython-313's.

### 3. The landing in one call: `office_bale land`

`land_whole` runs what land-prepare, land-run and land-outcome ran, in
one process, each step as its own process ran it:

1. `take_record_out`, the plan written back, and the line it returns said
   as `[office] LINE` on stderr: bin/office's `log`, the same bytes in the
   same place (the line without trailing newlines, nothing when empty, as
   `$(...)` and `[ -z ]` had it). A refusal is said and exits 1, and
   nothing else runs.
2. `land_run`, with the terminal's stdin, stderr and stdout (bale's
   stdout is copied to ours as it comes, as before). Its failures become
   the code the outcome reads, as land-run's exit was: its error lines and
   1, a traceback and 1 for an error it did not expect, and a code taken to
   its low byte as a process exit took it (bale killed by a signal is
   -2 here and was 254 through the exit).
3. `land_outcome`, with a fresh Reader (the consumption manifest shared:
   it is read-only) and `office_host.forget_reach()`, so a host that did
   not answer during the run is asked again and one that did is carried,
   as the reach file carried it to a new process; nothing the run cached
   stands in for what bale recorded. Its JSON goes to `--outcome FILE`,
   since stdout is bale's. A refusal exits 3, or 4 when the record line
   was said (the record may still be out of its folder).

Each step reads the plan from the file, as its process did. bin/office's
`cmd_land` runs `reader land ... --outcome "$tmp/outcome.json"` and
reads `out="$(< "$outcome_file")"` on 0; on 3 or 4 it says what it said
when land-outcome refused (the warning on 4 only), and dies; anything
else exits 1, as a refused land-prepare did. The three old subcommands
are gone from office_bale's parser and dispatch: nothing else called
them.

So the brief's condition holds: bin/office's one line between prepare
and run is kept, in its order, from inside. The test that shows it runs
an office session's landing with stdout and stderr in one stream, as a
terminal shows them: the landing line, then the record line, then bale's
first line, then `Landed:`. A plain landing starts nine helpers where it
started eleven (test_land `TestFewerHelperStarts`, changed from 11).

## What the occupant sees

Byte for byte, as before, but for the new status line: the suite, and a
scratch sequence of 21 commands run against both trees in the suite's
own world (status, the walk-in, a project start, status and walk-in
again, its land, status and walk-in again, a second start, a land that
finds no response, its held landing, its retry with `--response`, an
office session's start and land, a land with nothing out, a second office
session landed with bale's stats refusing after the apply, status,
walk-in, desk, week). The four landings that reached bale's apply or
retry ran with both streams merged, in the order written; the rest with
stdout and stderr apart. Compared after masking times, hashes and temporary
directory names: 17 identical, and the four statuses differ by exactly
the new line. Repeated with no zone database (TZDIR at an empty
directory): the same.

Two things differ that the brief's "but for the one new line" does not
cover, both for ratification (decision 6 and 7): `office status --help`
names the cache in its sentence of what status says, and an error a
landing step did not expect prints a traceback that starts at
`land_whole` where it started at runpy's frames (only on that crash
path; the landing goes on as it did).

## Tests

- **New, 18.** tests/test_office.py `TestTheInstallsBytecodeCache` (5):
  install.sh into the Env's own prefix with PYTHONPYCACHEPREFIX,
  PYTHONOPTIMIZE=2 and SOURCE_DATE_EPOCH set compiles one plain,
  timestamp-checked, level pyc per lib/ module into lib/__pycache__ and
  nothing into the prefix, says nothing new, and the code names the
  install's path; status's line is the level line, in its place, and with
  the install read-only every office module a status imports is read
  from the cache and nothing in the install changes; a stale source and
  a removed cache are the BEHIND and NONE lines with install.sh's line,
  a cache prefix is said, and install.sh again brings it level; a
  compile that fails (a python3 on the PATH whose compileall fails) is
  the warning, the install goes on and status says NONE; a copy outside
  git carries none of the working copy's `__pycache__`.
  `TestTheBytecodeLine` (5): every state of the line on a small install
  of its own, the names and the "and N more", the working copy, a stamp
  with no source and a quoted one, a cache prefix, and `pyc_state`
  against checked and unchecked hashes, a wrong magic number, unknown
  flags and a short file. tests/test_land.py `TestTheLandingInOneCall`
  (2): the record line between the landing line and bale's in one
  stream; bale's stats refusing after the apply, for an office session
  (the warning, before the error) and a project session (the error
  alone). `TestLandWholeInProcess` (6): the three steps stubbed, each
  reads the plan its predecessor wrote, the line said once and stripped,
  nothing said for an empty one, a refused prepare runs nothing, the
  run's failures and codes reach the outcome (1, 254, 125, 3), an
  unexpected error is a traceback, and an unread outcome exits 3 or 4.
- **Changed, 2:** tests/test_land.py
  `TestFewerHelperStarts.test_a_start_and_a_land_start_a_handful_each`
  counts nine helpers for the landing where eleven; and, in this
  re-attempt, tests/test_watches_digest.py
  `TestDigest.test_watches_standing_desk_agenda_blueprints` waits the
  clock past the first digest's second before its second run (the
  section above). And TestInstall's
  setUp and `install()` moved into a base class, `InstallCase`, which
  TestInstall and the new class share; TestInstall's four tests are as
  they were (the fast tier names one of them).
- **None dropped or merged.** 924 at 0.29.0, 942 now; the runner's plan
  and discover agree.

Run over the unchanged code (the request's tree with these two test
files), 17 of the 19 fail: no bytecode-check, no cache, no `land`
subcommand, eleven starts. The two that pass are
`TestTheLandingInOneCall`'s, by design: they pin what the landing had
to keep through the merge (the record line's place on a terminal, and
the unread outcome's warning and error), so they hold on both trees.

## Run results (this sandbox, two cores, the same sandbox throughout)

| run | tests | result | wall clock |
|---|---|---|---|
| whole suite, 0.29.0 as shipped | 924 | "[run] OK (924 tests run)" | "658s" (real 11m3.8s; user 15m56.9s, sys 4m38.8s) |
| fast tier, 0.29.0, twice | 356 | OK | "the fast tier took 76.9s", then 75.6 |
| test_office, test_land, test_suite_clock, test_read_side, 0.30.0 | 292 | "[run] OK (292 tests run)" | 160 s |
| whole suite, 0.30.0 final code (after it only the record's numbers were filled in) | 942 | "[run] OK (942 tests run)" | "659s" (real 11m3.8s; user 16m7.3s, sys 4m43.7s; I listed the tests by discover, a few seconds, while it ran) |
| fast tier, 0.30.0 | 356 | "[run] OK (356 tests run)" | "the fast tier took 74.3s" |
| fast tier with this session's tests named after it (validation's line), on the staged copy | 375 | "[run] OK (375 tests run)" | "the fast tier took 96.7s" |
| re-attempt: whole suite, with the digest test's wait (after it only RELEASES.md's sentence was added) | 942 | "[run] OK (942 tests run)" | "635s" (real 10m40.6s; user 15m38.3s, sys 4m40.9s) |
| re-attempt: the fixed digest test alone, five runs | 1 | OK five of five | about 8.7 s each |
| re-attempt: validation.sh on a fresh staged copy | 375 in its fast tier | every check PASS, the fast tier [agree] | 1m22s; "the fast tier took 80.1s" |

Everyday use, the install each version's own install.sh made, the
suite's land world, wall / CPU ms, the median across rounds (each round:
status and walk-in the median of 7, a start and a land once), rounds run
interleaved:

| command | 0.29.0 as shipped, no cache (6 rounds) | 0.30.0, its install's cache (6) | 0.29.0, a cache compiled by hand (2) | 0.30.0, its cache removed (2) |
|---|---:|---:|---:|---:|
| office status | 556 / 575 | 299 / 315 | 308 / 335 | 601 / 605 |
| office (the page) | 919 / 925 | 403 / 435 | 420 / 460 | 917 / 950 |
| office start | 2,799 / 2,775 | 1,602 / 1,610 | 1,755 / 1,765 | 2,967 / 2,960 |
| office land | 2,870 / 2,875 | 1,272 / 1,320 | 1,437 / 1,490 | 2,513 / 2,535 |

The two middle columns split the change: the cache alone (0.29.0 with a
cache) takes a land from 2.9 seconds to 1.4, and the landing in one call
takes off about 150 ms more with a cache (1.44 to 1.27) and about 350 ms
without one (2.87 to 2.51: two starts that each compiled office_bale).
A start is the same in both trees, as it should be (2.8 and 3.0 without a
cache are this sandbox's noise across two rounds). Status without a
cache is about 45 ms slower at 0.30.0 than at 0.29.0: office_helper is
140 lines longer to compile, and bytecode-check reads fifteen small files;
with the cache that is under the noise. With the fake bales' own modules
precompiled too (two rounds each), the same picture: status 595 to 292,
the walk-in 911 to 378, a start 2,781 to 1,531, a land 2,863 to 1,121.

The suite barely moves because the runner already compiles lib/, tests/
and tests/fakes/ into its own cache (tests/runner.py seed_bytecode) and
hands it to every command; this session changes nothing there. Its
eighteen new tests add their own time (the five install tests run
install.sh and init).

validation.sh, rehearsed twice:

- On a staged copy (the request's tree, files/ written over it with
  their modes stripped, apply.sh's two chmods, the manifest beside it for
  the epilogue): every check passed and both claims reconciled (the fast
  tier [agree], the whole suite [n/a], skipped without `--slow`). The
  script took 1m39s in all, the fast tier with this session's tests
  96.7 s of it, under its 120 s budget in this sandbox (which runs the
  bare tier in 75 where helper-starts' ran it in 56). A first version that
  also named TestInstall, TestLandAnOfficeSession and the whole
  TestFewerHelperStarts took 109 s; I named only what this session made
  or changed. Afterwards the staged tree was byte for byte my working
  tree but for the logs and the manifest copy: no `__pycache__`, and the
  scratch install removed. The whole suite is behind `--slow`, claimed
  pass on the final run above.
- On the request's tree, unchanged, the assertions that test this change
  fail, as they should: the record, install.sh's cache, the bytecode
  line, the landing, and the fast tier, which stops before running on
  the class names it does not know. The syntax checks and the exec bits
  pass on both, deliberately.

## Decisions to ratify

1. **The cache lives in lib/__pycache__**, written by install.sh in its
   stage before the swap (section 1 says why not a prefix).
2. **A read-only install** reads the cache as any other does; the cases
   left that compile from source are a failed compile, another python3,
   a source changed inside the install and a cache prefix, each said by
   `office status`.
3. **install.sh is quiet when the compile succeeds** and warns, then goes
   on, when it fails; `-I`, timestamp invalidation and `-d` as section 1
   says.
4. **The status line's states and words** (level, BEHIND, NONE, none read
   for a working copy, the prefix's line) and its place under `source:`;
   exit 3 when not level, `could not be checked` when the check cannot
   run, never a refusal.
5. **`office_bale land`** replaces the three subcommands outright (exit 0,
   1, 3, 4; the outcome to a file; a fresh reader and reach for the
   outcome), rather than adding a fourth beside them.
6. **`office status --help`** says the status names the cache ("whether
   its bytecode cache is level with its lib/ for this python3"): a
   verb's output, changed by one clause, so that the help still lists
   every line status prints.
7. **A traceback from an error a landing step did not expect** starts at
   land_whole's frame where it started at the interpreter's; the step
   goes on as bin/office went on after its exit 1.
8. **The digest test waits for the clock** (this re-attempt): the fix is
   in the test, not the digest, since a re-run within one second has
   nothing new to write and committing nothing is right.

## Paths outside the forecast

None. Every changed path is under the request's `resolved_scope`
(README.md, RELEASES.md, VERSION, bin, claude, install.sh, lib, tests).
Nothing under doctrine/, share/, templates/ or migrations/ changed: the
doctrine says the install is never written, which still holds (install.sh
writes the cache as it writes the install, before it is one), and says
nothing about bytecode or about the landing's helper calls.

## Proposals

- **What:** say a cache that is not level on the walk-in too, the way the
  walk-in says an install behind its source (the head's `install-lines`
  read), and put install.sh's line on the Next line when it is.
  **Why:** the occupant walks in far more often than he runs `office
  status`, and the case that will happen to him is a Python upgrade
  (Ubuntu's next release brings 3.13 or later): every command then
  compiles from source again and takes about twice as long, with only
  status saying why. Here a status without the cache is 0.6 seconds
  where 0.3, a land 2.5 where 1.3. The brief asked for status alone, and
  the walk-in's bytes stay as they were this session.
  **Scope hints:** lib/office_bale.py `install-lines` (or a batch call of
  `bytecode-check` in `walk_in_head`), bin/office `walk_in_head` and the
  Next line's order; tests/test_read_side.py.
- **What:** run office_letterhead.py through the cache when office_deliver
  runs it on this machine: it starts it as a script
  (`sys.executable -B lib/office_letterhead.py`, lib/office_deliver.py),
  and a script's own code is never read from a cache, so that call still
  compiles its 540 lines every time.
  **Why:** the same lever on a smaller call, found while checking what
  else runs from the install; it is in deliver and land's review, not in
  the four commands measured here, so I left it.
  **Scope hints:** lib/office_deliver.py, where it builds that argv; the
  hosted form (the module sent on stdin) stays as it is.

## Handbook

### office-src

- install.sh compiles lib/ into lib/__pycache__ as it installs (python3 -I -m compileall -q --invalidation-mode timestamp -d PREFIX/lib, in its staging directory before the swap; a __pycache__ the copy carried is removed first); quiet when it succeeds, a warning and the install goes on when it fails
- office status's bytecode line is office_helper bytecode-check INSTALL (bytecode_line, bytecode_state, pyc_state), in status's batch: each lib/ module judged as the import system judges it for the running python3 (cache_from_source: its cache tag, optimization level and PYTHONPYCACHEPREFIX; then magic, flags, time and size or hash); level exits 0, BEHIND, NONE and a working copy's none read exit 3
- under PYTHONPYCACHEPREFIX (the test runner's, handed to every Env) the interpreter reads that cache alone, never an install's lib/__pycache__; a test that means the install's cache runs its commands without it (tests/test_office.py TestTheInstallsBytecodeCache)
- office land's landing is one office_bale land call (land_whole: take_record_out and its line said, land_run, then land_outcome with a fresh Reader and office_host.forget_reach, its JSON into --outcome; exit 0, 1 nothing ran, 3 unread, 4 unread with the record still out); land-prepare, land-run and land-outcome are gone; a plain land starts nine helpers
- the digest page is stamped to the second (written_at), and office digest commits only a page that changed: two runs inside one second commit once; a test that counts the second run's commit waits the clock past the first page's second (tests/test_watches_digest.py)
- in everyday use, from an install with its cache, office status took 0.30 s here where 0.56 at 0.29.0, a start 1.6 where 2.8, a land 1.3 where 2.9; a small helper call 50 ms of CPU where 100, an office_bale call 60 where 210

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.30.0
its install carries the office's Python helpers already compiled:
install.sh compiles them once, as it installs, where every helper call
used to compile its own from source. In the worker's sandbox `office
status` took 0.3 seconds where it took 0.56, the walk-in 0.4 where 0.9, a
start 1.6 where 2.8 and a land 1.3 where 2.9; a land also starts two
helpers fewer, its three steps around bale's apply now one. `office
status` has one new line, under the install's source line, saying
whether that compiled code is level with the sources for the python3 you
run; when it is not (after a Python upgrade, say), it names what
compiles from source and the one line that brings it level, install.sh
again. Nothing else you use changes, and installing takes about half a
second longer.

## Walkthrough

### What changed

- **The install's bytecode cache** (install.sh): lib/ compiled into
  lib/__pycache__ with `python3 -I -m compileall`, in the staging
  directory before the install takes its place; a copied `__pycache__`
  removed first; a failed compile a warning.
- **Its line in office status** (lib/office_helper.py `bytecode-check`,
  `bytecode_line`, `bytecode_state`, `pyc_state`, `installed_source`,
  `shell_single_quoted`; bin/office `cmd_status`, `usage_status`, and
  pylib's comment).
- **The landing in one call** (lib/office_bale.py `land`, `land_whole`,
  `LAND_UNREAD`, `LAND_UNREAD_RECORD_OUT`, `land_main`; the land-prepare,
  land-run and land-outcome subcommands removed; bin/office `cmd_land`).
- **Tests:** tests/test_office.py `TestTheInstallsBytecodeCache`,
  `TestTheBytecodeLine`, `InstallCase`; tests/test_land.py
  `TestTheLandingInOneCall`, `TestLandWholeInProcess`, and
  `TestFewerHelperStarts`' landing count; tests/test_watches_digest.py's
  digest test, which waits for the clock's next second before running
  the digest again (the cause of the first response's HOLD).
- **The record:** README (Install, the status line's comment, Layout,
  Tests), RELEASES 0.30.0, VERSION, the development record's front sheet
  (The suite's clock, Recent changes, Known problems, Questions).

### Why

Your words of 2026-10-12, still in force: "The biggest barrier to this
is honestly the extended time that using office allots to me".
helper-starts found that on your machine every helper call compiles its
module from source, about half of what a call costs, because the office
runs its helpers without ever writing the install, and nothing else
writes a compiled copy. Compiling once at install time removes that
from every call. The landing's three calls in a row were the next small
cut helper-starts named.

### How to explain each piece

- **The compiled helpers:** Python has to translate each helper from its
  source text before it runs it. It can keep the translation on disk and
  reuse it, but the office never writes into its own install, so on your
  machine it translated afresh every time, seventeen times for one
  `office status` before 0.29.0, once now. install.sh now does the
  translation once, when it installs, and every command reads it.
- **The status line:** says whether that translation matches the helpers
  installed, for the Python you run. It goes out of step only if Python
  changes or someone edits the install, and then the line says what to
  run.
- **The landing in one call:** a landing took the office's own note out
  of the folder, ran bale, then read what bale recorded, as three
  separate helpers; now it is one, which says the same line in the same
  place.

### Questions a reviewer will ask

- *Does anything change for me?* One line in `office status`, and its
  help's sentence. Everything else is byte for byte: the suite, and 21
  commands compared against the old tree.
- *What if the install directory is read-only?* Nothing changes: the
  compiled files are written while the install is made, before it is in
  place, and no command writes them.
- *What happens when Ubuntu upgrades Python?* The compiled files are for
  the old Python, so every call compiles from source again, as before
  this release, until install.sh runs again; `office status` says so
  with the line to run. A known problem on the front sheet says the
  same.
- *Why did the suite not get faster?* It already had a cache of its own
  (the runner compiles everything once per run); this release gives your
  install what the suite had.
- *Did any test go?* No. 924 then, 942 now.
- *Why was the first response held?* One digest test ran the digest
  twice and expected two commits, but on a fast machine both runs can
  fall in the same second and write the same page, so there is nothing
  new to commit. Your machine is fast enough to hit it; the worker's
  sandbox was not. The test now waits a moment for the clock.

### A hand test

Run these on your WSL terminal, one line at a time.

1. After this lands, `office land` runs `./install.sh` for office-src.
   Then `ls ~/.local/share/office-src/lib/__pycache__ | head -3` shows
   files ending in `.cpython-312.pyc`.
2. `office status | sed -n 5p` in any office reads `bytecode:   level
   with lib/'s 15 modules (cpython-312, in lib/__pycache__)`.
3. `time office status`: compare with the 1.611 s the sitting's probe
   measured on 2026-10-22 (0.26.0); expect well under half of it.

## Delivery

- to: nobody: office-src has no audience

### Commit

Give the install a bytecode cache, and land in one helper call

Every office command runs its Python helpers with -B and never writes
the install, so in everyday use each helper call compiled the module it
loaded from source, about half of what the call cost. install.sh now
compiles lib/ into lib/__pycache__ as it installs, with the python3 the
office runs, in its staging directory before the install takes its
place (python3 -I -m compileall, timestamp-checked), and every helper
call reads it. office status says in one new line, under the install's
source line, whether that cache is level with the sources for the
running python3 (office_helper bytecode-check), and names what compiles
from source and the line that brings it level when it is not; a compile
that fails at install is a warning, and the install goes on.

The landing's three helper calls around bale apply (the office's record
out of its folder, the apply or retry, its outcome) are one, office_bale
land, which says the record's line itself in its place and writes the
outcome to a file, since its stdout is bale's. A plain land starts nine
helpers where eleven.

Every verb's output, exit code and side effects are as they were, but
for the new status line and the status help's sentence naming it. In a
two-core sandbox, from an install each version's install.sh made,
office status took 0.30 s where 0.56, the walk-in 0.40 where 0.92, a
start 1.6 where 2.8 and a land 1.3 where 2.9; the whole suite, which
already ran on its own cache, 659 seconds where 658, every test kept and
eighteen added. A digest test that could fail on a fast machine, when
its two runs fell in one second, now waits the clock past the first.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.

## Structure

- title: The install's bytecode cache
- size: small
- goal: Give the install a bytecode cache compiled by install.sh, say in office status whether it is level, and make the landing's three bale calls one helper call, measured in everyday use before and after
