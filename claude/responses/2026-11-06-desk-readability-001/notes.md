# Notes: 2026-11-06-desk-readability-001, the desk made readable (office-src 0.49.0)

All five items shipped; nothing went to the seam. Every path is inside the
forecast (bin/office, lib, share, tests, README.md, RELEASES.md, VERSION,
doctrine/OFFICE.md, claude/context/front-sheet.md), so there are no
departures to admit. templates/ was forecast and not touched.

## Decisions

The calls the brief left to me first, then the deviations, each flagged.

1. **The two tables' columns.** Projects: `PROJECT  WHERE  AUDIENCE
   PAUSED  RIDES AND AFTER-LAND`. WHERE is `here (PATH)` or `on HOST
   (PATH)`, or `cannot be read: WHY` for a broken entry. AUDIENCE is `none`
   or today's audience words without the word "audience" (`origin, author
   Pat <p@x.org>, base main, branch_prefix feature/`). PAUSED is `yes` or
   `no`. The last cell is `rides: a, b; after: x; y`, with each
   declaration problem appended as `declaration problem: X`, and `none`
   when there is nothing. Folders: `FOLDER  PROJECT  TITLE  SIZE  STATE`.
   An empty size is `-`. The header row is in capitals, two spaces between
   columns, and the last column is never padded.
2. **The rides are carried whole**, not counted. `office map PROJECT` has
   the same table shape, so counting them there would only move the
   problem. On a terminal the rides cell is the first in the projects
   table to give way, so a long one is cut with `...`. Piped, it's whole.
3. **Where the width stops cutting.** In the folders table the title gives
   way first, down to 16 characters, then the state down to 20, then the
   project down to 10. In the projects table the rides go first (16), then
   the audience (12), then where (16). Past those floors a line runs on and
   the terminal wraps it. I thought that was better than cutting a
   folder's state to nothing. The width is read only when stdout is a
   terminal (`shutil.get_terminal_size`, so `COLUMNS` wins, which is what
   the pty test uses).
4. **Three closed rows before the fold**, the sitting's number
   (`office_map.CLOSED_SHOWN`). The fold line sits under the TITLE column
   so it reads as part of its project's group: `and N more closed: office
   map --all`, exactly as the brief has it. It doesn't name the project
   because the rows right above it do.
5. **What counts as closed for the fold**, flagged. A folder in the filing
   cabinet that has a session out, a merge job waiting, or work landed and
   not delivered is shown with the open folders and never folded
   (`is_closed`). Otherwise the fold could hide the one thing waiting on
   him.
6. **The project cell's words**, flagged. `the office` for an office
   lane. `no lane yet` for a folder with no lane in an office that scopes
   projects: the map used to put these under the office, but start still
   asks where they land, so "the office" would have said something untrue.
   In an office that scopes no project, a folder with no lane is `the
   office`. A lane naming a project the office doesn't scope reads `gamma,
   not a project here`, shorter than 0.46.0's `lane: gamma: src, not a
   project here` so it fits a cell. The same words come from one function,
   `office_helper.folder_project_words`, for the map, the pickers and the
   desk. These folders still group with the office's own, last.
7. **`office map PROJECT`** prints both tables cut to that project: its
   one project row, then its folders with nothing folded. The office's own
   folders don't appear. With no folders it says `no folder on PROJECT`.
   `--all` beside a project is accepted and changes nothing. Beside a
   folder it's refused, because a record has nothing folded.
8. **The `a` key**, flagged as my reading of "says `--all`". The key still
   runs `office map`, folded, since a readable page is the point. Its label
   now names the unfold: `the map: every project and its folders (office
   map --all unfolds)`. The home screen's 80-column rule is why it isn't
   longer. The verbs-table row (doctrine/OFFICE.md) and share/verbs.toml
   both say `--all`. If you meant the key to open `--all`, change one argv
   in office_home.FIXED_KEYS.
9. **The state cell.** `in flight 3 days` / `sitting out 2 days, step 8
   of 14`. The age is office_home.age_words without "ago", with
   `yesterday` as `1 day` and `just now` kept. Then `; and N more open`,
   `merge job waiting` or `landed, not delivered`, then the desk's group
   in short words (`open`, `ready`, `candidate`, `parked`, `no status
   line`, `STATUS on the desk`) or the filing cabinet's status (`done`,
   `retired`, ...), then `delivered BRANCH` and `review #N STATE`. The
   older `Reading.state` is untouched because `office map N` still uses it
   (the brief keeps that record as it was).
10. **The desk's line keeps `(sessions: N)`**, as the sitting said:
    `folder N  NAME (PROJECT)  next: ...  (sessions: N)  SIZE`. The project
    names are read once per office per process, keyed by the floor plan's
    mtime (`office_bale.floor_plan_names`), so an in-process caller that
    adds a project sees it. Flagged: `office digest` renders through the
    same `folder_line`, so drafting-table/digest.md now carries
    ` (PROJECT)` after each folder's name too. It's still ASCII. No
    stored page the brief named changes, but it is a regenerated page whose
    lines differ.
11. **Where the unescaping reader sits**, so a later screen finds it:
    `office_helper.shown(text)`, beside `ascii_escape`. It's called at the
    point a line is printed:
    - office_bale's main print loop, which covers desk, walk-in, status,
      in-flight, folder-sessions, ledger, landed and versions;
    - office_home's page and its `elsewhere` sections, and the bundle
      offer's words;
    - office_map's `table` (every cell, before anything is measured) and
      the folder record and `fields` output;
    - `office_bale.folder_title`, used by deliver's picker and the home
      screen's deliver and merge items;
    - `office_standing.words`, the standing's screen words;
    - `office_helper.folder_label` for the pickers;
    - `helper shown` (stdin to stdout) for bin/office's two bash-built
      titles, land's and withdraw's.

    A new screen calls `oh.shown` on the line it prints. Nothing written
    to a file goes through it.
12. **`shown` also takes `\xNN`**, a deviation from the brief's
    `\uXXXX` and `\UXXXXXXXX`. `ascii_escape` uses Python's
    backslashreplace, which writes U+0080 to U+00FF as `\xNN`, so an e with
    an acute accent is stored `\xe9`. Without this, an accent would still have shown
    escaped. It only undoes what ascii_escape could have written: an
    escape for an ASCII character, a surrogate or anything past U+10FFFF
    stays as typed text. It also keeps the escape for a character stdout's
    encoding can't carry, so a non-UTF-8 locale gets an escape instead of
    an exit 2.
13. **The pickers.** `folder_choices` is now one helper call, `helper
    folder-rows ROOT SPACE`, instead of one folder-facts call per folder,
    so it's faster on a full desk. It reads the lane and the floor plan's
    names in the same call. That covers start's jobs on the desk, `Folders
    in desk/` (close, reopen, folder, sessions, rider, deliver's fallback,
    standing, probe's fallback) and the planner's folder. Probe's folders
    with a session open now read `folder N, TITLE (PROJECT): SID, WORDS`,
    flagged because the row used to be `desk/NAME: SID (WORDS)` (the
    reader's probe-folders prints the label as a fourth field). Deliver's
    landed list and land's and withdraw's rows already named the project.
    They now show the title unescaped, and land says `the office` where it
    said `this office`. There is no tray picker (bare `office tray` takes
    the newest), so nothing changed there.
14. **When the downloads are not set**, flagged. On a terminal,
    `--bundle NAME` asks where downloads land once and keeps the answer,
    the same question the bundle offer asks. Piped, it refuses by name:
    `no NAME.bale-bundle in your downloads (none set: downloads in
    MACHINE.toml) or here; ...`. I counted that question as part of
    resolving the name. It is not one of the job questions the brief
    meant by "nothing asked".
15. **No bare name is left to bale's search any more**, flagged for its
    consequences. `resolve_bundle` hands bale a path every time. Because
    the office can now read every bundle start sends, its own pre-checks
    (`bundle_precheck`: paths not in the tree, an overlap) run on bundles
    named by stem too, as they always did for a path. So:
    - Below a bale whose rehearsal speaks `--json` (0.4.50), starting a
      browser copy of a bundle whose session is still open is refused in
      the office's words, naming the open session. Before, bale found the
      bare name and the second desk was said after the fact. On 0.4.50
      and later, bale's rehearsal still decides, and the live case is
      joined as before (its test passes).
    - A forecast path that doesn't exist is said in the office's words
      before bale is asked.
    - `resolve_hosted_bundle` and the bare-name fallback in
      `bundle_lands_read` can no longer fire from start. I left them in
      place (see Proposals).
16. **The bundle offer's cut moved into Python.** office_home's `bundles`
    output now carries the words unescaped and already cut to 60
    characters (`OFFER_WORDS_MAX`). Bash counting `${#words}` in a C
    locale would count bytes and could cut a character in half. The
    trailer and the question say `--bundle STEM`.
17. **Unreadable pack lines.** When start hands bale a file and bale's
    rehearsal doesn't say where it found it, the digest line says `its
    pack line at PATH does not read` instead of "bale's rehearsal did not
    say where it found it" (office_bale, start's sitting check). The fake
    bale reports the path, so the test still reads `bale found it at`.

## Item 5: the sweep

The sweep was an AST pass over tests/: every test function that both
names a literal session id (`\d{4}-\d\d-\d\d-[a-z0-9-]+-\d{3}`) and starts
or packs, or names a bundle. It found 18 functions, and I read each one.
I also grepped for future-dated id literals and found none.

Changed, one:

- `tests/test_standing.py TestTheEndsLine.test_the_readers_as_units`
  compared the sitting the fake minted (`self.sit`, today's UTC day) with
  `2026-11-04-plan-next-001` and `2026-11-05-y-001` as later sittings, so
  it passed only through 2026-11-05. It failed in the baseline run today,
  and was the suite's one failure there. The later ids are now dated a
  day after the minted one.

Left as fine, 17. None compares a literal with a minted id:

- The literal only names a session that is never minted. That covers a
  `--sid` value, a rider's source, the fake's registry seeded by hand,
  `bale relay`'s refused sid, a block for another sitting, and a recorded
  id: test_audience_line 1290, test_desk_verbs 275, 740 and 751,
  test_drafting_table 180, test_drop 495, test_meetings_view 439,
  test_one_door 220, test_probe 312, test_sort 192, 647 and 782,
  test_standing 492, test_tidy 167.
- The literal names a page or a menu entry, not a session the test mints:
  test_land 987 (the sitting page's name in a brief), test_home_screen 84
  and 122, test_home_screen_offers 232.

Not a literal, but the same family: tests that set `FAKE_BALE_DAY`
(test_land's second-desk helper) or read the UTC clock
(test_folders_and_projects, 0.48.0's fix) were already right.

## The suite

- Baseline, the unchanged 0.48.0 tree, whole: 1369 tests in 12m28s on two
  CPUs, one failure. It's item 5's test, failing because today is
  2026-11-06.
- With the change, whole, before the test moves below: 1387 tests, 19
  failures. All of them were pins of the old shapes (the desk line, the
  bundle trailer) or bare bundle names that relied on bale's search
  without machine.toml's downloads. The tests moved with the behavior.
  Each module that failed then passes now (rerun: 499 and 119 tests, OK).
- The whole suite on the final tree: 1387 tests in 12m10s on two CPUs, one failure:
  tests/test_ask.py TestTheRecord pinned `VERSION == 0.48.0`, so it fails at
  any next release. It now holds the version at 0.48.0 or later, as the
  older release tests do (`compare_versions ... >= 0`), and test_ask passes
  whole (18 tests). Like item 5's test, it was correct only for one stretch
  of time; this one was bound to a version rather than a day.
- The fast tier with this session's module (`tests/run.sh --fast
  test_desk_readability`): 385 tests, OK, 69.4 s of the 120 s budget.
- validation.sh in a staged copy (the 0.48.0 tree, files/ overlaid, apply.sh
  run): every check passed, about 2 minutes without --slow and 6m48s with
  it (the touched modules whole). On the unmodified tree the syntax check
  (the new module is missing), the release check and the fast tier fail,
  as they should. The doctrine-core and ASCII checks are guards that pass
  on both trees.

Tests moved with the change, outside test_desk_readability.py:

- test_folders_and_projects: TestTheMap's three tests and the project
  facts unit take the table shape, and the offer's trailer says STEM.
- test_office: the walk-in's desk line.
- test_desk_verbs: three desk lines.
- test_home_screen: the offer's question says STEM, and one start by
  bare name sets the downloads.
- test_home_screen_offers: probe's picker row.
- test_land: a `downloads_known()` helper on LandCase, the bare-name
  tests, and the two second-desk tests. The pre-0.4.50 one is renamed
  `..._the_open_session_is_named_before_bale_runs` (decision 15).
- test_third_trip: three bundle tests.
- test_front_door and test_return_trip: one bundle test each.
- test_out_trip_to_host: the hosted bare name's refusal.
- test_standing: item 5.
- test_ask: the record test's VERSION pin, as said above.

## Walkthrough

### What changed

- `office map` (lib/office_map.py) prints two tables through `table`:
  `project_row` per project, then `folder_row` per folder, with
  `short_state` for the state cell, grouped by project, open before
  closed, and the closed ones folded past three (`folder_rows`,
  `is_closed`). `--all` unfolds them. `terminal_width` cuts the page only
  on a terminal. bin/office `cmd_map` takes `--all`, and its usage says
  the new shape.
- lib/office_helper.py: `shown`, `folder_project_words`, `folder_label`,
  `office_project_names`, and the helper verbs `folder-rows`,
  `folder-label` and `shown`.
- bin/office: `folder_choices` reads `helper folder-rows`. Probe's,
  land's and withdraw's rows name the project the same way and show the
  title as written. The new `resolve_bundle` resolves `--bundle NAME` (and
  a word ending `.bale-bundle`) before anything else. The offer's trailer
  and the usage say STEM.
- lib/office_bale.py: `folder_line` adds ` (PROJECT)`. The reader's
  printed lines and `folder_title` go through `shown`. `probe-folders`
  prints the label.
- lib/office_home.py: the page, `elsewhere` and the bundle offer's words
  are shown unescaped. The `a` key's label names `--all`.
- lib/office_standing.py: `words` is shown unescaped.
- Release 0.49.0: VERSION, RELEASES.md, the front sheet, README.md, and
  doctrine/OFFICE.md past the banner (the map's paragraph and verbs row,
  and the bundle paragraph). share/verbs.toml's map comment too.

### Why

He met four things in one sitting and called them atrocious. `office
start --bundle STEM` fell through to "Jobs on the desk", because the stem
without its extension matched nothing and nothing refused it. The job
list named no project. The map was forty prose lines with sixteen closed
folders above the two open ones. A curly quote showed as `\u201c`. And
0.48.0's worker found one test that passed on one day only.

### How to explain each piece

- The map is a table you read across: one row per project, then one row
  per folder. The closed folders past the newest three fold into one
  line, and `office map --all` shows them.
- Every list that offers folders by key says which project each one is
  on, the same words as the map's project column.
- What you typed is what you see. The files keep their ASCII escapes, and
  the screens turn them back.
- `office start --bundle STEM` looks here and in your downloads first. If
  the bundle isn't in either, it says so and stops, before asking
  anything.

### Questions a reviewer will ask

- *Does the map write anything?* No. TestTheMapsTwoTables checks HEAD and
  `git status` after `office map`, `--all` and `office map PROJECT`.
- *Can unescaping change a stored page?* No. `shown` is called only where
  a line is printed. TestTheWordsAsHeWroteThem checks that folder.md is
  still ASCII after the map, the desk and a picker showed the character.
- *What if a title really contains `A`?* It stays as typed. `shown`
  only undoes escapes ascii_escape could have written, and ASCII is never
  escaped.
- *Why did so many bundle tests change?* They named bundles by stem and
  relied on bale's own search, without machine.toml's downloads set. The
  brief's rule makes the office find the name itself, so those tests set
  the downloads (decisions 14 and 15).

### A hand test

1. In an office with a few closed folders on one project, run `office
   map` in a terminal narrower than the longest title. Each line fits,
   the titles end in `...`, and the closed folders past three fold into
   one line. Then run `office map | cat`: every cell is whole.
2. Run `office folder N --title` with a title holding curly quotes (typed
   or pasted), then `office
   map`, `office desk` and `office start` (answer the jobs question with a
   word that matches nothing). Each shows the quotes. `head -1
   desk/*/folder.md` still shows `\u201c`.
3. Run `office start --bundle 2026-01-01-nothing`. It says `no
   2026-01-01-nothing.bale-bundle in your downloads (...) or here; ...`,
   exits 1, and asks nothing.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: desk-readability

### Commit

Make the desk readable: two map tables, the project on every list

office map now prints two aligned tables, the projects and then their
folders, with a project's closed folders past the newest three folded
into one line that office map --all unfolds. On a terminal the page is
cut to its width, the titles first. Every list of folders offered by key,
and the desk's line, names the folder's project. Titles and words past
ASCII show as written on every screen, while the pages keep their
escapes. office start --bundle STEM finds the bundle here or in the
downloads before it asks anything, or refuses by name. One test that
passed on one day only now dates its sessions from the one minted.

### Review

Make the desk readable: two map tables, the project on every list

Look at lib/office_map.py's table, short_state and folder_rows, at
office_helper.shown and folder_label, and at bin/office resolve_bundle.
To try by hand: office map on a narrow terminal and piped, a title with
curly quotes on the map and the desk, and office start --bundle with a
stem that is not in the downloads. Deliberately untouched: the stored
pages, the home screen's and the walk-in's layouts, and office map N's
record.

## Structure

- title: Make the desk readable: two map tables, the project on every list
- size: medium
- goal: Make the desk readable: office map as two tables with closed folders folded, every folder list naming its project, his words shown unescaped, office start --bundle NAME resolved and refused by name, and the suite swept for day-bound tests

## Handbook

### office-src

- every list of folders offered by key says `folder N, TITLE (PROJECT)` through office_helper.folder_label; bin/office reads it with `helper folder-rows ROOT SPACE`, and office_helper.folder_project_words gives the project's words (the project, `the office`, `no lane yet`, `X, not a project here`)
- a line that reaches a screen goes through office_helper.shown, the inverse of ascii_escape (`\xNN`, `\uXXXX`, `\UXXXXXXXX`); nothing written to a file does, so the pages stay ASCII
- office start resolves `--bundle NAME` in bin/office resolve_bundle before anything is asked or written (here, then machine.toml's downloads through find-download), and bale is always handed a path
- a LandCase test that starts a bundle by its stem sets machine.toml's downloads first (`self.downloads_known()`, tests/test_land.py)
- office map cuts its tables to the terminal's width only when stdout is a terminal (office_map.terminal_width); a pty test sets COLUMNS
- a test that needs a session id later than one the fake bale minted dates it from the minted id's day, never from a literal day

#### Front sheet

office-src 0.49.0 makes the desk readable. `office map` is now two tables:
the projects, one row each, then their folders, one row each with the
project, the title, the size and the state in a few words. A project's
closed folders past the newest three fold into one line, and `office map
--all` shows them. On a terminal the page fits its width. Every list that
offers folders by key names each folder's project, and so does `office
desk`. A title with curly quotes or accents shows as you typed it on
every screen. `office start --bundle STEM` finds the bundle here or in
your downloads first, and if it isn't there, it says so by name and asks
nothing. Additive: no migration.

## Proposals

- **What:** remove `resolve_hosted_bundle` and the bare-name branch of
  `bundle_lands_read` from bin/office, and the `START_BUNDLE_FOUND` /
  `--bundle-found` plumbing if nothing else feeds it. **Why:** since
  resolve_bundle, start always hands bale a path, so those branches can't
  fire from start. They're dead code that reads as live. **Scope hints:**
  bin/office around resolve_hosted_bundle, bundle_lands_read and
  check_start_bundle; lib/office_bale.py `start(..., bundle_found)` and
  the digest's `found_read_only`. Check `office land`'s and the offer's
  callers first.
- **What:** decide whether the second desk on a bale below 0.4.50 should
  defer to bale's rehearsal, as it does from 0.4.50 on. **Why:** decision
  15. Starting a browser copy of an open bundle is now refused in the
  office's words on an old bale, where it used to be bale's call. That's
  probably right (old bales can't say "second desk" before opening), but
  it's a ruling of 2026-10-12's ground. **Scope hints:**
  office_bale.bundle_precheck's defer_overlap.
- **What:** give the walk-in's In flight lines and the home screen's
  Projects block the project-first table shape. **Why:** the brief kept
  their layouts out of scope, but now they're the only screens still in
  prose next to the map's tables. **Scope hints:** office_bale
  render_desk's in-flight lines, office_home render_page.
