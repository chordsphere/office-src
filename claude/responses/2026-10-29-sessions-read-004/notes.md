# notes: 2026-10-29-sessions-read-004

Wave 1, lib only. `office sessions FOLDER` now reads past a project the
office cannot read: that project is one line, the search goes on, the
folder's own project is searched first, and the stop fires only when a
session was not found while some project could not be read. Beside it,
a suite test that RELEASES.md's headings and the front sheet's releases
are the same versions. No VERSION bump, no README, RELEASES, doctrine,
bin/office or front sheet change; the release paragraph is under the
Walkthrough, as the brief asks.

I built from the request's tree as shipped (0.37.0). Both forecast files
hash to the request's `base_files` stamps. No probe was needed: the
failure needs no fact from the machine, since the fake bale refusing in
a project it has no captures for is the same path (bale exits non-zero
in a directory that exists) that a broken clone takes.

## What the code did, read at 0.37.0

The brief's reading holds. The anchors match (locate at 1675, not 1670,
and render_folder_sessions at 1697). One thing it did not say: the same
failure also hit hosted projects twice. A host that does not answer was
said once at the top by the prefetch loop, then again under every
session, because locate's `readable(p)` succeeds for a hosted place
(the reach happens at the first bale read) and `known_sids` then raised
out of locate. Running my new tests against the old code shows it: the
host's whole line three times and exit 1, with both sessions sitting in
the project on this machine.

## Decisions to ratify

1. **A project is read only when a search reaches it.** The new helper
   `project_records` reads one project in its own try: its place, its
   status (the sids its records name), and for a hosted project the one
   dossier batch the old prefetch loop sent. It caches the result, or
   the failure's words, for the rest of the rendering. So the prefetch
   loop up front is gone. Each host still costs the same two
   connections, a status and one batch (test_project_on_host's count
   still holds), but now only when a search needs that host. That is
   what "an unrelated broken clone is never even opened" takes. With a
   lane whose project holds every recorded session, no other project is
   touched: no bale call in a broken clone, no connection to a host
   that is down (both tested).
2. **The search order.** The lane's project first. Then every other
   project's status is read (each in its own try), and the ones whose
   records name the sid are tried before the rest, as before. Without a
   lane, or when the lane's project does not hold the sid, every project
   is still read for that sort. So the broken project's line appears in
   that case even when every session is found, and the exit is 0. I kept
   the sort because it saves dossier reads, and the brief keeps it.
3. **Which failures pass a project over.** A status failure, or a
   dossier read that fails at the project (kinds `missing`, `path`,
   `refused`, `unreachable`: bale refused there, the directory went, the
   host stopped answering), passes the project over for the rest of the
   rendering. It is said once. Any other dossier failure (`output`,
   `key`: bale answered about this one session in words that do not
   read, such as a record it could not parse) stays that session's own
   `    cannot read: ...` line, as before. The project stays in the
   search for the other sessions. That way one bad record does not hide
   a project's other sessions, and a broken clone is still one line.
   This split is `PROJECT_WIDE_KINDS` in lib/office_bale.py. Change the
   tuple if you would draw the line elsewhere.
4. **The words.** The project's line, unindented, after the sessions and
   just before the folder's tally, once per project in the floor plan's
   order: `attic: not read: bale status --json refused in /path (exit
   97): ...` (bale's own words follow, as BaleError carries them). An
   uncertain miss, under its sid: `    not found in the projects that
   could be read; attic could not` (several projects are comma-separated,
   sorted). A certain miss keeps its old words: `    not in the records
   of any project this office scopes`. The old prefetch-loop line (`
   NAME: cannot read: ...`, at the top) is gone. It is replaced by the
   new line, which a hosted project now gets too.
5. **The exit.** render_folder_sessions' second value is now the count
   of uncertain misses: sessions not found while some project could not
   be read for them, either passed over or failing its record for that
   sid. main's `3 if bad else 0` and bin/office's mapping of 3 are
   unchanged, so the stop fires exactly then. bale missing from PATH
   still returns 1 there, so the verb still stops (the existing test
   holds that). A session whose record does not read and that no other
   project holds counts as uncertain. Its absence is in doubt.
6. **The tally line.** `not found: ...` now lists every session not
   found, the uncertain ones too. Before, a session under `cannot read`
   was counted neither found nor not found.
7. **Where the lane is read.** In render_folder_sessions, from the folder
   page (`folder_lane`, over `oh.folder_lane_project`), so the reader's
   argv and bin/office stay as they are. A lane naming a project the
   office does not scope means no project goes first. That gets a debug
   line, as does a lane that cannot be read.
8. **The releases test** is its own class,
   `TestTheReleasesMatchTheFrontSheet`, right after
   TestTheLandFlagsRecord, not a method inside it. The record class is
   0.37.0's record, and this rule outlives it. The parsing is three
   module-level functions (`release_headings`, `front_sheet_releases`,
   `releases_differ`) so validation.sh can use them on the tree's own
   files. The class has a second test that runs the rule on a small
   made-up pair: a lost patch heading is named, and so is a release
   written on one side only. It also fails if either record parses
   empty, so a change of shape cannot pass on two empty sets.

## Outside the write forecast

- `tests/test_sessions_read.py` (new). The brief says the sessions
  verb's tests go beside the existing ones when they are in test_land.py,
  and in a new module otherwise. They are in tests/test_read_side.py
  (`TestFolderSessions`), which no forecast names, so this is the new
  module. It imports test_read_side's fake bale and world pieces and
  test_project_on_host's `HostedCase` (no test methods of its own, so
  nothing runs twice), and holds one class per item: an unreadable
  project is a line, the folder's own project first, `locate` against a
  plain-records reader, and a host that does not answer.

Every other path is in the forecast. No sibling's path is touched.

## Doc lines this makes stale

I looked for a sentence saying every project is searched, or that one
unreadable project stops the verb, in README.md, the usage text
(`usage_sessions`), doctrine/OFFICE.md and the front sheet. There is
none. Nothing is stale in the strict sense. Two lines are now
incomplete, for home-screen-offers to decide on:

- bin/office cmd_sessions, the exit-3 die: "some of this office's
  projects could not be read; the lines above say why". This is still
  true, but it now fires only when a session was not found, so it could
  say so ("a session was not found and some of this office's projects
  could not be read; the lines above say which").
- README.md, the paragraph after the `| office sessions fix-login -`
  example: "`office sessions fix-login` lists what is recorded, and under
  each id what bale records about the session: its outcome, dates,
  claims beside verdicts and exchange rounds." It could gain a sentence
  on the search: the folder's own project first, and a project that
  cannot be read is a line, not a stop. The doctrine's matching line
  (section 13, "in `office sessions FOLDER`, each session with its
  outcome, dates, claims beside verdicts and exchange rounds") is the
  same case.

## Validation

- `tests/run.sh --fast` with this session's tests (test_sessions_read
  whole; test_land TestTheReleasesMatchTheFrontSheet and
  TestTheLandFlagsRecord; test_read_side TestFolderSessions and
  TestLedgerLandedVersions; test_project_on_host
  TestReadSideThroughTheShell and TestReach): passed, observed, 396 tests
  in 46 s of the 120 s budget, on a two-core sandbox.
- The whole suite on the changed tree, observed: 1072 tests, all passed,
  in 406 s with four jobs (1053 at 0.37.0, plus this session's 19).
- The touched modules whole (`--slow`): test_land, test_read_side,
  test_project_on_host, test_sessions_read. Passed, observed, in 78 s.
- Against the old lib/office_bale.py, with the new tests in place, 15 of
  test_sessions_read's 17 fail. The two that pass on both trees are
  guards the brief pins: nothing is written into the folder, and with
  every project read a miss keeps its old words. The releases test
  passes on the unchanged tree by design. The two records agree at
  0.37.0 (41 and 41, the same versions). Its second test and
  validation.sh's releases assertion show it fails when a heading goes.
- validation.sh --slow, rehearsed on a copy of the base with files/ laid
  over it, apply.sh run and the manifest placed as .bale-manifest.json:
  every check passed and every claim agreed, in 2 min 3 s (the fast tier
  45 s, the touched modules 78 s; without --slow it is under a minute).
  The copy afterwards differed from before only by .validation-logs/,
  which the script announces. Run on the unchanged base, the releases
  assertion and the fast tier fail (and the syntax check, since the new
  module is not there). The untouched-files check passes on both trees.
  It is a guard the brief pins.

## Proposals

- **What:** bin/office's exit-3 die for `office sessions FOLDER` names
  the case it now means (a session not found while a project could not
  be read), and README's sessions paragraph says the search order.
  **Why:** the stop now fires only for an uncertain miss. Its words
  still say only that projects could not be read (Doc lines above).
  **Scope hints:** bin/office cmd_sessions' `case $?`, README.md's
  paragraph after the `office sessions fix-login -` example, and the
  doctrine's section 13 line. home-screen-offers holds those files.
- **What:** the walk-in's In flight list and `office projects --ledger`
  could take the same rule: one unreadable project is a line, said once.
  **Why:** they already go on past a project that cannot be read (their
  tests say so), but each has its own words for it (`  NAME: cannot
  read: ...`), now different from sessions' `NAME: not read: ...`.
  One spelling across the renderings would read better.
  **Scope hints:** lib/office_bale.py render_in_flight, render_ledger,
  render_landed, render_versions; tests/test_read_side.py and
  test_project_on_host.py assert the current words.

## Walkthrough

### What changed

- `office sessions FOLDER` reads each project in its own try, only when a
  search for one of the folder's sessions reaches it
  (lib/office_bale.py `project_records`). A project that cannot be read
  is said once, after the sessions (`attic: not read: WHY`), and the
  search goes on through the others.
- The search starts with the folder's own project, the one its lane
  names (`folder_lane`, then `locate`), then the projects whose records
  name the session, then the rest.
- A session not found while a project could not be read says so under
  its id (`not found in the projects that could be read; attic could
  not`), and only then does the verb stop. Every other run exits 0.
- tests/test_land.py `TestTheReleasesMatchTheFrontSheet`: RELEASES.md's
  `## X.Y.Z` headings and the front sheet's `- X.Y.Z (session SID)`
  lines are the same versions.

### Why

A7 of the gaps of 2026-10-28: one broken clone in a project the folder
has nothing to do with made `office sessions 10` fail. The office's
answer about its own folder depended on every project it scopes being
readable, and the only way past was a probe. 0.37.0's worker asked for
the releases check: 87ce51a lost a heading that every gate passed, and
the order test catches only a skipped minor, not a lost patch.

### How to explain each piece

- "One project you can't read is one line now, not a stop: the office
  says which and why, and keeps looking in the others."
- "It looks in the folder's own project first, so most of the time it
  reads one project and nothing else."
- "It stops only when it couldn't find a session and couldn't read
  somewhere it might have been. Then 'not found' isn't certain, so it
  says so."
- "The release history and the front sheet each list every release. A
  test now checks they list the same ones, so a heading that goes
  missing fails the suite at once."

### Questions a reviewer will ask

- Does a broken project still show up when every session is found? Yes,
  unless the folder's lane finds them all first. Without a lane every
  project's status is read to order the search, so the line appears and
  the exit is 0.
- Why is a garbled record not a whole-project failure? It is bale
  answering about one session. Passing the project over would hide its
  other sessions (decision 3).
- Does a host cost more connections now? No. The same status and one
  batch per host, now only when a search reaches it, and none at all
  when the lane's project holds everything.
- Why compare against the front sheet and not git? The front sheet's
  line is owed per VERSION bump and names the session, so it is an
  independent record in the tree itself. A suite test runs on every
  landing and every detached run; a validation pattern runs only where
  a session remembers to write it.

### A hand test

1. In an office scoping two projects, make one unreadable without
   deleting it: `office projects add` a scratch git repo, then break its
   HEAD (`echo junk > SCRATCH/.git/HEAD`), the way distributions-app's
   clone is broken.
2. `office sessions FOLDER` for a folder whose sessions are in the other
   project: every session renders as before, one line after them reads
   `SCRATCH-NAME: not read: ...` with bale's or git's words, and the
   command ends with no error.
3. Give the folder a lane naming the good project (`office open` with
   `--lane`, or the folder's existing lane) and run it again: the
   scratch project is not mentioned at all.
4. Record a session id no project holds (`office sessions FOLDER SID`),
   with no lane: its line says `not found in the projects that could be
   read; SCRATCH-NAME could not`, and the command stops with "some of
   this office's projects could not be read".
5. Mend the scratch repo (or remove it from the floor plan): the same id
   now reads `not in the records of any project this office scopes`, and
   the command ends with no error.

### Release paragraph

`office sessions FOLDER` reads past a project it cannot read. When one
project in the floor plan could not be read (a clone where git cannot
read HEAD, a directory gone, a host not answering), the verb searched
every project, hit that one, and reported the folder's sessions as
unreadable or not found (found 2026-10-28: distributions-app's broken
clone stopped `office sessions 10`, and a probe had to do its job). Now
each project is read in its own try, and only when the search for one
of the folder's sessions reaches it. The folder's own project, the one
its lane names, is searched first, then the projects whose records name
the session, then the rest. So a folder's session is found with one
read in the common case, and an unrelated broken clone or a host that
is down is never even opened. A project that cannot be read is said
once, in one line after the sessions (`distributions-app: not read:
WHY`, with bale's or the host's words), and the search goes on. A
session found renders as it always did. The verb stops (exit 3 from the
reader, bin/office's "some of this office's projects could not be
read") only when a session was not found while some project could not
be read, since only then is "not found" in doubt, and its line says so
(`not found in the projects that could be read; distributions-app could
not`). A record bale holds but cannot parse stays that session's own
`cannot read` line, and its project stays in the search for the others.
lib/office_bale.py `project_records`, `folder_lane` and
`PROJECT_WIDE_KINDS` are new; `locate` and `render_folder_sessions`
carry them, and the hosted batch of dossiers now rides the first read
of each host rather than a loop over every host up front, at the same
two connections per host. And a test that no release heading is lost
again: tests/test_land.py TestTheReleasesMatchTheFrontSheet reads
RELEASES.md's `## X.Y.Z` headings and the front sheet's `- X.Y.Z
(session SID)` lines under Recent changes, the older record, and fails
naming any version in one and not the other, so a heading lost in a
whole-file overlay (what 87ce51a did to 0.33.0's) fails the suite on the
next run, a minor or a patch release alike. Tests:
tests/test_sessions_read.py, new (TestOneUnreadableProjectIsALine,
TestTheFoldersOwnProjectFirst, TestLocate, TestAHostThatDoesNotAnswer),
and tests/test_land.py TestTheReleasesMatchTheFrontSheet. Nineteen new
tests.

## Delivery

- to: nobody

### Commit

office sessions reads past a project it cannot read

office sessions FOLDER read every project's records, and one it could
not read (a broken clone, a missing directory, a host not answering)
made every session of the folder unreadable. Now each project is read
in its own try, only when the search reaches it, the folder's own
project first, then those whose records name the session, then the
rest. A project that cannot be read is said once, in one line after the
sessions, and the search goes on. The command stops only when a session
was not found while some project could not be read, and that session's
line says so.

A suite test now holds RELEASES.md's headings and the front sheet's
releases to the same versions, so a lost release heading fails the next
run.

### Review

office sessions: one unreadable project is a line, not a stop

What to look at: locate's search order (the folder's own project first),
the per-project read that is said once and passed over, which dossier
failures pass a project over and which stay one session's line, and the
exit, which is 3 only for an uncertain miss.

What to try by hand: break a scratch project's HEAD, then list a folder
whose sessions are in another project, with and without a lane naming
that project, and with a session id no project holds.

Deliberately untouched: bin/office, its exit mapping and its words, the
docs, and the other renderings' wording for an unreadable project.

## Structure

- title: office sessions reads past a project it cannot read, and the releases test
- size: small
- goal: Make office sessions FOLDER read a session's record past a project the office cannot read, saying the project in one line and searching the folder's own project first, and add the test that RELEASES.md's headings match the front sheet's releases

## Handbook

### office-src

- office sessions FOLDER reads projects lazily (lib/office_bale.py
  project_records): the lane's project first, then every other project's
  status for the named-first order, each in its own try. A project that
  cannot be read is cached in `unread` and said once after the sessions
  as `NAME: not read: WHY`.
- render_folder_sessions' second value is the count of uncertain misses
  (a session not found while some project could not be read for it), not
  a count of unreadable projects. The reader's exit 3 for folder-sessions
  means exactly that, and bin/office dies on it.
- A dossier BaleError whose kind is in PROJECT_WIDE_KINDS (missing, path,
  refused, unreachable) passes the project over for the rendering. Any
  other kind (output, key) stays that one session's `cannot read` line.
- The hosted dossier batch for office sessions rides each host's first
  read (project_records), not a loop over every host up front. A host
  costs two connections when a search reaches it and none when the
  lane's project holds every recorded session.
- In the suite, a project directory the fake bale (tests/fakes/replay_bale.py)
  has no route for refuses every call with exit 97, which stands in for
  a broken clone. tests/test_sessions_read.py uses it so.
- tests/test_land.py TestTheReleasesMatchTheFrontSheet holds RELEASES.md's
  `## X.Y.Z` headings and the front sheet's `- X.Y.Z (session ` lines
  under Recent changes to the same set. A release session that writes one
  without the other fails it; the parsing is the module's
  release_headings, front_sheet_releases and releases_differ.
