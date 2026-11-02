# Notes: home-screen-offers (office-src 0.41.0)

All seven items of the brief are built, each with a class in the new
tests/test_home_screen_offers.py (26 tests). The whole suite ran on the
finished tree: 1194 tests in 589 s here (four jobs on two CPUs), with
one failure: tests/test_three_gaps.py's adopted-branch terminal test
read `desk/NAME/folder.md` after a terminal delivery, which now closes
the folder (the brief's ruling). I changed that test to read the folder
from the filing cabinet and to pin the closing line, and reran its
module: 17 tests OK. validation.sh's fast run (the tier plus this
session's classes, 368 tests) took 61 s of the tier's 120. On the unchanged tree with the new module
copied in, 24 of the 26 fail (the two that pass are the "as before"
guards for a project with no audience). The request carried the whole
tree, so nothing failed for want of fixtures; the unchanged tree's whole
suite was 1168 tests, all OK, in 543 s here (two CPUs, four jobs).

Every changed path is inside the write forecast (bin/office, lib, share,
tests, README.md, RELEASES.md, VERSION, doctrine/OFFICE.md,
claude/context/front-sheet.md). The brief expected the new test module to
be out-of-forecast drift; `tests` is in the forecast as a directory, so
tests/test_home_screen_offers.py is inside it, and nothing needs
admitting. tests/test_three_gaps.py is modified for the reason above.
share/verbs.toml changed because two of its declarations name
what changed: deliver now writes `filing-cabinet/{folder}` (it closes the
folder), and withdraw now renames bundles in the downloads.

Where a cite and the tree disagreed: nothing material. The line numbers
in the brief matched 0.40.0 closely enough to find everything.

## Decisions

1. **Deliver closes on a terminal, and piped only with `--close`
   (flagged deviation).** The brief says deliver closes the folder after
   a successful push, "in land's words", with `--leave-open` as land has
   it. Land closes a finished folder on a terminal without asking, and
   piped it leaves the folder open and says so unless `--close`. I gave
   deliver the same rule and added `--close` to it, so a delivery piped
   from a script never moves a folder silently, and land and deliver
   behave the same way. It also keeps every existing deliver test green
   (they deliver piped and read `desk/NAME/folder.md` afterwards). On a
   terminal, which is how the occupant delivers, it closes as the brief
   asks. If you want piped deliveries to close by default, the change is
   one `case` arm in `deliver_close`.
2. **Which sessions count as delivered.** A folder's applied session is
   delivered when *any* folder's `delivered` History line for that
   project names it (`office_bale.delivered_by_project`), not only this
   folder's. That is how deliver already reads the records
   (`other_deliveries`): a session another folder delivered with
   `--others-too` is on the audience, so it does not hold this folder
   open, and the desk and home screen do not offer it as undelivered. A
   session the base holds (0.40.0's `held`) also counts, through the
   plan's new `held_sessions`. This is your "deliver's close and
   `--others-too`" call.
3. **Landed, not delivered, computed once.** `waiting_on_delivery`
   runs inside `render_desk`, on the folders `render_desk` already read,
   and leaves its results in the desk's groups, so the desk lines, the
   Next line and the home screen share one read. It reads git only when
   some folder on the desk could be such a folder (a lane naming a
   project with an audience, at least one recorded session), and then
   one `git for-each-ref refs/tags/applied/` per such project (through
   the shell for a hosted one). No fetch, no bale call. The landing day
   is the `applied/SID` tag's creator date, in the office's timezone.
4. **A folder whose merge job waits is offered the merge, not deliver.**
   Such a folder also has landed work not delivered, but deliver would
   only name `office start N --merge`, so it is left out of the
   undelivered list. A job whose session is out is said nowhere new (the
   folder is in flight). A job whose session is applied makes the folder
   landed-not-delivered, and status says deliver makes the merge.
5. **The tail is built in bin/office.** Folder state is only known after
   land's closings, so `land_tail` builds the tail at the very end and
   `carry_relays` appends it to blocks addressed to the planner when
   `at_end` is 1. bale's lines are untouched; the tail follows its END
   marker after one newline. The folder's state is read from where the
   folder now is (desk or filing cabinet), so the founding folder's close
   and a `--close` show correctly without extra bookkeeping. Land's review
   lines are written to a file by `land-review --out` (no new helper
   start). Piped, nothing is copied, so the tail is not seen; that is
   to the brief's letter (it rides in the copies the office makes).
6. **No new helper starts.** The land plan carries the project's
   `audience` (read in the existing one-liner), the folder's number is
   read with sed, and status's merge lines ride status's one batch.
   `TestFewerHelperStarts` (land 9, status 1, walk-in 3) stays as it was.
7. **Bare probe counts office sessions too.** The brief lists "a
   read-only sitting open in the office, or a session open on a
   project". I also count a non-read-only session open in the office,
   since a probe runs there (`--project office`) just the same. Its
   parenthesis says `in the office`; a project's says `on PROJECT`; a
   sitting's `a sitting`. Piped with several, the probe refuses and names
   them; with exactly one, it takes it piped too (it used to refuse
   piped with no folder at all).
8. **`--paused` goes alone.** Given with any other `projects set` flag
   it refuses, saying so, rather than mixing set's questions into the
   mark. The key sits at the end of the project's entry as
   `paused = true`; `--unpaused` removes the line. A value that is not
   a boolean is a declaration problem and reads as not paused.
   `office projects` lists a paused project as
   `NAME  PATH  (paused: office projects set NAME --unpaused)` instead of
   checking its path.
9. **Paused, and the verbs that still run.** The renderings use a new
   `office_bale.rendered(project)`, which raises a `paused` BaleError;
   `readable()` is unchanged, so land, deliver and probe still reach a
   paused project. `repos()` and `open_anywhere()` take `rendering=True`
   for the walk-in's Next line and the home screen (which then skip a
   paused project) and stay as they were for land and withdraw. A paused
   project is never counted as unreadable, so `office projects --ledger`
   and the digest do not exit 3 over it. One consequence: the home
   screen does not read a paused project's records to see whether a
   bundle was opened there; such a bundle would be offered until you
   unpause or withdraw it. Rare, and said here.
10. **The two-copies count covers every copy, any age**; the offered
    copy is still the newest within the two weeks.
11. **The doctrine's core sentence** was rewrapped in its eight lines.
    To make room I also changed "files what the session's notes.md sends
    back" to "files what its notes.md sends back", "last of all" to
    "last", and "Given a read-only sitting it sent out, it ends the
    sitting with bale's unlock instead." to "A read-only sitting it sent
    out it ends with bale's unlock." The banner stays at 299 and no
    heading changed.

## Walkthrough

### What changed

- bin/office: land's `offer_close` leaves an audience project's folder
  on the desk with one line (`--close` still closes it); `land_tail`
  and `carry_relays` put the office's tail on the planner's block; land
  ends with `Next: office deliver N`. Deliver has a bare offer of the
  landed folders and closes the folder after the push (`deliver_close`,
  `--close`, `--leave-open`). Bare probe picks the one folder with a
  session open. `withdraw --bundle` and the combined bare offer.
  `projects set --paused/--unpaused`. Start refuses a paused project.
  Status prints the merge-job lines.
- lib/office_bale.py: `waiting_on_delivery` and its helpers, the desk's
  `open_words`, `delivery_move` on the Next line, `waiting_lines`,
  `probe_folders`, `rendered` and `unread_line`, and three subcommands.
- lib/office_home.py: the new items, the copy count, the bundle
  withdrawal, the `w` key's words, a paused project's row.
- lib/office_deliver.py: `still_to_deliver`, `held_sessions` in the plan,
  `land-review --out`.
- lib/office_helper.py: the `paused` key end to end.
- lib/office_digest.py, lib/office_watches.py: read a paused project
  for nothing.
- share/verbs.toml, README.md, the doctrine, RELEASES.md, VERSION, the
  front sheet.

### Why

The occupant should never type a number he has to look up (A1), the
planner should never have to ask for the folder's state or miss land's
review (A9, A14), a bundle nobody will send should leave the offer (A10),
and a broken project should not warn on every walk-in (A7). The merge job
was only said when deliver ran; now the screens offer it.

### How to explain each piece

- A folder on a project with an audience is not done when its work
  lands; it is done when the work reaches the audience. So land leaves it
  on the desk, and deliver closes it.
- Everything that waits now has a key: the folder to deliver, the merge
  to send, the probe's folder, the bundle to withdraw.
- The relay block the occupant pastes now ends with the office's own
  lines, so the planner sees the folder and the review without asking.
- A paused project is skipped by every screen and refused by start.

### Questions a reviewer will ask

- *Does anything reach the audience to decide "not delivered"?* No. Only
  the office's folder pages and `git for-each-ref` on the applied tags.
- *Is bale's block changed?* No. The tail follows bale's END line; the
  test compares bale's block as printed on the screen with the copy.
- *Why does piped deliver not close?* See decision 1.
- *Does a paused project's session still land?* Yes, tested.
- *More helper starts?* No; TestFewerHelperStarts is unchanged and green.

### A hand test

1. On a project with an audience, land a session in a terminal: the
   folder stays on the desk, the last line is `Next: office deliver N`,
   and pasting the clipboard shows bale's block then the `--- OFFICE
   land ... ---` tail with the folder, the deliver line and the review.
2. Run `office`: the home screen offers `Deliver folder N, ...`; press
   its key, push with y; the folder goes to the filing cabinet with
   `the folder NAME: closed, done (...)`.
3. Save one bundle twice in the downloads: the home screen says
   `2 copies, the newest offered`; `office withdraw --bundle STEM`
   renames both to `.declined`; the home screen no longer offers it.
4. `office projects set NAME --paused`, then `office`: the project's
   line says paused, and nothing about it is read; `--unpaused` undoes.

## Delivery

- to: the occupant

### Commit

Offer the next step by key (0.41.0)

A folder on a project with an audience now stays on the desk after
office land and closes at delivery, and land ends with the deliver line,
its number filled in. The desk, the walk-in's Next line, the home screen
and bare office deliver offer the folders whose work landed and is not
delivered, and a merge job waiting for its session; bare office probe
takes the one folder with a session open. The block for the planner
carries the office's lines after bale's own: the folder, its state, the
deliver line and land's letterhead review. office withdraw --bundle takes
a bundle out of the offer by renaming it, and office projects set
--paused marks a project the screens read nothing of.

### Review

Offer the next step by key (0.41.0)

What to look at: land's close for a project with an audience and
deliver's close after the push (bin/office offer_close, deliver_close),
the tail on the planner's block (land_tail, carry_relays), and
lib/office_bale.py waiting_on_delivery, which reads the folders and the
applied tags with git alone. What to try by hand: land and deliver one
folder on a terminal; withdraw a bundle saved twice; pause a project and
walk in. Deliberately untouched: bale's block between its markers, the
downloads beyond the rename, and the verbs that carry work already out.

## Structure

- title: Offer the next step by key (0.41.0)
- size: medium
- goal: Offer the next step by key (0.41.0): a folder with an audience closes at delivery and land ends with its deliver line, the home screen and bare deliver offer landed-not-delivered folders and a waiting merge session, bare probe takes the one open session's folder, the planner's relay block carries the folder's state and land's letterhead review, office withdraw --bundle takes a bundle out of the offer, and office projects set --paused marks a project paused

## Handbook

### Front sheet

office-src 0.41.0 offers the next step by key. A folder on a project with
an audience stays on the desk after office land and closes at delivery;
land ends with `Next: office deliver N`. The desk, the walk-in's Next
line, the home screen and bare office deliver offer the folders landed
and not delivered, and a merge job waiting for its session, all read from
the office's pages and the applied tags with git alone. Bare office probe
takes the one folder with a session open. The planner's relay block
carries the office's tail after bale's END marker. office withdraw
--bundle renames a bundle out of the offer, and office projects set
--paused marks a project the renderings read nothing of. Additive: no
migration.

### Facts

- office land leaves a folder on a project with an audience on the desk (bin/office offer_close reads LAND_AUDIENCE, the land plan's audience); office deliver closes it after the push when lib/office_deliver.py still_to_deliver returns none, on a terminal, or piped with --close (bin/office deliver_close)
- a session counts as delivered when any folder's delivered History line for the project names it (office_bale.delivered_by_project), or the base holds it (the plan's held_sessions)
- landed-not-delivered folders and waiting merge jobs are office_bale.waiting_on_delivery, read once in render_desk into the groups undelivered, merges, undelivered_by_rel and merge_by_rel; the landing day is the applied/SID tag's creatordate in the office's timezone
- the Next line's delivery row is office_bale.delivery_move, after the desk moves and before a drop: a waiting merge job first, then the newest undelivered folder
- the office's tail on the planner's relay block is bin/office land_tail, appended in carry_relays when at_end is 1 and the block is to the planner; land-review --out FILE keeps the review's lines for it
- bare office deliver reads office_bale awaiting-delivery; bare office probe reads office_bale probe-folders; office status reads bale:waiting-lines in its batch
- office withdraw --bundle STEM is office_home withdraw-bundle (--check first): each copy renamed NAME.bale-bundle.declined, which downloaded_bundles never matches
- a paused project is `paused = true` in its [projects] entry (office_helper.PAUSED_KEY); renderings read it through office_bale.rendered, which raises BaleError kind paused; readable() still reaches it for land, deliver and probe
- tests/test_home_screen_offers.py holds 0.41.0's tests (26, in thirteen classes)

## Proposals

- **What:** Print the office's tail when piped too, after bale's block,
  under one marked line. **Why:** piped, nothing is copied, so a landing
  run from a script or a session never shows the tail to anyone; the
  planner only gets it from a terminal landing. **Scope hints:**
  bin/office carry_relays; tests in test_home_screen_offers.
- **What:** Let the home screen read whether a bundle was opened on a
  paused project. **Why:** decision 9: `rendering=True` skips the paused
  project's records, so a bundle opened there stays offered. Reading
  `known_sids` there is a bale call on a paused project, which is why I
  did not. **Scope hints:** lib/office_home.py every_place.
- **What:** A landed-not-delivered folder on a hosted project costs one
  ssh connection per walk-in. **Why:** `waiting_on_delivery` reads the
  applied tags through the shell. If that is felt, cache the tags per
  walk-in day, or skip hosted projects on the walk-in and keep them for
  the home screen and bare deliver. **Scope hints:**
  lib/office_bale.py applied_tag_times.
