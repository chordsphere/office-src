# Notes: 2026-10-07-project-on-host-003, a project on a host (office-src 0.14.0)

The brief's seven items, built as one additive release. Nothing landed
outside the forecast (the forecast is the whole repo). The suite is
green here: 547 tests, the 42 new ones in `tests/test_project_on_host.py`,
side by side as 0.13.0 left it, with a fake `ssh` first on the PATH and
no network call anywhere.

Bottom line: a project may declare `host`, `shell` and `connect`; the
office reads it through that shell (every bale and git read, batched
per round), checks reach once per host and command, says in `office
status` which bale answers there against the floor, prepares a clone
for bale without a trace, and refuses to start or land on it until the
next release. Nothing from the brief's names is in the tool: the suite's
text rules pass, and the new test module invents its own hosts.

## The retry: the HOLD, what it was and what it wasn't

This is the second attempt (`corrects` the first). The first held on
one test, `test_second_trip.TestSurveyBeforeEveryPack.
test_an_open_session_holding_the_page_keeps_it_as_it_is`, listed as an
**error**, not a failure; the other 546 tests and every session
assertion passed. `files/` here is byte-identical to the first attempt.
Only `validation.sh` and these notes changed.

**Not the start changes, as far as the evidence reaches.**

- *The path.* The test sends two sessions out in the office (a worker
  forecasting `floor-plan`, then a read-only sitting) and checks that
  the second leaves the survey page alone under the one-writer rule. Of
  this session's diff, that path meets only plumbing:
  - `helper()` runs with `-B`;
  - `main()` exports `OFFICE_RERUN`;
  - `office_helper` imports `office_host`;
  - the digest's git calls go through `office_host.run_in` (same argv,
    directory and timeout);
  - `LandCase.setUp`'s `projects add` checks the path through `reader
    check-project`.

  The hosted-project branches (`start_check_place`, `ask_where`, the
  guards in `start()`) are never reached by a start in the office about
  a local project.
- *The timing.* I put a timer around `Env.run` and ran the test three
  times on each tree. Each start took 2.9 to 4.9 s on the unmodified
  tree and 3.3 to 6.2 s with the change; init, open and add were level.
  The timer is gone from what ships.
- *It never failed here*:
  - alone;
  - the class six times at once;
  - the test sixteen times at once on this two-core container (eight
    per core, slowest start 55 s);
  - with `R`, `quarto` and `node` on the PATH taking 7 s each, past the
    survey's 5 s per-tool timeout;
  - in three full runs, two before the HOLD and one for this attempt
    (547 tests, inside this `validation.sh`).

**What an error there can be.** The runner's `error:` is unittest's
errors list: an exception other than an assertion. In this test that
means:

- `Env.run`'s 120 s subprocess timeout. **Ruled out by your own
  timing**: the module took 149.6 s. Your machine ran the other modules
  at 0.52 to 0.66 of this container's times, which puts this one at
  about 110 to 125 s. That leaves about 25 to 40 s extra, not 120.
- `AttributeError` from the `Packed` regex. **Out**: the line is printed
  on the one path that exits 0.
- A decode error. **Out**: the survey's facts go through
  `errors="replace"` and are written as ASCII.
- A git lock held by a straggler. **Out**: nothing in the tool or the
  fakes runs in the background unless stdout is a terminal (only the out
  tray's opener does).
- A `CalledProcessError` from the test's own `git commit -qam` (it runs
  `check=True`), for a reason I can't produce. **Not ruled out.** That
  is all that's left, unless it's something I haven't thought of.

The extra 25 to 40 s fit the survey's per-tool `timeout 5` probes
running out under load. That is the one wall-clock bound in this path,
and the one step that touches your real `R`, `quarto` and `node`. But my
slow-tool run passes, so I can't tie that to an exception.

**So the cause is not established, and I didn't ship a fix for one.** A
wait added against a race I can't name would be a guess made to look
like a fix; a retry is ruled out. The log that names the exception was
in `/tmp/office-tests.vc7qegj6`. It was gone when you probed, along with
every other runner log on your machine: WSL empties `/tmp` on a
restart, and nothing in the suite deletes it.

**What I fixed is mine:** the first `validation.sh` printed only the
runner's summary, so the relay, which holds only what the script prints,
carried the test's name and not its exception. It now prints each
failing test's traceback from its job log, right after the summary
(checked against a stand-in runner that fails). If this recurs, the next
relay names the exception, and the fix can be aimed at it.

**Why the first claim disagreed with the verdict.** I claimed
`tests/run.sh` pass, observed, and it was observed: green on this
container. The verdict came from your machine, under bale's staging,
where one test raised an exception. An observation on one machine
predicts another's only as far as the suite behaves the same on both,
and this test didn't, in a way that doesn't show here. I keep the claim
at pass, observed: it held here in every run before and after the HOLD.
It is a prediction about your run, and I can't put a number on the
flake's rate.

## What the probes established

Two paste-back probes ran before any code; you pasted both back whole
(111 and 113 lines, the integrity counts matched). The first cut of the
first probe hung on your terminal; that was my bug, recorded below as
the first thing the build took from it. Read-only on both machines:
`true`, `echo`, `ls`, `find`, `--version`, `bale status --json`, `git
status`; bale's imports were told not to write bytecode.

- **The login.** Plain `ssh USER@HOST` in BatchMode works with the
  default identity search (no `-i`), about 400 ms a round trip; the key
  is `id_ed25519`, there is no `~/.ssh/config` and no agent. The login
  lands on the host, in the user's home there, which has its own
  `~/development` (two repos, none with bale) and no bale.
- **The container.** `docker exec -i NAME bash -lc '...'` works without a
  tty; `docker exec -it` refuses without one and works through `ssh
  -tt`; one quoted command through the full prefix round-trips intact.
  Plain `docker exec` enters as root (`HOME=/root`, no bale, no git
  identity, no `~/development`). The repos and bale belong to the
  occupant's own user inside the container, same name and uid as on the
  host, reached with `docker exec -i -u USER`: `HOME=/home/USER`, bale
  **0.4.40** at `~/.local/bin/bale` (the install at `~/bale`), on the
  PATH of a login shell, git 2.43, python3 3.12.3, git identity set.
  The repos sit in the container's own `/home` volume: ten under
  `~/projects`, six under `~/development`, each with `.bale/`. The host's
  `~/development` is a different directory.
- **Cost.** A round trip as that user is about 2.5 s (ssh 0.4 s; the
  rest is the login shell, presumably the user's profile); as root it
  was 0.44 s. This is what sized the connection count below.
- **The traces.** In the one repo I read, `claude/telemetry/*.json`
  shows in `git status` as untracked and `.gitignore` names bale once:
  exactly what `--prepare` prevents in a new clone. `bale status --json`
  there answers with `version 0.4.40` and the keys the office reads.
- **Not established**: whether 0.4.40 has `bale open` and `bale
  clipboard` (the help's head showed pack, apply, retry; my verb-list
  grep came back empty). It is below the floor anyway, and status says
  so; the next session cares.

## Decisions to ratify

The four the brief asks for, then the rest.

1. **The key names: `host`, `shell`, `connect`**, as the brief pins them,
   on the `[projects.NAME]` entry beside `path`, `rides` and
   `after_land`. `shell` and `connect` are written out at `add` (the
   defaults, so the floor plan says what runs), not left implicit.
2. **The reach timeout: 5 seconds.** `-o BatchMode=yes -o
   ConnectTimeout=5` go on every ssh call the office makes, not only
   the check, and a batch of reads is bounded at 60 s per command in
   it plus the connect allowance. The reach check is the **first
   connection a command makes through a prefix**: a batch that goes
   through counts as it (the host answered), one that comes back empty
   is the unreachable line. So an answering host costs no extra
   connection, and a down host costs one, 5 s. `office_host.reach()`
   still exists as the explicit `true` for a caller that wants one;
   nothing calls it in the tool today.
3. **How many connections a walk-in makes: two per hosted project**
   (status; then every open session's dossier in one batch). A ledger,
   landed or versions rendering makes two (aggregate and status; then
   every class aggregate and every dossier), `office status` one, the
   digest about five (status, git subjects, dossiers, the release's two
   git reads). The mechanism is a batch: `Reader.prefetch` sends
   several declared surfaces as one remote script whose per-call
   pipelines tag stdout and stderr lines and end each call with its
   exit code, and the reads that follow are cache hits. I did not use
   ControlMaster: it writes a socket, and the cost here is the login
   shell, not the handshake. At 2.5 s a connection, a walk-in is about
   5 s for your one hosted project. Local projects are unchanged: a
   prefetch on this machine does nothing, each read being cheap.
4. **`--prepare`'s mechanism**: four lines appended to
   `.git/info/exclude` (`.bale/`, `bale.toml`, `.baleignore`, bale's
   record directory), each once, under one header comment, and a
   comment-only `bale.toml` so `check_project_dir`'s "bale runs here"
   test passes and `bale config init` has a file to fill. I did not run
   bale's wizard (it needs a terminal and, through a shell, a tty: the
   next release's seam) and did not make `.bale/` (I don't know what
   bale makes of an empty one; `bale status` says it works in a
   not-yet-initialised repo, and pack initialises it). An empty TOML
   file is valid and bale's project layer then adds nothing over the
   global one. Idempotent, and a test proves `git status` clean, `git
   ls-files` unchanged, `.gitignore` byte-identical, and bale's files
   invisible once made.
5. **The default `shell` is `ssh HOST bash -lc`, not the brief's `ssh
   HOST`** (a flagged deviation). The office appends exactly one
   shell-quoted command; through ssh the far side's login shell parses
   the line again, so with a bare `ssh HOST` the quoted command arrives
   as one word and "command not found" is the answer. A prefix must end
   in the word that takes a command string (`bash -lc`, `sh -c`), and
   `check_shell` refuses one that does not, naming why. `-l` is also
   what puts `~/.local/bin` on the PATH on your host (the probe showed
   bale there only through a login shell). Your real prefix is `ssh
   HOST docker exec -i -u USER NAME bash -lc`, which the usage text
   gives as the container example.
6. **Quoting travels differently for a local prefix.** A prefix whose
   first word is not `ssh` (a `docker exec ... bash -lc` on this
   machine) gets the command as one argv word, unquoted, since nothing
   re-parses it. `Place.argv()` is the one place that decides.
7. **The unreachable line's shape**: `NAME: cannot read: HOST does not
   answer (ssh's last words); CONNECT; then rerun: office ...`. The
   reader prints it, bin/office exports the command as typed
   (`OFFICE_RERUN`, quoting only the words that need it). Every caller
   that already prefixes the project's name keeps doing so, which is why
   the line itself starts at the host.
8. **The walk-in and `office status` never die**: the line sits in the
   project's place. A rendering (`--ledger` and the rest) stops with
   the line and exit 3, as an unreadable project always did.
9. **`office status`'s host line** says `HOST answers; bale X there,
   within the read side's range`, or the brief's remedy sentence
   verbatim when it is behind, or the unreachable line. For your host
   today that is the remedy: 0.4.40 against 0.4.45. The survey is
   untouched and makes no network call (a test checks that).
10. **Start and land refuse at the earliest point**: `--on PROJECT`
    given, before any folder, survey or tray; in the where question, the
    hosted project is named and the question asked again; land refuses
    in the plan, before bale runs, for a session and for a sitting. The
    words are the same in bash and Python (`NOT_BUILT_ON_HOST`).
11. **`office init` no longer checks a path itself**: it hands each
    answer to `office projects add --path`, whose wizard asks where the
    repo is and checks there. A path given as a flag or a word that
    fails is not re-asked (add exits 1 and init says "that one was not
    added"); one the wizard asked is asked again. Three terminal tests
    changed for the new question.
12. **The listing (`office projects`) makes no connection**: a hosted
    project shows `on HOST; office status checks that it answers`, its
    shell and its connect line. Reach is checked where it matters.
13. **A new module, `lib/office_host.py`** (CODE.md §4.2: a separate
    subject with a small surface: Place, run_in, run_many, reach,
    check_project, prepare). The helper imports it for the key checks,
    so `helper()` in bin/office now runs with `-B` like the reader (the
    bytecode test caught it). office_bale's docstring still calls
    itself the only code that runs bale; office_host is its transport,
    and `Reader.invoke` is still the one door every bale call goes
    through.
14. **Prepare and check run from the shell's landing directory**, not
    the repo (`chdir=False`), since the path may not exist yet; every
    bale and git read runs in the repo's path.
15. **`project-facts` prints the host keys**; `set --shell` or
    `--connect` alone keeps the project's host; `--host` alone on a
    project already on another host resets shell and connect to the
    new host's defaults (they named the old one). `--on-this-machine`
    removes the three.

## What the first probe taught, kept in the tool

The hung probe: `timeout` puts its child in a background process group,
and an `ssh -tt` that touches the terminal there is stopped, not
killed. So every ssh call the office makes has stdin on `/dev/null`
(`subprocess.DEVNULL`, as the bale reads always had), and the one
attended path a tty needs is left for the next session, with `ssh -tt`
and `docker exec -it` noted as the form that works (the probe proved it
with stdin closed).

## Seams for the next session (start and land over the shell)

- `Reader.interact` refuses a hosted place today with the not-built
  line. The attended form is `ssh -tt HOST docker exec -it -u USER NAME
  bash -lc 'cd P && bale apply ...'` with the terminal as stdin; a
  `shell_tty` key, or deriving it (`-tt` after `ssh`, `-it` for `-i`),
  is the choice to make there. `Place.argv` is where it would go.
- `pack_place`, `bundle_precheck` and `start()` assume a local
  directory (they copy trees into the tray). A pack on a host means
  bale's pack there and the tarball carried back, or the tray built on
  the host; the context tarball the office makes rides the other way.
- `land_plan` keeps `place` out of the JSON plan; a hosted plan would
  carry the three keys instead of `repo`.
- `Reader.prefetch` could take git reads too; the digest's five
  connections would become three.
- `office projects add` through `office init` works for a hosted
  project (the wizard asks), but `init --project PATH` as a flag is
  local only (`project_spec` checks here); a `--project NAME=HOST:PATH`
  spelling is a small follow-up if you want hosted projects at init.

## Proposals

- **What**: a `shell_tty` key, or the derived `-tt`/`-it` form, with
  `Reader.interact` through it, as the first piece of the next session.
  **Why**: the probe showed the tty form works with stdin left open,
  and every attended bale step (apply's questions, open's) needs it.
  **Scope**: `office_host.Place`, `Reader.interact`, `land_main`.
- **What**: ask bale-src for `bale --version` and `bale status --json`
  to be the same call, or for status to carry the verbs a bale has.
  **Why**: `office status` makes one connection per host for the
  version and the next session will want to know whether `open` and
  `clipboard` exist there before sending a bundle.
- **What**: a slip for bale-src: `bale status --json` in a prepared
  clone (comment-only `bale.toml`, no `.bale/`) as a documented state.
  **Why**: the office now creates it on purpose; a bale that refuses an
  empty project layer would break `--prepare`'s promise. I checked
  TOML validity, not bale's reading of it.

- **What**: have `tests/run.sh` print each failing test's traceback in
  its own summary, as this session's `validation.sh` now does after it.
  **Why**: the summary names a failing test and points at a log under
  the temp directory, and this session's HOLD showed that log can be
  gone by the time anyone reads it; validation now copes, but a person
  running the suite by hand doesn't. **Scope**: `tests/runner.py`'s
  `summary()`, which already holds each job's log path; a cap per test.

## Where to look at review

- `lib/office_host.py`: `_call_block` (the stream-tagging pipeline the
  batch is built on; POSIX sh, no PIPESTATUS) and `_split_calls`.
- `bin/office` `cmd_projects_add`: the wizard's loop with `path_given`.
- `lib/office_helper.py` `read_projects`: a hosted entry is never
  resolved on this machine; `resolved` is None and the renderings
  that touch `resolved` were checked (`bundle_places`, `install_behind`
  skip it by `problem`/`resolved` tests; a hosted project cannot be the
  install's source).
- `tests/test_project_on_host.py`'s `FAKE_SSH`: it asserts the target
  and prefix from `expect.json`, fails the `down` target with ssh's own
  words, and gives an `OLD` target its own bale (0.4.40) for the floor
  line.

## Claims

`tests/run.sh` is claimed pass, observed: the whole suite ran green here
side by side, in three full runs (the terminal lane took the longest, as
before). The first attempt's same claim disagreed with your verdict; the
retry section above says why, and why it stays pass. The session
assertions are claimed pass, observed on the changed tree; on the
unmodified tree they fail (no 0.14.0, no module, the old doctrine
sentence).
