# Notes: 2026-10-26-office-tidy-001 (office-src 0.31.0)

All eight items landed, each in a few lines, none waiting on another.
What you see changes in the four small ways the brief named: a
`structure:` line in `office status` (item 3), a `Bytecode:` walk-in line
and its Next line in one state (item 7), the drafting table arriving with
`office start --sort` (item 5), and the doctrine's words (item 6). Two
items came out a little different from how they were proposed, because
the code said otherwise once I read it (items 2 and 3 below, flagged as
decisions), and the doctrine changed in three more places than item 6's
sentence, each where it pins one of the visible changes (decision 6).

The pre-flight check said it fits, comfortably. No probe and no light
block: the tree, the brief and the survey answered everything. Every
changed path is inside the forecast. No compaction.

## The items, as the code stood and as it stands

### 1. sitting_key joins a sitting's pages by slug

At 0.30.0 `sitting_key` (lib/office_watches.py:283; the sitting's probe
found it at 286 at 0.26.0) joined a page `X-N.md` to `X.md` only when `X`
is a session id (`2026-10-03-plan-4b-sitting-001-3.md`). But office start
files a sitting's pages from the brief's NOTEPAD PAGE markers, and the
planners name them by slug: this very brief carries
`notepad/2026-10-22-after-the-arc-sitting-5.md`, continuing
`...-sitting.md`. Each such page was its own key, so `sittings_after`
(the watches' "N sittings since") counted one sitting of several pages
as several. The planner's `sitting_pages` already joined by slug (`SLUG-N.md`
whose `SLUG.md` is in the notepad); `sitting_key` now does the same,
reading the stems of every sitting page the notepad's history filed
(`sitting_filings` keys each page once all are known). A slug that merely
ends in a number (`2026-10-20-plan-2.md`, with no `2026-10-20-plan.md`)
stays a sitting of its own. The SID-N rule is kept as it was.

What the brief's note on the digest describes ("counted this sitting's
pages as its window's page by the last filed one") is the window's line,
which names the latest filing's page; that is right as it is (the window
opens at the commit that filed the latest page), and I left it.

### 2. every_sitting_carries and the drafting table

The proposal (meetings-view-001) said the planner sitting names the
drafting table on its ride list "even in an office that has none (bale's
start adds it only when it is there)", and that the prep filters it. I
ran both in the suite's world, in an office with no drafting table, before
changing anything: in both, the digest office start writes just before
the pack (`office digest --before-pack`, which runs `od.arrive` first)
brought the drafting table into the office, office_bale's start then
found it and added it to the includes, and `drafting-table/digest.md`
shipped in the request. So the planner sitting's list was right to name
it, and the prep's list was the one that was wrong: it left out a table
that rode.

So I did not make the list name it "only where there is one" at the
moment the list is written, which would have dropped it from the brief
of exactly the sitting that brings it. `every_sitting_carries` names it
with every sitting, as before where there is one, and where there is
none yet as "the drafting table, which arrives in this office with its
digest.md: written just before the pack, ..."; the prep's filter
(lib/office_meeting.py `write_prep`) is gone, so the prep's list now
names what rides. Decision 1. The one case left where the line would say
more than happens: an office with no drafting table whose digest is held
by an open session forecasting the floor plan or bale.toml (the
one-writer rule) or whose digest fails; office start says in its own line
that it left the digest as it was. I did not chase that further.

### 3. office status: a folder still provisional after its sessions landed

`structure:` lines, one per folder, right under the `folders:` line,
nothing at all when there is none (so status is byte for byte as before
in that case):

    structure:  folder 20 (filing-cabinet/2026-10-26-...) still marks title, size, goal provisional, though its one session landed applied: its Structure never came back, or came back off its shape and was not filed

How "landed applied" is read: bale's `applied/SID` tags, with git, in the
office's own repo and each project it scopes (`office_bale
provisional-lines`, `provisional_landed`, `applied_sids`), the way office
deliver already reads them. No bale call, and git runs only when some
folder has a provisional line and recorded sessions. The repos on this
machine are read first, and a project on a host (one connection through
its shell) only while some such folder's sessions are not all found;
that ordering is by reading, since the suite has no host to run it
against. A project that cannot be read is said for a folder it leaves
undecided. A read-only
sitting never tags, so a planner sitting's folder (which writes no
Structure) is never named. A provisional line that does not read stays
folder-check's to name, as before.

Desk and filing cabinet both (decision 2). one-door-002's proposal said
"the desk folders"; the brief's words do not limit it, and the case it
describes lands in the cabinet: a folder that records one session is
closed by `office land` on a terminal when that session lands applied.
The cost is that such a folder stays named: a closed folder moves whole,
and nothing files a Structure into it. If you would rather the cabinet
were left out, it is one condition (`f["space"] == "desk"`), and the
front sheet's known problem says the same either way.

### 4. A response filed twice adds nothing twice

`office land` and `office sessions FOLDER SID --pages RESPONSE` both run
lib/office_sort.py `file_notes`. Filed again:

- Questions and answers: a line already in the folder's section is said
  and left; only new lines are appended, under a `- from SID:` line
  unless the section's last such line is already this session's (so a
  new line is never filed under another session's). All already there:
  "all N line(s) already in FOLDER/folder.md, left as they are; nothing
  filed", and the file is not written.
- Facts: a fact the chapter holds from the same session is the same fact
  whatever day it was filed (the key is the fact and the session id, not
  the `- DATE:` it was filed on). The same words from another session
  are that session's and are filed.
- The front sheet: replaced whole as before, unless the chapter already
  reads as this session's, when it is said and not written.
- The Sort already said "sorted already" and left the page; unchanged.

Nothing filed is rewritten, and a chapter with nothing new is no longer
named among the paths to commit.

### 5. The drafting table arrives with office start --sort

`start_sort` (bin/office) gave the sort its moves page only `if [ -d
"$root/drafting-table" ]`. Now, whenever moves.md is missing, it runs
`drafting arrive --page moves.md`, which makes the table arrive or finish
arriving: README.md and moves.md from the install's templates, the floor
plan's entry as the catalog declares it, bale.toml's trigger, each only
when missing. The one-writer rule is checked over moves.md and, when the
table has not arrived, over `arrival_targets` (the floor plan, bale.toml,
the table's README), as `office digest` checks them. The arrival is
committed alone, "office start --sort: the drafting table arrives, for the
moves page" (the old subject when only the page was missing), and the
sort then forecasts the moves page as it always did where there was a
table. The sort brief's own words follow, since it is written after the
arrival ("This office has a drafting table, so its moves page ... is
yours").

### 6. The doctrine's second-desk sentence

What the code does today (lib/office_bale.py `bundle_precheck`,
`check_bundle_report`, `start`; bin/office `check_start_bundle`): a pack's
forecast overlapping an open session is refused before bale is asked,
naming the session, its folder and the overlap. A bundle whose pack line
the office can read is checked the same way, but with a bale whose
rehearsal answers in JSON (0.4.50 on) the office's overlap is deferred to
bale: `bale open --check --json` runs before anything is written; where
it passes (a bundle whose session is still open, which bale takes as a
second desk), the office says what its own check saw, prints bale's
second-desk line, and goes on (`--bale-rehearsed`); where bale refuses
too, the office refuses in its own words with bale's reason beside them.
With an older bale the overlap is refused on the office's reading alone.
A bundle the office cannot read (a bare name bale's search finds) is
bale's, in bale's words. README's account of it already said this.

The sentence now reads, in section 4 continued:

> A session whose forecast overlaps one already open is refused
> before bale is asked, and the open session, its folder and the overlap are
> named. A second desk is bale's to recognize, and the office refuses an
> overlap only where bale would (0.18.0): a bundle whose pack line the
> office can read is checked the same way, and bale's own rehearsal runs
> before anything is written; a bundle bale would take as a second desk on
> an open session is sent on, the overlap the office saw said beside bale's
> words, and one bale's rehearsal refuses is refused in the office's words
> with bale's reason beside them (a bale whose rehearsal does not answer in
> JSON is refused on the office's reading alone). Where the office cannot
> read the pack line (a bare name bale's search finds), it says so and
> bale's own words stand.

The code and the sentence had drifted only in the way the brief said; I
found no other gap.

### 7. The install's bytecode cache on the walk-in

`office_bale install-lines` (the walk-in head's batch read) prints a
`Bytecode:` line under the `Install:` line, before `Suite:`, when the
install's cache is not level for the running python3: office status's
own words less its label (`BEHIND: 1 of lib/'s 15 modules compiles from
source on every helper call (office_probe.py stale); (cd '...' &&
./install.sh) brings the cache level`, or the `NONE for this python3`
form after a Python upgrade). Unlike the Install and Suite lines it is
said in any office, not only one that scopes office-src: every office on
this install runs slower. Nothing is said when the cache is level, from a
working copy (no install, nothing to keep level), or under a cache prefix
(that python3 never reads the install's cache, and install.sh would not
change it; the test runner sets one, so no existing test's walk-in
moves).

The Next line (`next_move`, and so the home screen's first item, which
follows it): right after the install behind its source, before a session
out, `(cd SRC && ./install.sh)`, "the installed office-src's bytecode
cache is not level for this python3 (BEHIND: ...), so every office
command compiles its helpers from source and takes about twice as long;
install.sh compiles them again". Why there: the same one line as the
install behind its source, a second's work, and until it runs every
command, the land you would run next included, takes about twice as long.
Only where the install's stamp names its source; with none there is no
line to fill in, and status still says it (decision 4).

### 8. The letterhead check reads the cache

lib/office_deliver.py `check_in_project` ran `sys.executable -B
lib/office_letterhead.py ...` on this machine; a script's own code is
compiled from source every run. It now runs `letterhead_argv`: python3
`-B -P -S -c` with bin/office pylib's own program (runpy.run_module of
office_letterhead from the install's lib/, as `__main__`), so the module
is read from lib/__pycache__ and its last line calls main as before.
`-P` keeps the project's tree (the cwd) off sys.path, as the script's run
did; `-S` drops site, as every helper's run does (the module is standard
library only). The test runs it and the script form against the same
tree: same stdout, stderr and exit, byte for byte, and PYTHONVERBOSE shows
the code object read from `lib/__pycache__/office_letterhead.<tag>.pyc`
for the python that runs the test (the constraint's baseline: the test
names `sys.implementation.cache_tag`, never a version). The hosted form
is unchanged.

## What the occupant sees

As before, but for:

- `office status`: `structure:` lines, only when a folder is such a one,
  and its help's sentence names them ("folders against their History
  (and each one still provisional though every session it records landed
  applied)"), as 0.30.0 added the cache's clause, so the help still lists
  every line.
- The walk-in's `Bytecode:` line and Next line, only in that state.
- `office start --sort` in an office with no drafting table: the arrival's
  lines on stderr and its commit.
- A planner sitting's and a prep's ride list, in an office with no
  drafting table yet: the table's line says it arrives. A prep in such an
  office now names the table at all (it rode, unnamed).
- A response filed twice: the "already there" lines.
- The doctrine.

## Tests

- **New, 16**, in tests/test_tidy.py, one class per item:
  `TestASittingsPagesBySlug` (2: the key, and sitting_filings over a real
  git history with `sittings_after`), `TestTheDraftingTableOnASittingsList`
  (1), `TestThePrepNamesTheTableItCarries` (1: a prep in an office with
  none, its list, its brief and the digest shipped),
  `TestStatusNamesAFolderStillProvisional` (3: a folder from his words
  landed with notes that carry no Structure, closed, named in the
  cabinet under the folders line; not named while out, nor with a
  session never landed, nor without a provisional line; the rule in
  process over applied tags), `TestARefiledResponse` (3: land then
  sessions --pages with the same response, both pages byte for byte and
  nothing to commit; a new answer beside old ones under its own session's
  line; a fact filed again on a later day), `TestTheSortBringsTheDraftingTable`
  (1: an office with none, the arrival committed alone with exactly its
  four paths, the forecast, the brief, status's drafting line),
  `TestTheDoctrineSaysTheSecondDesk` (1), `TestTheRecord` (1),
  `TestTheCacheOnTheWalkIn` (2: an install, level then a stale module,
  the line's place and words and the Next line, nothing under a prefix,
  install.sh again and the page as it was; next_move's order),
  `TestTheLetterheadCheckReadsTheCache` (1).
- **Changed or dropped: none.** 942 at 0.30.0, 958 now.

Run over the unchanged code (the request's tree with test_tidy.py added),
15 of the 16 fail. The one that passes on both is by design:
`test_a_folder_whose_sessions_did_not_all_land_or_that_is_not_provisional_is_not_named`
pins what must stay silent.

## Run results (this sandbox, two cores)

Measured nothing beyond the suite's own runs, as the brief asked.

| run | tests | result | wall clock |
|---|---|---|---|
| whole suite, 0.30.0 as shipped | 942 | "[run] OK (942 tests run)" | "513s" (real 8m37s) |
| test_tidy alone, while building | 14 to 16 | OK, after three fixes to the tests themselves | about 17 s |
| test_tidy over the unchanged tree | 16 | 15 fail, 1 passes (above) | 29 s |
| whole suite, first pass of the code | 958 | one failure: tests/test_probe.py pins the doctrine's words "a `Suite:` line, under the install line", which I had changed; put back | "549s" |
| whole suite, the code final | 958 | one failure: tests/test_office.py's rule that no file names a model caught test_tidy.py spelling the development record's directory; it now spells it as the other tests do | "490s" (real 8m13s) |
| test_tidy and test_office after that fix | 145 | "[run] OK (145 tests run)" | |
| validation.sh --slow on a staged copy (the request's tree, files/ over it with modes stripped, apply.sh, the manifest beside it) | 372 in its fast tier, 958 whole | every check PASS, both claims [agree] | 9m44s in all; "the fast tier took 71.3s", the suite "505s" |
| validation.sh on the request's tree, unchanged | | every assertion of this change FAIL, the fast tier FAIL (no test_tidy), the syntax of bin/office and its exec bit PASS on both, deliberately | |

Afterwards the staged tree was byte for byte my working tree but for the
logs and the manifest copy: no `__pycache__`. Without `--slow`,
validation.sh is the fast tier and the assertions, about 80 seconds
here, under its 120.

## Decisions to ratify

1. **The drafting table on every sitting's list** (item 2): named with
   every sitting, as arriving where there is none yet, and the prep's
   filter removed, rather than "only where there is one" at gather time,
   since the digest before the pack brings it and it rides either way.
2. **Status's `structure:` line covers the filing cabinet too**, and
   reads "landed applied" from bale's applied/ tags with git, never a
   bale call; one line per folder, under `folders:`, nothing when none;
   status's help names it.
3. **A re-filed response's lines**: an answer is "already there" when the
   same line is anywhere in the folder's section; a fact when the same
   fact from the same session is in the chapter, whatever its day; a new
   answer goes under a fresh `- from SID:` line unless the section's last
   one is already that session's; an unchanged front sheet is not
   written.
4. **The walk-in's `Bytecode:` line** in any office, under `Install:` and
   before `Suite:`, silent under a cache prefix and from a working copy;
   its Next line right after the install behind its source, ahead of a
   session out, and only where the stamp names the source.
5. **The letterhead check runs through pylib's program** (`-B -P -S`,
   runpy as `__main__`), site dropped as for every helper.
6. **The doctrine changed beyond item 6's sentence**, where it pins what
   changed: the sort's forecast (section 4 continued), status's naming of
   provisional folders (section 5), and the walk-in's lines and the Next
   line's order (section 7). The code is the fact; the doctrine follows
   it.

## Paths outside the forecast

None. Every changed path is under the request's `resolved_scope`:
README.md, RELEASES.md, VERSION, bin/office, claude/context/front-sheet.md,
doctrine/OFFICE.md, lib/ (seven modules) and tests/test_tidy.py (new).
Nothing under share/, templates/, migrations/ or install.sh changed.

## Proposals

- **What:** a way to settle a closed folder that status's `structure:`
  line names: `office sessions FOLDER SID --pages RESPONSE` filing a
  Structure into a folder in the filing cabinet, say, or a line in the
  folder that marks its worked-out fields as kept.
  **Why:** seen here: once a folder whose one session landed without a
  Structure is closed, nothing can file one (a closed folder moves
  whole), so the new line names it for good. On your machine that is
  most likely only folders closed between 0.23.0 and now whose worker
  wrote no Structure.
  **Scope hints:** lib/office_sort.py `file_notes` (its filing-cabinet
  branch), lib/office_helper.py `file_structure`, doctrine section 5.
- **What:** say on a sitting's ride list when the drafting table will not
  arrive after all: an office with no drafting table whose digest office
  start leaves as it was (an open session holding the floor plan or
  bale.toml, or a digest that fails).
  **Why:** item 2's list says the table arrives with its digest; in that
  one case it does not, and only start's own warning says so. Rare, and
  only in an office that has never written its drafting table.
  **Scope hints:** bin/office `refresh_digest`, lib/office_planner.py
  `every_sitting_carries`.

## Handbook

### office-src

- the watches' and the digest's sittings are keyed by office_watches.sitting_key(rel, pages): a page SLUG-N.md joins SLUG.md when SLUG.md is a sitting's page the notepad filed (sitting_filings passes every filed stem), as office_planner.sitting_pages joins them; SID-N.md joins SID.md always
- the drafting table rides with every sitting, a meeting's prep included: office digest --before-pack makes it arrive (office_digest.write runs office_drafting.arrive) and office_bale start adds it; office_planner.every_sitting_carries names it for both, as arriving where there is none yet
- office status's `structure:` lines are office_bale provisional-lines (provisional_landed, applied_sids): each folder, on the desk or in the filing cabinet, with one provisional line that reads and whose every recorded session has bale's applied/SID tag in the office or a project it scopes, read with git (no bale call, and none at all without such a folder); printed under the folders line, nothing when none
- a response filed twice (office land, then office sessions --pages) files nothing twice: office_sort.file_notes appends only the answers not already in the folder's section, under a `- from SID:` line (QA_FROM_RE) unless the section's last one is that session's; file_handbook keys a fact by its words and session (filed_facts, FACT_LINE_RE), whatever day it was filed, and writes a front sheet only when it differs (front_sheet_body)
- office start --sort makes the drafting table arrive whenever drafting-table/moves.md is missing (drafting arrive --page moves.md; the one-writer rule over moves.md and arrival_targets), committed alone as "office start --sort: the drafting table arrives, for the moves page"
- the walk-in's `Bytecode:` line is office_bale.bytecode_behind, in install-lines between Install and Suite: office_helper.bytecode_line's words, in any office, silent when level, from a working copy and under PYTHONPYCACHEPREFIX; next_move(..., cache) puts `(cd SRC && ./install.sh)` right after an install behind its source, only when the INSTALLED stamp names the source
- the letterhead check on this machine is office_deliver.letterhead_argv: python3 -B -P -S -c with bin/office pylib's runpy program, so it reads lib/__pycache__; a hosted project's check still sends the module on stdin
- a test that means the install's bytecode cache names sys.implementation.cache_tag, never a version, and runs its commands without the runner's PYTHONPYCACHEPREFIX (tests/test_tidy.py, tests/test_office.py)

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.31.0
it has had a tidy after the front-door arc: eight small things, each a
few lines. `office status` now names, one line each, a folder whose
title, size and goal are still the office's guesses though every session
it records landed, so its worker never sent its own back. Walking in now
says when the install's compiled helpers are out of date for your Python
(after a Python upgrade, say), and the Next line is then the one line
that fixes it, install.sh again; until it runs every command takes about
twice as long. `office start --sort` brings the drafting table into an
office that has none, so the sort's desk moves have somewhere to go. The
rest you will not see: a planning sitting's several notepad pages count
as one sitting, a response filed twice files each answer and fact once,
the letterhead check reads the compiled helpers too, and the doctrine now
says what the office does with a second desk.

## Walkthrough

### What changed

- **A sitting's pages, one sitting** (lib/office_watches.py
  `sitting_key`, `sitting_filings`): SLUG-2.md and on join SLUG.md.
- **The drafting table on a sitting's list** (lib/office_planner.py
  `every_sitting_carries`; lib/office_meeting.py `write_prep`, its filter
  removed): named for every sitting, as arriving where there is none yet.
- **office status's `structure:` line** (lib/office_bale.py
  `provisional_landed`, `applied_sids`, the `provisional-lines`
  subcommand; bin/office `cmd_status`, `usage_status`).
- **A response filed twice** (lib/office_sort.py `file_notes`,
  `file_handbook`, `filed_facts`, `front_sheet_body`, `QA_FROM_RE`).
- **The drafting table with the sort** (bin/office `start_sort`).
- **The doctrine** (doctrine/OFFICE.md): the second-desk sentence in
  section 4 continued, and the sort's forecast, status's provisional
  folders and the walk-in's line and Next order where they are pinned.
- **The walk-in's bytecode line** (lib/office_bale.py `bytecode_behind`,
  `install-lines`, `next_move`, `next_line`; lib/office_home.py `home`,
  `home_items`; bin/office's comment in `walk_in_head`).
- **The letterhead check through the cache** (lib/office_deliver.py
  `letterhead_argv`, `PYLIB_PROGRAM`, `check_in_project`).
- **Tests:** tests/test_tidy.py, 16 tests, one class per item.
- **The record:** README (the walk-in, provisional folders, the sort, the
  letterhead check), RELEASES 0.31.0, VERSION, the development record's
  front sheet (Recent changes, Known problems).

### Why

The occupant's order: time, then the audience, then the rest. The time
run inside office-src is done for now, and the twine carrying waits on
twine-src, so the rest begins with the small items the arc's workers
proposed and the queue carried, folded into one session because each is
a few lines and none depends on another. Each one is a place where the
office said something slightly wrong (a sitting counted several times,
a table named or not named against what rode, a doctrine sentence behind
its code), said nothing where it should (a folder's guesses left
standing, a slow install unnoticed on the walk-in), or did a little work
twice (a response filed twice, a check compiled every run).

### How to explain each piece

- **Sittings counted once:** a planning sitting that runs to several
  pages files them as name.md, name-2.md and so on; the digest now knows
  they are one sitting.
- **The drafting table on the list:** every sitting carries the drafting
  table, because writing its opening page brings the table into an
  office that had none; the list now says so the same way for every
  kind of sitting.
- **The structure line:** when the office opens a job from your words it
  guesses a title, size and goal and marks them as guesses until the
  session that does the job sends its own. If every session landed and
  the guesses are still marked, status now says so.
- **Filed twice:** landing a response and then filing its pages again by
  hand used to add the same answers and facts twice; now the second time
  says they are there already.
- **The sort's drafting table:** the in-tray's sort writes its desk moves
  on a drafting table page; an office without a drafting table now gets
  one first, the way the in-tray arrives with the first drop.
- **The doctrine:** it now says what the office has done since 0.18.0
  when a planner's bundle meets a session already open: bale decides, and
  the office refuses only what bale would.
- **The bytecode line:** after a Python upgrade the install's compiled
  helpers no longer match, and every command is about twice as slow until
  install.sh runs again; walking in now says so, and the Next line is
  that one command.
- **The letterhead check:** it now runs the same way every other helper
  does, so it uses the compiled copy too.

### Questions a reviewer will ask

- *Does anything change for me day to day?* Nothing you have to do. A
  status line and a walk-in line appear only in the states they name;
  the sort's arrival happens once, in an office with no drafting table.
- *Why does the filing cabinet count for the structure line?* A folder
  whose one session landed is closed by the landing, so the case lands
  there. The line cannot be cleared for a closed folder yet; a proposal
  says how it could be.
- *Why does the prep's list change, when the item was about the planner
  sitting's?* Both carry the drafting table; the planner sitting's list
  said so and the prep's did not. They now say the same thing.
- *Why is the cache line on the Next line ahead of landing a session?*
  The same one install.sh line as an install behind its source, a second
  to run, and until it runs the landing itself is slower.
- *Did any test go?* No. 942 then, 958 now.

### A hand test

Run these on your WSL terminal, one line at a time, after this lands
(office land runs install.sh for office-src).

1. `office status | grep -c '^structure:'` in home-office: 0, or the
   folders whose worker sent no Structure, one line each.
2. `office | head -4`: no `Bytecode:` line (the install is level).
3. `touch ~/.local/share/office-src/lib/office_probe.py`, then `office |
   grep -e '^Bytecode:' -e '^Next:'`: the Bytecode line names
   office_probe.py stale, and the Next line is `(cd ... && ./install.sh)`.
4. Run that Next line, then `office | grep -c '^Bytecode:'`: 0 again.

## Delivery

- to: nobody: office-src has no audience

### Commit

Tidy the office after the front-door arc

Eight small items the arc's sessions proposed, each a few lines. office
status names, one line each, a folder whose worked-out title, size and
goal are still provisional though every session it records landed
applied, as the tag each landing leaves says, read with git. The walk-in
says when the install's bytecode cache is not level for the python3 that
runs it, in status's words, and its Next line is then install.sh's line,
right after an install behind its source. office start --sort brings the
drafting table into an office that has none, committed alone, so the
sort's moves have a page.

A sitting's pages filed by slug (SLUG.md, SLUG-2.md) count as one sitting
for the watches and the digest. Every sitting's ride list names the
drafting table the same way, as arriving where there is none yet, since
the digest written before the pack brings it; the prep's list had left
it out though it rode. A response filed twice, by land and then by
sessions --pages, files each answer and fact once and rewrites nothing.
The letterhead check runs as a module, as every helper runs, so it
reads the compiled code. The doctrine's second-desk sentence says what
start has done since 0.18.0, and the doctrine says each change above
where it pins it.

Additive: no migration. Every test kept and sixteen added.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.

## Structure

- title: The tidy after the front-door arc
- size: small
- goal: Tidy the office after the front-door arc: the eight small items the queue and the arc's workers carried, each a few lines, as office-src 0.31.0
