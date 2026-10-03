# Notes: 2026-10-03-friction-return-trip-001, the return trip (office-src 0.7.0)

The tree read VERSION 0.6.0, as the brief said, and session 1's notes were
where it said. One probe ran before any code (pasted back whole, 3144
lines, its integrity hash matched once the paste's CRLF line endings were
turned back into LF; every one of the 1456 hashed lines re-verified on
this side). Everything below about bale is what that probe showed on the
installed bale 0.4.45, in throwaway repos under one temp directory the
probe made and removed. No real repo applied, opened or packed anything,
`~/bale/user` was unchanged before and after, and no file under your home
changed while it ran. No light question block or clarification was
needed: the brief settled every intent question this session met.

## What the probe established

- **bale 0.4.45** still, so the floor stays. office-src is at
  `applied/2026-10-02-friction-out-and-in-002` plus the sweep, with this
  session and the friction-wave sitting open (the sitting read-only).
  home-office is idle, applied count 1, and its desk is empty.
- **`bale apply` plain** prints everything on stdout: the walkthrough, then
  the relay between `=== RELAY BEGIN <sid> to planner ===` and `=== RELAY
  END <sid> to planner ===`. Piped, the walkthrough merges by default. With
  stdin on a terminal and stdout piped, it still asks (`[Enter/m] merge into
  origin (default)   [r] revert`), on stdout. That is exactly the shape
  office land runs it in.
- **`bale apply --json`** prints one JSON line on stdout with `outcome`,
  `verdict`, `merge`, `drift`, `base_drift` and more, but no relay key; the
  relay, the banners and (per its help) the prompts all move to stderr.
- **A HOLD** prints two blocks, `to worker` first ("Send it now: it goes
  first"), then `to planner`; the session stays open, `held`.
- **The folder-record case (outcome 3).** A file committed after the pack
  that the response rewrites is refused as `base-drift-refused`, piped and on
  a terminal alike. There is no prompt, only a re-run line with
  `--accept-base-drift PATH`. Nothing is staged and the session stays open.
  With the folder's pack-time bytes committed back before the apply, it
  lands with nothing asked. The gate compares bytes, not commits.
- **Out of forecast**: piped, refused (`scope-drift-refused`); on a terminal
  bale asks `admit PATH? [y/N]` per path, decline by default.
- **A clarification**: apply exits 0, records the round, prints no relay,
  and adds no attempt to the dossier. `bale relay SID` with no file
  re-emits the planner's paste block on stdout (`BALE EXCHANGE BEGIN
  <sid>` ... `BALE EXCHANGE END`) and records nothing.
- **Names**: a bare `response-SID.tar.gz` is found through the repo's
  `apply.search_paths` (cwd first). A missing one is refused with every
  directory searched. Bare `bale apply` (no tarball) resolves the newest
  response answering an open session, then asks y/N; piped it declines.
  Your global search path is `/mnt/c/Users/chord/Downloads/`, which holds
  89 responses, several saved twice by the browser as `response-SID
  (1).tar.gz`.
- **`bale pack --dry-run --json`** is refused: a pack cannot name its sid
  before it runs, so recording the folder before packing is still not
  possible.
- **`bale open`** has no `--json` and takes no flag beyond its own
  (`--include` beside it is a usage error, exit 2). Its whole report is on
  stdout: the replayed pack line, `session id:`, a `  tarball:` line with
  the request's path, and the opener between the same scissor lines as
  pack's. The post_pack hook is declined with stdin closed, as for pack. A
  bare bundle name resolves through the same search path as apply. The
  bundle is left where it was. A read-only bundle opens a session whose
  status scope is `[]`.
- **Dossiers** after each case carry the attempt outcomes the office words:
  `applied`, `held`, `base-drift-refused`, `scope-drift-refused`.

The captures land verbatim in `claude/fixtures/bale-0.4.45/land/`: 42 calls,
with a README saying what each is. `tests/test_land.py` reads them, and its
fake bale prints nothing that is not built from them.

## Decisions to ratify

- **apply runs plain, not `--json`.** Its stdin is your terminal and its
  stderr is the terminal's; its stdout is copied to the terminal as it
  arrives and kept for the relay blocks. The probe showed the prompts still
  arrive that way. Under `--json`, prompts and relay go to stderr, and a
  prompt reaching you through a piped stderr was not probed. The outcome is
  read from the session's dossier afterwards (the apply or retry attempt
  this landing added), never from bale's words. With no new attempt, an
  exit 0 on a session still open is a clarification, and anything else is
  "bale refused before it recorded an attempt".
- **The relay is taken from between bale's RELAY markers.** This is the
  opener's narrow exception, as the sitting's condition allows:
  `apply --json` has no relay key. The markers are declared in the
  consumption manifest, and a moved marker fails a test. The same holds for
  `bale open`: no `--json` at all, so the opener and the request's path are
  read from its report. The session id is not read from the report; it is
  the session `bale status --json` lists after the open and did not before.
  Slips below.
- **The office passes bale nothing that answers a question.** apply and
  retry are declared as `[verb, {tarball}]` with no optional flags, and a
  test pins it. Admissions, the merge or revert, and hooks are yours at
  bale's own prompts. bale's printed re-run lines (`--accept-base-drift`,
  `--allow-out-of-scope`) are left to you, and the office's words say so.
- **The response is named, not guessed.** With a sid (given, or the one
  out), land passes `response-SID.tar.gz` and bale's search finds it. A
  file given as a word or `--response` is passed by its full path, and
  its manifest's `responds_to` says which session it answers. That reads
  the worker's tarball, not bale's records; flag it if you see it
  otherwise. I did not use bare `bale apply`: it picks among the two
  newest response files in Downloads, whichever project they belong to,
  and could land a different open session's response if you said y
  without reading its echo.
- **A held session needs its file named.** The corrected response after a
  HOLD is usually `response-SID (1).tar.gz` in Downloads, and bale's search
  would find the held one first. On a terminal land asks for it (default
  the bare name, and `?` says why). Piped, it refuses naming `--response
  FILE`. The verb is `bale retry`.
- **The folder record (outcome 3): bale never has to ask.** For an office
  session, before apply, land checks that the last commit touching the
  folder's folder.md is the office's own record of this session
  (`office sessions: SID in NAME`, or a previous `office land: SID
  recorded again in NAME`), with nothing uncommitted. If so, it commits the
  folder's pack-time bytes (`office land: SID unrecorded in NAME while it
  lands`), runs bale, and then:
  - Applied and the landed folder lacks the sid: the office's record is
    merged back with a three-way merge (`git merge-file`: packed, recorded,
    landed), so the `opened` History line keeps the day it opened. If the
    worker touched the same lines, it falls back to a new append, as the
    brief's proposal said.
  - Nothing landed (HOLD, refusal, clarification): the recorded bytes go
    back as they were, so the desk and the walk-in still map the session to
    its folder. A later `office land` for the retry does the same dance
    again.

  A folder changed by anything else after the record, or one in the filing
  cabinet (only gains lines), is left alone. Land says why in one line
  before bale runs, and bale's refusal names its own re-run line. The cost
  is two extra commits in the office per office landing, and a History
  line that is out of folder.md for the length of one apply, on a live
  page, never a filed one.
- **After-land actions** run with `bash -c` in the project's root, in
  order, with stdin inherited, and only after an applied landing. The
  first failure stops the rest and prints the `(cd ROOT && CMD)` line for
  it and for each one after it. Land then exits 1, though the session did
  land. Office sessions run none.
- **Ratification comes last**, after the actions, so you can paste the
  relay into the planner's chat while install.sh runs. The default is
  "not now". Piped, with no flag, nothing is recorded, and the line to
  record it later is printed. A `--ratified` on a landing that did not
  apply records nothing and says so.
- **On a HOLD the worker's block goes on the clipboard first**, as bale
  orders it. On a terminal, a return puts the planner's block on next.
- **Exit codes**: 0 when bale applied (and every action ran) or recorded a
  clarification; 1 otherwise.
- **`office start` with a bundle** asks the folder and where, as for a pack,
  never the goal, and takes no pack flag beside `--bundle`. It runs `bale
  open` with stdin closed, so a pre-answered intent is bale's to honour and
  nothing else is answered. It skips its own forecast-overlap refusal for a
  bundle: bale open's gates make that refusal before any session exists,
  and start passes them through whole. That is the one thing start does for
  a pack and not for a bundle; say if you want the office's own words
  there too. That needs the office to read the bundle's argv, which it can
  only do when the bundle is a file it can find. When it can, it warns
  that a project bundle lacks the constraint of doctrine section 2, or that
  an office bundle's forecast does not name the folder; it never adds
  either.
- **The sitting's page is filed after the open succeeds**, from the
  README.md the request actually shipped (byte-exact with the brief, as
  bale verifies). A refused page leaves the session open and the tray
  ready, says so loudly, and exits 1. **I also file pages from a `--brief`
  given by hand**, the fallback form of a sitting's brief, so the
  convention means one thing. The ruling names bundles only; strike it if
  you want it narrower. The page path must be `notepad/DATE-SLUG.md`, the
  slug lowercase letters, digits and dashes, and the date a real date. A
  BEGIN without its END, or an END alone, is named and nothing between them
  is filed.
- **`office land` joins the walk-in's "From here" list and `office help`.**
  The Next line is session 3's and is untouched.

## Look closely on review

- `lib/office_bale.py`'s `Reader.interact`: os.read chunks copied to the
  terminal as they come, Ctrl-C waited out, the exit code passed through.
  The real terminal test is your first `office land`.
- office-src's own after-land action, `./install.sh`, replaces the install
  that the running `office land` is read from. install.sh removes the old
  install and moves the new one in, so bash keeps reading the old script
  through its open file, and the steps after it (the ratification) run the
  new helper. That is fine between additive releases. A release that
  renamed a helper subcommand would want its ratification asked before
  the actions.
- The clipboard step is now `to_clipboard` in bin/office, shared by start's
  opener and land's blocks. It is still untested on WSL.
- `folder_record` and `put_record_back`, the git dance above.
- The doctrine's edits in sections 3, 4, 5, 7, 9 and 10 and its front
  sheet. The verbatim bale/office paragraph and the append rule are
  untouched, and section 10 now says the verbs that run bale do so with
  you at the terminal.
- This brief's own page used bare `--- PAGE BEGIN ---` markers, so nothing
  of it would be filed into a notepad, as the brief said. It landed in
  `claude/context/sittings/` byte-exact (sha256 `2db9f41b...`) and is pinned
  in `WORDS_SHA256`.

## Slips for bale-src (doctrine section 10), from the probe

1. **`bale apply --json` has no relay key.** Add the blocks to carry, each
   with its addressee, so nobody reads them from between markers.
2. **`bale open` has no `--json`.** Add the report keys pack has (`sid`,
   `tarball`, and the opener the pack slip asks for).
3. **A clarification apply adds no attempt to the dossier.** The round is
   on `bale status` for the lock session only. A clarification row (or
   outcome) in the dossier's attempts would make it readable for any
   session.
4. **The dossier's `record.read_only` is false for a read-only session
   opened from a bundle** (status scope `[]`). Observed once, on
   `bale open` of a `--read-only` bundle.
5. **Bale's named search takes `response-SID.tar.gz` first even when a
   newer `response-SID (1).tar.gz` sits beside it.** That is how a browser
   saves a corrected response after a HOLD. Bare apply orders by mtime;
   named resolution could at least say a newer copy exists.

Session 1's three slips (the pack opener key, sids unique per repo only,
hooks declined when stdin is closed) stand as they were.

## Paths outside the write forecast

None. Every path is under the forecast the manifest stamps.

## The suite

The suite is now 306 tests; 40 of them are new, in `tests/test_land.py`.
It is green here and takes about seven and a half minutes. `validation.sh`
runs it whole, so validation is past the two-minute target, and
`validation_will_run` says so. `validation.sh` was run in a copy of the
tree both ways:

- With the change applied, all twelve checks pass, the exec bit included,
  and the ten claims agree.
- On the unmodified tree, eight of the nine session assertions fail, and
  so does the syntax check, because the files it parses are not there yet.
  The suite, the untouched-files check and the exec bit pass on both, by
  design.

The fake bale for land wraps start's packing fake and adds apply, retry,
the dossier, relay and open. Every line it prints is a captured line with
the sid and paths swapped in. On a terminal it asks bale's admission and
walkthrough questions where bale asks them, and the terminal tests answer
them as you would.

## Proposals

### Land this session with office land

- **What:** bring 0.7.0 back with `office land
  2026-10-03-friction-return-trip-001` from home-office, once office-src's
  `after_land` is declared (`office projects set office-src --after-land
  ./install.sh`). Then run the next office session through `office start`
  and `office land` both.
- **Why:** this release changes what lands it. 0.6.0's install has no
  `office land`, so this one session still lands by hand: `bale apply
  response-2026-10-03-friction-return-trip-001.tar.gz` in `~/office-src`,
  then `./install.sh`. Every session after it can use land. The relay
  clipboard, the prompts through the copy of stdout, and the folder dance
  have only run against a fake.
- **Scope hints:** none in the code; a slip with `office slip --about
  office-src` for anything that sticks.

### Let the walk-in name office land beside each session out

- **What:** session 3's Next line could say `office land SID` for a
  session out, the way it will say `office start` for a ready folder.
- **Why:** land with no argument already finds it, but the walk-in is
  where you look first.
- **Scope hints:** session 3, `render_desk`'s In flight lines and the
  Next line.

### File the five bale-src slips above with session 1's three

- **What:** one bale-src session for the report keys (pack opener, open's
  `--json`, apply's relay) and the record gaps (clarification attempt,
  read-only flag), plus the named-search duplicate.
- **Why:** each one is a marker the office reads today, or a fact land has
  to infer.
- **Scope hints:** bale-src's `format_pack_json` and `format_apply_json`,
  `bale open`'s report, and the dossier writer.
