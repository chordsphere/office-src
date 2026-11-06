# Notes: 2026-11-06-m10-host-rides-002, rides from a project's host, the branch at start, the audience URL kept (office-src 0.50.0)

All four items shipped; nothing went to the seam. Every path is inside the
forecast (bin/office, lib, tests, README.md, RELEASES.md, VERSION,
doctrine/OFFICE.md, claude/context/front-sheet.md), so there are no
departures to admit. share/ and templates/ were forecast and not touched.
No context compaction happened this session.

Every file:line anchor in the brief matched the 0.49.0 tree I was handed;
I found no number that disagreed with its anchor.

## Decisions

Each of these is a reasoned deviation from a pin, or a call the brief left
to me. They're numbered so you can ratify or correct them by number.

1. **The host path's form is a little stricter than read_projects' rule.**
   The brief points at read_projects' rule for a hosted project's own path
   (absolute, or starts with `~`). That rule lets `~user/x` through. I
   take `/...`, `~` and `~/...` only, because the scripts that expand the
   path on the host (and `office_host.shell_path`) only know those forms.
   `host:~me/x` refuses at declaration with a line that says so.
2. **Connections at start.** The ride check and the branch read add no
   connection: they ride hosted_round's extras, after bale status and the
   doctrine's sums. Packing what rides from the host does add some. Every
   `bale pack --context` goes in one batched connection, then each tarball
   is fetched with `fetch_file`, the same way the request is. A scratch's
   removal rides its fetch. I read "reaches a host once per start" as the
   reach check plus no extra connection for the reads, since a tarball has
   to travel somehow. In the suite's count, a start on `far` with three
   host rides (one per kind) makes 8 connections. The same start with none
   makes 4.
3. **The scratch is removed when its tarball is fetched, not when it's
   packed.** The brief's scratch is removed in the pack's connection.
   That can't work here: bale writes a context tarball into the packed
   directory's own `.bale/outbox/`, so removing the copy after the pack
   would delete the tarball before it came back. `fetch_file` gained an
   `after=` argument for this (shell words run in the same connection
   after the read, with the read's exit code kept). If anything fails
   between the pack and the fetch, start's `finally` removes the scratch
   in a connection of its own, and the suite checks that nothing is left
   in the host's TMPDIR.
4. **The carried line for a file.** A file outside git is fetched as it
   is, not packed, so its line says `plan.md: rides with far
   (host:~/plan.md, carried from HOST as it is)`. Packs say `packed on
   HOST` as pinned, and a scratch says `packed on HOST from a copy there`.
   Several host rides in one repo there go out as one pack with several
   `--include`s, as they do from here, and the line lists each declared
   ride.
5. **An office session about a hosted project (`--about`) makes one check
   connection of its own.** Before this release such a session made no
   round on the host at all, so there was no round for the check to ride.
   The check runs before anything is written, the same as on a project
   session.
6. **The fast-forward also covers a clone already on the branch.** The
   brief says a behind local branch is fast-forwarded "before it is said
   checked out". If I limited that to an actual checkout, the clone that
   already has the branch checked out (the common case for a second
   session on a review branch) would keep building on the old tip. That's
   the exact gap 0.39.0's proposal names. So a clone on the branch, behind,
   clean and with no session open, is fast-forwarded too, and the line
   says so. If that clone is dirty or has a session open, nothing moves
   and the line says why. That isn't a refusal, since nothing needed
   checking out.
7. **Which remote-tracking ref counts.** It's the branch's configured
   upstream. Failing that, it's the one remote that has a branch of that
   name. With several remotes and no upstream configured, nothing is
   compared and the checkout goes on as before. The fast-forward is `git
   merge --ff-only -q <the remote tip read a moment earlier>`, in the same
   connection as the checkout. A branch ahead of its remote is said as
   well as one that has diverged. Neither one moves.
8. **The branch line** is exactly as pinned: `{project}'s clone at
   {where} is on {branch}`, or `a detached HEAD`. For a hosted clone,
   `{where}` is `PATH on HOST`, the same words checkout_branch already
   uses. It's a `log` line, so it shows on start's screen and not only
   under OFFICE_DEBUG. A branch that can't be read for any other reason
   gets its own line and never refuses the start. I left the Packed line
   alone, since the brief made that optional.
9. **`--branch` and the session kinds.** It goes with `--on`, `new` and
   `--drop`, and with `--merge` too, since that's a project session. It
   refuses with `--in-office` before anything is written, and the same
   refusal fires when `--in-office` is the answer to the where question.
   With `--sort`, `--prep` and `--planner` it refuses as part of those
   modes' "takes nothing else" checks. Its words come from
   checkout_branch with `source="flag"`, through `reader bundle-branch
   --from-flag`. The BRANCH line's own words haven't changed, and
   TestTheBundlesBranch passes untouched.
10. **"Set or kept" for audience_url.** The URL is written whenever
    `office projects set` or `add` reads the clone's remote to check
    `--audience REMOTE`. That covers the flag and the walk's audience
    answer. A piped `office projects set NAME` with no flag refreshes the
    push guard through office_deliver and doesn't read clone_facts in
    bin/office, so it writes nothing. That's why the release entry says
    to run `set NAME --audience REMOTE` once. `--no-audience` and
    `--on-this-machine` clear the URL. `--audience-url` on a project on
    this machine refuses by name.
11. **Taking a project off its host with host rides still declared
    refuses**, naming the rides, unless the same command replaces the
    list (`--no-rides`, or `--ride PATH`). A host ride left behind on a
    project with no host would be a declaration problem, and start would
    refuse it later anyway. If a floor plan gets into that state some
    other way (edited by hand, say), read_projects reports it as a
    declaration problem beside the project. `office projects` shows it,
    and start refuses with it before anything is written.
12. **The wizard checks only a host ride's form, one answer at a time.**
    The path itself is checked through the shell once, when the list is
    written (set_declarations), so a list of several host rides costs one
    connection.
13. **`office status` says nothing new about host rides.** It never read
    rides before this release, and nothing in the friction asks it to.
14. **README's stale sentence.** "On a terminal it lists what the project
    declares to ride, with sizes, and asks which ride this time" was stale
    against bin/office and test_second_trip (0.22.0 stopped asking). It
    now says what start does: one line saying what rides, and it all
    rides. A sentence in the README's audience paragraph says
    `branch_prefix` has "no verb [that] sets it yet". tests/test_land.py
    pins those words, so I left them and added "(0.46.0 built it:
    `--branch-prefix`)" after them. Removing the pinned phrase and its
    test pin is one small cleanup if you want it.

## The suite

- Baseline, the unchanged 0.49.0 tree, the ten modules this session
  touches: 444 tests, OK.
- The whole suite with the change: 1414 tests in 12m38s on two CPUs, one
  failure. tests/test_suite_clock.py TestNoTestReadsTheMachine caught
  three `/tmp` literals in my new unit tests (the machine's own temporary
  directory). They're now `/srv/...` paths, which are never read, and
  test_suite_clock and test_host_rides both pass whole (52 and 27 tests).
  No existing test had to move. The bundle's BRANCH words, the local ride
  tests and the hosted start tests pass as they were.
- The fast tier with this session's names (`tests/run.sh --fast
  test_host_rides.TestTheSpelling test_host_rides.TestDeclaredOnTheHost
  test_second_trip.TestWhatRides test_three_gaps.TestTheBundlesBranch`):
  387 tests, OK, 67.2 s of the 120 s budget. test_host_rides whole would
  push the tier near its budget, so the rest of it runs behind `--slow`.
- validation.sh in a staged copy (the 0.49.0 tree, files/ overlaid,
  apply.sh run): every check passed, about two minutes without `--slow`
  and 5m34s with it (the 13 touched modules whole). On the unmodified tree
  the Python syntax check (the new module is missing), the release, the
  doctrine, the surfaces and the fast tier all fail, as they should. Only
  `bash -n` and the exec bit pass on both, and they're guards.
- tests/fast-tier.toml is unchanged, since no verb was added. No test
  hard-codes a day or a VERSION.

## Walkthrough

### What changed

- **A ride on the project's host.** office_helper gains HOST_RIDE,
  is_host_ride, host_ride_path, check_host_ride, ride_words and a
  host-aware check_ride. set_declarations checks the new list's host rides
  through office_host.ride_facts, in one connection, with the project's
  host or the one the same command gives it. read_projects reports a host
  ride on a project with no host. describe_declarations, the map's
  project_row and the listing say it as stored, marked `(on HOST)`.
  project-facts gives an empty third field for it, and ride_choice
  matches it as declared.
- **The ride at start.** office_bale.start splits the rides. For a
  hosted project, the ride facts script (office_host._RIDE_FACTS_SCRIPT)
  and the branch read ride hosted_round's extras, and read_host_rides
  stops the start on a ride that's gone. pack_host_rides packs them on
  the host: one batch of `bale pack --context`, in the repo's top with
  `--include` (bale_in_argv), or in a scratch copy (ride_scratch_argv).
  It fetches each tarball, or a file as it is, into the tray.
- **The branch line.** office_bale.BRANCH_ARGV, clone_branch_line and
  say_clone_branch. The read happens in the hosted round, or here for a
  project on this machine.
- **`--branch NAME`.** bin/office cmd_start parses it.
  start_branch_checkout runs it after the refresh offer, for a session
  that isn't a bundle's. check_start_bundle passes `--from-flag` when the
  flag stands over a BRANCH line, and bundle_lands_read says that it
  stands.
- **The fast-forward.** checkout_branch reads where the local branch
  stands against its upstream in the same connection as its other reads
  (_UPSTREAM_SCRIPT, read_upstream), then checks out and `merge
  --ff-only`s in one more. stand_words says ahead or diverged.
- **audience_url.** It's the sixth AUDIENCE_KEYS entry, with
  check_audience_url. That gives `--audience-url` and `--no-audience-url`
  on project-declare for free. bin/office set and add write it from the
  URL they already read, and remote_url_of returns it for a hosted
  project.
- **Docs and release.** The doctrine's core (two bullets, same line
  count, banner still at 299), section 10, the BRANCH paragraph and the
  projects and start rows. README, RELEASES.md, VERSION and the front
  sheet. tests/test_host_rides.py.

### Why

- Item 3 of the friction report: a ride had to be a path on chordsphere,
  so the shiny original that lives only in the container had to be
  carried home by git bundle before it could ride.
- Item 9: deliver squashes everything since the clone's branch left the
  base, and nothing showed or set that branch before a pack.
- 0.39.0's proposal: the refresh moves `origin/BRANCH`, but a local branch
  the clone already had was checked out at its old tip.
- 0.42.0's proposal: a hosted project showed no review state until its
  first `review` line, because a rendering never reaches the host.

### How to explain each piece

- `host:PATH` means "this path, where the project's repo is". It's
  checked there when you declare it and again at every start, and the
  host's own bale packs it, so bale's filters apply exactly as they do to
  the request.
- The branch line is the one fact deliver depends on, now said before
  the session goes out.
- `--branch` is the BRANCH line for a session you start yourself.
- A behind local branch is moved forward only when that can't lose
  anything: the clone is clean, the move is a fast-forward and no
  session is open in it.
- The audience URL is written once from the clone, so the office can ask
  the git host about reviews without touching the project's host.

### Questions a reviewer will ask

- *Why not tar the directory on the host?* The pin says the host's bale,
  and bale's filters are the reason. A plain tar would carry secrets and
  junk that a context pack leaves out.
- *How many connections does a start make now?* With no host rides, the
  same as before. The check and the branch read ride the existing round.
  With host rides, one more for all the packs, plus one fetch per
  tarball.
- *What if the scratch can't be removed?* It's said loudly with its path
  (`left behind`), the same as the brief's scratch. The suite checks that
  nothing is left in the host's TMPDIR.
- *Can a fast-forward surprise a session?* No. It never runs over
  uncommitted changes or under an open session, and it moves only to the
  tip the clone already fetched. The office fetches nothing.
- *Why keep the URL only for hosted projects?* A clone here is read live,
  so a kept URL could only go stale.

### A hand test

1. On a hosted project, `office projects set NAME --ride host:~/some/dir`.
   It should take a second, and `office projects` should show `rides:
   host:~/some/dir (on HOST)`.
2. `office projects set NAME --ride host:~/not-there` should refuse with
   `no such path on HOST`, and the floor plan should be unchanged.
3. `office start FOLDER --on NAME --goal "..."` should show a line
   `NAME's clone at PATH on HOST is on BRANCH` before `Packed`, and the
   tray's listing should show `rides with NAME (host:~/some/dir, packed on
   HOST)`. Open that tarball and check it holds what you expect.
4. On the host, `ls ${TMPDIR:-/tmp}/office-*` should show nothing left.
5. `office start FOLDER --on NAME --goal "..." --branch SOME-BRANCH` on a
   clean clone should check it out and say so. Try it again with a dirty
   file and it should refuse with nothing written.
6. `office projects set NAME --audience origin` on a hosted project with
   an audience should make `office projects` show `audience URL: ...`.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: host-rides

### Commit

Ride paths from a project's host, name and set the branch at start

A hosted project can now declare a ride on its host, host:PATH. It is
checked there through the project's shell when declared and again at
office start, packed there as a context tarball, and carried back
into the out tray like the request. office projects and the map show it
as stored, marked as the host's, and reach no host for it. Every project
session's start names the clone's branch before the pack, and office
start --branch NAME checks a branch out first, with the same refusals as
a bundle's BRANCH line. A local branch behind its remote-tracking ref is
fast-forwarded when the clone is clean, naming both tips, and a diverged
one is checked out as it is. A hosted project keeps its audience's URL,
audience_url, so its review state reads before its first review.

### Review

Ride paths from a project's host, name and set the branch at start

Look at office_bale.start and pack_host_rides, office_host's ride facts
and scratch scripts and fetch_file's after argument, set_declarations'
host check, and checkout_branch's fast-forward. To try by hand: declare
host:PATH on a hosted project, start a session on it and open the
tarball, look for nothing left in the host's TMPDIR, and start with
--branch on a clean clone and on a dirty one. Deliberately untouched:
office status, the planner's gathering, office probe, and where the
in-tray's drops, the doctrine and the office's context are made.

## Structure

- title: Rides from a project's host, the branch named and set at start, the audience URL kept
- size: medium
- goal: Rides from a project's host, the workbench branch named and set at start, and a hosted project's audience URL kept: office-src 0.50.0

## Handbook

### office-src

- a ride may be `host:PATH` on a hosted project (office_helper.HOST_RIDE, is_host_ride, check_ride with the project's host); set_declarations checks the new list's host rides through office_host.ride_facts in one connection, and read_projects reports one on a project with no host as a declaration problem
- office start checks host rides in hosted_round's extras (office_bale.read_host_rides) and packs them on the host in office_bale.pack_host_rides: one batched connection of `bale pack --context` (office_host.bale_in_argv, ride_scratch_argv), then office_host.fetch_file per tarball, a scratch's removal riding its fetch (`after=`)
- start's screen names the clone's branch for every project session (office_bale.say_clone_branch, BRANCH_ARGV), read in the hosted round or here
- office start --branch NAME runs `reader bundle-branch --from-flag` (bin/office start_branch_checkout) through checkout_branch(source="flag"); checkout_branch fast-forwards a behind local branch (_UPSTREAM_SCRIPT, read_upstream) when the clone is clean and no session is open
- audience_url is the sixth of office_helper.AUDIENCE_KEYS, kept for a project on a host only; office_review.remote_url_of returns it for a hosted project
- a test on a host ride puts what rides under the fake ssh's hosts/HOST/home, so `~/...` there is not a path on this machine (tests/test_host_rides.py HostRideCase)

#### Front sheet

office-src 0.50.0 lets a project on a host ride what lives on that host.
`office projects set NAME --ride host:PATH` declares a path there. It's
checked on the host, packed there by the host's bale at every start and
carried back into the out tray beside the request. `office projects` and
the map show it marked as the host's. Every project session's start now
names the branch the clone is on before it packs. `office start --branch
NAME` checks a branch out first, refusing over uncommitted changes or an
open session. A local branch that's behind its remote is moved forward
when that's safe. A hosted project now keeps its audience's URL, so its
review state shows before its first review. Run `office projects set
NAME --audience REMOTE` once on each hosted project with an audience.
Additive: no migration.

## Proposals

- **What:** let `office probe` reach a hosted ride (the brief's "Not this
  session" names it). **Why:** a worker can now be handed a ride's
  context from the host, but it can't probe the place it came from
  without the project's own clone. The ride facts script already answers
  where each path is. **Scope hints:** lib/office_probe.py, and
  office_host.ride_facts for the path.
- **What:** say on start's screen when a host ride's pack takes long, or
  cap what one may hold. **Why:** a host ride is packed and carried
  through the shell inside the session's start. A large directory
  outside git is copied in full on the host before the pack, and nothing
  bounds it before bale's own caps. **Scope hints:**
  office_bale.pack_host_rides, office_host._RIDE_SCRATCH_SCRIPT (a `du`
  beside the copy would cost nothing).
- **What:** drop README's pinned "no verb sets it yet" sentence about
  branch_prefix, with its pin in tests/test_land.py
  TestWhereTheReleaseIsSaid. **Why:** it has been false since 0.46.0, and
  decision 14 could only annotate it. **Scope hints:** README's audience
  paragraph and tests/test_land.py line 776.
