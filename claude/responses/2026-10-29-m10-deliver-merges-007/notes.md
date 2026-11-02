# Notes: 2026-10-29-m10-deliver-merges-007, office-src 0.40.0

All six items are built, with tests, and the release is cut: VERSION,
RELEASES.md, README.md, the doctrine past its banner, share/verbs.toml and
the front sheet. Every changed path is inside the forecast. No probe, no
light block, no clarification; no compaction.

What ran here, observed, in the work tree with the change applied:
`tests/run.sh --fast` with this session's fourteen names (370 tests,
73.3 s of the 120 s budget); the touched modules whole (test_deliver_merges,
test_host_refresh, test_audience_line, test_clean_delivery,
test_delivery_words, test_three_gaps, test_bale_own_commits, test_start,
test_land, test_office, test_suite_clock, test_desk_verbs: 519 tests, ok);
and, once, the whole suite (1168 tests in 35 jobs, 631 s, ok). The
validation.sh runs the first and, behind `--slow`, the second. The
session-specific assertions fail on the base tree (the doctrine one is the
exception by design: it pins that the core did not move).

## Decisions to ratify (each a flagged deviation or a call the brief left to me)

1. **No MERGES marker line.** The brief offered a `--- MERGES AUDIENCE/BASE
   SHA ---` line read beside LANDS, or deliver finding the landed job. I
   took a third shape that covers both: the job is a page in the folder,
   `merge/merge.md`, field lines read back by `read_merge_job`; `office
   start N --merge` writes `- session: SID` on it once the session is
   packed; `office land` makes the merge commit when the session it just
   landed is the one the page names; and the next `office deliver` makes
   it when land could not (a session open in the clone, a host that did
   not answer, a project with no author). Land never reads a brief (it
   has none in hand), so a marker would have needed land to find the
   request; the page is already in the folder, rides with it, and is the
   job's whole state. The pinned marker rule ("if you take the MERGES
   design") therefore does not engage.

2. **"The merge commit has the session's landed tree and nothing else."**
   Taken literally (the commit's tree is the session's landed tree), the
   merge commit would undo every change the audience made outside the
   conflicting files: the session ships only those files, so the landed
   tree holds the workbench's version of everything else, while the merge
   claims the base as a parent; the next squash from the base would then
   deliver the reverse of the audience's work. So the tree is git's own
   merge of everything that did not conflict, and for each file the job
   names, the version the landed tip holds (removed when it holds none).
   The office resolves nothing: a path still unmerged that the job does
   not name aborts the merge and checks the abort. `TestTheMergeSession
   .test_land_makes_...` pins README.md, which the audience changed
   cleanly, surviving the merge. Please confirm this reading.

3. **The first parent is the workbench's tip after the landing**, which
   must hold `applied/SID` (bale's landing merge, plus its record commit
   after it), not the tag itself; the resolution is read from that tip.

4. **A continued delivery's conflict.** "With the branch's tip in the
   base's place": the job brings the branch's tip into the workbench. Its
   files are the union of what the range's cherry-pick conflicts in and
   what a trial merge of the tip into the workbench conflicts in (so the
   merge land makes conflicts nowhere the session did not resolve), its
   three versions taken from the merge base of the two, the workbench and
   the tip. After that merge, the next delivery reads from where the
   workbench and the branch meet (the merge base of the branch and the
   workbench, when it is neither an ancestor of the last delivery's
   workbench commit nor on the base), and the sessions this folder's (or
   the joined folder's) records on that branch already carry are not
   named again. For a clone on a host, the tip has to be in the clone at
   land: land says `office projects refresh NAME` brings it, and deliver
   then makes the merge.

5. **The merge session writes no Walkthrough, Delivery or Structure**, and
   land leaves the folder's pages as they are for it (said in one line).
   The doctrine says every session that works a folder writes Structure;
   the new paragraph past the banner states the merge session's
   exception. The brief's "what every session owes" for it is therefore:
   Questions and answers, Handbook facts, a `## Merge` section (what each
   file kept from each side), and the Sort of any drop that rides.

6. **The content test** is a squash in a temporary worktree at the base
   (not `git merge-tree --write-tree`, which needs git 2.38); the history
   test stays first. When the delivery commit is not where the delivery
   is built (always the case for a hosted project's temporary mirror), it
   is fetched by its branch into `refs/office/audience/held`, one more
   ref the office removes with its others. When the branch is gone from
   the audience and the commit is nowhere, the test cannot run, and the
   refusal says so in parentheses after "by history or by content". For a
   clone on this machine the commit stays reachable through the
   remote-tracking ref the delivery's push updated.

7. **Held sessions** leave this folder's own list as well as `others`, so
   the delivered line never names them again even when this folder had
   them recorded (a session another folder delivered with `--others-too`).

8. **A folder in the filing cabinet** gets no materials (filed paper only
   grows, and the materials leave the folder once the merge is made); the
   line names `office reopen N`. `office start N --merge` refuses one too.

9. **`merge`** is declared in share/verbs.toml as a project-session kind
   (attended, manual, lands nothing of the office's) and has a row in the
   doctrine's verbs table; test_office's table-covers-the-declarations
   test holds the two together.

10. **One remedy reworded that the brief did not name:** the squash from
    the base that conflicts when the base could not be brought in (a dirty
    clone, an open session, a stale view) used to say "bring main into
    the workbench branch first (merge or rebase there)". It now repeats
    why the merge did not run and names `office deliver N` (and `office
    projects refresh` for a stale view). tests/test_audience_line.py's
    assertion moved with it.

## Places to look closely

- `_RESOLVED_SCRIPT` and `make_resolved_merge` in lib/office_deliver.py:
  the merge commit, the per-file take of the landed version, and the
  abort-and-check path (exit 4, 14, 15 abort; 5, 6, 7 are the
  half-done states, raised as a DeliverError naming the clone).
- `range_commit`: two temporary trees written through private index
  files (`git rm -f --cached` is needed there: that index matches neither
  the worktree's HEAD nor its disk), cherry-picked with `--no-commit`.
- plan's step 6 rule for the meeting point (decision 4): it is a
  heuristic on ancestry, and I would like a second pair of eyes on it.
- `resolve_landed_job` runs on every deliver; it costs nothing when the
  folder holds no job, and refuses the delivery only when a landed
  session's merge could not be made (what it would squash is not the
  folder's own work alone until it is).

## Remaining terminal lines (not in this release's items)

The pin says every refusal's Next line is an office line. Every conflict
and merge path now ends in one. Three deliver refusals that are not about
merging still point at a terminal, and I left them: `take_out_own`'s
"undo its change to PATH by hand on the workbench branch"; the fetch
failure's "check them (git ls-remote there, by hand)"; and the two
"look at the clone (git status there)" lines for a merge whose abort
itself failed (a state that should never happen). They are in the
manifest's deferred list and proposed below.

## Proposals

- **What:** give take_out_own's refusal an office line: a session that
  undoes bale's own change on the workbench (`office start N` with a
  composed goal, the way --merge composes one). **Why:** it is the last
  ordinary deliver refusal that sends the occupant into the clone.
  **Scope hints:** lib/office_deliver.py take_out_own and plan step 7;
  bin/office start.
- **What:** `office status` naming a folder whose merge job waits (no
  session sent, or one sent and landed without its merge). **Why:** the
  job is only said when the occupant runs deliver; the desk and the
  walk-in could offer `office start N --merge` by key. **Scope hints:**
  lib/office_deliver.py read_merge_job; lib/office_home.py and the desk's
  Next line; after home-screen-offers.
- **What:** a test that runs the whole loop through the terminal (deliver
  refuses, `office start N --merge`, a response landed through `office
  land`, deliver again). **Why:** each step is tested, and land's step on
  a real landing, but the classes join the steps in-process. **Scope
  hints:** tests/test_deliver_merges.py, the land fake.

## Walkthrough

### What changed

- The merge session. When bringing the audience's base into the
  workbench conflicts, `office deliver` aborts and checks the merge as
  before, then writes the merge's materials into the folder under
  `merge/`: each conflicting file in three versions (`parted/`,
  `workbench/`, `audience/`), `log.txt` with the audience's commits since
  the two sides parted, and `merge.md`, the job's page, committed in the
  office. Its last line is `office start N --merge`. That start packs a
  bale session on the project whose goal, forecast and brief (the new
  templates/merge-brief.md) are the job's, and names the session on the
  page. When it lands, `office land` makes the resolution a merge commit
  in the workbench (`Bring origin/main into the workbench, resolved by
  SID (office land)`), records a `merged` History line, and takes the
  materials out of the folder; the next `office deliver` makes it when
  land could not.
- A review merged as a squash is seen by content: `base_holds` tries the
  history test, then squashes the record's delivery commit onto the base
  in a temporary worktree and reads "nothing staged" as held. The refusal
  says which test failed.
- A continued delivery is squashed from its range: the range's net
  change, as one temporary commit, cherry-picked onto the branch's tip.
  A branch that moved on the audience and conflicts sends a merge session
  for its tip.
- Sessions the base holds leave the others list and the delivered line,
  said in one line.
- `office letterhead check --added --on PROJECT` works.
- deliver's closing line: `letterhead on the lines it adds and the words:
  clean`.

### Why

The M10 report's last clause on delivering: when the workbench and main
conflict, the office sends a merge session, never the occupant to a
terminal. The other four are the proposals deliver-adds and
wave-one-release left: a squash-merged review blocked the next delivery
forever, a second delivery to the same branch conflicted with itself,
held sessions were still asked about and named twice, and the hand check
refused a pair its module already took.

### How to explain each piece

- The merge session is a session like any other on the project, whose
  only job is to write the conflicting files as they should read; the
  office then records the merge git would have made had there been no
  conflict, with the session's files in it.
- The content test asks "would applying that delivery again change
  main?"; no means main already has it.
- The range squash is "apply what changed since the last delivery", not
  "apply everything since the branch began".
- The materials are the three versions a person resolving by hand would
  look at, put where a session can read them.

### Questions a reviewer will ask

- Does the office ever choose a side? No. Files the job names take the
  session's landed version; anything else unmerged aborts the merge.
- What if a session is open in the clone when the merge session lands?
  The merge commit is not made under it; land says so, and the next
  deliver makes it once nothing is open.
- What if the review was merged with changes to the same lines? The
  content test does not hold it, and the refusal stands with its remedy:
  the work left twice would conflict.
- Where do the materials live after the merge? In the office's git
  history; the folder no longer holds them.

### A hand test

1. On a project with an audience, make the audience's main change a line
   the folder's work changed; `office deliver N` should refuse, name the
   files and end with `office start N --merge`; look at
   `desk/FOLDER/merge/` (three versions, log.txt, merge.md) and at `git
   status` in the clone (clean).
2. `office start N --merge`; read the brief in the out tray and the
   forecast; check merge.md now names the session.
3. Land its response with `office land`: the merge commit in the clone
   (`git log -1 --format='%P %s'`: two parents, the subject naming the
   session), the History line, `merge/` gone from the folder, and the
   folder's walkthrough.md and delivery.md unchanged.
4. `office deliver N`: the branch's commit should be the folder's own
   work against main's tip.
5. After a reviewer squash-merges a review on the git host and deletes
   the branch, deliver a second folder whose landed work carries the
   first one's session: no refusal, one line saying the session is on
   main already, no `--others-too` question.

## Delivery

- to: nobody

### Commit

office-src 0.40.0: a merge session for a conflicting delivery

When bringing the audience into the workbench conflicts, office deliver
leaves the clone clean, writes the merge's materials into the folder
(each conflicting file in three versions and the audience's log) and
names office start N --merge, which sends a session with both sides in
context; office land makes its landed resolution a merge commit in the
workbench, and the next delivery carries the folder's own work. A review
merged as a squash is now seen by its content, and the sessions the base
already holds are no longer asked about or named again. A delivery onto
a branch carries only what is new since the last one there. office
letterhead check takes --added with --on PROJECT, and the delivery's
closing line says it read the lines the delivery adds.

### Review

office-src 0.40.0: no delivery ends at a terminal

What to look at: the merge session's section and plan's steps 4c, 6 and
7 in lib/office_deliver.py, templates/merge-brief.md, start's --merge and
land's merge step in bin/office, and the 0.40.0 entry in RELEASES.md.

What to try by hand: a conflicting deliver, then office start N --merge,
office land and office deliver again; a second delivery to the same
branch that edits a line the first delivered; a delivery after a review
was squash-merged on the git host.

Deliberately untouched: the refusal of a bale commit that cannot be taken
out (it still names a hand step), the credential check of a failed
fetch, and the refresh.

## Structure

- title: office-src 0.40.0, the merge session and deliver's squash fixes
- size: high
- goal: Release office-src 0.40.0: when a delivery's merge or squash conflicts, deliver sends a merge session on the folder and makes the landed resolution a merge commit, never the occupant to a terminal; a review merged as a squash is seen by content; a continued delivery is squashed from its range; a session the base holds leaves the others list; letterhead check --added works with --on PROJECT, and deliver's closing letterhead line says what it reads

## Handbook

### office-src

- A folder's merge job is `merge/merge.md` in the folder (field lines `project`, `audience`, `kind` base or branch, `branch`, `tip`, `workbench`, `parted`, `day`, one `file` line per path, and `session` once office start --merge sent one), beside `parted/`, `workbench/`, `audience/` and `log.txt`; `read_merge_job` reads it, and the page is the job's whole state.
- office land makes a merge session's merge commit only when the folder's merge page names the session it just landed (`office_deliver land-merge`, run only when `merge/merge.md` exists); every office deliver tries the same step first (`resolve_landed_job`) and refuses only when a landed session's merge could not be made.
- The merge commit's tree is git's merge of the side's tip into the workbench's tip with each file the job names taken as the workbench's tip holds it; anything else unmerged aborts it, checked (`_RESOLVED_SCRIPT` exits 4, 14 and 15 after an abort; 5, 6 and 7 mean the abort itself failed).
- `base_holds(repo, rec, where)` returns `("by history" | "by content" | None, why)`; with no `where` it runs the history test alone. The content test squashes the delivery commit onto `refs/office/audience/base` in a temporary worktree and fetches it by its branch into `refs/office/audience/held` when it is not in the repo.
- A delivery onto a branch with a known starting point cherry-picks `range_commit`'s temporary commit (since and the cleaned tip, bale's paths out of both, each tree written through a private GIT_INDEX_FILE) onto the branch's tip with `--no-commit`; a delivery from the base keeps `git merge --squash`.
- The merge session's brief is templates/merge-brief.md, rendered by `merge_start` through `render_template` with title, folder, rel, project, side, tip, workbench, parted, where, files and materials.
- tests/test_deliver_merges.py builds on test_host_refresh's RefreshCase (the fake bale there answers `bale status --json` only); a test that packs swaps it for test_start's FakePackBale, and the office land test uses test_land's LandCase.

#### Front sheet

office-src is at 0.40.0. No delivery ends at a terminal now: when the
audience's main conflicts with the workbench, `office deliver N` leaves
the clone clean, writes the merge's materials into the folder and tells
you to run `office start N --merge`; land that session's response with
`office land` and the office makes the merge commit itself, then
`office deliver N` delivers the folder's own work. A review merged as a
squash on the git host no longer blocks the next delivery, sessions
already on main are not asked about again, a second delivery to the same
branch carries only what is new, and `office letterhead check --added
--on PROJECT` works. Still open: a bale commit of its own that deliver
cannot take out still names a hand step, and the home screen does not yet
offer a waiting merge session by key.

## The re-attempt (after the HOLD of 2026-11-02)

The held attempt failed one test in its fast tier on your machine:
test_audience_line.TestDeliver.test_a_conflict_with_the_audience_refuses_and_names_the_remedy.
The cause is the suite's world, not the release: the test's world has no
fake bale, so whether deliver's clean merge runs depended on the machine.
On yours a real bale on the PATH reads the clone's empty registry, the
merge runs, conflicts, and takes 0.40.0's merge-session path; in my
sandbox no bale was on the PATH, the sessions could not be read, the merge
was skipped and the squash conflicted as the test expects. (Under 0.39.0
the same test on your machine would have met that release's conflict
refusal too; the test was simply never in a validation's names before.)

The fix is in the test alone: a fake bale first on its PATH holds a session
open in the clone, so the clean merge never runs on any machine, and the
test still checks the squash conflict, the line that says why the base was
not merged, the office-line remedy, and that no merge materials were
written. Nothing else changed. I reran the touched modules whole with a
stand-in for a machine bale on the PATH (answering `bale status --json`
with no session, as yours does): before the fix that one test failed and
the other 519 passed; after it, it passes with and without the stand-in.
The response's `corrects` names the held attempt.
