# Notes: 2026-10-02-friction-out-and-in-002, the out trip (office-src 0.6.0)

The tree read VERSION 0.5.0, as the brief said, and every name the brief
points at (`ask`, `cmd_note`, `add_project`, `read_projects`,
`record_session`, `sid_from_pack_report`, `doctrine_context_cmd`,
`require_one_writer`, `writers_holding`) was where it said. One probe ran
before any code (pasted back whole: 1201 lines). Its integrity hash
matched once one trailing space the paste had trimmed was restored
(`tags at HEAD: `). Every captured stdout line's sha256 was re-verified
on this side. Everything below about bale is what that probe showed on
the installed bale 0.4.45, in throwaway repos under a temp directory the
probe made and removed. No real repo opened a session.

## What the probe established

- **bale 0.4.45**, at the read side's floor, so the floor stays.
  office-src's HEAD is 09acf76 (`applied/2026-09-30-desk-verbs-002`, plus
  three sweep commits), VERSION 0.5.0, with this session and the
  friction-wave sitting open. **The installed office is still 0.4.0**:
  0.5.0 was never installed.
- **home-office's `[projects]`**: ironwood, bale-src, office-src,
  twine-src and nisaba-src. Each is `path` only, with `.bale/` present
  and ignored by git. `~/nisaba-src/blueprints` holds one tracked file,
  drafting-table.md. The declarations were built against that table.
- **`bale pack --json`** prints one line on stdout. Its keys are
  `outcome` (`packed`), `sid`, `tarball` (an absolute path in
  `.bale/outbox/`), `log`, `session_dir` and `context_files`, then the
  readme and checkpoint echoes, `branch`, `applied_latest`, `sweep` and
  `include_group`. **There is no opener in it.** The opener goes to
  stderr, between bale's scissor lines, exactly as the plain report
  prints it on stdout.
- **A second office pack is refused**: exit 1, nothing on stdout under
  `--json`, and the reason as stderr's last line (`pack write forecast
  intersects 1 open session(s): SID (notepad ~ notepad). ...`).
  `bale status --json` names the open session in `sessions` and its
  forecast in `scopes`, both already declared surfaces.
- **`bale pack --context --json`** prints `{"outcome":"context-packed",
  "tarball", "directory", "tree_name", "context_files", "total_bytes",
  "git"}`. The tarball is always `<dir>/.bale/outbox/context-<dir>.tar.gz`
  and is overwritten on every run. **Include groups do not fire under
  `--context`**: one folder shipped one file, with no profile and no
  survey. Run inside a subdirectory of a repo, it writes a `.bale/` in
  that subdirectory. In a plain directory it walks the tree.
- **bale writes `claude/telemetry/<sid>.json` into the repo it packs in**,
  an office included. It stays untracked until bale's own sweep commit at
  apply (home-office's founding shows that). The office's commits name
  their own paths, so they never sweep it in.
- **The occupant's global post_pack hook** (copy-request-to-downloads.sh)
  prompts, and with stdin closed bale declines it. office start runs pack
  with stdin closed, so the hook never runs from it. The out tray does
  that job now.
- **WSL**: `clip.exe`, `explorer.exe` and `wslpath` are on the PATH;
  `wslview` is not.
- **No per-machine bale config directory exists.** bale's global layer
  is `~/bale/user/bale.toml`, and S7 found nothing changed under it.

The captures land verbatim in `claude/fixtures/bale-0.4.45/pack/`. That
is 11 calls plus `pack --help`, whose lines were hashed from the paste.
They are read by the new `tests/test_start.py`.

## Decisions to ratify

- **The opener comes from between bale's scissor lines.** The report has
  no opener, and OFFICE.md 10 says a missing datum is a slip, never a
  scrape. I read this as the narrow exception: those lines are the block
  bale itself prints for a person to copy, and the markers are declared
  in the consumption manifest (`opener`), so a moved marker fails a test.
  If bale prints no block, office start says so and keeps the session.
  The slip is below.
- **The predictable refusal is checked before bale runs.** office start
  reads `bale status --json` where the pack will run and compares the
  forecasts. It refuses with the open session's id, its folder, and the
  entries that overlap. For office sessions it adds that they take turns
  on the notepad and that `--read-only` does not. bale is never asked,
  so its refusal is never passed through bare.
- **Order: context packs first, the session last.** A failed context pack
  opens nothing and leaves no tray behind (a `.filling-*` staging
  directory is removed). If the session packs and the tray then cannot
  be finished, the error names the sid, where the files are, and the
  `office sessions` line to record it.
- **The doctrine is packed from a scratch copy**, so the install is never
  written. The same goes for a ride-along that is a plain directory
  outside git. A ride-along inside a repo is packed from the repo's top
  with `--include`, because its `.bale/` there is ignored and a
  subdirectory's would not be. A whole repo is packed as is. A file
  outside any repo is copied into the tray. Ride-alongs that share a
  repo go in one pack.
- **An office session about a project** (its folder's lane names one of
  the office's projects) carries that project's tree as a context tarball
  plus the project's ride-alongs. That is exactly the hand step message 17
  names, office-src's context beside a sitting. There is no flag to turn
  it off. Say so if you want one.
- **The out tray** is `~/out-tray/SID`, a directory outside every office.
  `~/.config/office-src/machine.toml` can set `out_tray`. The opener is
  printed after the tray's list, not written into the tray, so dragging
  the tray's contents attaches only the files.
- **WSL: built, because it was cheap.** On WSL, and only when stdout is a
  terminal, office start pipes the opener to `clip.exe` (through `iconv`
  to UTF-16LE, since clip.exe does not read UTF-8) and runs `explorer.exe
  .` in the tray. `clipboard_command` and `open_command` in machine.toml
  override either, and `""` turns it off. Off WSL both are off until set.
  **Untested on a real WSL machine**: the first `office start` on
  chordsphere is the test.
- **Default slugs**: the folder's name without its date, plus `-office`
  for an office session. bale numbers sessions per repo, so the same
  folder packed in home-office and in office-src on the same day would
  otherwise mint one id twice. The tray also takes the next free name if
  one exists.
- **Every question has a flag twin except `new`.** On a terminal, `new`
  at the folder question runs `office open`'s own wizard. Piped, a new
  job is `office open ...` first, then `office start FOLDER`, and the
  refusal says so.
- **`--read-only`** packs an office session that forecasts nothing (a
  sitting). The brief named two places and the goal. I added this flag,
  with no question, because sittings are read-only packs, and without it
  every sitting would wait on the notepad.
- **The declarations** are `rides = [...]` and `after_land = [...]` in
  `[projects.NAME]`, each on one line. They are written by `office
  projects set` (and `add`), which keep every other byte. Setting a key
  to an empty list removes it, so a set and clear round trip restores the
  file byte for byte. A ride-along must exist when it is set, and a
  missing one stops office start before any pack. A declaration that
  does not read is reported beside the project and never makes the
  project unreadable to the read side. `--ride` replaces the list. On a
  terminal, set asks keep (y/n) for a non-empty list, then one entry per
  question.
- **office slip**: one word of `--about` (office, bale, office-src, a
  project, or another tool's name). Piped and untold, it writes no about
  line and says which flag would have. The page is
  `suggestion-box/DATE-SLUG.md`, with `-2` and onward for the same words
  on the same day, and the slug is taken from the words as typed, the
  way `office open` takes one.
- **office note** runs the new `helper append-check ROOT PATH` after
  appending and before committing. If the page's committed bytes
  changed, it exits 1, the words stay on disk, and nothing is committed.
  4b's `watches check --record` can call the same subcommand.
- **lands**: close lands `filing-cabinet/{folder}` and reopen lands
  `desk/{folder}`. open and sessions keep both entries, meaning one of
  them. The suite's lands-equals-writes pin now holds for every script
  except the movers (pinned to where the folder ends up) and the prose
  writers (init, upgrade, default, start). `work` and `build` are
  `built = true`, through start.

## Look closely on review

- **An office session forecasts its own folder, and office start records
  the session in that folder after packing.** The folder.md the worker
  was shown is one commit behind the office. A response that rewrites
  folder.md will meet bale's base check at apply. I am assuming that
  check catches it rather than merging silently; I could not see bale's
  apply code. The sid cannot be known before the pack, so recording
  first is not possible. office land (session 2) is where the record and
  the response meet, and it is on the front sheet's known problems.
- **The doctrine edits** in sections 4, 5, 7 and 10 and its front sheet.
  The verbatim bale/office paragraph is untouched, and section 2's
  constraint is unchanged and used verbatim (`PROJECT_CONSTRAINT`).
- **`office init` and `office upgrade` still print `(cd DOCTRINE_DIR &&
  bale pack --context)`**, which writes an outbox into the install. I
  left them, since they belong to the founding and renovation flows. They
  are on the front sheet and in `deferred`.

## Slips for bale-src (doctrine section 10), from the probe

1. **The `--json` pack report has no opener.** Add an `opener` key (the
   lines between the scissors) so nobody reads stderr for it.
2. **Session ids are unique within one repo only.** Two repos can mint
   the same sid on the same day. The office's folders, which span repos,
   can then hold one id for two sessions. office start works around it
   with the `-office` slug. Either a cross-repo-unique id or a repo stamp
   beside the sid would end that.
3. **A hook with stdin closed is always declined.** A non-interactive
   pack, the office's and any harness's, cannot opt into the user's own
   global hooks. A flag or a config key accepting remembered hooks when
   piped would let the copy-to-downloads hook run under office start.
4. Observation, not necessarily a slip: include groups do not fire under
   `--context`. office start names the hung items itself, so nothing is
   needed unless bale meant them to fire.

## Paths outside the write forecast

None. Every path is under the forecast the manifest stamps.

## The suite

266 tests, 39 of them new in `tests/test_start.py`. The whole suite is
green here and takes about four and a half minutes. validation.sh runs it
whole, as the read side's did, because it is the check that matters.
That puts validation past the two-minute target, and `validation_will_run`
says so. validation.sh was run in a staging copy both ways:

- With the change applied, all eleven checks pass and the ten claims
  agree.
- On the unmodified tree, the seven session assertions fail. The three
  project checks and the exec-bit check pass on both, by design.

The suite's fake bale for office start packs for real: it writes tarballs
and keeps open sessions in its own state file. Every line it prints is
built from the captured packs, with the sid, paths and goal swapped in.
The office's readers are also run over the captured bytes directly, and
every flag office start passes is checked against the captured `bale pack
--help`.

## Proposals

### Install 0.6.0 on chordsphere, then try office start once by hand

- **What:** run `~/office-src/install.sh` (the install there is 0.4.0),
  then `office start` on one real folder, in home-office and on
  office-src.
- **Why:** this is the first release that runs bale for the occupant. The
  WSL clipboard and Explorer steps and the real opener round trip have
  only run against a fake.
- **Scope hints:** none in the code. A slip with `office slip --about
  office-src` for anything that sticks.

### Fold init's and upgrade's printed pack lines into office start

- **What:** the founding session and a renovation are office sessions.
  Let `office init` and `office upgrade` hand off to the same packing
  instead of printing a `bale pack` line that writes into the install.
- **Why:** they are the last lines that ask the occupant to copy a
  command and attach a file from memory, and the last writers into the
  install.
- **Scope hints:** bin/office (`founding_line`, `renovation_line`,
  `doctrine_context_cmd`), lib/office_bale.py `start`. Best after session
  2, which teaches start to take a bundle.

### Let office land re-apply the session record when a response rewrote the folder

- **What:** when an office session's response lands a folder.md without
  the Sessions line office start recorded, office land puts it back as a
  new append.
- **Why:** the drift described under "Look closely".
- **Scope hints:** session 2's office land, `record_session_opening`.

### File the three bale-src slips above as one bundle

- **What:** the opener key, cross-repo session ids, and piped hook
  acceptance.
- **Why:** each one is a workaround or a lost step in office start today.
- **Scope hints:** bale-src's pack report (`format_pack_json`), the sid
  minting, and the hook acceptance store.
