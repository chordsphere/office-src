# Notes: m10-pull-requests (office-src 0.42.0)

Items 1 to 7 and 9 of the brief shipped; item 8 (take_out_own's refusal
as a session) is the half left, as the brief's seam named, and it is the
first Proposal below with what I learned of take_out_own. Each shipped
item has a class in the new tests/test_pull_requests.py (24 tests) but
item 5, which is words, and item 9, which is
tests/test_deliver_merges.py TestTheWholeLoopThroughTheOffice as the
brief asked.

The whole suite ran on the finished tree: 1219 tests, all OK, in 926 s
here (four jobs on two CPUs). The unchanged tree's suite was 1194 tests,
all OK. A few small edits landed after that run started: the hosted
project's silence (decision 7), the refusal's wording (decision 10),
share/verbs.toml and a lint fix in the fake. So I reran the modules they
touch on a staging copy built from the request's tree plus this
response's files/: test_pull_requests, test_office, test_desk_verbs,
test_project_on_host and test_suite_clock, 299 tests, OK.
validation.sh's fast run on that copy (the tier plus eight of this
session's tests, 367 tests) took 75 s of the tier's 120. The rest of
test_pull_requests, the terminal class and the whole-loop test (19 s) sit
behind --slow with the touched modules. On the unchanged tree the new
module cannot import lib/office_review.py, and the release, doctrine and
History-verb assertions in validation.sh fail there, as they should.

The whole-loop test found a real gap on its first run, which is the point
of it: with the merge session open in the clone, a second `office
deliver` did not say `office land SID`. It went on to a squash that
conflicted and refused with the generic "brings origin/main into the
workbench first" line. The step-by-step tests never saw it, because they
named the session on the job in-process (`odl.merge_sent`) without bale
ever reporting it open. `resolve_landed_job` now returns the landing line
for deliver when the job's session is still open, and the plan refuses
with it (decision 9).

Every changed path is inside the write forecast (bin/office, lib, share,
templates, tests, README.md, RELEASES.md, VERSION, doctrine/OFFICE.md,
claude/context/front-sheet.md); no template changed, since item 8 did not
ship. share/verbs.toml changed because deliver now writes one more thing
outside the office (a pull request, through gh).

Where a cite and the tree disagreed: nothing material. `named_branch`,
`slug_branch`, `take_out_own`, `run`'s `adopting` and `joined` branches,
`review_url`, `branch_url` and the survey's Tools loop were where the
brief said, give or take a few lines.

## Decisions

1. **The gh door is `OFFICE_GH_PATH`, read by `office_review.gh_program`.**
   Set, it lists the directories gh is looked for in ("" none); unset, the
   PATH. It never runs a shell lookup, so tests/test_suite_clock.py's
   lookup rule has nothing to excuse. Every `Env` and every runner job set
   it empty (tests/runner.py `GH_VARS`, asserted beside `SURVEY_VARS`), so
   no test touches a real gh, and the tests that want one put the fake
   (tests/fakes/gh_fake.py) in a directory and name it. This mattered
   here: the sandbox I built in has a real gh on its PATH, and without the
   door every terminal deliver test would have met a new question.
2. **How the host is named to gh: `--repo HOST/OWNER/REPO`**, from the
   audience remote's URL (`parse_remote_url`). No GH_HOST, no running in
   the clone, so the same call works for a project whose clone is on a
   host. Whether gh is signed in is asked first with `gh auth status
   --hostname HOST`, so a signed-out gh is said before the question
   rather than after a yes.
3. **The reviewer is passed only when `to:` reads as a GitHub login**
   (`@pat-reviewer` or `pat-reviewer`: letters, digits and single
   hyphens, at most 39). A name, an address or several people are printed
   as before and never passed; the question says which.
4. **The History verb is `review`**: `- DATE review: BRANCH on AUDIENCE
   of PROJECT: #N URL`, mirroring `delivered`'s head so one regex reads
   both. Added to HISTORY_VERBS, so office status knows it. It is written
   before the folder closes at delivery (bin/office calls
   `deliver_review` before `deliver_close`), so it lands where the folder
   is; a test pins it on a terminal, where the folder closes.
5. **The body never rides on gh's command line**: `--body-file` from a
   temporary file, removed after. The question shows the gh line with
   `<the review's body>` in the file's place.
6. **The clipboard gets the body whenever the office did not open the
   review**, including a branch whose review is open already (joined,
   adopted, continued), where the body is the reply's words. Before
   0.42.0 the URL went to the clipboard; A6 says the URL's query was not
   taken by the host, so the URL is printed and the body is the paste.
   When the review was opened, nothing is copied.
7. **Review state is one `gh pr list --state all` per project** with a
   branch the office delivered (from the folders' `delivered` and
   `review` lines), not one call per branch; 15 seconds; never a prompt.
   An open review always shows; a merged or closed one shows while one of
   its folders is on the desk, or for seven days after it closed, so the
   walk-in does not list every merged review forever. Nothing is cached.
   For a project whose clone is on a host and that has no recorded review,
   the repository is not known without reaching the host through its
   shell, which a rendering does not do, so nothing is said (a debug
   line); once a review is recorded its URL names the repository.
8. **Where review state is said.** The walk-in and `office desk` get a
   `Reviews:` section after the In flight block, one line per project,
   plus a line for each review that asked for changes saying what answers
   it. "The folder's Next names it" I read as the desk's folder line: its
   `next:` says `answer review #N's requested changes on BRANCH; then
   ...` before the folder's own Next. That is a rendering. The folder's
   Next section on disk is never written. A folder closed at delivery is
   not on the desk, so the Reviews section is where its review shows. The
   home screen's project line ends `; reviews: ...`; the digest gets a
   `## Reviews` section after "Since the last sitting", left out when
   there is nothing to read. I did not add a line to land's relay tail
   (0.41.0's `land_tail`): the sitting would welcome it, but the tail is
   written right after a landing, before any delivery, so it would almost
   always say nothing new. It is a Proposal.
9. **Deliver names `office land SID` while the merge session is open**
   (the gap the whole-loop test found, above). `resolve_landed_job`
   returns the line only when its verb is deliver; land's call is
   unchanged.
10. **The branch-name check (item 7).** The name is read as words are
    read: the office's forbidden strings, names, phrasing, bale's marks
    and the cleanup list. The "ends in three digits" rule applies only
    to a name the folder's slug chose, never to a name the occupant gave
    with `--branch` or `branch:`, because `fix-123` is a common branch
    for an issue and the session-id mark needs the date anyway. The flag's
    and the words' name is checked before any fetch, as the brief asked.
    The clone's branch and the slug are only settled after the audience
    has been asked whether it has the clone's branch (a fetch into the
    office's own refs), so they are checked right then, before the base is
    brought in or a worktree is made. The refusal says "nothing was made or
    pushed" in that case rather than "nothing was fetched". Flagged
    deviation, small.
11. **Item 3 runs for every continued delivery**, adopted, joined or this
    folder's own, since a folder's own branch can have a review whose base
    is not the project's. Without gh it says one line on the question's
    `from:` line; for a non-GitHub audience it says nothing.
12. **The doctrine's core.** Boundary 2 gained the clause in the brief's
    words, one line more. To keep the banner at line 299 I rewrapped a
    bullet of section 4's list ("This doctrine rides as a context tarball
    ...") from five lines to four, with no word changed. That was easier
    to read and kinder to the doctrine than taking words out of boundary
    2. Every heading is whole, and the core-first tests pass.
13. **`letterhead check --delivery` (item 6)** goes through a new
    `office_deliver delivery-words` subcommand, which prints `[[label,
    text]]` from `delivery_words` and logs the unread line. bin/office
    passes it as `--words-json`, which office_letterhead already took, so
    the letterhead module still imports nothing of the office. It travels
    with `--on PROJECT`, to a host too (deliver_py check gained
    `--words-json`).
14. **The test world for gh** reaches the bare audience as
    `git@github.example.org:acme/proj.git` through a fake ssh named in
    GIT_SSH_COMMAND that serves the bare repo. An `insteadOf` rewrite would
    not do, because `git remote get-url`, which deliver reads, expands it
    back to the path. The host and the login (`pat-reviewer`) are invented.

## Walkthrough

### What changed

- lib/office_review.py (new) is the office's one door to a git host's
  API. It finds gh, checks it is signed in to the audience's GitHub host,
  builds the review deliver offers, opens it on a yes, records the
  `review` History line, reads the open pull request on a branch, and
  reads review state for the renderings.
- office deliver, after the push, shows the review as gh will open it and
  asks once (`--open-review`, `--no-open-review`). Yes opens it and
  records it. Otherwise the review's body goes on the clipboard and its
  title and URL are printed under Next.
- office deliver reads the pull request open on a branch it adds to and
  shows that request's base in the question.
- office deliver checks the branch's name against the letterhead's marks
  before anything leaves, and while a merge session is out it names
  `office land SID`.
- The walk-in, office desk, the home screen and the digest say each
  review on a branch the office delivered.
- The survey records gh; `office letterhead check --delivery` reads a
  delivery.md as deliver does.
- Doctrine, README, RELEASES, front sheet, verbs.toml say all of it.

### Why

The report asked for a protocol for pull requests, so that nothing goes
to GitHub from a bare script and the office knows its reviews' state. A6
asked that the review's words reach the host without a retype. The
branch check and `--delivery` close two places where a name or a page
could leave in a shape the letterhead would refuse elsewhere. The
whole-loop test was 0.40.0's proposal.

### How to explain each piece

- gh is optional. Without it, everything behaves as before and says so
  in one line.
- Nothing is opened on GitHub without the one question, and the answer
  defaults to no. Reading state asks nothing and changes nothing.
- The office never signs gh in and writes no token. It writes one History
  line with the review's number and URL.
- Review state is recomputed on every walk-in and kept nowhere.

### Questions a reviewer will ask

- What if gh hangs? Every call has a timeout (15 s to read, 60 s to
  open), stdin is closed, and gh's prompts are turned off.
- What if a pull request is already open on the branch? gh refuses; its
  words are printed, and the delivery stands. A branch the office knows
  has a review (adopted, joined, or one gh reads) is never offered.
- Why not one call per branch? One `gh pr list` per project is cheaper,
  and the office filters the result to its own branches.
- Why does a slug ending in `-002` refuse? Without its date it still reads
  as a session's slug and counter, and the brief asked that it not leave.
  A name you give is not held to that rule.

### A hand test

1. With gh signed in to the audience's host, land a session on a project
   with an audience and run `office deliver N` on a terminal. Answer y to
   the push and y to the review. A pull request opens with the Review
   section's title and body, and the folder's History has a `review`
   line.
2. Run `office` piped and `office desk`. The `Reviews:` section names the
   review. Approve it on GitHub and walk in again: `#N approved`.
3. Run `office deliver M --yes` on another folder, piped. Nothing is
   opened, and the Next lines carry the compare URL and the title.
4. Run `gh auth logout` for that host and walk in. The project's line
   says the state was not read, and the walk-in still succeeds.

## Delivery

- to: the occupant

### Commit

Open reviews through gh and read their state (0.42.0)

office deliver now shows the review as gh will open it and asks once,
then opens it and records its number on the folder, or puts its body on
the clipboard with the title and URL printed. The walk-in, the desk, the
home screen and the digest read each review's state through gh, read
only. A delivery added to a branch with an open pull request shows that
request's base. The survey records gh, the letterhead check reads a
delivery page as deliver does, the branch's name is checked before
anything leaves, and deliver names the landing while a merge session is
out. gh is optional everywhere.

### Review

Open reviews through gh and read their state (0.42.0)

What to look at: lib/office_review.py, the one place gh runs, and its
door gh_program; bin/office deliver_review, the question and what
happens on each answer; lib/office_deliver.py run's review offer,
branch_marks, and the plan's review_pr; lib/office_bale.py read_reviews
and the Reviews section. What to try by hand: one delivery on a
terminal with gh signed in, answered yes, then walk in. Then the same
piped with no flag, and once with gh signed out. Deliberately untouched:
answering a review's comments, a push from the host, the adoption
itself, and take_out_own's refusal, which is the next session's.

## Structure

- title: Give pull requests a protocol through gh (0.42.0)
- size: high
- goal: Give pull requests a protocol through gh (0.42.0): office deliver opens the review when asked and records its number on the folder, or puts the review body on the clipboard when it cannot; review state is read for the walk-in, the home screen, the desk and the digest; an added delivery shows the pull request's base; the survey records gh; letterhead check --delivery reads a delivery.md as deliver does; the branch name is checked against the marks; and the merge session's whole loop is tested through the office's commands

## Handbook

### Front sheet

office-src 0.42.0 gives pull requests a protocol through gh, optional
everywhere. office deliver shows the review as gh will open it and asks
once (`--open-review`, `--no-open-review`). Yes opens it and records a
`review` line in the folder's History. Otherwise the review's body goes
on the clipboard with its title and URL printed. The walk-in, office
desk, the home screen and the digest read review state through gh, read
only and kept nowhere. An added delivery shows its pull request's base.
The survey records gh, `office letterhead check --delivery` reads a page
as deliver does, and the branch's name is held to the letterhead's
marks. Additive: no migration.

### Facts

- gh is found only through lib/office_review.py gh_program: the directories OFFICE_GH_PATH lists ("" none), else the PATH; every Env and runner job set it empty, and tests use tests/fakes/gh_fake.py (a state file of hosts and pulls)
- gh is told the repository as --repo HOST/OWNER/REPO from the audience remote's URL; signed-in is asked with gh auth status --hostname HOST before deliver's review question
- the `review` History line is `BRANCH on AUDIENCE of PROJECT: #N URL` (office_review.REVIEW_RE); it is written before deliver_close, so it lands while the folder is on the desk
- office_deliver.run returns a fourth value, the review offer, printed as `review` in the run's JSON; bin/office deliver_review shows it and asks, and office_review.py open runs gh pr create --body-file
- review state is office_review.office_reviews, read once in office_bale.render_desk into groups reviews and reviews_by_rel: one gh pr list --state all per project with a branch the office delivered or reviewed; an open review always shows, a merged or closed one while a folder is on the desk or for RECENT_DAYS (7)
- deliver's branch name is checked by office_deliver.branch_marks: the letterhead's words rules for every name, and a trailing -NNN only when the folder's slug chose it
- a merge session still open in the clone stops deliver with `office land SID brings it back` (resolve_landed_job, verb deliver)
- the gh test world reaches the bare audience as git@github.example.org:acme/proj.git through a fake ssh in GIT_SSH_COMMAND; insteadOf does not work, since git remote get-url expands it
- tests/test_pull_requests.py holds 0.42.0's tests (24 in nine classes); the merge loop's is tests/test_deliver_merges.py TestTheWholeLoopThroughTheOffice

## Proposals

- **What:** item 8 of this brief, take_out_own's refusal as a session
  (`office start N --undo-bale`), with its own whole-loop test, as a
  session of its own. **Why:** it is the last ordinary deliver refusal
  that sends the occupant into the clone, and this session spent its
  budget on items 1 to 7 and 9. What I learned of take_out_own: it
  reverts each of bale's own commits newest first in the temporary
  worktree on the workbench's tip (`git revert --no-commit`). A conflict
  on a file bale only added lines to is resolved line by line
  (`lines_added_only`). Any other conflict aborts and raises one
  DeliverError naming the commit and the paths, so the job's inputs are
  all in hand at that point: the commit's sha and subject, the
  conflicting paths, and the workbench tip. The merge job's machinery
  fits it closely. `merge_job_lines` writes a page and three versions per
  file through `carry_materials`, and `merge_start` and
  `resolve_landed_job` read it back. A second kind on the same page (kind
  `undo`, the side being bale's commit rather than the audience's) would
  let one reader serve both, with `make_resolved_merge`'s counterpart
  making a plain commit on the workbench (`Undo bale's own change to
  PATH, resolved by SID (office land)`) instead of a merge. The new
  template sits beside templates/merge-brief.md. **Scope hints:**
  lib/office_deliver.py take_out_own (the refusal), merge_job_lines,
  read_merge_job, merge_start, resolve_landed_job and land_merge;
  bin/office start's `--merge` branch (5417, 5607) and land's merge step;
  templates/; lib/office_bale.py waiting_on_delivery for the offer.
- **What:** one more line on the planner's relay tail (0.41.0
  `land_tail`): the review state of the landed folder's branches when
  there is one. **Why:** the sitting said it would welcome it. I left it
  out because the tail is written at landing, before any delivery, so it
  would say something only when an earlier delivery of the same folder
  has a review. **Scope hints:** bin/office land_tail; office_review
  `states --project`.
- **What:** read a hosted clone's audience URL once and keep it in the
  floor plan (say `audience_url`), so review state reads for a project
  on a host before a review is recorded. **Why:** a rendering does not
  reach a host's shell, so such a project says nothing until its first
  `review` line. **Scope hints:** office_review.remote_url_of; office
  projects set; the push guard already records the URL in the hook.
