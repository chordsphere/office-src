# notes: 2026-10-28-m10-land-flags-005

office-src 0.37.0, additive. `office land` passes bale's two
per-invocation accepts through, said and never added on its own, and
RELEASES.md's 0.33.0 entry is the tag's bytes again.

## What the probe established

One paste-back probe, run at the top of office-src's clone on the
packing machine (WSL2, bale 0.4.56). The paste came back intact (337
lines, the integrity trailer agreeing) with CRLF line ends, which I
stripped before reading it.

- The base has not moved: every forecast file's HEAD bytes hash to the
  request's stamp (HEAD 09789cf, 0.36.0). The only untracked files are
  three telemetry records, none of them mine to touch.
- The tag `applied/2026-10-28-m10-sitting-fixes-001` (422684c) holds the
  0.33.0 entry: 97 lines, 5970 bytes, sha256 `5bd5083c4167...`, no tabs.
  The text I rebuilt from the framed lines hashes to exactly that.
- How it was lost: of the commits since the tag that touched RELEASES.md,
  the first is 87ce51a, 0.34.0's own work commit (`[bale
  2026-10-28-office-src-fix-three-gaps-m10-hit-on-002]`), whose parent
  6fcb558 (0.33.0's sweep) still held the heading. Every commit from
  87ce51a on lacks `## 0.33.0`.
- bale 0.4.56 refuses a changed checkpoint in bale_apply.py with
  `fail(format_checkpoint_stamp_refusal(...))`, before staging: an error
  path, with no `-refused` outcome literal for it (the source's are
  base-drift, scope-drift, required-check and the verbs' own), and, as far
  as the source shows, no attempt recorded. bale's help says error paths
  exit through stderr. bale_report.py composes re-run lines carrying one
  `--accept-base-drift` per drifted path and, in the retry line after
  `bale amend-checkpoint`, `--accept-checkpoint-change`.

## Decisions to ratify

1. **Only the 0.33.0 heading was lost, so only the heading went back.**
   This is the main thing to check. The brief says to put the entry back
   between 0.34.0 and 0.32.0, verbatim from the tag. Read against the
   tree, the entry's body was never gone. 87ce51a dropped just the line
   `## 0.33.0`: the body stayed at the end of 0.34.0's entry, with a
   blank line doubled where the heading had been. So 0.34.0's entry read
   as though it ran on into 0.33.0's prose, and
   test_answer_review's split found no heading. Inserting the whole
   entry would have doubled 97 lines of 0.33.0's text. I put back the one
   line instead (that also takes out the doubled blank line). From the
   heading to 0.32.0's, the file is now the tag's bytes exactly: same
   sha256, same 5970 bytes, checked in validation.sh and pinned in
   tests/test_land.py `TestTheLandFlagsRecord`. Nothing was rewritten
   from notes. The outcome the brief pins (the tag's bytes, between 0.34.0
   and 0.32.0) holds; only the mechanism differs, and this is why.
   Why 87ce51a dropped the line, git cannot say. That session was packed
   a minute after 0.33.0 landed, against a base that held the heading,
   and its RELEASES.md arrived without it. bale's base-drift gate could
   not catch it, because the base had not moved; it was the response's
   own whole file. My best guess is that the worker wrote 0.34.0's entry
   over the old top heading. The record test now refuses a skipped minor
   release, so the next such loss fails the suite rather than surfacing
   at a later run.
2. **A changed checkpoint's next line is offered on bale's words, not
   asserted.** The brief wants land's next line to name `office land SID
   --accept-checkpoint-change` when bale refuses a changed checkpoint.
   But land keeps bale's stdout only. Its stderr is the occupant's
   terminal, and I did not change that ("every other line of land is as
   it was"; teeing stderr would also take bale's terminal away from its
   prompts). bale words this refusal on stderr and records no attempt,
   so on a project here the office sees only "bale refused before it
   recorded an attempt". So:
   - a **retry** refused that way gets the next line `office land SID
     --accept-checkpoint-change, if bale's words above say the session's
     checkpoint changed since the pack (after bale amend-checkpoint,
     say)`. A retry is where it comes, since amend-checkpoint follows a
     HOLD;
   - an apply refused that way gets no line, as before. A checkpoint
     that changes before the first apply is rarer, and bale names its
     own line there;
   - wherever bale's own re-run line does reach the capture (through a
     host's attended terminal, where both streams arrive on one pty), the
     office reads the accept from it and names the refusal outright.
   If you want it definite everywhere, the clean fix is on bale's side
   (Proposals).
3. **Moved base: the next line comes from bale's own re-run line.** On
   `base-drift-refused`, land reads bale's printed `bale apply|retry ...
   --accept-base-drift 'P'` line as a shell would (`accepts_bale_names`).
   Its next line passes the same paths, plus any accept typed this time,
   since bale carries none forward. When it can read no such line, the
   next line is `office land SID --accept-base-drift PATH, once for each
   path bale names above`. The Refused words for this outcome changed to
   say so. Scope drift and a missing required check keep their old words
   and no next line: they are bale's questions, unchanged.
4. **The argv order.** The flags go before the tarball, as the brief
   pins, through a new consumption key `flags_before = "{tarball}"`
   (the builder already put declared flags after the whole argv). Within
   the flags, the builder's existing group order puts the repeated
   `--accept-base-drift` before the `--accept-checkpoint-change` switch.
   bale's argparse does not care. I left the builder's order alone rather
   than reorder `pack`'s pinned argv for it.
5. **A read-only sitting refuses an accept, and nothing is ended.** A
   sitting lands nothing, so an accept on one is almost certainly the
   wrong sid. land-plan refuses before anything is unlocked, naming the
   line that does end it. The alternative was to log and ignore, the way
   `--ratified` on a sitting is.
6. **`--accept-base-drift` reaches the helper as
   `--accept-base-drift=PATH`**, so a path that starts with a dash
   survives argparse. The path is otherwise untouched: through a host's
   shell each word is quoted the way every other argv word is, and the
   hosted test sends `docs/it's $NOPE \`x\`.md` and reads it back
   verbatim.
7. **What land says.** One line per accept, after the existing `landing
   SID ...` line and the record line, before bale starts:
   `passing --accept-checkpoint-change to bale retry, as you typed it:
   bale runs the session's checkpoint as it is committed now, not as it
   was stamped at the pack, and records that it did` and `passing
   --accept-base-drift 'P' to bale apply, as you typed it: the response's
   bytes land over P as it is now, superseding what changed there since
   the pack`.

## Outside the write forecast

- `doctrine/OFFICE.md`: one sentence in section 4, continued, where the
  doctrine describes `office land` ("Of bale's own flags it passes only
  the two accepts..."). The brief asks for doctrine/OFFICE.md to change
  wherever a verb's behavior changes, and the forecast did not name it.
  Section 7's verb table is untouched. The doctrine's hash changes, so a
  sitting out under 0.36.0's doctrine will be said to be under an older
  one, as designed.

Every other path is inside the forecast (`tests` covers the three test
modules and the fake; tests/test_bale_own_commits.py's change is the
version pin above).

## Places to look closely

- lib/office_bale.py `outcome_words`: the `refused` branch for a retry,
  and the `named[0]` branch above it (decision 2).
- tests/fakes/land_bale.py: the fake now takes the two accepts before the
  tarball, admits a moved base per named path, and rewrites the drift
  capture's re-run line for the verb, tarball and paths of the call.
  `FAKE_BALE_CHECKPOINT_CHANGED=SID` makes it refuse on stderr with no
  attempt. That one line is not a capture: it stands in for
  format_checkpoint_stamp_refusal's words, which no fixture holds. The
  fake's docstring says every line is a capture, so this is the one
  exception, marked where it is printed.
- tests/test_land.py `TestLandFixtures.test_the_office_passes_bale_no_answer`
  changed meaning. It held that apply and retry declare no flags at all;
  now it holds that the two accepts are the only ones, both in bale's
  help, and that the call with none given is the tarball alone.

## Validation

- `tests/run.sh --fast` with this session's tests (the two new classes in
  test_land, the declaration test's class, the hosted class, and
  test_answer_review's TestTheRecord): passed, observed, 368 tests in 75 s
  of the 120 s budget.
- The whole suite on the changed tree, observed here: the first run
  failed two record tests of mine to fix: RELEASES.md's placeholder
  check (test_walkthrough_tidy) caught my unfilled test count, and
  0.36.0's record pin (tests/test_bale_own_commits.py
  `TestTheRecord`) held VERSION to exactly 0.36.0, which every next
  release breaks. It now reads 0.36.0 or later, as 0.32.0's and the
  others' pins do. After both fixes: passed, observed, 1053 tests in
  603 s with four jobs.
- validation.sh --slow, rehearsed on a copy of the base with files/ and
  apply.sh laid over it (bin/office's exec bit stripped first, then put
  back by apply.sh): every check passed. The fast tier with this
  session's tests ran 368 tests, and the touched modules whole
  (test_land, test_return_trip, test_answer_review) ran 109. Every claim
  agreed with its verdict, and the copy was byte-identical to the tree
  afterwards.
- Baseline, the unchanged tree whole: 1043 tests, the one failure
  test_answer_review's TestTheRecord (the missing heading), 604 s.
- The new tests against the unchanged code: all fail except
  `test_no_setting_turns_one_on`, a guard that holds on both trees by
  design. validation.sh's session assertions fail on the unchanged tree
  except two guards, "nothing is passed unasked" and "the releases run
  newest first", kept because the brief pins them.

## Proposals

- **What:** a slip for bale-src: the checkpoint provenance gate's refusal
  as a reported outcome (a `checkpoint-change-refused` outcome in apply's
  `--json` report and an attempt in the dossier, like
  `base-drift-refused`), or at least its re-run line on stdout.
  **Why:** land reads how a landing ended from bale's records, never its
  words. Today this one refusal is an error path on stderr with no
  attempt, so the office can only offer the accept line conditionally
  (decision 2).
  **Scope hints:** bale_apply.py `format_checkpoint_stamp_refusal`'s two
  call sites; office-src's `outcome_words` and the consumption manifest's
  `[surfaces.apply] outcomes` would then name it outright.
- **What:** have a release session's validation compare the RELEASES.md
  headings it ships against the base's.
  **Why:** 87ce51a lost a heading in a whole-file overlay that every gate
  passed. `TestTheLandFlagsRecord.test_the_releases_run_in_order_and_skip_none`
  now catches a skipped minor, but not a lost patch release.
  **Scope hints:** tests/test_land.py's record class, or test_suite_clock's
  TestTheRecord, which already reads RELEASES.md's newest heading.

## Walkthrough

### What changed

- `office land` takes `--accept-checkpoint-change` and
  `--accept-base-drift PATH` (repeatable). They ride in land's plan
  (lib/office_bale.py `land_plan`) and reach `bale apply` or `bale retry`
  before the tarball (`land_run`, through the consumption manifest's
  `switches`, `repeated` and new `flags_before` on `[surfaces.apply]` and
  `[surfaces.retry]`). On a host they go through the project's shell, as
  typed.
- Before bale runs, land says one line per accept (`accept_said`).
- After a moved-base refusal, the Next line is the office line with the
  paths bale named (`accepts_bale_names`, `accept_line`). After a retry
  refused before any attempt, the Next line offers
  `--accept-checkpoint-change`, for when bale's words say the checkpoint
  changed.
- A read-only sitting refuses an accept and ends nothing.
- RELEASES.md: the 0.33.0 heading is back, so the entry under it is the
  tag's bytes again; 0.37.0's entry says what happened.
- README.md's land details, `office land --help`, the doctrine's landing
  paragraph and the front sheet say all of it.

### Why

After `bale amend-checkpoint`, the retry of the same response had to be
run by hand with bale, outside land, so nothing land does after a landing
ran for it. The two accepts are bale's deliberate one-time rungs with no
setting, so the office passes them only when typed, and says so. The
0.33.0 entry's loss broke a test on every whole run and made the history
skip a release.

### How to explain each piece

- "land never decides to accept anything; it passes on what you typed,
  says that it did, and bale records it."
- "When bale refuses a moved file, land tells you the exact office line
  that accepts it, so you never step outside land to finish a landing."
- "A changed checkpoint is refused on bale's error stream, which land
  does not keep, so after a refused retry land offers the line and you
  read bale's words above it to confirm."
- "Only one line of the release history was lost, the 0.33.0 heading;
  putting it back makes the entry the tag's bytes again."

### Questions a reviewer will ask

- Can a setting turn an accept on? No. Only cmd_land's own loop reads
  them (a test and a validation assertion hold that), and bale has no
  config key for either.
- Does an accept carry to the next landing? No, as in bale. The Next
  line says each one again.
- Why is the checkpoint's Next line conditional? Decision 2: bale's
  refusal is on stderr with no attempt, so the office cannot tell it
  from another refusal.
- Why not paste the whole 0.33.0 entry back, as the brief said? Its body
  was still there; only the heading was missing. The result is the
  tag's bytes either way, and this way nothing is doubled.

### A hand test

1. On a project with a session out, change a forecast file after the
   pack and commit it. Then `office land SID`: bale refuses, and the
   Next line reads `office land SID --accept-base-drift 'PATH'`.
2. Type that line: land says `passing --accept-base-drift 'PATH' to bale
   apply, as you typed it: ...` before bale's own lines, and the session
   lands, after-land actions and all.
3. In a project with a blind checkpoint, after a HOLD and `bale
   amend-checkpoint`, run `office land SID`: bale refuses the retry,
   and land's Next line offers `--accept-checkpoint-change`. Run it
   with the flag: the retry lands through land, and the folder's pages
   and the after-land actions follow.
4. Open RELEASES.md: 0.34.0 is followed by 0.33.0 and then 0.32.0, and
   0.34.0's entry ends where its own text ends.

## Delivery

- to: nobody

### Commit

office land passes bale's two accepts; 0.33.0's release heading back

office land now takes --accept-checkpoint-change and --accept-base-drift
PATH (repeatable) and hands them to that landing's bale apply or bale
retry, before the tarball, exactly as typed, through a host's shell
when the project has one. Each is said in its own line before bale runs.
Neither is ever added on its own, and no setting turns one on. After
bale refuses a moved base, the Next line is the office line that accepts
it. After a retry refused before any attempt, it offers the checkpoint's
accept, for when bale's words say the checkpoint changed. A read-only
sitting refuses an accept.

RELEASES.md had lost the 0.33.0 heading line in 0.34.0's landing; it is
back, and the entry under it is again the 0.33.0 tag's bytes. Release
0.37.0.

### Review

office land: bale's two accepts, and the 0.33.0 release heading

What to look at: the land plan and run carrying the two accepts, the
words land says before bale runs, the Next line after a refusal, and the
one line put back in RELEASES.md.

What to try by hand: land a session whose forecast file moved after the
pack, then type the Next line land prints; and, after a checkpoint
amendment, land the held session with --accept-checkpoint-change.

Deliberately untouched: the admissions bale asks for itself, and every
other line of a landing.

## Structure

- title: office land passes bale's two accepts, and 0.33.0's release heading
- size: small
- goal: Let office land pass bale's --accept-checkpoint-change and --accept-base-drift through to apply and retry, said and never added on its own, and restore RELEASES.md's lost 0.33.0 entry from the tag's bytes

## Handbook

### office-src

- office land passes bale's two accepts (--accept-checkpoint-change,
  --accept-base-drift PATH) only when typed. share/bale-consumption.toml
  declares them on apply and retry as `switches` and `repeated`, placed
  before the tarball by `flags_before`. The builder puts repeated flags
  before switches, so the argv reads `apply --accept-base-drift P
  --accept-checkpoint-change TARBALL`.
- bale 0.4.56 refuses a changed checkpoint with
  `fail(format_checkpoint_stamp_refusal(...))` before staging: stderr, no
  `-refused` outcome, no attempt. land's capture is stdout only, so on a
  project here the office cannot see that refusal's words.
- RELEASES.md's 0.33.0 entry is pinned by sha256
  (`5bd5083c4167...`, the tag's bytes from its heading to 0.32.0's) in
  tests/test_land.py TestTheLandFlagsRecord, which also refuses a
  skipped minor release. An edit to that entry fails the pin by design.
- A probe's paste may come back with CRLF line ends (WSL's clipboard).
  Strip them before hashing anything read from it.
- The suite's machine rule (test_suite_clock
  TestNoTestReadsTheMachine) refuses the literal string `$HOME` anywhere
  in a test file, even inside a string meant for a far shell.

#### Front sheet

office-src 0.37.0: `office land` finishes a landing that needs one of
bale's two one-time accepts. After `bale amend-checkpoint`, `office land
SID --accept-checkpoint-change` retries the same response through land;
after a moved file, `office land SID --accept-base-drift PATH` lands it.
land says what it passes before bale runs, never passes one you did not
type, and after a refusal names the line to type. RELEASES.md's history
is whole again.
