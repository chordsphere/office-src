# Notes: 2026-11-07-start-handoff-001, a bailout's fresh session sent from the office (office-src 0.52.0)

All four items shipped, and the seam went unused. Every path is inside the
forecast (bin/office, lib, share, templates, tests, README.md, RELEASES.md,
VERSION, doctrine/OFFICE.md, claude/context/front-sheet.md), so there are
no departures to admit. There was no context compaction this session.

Every anchor the brief gave matched the tree I was handed (0.51.0, the
whole tree): open_bundle 4279, start 4376, handoff_line 5917, BALE_VERBS
5932, office_words 5936, the bailout reads at 660, 5988 and 6000, withdraw
5651, cmd_start 5836 and its START_ globals 5847, check_start_bundle 5069,
resolve_hosted_bundle 5117-5123 and its callers 6059 and 6247,
bundle_lands_read 5764, README 548, OFFICE.md 2271-2272, sitting-brief 71,
the fake's verbs at 149, 290, 359 and 504, response_tarball at 92.

## Decisions

The calls the brief left to me, and the places I deviated from a pin,
numbered so you can ratify or correct each one by number.

1. **The History verb is `handed-off`, not `handed off`.** The History
   line's reader (office_helper HISTORY_LINE_RE) takes `[a-z-]+` as the
   verb, so a two-word verb would never read back. The line is `- DATE
   handed-off: SID from the handoff of BAILOUT`, written beside the
   Sessions line `- SID: from the handoff of BAILOUT`, one commit (`office
   start: SID from the handoff of BAILOUT in NAME`). It changes no status.
2. **A third branch inside office_bale.start, with handoff_session beside
   open_bundle.** handoff_session is open_bundle's discipline exactly:
   bale status's open set before and after (exactly one new), the
   report's `session id` and `tarball` rows ([surfaces.handoff]'s
   `sid_line` and `tarball_line`, read by report_rows) held to it, and
   `request-SID.tar.gz` held to status's outbox. Inside start(), a handoff
   skips the office's overlap check (the forecast is bale's, inherited
   from a record the office does not read; bale's gate is the check),
   ships the office's context beside the request even for a session in
   the office (bale's request carries only the handoff and its reading
   plan), and carries no doctrine of the tree's (the request ships no
   tree, so the install's doctrine rides).
3. **No survey before a handoff.** The pin says nothing is written in the
   office when bale refuses, and survey_before_pack commits the survey
   page before bale runs. For a handoff it is skipped (said under
   OFFICE_DEBUG): a refusal leaves the office's HEAD and status exactly as
   they were, which the refusal tests check byte for byte. The cost is
   that the fresh session reads the survey as it was.
4. **On a host the bailout's scratch is removed in the handoff's own
   connection, not the fetch's.** The brief said the connection that
   fetches the request. I rode it on bale handoff's batch, beside the
   status after, as pack and open_bundle already do, so start's one
   `finally: scratch.__exit__` stays the backstop for every kind and the
   fetch stays a plain fetch. The connection count is the same. The
   hosted test checks nothing is left on the host and every connection
   went to it.
5. **How RESPONSE resolves (handoff_check).** A path is taken as given. A
   bare name is looked for here, then the newest browser copy in the
   downloads. A name found in neither, on a project on this machine, is
   handed to bale's own search, as land hands it bale for an apply, and
   said. On a hosted project that is refused, since the file must travel.
   With no RESPONSE, `response-NEWEST.tar.gz` for the folder's newest
   recorded session, here or in the downloads, else a refusal naming what
   it looked for and where. The tarball is read before anything runs:
   response_kind must be bailout, handoff.md must be there, and
   responds_to must be one of the folder's sessions.
6. **Where the bailed session ran is read from bale's records.** A bailed
   session is closed, so open_anywhere cannot see it. handoff_check asks
   for its dossier in the folder's lane project first, the other projects,
   then the office (handoff_places). The dossier also gives three more
   refusals the brief didn't list but that follow from it: a session
   still open ("office land SID lands its bailout first"), one that ended
   otherwise, and a read-only sitting (out of scope by the brief: "the
   office sends sittings itself"). A handoff of an office session works
   the same way and goes out without the project constraint.
7. **The flags.** Refused by name, together in one line: `--merge`,
   `--undo-bale`, `--bundle`, `new`, `--drop` (and `--title`, `--lane`,
   `--size`), `--goal`, `--slug`, `--brief`, `--write`, `--include`,
   `--read-only`, `--sort`, `--prep`, `--planner`, `--words`, `--about`,
   `--sort-first`, `--carry` and `--in-office`. `--branch` is allowed and
   checks out before the handoff (start_check_place). `--on PROJECT` is
   allowed only when it names where the session ran, and refused
   otherwise. `--leave-out`, `--no-rides` and `--refresh` work as for any
   project session. The folder is required (no asking), since the Next
   line names it. `--carry` is refused because riders are carried into the
   folder by forecast, and the office does not know the inherited
   forecast before bale runs. Ratify or tell me to read it from the
   bailed session's attempt scope.
8. **The opener.** Composed by handoff_opener from the request in the
   tray (its manifest's goal and packed_at, and handoff.md's path inside
   it, `context/handoff.md` in the fake). It follows the captured openers
   line for line where it can, swaps "then README.md, my brief" for "then
   context/handoff.md, the handoff the worker of BAILOUT wrote", names the
   folder's brief.md where it rides (or says the folder rides and there is
   no README brief), restates the constraint for a project session, and
   ends with `(This opener is the office's: bale handoff prints none, so
   office-src composed it from the request, in the shape of bale's own.)`.
   The screen says the same before the scissor block. One small change
   from bale's words: its em dash is a plain hyphen, since this text is
   the office's own.
9. **A bailout is kept on the job's page as a `- bailed: SID` line.**
   Item 2 clears the session line when a bailout lands. For the handoff to
   know which job the fresh session takes, the page has to remember the
   bailout, and History alone would have meant matching folders to jobs
   by text. So the merge and undo pages gain one optional field, read
   only when present (read_merge_job and read_undo_job add no key
   otherwise, so every existing page and test reads the same).
   merge_sent and undo_sent drop it when another session is sent.
10. **The undo close's rule (item 3).** From the materials, per path: put
    is the lines in bale/ that before/ does not hold, took is the lines in
    before/ that bale/ does not hold, blank lines left out. A path still
    holds bale's change when the workbench's version at HEAD (git show,
    one connection on a host) has every line of put and none of took. So a
    session that kept some of bale's lines on purpose but restored a line
    bale took away, or dropped one bale put, closes the job. One that
    changed nothing of bale's keeps it open. A path whose change has no
    such line (bale only reordered, or touched blank lines) can't be told,
    is said under OFFICE_DEBUG, and never keeps a job open. Kept open
    means: the page's session line cleared, the landed session written as
    the page's `earlier` line (so the next undo brief names it), the
    materials left, one office commit, and lines naming each path and one
    line that shows it. land-undo prints `undo-open`, and land's Next line
    becomes `office start N --undo-bale` in place of deliver's line.
11. **land's exit code after a bailout stays 1**, as before (nothing
    landed). The Next line is the office line, and `In office words:`
    maps `bale handoff` to it.
12. **The fake bale's bailout and handoff are not captures** (no real
    bailout exists on your machine), and land_bale.py's docstring and the
    consumption file say so. The fake's bailout apply records an attempt
    with outcome bailout, closes the session, keeps the scope it had (as
    bale keeps the parent's recorded forecast) and prints a next-step
    line naming bale handoff. Its handoff reads the parent's request from
    the outbox as the fake's stand-in for `.bale/sessions/SID/
    manifest.json` (FAKE_BALE_RECORD_GONE makes it missing). It refuses a
    detached HEAD, a non-bailout and a bailout with no handoff.md, runs a
    disjointness gate, keeps the slug, writes `request-001/context/
    handoff.md`, and prints the summary rows. The row starts are the same
    format_summary_block spacing as open's captured `  tarball:        `.

## Item 4: what went, and what stayed

- **Gone:** resolve_hosted_bundle (the function and its two callers) and
  bundle_lands_read's bare-name branch (its find-download fallback and the
  debug line for a bundle that is not a file). Since 0.49.0 every bundle
  start takes is a file: resolve_bundle returns `readlink -f` of a file or
  find-download's path, and the offer's choice is `readlink -f` too. So
  `[ ! -f "$bundle" ]` was never true in either. Neither land nor the
  offer calls them; land has its own response search.
- **Stayed:** START_BUNDLE_FOUND, as the brief says (it feeds
  --bundle-found). Two lines of the same shape as the dead code stayed
  too, because the brief scoped item 4 to the three named pieces: the
  `bundle_here` fallbacks to START_BUNDLE_FOUND in offer_sort_first and
  in start new (`[ -f "$bundle" ] || ...`). They are just as unreachable
  now. And the Python side that reads --bundle-found (start's `bundle and
  argv is None` branch) only acts when the bundle's own pack line does
  not read where it was named, which is the same file bale found. A
  proposal below.

## The suite

- Baseline, the unchanged 0.51.0 tree: 1437 tests, OK, 633 s on two CPUs.
- With the change: 1462 tests, OK, 773 s on two CPUs (25 of them new, in tests/test_handoff.py), on a machine also running another test job for part of the time.
- New: tests/test_handoff.py, 25 tests. Touched: tests/test_land.py
  (response_tarball writes a bailout's handoff.md), tests/
  test_from_the_artifact.py (the pinned bailout line moved to the new
  one, and its header says so), tests/fakes/land_bale.py. No other test
  needed a change. test_undo_bale's own responses take bale's change out,
  so the close's check passes them as before.
- No test hard-codes a day or a VERSION, and nothing is named `m10_`.
  tests/fast-tier.toml is unchanged, since no verb was added.
- validation.sh runs the fast tier with test_handoff and the two pinned
  classes of test_from_the_artifact, and behind `--slow` the modules this
  change reaches. In a staged copy (0.51.0, files/ overlaid, apply.sh run)
  every check passed: 1m15s without `--slow` (the fast tier 395 tests),
  4m57s with it. On the unmodified tree every change-dependent assertion
  fails as it should; the three that pass there (the banner at 299,
  START_BUNDLE_FOUND feeding --bundle-found, bin/office's exec bit) guard
  what must not move. Nothing was written in the staged tree.

## Walkthrough

### What changed

- `office start FOLDER --handoff [RESPONSE]` (bin/office cmd_start's flag
  and start_handoff; lib/office_bale.py handoff_check, handoff_session,
  handoff_opener, and a third branch in start). It reads which bailout
  and where it ran, runs bale handoff there, fills the tray, records the
  session and puts the office's opener on the clipboard.
- A bailout's Next line, and `bale handoff` in office words, is `office
  start N --handoff RESPONSE (bale handoff runs in REPO; ...)`
  (handoff_line).
- share/bale-consumption.toml declares [surfaces.handoff], and
  share/verbs.toml and the doctrine's session kinds gain `handoff`.
- A merge or undo job's session line: cleared when office withdraw closes
  the session or its bailout lands, the bailout kept as `- bailed:`
  (office_deliver.job_session_ended, called from office_bale.withdraw and
  land_outcome), and replaced on handoff (job_handed_off, `deliver_py
  job-handoff`). The merge line says `sends another in its place`.
- The undo close checks each path (bale_change, still_holds, held_paths,
  kept_open in office_deliver; land-undo's `undo-open`; land's Next line).
- resolve_hosted_bundle and bundle_lands_read's bare-name branch are gone.

### Why

A bailout was the last place the office sent you to type a bale verb in a
repo. Now it's one office line, like every other outcome of a landing. A
job page that named a session which would never land kept deliver asking
you to land it. And a closed undo job is trusted by the next delivery for
its paths, so closing one whose session changed nothing would have let
bale's change leave.

### How to explain each piece

- The handoff is a pack where bale chooses the goal and forecast: bale
  copies them from the session that bailed. The office does everything
  else it does for a pack, and writes the opener bale doesn't print.
- The job's line follows its session: withdrawn or bailed, it's cleared
  and the job is offered again; handed off, the new session takes it.
- The undo close asks one question per file: is bale's change still all
  there? If so, the job stays open and says which file.

### Questions a reviewer will ask

- *Why not ask bale for a --json report?* bale handoff has none. The two
  rows read here are the summary block bale prints for every request it
  makes. A slip for bale is proposed below.
- *Why is the survey skipped?* So that a refusal of bale's leaves the
  office as it was (decision 3).
- *What if the bailed session's response is not in the downloads?* On
  this machine bale's own search gets the name; for a host, start refuses
  and says to give the path.
- *Can a handoff's session overlap another open one?* bale's gate refuses
  it, and the office adds the line that frees the forecast.

### A hand test

1. Send a session out on a project (`office start N --on P --goal ...`),
   and have the worker bail out (a response with response_kind bailout
   and a handoff.md). Save it in your downloads.
2. `office land N`: it says `Bailed: ...` and ends with `Next: office
   start N --handoff response-SID.tar.gz (...)`.
3. Type that line. Check the tray holds the request with handoff.md in
   it, and that the opener names handoff.md first, the folder's brief and
   the constraint, and ends with the office's line.
4. `office sessions N` shows the new session, and the folder's History
   has a `handed-off` line.
5. On a real bale, check that bale status lists the new session and that
   the request in the tray is the outbox's.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: start-handoff

### Commit

Send a bailout's fresh session from the office

office start N --handoff [RESPONSE] runs bale handoff where the bailed
session ran, here or through the project's shell on a host, reads which
session it opened from bale status before and after, fills the out tray
as a pack does and records the session in the folder with a handed-off
line. bale handoff prints no opener, so the office writes one in the shape
of bale's and says it is the office's. A bailout's Next line is now that
office line. A merge or undo job's session line is cleared when its
session is withdrawn or bails, and taken by the session a handoff sends.
An undo job closes only once the workbench no longer holds bale's change
in its files. Two pieces of bundle plumbing that nothing reached are gone.

### Review

Send a bailout's fresh session from the office

Look at office_bale.handoff_check, handoff_session and start's handoff
branch, bin/office start_handoff, and office_deliver's job_session_ended,
job_handed_off and held_paths (notes, decisions 2, 9 and 10). To try by
hand, follow the walkthrough's hand test. Deliberately untouched: bale's
own handoff (no --json, no opener, no kept constraints: a slip below), a
handoff of a planner sitting, m10-status-more's lines and practice-rules.

## Structure

- title: Send a bailout's fresh session from the office
- size: medium
- goal: Send a bailout's fresh session from the office, and keep a job's session line true: office-src 0.52.0

## Handbook

### office-src

- office start N --handoff [RESPONSE] (bin/office start_handoff) runs `reader handoff-check` (office_bale.handoff_check: the bailout read and refused before anything runs, where it ran read from bale's dossiers) and then `reader start --handoff T --handoff-sid S`, whose handoff branch runs office_bale.handoff_session (bale handoff, the open set before and after, the report's two rows) and handoff_opener
- bale handoff (0.4.56) prints no opener, has no --json and keeps no constraint; [surfaces.handoff] reads its summary rows `  session id:     ` and `  tarball:        `
- a folder records a handoff as `- SID: from the handoff of BAILOUT` in Sessions and the History verb `handed-off`
- a merge or undo job's page may carry `- bailed: SID`; office_deliver.job_session_ended clears a job's session line (office withdraw, a landed bailout) and job_handed_off gives it to the fresh session
- close_landed_undo checks each path first (bale_change, still_holds, held_paths); a path that still holds bale's change keeps the job open (kept_open), and land-undo prints `undo-open`
- the suite's fake bale (tests/fakes/land_bale.py) lands a bailout and runs bale handoff, built from bale's code, not captured
- tests/test_handoff.py holds 0.52.0's tests

#### Front sheet

office-src 0.52.0 sends a bailout's fresh session from the office. When a
worker bails out, `office land` ends with `office start N --handoff
RESPONSE`, which runs bale handoff where the session ran, fills the out
tray as for a pack, records the session in the folder, and gives you an
opener the office wrote, since bale prints none. A merge or undo job whose
session is withdrawn or bails no longer names it, and a handoff's session
takes its place. An undo job stays open when the workbench still holds
bale's change. Additive: no migration.

## Proposals

- **What:** a slip for bale-src: `bale handoff --json` with the sid, the
  tarball and an `opener` key, and the parent's constraints and
  out_of_scope carried into the handoff's request. **Why:** the office
  reads two text rows and composes the opener and the constraint itself,
  because bale prints neither. A --json report and kept constraints would
  let start drop handoff_opener and read the handoff as it reads an open.
  **Scope hints:** bale's cmd_handoff; then office_bale.handoff_session
  and [surfaces.handoff].
- **What:** take out the last of the bundle plumbing that 0.49.0 made
  dead: the two `bundle_here` fallbacks to START_BUNDLE_FOUND (start new,
  offer_sort_first), and with them --bundle-found and start's
  `bundle_found` reading. **Why:** every bundle start takes is a file, so
  the fallbacks never fire. --bundle-found only matters when a bundle's
  pack line does not read where it was named, and that's the file bale
  found anyway. The brief kept START_BUNDLE_FOUND live this release.
  **Scope hints:** bin/office cmd_start and offer_sort_first,
  check_start_bundle; office_bale.start's `bundle and argv is None`
  branch and the parser's --bundle-found.
- **What:** offer the handoff wherever a job's bailout is shown: the
  status line, the home screen and the walk-in's Next line, for a job page
  with a `bailed` line. **Why:** today those offer `office start N
  --merge` (or `--undo-bale`) for a job with no session, which sends a
  fresh session from scratch. Land's bailout lines name the handoff, but
  the offers don't yet. **Scope hints:** office_bale job_waiting_words,
  waiting_lines, open_words; office_home; it fits m10-status-more.
- **What:** say on the dossier search when the bailed session's record
  is found in more than one place. **Why:** handoff_places takes the
  first project whose bale records the sid, lane first. Real bale keeps
  records per repo, so that's sound. But the suite's fake answers a
  dossier for a sid in any repo, which is why no test here can tell
  "still open in alpha" from "in the office". **Scope hints:**
  tests/fakes/land_bale.py's `stats --sid`, held to the repo that packed
  the sid.
