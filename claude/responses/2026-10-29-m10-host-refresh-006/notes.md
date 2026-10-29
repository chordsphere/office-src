# notes: 2026-10-29-m10-host-refresh-006

office-src 0.39.0. All five items of the brief are here, inside the
forecast (the one new module is under lib/, the one new test module
under tests/); nothing was probed and nothing was asked. `office projects
refresh NAME` brings a clone's view of its audience level through this
machine, start and deliver offer it when the view is behind, deliver
brings the base into the workbench itself when that merge is clean
(a conflict is aborted, checked and refused by name), and prepare writes
bale's sandbox setting only where bale's sandbox cannot run, with
`office projects set NAME --prepare` to reach the two M10 clones without
re-adding them. Three places where I read the brief differently, or found
it claiming more than the code does, are first below.

## Decisions to ratify

1. **The merge runs only for a delivery made from the base.** The brief
   says "when the workbench is behind the base ... and the squash in step
   7 would otherwise run from an old parting point". A delivery that
   continues on a branch (its own, another folder's, an adopted one)
   squashes onto that branch, not onto the base; merging main into the
   workbench there would put main's new commits into the squash and so
   into the review's diff. So `continuing` deliveries are not merged, and
   that case stays with m10-deliver-merges' "squash from the range".
2. **The brief's claim about twice_lines does not hold, and I changed
   nothing there.** The brief says the merge "is what makes deliver-adds'
   twice_lines quiet for work the base holds, whatever way the audience
   merged it". It is not: the office delivers squash commits, so the
   audience never holds another folder's workbench commits, and after
   the merge the range base..workbench still carries them (they are on
   the workbench side of the merge). twice_lines sees exactly the
   sessions it saw before. A review merged as a merge commit was already
   quiet through base_holds (the delivery commit is on the base); a
   review merged as a squash still refuses. What the merge does buy is
   the squash itself: it runs from the base's tip, so the delivery's diff
   is the folder's own work and no longer conflicts with what the
   audience merged (A5's actual failure). This is m10-deliver-merges'
   "base_holds by content" to fix; the release text says the merge
   changes nothing there.
3. **The merge needs the clone's view of the base level with the base as
   fetched, not just behind-and-refreshable.** If the occupant declines
   the refresh (or deliver is piped without `--refresh`), the clone's
   AUDIENCE/BASE is not the base the squash runs from, so no merge is
   made and one line says why. Merging an old main would leave the
   parting point old anyway.
4. **The merge is refused while a bale session is open in the clone**,
   which the brief did not ask for. A merge commit on the workbench moves
   files under an open session, and bale would refuse that session's
   apply for base drift. Said, and the plan goes on as before. The
   check costs a `bale status` (one more connection on a host) only when
   a merge is otherwise about to run.
5. **A merge that cannot start** (an untracked file the audience now
   tracks, say: git refuses before MERGE_HEAD exists) is said, nothing
   changed, and the plan goes on. Only a real conflict refuses.
6. **For a clone on this machine deliver's own fetch already refreshes
   the view.** plan() fetches the base from the clone's remote by name,
   and git moves `refs/remotes/origin/main` on that fetch
   (opportunistic remote-tracking update). So for a local clone the view
   is read after the fetch, is never behind, and deliver never offers a
   refresh there; it merges straight away when the workbench is behind.
   start still compares a local clone (ls-remote does not move it). The
   offer that matters is the hosted one, as the friction report says.
7. **`office refresh` (the short verb) does not exist.** `projects
   refresh` is the floor, and with start and deliver offering it the
   verb is typed rarely; a top-level verb also costs a catalog entry, a
   fast-tier entry point and a help line. Easy to add if wanted.
8. **`--yes` is taken and changes nothing**: refresh asks nothing on any
   path (the brief: "nothing is asked on the happy path"; I found no
   unhappy path that should ask, since each stop is said and left).
9. **The stamp is a blob ref outside refs/office/.** `refs/office-refresh/
   AUDIENCE` names a three-line blob (`refreshed 2026-10-29T13:35:31Z`,
   `from origin URL`, `by way of HOSTNAME`). Not under refs/office/,
   because deliver owns that namespace and empties it after every
   delivery (four tests hold it empty). A reflog was the other option the
   brief offered; git writes no reflog entry when a ref does not move, so
   a refresh where nothing moved would leave no trace. The time is UTC,
   as git's own records are; it is the clone's record, not an office
   page, so I did not convert it to the floor plan's clock.
10. **`office projects` now connects** for a hosted project with an
    audience, once each, to read that stamp (the brief pins "read from
    the clone itself"). The listing made no network call before; a host
    that does not answer is said on the line (`refreshed: unread (...)`)
    and never fails the listing. A project here reads its clone locally.
11. **The sandbox test is `unshare -Ur true`.** bale's help names the
    condition, "hosts without unprivileged user namespaces", but not its
    probe's command, and no bale verb runs the probe. One user namespace
    is the least bale's sandbox needs, so this test is never stricter
    than bale's own: where it refuses, bale's probe refuses too, and the
    setting cannot be written where the sandbox would have run. The
    reverse can happen (it passes, bale's probe refuses for a PID or
    mount namespace): then nothing is written and bale asks as before,
    which is the safe side. An exit of 126 or 127 (no unshare there)
    writes nothing and says so.
12. **`OFFICE_SANDBOX_PROBE`** names another command for the suite, as
    OFFICE_CONTAINER_MARKER does for the survey; tests/test_office.py's
    Env sets it to `true` for every test, so prepare writes nothing for
    the sandbox whatever the machine running the suite allows (a nested
    sandbox in validation might refuse user namespaces, and a dozen
    existing tests compare bale.toml with the stub). A hosted test that
    wants the real probe sets it empty and puts a refusing `unshare` on
    the fake host's PATH.
13. **The ff of a checked-out base.** The brief asks for `--ff-only` when
    the base is checked out and clean, and also says refresh never
    touches the workbench. A checked-out branch is the workbench, so the
    fast-forward is only possible when it has no commits of its own
    (`--ff-only` refuses otherwise, and the office says so before trying).
    I kept the brief's behavior and the lines say which branch moved.
14. **The `merged` History line is written at plan time**, before the
    question, because the merge is real in the clone whatever the
    occupant answers next. plan takes `--day` (the office's date) for it.
15. **prepare's stub line** still says "bale's project layer, empty"
    above the sandbox table when one is written. I left the stub's text
    alone (tests compare it byte for byte, and it was empty when
    written); the office's comment under it says what the table is.

## Places to look closely

- lib/office_deliver.py plan(), steps 4b and 4c, and `merge_base_in`.
- lib/office_host.py `_SANDBOX_STEP`: shell inside a Python string
  inside `sh -c`, with `\\[` escapes; tested through a host and here.
- The connection counts: deliver on a host stays at three (the clone's
  view rides in the facts batch, `git_facts_argv` + `view_argvs`), and
  status's bale line stays at one (the sandbox read rides after `bale
  --version` through `Reader.invoke(also=...)`). Two existing tests pin
  those counts; both pass unchanged.
- bin/office cmd_deliver: the plan is now a loop over its two questions
  (author, exit 4; refresh, exit 5), each asked once.

## Anchors

The brief's names and line hints agreed with the tree except where it
said they might not: bin/office cmd_projects is at 7654 (hint 7651),
usage_projects 6939 (6936), start's "answers, with bale" log line 4540
(4537); lib/office_host.py's hints all matched. lib/office_deliver.py's
plan() is where deliver-adds' notes put it.

## Validation, as run here

The whole suite, `tests/run.sh` on the finished tree: OK, 1146 tests
(34 jobs, 670 s), 22 of them new. An earlier whole run had four failures,
all from my editing bin/office while it ran (bash reads a running script
as it goes, and four office processes read a shifted file: `line 9502:
syntax error`); the four, rerun alone, passed, and the run above was made
with nothing touched.

validation.sh in a staging copy (the base, files/ over it, apply.sh,
the manifest as .bale-manifest.json): PASS in 72 s, every claim
`[agree]`; with `--slow` (the touched modules whole: test_host_refresh,
test_audience_line, test_three_gaps, test_project_on_host,
test_out_trip_to_host, test_start, test_read_side, test_office,
test_suite_clock): PASS. On the unmodified tree the release, syntax,
fast-tier and History/sandbox checks fail, as they should; the two pin
checks (the doctrine's core, and base_holds, twice_lines, own_commits and
take_out_own byte for byte, plus the squash and --others-too lines) pass
on both by design, since they assert what this session must not change.

What the suite cannot see: a real container's `unshare`, and a real ssh
and docker exec prefix. The fake host's refusing `unshare` prints the
words a container's does; the hand test below is the one that matters.

## Proposals

- **What:** office start's BRANCH checkout fast-forwards a local branch
  that is behind its remote-tracking ref (when clean and an ancestor).
  **Why:** the refresh moves `origin/picklists`, but a clone that already
  has a local `picklists` checks it out at its old tip, so "a branch the
  brief names is checked out at its current tip" holds only for a branch
  the clone has not checked out before. **Scope:** lib/office_bale.py
  checkout_branch; after this release.
- **What:** office status's sandbox line for a project on this machine
  when this machine is a container. **Why:** the line reads hosted
  projects only, as the brief says; an office run inside a container
  (the survey's machine class already knows) has the same prompt.
  **Scope:** lib/office_bale.py status_lines; small.
- **What:** base_holds by content, so a review merged as a squash is
  seen (decision 2). **Why:** the merge does not quiet twice_lines; only
  this does. **Scope:** m10-deliver-merges, already planned.

## Walkthrough

### What changed

- `office projects refresh NAME` (lib/office_refresh.py, new): fetches
  the audience's branches on this machine into a temporary repo with a
  forcing refspec; for a clone on a host, reads the clone's refs in one
  batch, bundles only the branches that moved, thin against every commit
  the clone names, sends the bundle into the office's temporary
  directory there and fetches it with `+refs/heads/*:refs/remotes/
  AUDIENCE/*`, removing the directory in the same connection; for a clone
  here, a forced fetch. Then the base is fast-forwarded where it can be,
  one line per branch that moved is said, and a stamp ref is left.
- `office projects` lists, under each project with an audience, when its
  clone's view was last refreshed and from where, read from that stamp.
- office start (bin/office `start_offer_refresh`) and office deliver
  (plan's step 4b) compare the clone's view of the base with the
  audience's, say how far behind, and ask once on a terminal
  (`--refresh`, `--no-refresh`).
- office deliver (plan's step 4c, `merge_base_in`) merges the base into
  the workbench in the clone when the workbench is behind and the merge
  is clean, writes a dated `merged` History line, and shows a `merged:`
  line in the question; a conflict is aborted, checked and refused.
- prepare (lib/office_host.py) tests whether bale's sandbox can run
  where the clone is and writes `[sandbox] enabled = false` into its
  bale.toml only where it cannot; `office projects set NAME --prepare`
  runs prepare on a declared clone; `office status` names the setting.

### Why

The work office's container clone had no credentials for the audience,
so its view of main was weeks old and every session built on it; after a
review merged on the git host, deliver's squash conflicted and its
remedy needed a terminal in the container. And bale asked at every apply
in that container whether to run without its sandbox. The refresh, the
offers and the clean merge take the terminal out of the first; the
setting takes the question out of the second.

### How to explain each piece

- The refresh is what `git fetch` would do in the clone if the clone
  could reach the audience: this machine fetches, and carries the result
  in as a bundle, the way `--from` carried the clone there.
- The offers are one line and one question, only when the clone is
  behind; level, nothing is said.
- The merge is the step deliver used to ask for by hand ("bring main
  into the workbench first"), done for you when git can do it without a
  decision, and left to you, with nothing half-done, when it cannot.
- The sandbox setting is the durable form bale itself recommends for
  such a host, written once instead of being answered at every apply.

### Questions a reviewer will ask

- Can a refresh lose work? It never deletes a ref, never moves the
  workbench branch, never merges, and pushes nothing; a base with
  commits of its own is left as it is.
- Why not fetch in the clone? It has no credentials for the audience;
  this machine does.
- Why does the merge commit stay on the workbench? It is how the
  workbench and main come to part at main's tip; it never leaves (the
  delivery is a squash of the workbench's own changes).
- Why not merge under an open session? bale would refuse that session's
  apply for files that moved under it.
- Is the sandbox setting written everywhere? Only where `unshare -Ur
  true` refuses, which means bale's own probe refuses too.

### A hand test

1. On the work office: `office projects set NAME --prepare` for each of
   the two container clones; `office status` should show `sandbox: off by
   bale.toml, written ...` for each, and the next `office land` there
   should not ask about the sandbox.
2. `office projects refresh NAME` for the container clone: read the
   lines (what moved, the bundle carried, main left or fast-forwarded),
   then `office projects` for the refreshed line.
3. After a review merges on the git host, `office deliver FOLDER` on a
   terminal: answer the refresh question, read the `merged:` line and the
   folder's History, and decline the push if you only want to look.
4. On a clone whose workbench conflicts with main: deliver should name
   the files and say the merge session is the next release's; `git
   status` in the clone should be clean.

## Delivery

- to: nobody

### Commit

office-src 0.39.0: refresh a hosted clone's view of its audience

office projects refresh NAME fetches the audience's branches on this
machine, with a forcing refspec, and carries them into a clone on a host
as a thin bundle, fast-forwarding its base where it can; it never moves
the workbench branch, deletes no ref and pushes nothing. office start and
office deliver say when the clone's view of the base is behind and offer
the refresh. office deliver brings the base into the workbench as a merge
commit when that merge is clean, and refuses a conflict by name with
nothing left half-done. Prepare writes bale.toml's sandbox setting only
where bale's sandbox cannot run, and office projects set NAME --prepare
runs it again on a declared clone.

### Review

office-src 0.39.0: a hosted clone's view of its audience

What to look at: lib/office_refresh.py, plan's steps 4b and 4c and
merge_base_in in lib/office_deliver.py, prepare's sandbox step in
lib/office_host.py, and the 0.39.0 entry in RELEASES.md.

What to try by hand: office projects refresh on a hosted clone after the
audience moves; office deliver on a terminal after a review merges; office
projects set NAME --prepare in a container, then office status.

Deliberately untouched: a merge that conflicts (the next release's merge
session), base_holds and the refusal of work leaving twice, the squash's
shape, and --others-too.

## Structure

- title: office-src 0.39.0, a hosted clone's view of its audience
- size: large
- goal: Release office-src 0.39.0: office projects refresh NAME brings a clone's view of its audience level through this machine (forcing refspecs, a thin bundle to a hosted clone, the base fast-forwarded, what moved said), start and deliver offer it when the view is behind, deliver brings the base into the workbench as a merge commit when that merge is clean, and prepare writes bale's sandbox-off setting only where bale's sandbox cannot run

## Handbook

### office-src

- `office projects refresh NAME` leaves `refs/office-refresh/AUDIENCE` in the clone, a ref to a three-line blob (refreshed UTC time, from the audience and URL, by way of this machine's hostname); `office projects` reads it, and it sits outside refs/office/, which office deliver empties after every delivery.
- For a clone on this machine, office deliver's fetch of the base from the clone's own remote by name moves `refs/remotes/AUDIENCE/BASE` too (git's opportunistic remote-tracking update), so deliver reads that clone's view after the fetch and never offers it a refresh; only a hosted clone's view goes stale.
- office deliver on a host reads the clone's git facts and its view of the audience (`office_refresh.view_argvs`, with the two merge-base ancestry checks) in one connection, and office status reads the sandbox setting after `bale --version` in one connection (`Reader.invoke(also=...)`); tests pin both counts.
- The clean merge runs only for a delivery made from the base (not one continuing on a branch), only when the clone's AUDIENCE/BASE equals the base deliver fetched, the tree is clean (tracked files) and no bale session is open in the clone; a merge git refuses to start (exit 8 of `_MERGE_SCRIPT`) is said and the plan goes on.
- The merge does not change what twice_lines sees: another folder's workbench commits stay on the workbench side of the base, so a review merged as a squash still refuses until base_holds reads content.
- prepare's sandbox test is `unshare -Ur true` where the clone is (OFFICE_SANDBOX_PROBE on this machine replaces it; the suite's Env sets it to `true`); it writes the table only on a non-zero exit other than 126 or 127, under a `# office sandbox: written DAY: WHY` line that office status reads.
- tests/test_suite_clock.py SIBLINGS_AT_TOP names lib/office_refresh.py's top-level imports (office_helper, office_host, office_bale); office_deliver imports office_refresh inside the functions that use it, so its own set is unchanged.

#### Front sheet

office-src is at 0.39.0. A clone on a host gets its view of the audience
refreshed through this machine with `office projects refresh NAME`, and
office start and office deliver offer that when the view is behind.
office deliver brings main into the workbench itself when that merge is
clean, and when it conflicts it names the files, leaves the clone clean
and says what to do by hand until the merge session arrives in the next
release. Prepare writes bale's sandbox-off setting where bale's sandbox
cannot run: run `office projects set NAME --prepare` once on each of the
two container clones and the sandbox question at every apply stops.
Still open: the merge session for a conflict, a review merged as a
squash (deliver still cannot see the base holds it), the squash of a
continued delivery from its range, and a local branch the BRANCH
checkout finds behind its remote.
