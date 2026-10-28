# Notes: 2026-10-28-office-src-fix-three-gaps-m10-hit-on-002

office-src 0.34.0: the three gaps the M10 walkthrough hit on 2026-10-27,
deliver first, one additive release. All three are built with their
tests, the doctrine and README in their own voice. Three things to look
at on review: what the probe found about the slips, the mechanism calls
below for ratification, and one path outside the forecast.

## What the probe established (TARBALL.md 4.5)

One probe round, read-only, run from office-src's repo on your machine
(the host section stayed off; nothing left the machine):

- **The slips are not in work-office's suggestion box.** It holds `.keep`
  and one slip, 2026-10-09's "office start on a host: a lane with several
  paths" (a different gap, not this session's). No slip from 2026-10-27
  exists there. I built the three fixes from the goal's three sentences
  and from the record of the job that hit them, which the probe read
  whole: work-office's folder 6, "Answer Andrew's review on the API
  picklists PR", lane m10-api (a project on docker.medgen through a
  container shell, audience `origin` on github.iu.edu, base main). Its
  History shows a planner sitting
  (2026-10-27-get-m10-ready-to-show-answer-andrew-s-sitting-002), the
  worker that answered the review (2026-10-28-picklists-review-andrew-001,
  landed 20:35) and a second session that fixed delivery.md's Review
  title so deliver would read it (2026-10-28-folder-6-review-title-001,
  landed 20:53), and no `delivered` line: the delivery onto the pull
  request's branch is what deliver refused. If you did write slips and
  they are elsewhere, read this release against them; the mechanism calls
  below are where they would change anything.
- **No bundle in your downloads names a branch.** The twelve newest
  bundles' briefs carry no marker line of any kind except the sort's
  LANDS line, and no line mentions a branch; so the BRANCH line is a
  new convention, named in the doctrine and the sitting's brief template
  so the next planner knows it.
- office-src is at 6fcb558 (0.33.0, m10-sitting-fixes landed), the
  install at 0.32.0, bale 0.4.55, python 3.12.3, git 2.43.0, WSL.

## What I decided, for you to ratify

1. **Adoption is asked, never assumed.** A branch the audience has that
   the folder never delivered to may be a stranger's; only you know it is
   the pull request's. Piped, deliver refuses as before, its words now
   naming `--adopt`; on a terminal it asks once after showing the
   delivery whole, default no. `--adopt` on a branch the folder delivered
   to before changes nothing and is never said.
2. **The adopted delivery's range.** The sessions covered and the
   "commits on the workbench since" line read from where the workbench
   and `AUDIENCE/BRANCH` parted, not the base: when the pull request's
   commits were pushed by hand from the same clone, they are not read as
   new work (git's squash never delivered them twice either, since it
   merges from the same point; this makes the words agree). With no common
   history the base's merge-base stands, as before.
3. **The record.** The `delivered` History line ends `; adopted` (the
   reader accepts both forms, so no old line changes meaning), and the
   next delivery continues on the branch as on the folder's own, through
   the record. Nothing is written in the folder about which pull request.
4. **The next line after an adopted delivery** lists the reviews for the
   branch (GitHub `pulls?q=is:pr head:BRANCH`, GitLab merge requests by
   source branch) and says the Review section's words are the reply,
   rather than the compare page that opens a new review's form; an
   unknown host gets the sentence without a URL. The line still starts
   `open the review:` so bin/office's clipboard copy of it holds.
5. **The BRANCH line lives in the brief**, `--- BRANCH NAME ---`, read
   where the LANDS and RATIFIED lines are read (outside fences and
   notepad pages), since bale's bundle format is bale's and names no
   branch. A line that does not read, or a second one, is said and the
   start goes on without it, as the LANDS line's problems are handled.
6. **What the checkout refuses.** Uncommitted changes (tracked files;
   untracked ones do not block a checkout), a session open in the clone
   (bale lands it on the branch checked out, so moving the clone under it
   would land it elsewhere; a clone already on the named branch is not
   refused for an open session, since nothing moves), a branch that is
   nowhere in the clone, and a branch on several remotes with no local
   one. The office fetches nothing: a hosted clone's credentials are not
   its own, and the deliver mirror's reverse (fetching here and carrying a
   bundle there) is a mechanism of its own, proposed below. A local
   branch is checked out; a branch on exactly one remote gets a tracking
   local branch, as `git checkout` would make.
7. **A BRANCH line in an office bundle refuses** rather than being
   ignored: the office works on one branch, and a planner who wrote it
   meant a project.
8. **The spanning probe's shape: `office-on PROJECT COMMAND...`.** A
   worker cannot be handed a shell prefix to quote correctly, so the
   office hands it a command. The names are read from the block's own
   non-comment lines before anything runs (a header line that mentions the
   helper names no project), each must be literal (a name through a
   variable is refused at run time, exit 97, and the plan says so), and
   the block runs in the office root with the helper first on its PATH,
   written beside the plan under bin/office's temporary directory and
   gone with it. Each call runs `bash -c COMMAND` where the project lives
   through office_host.run_in: on a host through the shell's plain form,
   in the path, stdin closed, with the 900-second transfer timeout per
   call under the probe's own backstop. Through a shell the streams come
   back line by line without their last newline (office_host's call
   blocks), so run_on adds one; a block's next line then starts fresh.
9. **A spanning block takes no --project.** cmd_probe sets the project
   to office and says so; `--project office` is accepted, another name
   refused before any host is reached. Its session pool is the folder's
   sessions open in the office (sittings and office sessions) plus those
   open in every project reached (one connection each, which is also the
   reach), chosen by choose_session as before, so a sitting's spanning
   probe needs no --sid when the sitting is the folder's one session.
10. **The release is 0.34.0**, additive, and claude/context/front-sheet.md
    gets its line, which test_suite_clock's record pin needs.

## One new module, inside the forecast: tests/test_three_gaps.py

The request forecasts `.`, so nothing is outside it and there is no
departure to admit. The new module holds all seventeen of this session's tests
in seven classes (one per mechanism, its hosted twin, and the terminal
cases), so the three gaps read as one release's tests the way
test_answer_review.py holds 0.33.0's. No module avoids `m10_`; its name is
test_three_gaps.

## Things you should know

- **tests/test_audience_line.py's existing pin held unchanged**: the old
  refusal's two phrases ("origin already has a branch named theirs, and
  desk/", "name another: --branch NAME") are both in the new refusal, so
  that test passes as written; I did not touch it.
- **The terminal tests needed no `[keep]:` step**: deliver's questions are
  one-line asks, not ask_words.
- **The hosted spanning probe makes one connection more than a plain
  hosted probe** (the plan's status read of each project reached, then
  each office-on call is a connection of its own: run_in through
  run_many). TestProbeOnAHost's cap of five connections is for the plain
  shape and is untouched; the spanning test asserts the host, the plain
  form and nothing left behind, not a count.
- **office-on and bale**: a call may run `bale status` on the host, as the
  probe I sent you would have with PROBE_HOST=1; it is a read like any
  other command the block names, under the header's promise.

## Validation, as it ran here

The request carries the fixtures and migrations, so the suite runs whole
in this sandbox. I rehearsed bale's staging (the request's tree, `files/`
over it, `apply.sh`, the manifest as `.bale-manifest.json`) and ran
validation.sh both ways, and against the unchanged tree:

- Every session assertion passed on the change and failed on the
  unchanged tree (`bash -n` and the exec bit pass on both, as they
  should; the python syntax check fails on the unchanged tree only
  because it names tests/test_three_gaps.py, which is not there).
- `tests/run.sh --fast, with this session's tests`: passed, observed; the
  tier took 92.8 s of wall clock here against the 120 s budget (88.6 s in
  a run outside staging). It names six of the module's seventeen tests
  by id: the module whole took about 150 s under the runner's four-way
  load, so naming it would break the budget, as 0.33.0's notes warned.
- `--slow`, the eight touched modules whole (test_three_gaps,
  test_audience_line, test_clean_delivery, test_probe,
  test_planner_from_words, test_land, test_start, test_out_trip_to_host):
  passed, observed, 308 tests in about eight minutes with four jobs.
- The fixture pins of 0.32.0 and 0.33.0 (test_walkthrough_tidy,
  test_probe's and test_audience_line's TestTheRecord) and test_office's
  text rules pass; the suite's placeholder check caught an unfilled line
  in my RELEASES.md entry before I shipped it, which is what it is for.
- The new tests against the 0.33.0 code: every one that drives a verb
  fails there (the refusal's words, the branch left where it was, a
  spanning block refused for `--project office` not fitting); the unit
  tests of the URL and of `brief_branch` fail on the missing names.

## Proposals

- **What:** let `office start` fetch the branch a bundle names when the
  clone has none: here, with your credentials, as deliver fetches the
  audience, and carried to a hosted clone as a bundle the way deliver's
  mirror carries the landed work back. **Why:** a pull request's branch a
  coworker opened is on the audience and not yet in the clone on the
  host, and today start stops and names `git fetch`, which on the host
  means a credential prompt in a container. **Scope hints:**
  lib/office_bale.py `checkout_branch`; lib/office_host.py `send_file`
  and a bundle through the shell; the audience is known only for a
  project with one.
- **What:** `office deliver` for an adopted branch could read the pull
  request's own base from the git host, when the host's API is
  reachable, rather than the project's `base`. **Why:** the `from main`
  shown is the project's declared base; a pull request onto another
  branch would be squashed onto its own branch all the same, but the
  question's `from` would be wrong. **Scope hints:** office_deliver.plan's
  shown base; small, and only for a GitHub or GitLab audience.
- **What:** a slip that is dropped should leave the office knowing it
  was: `office slip` could say the box's path and the count. **Why:** the
  three slips this goal names were never in the box; whether they went
  elsewhere or were never written, nothing told you. **Scope hints:**
  bin/office cmd_slip's last line.

## Walkthrough

### What changed

- **`office deliver` adopts a branch made outside the office**
  (lib/office_deliver.py `plan`: `adopting`, the refusal piped, the range
  from where the workbench and the branch parted, `branch_url` and `run`'s
  words and next lines; lib/office_helper.py `DELIVERED_RE`,
  `delivered_records`, `delivered_text` with `; adopted`; bin/office
  cmd_deliver's `--adopt`, deliver_show's branch line and the one question).
- **A bundle's brief names its branch and start checks it out**
  (lib/office_helper.py `brief_branch`, `BRANCH_MARK_RE`;
  lib/office_bale.py `bundle_lands` reads it beside the LANDS line,
  `checkout_branch` and the reader's `bundle-branch`; bin/office
  bundle_lands_read's `branch` row into START_BRANCH, check_start_bundle's
  checkout before `reader bundle-check`, usage_start's paragraph;
  templates/sitting-brief.md names the line).
- **`office probe` runs a spanning block** (lib/office_probe.py
  `reaches_of` on `read_block`, `plan_spanning`, `write_on_helper`,
  `run_on`, `on_main`, the `reaches` and `on` subcommands, `run` with the
  helper on PATH; lib/office_host.py `run_probe(env=)`; bin/office
  cmd_probe's reaches step and usage_probe).
- doctrine/OFFICE.md (front sheet; section 4 continued, the BRANCH line
  and the adopted branch; section 10, the spanning probe; the verb table's
  start, deliver and probe rows), README.md (start, probe and deliver in
  the short and the long passages, the module table), RELEASES.md 0.34.0,
  VERSION, the front sheet's Recent changes line.
- tests/test_three_gaps.py (new, 17 tests; the suite holds 1017).

### Why

The M10 walkthrough's planner sitting of 2026-10-27 answered Andrew's
review of the picklists pull request: the answer's delivery could not
reach the review's branch, since deliver refused a branch the folder had
never delivered to; its bundle was opened on whatever branch the clone
had, since nothing could name one; and its probes could not read the
work office's folder and the hosted repo in one block.

### How to explain each piece

- The adoption: "A pull request someone opened by hand is a branch the
  office never made. deliver now says so and asks whether this delivery
  joins it; say yes and the commits go onto the review's branch, and from
  then on the folder treats it as its own."
- The BRANCH line: "A planner's brief can say `--- BRANCH picklists ---`,
  and start puts the clone on that branch before bale opens the bundle,
  so the session builds where its work belongs. A clone that cannot be
  moved there is said, and nothing is written."
- The spanning probe: "A worker's block can call `office-on m10-api 'git
  log -3'`; the block runs in the office, and that line runs on the host.
  You still read the header and say yes once."

### Questions a reviewer will ask

- *Can `--adopt` push onto a stranger's branch?* Only when you name that
  branch with `--branch` and say yes, or pass `--adopt`; the default
  branch is the folder's slug, which is never on the audience unless the
  office put it there.
- *Does an adopted delivery rewrite the pull request's commits?* No: the
  worktree starts at the branch's tip as fetched, and the squash adds one
  commit (or the words' several) on top.
- *Why refuse the checkout when a session is open in the clone?* bale
  lands a session on the branch the clone has checked out; moving the
  clone under it would land that session on the review's branch.
- *Why is a project name through a variable refused by office-on?* The
  office reads which projects a block reaches before it runs, so it can
  refuse one it does not scope with nothing reached; a name it could not
  read is one it did not check.
- *Does a spanning block ever run on the host itself?* No: the block runs
  in the office root, and only each office-on command crosses.

### A hand test

1. In work-office: `office deliver 6 --branch BRANCH` where BRANCH is the
   picklists pull request's branch on origin. deliver fetches it, shows
   the review's answer as one commit on top of it, and asks
   "origin already has a branch named BRANCH, and this folder records no
   delivery on it, so it was made outside the office; add this delivery
   to it? (--adopt) (y/n) [n]". `y`, then `y` to the push. Folder 6's
   History gains `delivered: BRANCH on origin of m10-api: ...; adopted`,
   and the Next line lists the pull requests for that branch on
   github.iu.edu.
2. Have the next planner's brief carry `--- BRANCH BRANCH ---` beside its
   LANDS line; `office start` on its bundle says "checked out BRANCH in
   m10-api's clone at ... on zagoodma@docker.medgen.iupui.edu" before
   "asking bale whether it can open"; `git -C` the clone there shows
   HEAD on BRANCH.
3. Put a probe block on the clipboard whose body has `office-on m10-api
   'git log --oneline -3'` and run `office probe 6`: it says the block
   calls office-on for m10-api and runs in the office root; after `y` the
   three commit lines from the host appear inside the PROBE BEGIN/END
   block beside the office's own lines.

## Delivery

- to: nobody

### Commit

Fix the three gaps M10 hit: deliver adopts a branch, a bundle names its branch, a probe spans the host

office deliver adopts a branch the audience has that the folder never
delivered to (a pull request opened by hand), asked once on a terminal
or with --adopt, so a review's answer lands on the review's own branch;
the folder's delivered line ends "; adopted" and the next delivery
continues on it.

A planner's brief may carry one BRANCH line, "--- BRANCH NAME ---",
beside its LANDS line, and office start checks that branch out in the
project's clone, here or through its shell on a host, before bale open
--check runs; a dirty clone, a session open in it or no such branch
stops the start with nothing written.

office probe runs a block that calls office-on PROJECT COMMAND in the
office root with that helper on its PATH; each call runs its command
where the project lives, through its shell on a host, so one block
reads the office and the host.

Release 0.34.0, additive.

### Review

Fix the three gaps M10 hit (0.34.0)

What to look at: lib/office_deliver.py plan's adopting branch and range,
lib/office_bale.py checkout_branch's refusals, and lib/office_probe.py
plan_spanning and run_on (the helper's line is read by hand in on_main).

What to try by hand: the three steps of the walkthrough's hand test.

Deliberately untouched: bale's pack, open and bundle format; the office
never fetches a branch (proposed); the LANDS and RATIFIED readers.

## Structure

- title: Fix the three gaps M10 hit: deliver adopts a branch, a bundle names its branch, a probe spans the host
- size: medium
- goal: Fix the three gaps M10 hit on 2026-10-27: office deliver adopts an existing audience branch made outside the office, a planner's bundle names the branch its session builds on and office start checks it out before bale opens it, and office probe carries a block that spans the office and a project's host

## Handbook

### office-src

- A `delivered` History line may end `; adopted` (office_helper.DELIVERED_RE, delivered_text's adopted flag): the branch was on the audience before the folder delivered to it; office deliver's --adopt (or yes on a terminal) is the only way such a branch is delivered to, and the next delivery continues on it through the record.
- A planner brief's `--- BRANCH NAME ---` line (office_helper.brief_branch, read beside the LANDS line by office_bale.bundle_lands) has office start check the branch out in the project's clone (office_bale.checkout_branch, the reader's bundle-branch) inside check_start_bundle, before bale open --check; a clone with uncommitted changes, a session open in it or no such branch stops the start, and the office never fetches.
- A probe block that calls `office-on PROJECT COMMAND` on a non-comment line spans the office and that project (office_probe.reaches_of, plan_spanning): it runs in the office root with the helper office_probe.write_on_helper writes beside the plan first on its PATH, and each call runs through office_host.run_in where the project lives (office_probe.run_on; exit 97 when it cannot be reached); such a block takes no --project.
- Through a shell, office_host.run_many's call blocks hand back each stream line by line without its last newline; a reader that prints the stream whole adds one (office_probe.run_on).
- tests/test_three_gaps.py holds 0.34.0's tests (17, in seven classes; the suite holds 1017); its hosted cases reuse FakeSsh through HostedStartCase and AudienceCase(hosted=True).

#### Front sheet

office-src 0.34.0 fixes the three gaps the M10 walkthrough hit on
2026-10-27, answering a review of a pull request on a hosted project.
`office deliver` can now add a review's answer to the pull request's own
branch: a branch the audience has that the folder never delivered to is
named as made outside the office, and you say once whether to adopt it
(`--adopt`). A planner's brief can name the branch its session builds on
(`--- BRANCH NAME ---`), and `office start` puts the clone on it before
bale opens the bundle, stopping with nothing written when the clone
cannot be moved. And `office probe` runs a block that spans the office
and a project's host: `office-on PROJECT COMMAND` inside the block runs
that command where the project lives. The suite holds 1017 tests. The
next of the eight M10 sessions is whatever the planning sitting lists
after these three.
