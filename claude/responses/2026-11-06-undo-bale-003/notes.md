# Notes: 2026-11-06-undo-bale-003, bale's own change taken out of the workbench through a session (office-src 0.51.0)

All four items shipped, and the seam went unused. Every path is inside the
forecast (bin/office, lib, share, templates, tests, README.md, RELEASES.md,
VERSION, doctrine/OFFICE.md, claude/context/front-sheet.md), so there are
no departures to admit. There was no context compaction this session.

Every file:line anchor in the brief matched the tree I was handed (0.50.0,
the whole tree): take_out_own 481-543, merge_job_lines 1156, cmd_start
5818, 5849, 5918, 6108-6125, 6336, land 7301-7307 and 7383, office_bale
1361, 1712, 2314, 2325, 2423, 2445, 2457, office_home 720, README 183,
1335, 1741 and 1862, OFFICE.md 1085, 1227, 1645, 1646, 1651, 1665 and 1815,
verbs.toml 379, 411 and 693. None disagreed with its anchor.

## Decisions

These are the calls the brief left to me, plus the places I deviated from
a pin. They're numbered so you can ratify or correct each one by number.

1. **The undo job has a page of its own, undo/undo.md, not a third kind
   on merge.md.** read_merge_job requires audience, branch and tip, and
   MERGE_KINDS is base or branch. An undo job has none of the three. One
   page would have meant a reader that requires nothing, plus a branch in
   every `{audience}/{branch}` line. Instead, `office_deliver.folder_job`
   reads either page and `is_undo` tells them apart. office_bale's offers
   (`job_flag`, `job_waiting_words`) and office_map branch on that, and
   every list that held merge jobs holds both kinds. The page's fields are
   project, commit, subject, workbench, parent, day, earlier, a `file:`
   line per path, and session.
2. **carry_materials serves as it is.** The call is parted = `sha^`,
   workbench = the workbench's tip, audience = `sha`, log from `sha^`, in
   the repo take_out_own ran in. That's the clone here, or the mirror a
   hosted delivery is built in, so nothing new crosses to a host. After the
   carry, parted/ is renamed before/ and audience/ is renamed bale/.
   log.txt is dropped, since it only ever holds bale's one commit, and
   bale.diff is written from the same repo (`git show SHA -- PATHS`). One
   small widening: bale/ holds every file the commit changed, not only the
   refusing ones, because the copy step copies bale's whole change set.
   That set is small by nature, and it lets the session see all of what the
   commit did. before/ and workbench/ hold the job's paths only.
3. **The deviation that matters most: the next delivery takes the
   session's paths as the workbench holds them, read from the `undone`
   History line.** The brief expected the next take-out to find bale's
   commit already undone (`nothing left to undo`) on its own. git does not
   behave that way. Reverting bale's commit on the session's result is a
   three-way merge: base is bale's version, ours is the session's result,
   and theirs is the version before bale's commit. Later work sitting next
   to bale's lines is exactly what made the job, and that still makes the
   revert conflict after the session has taken bale's change out
   correctly. I checked this in a scratch repo with the whole loop's
   .gitignore (`*.pyc` → `.bale/` → `.bale/ *.log` → the session's
   `*.pyc *.log`), and the revert conflicts again. So land's `undone` line
   names the commit, the paths and the session (`bale's own commit SHA7
   (SUBJECT) taken out of PATHS by SID`). The plan reads that line through
   `undone_records` into take_out_own's new `undone` argument, and
   take_out_own takes each such path as the workbench holds it, before it
   judges any conflict. The plan says `nothing left to undo: the undo
   session SID took it out of PATHS on the workbench`, or names those
   paths beside "undone" when the commit had other files. Look at this
   closely on review. It trusts the session for its paths. A session that
   ships nothing for a path leaves bale's change in that path, and the
   delivery carries it. For bale's commonest case, a `.bale` line, the
   letterhead's marks are still the backstop. Proposal 1 is the
   stronger check.
4. **land makes no commit of its own,** as you read it. The session's
   landed commit is the undo. land checks two things before it closes the
   job. First, that no session is open in the clone, as resolve_landed_job
   checks. Second, that bale's `applied/SID` tag exists there, which is the
   counterpart of _RESOLVED_SCRIPT's exit 13. A session that never landed
   closes nothing and says nothing. Deliver runs the same close before it
   plans (`close_landed_undo`), right after the merge job's step. The
   session still out stops the delivery, naming `office land SID`, and
   another open session stops it naming deliver.
5. **"Writes the job again naming the landed session."** When later work
   touches bale's lines in another of the commit's paths, the next
   delivery refuses on those paths alone. The new page carries
   `- earlier: SID`, and the refusal says which session landed, when, and
   what it took out. tests/test_undo_bale.py pins this case.
6. **One job a folder at a time.** merge_job_lines refuses while an undo
   job is waiting, and undo_job_lines refuses while a merge job is
   waiting. Each names the waiting job's next line (its start, or `office
   land SID` once sent), and nothing is written. A page that does not read
   blocks neither kind. It holds no job, and the next delivery writes its
   own kind again.
7. **The refusal's office line names the folder as deliver names it,**
   by its directory name, exactly as the merge job's line does (`office
   start 2026-11-06-health-route --undo-bale sends the session that takes
   bale's own change out of the workbench`). The brief writes N. Both
   forms resolve, and the walk-in, Next line, status and map use the
   number, as for merge.
8. **The refusal names every path.** Its first line says `changed in A, B
   cannot be taken out`. take_out_own now computes lines_added_only for
   every unmerged path before acting, and raises `UndoConflict` (a
   DeliverError subclass) carrying the sha, the subject and the refusing
   paths. A path that bale only added lines to is still taken out line by
   line and never goes into the job.
9. **One door for both job flags.** `--undo-bale` sets the same `merge=1`
   as `--merge`, with `job_kind` and `job_flag` beside it. The refusals,
   the slug (`-undo`), the brief's temp file and the sent step follow the
   kind. `--merge --undo-bale` together is refused. Anything else beside
   the folder is refused in --merge's words with the flag swapped, and
   what rides plus the refresh's answer are allowed, as for --merge.
10. **`undone` is a new History verb** in office_helper.HISTORY_VERBS. It
    changes no status. The doctrine's sentence on the verbs that change
    nothing names it.
11. **The cap is 200** (`MATERIALS_CAP`). Conflicting files are copied
    with their three versions first, and the copier passes over anything
    already in audience/, so they're never counted. Of the others, the
    first 200 in git's order are copied. The count rides in a file beside
    the copies because xargs may run the copier more than once. A path
    that's listed but not copied is written `- changed: PATH (HOW, not
    copied)`, and the reader gives back `uncopied`. A page from before
    reads with none. carry_materials now returns four values and takes
    `cap=`, and its only caller is merge_job_lines. The page and the brief
    say how many were left and that `git show TIP:PATH` in the clone reads
    them. One caveat: a branch-kind job on a hosted project read its tip in
    the mirror, but that tip is the audience branch's own, which the clone
    has once refreshed.
12. **The empty landing.** The fake bale commits with `--allow-empty` when
    `changes[]` is empty and tags it, as the probe read bale 0.4.56 doing.
    TestAnEmptyLanding pins it through office start --merge and office
    land, ending in the merge commit with the workbench's versions.
    merge-brief.md's pinned sentence stands as it was. I added one sentence
    after it: when the workbench's version is the resolution of every file,
    the response ships no file at all, bale lands it and tags it, and land
    makes the merge commit. make_resolved_merge's exit 13 still names no
    line.
13. **office map says the undo job too** (`undo job waiting`, and its
    `office start N --undo-bale` row). This wasn't in the brief's list, but
    the map is one of the places a merge job is offered.
14. **The pinned refusal test** (tests/test_bale_own_commits.py 207-226)
    now pins the job's words and the job's page, plus a clean office. It
    keeps every "nothing moved" assertion as it was.

## The suite

- Baseline, the unchanged 0.50.0 tree: 1414 tests, OK, 721 s on two CPUs.
- With the change: 1437 tests, OK, 628 s on two CPUs (23 of them new, in
  tests/test_undo_bale.py). No existing test needed to change beyond the
  pinned refusal test.
- The fast tier with this session's names, as validation.sh runs it:
  408 tests, OK, 67.7 s of the 120 s budget.
- validation.sh in a staged copy (0.50.0, files/ overlaid, apply.sh run):
  every check passed, in 1m08s without `--slow` and 3m46s with it (eleven
  modules whole). On the unmodified tree the session assertions fail as they
  should (VERSION, the release, the front sheet, the template, the
  remedy's words, the usage, the doctrine row, the verb, the fake bale's
  empty landing), and so does the fast tier (test_undo_bale isn't there).
- No test hard-codes a day or a VERSION. The record test reads the 0.51.0
  entry by its heading, as the earlier record pins do, and requires
  VERSION at or above it. tests/fast-tier.toml is unchanged, since no verb
  was added.

## Undo, merge and the forecast in one table

| What | Where |
|---|---|
| the job written | office_deliver.undo_job_lines, from plan's step 7 on UndoConflict |
| its page | undo_page_text, read_undo_job, folder_job, is_undo |
| the session sent | bin/office cmd_start (`--undo-bale`), undo_start, undo_sent, templates/undo-brief.md |
| the job closed | close_landed_undo (land and deliver), land_undo, bin/office land |
| the take-out after it | undone_text, undone_records, take_out_own(undone=) |
| the offers | office_bale job_flag, job_waiting_words, open_words, delivery_move, waiting_lines; office_home; office_map |
| the cap | MATERIALS_CAP, _AUDIENCE_COPY, carry_materials(cap=), changed_line, uncopied_words |
| the empty landing | tests/fakes/land_bale.py, templates/merge-brief.md |

## Walkthrough

### What changed

- **The undo job.** take_out_own no longer ends in a remedy that sends
  you into the clone. When one of bale's own commits did more than add
  lines where later work touches them, it raises UndoConflict with every
  path that refused. plan answers with undo_job_lines. That pushes nothing
  and leaves the clone clean, with the worktree removed as before. It
  writes undo/ into the folder: before/, bale/ and workbench/ copies of
  each path, bale.diff, and undo.md. It commits them in the office and
  ends on `office start N --undo-bale sends the session that takes bale's
  own change out of the workbench`.
- **The session.** `office start N --undo-bale` packs a project session on
  the job's project. The forecast is the job's paths, the goal is `Take
  bale's own commit SHA7 (SUBJECT) out of the workbench of folder N, in
  PATHS`, and the brief comes from templates/undo-brief.md. The page names
  the session, committed alone.
- **The landing.** office land runs `land-undo` after an applied landing
  of the session a folder's undo job names. That writes a dated `undone`
  line, removes undo/, commits both, and ends on `office deliver N`. The
  folder's two pages are left as the work's. Deliver closes the job when
  land could not, and names `office land SID` while the session is out.
  The next delivery reads the `undone` line and takes those paths as the
  workbench holds them.
- **The offers.** The waiting job shows on the desk line, the Next line,
  the home screen, `office status` and `office map`, and each place offers
  `office start N --undo-bale` by key.
- **The cap.** A merge job copies at most 200 of the audience's other
  changed files. It still lists every path, marks the rest not copied, and
  says how many are left and how to read them.
- **The empty landing.** The fake bale lands `changes: []` as bale does,
  and the merge brief says an empty response lands.

### Why

Since 0.36.0, deliver took bale's own commits out of every delivery, and
the last way it could fail sent you to a terminal to undo bale's change
by hand. That was the only ordinary deliver refusal left that did so. A
session now does that undo, from the same three versions a merge session
gets. The cap keeps a long-parted workbench behind a busy base from
committing thousands of copies into the office. The empty landing makes
the 0.47.0 rule testable: a merge session may ship nothing.

### How to explain each piece

- The undo job is the merge job's twin. It lives in the folder, it's
  written by deliver, it's sent by one office line, and it's closed by
  land.
- The session decides which lines are bale's. The office never guesses,
  and after the session lands it trusts the session's version of those
  files.
- The `undone` line is the record. It says which commit, which files and
  which session, and the next delivery reads it.

### Questions a reviewer will ask

- *Why does the next delivery need the History line at all?* Because
  git's revert of bale's commit conflicts again on a correctly undone file
  whenever later work sits next to bale's lines (decision 3).
- *What if the session ships nothing for a file?* Then the workbench's
  version stands and the delivery carries it. If that version still holds
  a `.bale` line, the letterhead refuses it. Proposal 1 would check it
  outright.
- *What if both kinds of job would be written?* They can't arise
  together, since a conflicting merge stops deliver before step 7.
  Whichever is waiting is named, and the other waits.
- *Does land touch the clone?* Only to read whether sessions are open and
  whether `applied/SID` exists. It makes no commit.

### A hand test

1. In a project with an audience, commit `.gitignore` with `*.pyc`, then
   make a commit subjected `bale: ignore .bale/` that turns it into
   `.bale/`, then append `*.log` in a commit of your own.
2. `office deliver N`: it should refuse, name `office start N --undo-bale`,
   push nothing, and leave `undo/` in the folder with before/, bale/,
   workbench/ and bale.diff.
3. `office` and `office status`: the undo job should be offered, by key on
   the home screen.
4. `office start N --undo-bale`, then land a response whose .gitignore is
   `*.pyc` and `*.log`. The folder should gain an `undone` line, and undo/
   should be gone.
5. `office deliver N`: the plan should say `nothing left to undo: the undo
   session SID took it out of .gitignore on the workbench`, and the
   audience's .gitignore should hold no `.bale/`.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: undo-bale

### Commit

Send a session to take bale's own change out of the workbench

When office deliver cannot take one of bale's own commits out of a
delivery, because later work on the workbench touches the same lines
and the commit did more there than add lines, it no longer sends you
into the clone. It pushes nothing, writes an undo job into the folder
(every path that refused, in three versions, and the commit's diff) and
names office start N --undo-bale. That sends a session that writes each
file with bale's change taken out. When it lands, office land closes the
job with an undone line in the folder's History, and the next delivery
takes those files as the workbench holds them. The waiting job is offered
wherever a merge job is. A merge job's copy of the audience's other
files is capped at 200, every path still listed. The suite's fake bale
lands an empty response as bale does.

### Review

Send a session to take bale's own change out of the workbench

Look at office_deliver.take_out_own and its new undone argument,
undo_job_lines, close_landed_undo, and the take-out reading the History
line (notes, decision 3). Look at start's --undo-bale branch and land's
land-undo step in bin/office too. To try by hand, follow the walkthrough's
hand test. Deliberately untouched: lines_added_only, own commits outside a
delivery's range, start-handoff, and the status lines planned for
m10-status-more.

## Structure

- title: Take bale's own change out of the workbench through a session
- size: medium
- goal: Take bale's own change out of the workbench through a session, not by hand: office-src 0.51.0

## Handbook

### office-src

- office deliver writes an undo job when take_out_own raises UndoConflict (every path whose revert conflicts and that lines_added_only cannot take out): office_deliver.undo_job_lines writes desk/FOLDER/undo/ (before/, bale/, workbench/, bale.diff, undo.md) through carry_materials with parted = SHA^ and audience = SHA, read in the repo the delivery is built in (the clone, or the mirror for a hosted project)
- office start N --undo-bale runs `deliver_py undo-start` and `undo-sent` (bin/office cmd_start's merge branch, job_kind undo); templates/undo-brief.md is its brief
- office land runs `deliver_py land-undo` (office_deliver.land_undo, close_landed_undo) when undo/undo.md exists: never under an open session, only once applied/SID is in the clone; it writes the History verb `undone`, `bale's own commit SHA7 (SUBJECT) taken out of PATHS by SID`, and makes no commit in the clone; office deliver runs the same close before it plans
- git's revert of a bale commit conflicts again on a file an undo session took the commit out of whenever later work sits beside bale's lines; office_deliver.undone_records reads the `undone` lines and take_out_own(undone=) takes those paths as the workbench holds them
- a folder holds one job at a time, merge (merge/merge.md) or undo (undo/undo.md): office_deliver.folder_job reads either, is_undo tells them apart, office_bale.job_flag gives start's flag
- a merge job copies at most office_deliver.MATERIALS_CAP (200) of the audience's other changed files; a path past it is a `- changed: PATH (HOW, not copied)` line, read back into the job's `uncopied`
- the suite's fake bale (tests/fakes/land_bale.py) lands an empty changes[] as one commit with no change, tagged applied/SID, as bale 0.4.56 does
- tests/test_undo_bale.py holds 0.51.0's tests

#### Front sheet

office-src 0.51.0 sends a session to take bale's own change out of the
workbench, where office deliver used to send you into the clone to do it
by hand. When one of bale's own commits can't be taken out of a delivery,
deliver pushes nothing, writes an undo job into the folder and names
`office start N --undo-bale`. When that session lands, `office land`
closes the job, and the next delivery carries the folder's work without
bale's change. The waiting job is offered by key wherever a merge job is.
A merge job now copies at most 200 of the audience's other changed files
and lists the rest. A merge session may ship no file at all. Additive: no
migration.

## Proposals

- **What:** at close, check that each of the job's paths no longer holds
  bale's change, and if it does, say so and keep the job open. For
  example, check that the commit's added or changed lines aren't all
  still present in the session's version. **Why:** the next delivery
  trusts the session for its paths (decision 3). A session that ships
  nothing for a path leaves bale's change in the delivery, and only the
  letterhead's marks catch a `.bale` line. **Scope hints:**
  office_deliver.close_landed_undo, with bale.diff's hunks read before
  undo/ is removed.
- **What:** let `office withdraw` clear the session line of a merge or
  undo job whose session it withdraws. **Why:** a withdrawn session
  stays named on the page, and deliver keeps naming `office land SID`
  for it. This session added "office start N --undo-bale sends another
  in its place" to the undo line, but the merge line still lacks it.
  **Scope hints:** office_bale.withdraw, merge_sent and undo_sent's
  page writers.
