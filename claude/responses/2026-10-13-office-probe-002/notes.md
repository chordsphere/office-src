# Notes: 2026-10-13-office-probe-002 (office-src 0.18.0)

Everything the brief asked for is here: `office probe`, the second-desk
ruling, a live `bale open --json` capture on 0.4.52 (for both `opened`
and `second-desk`, and the `--check --json` rehearsal besides), the
doctrine's sentences, RELEASES.md and VERSION 0.18.0. One deviation from
the brief needs your ratification. It is the first item below.

Before you apply: the probe ran from `~/office-src`, so its output is in
office-src's working copy as an untracked `probe-output/` (the captures,
the throwaway repo and `office-probe-002.tar.gz`). Everything the
session needed from it is in this response, so remove it first, from
`~/office-src`: `rm -rf probe-output`.

## Decisions to ratify

1. **The ruling reads bale's outcome, not the `rehearsal` key (a
   flagged deviation).** The brief said: if `bale open --check --json`'s
   `rehearsal` key does not say which bundle opened the session, say
   what it does say and leave the refusal as it is, flagged. It does not
   say. On a second desk the key is `"check"`, and the whole stdout line
   is byte for byte a fresh bundle's (check-desk and check-fresh share
   one sha256). bale names the session only on stderr: `[bale] second
   desk: this bundle opened session SID, which is still open; bale open
   would record desk-2 on it`.

   The probe also showed that bale's verdict is in the line all the same,
   as its `outcome`. A bundle whose session is still open rehearses
   `"rehearsed"`, exit 0. A different bundle on the same forecast is
   `"open-refused"`, reason `"gate-refused"`, exit 1. The ruling you are
   ratifying is "the office refuses an overlap only where bale would
   refuse it". The outcome answers exactly that question, as a declared
   JSON key, with nothing read from `.bale/` and nothing parsed from
   stderr for a decision. Leaving the refusal in place would have the
   office refuse precisely the case the ruling says is bale's. So from
   bale 0.4.50 (open_json's `since`), office start goes to `bale open
   --check --json` with the office's overlap lines held, and:
   - if bale passes it, start prints what the office's check saw and
     bale's own second-desk line, then goes on; the open that follows
     joins the desk exactly as 0.17.2 does, held to the registry diff;
   - if bale refuses it, start refuses in the office's words with
     bale's reason and cause beside them.

   Below 0.4.50 nothing changed. If you want the brief's literal
   fallback instead, it is one line: in `check_bundle_report`, raise
   `StartError(over)` whenever `over` is non-empty.
2. **The front-sheet sentence is in the core.** The brief placed both
   doctrine sentences "past the core". The verb table and section 7's
   walk-in paragraph are. "The front sheet's list of everyday verbs"
   sits above the PAST THE CORE banner, though: it is the front sheet,
   section 1's summary. I put the sentence there, since that is where
   the list is. TestTheDoctrinesCore is unaffected, as the brief
   expected: it holds headings and the banner's budget (now line 196,
   against its limit of 300), not bytes. validation.sh proves the three
   insertions are the only doctrine change. It undoes them and gets the
   request's base sha256.
3. **The Suite line sentence is its own sentence.** It sits right after
   the walk-in's long list sentence, rather than inside it, which reads
   better.
4. **A probe needs an open session.** The session is the folder's
   recorded session open where the project lives, read through bale
   status there. With several open, the one the block's slug names
   wins, else `--sid` (asked on a terminal). With none, the probe is
   refused. The brief's out tray and History line are both per session,
   and a block with no session to return to is a stray.
5. **What "read-only" means at the gate.** A header line has to say
   "read-only" (or "read only"), and no header line may say "not
   read-only". A fallback probe whose header says "Read-only except
   ./probe-output/" passes, which is how the fallback gets carried at
   all. The header is the comment lines before the first blank line,
   the shebang aside. A chat's code fence around the block and CRLF
   line ends are dropped.
6. **A `probe-output/` already where the block would run stops it before
   it runs**, so a fallback's fresh output is never mixed with a stale
   one. A second fallback probe of the same session lands beside the
   first in the out tray, as `probe-output-2/`.
7. **The History line respects the one-writer rule.** When an open
   session in the office's own registry forecasts the folder (an office
   session), the line is not written and is printed instead, since
   writing it would hand that session's landing a base drift.
8. **The WSL paste command offered is `powershell.exe -NoProfile -Command
   "[Console]::OutputEncoding = [Text.Encoding]::UTF8; Get-Clipboard"`.**
   That is the sitting's guess plus the UTF-8 setting, so a block's em
   dash survives the console code page (the probe's own paste showed
   CP437 mangling, as 0.4.47's did). It is still memory, not a probe's
   fact. The probe only confirmed powershell.exe is on your PATH. Correct
   it at the question if it misbehaves; the front sheet lists it as a
   known problem until it has run once.
9. **VERSION is 0.18.0**, as the brief proposed: a new verb, additive,
   no migration.

## Where to look closely

- `lib/office_bale.py`, `check_bundle_report` and `bundle_precheck`: the
  ruling. `start()` takes `--bale-rehearsed` from bin/office, which sets
  it only when bundle-check printed `over` lines, meaning bale's
  rehearsal passed what the office's check caught.
- `lib/office_host.py`, the new section at the end: `run_probe`,
  `carry_dir_here` and `remove_dir_there`. office_host stays the only
  code that runs the shell. The block travels as the one command string
  through the plain prefix (`Place.argv`, never `attended_argv`), with
  `</dev/null`. A probe-output/ comes back as one tar stream, and its
  file count is held to the far side's before anything is removed there.
- `tests/test_land.py`: the fake bale's two open branches now replay the
  0.4.52 captures (sid, bundle and paths swapped in). They used to build
  lines from the docstring. The live second-desk test's opener assertion
  moved, because the real desk opener names `SID@desk-2` on its fifth
  line, not its second (0.17.2's fake had invented a second line).

## What the probe established (TARBALL.md 4.5)

The file-based fallback probe office-probe-002 ran on chordsphere on
2026-10-13, from `~/office-src`. All 301 lines came back, matching the
integrity trailer. It established:

- bale 0.4.52, installed at `~/bale`.
- `format_open_json`'s docstring is the key contract. It is kept as
  `fixtures/bale-0.4.52/format_open_json.txt`, with its four CP437-mangled
  characters restored.
- On `"rehearsed"`, `rehearsal` is `"check"` or `"dry-run"`, and it is
  null on every other outcome.
- On a second desk, `bale open --check --json` exits 0 with a line
  identical to a fresh bundle's. bale names the session on stderr alone.
  The browser `(1)` copy rehearses the same way.
- A different bundle overlapping the open session is refused:
  `open-refused`, `gate-refused`, with the forecast-intersection text as
  the cause, exit 1.
- The `bale open --json` lines look as follows:
  - `opened` carries the replayed pack's own keys.
  - `second-desk` carries the joined sid, `desk` ("desk-2", then
    "desk-3" for the `(1)` copy by bare name), the outbox tarball and
    the desk's opener.
  - Every key `[surfaces.open_json]` declares is in them.
- bale's install `user/` was unchanged before and after, and the
  throwaway repo's tree was clean at the end.
- powershell.exe and clip.exe are on your PATH. machine.toml holds only
  `downloads`.
- An observation, not in this session's scope: your global post_pack
  hook (`user/scripts/copy-request-to-downloads.sh`) is declined
  whenever bale's stdin is closed. That covers every pack and open
  `office start` runs, so that hook never fires for an office-started
  session.

## Tests and the suite's clock

- 41 new tests in `tests/test_probe.py`, and 733 in the suite. They
  cover the block and the output as units, the paste command, the verb
  on a project here, the office root and a host, the terminal, the
  ruling end to end and over the captures, the captures themselves, and
  the record.
- `office probe`'s entry point and test_probe's four cheap classes joined
  `tests/fast-tier.toml`.
- validation.sh runs `tests/run.sh --fast` plus six names. In this
  sandbox (two cores), with this response applied to a copy of the
  request's tree, that was 307 tests in 103 seconds, against the
  120-second budget. On the unmodified tree its session assertions
  fail, as they should. The probe tests are about 7 seconds each,
  because each one packs a session first, so only the ruling (both
  sides, and over the captures), the host run, the doctrine's core and
  0.4.47's rehearsal reader ride in validation. The refusals by name
  run in the tier as units (TestTheBlock); the rest wait for `--slow`
  or the detached run.
- The whole suite in this sandbox: OK, 733 tests in 20 minutes 20 seconds of wall clock (1,220 seconds side by side, 4 jobs on two cores), with every change here applied.

## Proposals

- **What:** amend doctrine section 4 (continued), which still says "a
  bundle is refused the same way whenever the office can read its pack
  line". **Why:** since 0.18.0 that holds only below bale 0.4.50. From
  there, bale's rehearsal decides an overlap the office found. This
  session was held to two named doctrine sentences, so the sentence
  waits. The front sheet lists it as a known problem. **Scope hints:**
  one sentence in doctrine/OFFICE.md, the paragraph starting
  "`office start` does all of this"; past the core.
- **What:** the post_pack hook question, if it matters to you. Should an
  office-started session's request still be copied to the downloads by
  your global hook? **Why:** the probe showed the hook declined with
  stdin closed, which is how office start always runs bale. **Scope
  hints:** a bale-src question first (a hook default for non-interactive
  runs), not an office one.
- **What:** in a later wave, `office probe` could read a block straight
  from the downloads by name (`probe-*.sh`), the way land finds a
  response. **Why:** not asked for; it is just what this session's own
  fallback probe would have wanted. **Scope hints:** lib/office_probe.py's
  block source and bin/office's question order.

## Walkthrough

### What changed

- `office probe FOLDER [FILE | -]`, a new verb (bin/office, lib/office_probe.py,
  and a new section of lib/office_host.py). It runs a worker's probe
  block where the folder's project lives:
  - in its repo on this machine;
  - through its shell on a host, using the plain form with no terminal,
    stdin closed;
  - or in the office root.

  It shows the block's purpose header, asks once, then hands the output
  back. The lines from PROBE BEGIN to PROBE END go on the clipboard here,
  with a count checked against the integrity trailer. A fallback's
  probe-output/ is carried to `~/out-tray/SID/probe-output/` and removed
  where it ran. The folder's History gains `- DATE probe: SID, N lines`.
- machine.toml gains `paste_command`, how this machine reads its
  clipboard, asked once (lib/office_helper.py).
- `office start --bundle`: for a bundle the office can read, an overlap
  its own check finds is now bale's to judge from bale 0.4.50, through
  `bale open --check --json` (a new surface in
  share/bale-consumption.toml).
- claude/fixtures/bale-0.4.52/: 13 live captures and the docstring. The
  suite's fake bale replays them.
- The doctrine names `office probe` twice (the front sheet's everyday
  verbs, the verb table) and the walk-in's `Suite:` line once.
  share/verbs.toml declares the verb; README, RELEASES and the front
  sheet say all of it.

### Why

A worker writes its probe for the machine its project's repo is on.
For the work office's projects that is a container behind ssh and a
VPN. Until now you ran each such probe by hand: VPN, ssh, docker exec,
paste, copy, paste back. The office is your hands at the terminal and
already reaches those containers through each project's shell, so it
runs the probe.

The second-desk change is the ruling you ratify with this bundle. A
bundle whose session is still open overlaps that session by
construction, and bale takes it as one more desk. The office had been
refusing that case in its own words before asking bale.

### How to explain each piece

- office probe: "Give it the folder and leave the worker's block on the
  clipboard. It shows you what the block says it does, asks, runs it
  where the project lives, and puts the answer back on your clipboard
  to paste."
- The refusals: "It won't run anything that doesn't call itself a probe
  or doesn't say it's read-only. A probe that writes is the fallback,
  and that one says where it writes."
- The fallback: "If the probe leaves a probe-output folder, the office
  brings it home to the session's out tray and cleans up where it ran."
- The ruling: "When you start a bundle that's already open, bale knows
  it's a second desk. The office now lets bale say so instead of
  refusing it first."

### Questions a reviewer will ask

- Why not a new connection for each step on a host? It is one reach and
  few connections. The plan's batch (bale status plus whether
  probe-output/ is there) is the reach. Then come the run and the check
  for probe-output/, and on a fallback the carry and the removal: five
  connections at most, and no `true`.
- Can a block wait on a terminal? No. Its stdin is /dev/null, and the
  host's shell is the plain form, so no `-tt` and no `-it`.
- What if the block never ends? It gets the office's backstop:
  `OFFICE_PROBE_TIMEOUT`, 1800 seconds by default.
- Does the office read `.bale/`? No. It reads bale status, and the
  rehearsal's outcome key.

### A hand test

1. Install and land as usual (`./install.sh`). First check that
   `~/office-src/probe-output` is gone (`rm -rf ~/office-src/probe-output`).
2. With a session of folder 13 out (the next one `office start` sends),
   run, from any directory, `python3 ~/bale/tools/craft_response.py
   --probe hand-test > ~/hand-test.sh`. That is a skeleton probe: its
   header says read-only, and its body prints a TODO line. Open the file
   and copy all of it to the clipboard.
3. Run `office probe 13`. The first time it asks how this machine reads
   its clipboard and offers the PowerShell line; take it with a return.
   Then check:
   - It asks where the probe runs, because folder 13 has no lane. Answer
     `office-src`.
   - It shows the header (PROBE hand-test, Why, Read-only, Bound), says
     where it runs and for which session, and asks "Run it? y or N".
     Answer `y`.
   - The block's output appears, ending with `=== PROBE END hand-test ===`.
   - The office says the lines came back and the trailer matches, and
     that the block is on the clipboard.
4. Paste into any editor. You should see the block from `=== PROBE BEGIN
   hand-test ===` to `=== PROBE END hand-test ===`, and nothing mangled.
5. `office desk` or folder 13's folder.md: its History ends with `-
   DATE probe: SID, N lines`.
6. When the VPN is up and a work-office folder has a session out, repeat
   on one of its projects with `--project` naming it. The block's cwd
   line (if it prints one) is the container's repo path, and nothing is
   asked inside the container.

## Delivery

- to: nobody: office-src has no audience

### Commit

Add office probe, and let bale judge a second desk

office probe runs a worker's probe block for a folder where the folder's
project lives: in its repo, through its shell on a host, or in the
office root. It shows the block's purpose header and asks once before
anything runs, and refuses by name a block that is not a probe or does
not say it is read-only. The block runs with its stdin closed and no
terminal; its output comes back whole. Then:

- the lines between its PROBE BEGIN and PROBE END go on the clipboard
  here, counted against its integrity trailer;
- a probe-output directory it leaves is carried to the session's out
  tray and removed where it ran;
- the folder's History gains one probe line per run.

The block comes from a file, stdin, or the clipboard, read with a new
paste_command setting asked once per machine.

office start lets bale judge a bundle the office can read whose forecast
overlaps an open session. From bale 0.4.50 it asks bale open --check
--json. A bundle bale would take as a second desk goes on, and one bale
refuses is refused in the office's words with bale's reason.

The suite replays live bale 0.4.52 open --json lines, and the doctrine
names the new verb and the walk-in's Suite line.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.
