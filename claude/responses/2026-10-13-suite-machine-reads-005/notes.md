# Notes: 2026-10-13-suite-machine-reads-005 (office-src 0.20.1)

The suite no longer touches the machine it runs on. The office's two
desktop reads, whether the machine is WSL and where its desktop programs
are, each come from one place the environment can steer. The suite's Env
and the runner set both for every test. The `office probe` terminal test
that failed only on your machine keeps its exact assertion and gets its
reader from the Env. `tests/test_suite_clock.py`'s rule names both reads,
in the test files and in the office's own source. New terminal tests
imitate your machine and prove that nothing of Windows runs. VERSION is
0.20.1. The suite went from 783 tests to 795. Run results are near the
end, above the two pages.

The pre-flight check said it fits, with room to spare. No probe and no
light block: your probe's 151 lines and the tree answered everything.
Every changed path is inside the forecast.

## What I checked for you: did the suite reach explorer.exe?

Yes. The brief asked me to check, and the code says the same two
terminal starts that wrote your clipboard also ran `explorer.exe .` in
their out trays. Those are `TestStartOnATerminal`'s two tests: folder 1
(`fix-login`, "Fix the login redirect") through the wizard, and `new`
with goal "g" (`write-the-plan`). `start_desktop` computes the default
the same way for both programs.

Why you saw no window: most likely the test's terminal hung up first.
`on_a_terminal` runs the command as the session leader of its own
pseudo-terminal. When the office exits a moment after starting explorer
in the background, the hangup reaches the background process before it
has run. I measured this in the sandbox: of 10 background launches on a
pty whose leader exited at once, 0 ran, and `nohup` and `setsid` did not
help. With half a second's grace, 3 of 3 ran. I can't confirm it on your
machine. In your own use your shell is the session leader and outlives
`office start`, so the Explorer step is unaffected there. Your clipboard
was written because `clip.exe` runs in the foreground, before the
office exits.

## Decisions to ratify

1. **The mechanism: two environment variables, read in one place each.**
   - `OFFICE_PROC_VERSION` names the file the WSL check reads; the
     kernel's own when unset, and `""` means not WSL. bin/office's
     `on_wsl` and the helper's new `machine_is_wsl` read it. The
     survey's machine class now asks `on_wsl` too: it was the second
     place reading the kernel's file (`bin/office:225`).
   - `OFFICE_DESKTOP_PATH` lists the directories searched for a desktop
     program. PATH is used when it is unset, and `""` finds none.
     bin/office's new `desktop_tool` (for `clip.exe` and `explorer.exe`)
     and the helper's new `desktop_which` (for the paste command's
     candidate) read it.

   Unset, the office behaves exactly as before on your machine. I chose
   this over the brief's other options:
   - **Env writing machine.toml:** it collides with tests that assert
     what machine.toml holds, or that it does not exist
     (test_return_trip, test_probe). It also does nothing for the paste
     candidate, which is offered precisely when machine.toml has no
     `paste_command`.
   - **The runner stripping Windows mounts from PATH:** it covers only
     WSL. It leaves the WSL check itself reading the machine. It does
     nothing for a Linux machine whose `xclip` would be offered.

   These variables are the downloads scan's pattern
   (`OFFICE_WINDOWS_USERS`) applied twice.
2. **A program found is the program run.** `desktop_tool` prints the
   path it found, and that path is what runs. So when the variable
   points somewhere, nothing else on the PATH can stand in. One visible
   change follows: the log now names the program by its path, for
   example "the opener is on the clipboard (/mnt/c/WINDOWS/system32/clip.exe)"
   where it used to say "(clip.exe)". The paste candidate keeps its bare
   names (`powershell.exe -NoProfile ...`, `wl-paste --no-newline`),
   since that line is kept in machine.toml for you to read and edit, and
   the test pins it.
3. **Every Env has a desktop: `self.e.desktop`, empty, first on its
   PATH.** It is the only place the office looks for a desktop program,
   so a test that needs one puts a fake there and that fake is what runs.
   The probe test now writes its fake `wl-paste` there instead of making
   a PATH of its own. Its assertion line,
   `(b"(paste_command in machine.toml) [wl-paste --no-newline]:", "?")`,
   is byte for byte as it was, and validation.sh checks that.
4. **The runner's declared tools:** `runner.DECLARED_TOOLS` is git,
   python3, bash and the coreutils, as the brief lists them, plus two
   more, flagged:
   - `sh`, which is a shell;
   - `iconv`, which `to_clipboard` looks up to feed `clip.exe` UTF-16.

   I kept iconv's lookup rather than replacing it with python3. Your
   clipboard showed that path works, and changing a working path on
   your machine was not the ask.
5. **The source rule, and what it still allows.**
   - The rule reads every `command -v`, `type -P`, `require_tools` and
     `shutil.which` in bin/office and lib/. Each name must be declared,
     be the suite's fake bale (`FAKED`), or go through the desktop door.
     Putting the old `command -v clip.exe` line back fails it, naming
     the line.
   - Three lookups by a variable or of the office itself stay, each in
     `SOURCE_ALLOWED` with its reason: `require_tools`' own loop (its
     callers' names are each checked), and the survey's Tools facts and
     `office-src on_path` fact.
   - The survey's facts are still reads of the machine. Recording what a
     machine holds is the survey's whole purpose, and no test asserts
     their values. I proposed steering them below rather than widening
     this session.
6. **The imitated-WSL start tests run under a stand-in for your shell.**
   It is a five-line script that runs the command and then waits up to
   three seconds for a started program to report. Without it, the
   control test (pointed at the fakes) can't see `explorer.exe` run,
   which is the hangup above. With it, both directions are honest: under
   the Env nothing runs, and pointed at the fakes, `clip.exe` gets the
   opener as UTF-16, line for line, and `explorer.exe .` runs in the out
   tray.
7. **VERSION 0.20.1:** additive, no migration, no new flag or question.
   The only change you can see is that path, in the clipboard and
   Explorer log lines.

## Proof that the tests test the change

I made two mutations on a scratch copy, with the WSL check still
steerable so the imitation could run:
- **The old `command -v` lookups put back:**
  `TestStartOnAnImitatedWsl.test_under_the_suites_env_...` fails, listing
  exactly what happened to you: `clip.exe` run in the office, and
  `explorer.exe .` in `out-tray/2026-10-13-fix-login-001`.
- **The paste candidate searching the plain PATH:**
  `TestProbeOnATerminal.test_on_an_imitated_wsl_the_envs_reader_...`
  fails. The screen shows your run.log's line word for word: `... (paste_command
  in machine.toml) [powershell.exe -NoProfile -Command "[Console]::OutputEncoding
  = [Text.Encoding]::UTF8; Get-Clipboard"]:`.

validation.sh's six session assertions fail on the request's tree and
pass on this one (the run results below show both).

## Paths outside the forecast

None. Every changed path is under the request's `resolved_scope`.

## Something the request did not carry

Two paths the suite reads were not in the request. Both are outside the
forecast, so I put local stand-ins in place for my runs only. Neither is
in this response.
- **`.gitignore`:** the last session hit the same gap.
  `test_office.TestText` reads it.
- **`migrations/`:** `test_office.TestInstall` runs `git archive` over
  install.sh's shipped paths. Without the directory, the baseline fast
  tier failed that one test in the sandbox.

## Tests

- **New: 12 tests.**
  - test_suite_clock, 7, in the fast tier with the rest of the module:
    - the door units, bash and Python alike: the WSL check reads only
      the named file; a desktop program is found only where the door
      looks; the paste candidate takes both reads from the environment,
      including the helper CLI `office probe` calls;
    - the source rule, with its own catch-each-way test;
    - the Env and runner assertions extended.
  - test_start, 2, terminal, behind `--slow`: `office start` on an
    imitated WSL machine, under the Env and pointed at the fakes.
  - test_probe, 2, terminal, behind `--slow`: `office probe`'s paste
    question on an imitated WSL machine, the same two ways. The second
    is the first end-to-end test of the WSL paste path: the PowerShell
    line offered, the fake `powershell.exe` read, and the block handed
    back to `clip.exe` as UTF-16.
  - test_office, 1, behind `--slow`: the survey's machine class from
    the steerable file.
- **Changed:** the probe test, as decision 3 describes, and three
  `test_suite_clock` tests: the two that pin Env and the runner's job
  environment, and the rule's catch-each-way test, which gains the new
  patterns' lines.
- **The rule for test files** gains two patterns: the kernel's version
  file, and a program looked up on the PATH (`shutil.which(`,
  `command -v`, `type -P`). No existing test file trips them.
- **The fast tier's new cost is 0.7 s in all**, the seven
  test_suite_clock tests.

## Run results (worker's sandbox, two cores)

| run | tests | result | wall clock |
|---|---|---|---|
| fast tier, the request's tree | 325 | every test OK; over the budget in this sandbox | 139.3 s |
| fast tier, the changed tree | 332 | every test OK; over the budget in this sandbox | 144.3 s |
| validation.sh, a staging copy (the request's tree plus files/ and apply.sh) | its checks plus the fast tier | the 8 checks PASS; the tier's 332 tests OK but over the budget, so `[FAIL]` and a `[DISAGREE]` on that line | 2 min 18 s in all; the tier 136.6 s |
| validation.sh on the request's tree | its checks plus the fast tier | the six session assertions FAIL, as they should; the tier's 325 tests OK, 142.2 s | |
| the whole suite, the changed tree (`tests/run.sh --detach`) | 795 | 794 pass; 1 fails (below) | 2,225 s (37 min) |
| the six new and changed slow tests again, on the final bytes (the detached run copied the tree before a last round of comment and docstring edits) | 6 | OK | 72 s |

**Reading the timings.** This sandbox is slower than the last session's.
That worker measured the request's 325 tier tests at 109.7 s, and here
the same tree took 139.3 to 142.2 s. So the budget line fails here for
any tree, and I claim it `pass` on a prediction, not an observation.
The difference this change makes is its seven tier tests, 0.7 s in all.
The rest of the gap between my two runs (144.3 s against 136.6 s for the
same tree) is noise between parallel jobs. At 0.19.0 your machine ran
313 tier tests in about 90 s, so expect under 100 s.

**The one failure in the whole suite** is
`test_office.TestUpgrade.test_the_real_0_2_0_migration_gives_an_old_office_its_include_group`.
It runs the real 0.2.0 migration from `migrations/`, which the request
did not carry; my stand-in holds only a README. It fails the same way on
the request's tree. On your machine the directory is whole.

**The serial lane** passed all 85 tests, the four new ones among them,
in 1,198 s. The four new terminal tests took 89.6 s of that.

## Outcome 4, the hand test

I can't run on your machine, so the verdict there is the hand test,
after `./install.sh`. The detached run that `office land` starts after
this landing (or `tests/run.sh --detach`) should read
`OK ...: 795 tests passed in ...` in
`cat ~/.local/state/office-src/suite/latest/verdict`, and the walk-in
should show no `Suite:` line. Your clipboard should be untouched by it:
copy something before it starts and paste it after it ends.

## Proposals

- **What:** steer the survey's remaining machine reads in tests: its
  Tools facts (`bale`, `R`, `quarto`, `node` and the `office` on PATH)
  and the container marker (`/.dockerenv`).
  **Why:** they are the last places a test of the command reads the
  machine. No test asserts what they find, which is why I left them, by
  name and with reasons, in `SOURCE_ALLOWED`. On a machine with a slow
  `R --version`, every `office init` in the suite still waits for it.
  **Scope hints:** `gather_facts` and `tool_version` in bin/office. One
  more variable in the Env's pattern (a tools directory) would do it.
- **What:** the serial lane's cost of the four new terminal tests.
  **Why:** they took 89.6 s of this sandbox's 1,198 s serial lane, so
  roughly a minute on your machine, added to the lane that is already
  the floor of every whole run. Most of it is their setUp (an office, a
  project and a pack, and for the probe tests a session out). The
  ordering work the brief queued after the wave would absorb this, and I
  did not touch it (out of scope). **Scope hints:** the two imitation
  pairs could share one setUp each if the lane's cost matters more than
  each test standing alone.

## Walkthrough

### What changed

- **The office's two desktop reads come from one steerable place each**
  (bin/office `on_wsl`, `desktop_tool`; lib/office_helper.py
  `machine_is_wsl`, `desktop_which`, `paste_candidate`).
  - Whether the machine is WSL: the kernel's version string, read from
    the file `OFFICE_PROC_VERSION` names, else the kernel's own; `""`
    means no.
  - Where its desktop programs are: the directories
    `OFFICE_DESKTOP_PATH` lists, else the PATH; `""` means none.
  - `office start`'s clipboard and Explorer defaults, every other
    clipboard copy, the survey's machine class and `office probe`'s
    paste candidate all ask these two.
- **The suite sets both for every test** (tests/test_office.py `Env`,
  tests/runner.py `isolated_env`). The machine is never WSL to a test
  unless the test imitates it. Each test has an empty desktop directory
  of its own, first on its PATH.
- **The `office probe` terminal test** puts its fake `wl-paste` in that
  desktop. Its assertion is unchanged.
- **New terminal tests imitate a WSL machine.** They write a WSL kernel
  version file and put fake `clip.exe`, `explorer.exe` and
  `powershell.exe` first on the PATH.
- **tests/test_suite_clock.py's rule** names the kernel's version and PATH
  lookups, in test files and in the office's source.
  `runner.DECLARED_TOOLS` lists what a job may take from the machine's
  PATH.
- **The record:** README (the desktop steps and the Tests section),
  RELEASES 0.20.1, the front sheet, and VERSION.

### Why

The detached suite that runs after every landing put two session
openers on your clipboard, and failed one test on your machine only.
Both had one cause: tests of the office read what the office reads, and
the office read the machine directly. A test suite that touches your
desktop, or passes in the sandbox and fails at home, can't be trusted
in the background. Now it can't see your machine through either door.

### How to explain each piece

- **The two variables** are knobs for the test suite. Nobody sets them
  in everyday use, and with neither set the office does what it did.
- **`desktop_tool`** answers "where is clip.exe?" from one list of
  directories. It returns the path, and that path is what runs.
- **Env's desktop** is each test's own little "Windows": empty unless
  the test puts a fake there.
- **The rule** is a tripwire for the next session. A new `command -v
  something.exe` in the office fails the suite with the line named.

### Questions a reviewer will ask

- *Does anything change on my machine?* One thing: the clipboard and
  Explorer log lines (start, probe, land's relay, deliver's review URL)
  name the program by its path. Nothing else changes.
- *Could a test still write my clipboard?* Only one that sets
  `OFFICE_DESKTOP_PATH` to a real Windows directory itself. The tests
  that point it anywhere point it at fakes in their own tree, and the
  rule refuses a test file that looks a program up on the PATH.
- *Why does the probe test pass now on WSL?* It is offered the reader
  in its Env's desktop. Your `powershell.exe` is on the PATH, and the
  office no longer looks for desktop programs there during tests.
- *What still reads the machine?* The survey's tool versions and its
  container check. Recording what a machine has is the survey's purpose,
  and no test asserts what they find. They are named in the rule's
  allowances, with a proposal to steer them.

### A hand test

1. In ~/office-src, after this lands, `./install.sh`. Then copy a line
   of your own to the Windows clipboard.
2. `tests/run.sh --detach`, or let `office land`'s after-land action
   start it. It prints one line naming the verdict file.
3. While it runs, and after it ends (about 16 minutes on your machine),
   paste: your own line should still be there. No Explorer window should
   open.
4. `cat ~/.local/state/office-src/suite/latest/verdict`. It shows
   `OK <time>: 795 tests passed in <N>s, <commit>`.
5. Walk in (`office` in an office that scopes office-src). It shows no
   `Suite:` line.

## Delivery

- to: nobody: office-src has no audience

### Commit

Keep the test suite off the machine it runs on

On WSL the suite's terminal tests of office start put session openers
on the real clipboard through clip.exe, and started explorer.exe; and
the terminal test of office probe's paste question failed there alone,
offered the machine's powershell.exe. The office read the machine
directly: whether it is WSL, from the kernel's version string, and which
desktop programs exist, from the PATH.

Each read now comes from one place the environment can steer:
OFFICE_PROC_VERSION names the file the WSL check reads, and
OFFICE_DESKTOP_PATH the directories searched for a desktop program.
Unset, nothing changes. The suite sets both for every test, so a test
sees no WSL and no desktop program but the fakes it puts in its own
directory. The probe test keeps its assertion. New terminal tests
imitate a WSL machine and show that nothing of Windows runs, and that
pointed at the fakes the same steps reach them. The suite's rule against
reading the machine now covers the kernel's version and PATH lookups, in
the tests and in the office's source.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.
