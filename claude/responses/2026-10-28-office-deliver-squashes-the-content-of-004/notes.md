# Notes: 2026-10-28-office-deliver-squashes-the-content-of-004

office-src 0.36.0: no bale commit leaves a delivery in content any more
than in name. Two changes, the one the goal asks for on each side, plus
a small third the first one forced (the files deliver takes out of the
index are now named never read to the letterhead), their tests and the
record. Additive, no migration.

## What I decided, for you to ratify

1. **Subtract bale's own commits; keep squashing.** Deliver still
   squashes the whole workbench range onto the audience's tip, but first
   it undoes what bale's own commits in that range changed: in the
   temporary worktree, detached at the workbench's tip, `git revert
   --no-commit SHA` for each of them, newest first, each committed as a
   temporary commit (authored as the project's declared author, since a
   commit needs an identity and the clone's is never used), and the
   squash is then made from the result. Those commits live only in the
   worktree and go with it; nothing of them is pushed or left in the
   clone. I chose this over cherry-picking the sessions' work commits
   because the occupant's own commits on the workbench must keep
   delivering, and because a revert is git's three-way merge: a line
   bale added that later work already removed by hand is simply gone,
   with no special case. The plan names each one under `taken out:` (sha,
   subject, files), and `office deliver` logs them as it starts.
2. **What "bale's own" means.** The commits bale makes for itself, with no
   session's work in them: its housekeeping commits, whose subject starts
   `bale: ` (the one capture is `bale: ignore .bale/`, 1ee6bc7 in the
   work office's clone), and its sweeps (`[bale sweep SID] ...`, the
   telemetry record). A session's `[bale SID]` work commit and its `Merge
   bale SID` landing are the work itself and stay in. The `bale: ` start
   is declared in share/bale-consumption.toml beside the other subject
   shapes (`[surfaces.commits] own`), read by `Consumption.own_commit`,
   and pinned to the probe's captured subjects
   (fixtures/bale-0.4.45/watches/git/office-src_subjects.json holds the
   housekeeping commit), so a bale that renames it fails a test rather
   than a delivery. It is bale's convention, not a contract it declares:
   a commit of the occupant's that took the `bale: ` start would be read
   as bale's own. The manifest's comment says so; a slip for bale-src
   (a declared shape, or a mark on the commit) is proposed below.
3. **The sweep is taken out too.** Its record already never left (the
   record directory is on the exclude list), so nothing visible changes
   on a normal delivery, but the rule is now about commits, not about
   which directory a file lives in. The world's sweep shows up as the
   second `taken out:` line in every test delivery, which is right.
4. **A revert conflict: pure additions line by line, everything else
   refused by name.** Where later work on the workbench touches the same
   lines (the two shapes I expect for `.gitignore`: bale created it and a
   later commit appended, which git sees as modify/delete; or bale
   appended and a later commit appended right after it, a content
   conflict), the revert conflicts. When adding lines was all bale did to
   that file (`lines_added_only`, read from the commit's own `-U0` diff),
   bale's lines are taken out of the workbench's version one by one (the
   last occurrence of each; a line already gone is left alone), the file
   is deleted when nothing is left of one bale created, and the plan's
   line says `its lines taken out of .gitignore one by one, since later
   work on the workbench touches the same place`. A bale commit that
   removed or changed lines that later work also touches refuses the
   delivery by name with the remedy (undo its change by hand on the
   workbench branch and deliver again), nothing pushed, the worktree and
   refs removed as for any refusal. I would rather refuse there than
   guess which lines are bale's; the pure-addition case is the real one
   and it is handled without a hand edit.
5. **A bale path is one of the letterhead's marks.** `.bale` (with a word
   boundary after it: `.bale/`, `.bale-bundle`, `.bale-manifest.json`),
   `.baleignore` and `bale.toml` join share/letterhead.toml's marks. The
   goal says "a delivery whose diff names a bale path should be refused";
   the letterhead reads changed files whole, like every other mark, and I
   kept to that rather than add a diff-only check in deliver: one
   mechanism, one list, and the delivery's words are held to it too (a
   Review saying "bale.toml is untouched" is refused at its line, which is
   what the promise means). The consequence worth knowing: a file the
   audience already has that names a bale path refuses any delivery that
   changes that file until the line goes, and the delivery that removes
   the line passes. The suite holds office_host.EXCLUDE_LINES and the
   marks to one list; the record directory is a name already.
6. **The never-delivered files are named never read.** `git rm --cached`
   leaves bale.toml (when the clone tracks it) and the record directory
   on the worktree's disk, untracked, and the check read them as changed
   files. With a bale path a mark, bale.toml's own `.bale/staging` line
   would have refused a delivery it was not in. plan now passes
   `never=NEVER_DELIVERED`, as land's review always did, and the check
   says `N file(s) of bale's never read: bale.toml` when there are any.
7. **The doctrine's core, rewrapped.** Section 2's deliver bullet now
   promises "nothing a bale commit of its own changed" in one clause; the
   mechanism and the new mark are in section 7, past the core. The core
   was 301 lines against its 300-line pin since 0.34.0 (the previous
   session's notes proposed fixing it), and my clause made it 303. I
   rewrapped three ragged core paragraphs at 74 columns (the walk-in
   paragraph, the verbs paragraph, section 2's item 2) with no word
   changed, and the banner is at line 299: test_office's TestTheDoctrinesCore
   passes again. Please glance at the three paragraphs; the diff is only
   line breaks.
8. **0.36.0, additive.** No migration, nothing to do in any office. Folder
   6's branch on its audience keeps the `.bale/` line it was given: the
   release changes what leaves from now on and rewrites nothing on an
   audience; the line is yours to remove on the review by hand if you
   want it gone before the merge.

## Why no probe

The goal names the commit, its subject and what it changed (1ee6bc7,
`.bale/` added to `.gitignore`), and the probe's captured subjects
already hold `bale: ignore .bale/` as a real subject of bale's. The fix
depends on neither folder 6's bytes nor the clone's state: the range is
read from git at deliver, and the suite builds the same shape (a bale
housekeeping commit on the workbench beside a bale-landed session) in a
throwaway world. What I could not check from here is whether the work
office's other clones hold any other `bale: ...` subject; `git log
--format=%s | grep '^bale: '` in a clone would say, and anything it
shows is handled the same way.

## Paths, and the forecast

The request forecasts `.`, so every path is inside it: lib/office_bale.py,
lib/office_deliver.py, share/bale-consumption.toml, share/letterhead.toml,
bin/office, doctrine/OFFICE.md, README.md, RELEASES.md, VERSION,
claude/context/front-sheet.md, and the new tests/test_bale_own_commits.py.
Nothing of the office context (the desk folder, the handbook) lands; the
tests build their world from the suite's own AudienceCase.

## Things you should know

- bin/office changes in two places only: `deliver_show` prints the
  `taken out:` lines after the sessions line, and the two usage texts
  (deliver, letterhead check) say what changed. apply.sh restores its
  exec bit and validation asserts it.
- `commit_words` now shares `identity_of` with the temporary commits, so
  the identity logic (both halves, over any GIT_AUTHOR_* in the
  environment) is written once. Its behavior is unchanged.
- A hosted project's bale commits come here in the bundle as before and
  are undone in the mirror; still three connections, and the test pins
  it.
- `own_commits` reads the range with `--no-merges`, so a merge is never
  taken as bale's own even if its subject started `bale: `.
- The existing TestDeliver tests pass unchanged; their world's sweep is
  now reverted rather than only excluded, and the audience's tree is the
  same.
- **Two whole-module failures that aren't this session's**, both on the
  unchanged tree: test_answer_review's `TestTheRecord` (RELEASES.md has
  no `## 0.33.0` entry; 0.34.0 is followed by 0.32.0) still errors and
  stays out of validation's `--slow` list. test_office's
  `TestTheDoctrinesCore` was the other, and it passes now (decision 7),
  so test_office whole is in the `--slow` list.
- tests/test_bale_own_commits.py: 15 tests. On the unchanged tree 14
  fail (2 on the missing `own_commit`, 12 on behavior and the record);
  `test_plain_words_stay_clean` passes on both trees by design, since it
  guards against false hits from the new marks.

## Validation, as it ran here

The request carries the suite, its fakes and fixtures, so I ran it in
this sandbox (python 3.13, git 2.43), on the change and on the unchanged
tree.

- The new module, 15 tests, passes on the change; 14 fail on the
  unchanged tree as above.
- The touched modules whole (test_bale_own_commits, test_audience_line,
  test_clean_delivery, test_watches_digest, test_delivery_words): 134
  tests, all passed. The fast tier with the new module: 356 tests in
  54.8 s of its 120 s, alone.
- The whole suite, once, on the changed tree: 1043 tests, every module
  ok but test_answer_review, whose record pin errors on the unchanged
  tree too (the missing 0.33.0 entry, above). test_office whole passes,
  the doctrine core pin included.
- validation.sh, rehearsed in a staging copy (the request's tree,
  `files/` over it, apply.sh, the manifest as `.bale-manifest.json`):
  every check passed and every claim agrees; the fast tier with the new
  module took 67.8 s of its 120 s (371 tests), the whole script 68 s.
  With `--slow` the six modules whole passed too (2 min 59 s in all).
  One earlier rehearsal ran the tier in 151 s and failed the budget, but
  only because the whole suite was running beside it on the same machine.
- On the unchanged tree the four session assertions fail, as they
  should (no `own_commit`; `.bale/` is no mark; 0.35.0 in VERSION; the
  banner at 301).

## Proposals

- **What:** restore RELEASES.md's 0.33.0 entry. **Why:** still missing on
  this tree, so test_answer_review's record pin errors on every whole
  run and the release history skips a version. The previous session
  proposed it too; nothing changed. **Scope hints:** RELEASES.md between
  0.34.0 and 0.32.0; the 0.33.0 session's notes.
- **What:** a slip for bale-src: declare the shape of bale's own
  commits, or mark them. **Why:** the office now reads `bale: ` as a
  convention from one captured subject; a declared shape (or a trailer
  such as `Bale-Own: housekeeping` on the commit) would make "bale's own"
  bale's statement rather than the office's inference, and let an
  occupant's `bale: ...` commit be told apart. **Scope hints:**
  share/bale-consumption.toml `[surfaces.commits]`; the drafting table's
  slips.
- **What:** `office letterhead check --delivery FILE`, as the previous
  session proposed, now with one more reason. **Why:** a hand
  `--words desk/N/delivery.md` reads the page whole, and a page whose
  heading names a bale path (a folder titled after `.gitignore`'s
  `.bale/` line, like this one) is refused by hand where deliver reads
  only the words that leave. **Scope hints:** lib/office_deliver.py
  `check_in_project` already takes words_text; bin/office's usage.
- **What:** a line in `office status` (or land's review) counting the
  commits of bale's own on a workbench since the last delivery. **Why:**
  the occupant learns of them only at deliver; a count beside the
  project's line would say ahead of time that the next delivery will
  take something out. Small, maybe not worth it. **Scope hints:**
  lib/office_deliver.py `own_commits`; office_bale's project lines.

## Walkthrough

### What changed

- **Deliver takes what bale's own commits changed out before the
  squash** (lib/office_deliver.py `own_commits`, `take_out_own`,
  `lines_added_only`, `own_lines`, `identity_of`; `plan` step 7; bin/office
  `deliver_show`'s `taken out:` lines).
- **The consumption manifest names bale's own commits**
  (share/bale-consumption.toml `[surfaces.commits] own`;
  lib/office_bale.py `Consumption.own_commit`).
- **A bale path is one of the letterhead's marks** (share/letterhead.toml
  `[marks]`: `.bale`, `.baleignore`, `bale.toml`), and deliver names the
  never-delivered files never read to the check (`plan` step 8).
- doctrine/OFFICE.md (section 2's bullet, section 7's paragraph, three
  core paragraphs rewrapped), README.md (deliver's summary and details,
  the letterhead paragraph, the layout rows), RELEASES.md 0.36.0,
  VERSION, the front sheet's Recent changes line, both usage texts in
  bin/office.
- tests/test_bale_own_commits.py (new, 15 tests in five classes).

### Why

On 2026-10-28, delivering the work office's folder 6, bale's own commit
`bale: ignore .bale/` rode in beside the session's work: deliver squashed
the whole workbench range and took only bale's names out of the index, so
a line bale wrote into a file the clone tracks left with the work, and
the letterhead had no rule for a bale path. Deliver promises no bale
commit leaves; it now keeps that in content as well as in name, and the
letterhead refuses a bale path in anything that leaves.

### How to explain each piece

- The take-out: "before deliver squashes the work, it undoes the commits
  bale made for itself, in a scratch copy, so what they changed never
  reaches the audience. The plan lists them under `taken out:`."
- The shapes: "a line bale added that you already removed is just gone.
  If your later change sits on the same lines and bale only added lines,
  bale's lines are picked out one by one and the plan says so. Anything
  else, deliver stops and tells you which commit and file to undo by
  hand."
- The mark: "a line that leaves naming bale's directory, its config or
  its ignore file is refused like any other bale mark, wherever it came
  from. Files bale makes that stay home are not read."

### Questions a reviewer will ask

- *Could the revert drop something of the work?* Only if a commit of
  bale's own and a work commit changed the same lines, and then it
  refuses rather than resolve; a sweep touches only the record file and
  the housekeeping commit only `.gitignore`.
- *Why not cherry-pick the work commits instead?* Hand commits on the
  workbench deliver too, and cherry-picking replays history; reverting
  bale's few commits is the smaller change and keeps the squash's
  conflict behavior as it was.
- *Why a mark on whole files rather than a check on the diff?* One list
  and one mechanism, the words included; a bale path on the audience's
  side already is a thing to remove, and the delivery that removes it
  passes.
- *Does folder 6 need anything?* Its branch keeps the `.bale/` line it
  was given; remove it on the review by hand if you want. Its next
  delivery reads only the range since the last one, so the housekeeping
  commit is not seen again.
- *What if bale commits something else for itself?* A subject starting
  `bale: ` is read as bale's own; another shape is a slip for bale-src
  and the fixture test says when the convention moved.

### A hand test

1. Install 0.36.0 (`office upgrade` in the work office brings nothing
   to do; the install is what changed).
2. In a clone of a work office project: `git log --format=%s
   origin/main..HEAD | grep '^bale: '` shows the housekeeping commits in
   the undelivered range, if any.
3. On a folder whose range holds one: `office deliver N`. The plan shows
   `taken out: what K commit(s) of bale's own changed, which never
   leaves:` with one line per commit, the `changes:` stat without
   `.gitignore` (unless the work changed it too), and the commit's
   `files:` line without it. Answer `n` to see nothing pushed, or `y`.
4. `printf '.bale/\n' > /tmp/w.md; office letterhead check --words
   /tmp/w.md` names `/tmp/w.md:1: marks: '.bale'`.
5. On folder 6's review branch, `.gitignore` still holds the `.bale/`
   line from the first delivery; remove it by hand on the review if you
   want it gone.

## Delivery

- to: nobody

### Commit

Deliver takes what bale's own commits changed out of a delivery

office deliver squashed the whole workbench range onto the audience's
base and took only bale's names out of the index, so a line bale's own
housekeeping commit wrote into the clone's ignore file left with the
work, and the letterhead had no rule for a path of bale's. Now, before
the squash, the commits bale makes for itself (its housekeeping commits
and its sweeps, never a session's work commit or its landing merge) are
undone on the workbench's tip in temporary commits that never leave, and
the plan names each one. A line of bale's that later work already took
out is simply gone; later work on the same lines takes bale's lines out
one by one when adding lines was all bale did there; anything else
refuses the delivery by name with the remedy, nothing pushed.

A path of bale's own (its directory and the files named after it, its
config file, its ignore file) is one of the letterhead's marks, so a line
that leaves naming one refuses the delivery whatever put it there, and
the files deliver takes out of the index are named never read to the
check.

Release 0.36.0, additive.

### Review

Deliver takes what bale's own commits changed out (0.36.0)

What to look at: lib/office_deliver.py take_out_own and plan's step 7,
lib/office_bale.py Consumption.own_commit with the consumption
manifest's new own list, and the three new marks in the letterhead's
rules.

What to try by hand: the walkthrough's hand test, on a clone whose
undelivered range holds a housekeeping commit of bale's.

Deliberately untouched: the branch already delivered for the folder this
was found on keeps the line it was given; the shape of bale's own
commits stays bale's convention, read from one captured subject
(proposed: a declared shape); the hand letterhead check still reads a
file whole.

## Structure

- title: Deliver takes what bale's own commits changed out of a delivery
- size: small
- goal: office deliver undoes what bale's own commits in the delivered range changed (its housekeeping commits and its sweeps, declared in the consumption manifest) on the workbench's tip before the squash, naming each, and a bale path is one of the letterhead's marks, so no bale commit leaves a delivery in content any more than in name

## Handbook

### office-src

- office deliver takes what bale's own commits changed out of a delivery since 0.36.0: the commits in the delivered range whose subject bale gives a commit it makes for itself (a start in share/bale-consumption.toml `[surfaces.commits] own`, `bale: `, or a sweep; office_bale.Consumption.own_commit) are reverted on the workbench's tip in the temporary worktree, newest first, one temporary commit each, before the squash (office_deliver.own_commits, take_out_own); the plan lists them under `taken out:`. A revert conflict on a file bale only added lines to is resolved line by line (lines_added_only); any other conflict refuses by name.
- A bale path is one of the letterhead's marks since 0.36.0 (share/letterhead.toml `[marks]`: `.bale` with a word boundary, `.baleignore`, `bale.toml`), held to office_host.EXCLUDE_LINES by tests/test_bale_own_commits.py; deliver's check is told never to read the never-delivered files it took out of the index (`never=NEVER_DELIVERED`).
- The shape of bale's own commits is bale's convention, pinned to the probe's captured subjects (fixtures/bale-0.4.45/watches/git/office-src_subjects.json); a commit of the occupant's must not take the `bale: ` start.
- tests/test_bale_own_commits.py holds 0.36.0's tests (15, in five classes).

#### Front sheet

office-src 0.36.0 keeps deliver's promise that no bale commit leaves, in
content as well as in name. Delivering a work office's folder 6, bale's
own `bale: ignore .bale/` commit (1ee6bc7, `.bale/` added to
`.gitignore`) rode in beside the session's work, because deliver
squashed the whole workbench range and took only bale's names out of the
index, and a bale path was none of the letterhead's marks. Now the
commits bale makes for itself (its housekeeping commits and its sweeps,
as the consumption manifest declares them; never a session's work or its
merge) are undone on the workbench's tip before the squash, in temporary
commits that never leave, each named in the plan; a line later work
already took out is simply gone, later work on the same lines takes
bale's lines out one by one when adding lines was all bale did there,
and anything else refuses by name. A bale path is one of the letterhead's
marks, the backstop for a bale line that reaches the squash some other
way, and the files deliver takes out of the index are named never read.
Additive: no migration; the doctrine's core is rewrapped back under its
reading pin.
