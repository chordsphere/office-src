# Notes: 2026-11-08-prep-and-tidy-003, a meeting's prep filed, compared and probed, and six clean-ups (office-src 0.55.0)

All fourteen items shipped whole, each with its tests, item 14 among them
(the half the brief said to leave, which turned out smaller than its
estimate). Every path is inside the forecast (the one new file,
tests/test_prep_and_tidy.py, sits under `tests`), so there are no
departures to admit. There was no context compaction this session.

The tree I was handed is 0.54.0, the whole tree. Every anchor the brief
named is there, by name, at these lines before the change: office_meeting
prep_of 602, office_standing write 286, office_home home_items 697,
office_bale Doctrines 3625 (older_stamp 3651, doctrine_lines 3659),
office_probe read_block 157, calls_of 241, plan 723, plan_spanning 813,
run_on 935 (its `name each project literally, never through a variable`
at 954), office_map next_lines 502, office_bale render_desk 1424 and
handoff_places 4646, bin/office detail 40, cmd_slip 1988, cmd_drop 2090,
cmd_standing 10067, cmd_probe 10434, README's `no verb sets it yet` 2504,
tests/test_land.py test_where_the_release_is_said 775 (its pin at 780),
tests/fakes/land_bale.py `stats --sid` 359. The bundle plumbing is where
0.52.0's notes left it. None is gone.

## Decisions

Numbered so you can ratify or correct each by number.

1. **A prep's standing page is calendar/standing-SID.md**, one per prep,
   in the folder page's shape (office_standing write_prep, prep_rel). The
   block's id must be a prep the calendar's record line names; given no
   SID, the block's own id is taken, so `office standing --prep` with the
   block on the clipboard needs no id typed. The one-writer rule is the
   folder page's (`reader writers` on the page). The commit is `office
   standing: SID, the prep for TITLE`. Nothing deletes a page: when the
   prep is held it stays, as a folder's does when its sitting ends. The
   calendar is hung, so these pages ride with every office session; they
   are a few lines each, and I judged that cheaper than a new space. Say
   if you would rather they lived under calendar/standing/.
2. **The home screen's prep item says what a sitting's says**
   (office_home prep_item_words): `; it is out under an older doctrine:
   ...` from the record line's stamp (Doctrines.older_stamp, as the
   walk-in already did), then where it stands. It also gets the sitting's
   second key, `office standing --prep SID`, from its first turn, as a
   sitting's has since 0.44.0. The walk-in's In flight line for a prep
   says where it stands too.
3. **office status's doctrine lines name a prep out under another
   doctrine** as `  SID: the prep for TITLE (DATE HH:MM) out under an older
   doctrine: ...`, read from the calendar's record (state `prep out`,
   stamp not the install's). bale is still asked which sessions are open
   only when something stamps another doctrine.
4. **Item 3, my call: office probe reads the calendar's record line as
   what records the prep's session.** The other road, the prep brief
   saying "ask through the sitting's folder", has no folder to name: a
   prep is recorded by no folder, and a folder that does not record the
   prep's sid refuses it in plan, rightly. So `office probe --prep [SID]`
   plans with office_probe recorder() standing for the folder (the record
   line's one sid), and the rest of plan and plan_spanning run as they do
   for a folder's sitting: open read-only in the office, so a probe of a
   project runs there under the prep's id and one of the office runs in
   its root. Where it runs: `--project`, else the run line's, else the one
   concern of its meeting (office_meeting concerns_of: one project, or the
   office), asked on a terminal when it concerns several and refused piped
   naming `--project`. With no SID the one prep out is taken, said, and
   several are offered by key. The prep's run line is a second form, `#
   office: probe --prep SID [--project NAME]`; the folder form is
   unchanged, and the doctrine (past the core) pins both. The prep brief
   says to write it.
5. **A prep's probe writes no History line**, said in one line: the
   calendar's record line has a pinned shape and no History, and the brief
   pinned no record for it. A standing beside a prep's block is filed as
   the prep's, and a text holding a standing and no probe block, with no
   folder recording its sitting, is filed as the prep's when the calendar
   records it (office_standing place_of).
6. **Item 4: the refusal is in plan(), before plan_spanning**, so a block
   whose only call is unread (which reads as plain today) and a spanning
   block with one bad call among good ones are refused alike
   (office_probe check_calls). It names the line by number and text, in
   run_on's words (LITERAL_WORDS): `line 9 (office-on "$P" ls): office-on
   names '$P', which is not a project's bare name; a name is read from the
   block before it runs, so name each project literally, never through a
   variable; nothing ran`. A word made by `$(...)` and a bare `office-on`
   are refused the same way.
7. **Item 5: the warning rides the plan** (its `warnings` list) and bin
   office says it once, after the plan and before the header, rather than
   from plan itself, since plan runs twice when a session is asked for.
   calls_of now has a twin, call_words, which returns each call's words
   too; calls_of keeps its pairs (its tests are unchanged). Reading the
   words meant reading redirections: a redirection's target, and a
   descriptor's number before it (`2>&1`), are no words of the call. One
   side effect: a redirection at a command's start no longer ends the
   command's start, so `>f office-on alpha ls` now counts as a call, as
   bash runs it. **Flagged:** the templates did not say how to write a
   call, so by the letter item 5's template clause did not fire. I added
   one sentence to both briefs anyway (sitting and prep): name PROJECT
   literally, and a shell line as `office-on PROJECT sh -c 'LINE'`. The
   prep brief needed new probe words for item 3 in any case, and the
   sitting brief's would have been the odd one out. Take it out if you
   disagree.
8. **Item 6: after a no, a second question**, `Copy the message now, then
   r reads the clipboard again; a plain return ends here (office drop)`.
   It is `ask` with the r key and a return, as the home screen's keys are
   typed, not a raw single keystroke: every question in bin/office reads a
   line, and a raw read would be the only one that does not take `?`. The
   text read again is checked again (still a command line: asked again).
   Piped the branch is never reached, as before. The existing no test,
   tests/test_drop.py test_no_the_default_drops_nothing, gained one
   scripted answer for the new question; its assertions are unchanged.
9. **Item 7: the last line is on stderr**, after the page's path on stdout:
   `the suggestion box, ROOT/suggestion-box, holds N slip(s)`. stdout
   stays the page's path alone, which scripts read. N counts the box's
   pages as the walk-in's `Suggestion box: N slip(s)` does.
10. **Item 8, a reading of "the map's Next rows":** next_lines is a folder
    record's, and an ask lives in no folder, so no folder's record could
    name one without saying it is that folder's next move. The map's page
    (and a project's page, by the ask's project) ends with an `Asks out`
    block in next_lines' row shape instead: `office ask --learned` and
    `office tray ASK` for each, oldest first. `office desk` ends with an
    `Asks out (next: office ask --learned; ...)` section in the walk-in's
    words (office_ask out_line), and an `Asks whose tray is gone:` section
    with status's orphan words (office_ask orphan_words, orphan_line less
    its `asks:` label). Both take `--machine-file`, as the walk-in's desk
    call does since 0.54.0; the walk-in itself is unchanged.
11. **Item 9** is as asked: the paragraph says `--branch-prefix PREFIX`
    sets it (0.46.0) and `--no-branch-prefix` clears it. The pin now pins
    that sentence and that `no verb sets it yet` is gone.
12. **Item 10: what went, and what stayed.** Gone: both `bundle_here`
    fallbacks (start new, offer_sort_first), START_BUNDLE_FOUND, the
    --bundle-found flag and start's `bundle_found` argument and its
    reading. I read that nothing reaches them: every `bundle=` in cmd_start
    is resolve_bundle's `readlink -f` of a file, or the offer's path, so
    `[ -f "$bundle" ]` held wherever the fallback sat; and for a bundle
    here, bale's rehearsal found it at the very file it was handed, so
    bundle_read_only(bundle_found) read the same file bundle_pack_argv had
    already failed on (a hosted bundle's found_at was a host path, never a
    file here, so it never fed it). Stayed: start new's `[ -f "$bundle" ]`
    guard before the goal is read (one test, and a direct caller's
    safety), and the `unknown` branch in start, which now names the file:
    `its pack line at FILE does not read`. That changed one pinned line,
    tests/test_land.py test_a_pack_line_the_office_cannot_read, whose
    expected words were `bale found it at FILE, and its pack line there
    does not read`; FILE is the same path, and the test says why.
13. **Item 11: the fake answers a dossier only where the session was
    packed** (realpath of the packing repo against bale's cwd). The test
    that tells the two apart: an office session on a folder whose lane is
    alpha (tests/test_prep_and_tidy.py TestADossierIsItsReposOwn). The
    lane puts alpha first, and before this fake alpha answered, so
    handoff_check said `still open in alpha`; it now says `still open in
    the office`, which is where the session is. handoff_check reads every
    place through record_places, and when a record is in more than one it
    says so (`SID's record is in more than one place (alpha, the office):
    the office reads alpha's, the folder's lane first`). Past the first
    place that holds it, only places on this machine are read: the brief
    pins that nothing reaches a host that does not already, and before
    this a host after the first hit was never reached. No suite test of
    the real handoff needed a change.
14. **Item 12, the sweep, and what it found.** Two passes. First by
    the clock: the baseline suite on the unchanged tree started at
    23:57 UTC on 2026-11-08 and ran past midnight, so every module that
    ran after 00:00 minted 2026-11-09 sessions; all 1526 passed. Then
    on purpose: a copy of the tree with both fakes' default day moved
    to 2031-02-03 (FAKE_BALE_DAY unset), the whole suite run: one test
    failed, tests/test_folders_and_projects.py
    test_a_bundle_start_that_asks_nothing_prints_twelve_office_lines_at_most,
    which took the session's day from the wall clock after the start (so it
    would also fail on a run that straddles midnight UTC). It reads the day
    from the `Out tray:` line start printed now, and still checks the day
    is not the bundle's name's; its now unused datetime import went. A
    grep for every `now(...).strftime` and `date.today()` in tests/ found
    no other one beside a pack (the rest are office dates, not session
    ids). The hard-coded literals the brief's grep finds (about three
    hundred) are fixtures written by hand into folders, records and
    fakes' state, none minted by a fake, which is why the far-day run
    passes them. The second pass is a hand-patched copy, not shipped; a
    proposal below keeps it.
15. **Item 13: moved whole.** spanning_block, TestASpanningProbe and
    TestASpanningProbeOnAHost, assertions as they were, now in
    tests/test_spanning_probe.py under a heading that says where they came
    from; test_three_gaps keeps its deliver and branch classes and lost the
    imports only the moved code used. tests/fast-tier.toml did not name
    test_three_gaps, so it names neither now.
16. **Item 14: START_SCREEN became START_RUNNING**, set for every start,
    piped or not, so `detail` and the tray's per-file line are debug lines
    within a start. **A correction to the brief's mechanism:** making
    detail a debug line everywhere (my first cut) silenced verbs that
    share those functions when run on their own: `office open` called
    directly (the tour's step 3 pins its `opened desk/...` line), `office
    sessions`, the survey. So detail is quiet only inside a start, which
    is what 0.46.0's decision meant by start's background lines. The
    estimate of about forty assertIns did not hold: three tests pinned
    such a line piped, and they now run with OFFICE_DEBUG=1, assertions
    kept but for the `debug: ` the record now carries
    (tests/test_folders_and_projects.py TestStartsLinesPiped,
    tests/test_third_trip.py test_bale_is_asked_before_the_open_where_the_
    open_runs, tests/test_out_trip_to_host.py test_check_and_open_run_on_
    the_host_with_the_bundle_sent_there). The others the brief's grep
    names (`opened desk/` in the tour) are not start's.
17. **A defect I made and the suite caught, and a guard for it.** My first
    name for record_places' helper was place_words, which office_bale
    already defines for a bundle's places; Python took the second def, and
    every bundle line said `a's tree` for `alpha's tree` (six tests in
    three modules). It is record_place_words now, and
    tests/test_prep_and_tidy.py TestNoModuleDefinesANameTwice refuses a
    second top-level def of any name in any lib/ module. No module had one
    before this session.

## The suite

- Baseline, the unchanged 0.54.0 tree, whole: 1526 tests, OK, about 15
  minutes on two CPUs (tests/run.sh --jobs 2), started at 23:58 UTC on
  2026-11-08 and ended past midnight (decision 14's first pass).
- New: tests/test_prep_and_tidy.py, 30 tests, and three in
  tests/test_spanning_probe.py (TestTheCallsAreReadBeforeTheBlockRuns).
  Moved: tests/test_three_gaps.py's seven spanning tests, whole, to
  tests/test_spanning_probe.py (decision 15).
- Touched, each named in its reason and here: tests/test_drop.py (one
  scripted answer, decision 8), tests/test_land.py (the README pin,
  decision 11; the unreadable pack line's words, decision 12),
  tests/test_standing.py (the catalog pin names the prep's page),
  tests/test_folders_and_projects.py, tests/test_third_trip.py and
  tests/test_out_trip_to_host.py (OFFICE_DEBUG=1 runs, decision 16; the
  minted day, decision 14), tests/fakes/land_bale.py (decision 13).
- The whole suite on the finished tree: 1559 tests (0.54.0's 1526 and the 33 new),
  OK, 16 minutes on two CPUs (tests/run.sh --jobs 2, in the staged copy
  below). Run 1 of the changed tree, before the fixes decisions 16 and 17
  tell of, failed 14 tests; each is named there.
- validation.sh runs the syntax checks, the pinned outcomes (the doctrine's
  core by its 299 lines' sha256, VERSION, RELEASES, the front sheet, the
  README sentence, the plumbing gone, the tests moved), and the fast tier
  with this session's classes; behind `--slow`, eleven modules whole. In a
  staged copy (0.54.0, files/ overlaid, apply.sh run, bin/office's bit
  stripped first) every check passed: 1m21s without `--slow` (the tier
  itself 79.9 s of its 120, 390 tests), 6m40s with it. On the unmodified
  tree every change-dependent check fails; the six that pass there (bash
  -n, the syntax, the catalog as TOML, the exec bit, the doctrine core's
  banner and bytes) guard what must not move, and `no m10_` passes on both
  since it can only refuse. Nothing was written in the staged tree but the
  script's logs; the runner's scratch is under TMPDIR, as the header says.
  tests/fast-tier.toml is unchanged: no verb was added.

## Walkthrough

### What changed

- `office standing --prep [SID]` files a meeting's prep's standing as
  calendar/standing-SID.md; the home screen's prep item and the walk-in
  say where the prep stands, and the item has a key that files a new one
  (office_standing write_prep, place_of; office_home prep_item_words).
- The prep's item and `office status` say when the prep is out under an
  older doctrine (office_bale doctrine_lines, prep_words).
- `office probe --prep [SID]`, and a prep's run line `# office: probe
  --prep SID [--project NAME]`, run a prep's probe under the prep's id
  (office_probe recorder, prep_where, preps_out).
- `office probe` refuses a block whose office-on call names no project
  literally, and warns of a one-word shell line, before anything runs
  (office_probe call_words, check_calls).
- `office drop` offers `r` to read the clipboard again after a no; `office
  slip` ends saying the box and its count.
- `office desk` and `office map` name the asks out, and the desk an ask's
  record left without its tray (office_bale ask_desk_lines; office_map
  ask_lines).
- Clean-ups: README's branch_prefix sentence; the dead bundle plumbing;
  the fake bale's dossier held to its repo, and handoff saying a record in
  two places (office_bale record_places); the spanning tests in one
  module; start's background lines quiet piped too (START_RUNNING).

### Why

A prep can run as long as a sitting, and the office could file nothing
for it, compare nothing of it where it is ended, or run its probe at all,
because each of those keyed on a folder and a prep has none. The two probe
checks turn two run-time surprises (`command not found`, exit 127) into
one line before anything runs. The three said lines close small gaps
where the office knew something and did not say it. The clean-ups remove
words and code that had stopped being true or reachable, and make the
suite's fake behave as bale does.

### How to explain each piece

- A prep's paper lives in the calendar, because that is the meeting's
  space; everything else about it works as a sitting's does.
- The probe reads its calls before it runs them; a name it cannot read
  would only fail later, in the middle of the block's output.
- The asks live outside every folder, so the desk and the map list them
  after the folders, in the walk-in's words.
- The fake bale now keeps records per repo, as bale does, so the suite can
  tell where a session really is.

### Questions a reviewer will ask

- *Why not have the prep brief name a folder for its probe?* Decision 4:
  there is none that records the prep, and plan rightly refuses one that
  does not.
- *Does anything new reach a host?* No. A prep's probe reaches what a
  sitting's probe reaches; handoff reads no host past the first record
  (decision 13); the desk and the map read the out tray on this machine.
- *Why is `detail` not simply a debug line?* Decision 16: other verbs share
  it and keep their lines.
- *Why does the map not put the asks in a folder's Next rows?* Decision 10.

### A hand test

1. `office meeting "weekly review every mon 09:00 about alpha"`, then
   `office start --prep` from the home screen when it is near.
2. Copy a standing block the prep's chat printed and press the prep's
   second key (or `office standing --prep`): `calendar/standing-SID.md` is
   committed alone, and the home screen's prep item ends with `step N of
   M: ...`.
3. Copy a probe block the prep returned with `# office: probe --prep SID`
   in its header and run bare `office probe`: `from the block: probe
   --prep ...`, the header, and no History line, said.
4. Hand `office probe` a block with `office-on "$P" ls`: refused, naming
   the line, and nothing runs. With `office-on alpha 'git status; git log
   -1'`: a warning naming `sh -c`, then it runs.
5. Copy an office command, run `office drop`, answer no, copy the message,
   press `r`: the message is dropped.
6. `office slip testing the box`: its last line names the box and the
   count.
7. With an ask out (`office ask ...`), `office desk` and `office map`: an
   `Asks out` block at the end of each.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: prep-and-tidy

### Commit

File, compare and probe a meeting's prep, and tidy: office-src 0.55.0

A meeting's prep has no folder, so its standing is filed in the calendar
as calendar/standing-SID.md (office standing --prep), and the home
screen's item for the prep says where it stands and, with office status,
when it is out under an older doctrine. office probe --prep, or the
prep's run line, runs a prep's probe under the prep's id. office probe now
refuses a block whose office-on call names no project literally, and
warns of a shell line given as one word, before anything runs. office
drop offers to read the clipboard again after a no, office slip says the
box and its count, and office desk and the map name the asks out. Six
clean-ups: README's branch_prefix sentence, the last dead bundle plumbing,
the fake bale's per-repo records with handoff saying a record found in two
places, a sweep that found one test reading its day from the clock, the
spanning-probe tests in one module, and start's background lines said
under OFFICE_DEBUG piped too.

### Review

File, compare and probe a meeting's prep, and tidy: office-src 0.55.0

Look at office_standing write_prep and place_of, office_home
prep_item_words and the prep's two items in home_items, office_bale
doctrine_lines, office_probe recorder, prep_where and check_calls with
call_words, cmd_probe's --prep path and cmd_drop's loop, office_bale
ask_desk_lines and record_places, office_map ask_lines, and detail with
START_RUNNING (notes, decisions 4, 7, 10, 13 and 16). To try it by hand,
follow the walkthrough's hand test. Deliberately untouched: practice-rules,
pages_from_notes, the walk-in's and home screen's tables.

## Structure

- title: A meeting's prep filed, compared and probed, and six clean-ups
- size: medium
- goal: A meeting's prep filed, compared and probed, the probe block checked before it runs, three said lines, and six clean-ups: office-src 0.55.0

## Handbook

### office-src

- a meeting's prep's standing is calendar/standing-SID.md (office_standing.prep_rel, write_prep), filed by office standing --prep [SID], by office probe beside a prep's block, and by the home screen's key beside the prep's item; the block's id must be a prep the calendar's record line names (0.55.0)
- the home screen's prep item says its doctrine (Doctrines.older_stamp on the record line's stamp) and where it stands (office_home.prep_item_words); office status names a prep out under another doctrine (office_bale.doctrine_lines, prep_words)
- office probe --prep [SID] and the run line `# office: probe --prep SID [--project NAME]` plan a prep's probe with office_probe.recorder standing for a folder; where: --project, the run line's, else the meeting's one concern (prep_where); no History line
- office probe refuses at plan time an office-on call whose project is not a bare name and warns of a one-word shell line (office_probe.check_calls over call_words, the plan's `warnings`, said by bin/office before the header)
- office desk and the map name the asks out (office_bale.ask_desk_lines, office_map.ask_lines, both through --machine-file), the desk each ask's record whose tray is gone (office_ask.orphan_words)
- start's detail lines and the tray's per-file line are OFFICE_DEBUG lines within any start, piped too (START_RUNNING, set by cmd_start); the verbs that share detail say their lines when run on their own
- the fake land bale answers `stats --sid` only in the repo that packed the sid; office_bale.record_places reads every place a handoff looks in, no host past the first holding it, and handoff_check says a record found in more than one
- tests/test_prep_and_tidy.py holds 0.55.0's tests, with tests/test_spanning_probe.py TestTheCallsAreReadBeforeTheBlockRuns; the spanning probe's tests are all in tests/test_spanning_probe.py
- tests/test_prep_and_tidy.py TestNoModuleDefinesANameTwice refuses a second top-level def of a name in a lib/ module

#### Front sheet

office-src 0.55.0 gives a meeting's prep what a folder's sitting has. Its
standing is filed in the calendar and shown on the home screen with its
doctrine; its probe runs through the office with --prep. office probe
reads a block's office-on calls before anything runs. office drop can read
the clipboard again after a no, office slip says the box, and office desk
and the map name the asks out. Six clean-ups. Additive: no migration.

## Proposals

- **What:** bare `office probe`, with no run line and no folder that
  records a session open, could offer the preps out beside the folders
  (probe_folders' rows). **Why:** today a prep's probe needs its run line
  or `--prep`; the home screen's `r` key and bare `office probe` read
  folders only. **Scope hints:** office_bale probe_folders,
  office_probe.preps_out; bin/office cmd_probe's bare path.
- **What:** a test that runs the whole suite under a fake day far from
  today, kept as a runner option. **Why:** decision 14's second pass was a
  hand-patched copy; a `--fake-day` on tests/run.sh (setting both fakes'
  default) would keep the sweep honest without anyone remembering it.
  **Scope hints:** tests/runner.py's job environment; the fakes already
  read FAKE_BALE_DAY.
