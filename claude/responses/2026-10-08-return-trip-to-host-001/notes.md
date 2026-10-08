# Notes: 2026-10-08-return-trip-to-host-001, the return trip from a host (office-src 0.16.0)

## This is the corrected response (corrects the held first attempt)

Your HOLD was right, and the fault was the test's, not the tool's.
`tests/run.sh` was claimed pass, observed, and the verdict on your
machine was fail. The claim was honest for the machine it was observed
on and wrong about yours, for this reason:

- The terminal test
  `TestLandOnAHostOnATerminal.test_the_downloads_are_asked_once_...`
  answered the downloads question with "1".
- The question's candidate list scans `/mnt/c/Users/*/Downloads` on the
  real machine.
- My container has no `/mnt/c`, so its list had one line, the test's own
  `HOME/Downloads`, and "1" meant that directory.
- Your WSL machine has `/mnt/c/Users/chord/Downloads`, which listed
  first. So "1" took your real Downloads, where the test's response is
  not, and land refused.

The test depended on what directories the running machine holds, and
the tool gave the suite no way to stop that. I had observed the pass on
a machine that could not show the fault.

The fix, as you asked:

- **The scan is steerable.** `download_candidates` takes its Windows
  users' root from `OFFICE_WINDOWS_USERS`. Empty means none, unset means
  `/mnt/c/Users` as before, and an explicit argument still wins. It is
  the only directory the scan reads outside HOME. The XDG directory and
  `~/Downloads` already come from the test's own HOME and
  XDG_CONFIG_HOME.
- **The suite points it away everywhere.** The shared `Env`
  (`tests/test_office.py`) sets `OFFICE_WINDOWS_USERS=""`, so no office
  command any test runs reads the machine's Windows homes. A test holds
  `Env` to that, and a new session assertion checks both halves. This
  adds `tests/test_office.py` to the change set. It is inside the
  forecast.
- **The terminal test answers by path.** It gives the scan a Windows
  home of its own and checks that the list shows exactly that home and
  `HOME/Downloads`. The unit test covers the variable: set, empty and
  unset.
- **The failure is reproduced here first.** I made
  `/mnt/c/Users/someone-real/Downloads` in this container, the same
  shape as your machine. With that directory present, the shipped test
  failed the way your HOLD did. The corrected one passes.
- **The whole suite was rerun with the fake Windows home in place**, so
  the claim is observed on a machine that can show the fault. Both runs
  are in Claims below.

Nothing else in the release changed. One line each was added to README
(Tests) and RELEASES (0.16.0) naming the variable.

All six of the brief's items are built, as one additive release. Every
path I changed is inside the forecast, which is the whole repo. The
suite is green here: 621 tests, run side by side, 32 of them in the new
module `tests/test_return_trip.py`. No test makes a network call or runs
a real ssh, rsync or docker. The fake host in the new tests keeps its own
HOME, its own PATH (the fake bale and the system's tools, nothing else of
this machine's) and its own TMPDIR. Because of that, the tests can see
two things directly: an after-land action running in the repo there with
the host's HOME, and nothing the office made left in the host's
temporary directory.

In short:

- `office land` on a hosted project works the way it does for a local
  one.
- `downloads` in machine.toml is asked once, on a terminal.
- Land offers to close a finished folder.
- One `office start` or `office land` reaches a host once.
- A hosted start went from 7 connections to 4 in the suite's count.
- README now says to run the suite in the foreground, and the runner
  warns when SIGINT is ignored.

## No probe

`expects_probe` was agent-decides, and I decided against a probe, for
three reasons:

- The brief's likely questions were `bale apply`, `retry` and `unlock
  --help` on the host's 0.4.51. The `BALE_HELP.md` in the request is the
  packing bale's own, and that bale is also 0.4.51. The host's install
  is this machine's, copied there by `level-bale`, so the help could not
  differ.
- The work office's projects table is in the shape 0.15.0 writes, and I
  could read that shape from the code.
- Nothing I built depends on facts about the work host that the 0.14.0
  and 0.15.0 probes did not already establish.

So the first real `office land` on a work project is the test of
everything below. Have the VPN up when you run it. If it misbehaves,
`OFFICE_DEBUG=1 office land SID` shows every connection.

## To ratify (the brief's four, first)

1. **The `downloads` key and its first-time question.**
   - The key is `downloads = ["...", ...]`, a list of directories, in
     `~/.config/office-src/machine.toml`. It sits beside `out_tray`,
     `clipboard_command` and `open_command`.
   - The office writes it as a top-level key ahead of any table. Every
     other line in the file is left alone, and the file is read back as
     TOML before the write counts.
   - It is never written over. To change it, edit the file.
   - The question is asked the first time a verb needs it on a
     terminal: a hosted land that was given no path, or a hosted start
     given a bare bundle name. It opens with "Where do downloads land on
     this machine? WHY; this is asked once and kept as downloads in
     FILE". It then lists this machine's likely directories, numbered:
     each Windows user's `Downloads` under `/mnt/c/Users` (Public and
     Default skipped), the XDG download directory, and `~/Downloads`,
     those that exist.
   - The answer is numbers or paths, comma-separated, and the default is
     `1`. On your machine `1` should be `/mnt/c/Users/chord/Downloads`.
   - `?` explains the setting. Piped, the verb refuses and names the key
     with an example.
   - The office never reads bale's config. A test checks that neither
     `bin/office` nor `lib/` mentions `search_paths` or bale's
     `user/bale.toml`.
2. **Newest wins.**
   - The candidates for a name are `NAME.EXT` and `NAME (N).EXT`, where
     `.tar.gz` counts as one extension. They are collected from every
     downloads directory, and the newest by modification time wins.
   - Land names the file it took and the copies it left
     ("2 copies of response-SID.tar.gz are in the downloads; took the
     newest, PATH (left: ...)").
   - Two copies saved at the same moment refuse, naming both. The office
     will not guess.
   - Land's precedence: a path given wins. A bare name given is looked
     for in the current directory and then the downloads, in bale's own
     search order, and that exact name is taken.
   - A **local** land passes bale the newest by its path only when
     there are several copies. Otherwise it gives bale the plain name,
     as before.
   - One deviation, flagged: **after a HOLD with only one copy in the
     downloads, land does not retry that copy.** It asks for the
     corrected response and offers that copy as the default. Piped, it
     refuses and names that copy. The one copy is usually the held
     response itself, and retrying it would just hold again.
3. **The close offer's default is close.**
   - The offer comes right after the ratification question. The folder
     must record exactly one session, the one that landed, and that
     session must carry a `ratified` line with no `except`.
   - On a terminal the question reads "close the folder, done, or leave
     it open (--close, --leave-open) [close]".
   - Piped, the folder stays open and land says so, naming `--close`
     and `office close NAME`.
   - `--close` on a folder that does not qualify says why and leaves the
     folder open. It does not fail the landing.
   - The founding folder keeps its own rule (`close_founding_folder`),
     and the offer is not made for it.
   - Closing goes through `cmd_close` with the History text "office
     land: SID landed and was ratified, the folder's only session". It
     shows up among land's last lines, the way the founding folder's
     close does.
   - Local and hosted alike. Office sessions too, since their folders
     are desk folders like any other.
4. **Connection counts.** These are the fake ssh's call log, from the
   same scenario run against the request's tree and against this one.
   I left the scripts out of the response; ask if you want them.

   | command (hosted project)               | 0.15.0 | 0.16.0 |
   |----------------------------------------|-------:|-------:|
   | `office start`, a pack                 |      7 |      4 |
   | `office start`, a pack with `--brief`  |     10 |      5 |
   | `office start`, a bundle               |     18 |      8 |
   | `office land`, applied                 |      — |      4 + 1 per after-land action |

   No connection in either column is a bare `true`. A pack's four are:
   - start-check: version, status and the repo's check;
   - the pack's reads: status, the forecast's paths and the doctrine's
     sums;
   - the pack itself, with the brief's scratch removed in the same
     connection;
   - the request carried back.

   With a brief there is one more, the send, and the scratch is made in
   that same connection.

   A land's four are:
   - the plan: status and dossier;
   - the response sent into a new scratch;
   - bale apply, with the scratch's removal after it in the same
     command;
   - the outcome: the dossier, plus `bale relay` when bale exited 0.

   **The first hosted land on a machine makes one more**: it reads the
   plan again after the downloads question.

   A bundle start is still 8, because the bundle travels twice. 0.15.0's
   notes explain why: the check runs in its own process before anything
   is written. Sharing the copy is in `deferred`.

## The rest, decided and flagged

- **The plan's shape.** `land_plan` carries `place` (`path`, `host`,
  `shell`, `connect`, `name`) instead of `repo` for a hosted project. It
  also carries a display `where` ("PATH on HOST") for land's log lines
  and the "After land, in ..." header. A local plan keeps `repo` and
  gains the same `where`. Other new keys: `needs_downloads`,
  `response_default` and `took` (the lines land says about what it
  took). `plan_field` now reads a missing key as empty; it used to raise
  a traceback.
- **The reach file.**
  - `main` makes one `mktemp` file per office command and exports it as
    `OFFICE_REACHED_FILE`. Nested office calls inherit it, since they
    are part of the same command. The file is removed with the command's
    other temporary paths.
  - A reader process appends each shell prefix that answered, and the
    next process reads the file before its first connection. A host that
    did not answer is never written down: the command stops there anyway.
  - When a carried reach goes stale (the VPN dropped between steps), ssh
    exits 255 with nothing on stdout. That now raises the reach's own
    line, with the connect text and the rerun line, rather than "refused".
  - One cost: a SIGKILLed office leaves that empty file in the temp
    directory. Making the file on demand would have meant a predictable
    name in /tmp, and I preferred `mktemp`.
- **After-land actions on a host.**
  - Each action is its own connection (`reader land-after --index N`),
    run as `cd PATH && bash -c CMD` with its output on your screen.
  - On a terminal they run in the attended form (`-tt`, `-it`), so an
    action that asks reaches you. Piped, stdin is closed.
  - A failing action prints the one line that reruns it and the rest
    from this machine. The line is built from the stored shell, quoted
    once more for ssh's far side.
  - I did not batch the actions into one connection. Separate
    connections keep land's per-action report honest, and at the moment
    most work projects declare none.
- **A clarification on a hosted project.** The planner's block comes
  from `bale relay SID` run there, in the same connection as the
  dossier. The Next line is something you type here, `ssh HOST ... 'cd
  PATH && bale relay SID -' < ANSWER-FILE`: bale relay reads `-` from
  stdin, so the answer file never has to travel. The brief did not ask
  for an office verb that carries the answer back; see Proposals.
- **A sitting there.** `office land SID` runs `bale unlock` through the
  shell, and needs no downloads.
- **A host that does not answer**, when land is given a sid or a folder.
  Land reads every repo the office scopes to find the session. When it
  cannot find the session and some host did not answer, it says "...;
  and far's host did not answer, so it may be out there: HOST does not
  answer (...); CONNECT; then rerun: office land SID", followed by
  "nothing was carried and nothing ran". Exactly one connection is made
  (the test checks it). For a bare `office land` (no sid), the
  unreachable host shows as a warning above "no session is out".
- **A home-relative hosted path (`~/x`) never worked through the
  shell.** This is outside the brief, but land needed it, so I fixed it
  and flag it here. `office projects add` accepts `~/x` for a host, but
  every `cd` quoted it as `'~/x'`, which names a directory called `~`.
  Your work projects use absolute paths, which is why `office status`
  answered. 0.15.0's README example uses `--path ~/development/NAME`,
  and that would have failed. Now:
  - `shell_path()` writes `"$HOME"/x` wherever the office `cd`s on the
    far side: the read batches, `interact`, and the after-land runs.
  - The check, prepare, clone, exists and clone-cleanup scripts expand
    a leading `~` themselves.
  - A test drives a read, the check, the exists check and prepare
    through the fake host's HOME.
- **Three of 0.14.0's and 0.15.0's tests are rewritten to the new
  truth.** These are the only edits to older tests:
  - `test_project_on_host`'s land refusal now checks that a piped land
    needs the downloads and names the key.
  - `test_out_trip_to_host`'s land-waits test is gone. Its ground is
    covered by `test_return_trip`.
  - Its bare-name refusal now checks the piped refusal that names the
    key.

  Its record test pinned `VERSION == "0.15.0"`. It now holds VERSION at
  or above 0.15.0, the way 0.14.0's test already does.
- **`check_hosted_place(checked=True)` makes no connection.** It used to
  re-read the version and status. Start-check already held the floor
  this command, and the status now arrives with the pack's own reads.
  Without `checked`, the check runs the version, the status and the
  repo's check in one batch. One side effect: a hosted path that does
  not exist now reads "far: no such directory on HOST: PATH; nothing was
  written", where 0.15.0 said "far cannot be packed: no such directory
  ...". No test pinned the old words.
- **The runner's warning** names the interrupt tests in
  `runner.INTERRUPT_TESTS`, currently the tour's Ctrl-C test. A test
  imports each named test, so a rename fails loudly. The warning prints
  before any run except `--plan`.

## Things to know

- **`tests/run.sh` now warns whenever SIGINT is ignored**, which in
  practice means a background run. I ran the suite here with SIGINT
  restored to its default (`signal.signal` before `exec`), as 0.15.0's
  notes describe. My response's `validation.sh` does the same around the
  suite, so how bale starts it cannot cost the tour's interrupt test.
- **The 0.15.0 suite, unchanged, was green here first.** The request's
  tree passed 589 of 589 before I changed anything.

## Proposals

- **What**: `office relay SID ANSWER-FILE`. It would carry a planner's
  answer to a clarification back to the session's repo: run `bale relay`
  there for a local project, and pipe the file through the shell for a
  hosted one. It would also find the answer in the downloads by name.
  **Why**: a clarification on a hosted project now ends with a line you
  have to type, and that is the only step of the hosted loop the office
  does not do for you. **Scope**: `bin/office` (a verb),
  `office_bale.land_main`'s relay half.
- **What**: share one host copy of a bundle between `bale open --check`
  and `bale open`. bin/office would own the scratch for the whole start
  and pass its path to both reader steps, removing it in its EXIT trap.
  **Why**: it is the last double trip in a hosted start, 2 of the 8
  connections. **Scope**: `check_start_bundle`, `office_bale.start`,
  `check_bundle`.
- **What**: a slip for bale-src, still standing from 0.15.0: a `--json`
  surface that lists apply's search directories. **Why**: the downloads
  key duplicates something bale already knows, and the office only asks
  for it because bale will not say. With that surface, the question
  could offer bale's own directories first.

## Claims

- **`tests/run.sh`: pass, observed, this time on a machine that can show
  the fault.** I ran this response's own `validation.sh` in a fresh
  staging copy built the way bale builds one: the request's tree, then
  `files/` with `bin/office`'s exec bit stripped, then `apply.sh`, with
  the manifest as `.bale-manifest.json` and no `.git`.
  - The container had `/mnt/c/Users/someone-real/Downloads` in place
    for the run.
  - It exited 0: 621 tests in 953 s, side by side, and both claims came
    back `[agree]`.
  - I started it from a background job with SIGINT ignored, and the
    script's own restore kept the tour's interrupt test passing.
- **The held attempt's claim**, for the record: 620 tests in 919 s and
  936 s, both run here before `/mnt/c` existed. That is why it read pass
  here and failed on your machine (see the top of these notes).
- **The session assertions: pass, observed.** All fifteen pass on the
  changed tree. Fourteen of them fail on the request's unmodified tree,
  with `validation.sh --quick`. The fifteenth is the brief-names guard,
  which holds on both trees by design and says so in its comment. The
  new assertion is the downloads root's steerability and the suite's
  `Env` setting.
- The whole script takes about 16 minutes because of the suite, well
  past TARBALL.md's two-minute target, as 0.14.0's and 0.15.0's did.
  `validation.sh --quick` skips the suite and says so.
