# notes: 2026-11-04-folders-and-projects-002 (office-src 0.46.0)

All eight items shipped, the seam's three halves (5, 6 and 7) included;
nothing is left for the plan to move. Said first because you will meet it
before anything else: the office's own lane is written `the office`, not
removed (decision 2), and start's screen is cut on a terminal only, piped
output keeping every line (decision 6). Both are flagged deviations.

## Decisions

Each one either a call the brief left to me or a reasoned deviation. The
flagged deviations are marked **deviation**.

1. **Which half shipped: all of it.** Items 1, 2, 3, 4 and 8 are the
   release the brief asked for; 5, 6 and 7 turned out small against the
   code (set already asked group by group behind one `can_ask`, the
   paused read is one argument, the keys are one function), so they
   shipped too, each with its class.

2. **deviation: `--in-office` writes `- lane: the office`, not "none".**
   The brief says `--in-office` "writes the lane as none". Read as "no
   lane", that loses item 3's office answer: a folder whose lane is gone
   is asked again at the next start. Read as `- lane: none`, it reads as a
   project named `none` (PROJECT_NAME_RE takes it). `the office` is two
   words, so lib/office_helper.py lane_project returns None for it and
   every reader that looks for a project in a lane (the desk, deliver's
   waiting_on_delivery, the riders' project globs) sees no project, as the
   brief wants; start, probe and deliver read it as the office's own work
   (oh.OFFICE_LANE, oh.lane_is_office). The map puts such a folder under
   "the office".

3. **office folder takes `--source` and `--class` too** (the brief's
   call). The writer is one function over EDIT_FIELDS, so two more fields
   cost a line each, and a wrong work class is a real mistake (it reaches
   bale pack's --work-class). The status stays out: folder_edit refuses it.

4. **A re-laned folder with a session out elsewhere is said, never
   refused**, as the sitting leaned: `SID is out on alpha for desk/NAME;
   it lands there as packed, whatever the lane says now` (a warning line).
   lib/office_map.py `open-for` reads the sessions out on the folder.

5. **deviation (small): office deliver asks.** The brief's item 3 has
   deliver asking; at 0.45.0 it never asked, it refused (`... has no lane
   naming a project, so say which: office deliver N --on PROJECT`). On a
   terminal it now asks by key when the lane names no project (and is not
   the office's), and keeps the answer; piped it refuses as before. It
   offers every project, not only those with an audience (Proposal 3).

6. **deviation: the screen is cut on a terminal, and piped keeps every
   line.** `detail` (bin/office, beside `log`) says a line under
   OFFICE_DEBUG when START_SCREEN is set (a start whose stderr is a
   terminal; exported, so the reader's tray lines follow it) and as a
   plain `[office]` line otherwise. The piped record is what scripts,
   sessions and about forty existing tests read (`bale found it at ...`,
   `out tray: ...`, `opened desk/...`); the brief's pin is about a
   terminal. Cut to OFFICE_DEBUG on a terminal: the survey's two lines,
   bale open --check's two, the size-is-small line and `opened desk/X as
   folder N` (when start opens it), `opening the bundle` / `packing`, each
   out-tray file, `recorded SID`, the status line, `no forecast given`.
   Kept: every `from the ...` line, `forecast from the folder's lane`,
   `the goal is the folder's own`, the brief line, `what rides with X, as
   declared` (a settled line from the floor plan, and test_start pins it),
   the riders' lines, warnings, the refresh offer, the clipboard line, the
   tray opened, and `next:`. A bundle start that asks nothing prints four
   (five where Explorer opens).

7. **The opener comes after its copy, and stdout's "Attach every file"
   line is gone.** For `next:` to be the last `[office]` line before the
   opener, the copy and the tray's opening had to move ahead of the
   opener's print (hand_over_opener, used by start, the sort and the
   prep). The stdout line said what `next:` says, so it went (nothing
   twice); to_clipboard's "printed above" says "below" for this caller.

8. **deviation: the opener's copy is beside the tray, not in it.**
   `OUT_TRAY/SID.opener.txt` (the tray's own name plus `.opener.txt`, so a
   `SID-2` tray has `SID-2.opener.txt`). Inside the tray it would be one
   more file the occupant drags into the chat, and "attach every file in
   the out tray" would stop being true. start_desktop writes it, so the
   sort and the prep have one too.

9. **office tray's choices.** No argument: the newest session open in
   this office's repos that has a tray, newest by the tray's mtime (ids do
   not order within a day). A folder: the newest session its Sessions
   section records that has a tray, out or not. A tray from before 0.46.0
   has no copy, and that is one line. On a terminal it opens the tray as
   start does and copies the opener again.

10. **The offer's rest line comes after the nine keys.** pick() gained
    PICK_TRAILER, one line said after the keys and before the question;
    the stems not offered are listed under OFFICE_DEBUG. The words are the
    brief's, verbatim.

11. **The keys past nine (the brief's call).** 1 to 9, then the lowercase
    letters no fixed key takes, in order (b c e f g i j t u v x y z), then
    A to Z: 48 in all, each one keypress for read_key. Past 48 a line says
    how many have no key (never silent). The other offices' items share
    the sequence, so their own "and N more there" cut went with it. The
    menu file is unchanged (KEY<tab>KIND<tab>ARGV).

12. **The map key is `a`** ("the map: every project and its folders"),
    after `o` in the fixed row, as the brief names it.

13. **The map reads what the desk reads, once.** It calls render_desk
    with groups_out (the groups, the deliveries, the merges, the reviews),
    open_anywhere for the sessions out and their ages (the reader caches
    bale's status per repo, so the second read costs nothing), and
    render_folder_sessions for one folder's record. office_home.py's
    age_words and local_day are imported, not copied.

14. **A bundle opened on a paused project**: office_home every_place reads
    the repos with rendering=False, so a paused project's known_sids is
    read (one status call per screen, only when a bundle is in the
    downloads). The paused line's new words changed one pin in
    tests/test_home_screen_offers.py; test_home_screen's page test pins
    the new keys; test_drafting_table's blueprint-close test takes the
    tray as the one directory in `out-tray/` (the opener's copy sits
    beside it now).

15. **office projects set**: `walk` is set by `--edit`, or by no flag at
    all on a terminal; every keep question now hangs on it instead of on
    `can_ask`. `--prepare` alone is as it was. `--path` with `--prepare`
    prepares the new clone during the check; `--branch-prefix` refuses on
    a project with no audience (it means nothing there), and
    `--no-audience` clears the prefix with the rest of the line.
    set_declarations writes `path` as one more string key.

16. **Where a cite and the tree disagreed**: none that mattered. The
    brief's line numbers held within a few lines; read_key, home_screen,
    offer_bundles, ask_where and start_desktop were where it said.

## Walkthrough

What changed, in the order you will meet it.

- **`office map`.** One page: each project a heading, its facts on one
  line, `rides:` and `after it lands:` lines, then `folder N  TITLE
  (SIZE)  STATE` for every folder on its lane, newest first, `riders: 3,
  5` under one that carries any; then `the office`. `office map alpha` is
  one section, `office map 12` one folder's record ending with the lines
  that change it. Nothing is written.
- **`office folder 12 --lane alpha --size medium`.** Two lines said
  (`desk/NAME: size from small to medium`), two History lines, one
  commit, `office folder: NAME re-scoped: lane, size`. A field it names
  leaves the provisional line. `office folder 12` alone prints the fields
  and the lines.
- **The lane kept.** A start on a folder with no lane asks where by key
  once; the answer is the lane after that, said. Probe the same; deliver
  on a terminal asks the project by key once.
- **Bare start with many bundles.** Nine keys and `and N more, oldest
  first: ...`.
- **start's screen.** On a terminal: the `from the ...` lines, the
  clipboard line, the tray opened, `next: attach every file in the out
  tray (PATH) ...`, then the opener, then `When the response comes back:
  office land SID`.
- **`office tray`.** `Out tray for SID: PATH`, the files, the opener again.
  On the home screen while a response is not in: `Open the out tray for
  folder N, TITLE again (its files and opener)`.
- **`office projects set alpha --no-after-land`** on a terminal asks
  nothing else; `--edit` asks everything; `--path` and `--branch-prefix`.
- **The home screen past nine.** `[b] ...`, `[c] ...`.
- **The record.** VERSION 0.46.0, RELEASES.md's entry first, the front
  sheet's line, README.md's sections, share/verbs.toml (map, folder, tray;
  projects' comment), the doctrine past its banner (section 5's
  paragraph, three verbs-table rows, section 10's floor-plan sentence).

Questions a reviewer will ask:

- *Why not write the office lane as no lane at all?* Decision 2: it would
  be asked again, which is the complaint item 3 answers.
- *Does `the office` break any reader?* No: lane_project returns None for
  it (a space is not in PROJECT_NAME_RE), so every project reader sees no
  project; a unit test pins that.
- *Why is the piped output unchanged?* Decision 6. The pin is a
  terminal's, and the piped record is the one the suite and the sessions
  read.
- *Is the one-writer rule the same rule?* Yes: `reader writers ROOT
  REL/folder.md`, the check open's minting uses, exit 3 refusing. A
  registry that cannot be read is a warning and the write goes on, as
  open's does.
- *What if the map's bale read fails for a project?* open_anywhere's
  problem lines go to OFFICE_DEBUG and the folders show their desk state;
  render_desk already says what it cannot read.

Hand test (on WSL, with a real Explorer):

1. `office start` with a bundle waiting: four or five `[office]` lines,
   Explorer opens, the opener on the clipboard. Close Explorer.
2. `office tray`: Explorer opens again on the same tray, the opener is
   printed and copied again.
3. `office map`, then `office map N` for that folder; copy one of its
   last lines (`office folder N --size medium`) and run it; `office map
   N` again shows it.
4. On the home screen, `a` shows the map; with ten things waiting, `b`
   runs the tenth.

## Delivery words

office-src 0.46.0: folders and projects. `office map` shows every project
with its facts, what rides with it and what runs after it lands, and
every folder under it with its state; `office map N` is one folder's
whole record, ending with the lines that change it. `office folder N` is
the one writer of a folder's lane, title, size, goal, source and class
after office open, and a lane start, deliver or probe had to ask for is
kept. Bare `office start` offers the newest nine bundles, start's screen
on a terminal is cut to what it settled and what to do next, and `office
tray` opens a session's out tray again and prints its opener. `office
projects set` asks only what its flags imply (`--edit` walks
everything), with `--path` and `--branch-prefix`; a bundle opened on a
paused project leaves the offer; every home-screen item has a key.
Additive; no migration.

## Structure

- lib/office_map.py is new (about 400 lines): the map's page, one
  folder's record, the change lines `office folder` prints too, and
  `open-for`. It imports office_bale, office_home, office_review,
  office_standing and office_drafting where it uses them, as the suite's
  import rule asks.
- lib/office_helper.py gained folder_edit, folder_field_values,
  OFFICE_LANE, lane_is_office, EDIT_FIELDS and the `folder-edit`
  subcommand beside folder_set_field; set_declarations gained `new_path`.
- lib/office_home.py gained item_keys, the tray readers (tray_root_of,
  tray_dir, opener_copy, tray_items, tray_reading) and the `tray`
  subcommand; render_page's keyed loop replaced the MAX_ITEMS cut.
- bin/office gained cmd_map, cmd_folder, cmd_tray, folder_held,
  folder_write, keep_lane, find_any_folder, hand_over_opener and detail;
  it is about 400 lines longer (past 11,000). The three verbs' bash is
  thin; the next verb that reads this much could follow office_map.py's
  shape from the start.
- tests/test_folders_and_projects.py is new, one class per item (units
  beside verbs where the item has one).

## Handbook

office-src: front sheet

- `office map` is folders and projects on one page; `office map N` is one folder's record and ends with the lines that change it.
- A folder's fields after office open are written by `office folder N` alone; each change is one `re-scoped` History line, and a field it names leaves the provisional list.
- A folder whose work is the office's own carries `- lane: the office`, which names no project.
- office start keeps the opener beside the tray as OUT_TRAY/SID.opener.txt; `office tray` prints it again.
- On a terminal office start's background lines are under OFFICE_DEBUG; piped, every line is said.
- The home screen's keys are 1 to 9, then the letters no fixed key takes, then capitals; `a` is the map.

## Suite

The whole suite, once, on two CPUs: 1332 tests in 731 s (`tests/run.sh`,
12 min 14 s of wall clock), one error: test_drafting_table's
blueprint-close test took the out tray as the first entry of `out-tray/`,
and since 0.46.0 the opener's copy sits beside the tray (decision 8). The
test now takes the one directory there (tests/test_drafting_table.py, one
line), and the module ran again whole, 27 tests, OK. Nothing else in the
code changed after the run.

validation.sh ran on a staged copy (the request's tree, files/ over it,
apply.sh run, the manifest beside it as .bale-manifest.json): plain, every
check passed, the fast tier with this session's classes took 67 s of its
120 s (389 tests; it was 80 s at 0.45.0 with that session's module whole,
so I named the cheap classes here, not the module); with `--slow`, every
check passed in 4 min 16 s, the touched modules whole (test_folders_and_projects,
test_desk_verbs, test_home_screen, test_home_screen_offers, test_start,
test_office, test_read_side, test_project_on_host, test_three_gaps,
test_suite_clock), and the three claims agree with their verdicts. On the
unmodified tree the record's pins, the three verbs' check, the new test
module's syntax and the fast tier all fail, as they should; the doctrine's
core check passes on both, since it pins what must not move.

One thing about validation.sh you may trip on: the suite's scratch
(TMPDIR) is a temporary directory outside the staged tree, announced on
its first line. Inside the tree it broke test_office's install tests,
which copy the tree whole while the suite writes beside them.

## Proposals

1. **What:** say start's background lines under OFFICE_DEBUG piped too,
   once the sessions and scripts that read them read something steadier.
   **Why:** decision 6 leaves two records of one start, and a test that
   pins a line piped no longer says what the occupant sees. The tests
   that pin them (about forty `assertIn`s on `bale found it at`, `out tray:`
   and `opened desk/`) would move to OFFICE_DEBUG=1 runs. **Scope hints:**
   bin/office detail; the tests that grep start's stderr.

2. **What:** a way for `office tray` to print the opener of a session sent
   before 0.46.0. **Why:** those trays have no copy beside them, and the
   opener is bale's words (the pack's stderr between its scissor lines),
   which no --json surface carries; a session out today keeps that gap
   until it lands. A slip for bale-src (a dossier key, or `bale opener
   SID`), not an office workaround. **Scope hints:** share/bale-consumption.toml
   once bale has it; lib/office_home.py tray_reading.

3. **What:** office deliver's question offers only the projects with an
   audience. **Why:** decision 5: deliver carries work to an audience, and
   a project with none refuses one step later. **Scope hints:** bin/office
   cmd_deliver's pick; project-facts has the audience.

4. **What:** the map marks a folder whose project is paused. **Why:** a
   paused project's sessions are read for nothing, so its folders show
   their desk state (`ready`, `open`) and a session out there is not on
   the line; the project heading says paused, the folder line does not.
   **Scope hints:** lib/office_map.py Reading.state.
