# Notes: 2026-10-23-helper-starts-001 (office-src 0.29.0)

`office status` starts one Python helper where it started 17, the
walk-in three where ten, a plain start on a project twelve where 23, its
landing eleven where 19 (a landing that sorts drops and mints their
folders about 29 where 45, test_sort's count); the `python3 -c`
one-liners a land ran to read back its plan and its outcome are four
where they were about 25. In this sandbox (two cores, Python 3.13.17,
the same sandbox throughout) `office status` took 0.5 seconds where it
took 2.3 in everyday use and 0.26 where 1.3 with the suite's bytecode
cache, a start 2.6 seconds where 4.0, a land 2.7 where 4.2; the whole
suite 652 seconds where 0.28.0's took 894 here (919 tests then, 924 now:
none dropped, five added), the fast tier 56.0 where 64.2.

Nothing the occupant sees changes, with two exceptions said in section 4
and flagged for ratification: the suite is the net, and eighteen
commands were compared byte for byte against the unchanged tree besides.

The pre-flight check said it fits. No probe and no light block: the tree
and the brief answered everything. Every changed path is inside the
forecast. No compaction.

## What I measured first

At the shipped tree (0.28.0), in this sandbox, before any change. The
runner's own words:

- Whole suite: "[run] the suite, side by side: 26 jobs, 919 tests, 894s"
  and "[run] OK (919 tests run)". `time`: real 14m55.9s, user 23m6.8s,
  sys 5m40.5s. (helper-imports' sandbox gave 866 for the same tree; I
  timed `office status` by hand while this run was on, which cost it a
  little. Compare shares, as the brief says.)
- Fast tier: "[run] the fast tier took 64.2s of wall clock, 353 of the
  suite's 919 tests; its budget is 120s", "[run] OK (353 tests run)".

The helper calls per office command, by the worker's strace method
(`strace -f -e trace=execve,clone,clone3,fork,vfork` over `tests/run.sh
test_sort --jobs 1`, each `pylib` python3 charged to the nearest
`bin/office` ancestor; my parser is this session's scratch tool, not
shipped). It reproduces helper-imports' table to the call, and adds the
`python3 -c` one-liners, which that table left out:

| verb | commands | helper calls | per command | one-liners | modules |
|---|---:|---:|---:|---:|---|
| land | 3 | 134 | 44.7 | 75 | helper 93, bale 19, sort 11, drafting 5, watches 3, door 2, deliver 1 |
| start | 11 | 80 | 7.3 | 26 | helper 54, bale 16, drop 5, door 2, sort 2, drafting 1 |
| open | 6 | 58 | 9.7 | 0 | helper 52, bale 6 |
| drop | 9 | 54 | 6.0 | 9 | helper 36, drop 18 |
| walk-in | 3 | 30 | 10.0 | 0 | helper 24, bale 6 |
| moves | 3 | 26 | 8.7 | 0 | helper 18, sort 5, bale 3 |
| status | 1 | 17 | 17.0 | 0 | helper 12, drafting 1, drop 1, sort 1, bale 1, deliver 1 |
| survey | 4 | 16 | 4.0 | 0 | helper 12, bale 4 |
| the rest | 7 | 33 | 4.7 | 0 | projects, close, blueprint, init, sessions, desk |
| all | 47 | 448 | 9.5 | 110 | helper 327, bale 58, drop 24, sort 21, drafting 8, door 5, watches 3, deliver 2 |

(My parser counts the four `office survey --before-pack` runs a start
makes as survey, and the starts as 11; helper-imports' put them
differently and got 7 starts at 11.4 each. The 80 calls are the same.)

Where a command's calls came from, by the bash function that made them
(a traced copy of bin/office logging `FUNCNAME` on every `pylib`, over
test_land, test_start, test_office and test_home_screen; averages per
command over 28 lands, 70 starts, 12 statuses and 4 walk-ins, so a land
here averages less than test_sort's three full landings):

- land: 13.7 `plan_field` one-liners (one `python3 -c` per field of its
  plan), 3 more on the outcome's JSON and 1.6 each in carry_relays; the
  stamps and skew read twice (stamp, skew, stamp, then again in
  require_current: 5.3 calls), the zone 1.4 times, downloads 0.9, then
  land-plan, land-prepare, land-run, land-outcome, the two sort questions
  (pending, is-sort), door-folder twice (the founding folder, for both
  closings), finished-folder, watches check, land-review, file-pages,
  project-names and file-notes.
- start: six one-liners on the pack's JSON; `folder-facts` 3.7 times on
  the same folder.md (status, goal, lane, class, one call each),
  `project-facts` 2.4 times (the host, then the rides), the stamps and
  skew 3 calls, profile-check, project-names, the zone, start-riders,
  start, record-session, file-sitting-pages, ratifications, door-folder.
- status: the stamps and skew 3 calls, then stamp twice more, name,
  profile, survey-age, the zone, include-group, catalogs, folders, filed,
  and one call each of drafting, drop, sort, bale and deliver.
- walk-in: the zone 2.5 times (the head reads it twice, and office week
  again), name, the stamps and skew, profile, install-lines, desk, the
  calendar's space, recent-notes.

What a call costs here, CPU, the median of 15:

| call | with the suite's bytecode cache | no cache (everyday use) |
|---|---:|---:|
| `python3 -B -P -S -c pass` | 12.0 ms | 11.6 ms |
| `office_helper vercmp` | 43.1 | 98.1 |
| `office_bale status-lines` | 63.3 | 191.8 |
| `office_helper batch` of 12 vercmp | 47.5 | 96.1 |

Two things these say. A batch of twelve reads costs one read plus
0.3 ms each: the whole of a helper call but the read is the interpreter
and the modules, as helper-imports measured. And in everyday use there is
no bytecode cache: `pylib` runs with `-B` and the install is never
written, so every call compiles the module it loads from source
(office_helper.py, 3,800 lines, about 55 ms; office_bale.py, 5,200,
about 130). The suite's numbers (42 ms a call) are the cached ones; the
occupant's status at 0.28.0 was 17 compilations of office_helper.py.
That is where his 1.6 seconds went, and it is the proposal at the end.

## What changed, in the order it paid

### 1. Several reads in one helper call: `office_helper batch`

`batch COUNT [-q|-m] [MODULE:]SUBCOMMAND ARGS...`, repeated, runs each
call in the batch's process as its own process would have run it: the
named module's `main(argv)` (office_helper itself, or a sibling by its
short name: bale, drafting, drop, sort, watches, digest, door, deliver,
home, meeting, planner, probe, letterhead), its stdout captured at file
descriptor 1 (so a write through `sys.stdout.buffer` or by a child
process is captured too), its stderr inherited, discarded (`-q`, the
call's `2>/dev/null`) or merged into its stdout (`-m`, its `2>&1`), a
SystemExit read as the interpreter reads it and an uncaught exception
printed as a traceback with exit 1. It prints one record per call:
`RC<TAB>LINES` and then that many lines, the output's trailing newlines
dropped first, as `"$(call)"` drops them. The capture is a memfd (a
temporary file where the platform has none). A sibling imported into the
batch is imported once and kept for its other calls; the batch's own
office_helper is the running module (whatever runpy named it).

In bin/office, `batch_call ARRAY ...` appends one call to a batch (its
token count first, so no separator token is needed and an argument may
be anything), and `batch_run VAR... -- CALLS...` runs the batch in one
`helper` call and reads each record into its variable, with `VAR_rc` its
exit code; a record the process never printed (it failed to start, or
died) reads as exit 2 and nothing, so a caller that checks `VAR_rc` sees
it as it saw the call failing. `batch_read` is the record reader, a
`read` loop; nothing is `eval`ed.

The batches made, and why each read is in one (no write or question
between them, and no read depending on another's answer):

- **status**: all fourteen reads in one call, the stamps and skew first
  so a floor plan with no stamp refuses as it did; the lines each read
  printed itself (folders, filed, drafting, in-tray, handbook, bale,
  letterhead) are printed from its answer, so `office status` is one
  helper start.
- **the walk-in**: the head's five (name, zone, stamps and skew, profile,
  install-lines) in one; the page's desk, week and recent-notes in a
  second, since desk needs the head's skew and founded, and week the
  head's zone. `office week`'s own read, `has_space calendar`, stays a
  third (a `helper get`); it decides whether the week read is in the
  batch at all. The home screen (a terminal) uses the head's batch, then
  `home page` as before.
- **start**: `require_current_founded`, the skew, the profile and (for
  start) the project names in one call, at the top, where require_current
  and warn_if_unfounded sat together (five verbs had the pair; all five
  use it now). Then, once the folder is known, its facts, which folder
  is the founding one, the profile (for the founding door) and the out
  tray's setting in one call: the facts were four `folder-facts` calls on
  one folder.md, read once now (`fact_of` picks a key from the answer);
  the founding-door reads ran only in their condition and run always
  now, both reads of files start does not write. A planner sitting's
  `planner_asked` writes the folder's Asked section between the status
  fact and the goal fact, so on that path the facts are read again after
  it (they are in the field block, which that write does not touch, but
  the rule is kept rather than argued). The survey refresh the pack runs
  (`office survey --before-pack`) reads the survey's age and its writers
  in one call; its second survey-age, after the page is written, stays
  after it. The pack's JSON is read once (section 3).
- **land**: the zone and the downloads in one call, at the top; the two
  sort questions (`sort pending`, `sort is-sort`) in one, is-sort being a
  check on the id alone; the two closings' three reads (the founding
  folder, the profile, finished-folder) in one, `land_close_folders`,
  made after the ratification writes folder.md: the founding folder
  closes only when it is the folder that landed, and then offer_close
  reads nothing of it, so no read there follows a write. file_notes reads
  the project names alone when the zone was read (a land has), the two in
  one call otherwise (office sessions --pages).
- **the stamps and skew** everywhere: section 2.

Reads I left single, and why: `land-plan`, `land-prepare`, `land-run`,
`land-outcome` (bash logs a line between prepare and run, and run is
bale apply itself); `file-pages`, `file-notes`, `record-session`,
`file-sitting-pages`, `ratifications`, `ratify` (writes, each committed
before the next); `land-review` (between land_moves, which may write,
and the after-land actions); `watches check` (after the closings, which
move folders); `start-riders`, `start`, `project-facts` (asked questions
sit between them and the batches); `survey-render`, then `survey-age`
(a read of the page just written); the zone in a start (its one read
comes after the pack: a bad zone's warning would move up the screen if
it joined the folder batch, section 4 says why that mattered); and
everything in `cmd_open` and `cmd_moves`, which land runs for a sort's
minted folders (normalize-field per flag, next-number, render-template,
folder-set-field, folder-event, `bale writers`: most are writes, and the
verbs are outside the four the brief names). `office drop`, `office
open`, `office survey` and the rest gained only the skew read.

### 2. The stamps and the skew in one read, once per command

`office_helper skew-report MANIFEST INSTALL_VERSION MIGRATIONS` prints
`built_from<TAB>migrated_to` and then what `skew` prints for the
migrated_to stamp. Nearly every command read these as three calls
(`skew_report`: stamp, then skew; `require_current`: stamp again;
`cmd_status`: stamp twice more). `skew_read ROOT` in bin/office reads it
once into `OFFICE_BUILT`, `OFFICE_MIGRATED`, `SKEW_REPORT` and
`SKEW_STATE`; `skew_take` is the same reading for a command that read it
in a batch; `skew_report` and `require_current` are thin over them, and
`skew_judge` is require_current's judgment. The stamp line is printed
before the migrations are planned, so a caller still tells "cannot read
the version stamp" from "cannot plan migrations" by whether the first
line arrived (the two die lines are as they were).

The read is kept for the command (`SKEW_OF`): a verb's own code run
inside another in a subshell (land running `cmd_moves`, `cmd_close`,
`cmd_open`; upgrade's renovation running `cmd_open` and `cmd_start`)
answers from the first read. `skew_forget` after each `set-migrated` in
run_migrations makes the next read fresh; nothing else writes the stamp
in a command's lifetime (office init writes it before anything reads
it). The floor plan's timezone name (`office_tz_named`, with
`office_tz_keep` for a batch that read it) and a project's facts
(`project_facts`, for the host and the rides) are kept the same way,
and for the same reason: the floor plan's timezone line and its
[projects] table are written by init, upgrade and `office projects`
alone.

### 3. A JSON answer read once: `json_read`

`json_read SOURCE VAR=KEY...` reads one JSON document (a file, or stdin
as `-`) in one `python3 -B -P -S -c` start and prints its fields in the
same records `batch_read` reads: a string or number as is, a list one
item per line, true as `yes`, false or null as nothing, `KEY#` a list's
length, a dotted path for nesting (`place.host`, `relays.0.to`). A
missing key is an error on stderr and `VAR_rc` 1 unless the key ends in
`?`; a document that does not read is an error for every field. The
callers that checked a read (`|| die "could not read what office start
packed"`) check `sid_rc`. Converted: a start's eight reads of the pack's
JSON (sid, tray, warnings, second_desk, request, carried, opener,
sitting), the standalone sort's and the prep's five each, a land's
fourteen `plan_field`s (`plan_read`, read again after each time the plan
is written anew) and five outcome reads, carry_relays' count-and-outcome
and each relay's lines-and-recipient (two reads per relay, from four),
`land-end`'s two, a delivery's four, a blueprint close's four.
`plan_field` is one `json_read` now too, for the callers that read one
field at a time (the hosted after-land runner, office deliver). The semantics mirrored: `v.get(k)` paths read `?` (nothing
when absent), `["k"]` paths refuse, `x or ""` is the null rule, lists
join on newlines, bools print yes or nothing.

The one-liners that stay single (short_slug's, to_clipboard's two, a
withdrawal's, deliver_show's, the delivery's author read, the relay
block's, probe_field, the profile stub's `python3 -`) run with `-B -P
-S`, as the helpers do: a `python3 -c 'import json,sys'` start measured
28 ms wall here against 34, so grouping (one start instead of five to
fourteen) was the lever where a group existed, and the flags where none
did, as the brief offered.

### 4. What the occupant could see: two things

Byte for byte, every verb's stdout, stderr and exit code are as they
were: the suite is the net (924 tests), and a scratch script ran the same
eighteen commands against both trees in the suite's own world (a
status, the walk-in, a project start, status and walk-in again, its land,
status and walk-in again, a `start new --words` on the project, a land
that finds no response, its held landing, the walk-in, an office
session's start and land, status, walk-in, desk, week) and compared the
records: identical but for timestamps and a fake bale's random directory
name. Two things differ, and are deviations to ratify:

1. **The walk-in says a zone this machine lacks once.** The warning the
   office prints for a zone not in the zone database (the occupant's
   America/Indianapolis on Ubuntu 24.04 without tzdata-legacy, by
   test_second_trip) came twice from a walk-in in an office with a
   calendar: once from the head, once from office week's own read of
   the zone. The page's batch takes the head's zone, so it comes once.
   Every other command warns as it did: the zone's name is read once,
   but each `office_tz` call still checks it and warns (a land says it
   twice, as before, at its top and when it files the notes). The
   eighteen-command comparison was repeated with a zone database that
   lacks the office's zone (TZDIR at an empty directory): identical. The
   tests use assertIn, so none pinned the count; I judged the second copy
   noise, not information.
2. **A batched read's stderr comes before the batch's stdout lines.** A
   read that prints to stderr as it runs (an error, and only then) did so
   between the stdout lines of the command before and after it; in a
   batch it prints while the batch runs, before the command prints any
   line from the batch's answers. On a terminal, where both streams
   interleave, an error line of `office status`'s include-group check,
   say, appears above the `office:` line rather than below `migrated:`.
   The lines and both streams are unchanged; only their order across
   the two streams, and only when a read fails. Piped (and in every
   test) nothing changes. I chose this over capturing stderr and
   replaying it, which would have delayed every error until the batch
   ended and still not restored the interleaving.

Besides these, three things I checked because they could have differed:
a batched read that ran only under a condition before (the founding
door's door-folder and profile-check in start; is-sort when pending
answered) runs always now, all of them reads of files the command does
not write there; an argparse error inside a batch names the right
program (every module sets `prog` explicitly); and a module imported
into a batch beside office_helper is the sibling's own module object,
as it is when run alone through runpy (office_host's `_REACHED` is
shared across a batch's calls, which is what its file does across
processes: one command reaches a host once).

### 5. Smaller things

- `require_current` and `warn_if_unfounded` sat together in five verbs
  (survey, open, start, and start's --sort and --prep); each is one
  `require_current_founded` call now, and start's reads the project
  names in the same batch.
- `offer_close` and `close_founding_folder` take what `land_close_folders`
  read as arguments; their bodies are as they were.
- `land_files` takes the plan's response_here and project as arguments
  rather than reading the plan twice more.
- The `-rc` variables `json_read` and `batch_run` set are declared local
  beside the variables they belong to at every site.

## Tests

- **New, 5.** tests/test_suite_clock.py `TestFewerHelperStarts` (3):
  a batch of nine calls (gets, a stamp, a profile check, a failing get,
  a bad vercmp, skew-report, two `sort:is-sort`, an argparse error)
  prints each call's record as the call alone prints its stdout and
  exit code, with the lone call's last stderr line in the batch's
  stderr; `-q` discards and `-m` merges; a failing call is its own exit
  and the batch goes on; the command line's five malformed shapes
  refuse; `parse_batch` reads modules and modes. `skew-report` is the
  stamps then skew's report, and the stamps come before a planning
  failure. bin/office's `batch_run` and `json_read`, run from the
  script's own definitions, read a batch's three answers and a
  document's nine fields (lists, bools, null, a nested path, a length, a
  missing key, an optional one, stdin, a document that does not read)
  into variables with their exit codes. tests/test_land.py
  `TestFewerHelperStarts` (2): a python3 on the Env's PATH ahead of the
  real one logs every interpreter a command starts; `office status`
  starts one helper and no one-liner, the walk-in three, a plain start
  on a project twelve (three of them batches) and one one-liner, its
  landing eleven and four one-liners. All five fail on the unchanged
  tree (no `batch` or `skew-report` subcommand; 17 starts for a status).
- **Changed:** none. **None dropped or merged.** 919 at 0.28.0 are all
  there by id; discover finds 924 and the runner's plan matches it.

## Run results (this sandbox, two cores, the same sandbox throughout)

| run | tests | result | wall clock |
|---|---|---|---|
| whole suite, 0.28.0 as shipped | 919 | "[run] OK (919 tests run)" | "894s" (real 14m55.9s; user 23m6.8s, sys 5m40.5s) |
| fast tier, 0.28.0 | 353 | OK | "the fast tier took 64.2s of wall clock, 353 of the suite's 919 tests" |
| the four modules, first try at 0.29.0 (require_current_founded's `names` local shadowing the caller's) | 277 | 6 modules FAILED on `names: unbound variable` (fixed) | |
| the four modules and test_second_trip, test_sort, 0.29.0 | 277 | "[run] OK (277 tests run)" | |
| six modules after the skew cache (land, office, sort, desk_verbs, founding_door, front_door) | 300 | "[run] OK (300 tests run)" | |
| fast tier with the new classes, 0.29.0 (one line short of the final bin/office: the walk-in's zone kept for later reads) | 358 | "[run] OK (358 tests run)" | "the fast tier took 60.4s of wall clock, 358 of the suite's 924 tests; its budget is 120s" |
| whole suite, the same bytes | 924 | "[run] OK (924 tests run)" | "635s" (real 10m36.6s; user 15m52.0s, sys 4m21.9s) |
| fast tier with the new classes, 0.29.0 final bytes | 358 | "[run] OK (358 tests run)" | "the fast tier took 56.0s of wall clock, 358 of the suite's 924 tests; its budget is 120s" |
| whole suite, 0.29.0 final bytes (after it only the record's numbers were filled in) | 924 | "[run] OK (924 tests run)" | "652s" (real 10m53.6s; user 16m19.6s, sys 4m31.5s) |

`office status`, the walk-in (piped: the page), a start and a land in the
suite's own world (test_land's LandCase: an office scoping one project
with a fake bale), wall clock, status and walk-in the median of 7, the
start and the land once; two rounds, this sandbox idle:

| command | 0.28.0, no cache | 0.29.0, no cache | 0.28.0, suite cache | 0.29.0, suite cache |
|---|---:|---:|---:|---:|
| office status | 2,330 / 2,371 ms | 530 / 523 | 1,335 / 1,257 | 255 / 265 |
| office (the page) | 1,477 / 1,500 | 856 / 846 | 978 / 892 | 491 / 416 |
| office start | 4,154 / 3,852 | 2,598 / 2,538 | 2,516 / 2,420 | 1,707 / 1,601 |
| office land | 4,369 / 4,147 | 2,770 / 2,540 | 2,520 / 2,396 | 1,678 / 1,378 |

"No cache" is everyday use (the install is never written, `pylib` runs
with `-B`); "suite cache" is the runner's bytecode cache, the suite's
condition and helper-imports' 42 ms a call. The occupant's 1.611-second
status (2026-10-22, 0.26.0, a faster machine than this sandbox) is the
no-cache column: expect about a quarter of it back as the whole, by the
share here (2.3 to 0.5).

Under strace, `tests/run.sh test_sort --jobs 1` at the final tree (the
same 18 tests and 47 office commands):

| verb | commands | helper calls | per command | one-liners | modules |
|---|---:|---:|---:|---:|---|
| land | 3 | 86 | 28.7 | 12 | helper 51, bale 19, sort 7, drafting 5, watches 3, deliver 1 |
| start | 11 | 45 | 4.1 | 4 | helper 21, bale 16, drop 5, sort 2, drafting 1 |
| drop | 9 | 45 | 5.0 | 9 | helper 27, drop 18 |
| open | 6 | 40 | 6.7 | 0 | helper 34, bale 6 |
| moves | 3 | 20 | 6.7 | 0 | helper 12, sort 5, bale 3 |
| survey | 4 | 12 | 3.0 | 0 | helper 12 |
| walk-in | 3 | 9 | 3.0 | 0 | helper 9 |
| status | 1 | 1 | 1.0 | 0 | helper 1 |
| the rest | 7 | 26 | 3.7 | 0 | init, projects, close, blueprint, sessions, desk |
| all | 47 | 284 | 6.0 | 25 | helper 185, bale 46, drop 23, sort 17, drafting 7, watches 3, deliver 1, door 1 |

Against 0.28.0's 448 helper calls and 110 one-liners: 284 and 25. The
three lands here sort drops and mint their folders (office moves, then
office open's own code), which is most of what a land still starts
(normalize-field per field, folder-facts, bale writers, next-number,
render-template, folder-set-field, folder-event: nearly all writes, and
verbs outside the four); a plain landing in the suite's land world is
eleven helper starts where it was 19, and a plain start twelve where 23
(test_land TestFewerHelperStarts pins both).

Where the time goes by test file: summed test time, the 635-second run
against 0.28.0's (the 652-second run on the final bytes differs by one
line of bin/office; four jobs share two cores, so a test's time includes
waiting for a core):

| test file | tests before | seconds before | tests after | seconds after | change |
|---|---:|---:|---:|---:|---:|
| test_land | 49 | 337.3 | 51 | 233.0 | -31% |
| test_return_trip | 31 | 257.3 | 31 | 154.1 | -40% |
| test_probe | 43 | 232.2 | 43 | 155.7 | -33% |
| test_third_trip | 34 | 220.5 | 34 | 148.2 | -33% |
| test_audience_line | 35 | 213.0 | 35 | 172.4 | -19% |
| test_desk_verbs | 53 | 194.0 | 53 | 132.0 | -32% |
| test_front_door | 38 | 191.9 | 38 | 137.5 | -28% |
| test_second_trip | 35 | 180.2 | 35 | 111.2 | -38% |
| test_founding_door | 23 | 164.6 | 23 | 118.4 | -28% |
| test_start | 42 | 161.2 | 42 | 123.6 | -23% |
| test_drafting_table | 27 | 156.6 | 27 | 101.7 | -35% |
| test_planner_from_words | 27 | 154.5 | 27 | 114.2 | -26% |
| test_office | 119 | 151.8 | 119 | 110.6 | -27% |
| test_drop | 32 | 134.0 | 32 | 97.4 | -27% |
| test_out_trip_to_host | 42 | 132.4 | 42 | 109.1 | -18% |
| test_watches_digest | 47 | 101.8 | 47 | 84.4 | -17% |
| test_sort | 18 | 85.6 | 18 | 54.0 | -37% |
| test_project_on_host | 41 | 73.4 | 41 | 53.9 | -27% |
| test_meetings_view | 22 | 72.6 | 22 | 52.6 | -28% |
| test_clean_delivery | 19 | 66.0 | 19 | 44.5 | -33% |
| test_one_door | 15 | 63.6 | 15 | 44.0 | -31% |
| test_read_side | 52 | 63.3 | 52 | 52.6 | -17% |
| test_home_screen | 14 | 58.2 | 14 | 41.0 | -30% |
| test_suite_clock | 49 | 21.3 | 52 | 23.9 | +12% |
| test_filed_append_only | 12 | 0.6 | 12 | 0.6 | -2% |
| all | 919 | 3487.8 | 924 | 2470.6 | -29% |

validation.sh, rehearsed twice:

- On a staged copy (the request's tree, files/ over it, apply.sh's chmod,
  the manifest beside it for the epilogue): every check passed and every
  claim agreed with its verdict. The fast tier with this session's
  classes named after it was "OK (358 tests run)" in 59 s, under its 120
  s budget; the script took 57 s in all, and wrote nothing but its logs
  (no __pycache__: the syntax check parses, it does not compile to
  disk). The whole suite is behind `--slow`, claimed pass on the final
  run above.
- On the request's tree, unchanged, the assertions that test this change
  fail, as they should: the record (four: VERSION, RELEASES, the front
  sheet, README), the batch and skew-report (two), bin/office's functions
  and status's one batch (two), the one-liners' flags, and the fast tier,
  which stops before running on the class names it does not know. The
  syntax checks and the exec bit pass on both, deliberately.

## Where the time goes now

A plain land is eleven helper starts: the skew, which session is out,
the four bale calls that are the landing itself (plan, prepare, run,
outcome), the letterhead's review and the watches after the closings,
and three batches; with pages to file, the two writes committed before
the next (file-pages, file-notes). A plain start is twelve: three
batches, the riders, the pack, its survey (the page rendered, then its
age), the project's facts, the zone, and the three writes after the pack
(record-session, file-sitting-pages, ratifications). These are the
writes and the questions between which the brief said a batch must not
cross; the next cut is not in bin/office's reads.

It is in the compile. In everyday use a helper call compiles its module
from source every time: `office_helper vercmp` is 98 ms of CPU here
without a bytecode cache and 43 with one, `office_bale status-lines` 192
and 63. `pylib` runs with `-B` and the install is never written by a
command, so nothing ever caches the compiled code the way the suite's
runner does for itself (tests/runner.py seed_bytecode). The proposal
below is that lever; it is install.sh's, which the brief's list of what
may change does not name, so it stays a proposal.

## Decisions to ratify

1. **The two visible differences in section 4**: the walk-in's zone
   warning once rather than twice, and a batched read's stderr lines
   before that batch's stdout lines on a terminal.
2. **`batch` runs sibling modules in-process** (a status is one process
   for office_helper, drafting, drop, sort, bale and deliver), on the
   reasoning in section 4's last paragraph; the alternative, one batch
   per module, would make a status five calls.
3. **The reads kept for a command** (the skew, the zone name, a
   project's facts: section 2), with `skew_forget` after a stamp write.
4. **The founding-door and is-sort reads run unconditionally** inside
   their batches (section 4).
5. **The one-liners**: grouped where a group existed, `-B -P -S` where
   not (section 3).

## Paths outside the forecast

None. Every changed path is under the request's `resolved_scope`
(README.md, RELEASES.md, VERSION, bin, claude, lib, tests). Nothing
under doctrine/, share/, templates/, migrations/ or install.sh changed;
the doctrine states nothing about how many helpers a command starts, and
its rule that the office reads bale's --json surfaces, never its words,
holds through every batch (the bale reads are the same subcommands,
run in one process).

## Proposals

- **What:** compile lib/ at install time, so a helper call reads its
  module's bytecode instead of compiling it: `install.sh` running
  `python3 -m compileall -q lib` into the install's `lib/__pycache__`
  (or into a cache directory the install names through
  PYTHONPYCACHEPREFIX, as tests/runner.py does for a run), and a check
  in `office status` that the cache is level with the sources.
  **Why:** measured above: without a cache a small helper call is 98 ms
  of CPU here and 43 with one, an office_bale call 192 and 63; the
  occupant's install has no cache (`-B`, and commands never write the
  install), so his `office status` compiled office_helper.py seventeen
  times at 0.28.0 and compiles it once now, about 55 ms of its half
  second; a start and a land compile office_helper and office_bale in
  each of their ten to fourteen calls, about a second of the 2.6 here.
  `-B` stays (a command still writes nothing); the compiled files are
  install.sh's, written once beside the sources it copies.
  **Scope hints:** install.sh; bin/office status's install line;
  tests/test_office.py TestInstall. Small; the one question is where the
  cache lives when the install's directory is read-only.
- **What:** `office_bale land` as one subcommand for land-prepare,
  land-run and land-outcome, printing prepare's line itself.
  **Why:** three helper starts per land that are the landing in
  sequence, with one bash log line between the first two; one process
  would save two starts (about 130 ms in everyday use). Small, and a
  change to the read side's surface, so not this session's.
  **Scope hints:** lib/office_bale.py; bin/office cmd_land.

## Handbook

### office-src

- an office command's side-by-side reads go out as one helper call: office_helper batch (COUNT [-q|-m] [MODULE:]SUBCOMMAND ARGS..., repeated) runs each in one process as its own call would run and prints one record each; bin/office batch_call builds the batch, batch_run reads each answer into VAR and its exit code into VAR_rc; a read after a write, or one that needs another's answer, stays a call of its own
- the two version stamps and the skew report are one read (office_helper skew-report), made once per command (bin/office skew_read, skew_take, skew_judge, SKEW_OF; skew_forget after set-migrated); the floor plan's timezone name (office_tz_named, office_tz_keep) and a project's facts (project_facts) are kept per command the same way
- a helper's JSON answer is read back by one json_read (SOURCE VAR=KEY..., KEY? for a key that may be absent, KEY# for a list's length), printing the same records batch_read reads; plan_read reads land's plan; the one-liners that stay single run with -B -P -S
- office status starts one helper, the walk-in three, a plain start on a project twelve, its landing eleven, a landing that sorts drops about 29 (tests/test_land.py TestFewerHelperStarts counts them with a python3 shim on the Env's PATH); tests/test_suite_clock.py TestFewerHelperStarts holds the batch to each call run alone
- in everyday use a helper call compiles its module from source (no bytecode cache: pylib runs with -B and the install is never written): about 98 ms a small call here where the suite's cache gives 43; office status took 0.5 s here where 2.3 at 0.28.0

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.29.0
every `office` command starts fewer Python helpers: `office status` starts
one where it started 17, the walk-in three where ten, a start twelve
where 23, a land eleven where 19, because the reads a command made one
after another now go out as one call, and what a helper answers is read
back once. In the worker's sandbox `office status` took half a second
where it took 2.3, a start 2.6 where 4.0, a land 2.7 where 4.2, and the
suite 652 seconds where 0.28.0's took 894. Nothing you use changes, with
two small things said differently: the walk-in mentions a timezone this
machine lacks once instead of twice, and when a read fails inside a
batch its error line comes above the command's lines rather than between
them. The next lever is the
compile: with no bytecode cache on your machine, each helper call
compiles its module from source, about half of what a call costs.

## Walkthrough

### What changed

- **Several reads in one helper call** (lib/office_helper.py `batch`,
  `parse_batch`, `run_call`, `batch_record`, `BATCH_MODULES`; bin/office
  `batch_call`, `batch_run`, `batch_read`), used by `cmd_status`,
  `walk_in_head`, `walk_in`, `require_current_founded`, `cmd_start`,
  `refresh_survey`, `cmd_land`, `land_moves`, `land_close_folders`,
  `file_notes`.
- **The stamps and the skew in one read, once per command**
  (lib/office_helper.py `skew-report`, `skew_lines`; bin/office
  `skew_read`, `skew_take`, `skew_judge`, `skew_forget`, `skew_report`,
  `require_current`, `unfounded_judge`, `require_current_founded`), and
  the zone name and a project's facts kept per command (`office_tz_named`,
  `office_tz_keep`, `office_tz_resolved`, `project_facts`, `project_host`).
- **A JSON answer read once** (bin/office `json_read`, `plan_read`,
  `plan_field`; the readers in `cmd_start`, `start_sort`, `start_prep`,
  `cmd_land`, `carry_relays`, `cmd_deliver`, `cmd_blueprint_close`), and
  `-B -P -S` on the one-liners that stay single.
- **Tests:** tests/test_suite_clock.py `TestFewerHelperStarts` (three),
  tests/test_land.py `TestFewerHelperStarts` (two).
- **The record:** README (Layout, the helpers' paragraph), RELEASES
  0.29.0, VERSION, the development record's front sheet (The suite's
  clock, Recent changes).

### Why

Your words of 2026-10-12, still in force: "The biggest barrier to this
is honestly the extended time that using office allots to me".
helper-imports made each helper start about half as costly and left the
count alone; its numbers said the count still mattered (a status 17
starts, a land 45, most of each start paid before it reads anything),
and the sitting sent this session on them. The reads a command made one
after another now go out together.

### How to explain each piece

- **One call for several reads:** a command used to start a fresh Python
  for every question it asked about the office (is the stamp current, is
  the profile complete, how old is the survey, ...), seventeen times for
  `office status`. Now it asks all of them in one start, and each answer
  comes back labelled.
- **The stamps and skew once:** nearly every command checked the
  office's version against the install three times over, in three
  starts; now once, in one, and a command's inner steps reuse it.
- **A JSON answer read once:** when a helper answered with a block of
  fields, the command started another Python per field to pick each one
  out, fourteen times for a landing's plan; now one start picks them all.

### Questions a reviewer will ask

- *Does anything change for me?* Two small things, both said in the
  release note: the walk-in mentions a timezone your machine lacks once
  rather than twice, and if a read inside a batch fails, its error line
  appears above the command's lines rather than between them. Everything else is byte for byte what it was: the suite,
  and eighteen commands compared against the old tree.
- *Why is status still half a second if it is one helper call?* Your
  install has no bytecode cache, so that one call compiles the helper's
  3,800 lines from source, and bash, git and the survey do the rest.
  The proposal in the notes (compile at install time) is the next cut.
- *Why not one call for a whole land?* A landing is bale apply with
  reads before it and writes after it, each committed; a read after a
  write has to come after it, and a question to you has to be asked
  before what depends on it. What sat side by side is batched; the rest
  is the landing's own order.
- *Did any test go?* No. 919 then, 924 now; discover and the runner's
  plan agree.
- *Is the suite at two thirds?* Near it: 652 seconds where 0.28.0's took
  894 on this sandbox, 73 percent, against the projection's 67 (an
  earlier run, one line of bin/office short of the final bytes, took
  635); the tests' summed time fell 29 percent, every file but
  test_suite_clock (five tests added, two of them starting interpreters)
  between 17 and 40.

### A hand test

Run these on your WSL terminal, one line at a time.

1. After this lands, `office land` runs `./install.sh` for office-src and
   starts the detached suite. When it ends, `cat
   ~/.local/state/office-src/suite/latest/verdict` should read `OK
   <time>: 924 tests passed in <N>s`.
2. `time office status` in any office: compare with the 1.611 s the
   sitting's probe measured on 2026-10-22; expect about a quarter of it.
3. `grep -c 'batch_call calls' ~/office-src/bin/office` shows the batched
   reads (about 40 lines); `office status 2>&1 | head -3` reads as it did.

## Delivery

- to: nobody: office-src has no audience

### Commit

Cut the helper starts per command: side-by-side reads in one call

Every office command started a Python helper per question it asked
about the office (office status 17, a start about 11, a land about 45),
and about 35 ms of each start, or 95 with no bytecode cache, was the
interpreter and the modules, paid before the read. The reads a command
makes side by side now go out as one office_helper batch call, which
runs each subcommand, of office_helper or a sibling module, in one
process exactly as its own call would run and prints one record each;
bin/office builds a batch with batch_call and reads it back with
batch_run. The two version stamps and the skew are one read
(skew-report), made once per command; a helper's JSON answer is read
back by one json_read rather than one python3 -c per field, and the
one-liners that stay single run with -B -P -S.

office status starts one helper, the walk-in three, a plain start on a
project twelve where 23, its landing eleven where 19. Every verb's
output, exit code and side effects are as they were, but for the
walk-in's zone warning said once rather than twice, and a failed batched
read's error line coming above the command's lines on a terminal rather
than between them. In the worker's two-core sandbox office status
took 0.5 s where 2.3, a start 2.6 s where 4.0, a land 2.7 where 4.2, the
whole suite 652 seconds where 894 and the fast tier 56.0 where 64.2,
every test kept and five added (tests/test_suite_clock.py and
tests/test_land.py TestFewerHelperStarts).

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.

## Structure

- title: Fewer helper starts
- size: medium
- goal: Cut how many Python helpers each office command starts, the side-by-side reads batched into one call, measured before and after in one sandbox, every verb's behaviour unchanged
