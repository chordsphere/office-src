# Notes: 2026-10-07-out-trip-to-host-004, the out trip to a host (office-src 0.15.0)

I built all five of the brief's items and the record as one additive
release (item 6 covers the docs and the record). Nothing lands outside the
forecast, which is the whole repo. The suite is green here: 589 tests, 38
of them in the new module `tests/test_out_trip_to_host.py`, run side by
side. The fake ssh is first on the PATH, and there is no network call and
no real ssh, rsync or docker. The new tests give each fake host its own
HOME, PATH and TMPDIR, so they can see that nothing the office makes is
left in the host's temporary directory.

In short:
- `office start` on a hosted project packs the session on its host and
  carries the request back into the out tray.
- `office projects add --from` moves a clone there.
- `office projects level-bale` installs this machine's bale there through
  the host's own `upgrade.sh`.
- Attended bale steps go through `ssh -tt` and the container's `-it`.
- `office land` still waits, and now says so in the brief's words.
- `tests/run.sh` prints each failing test's traceback.

## What the probes established

Two paste-back probes ran before any code was written, and both were
pasted back whole (494 and 839 lines; the integrity counts matched). The
first one's host half timed out on port 22 because the VPN client was not
connected, so the second re-ran the host half and read bale's install
scripts. Both were read-only: no file written here or there, `git` run
with `GIT_OPTIONAL_LOCKS=0`, and bale's help run with bytecode off.

- **How bale is installed, on both machines.** Each is a release install
  at `~/bale`, linked from `~/.local/bin/bale`, with the version in
  `bin/VERSION`, and `install.sh`, `upgrade.sh` and `validate.sh` beside
  `bin/`. bale ships its releases as tarballs (`~/bale-src/dist/bale-vX.Y.Z.tar.gz`
  holds one top-level directory). `upgrade.sh TARBALL` (0.4.51's, read in
  full) does the following:
  - takes `-y`, `--no-validate` and `--no-symlink`;
  - moves `<install>/user/` aside, wipes the rest, copies the release in
    and puts `user/` back;
  - execs `install.sh -y`, which restores exec bits, manages the
    `~/.local/bin` link and runs `validate.sh`.

  This machine's `~/bale` is refreshed by `~/bale-src/scripts/reinstall.sh`
  (bale-src's own post-apply hook), which mirrors `bin/ docs/ schemas/
  tools/` and the four top-level files and then runs `install.sh -y
  --no-symlink`. This machine's `~/bale` also holds a `.git` (9 tracked
  files, last commit in May) and a `.bale/`, neither of them bale's
  release. The host's install was made from `bale-v0.4.40.tar.gz` (the
  same timestamp as the dist file). The host's home directory is a git
  work tree with no commits, which is why `git -C ~/bale rev-parse` said
  true there. Nothing outside `user/` names a home path, so a copy of the
  install is position-independent.
- **`user/`**: on the host, `bale.toml` alone (sections `[apply]` and
  `[identity]`). Here: `bale.toml` (`[hooks]`, `[apply]`, `[identity]`,
  `[probe]`), a `scripts/` hook directory and `hook-acceptances.json`.
- **The host's bale 0.4.40.** `pack` has `--json`, `--readme-file`,
  `--no-readme`, `--read-only`, `--work-class`, `--constraint` and
  `--context`. `open` has no `--check` and no `--json`, and there is no
  `clipboard` verb. Those captures are kept, restored from the console's
  CP437 view as 0.4.47's were, under the record's
  `fixtures/bale-0.4.40/host/`. They are why the floor is a refusal for
  sending a session there, not only a status line.
- **Streams.** A tar of this machine's `~/bale` piped to the host's
  `sha256sum` through the full prefix, and the host's streamed back and
  hashed here, both came through intact (0.67 s and 0.79 s). The login
  shell prints 0 bytes on stdout and nothing on stderr, and a round trip
  took 1.47 s.
- **The container user** (the same name and uid as on the host): home in
  the container's `/home` volume, 124 GB free. `/tmp` is writable,
  `TMPDIR` is unset, and `mktemp`, `sha256sum`, `tar`, `gzip`, `rsync`
  and git 2.43 (identity set) are all there. `~/development` exists and
  holds neither M10 repo.
- **The two clones.**
  - Both are clean, not shallow, with no submodules or LFS, and origin is
    on the university git host.
  - `M10_BINGO_APP_INTERFACE` is on `feature/app-shell-remaining-views`
    with six local branches. `ref/full-port-answer-key` and the branch it
    is on exist only locally.
  - `M10_BINGO_APP_API` is on `feature/wire-health-route`, not "main
    only" as the brief had it; both of its branches are on origin.
  - Both carry upstream config for their tracked branches.

## Decisions to ratify

The brief's five, then the rest.

1. **The tty mechanism is derived, not a key.**
   - `Place.attended_words()` puts `-tt` after `ssh`. It then turns the
     first standalone `-i` past the ssh target into `-it`
     (`--interactive` gains `--tty`); ssh's own options are skipped
     with their values, so an `ssh -i keyfile` stays ssh's.
   - A prefix with no container layer gets `-tt` alone. A local
     `docker exec -i` prefix gets `-it`.
   - The office never stores a second prefix that could drift from the
     first. A hand-set override key would be the escape hatch if a shell
     ever needs one; I did not add it.
   - `Reader.interact` uses the attended form when stdin is a terminal,
     and the plain form with stdin closed when piped, so nothing ever
     asks.
   - Through a pseudo-terminal every line ends in CR LF, so the capture
     file is rewritten with LF after bale exits; land reads blocks from
     it line by line.
   - Nothing in this release calls it yet except the code path land will
     use. The suite drives it on a real pty, with a fake bale that asks
     a question and reads the answer from the terminal.
2. **The bale-level step is `office projects level-bale NAME`,** beside
   add and set: it acts on a project's host.
   - It builds a release-shaped tarball of the install the `bale` on
     this machine's PATH resolves into. One `bale/` directory, holding
     everything except `user/`, top-level dot-entries (`.git`, `.bale`)
     and caches.
   - It sends the tarball into a scratch directory on the host and runs
     the host's own `upgrade.sh -y TARBALL`. That is bale's documented
     upgrade path, so `user/` is kept by bale's own code, not the
     office's.
   - It then reads the version and the `user/` names again. A version
     that did not move, or a `user/` that lost a name, is an error, not
     a success.
   - A host with no bale on its login PATH (and no `~/bale`) gets the
     tarball unpacked in its home and `install.sh -y` run.
   - It refuses a host whose bale is newer, saying it never moves a bale
     back, and asks first on a terminal (`--yes` piped).
   - The script and flags are declared in `share/bale-consumption.toml`
     as a new non-call surface, `upgrade`.
   - One thing is not established: I read 0.4.51's `upgrade.sh`, not the
     host's 0.4.40 one. If 0.4.40's does not take `-y`, it exits 2
     ("unknown flag") before touching anything, and if it asked anyway
     its `/dev/tty` read fails and it exits 0 having changed nothing. In
     both cases the office reports the host's words, or "exited 0, but
     bale there says 0.4.40". The first real run is the test.
3. **`--from` moves the clone as a `git bundle` through the shell.**
   - The bundle holds every branch and tag, plus origin's
     remote-tracking refs, so `git status` there can say ahead or
     behind without fetching.
   - On the host it is `git init` (under a throwaway initial-branch
     name), then `git fetch --update-head-ok BUNDLE` into the same ref
     names.
   - The `remote.*` and `branch.*` config is copied verbatim and the
     symbolic remote HEADs are set by name. HEAD is set where the
     clone's is (a branch, or a detached commit), then `reset --hard`.
   - Every ref is checked against the clone's before it is prepared, and
     a clone that does not come out level is removed again.
   - The dirty-clone flag is `--from-dirty-ok`. On a terminal, the
     question defaults to no.
   - The local clone is read with `GIT_OPTIONAL_LOCKS=0`, so even its
     index is not refreshed.
   - A shallow clone is refused, since a bundle of it lacks history.
   - Remote URLs are copied as the clone has them, credentials included
     if a URL embeds any. The office never prints them.
4. **What start leaves on the host:** nothing outside the project's
   repo. The brief or bundle goes into one `mktemp -d
   "${TMPDIR:-/tmp}/office-XXXXXXXX"` directory, removed in a `finally`
   whether the session opened or not. A removal that fails is a warning
   naming the path, never silence. Inside the repo, bale's own pack
   leaves what it always does (the request in `.bale/outbox`, its
   registry), as it would for a local project. The office copies the
   request out; it does not delete bale's copy.
5. **What a bundle did differently from a pack:**
   - The bundle file travels to the host twice: once for `bale open
     --check`, in bundle-check's own scratch directory, removed at once;
     and again for `bale open` inside start. The check runs in its own
     process before anything is written, so the copy cannot be shared.
   - The found line bale prints names the host's copy. The office
     re-words it to the local path, adding "(sent to HOST for the
     check)".
   - A bare bundle name is refused for a hosted project, as a flagged
     deviation. bale's search for a bare name would run on the host,
     where the downloaded file is not, and the office cannot list this
     machine's search directories (`bale status --json` gives only
     their count). So the office asks for the path. If you would rather
     the office read the local global `bale.toml`'s
     `apply.search_paths` itself, that is a ruling against "never
     scrape"; I did not do it.
   - In 0.9.0's "where does the bundle open" question, a hosted project
     answers through its shell. A host that does not answer is a
     warning, and that place holds nothing for this question.

The rest:

6. **Checked once, before anything is written.**
   - bin/office calls a new `reader start-check` as soon as a hosted
     project is named (at `--on`, after the where question, and before
     a folder is opened for `new`). It makes one connection with
     `--version` and `status` in a batch (the reach check), holds the
     bale to the floor, and checks the repo.
   - bin/office then passes `--checked` to `reader start`, so the repo
     check is not repeated.
   - Each reader process still re-reaches the host, since the reach
     cache lives per process. A hosted start therefore makes about six
     connections: check, bundle check (send, check, remove), then the
     status and doctrine reads, the pack, the fetch and the scratch
     removal. At about 2.5 s each, a hosted start takes tens of seconds.
     Batching more is possible but would cost clarity; see Proposals.
7. **The doctrine on a hosted tree** is compared by sha256 through the
   shell (`doctrine_sums`), so office-src hosted somewhere would still
   ride its doctrine once.
8. **The request comes back with its sha256 checked.** `fetch_file`
   sends the far side's sum on stderr and the bytes on stdout, then
   hashes what arrived. A login shell that prints on stdout makes that
   a loud error naming both sums, which the suite proves with a host
   whose shell chatters. `send_file` checks the same way.
9. **`office status`** for a hosted bale says
   `office projects level-bale NAME brings it level with this machine's
   bale (X)`. It does so below the floor (replacing 0.14.0's sentence;
   0.14.0's test is updated) and, as a new line, when the host is within
   range but behind this machine.
10. **Land's refusal** now reads "the return trip is not built yet; the
    session is out and its response waits". It is one constant, used for
    a session and for a sitting.
11. **A small order change for local bundles:** `check_bundle` now finds
    the pack place before its own precheck, so a hosted host is reached
    and checked first. For a local project, the only visible effect is
    that a broken project directory is named before a missing bundle
    path when both are true.
12. **The wizard's new question** comes after the connect line and is
    asked only when a host was given. 0.14.0's wizard test is updated to
    answer it.

## The runner (item 5)

`run_job` now writes each failing test's traceback into the job's
result JSON. `summary()` prints it under the test's line, capped to its
last 40 lines (`TRACEBACK_LINES`), with a line saying how many were cut
and where the whole log is. It is the same idea 0.14.0's validation.sh
applied, done where the data already is, so it also holds when a log
under `/tmp` is gone. Its own tests drive it on a module that fails on
purpose.

## Things to know

- **A tour failure that came from how I ran the suite, not from this
  change.** Two of my full runs failed one test,
  `test_front_door.TestTourOnATerminal.test_an_interrupt_deletes_the_office_and_says_so`,
  with "still running after its last step": the tour ignored the Ctrl-C.
  I had started those runs in the background (`nohup ... &`), and a
  background job started from a non-interactive shell inherits SIGINT as
  ignored. A shell cannot trap a signal it inherits ignored, so the
  tour's INT trap never fired.
  - The test passes alone in the foreground, and its module's share of
    the serial lane passes too.
  - A full run with SIGINT put back to its default first was green
    throughout (589 tests).
  - bale's apply runs validation.sh in the foreground, so your run is
    not affected. The runner's summary printed the test's traceback
    itself, which is item 5 doing its job.
  - It is worth a line in the README's Tests section ("run the suite in
    the foreground; a background job ignores Ctrl-C and the tour's
    interrupt test fails"). I have not added it; see Proposals.
- **The workspace restarted once mid-session,** killing a test run. My
  context was not compacted: everything up to the restart is in this
  conversation, and the tree on disk was intact. The run was repeated
  and passed.
- **The test fakes for upgrade.sh and install.sh** follow 0.4.51's
  shape: `-y`, `user/` moved aside and restored, the release copied in,
  then `exec install.sh -y`. They are fakes. The first real
  `level-bale` is on your host.

## Proposals

- **What**: the return trip (W1c). `office land` over the shell: carry
  the response to the host into a scratch directory, run `bale apply` /
  `retry` there through `Reader.interact` (the attended form is built),
  carry the relay back from the capture, run the after-land actions
  there, and keep `place` in `land_plan`'s JSON as host, shell and
  connect instead of `repo`. **Why**: everything on the out side is in
  place; land is the half the brief left for the next session.
  **Scope**: `land_plan`, `land_main`, `run_after_land` in bin/office.
- **What**: a slip for bale-src: a `--json` surface (status's `config`,
  say) that lists the search directories, not just their count. **Why**:
  it would let a hosted start accept a bare bundle name by resolving it
  here; today the office has to ask for the path.
- **What**: a slip for bale-src: `bale --version` (or status) saying
  whether its install is a release install with `upgrade.sh`, and that
  script's flags. **Why**: `level-bale` relies on the host's `upgrade.sh`
  taking `-y`, which was read only on 0.4.51.
- **What**: fewer connections for a hosted start: carry the reach result
  across reader processes for one `office start` (an environment
  variable naming the host already checked), and fold the doctrine sums
  and the path checks into the status batch. **Why**: each connection
  costs a login shell, about 2.5 s on your host. **Scope**:
  `check_hosted_place`, `ohost._REACHED`.
- **What**: a line in the README's Tests section, and perhaps a check in
  `tests/runner.py` that warns when SIGINT is ignored (`signal.getsignal`
  is SIG_IGN), saying the terminal tests' interrupt checks will fail.
  **Why**: this session lost two full runs to it before finding the
  cause. **Scope**: `tests/runner.py` `main()`.
- **What**: `office init --project NAME=HOST:PATH` (0.14.0's seam,
  still open), now with `--from`. **Why**: a work office founded on a
  hosted project could then bring its clone in one step.

## Claims

`tests/run.sh` is claimed pass, observed: the whole suite ran green here,
side by side, with SIGINT at its default (589 tests, 898 s on this
two-core container). The earlier runs had the background-launch tour
failure above, and one had a text-rule failure I fixed (the consumption
manifest named the record directory). I also ran this response's own `validation.sh` end to end
in a staging copy built the way bale builds one (the request's tree, then
`files/`, then `apply.sh`, the manifest as `.bale-manifest.json`; no
`.git`): exit 0, 589 tests, both claims `[agree]`. It takes about 15
minutes here, well past TARBALL.md's two-minute target, as 0.14.0's
did: the whole suite is the check. The session assertions are claimed pass,
observed on the changed tree; all twenty of them fail on the unmodified
tree, checked.
