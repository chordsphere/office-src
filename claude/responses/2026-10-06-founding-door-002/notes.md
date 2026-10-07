# Notes: 2026-10-06-founding-door-002 (office-src 0.12.0)

The founding door, built as one additive release, 0.12.0. The pre-flight
said the work fit one session, so I didn't split it. Nothing was written
outside the forecast (it is the whole repo).

Bottom line: `office init` now asks the profile's questions and sends the
founding session out through `office start`; `office upgrade` sends a
renovation out the same way; an unfounded office's Next line names a
command that works; and nothing writes into the install any more.

## What the probe established

No probe ran. The brief expected one ("your probe says what is true"),
but nothing in this work turned on the registry, and the survey that
`office start` wrote at 2026-10-06T21:01:17Z (two seconds before the
pack, riding in the office context) gave the machine facts the code
needed:

- bale is **0.4.46** now, not 0.4.45 as the brief says (the survey's
  change report says so, and the request was packed by 0.4.46).
  `BALE_HELP.md` showed nothing in `bale pack` that the founding pack
  depends on differently: it is the same office-session shape every
  `office start` has packed since 0.6.0.
- office-src 0.11.0 is installed; the system zone is
  America/Indianapolis, TZ unset.

If you want the registry state on record, say so and I'll send a probe
with the next session; it changes nothing here.

## Decisions to ratify

1. **Flag twins: one per section, not `--answers FILE`.** `--purpose`,
   `--not-for`, `--audiences`, `--site`, `--house-rules`,
   `--when-to-open`, `--spaces`, plus `--timezone ZONE`. They come from
   new `flag` keys in `share/profile-shape.toml`, beside a `hint` (what
   `?` adds to the asks line) and `asked = false` on Founding. A section
   without the keys gets a flag made from its heading, so a renovation
   that adds a section still gets a question. A longer answer is
   `--purpose "$(cat purpose.txt)"`; the terminal takes one line each.
2. **A new verb, `office found`, for an office that exists.** It is the
   founding door's second half on its own: the questions (only those the
   founding folder doesn't already keep; a flag given now wins), the
   folder, the session. `office start FOLDER` on the founding folder of
   an unfounded office goes through it, so the Next line can say either.
   It refuses a founded office, and one whose founding session is out
   (it names `office land SID`).
3. **The Next line for an unfounded office**, which still sits before
   the ready folder, as it did:
   - founding folder on the desk, nothing out: `office start
     DATE-founding` (the brief's ask; it works because start delegates);
   - no founding folder: `office found`;
   - founding session out: `office land SID`, as in 0.8.0.
4. **Init writes the zone to the floor plan when it resolves.** It does
   this as soon as you answer, in its own commit, so the founding
   folder and everything after it is dated in your zone. The founding
   session then only writes Site. A zone that doesn't resolve is named
   with `zone_remedy`'s words. On a terminal it is asked again; the same
   answer twice keeps it. The floor plan keeps the machine's zone, and
   the brief tells the session to settle it with you. This is how I
   read "founding checks the zone it writes". Say if you meant the
   session to write the floor plan too.
5. **Where the answers live: `answers.md` in the founding folder.** They
   are your words, quoted as typed, with the date and the verb that took
   them. The brief tells the founding session to record "answered
   through office init on DATE" in **both** places: the profile's
   Founding section and the notepad page it files. It also files your
   init answers verbatim on that page, as the sitting leaned. Init
   itself files nothing in the notepad.
6. **The machine's zone reads TZ first.** If TZ names a zone, that wins,
   then /etc/timezone, then /etc/localtime. That's the order the C
   library uses, and it lets the tests set the machine zone without
   touching /etc. It changes nothing on chordsphere, where TZ is unset.
7. **Renovation forecast: the whole office, unless the migration
   declares `writes`.** `writes` is a new optional key on renovation
   migrations; it lists paths that must exist, and `.`, `..` and empty
   lists are refused. Without it, `office start` packs exactly as the
   old printed line did (no `--include`, no `--write`), so bale ships and
   forecasts the whole tree. The trigger is `--write .` passed to start.
8. **A renovation while the office is behind.** `require_current` lets
   the renovation's folder and session through only when `office
   upgrade` sets `RENOVATING`. `office land` lands while behind only
   when the session belongs to the renovation folder of the first
   pending migration; every other verb still refuses. When behind with
   the renovation out, the Next line names `office land SID` before
   `office upgrade`. A re-run of upgrade names the session out and
   never packs twice.
9. **`office init` exits 1 when the founding session did not go out.**
   That covers bale not on PATH and start refusing. The office is built
   and the answers are kept; the line says `office found` sends it, and
   the walk-in names it too. `--no-founding` builds only and prints
   `Next: office found`, which is what the tour now uses. The suite's
   offices use it too, so `Env.init` passes it unless a test asks for
   the door.
10. **The founding folder** is `founding`, source `office init` (or
    `office found`), class `meta`, size `small`, titled "Found the NAME
    office". The session's slug is still `NAME-founding`, so the sid
    reads like home-office's.

## Look closely on review

- `found_office` and `renovate_office` in bin/office. They call
  `cmd_open` and `cmd_start` with `OFFICE_ROOT` pinned. Start runs in a
  subshell, so a refusal comes back to init as a status rather than
  killing it.
- `cmd_start`'s delegation. It fires only when there is no `--brief`
  and no bundle, the folder is the one `door-folder` names, and the
  profile is incomplete. Then `--on`, `--write`, `--include`,
  `--read-only` and `--slug` refuse.
- `cmd_land`'s behind branch. It reads the first pending migration's
  version from `skew_report` to find the renovation folder, and lands
  nothing else.
- `office_bale.start`'s whole-office branch (`--write .`). It clears the
  folder include as well, since bale's default ships the whole tree. An
  occupant could also type `office start X --in-office --write .`. That
  is new, and it does what it says.
- `office_door.parse_answers`. It reads only the quoted lines under each
  heading. Quoting is also why an answer holding a NOTEPAD PAGE marker
  can never be filed as a page (tested).
- The brief's survey section copies the survey's facts at composition
  time. `office start` surveys again before it packs, so the hung page
  may be a few seconds newer.

## Slips for bale-src

- **Waiting, unfiled, from earlier notes** (the four the brief lists):
  - `bale unlock --help` and the sweep commit;
  - no after-land hook on bale's side;
  - the `[bale SID]` commit subject is a convention, not a contract;
  - `stats --since` takes a day, not an instant.
- Nothing new.

## Paths outside the forecast

None. The forecast is the whole repo.

## The suite

`validation.sh` runs the whole suite and says so in `validation_will_run`,
as before (`VALIDATION_SKIP_SUITE=1` skips it loudly). It runs
`tests.test_founding_door` on its own first, so a failure in the door
shows within about a minute and a half.

- **New:** `tests/test_founding_door.py`, 23 tests. They cover:
  - the questions as data;
  - piped init with the flag twins;
  - init on a pty: `?`, a skipped section, a flag that answered one, and
    a zone that does not resolve, corrected or kept;
  - init without bale, then `office start` on the founding folder;
  - `office found`, including refusing while out and refusing a founded
    office;
  - landing the founding session;
  - the unfounded Next line in every state, and the behind one;
  - upgrade against fixture renovation migrations: whole office,
    declared `writes`, scripts before it, a bad `writes`, no bale;
  - a static check that no line packs in the install.

  Each test sets its own TZDIR, TZ, HOME and machine settings (no
  clipboard, no file manager).
- **Changed:**
  - `test_office.py`: `Env.init` passes `--no-founding`; init's first
    test is rewritten; the two renovation tests moved to the new file.
  - `test_front_door.py`: init with `--no-founding` and its Next line;
    the unfounded Next line names `office found`.
  - `test_desk_verbs.py`: the terminal init passes `--no-founding`.
  - `test_watches_digest.py`: one doctrine-order assertion follows the
    new wording.
- **Runs:**
  - Before shipping, on this tree with this machine's zone left as it
    was: 475 tests, one failure, the doctrine-order assertion, since
    fixed. The release check in `validation.sh` also failed once on a
    wrapped front-sheet line; its pattern was fixed before the final run.
  - The final run: this response's `validation.sh` in a fresh staging
    copy of the packed tree with the response applied, the machine set
    to America/New_York and TZ unset. Every check passed, all six claims agree, and all 476 tests passed in 1394
    seconds, about 23 minutes on this machine (the label still says about 17,
    as the brief asked; this container was slower than the last one).
    My first attempt at this run died with the container partway through
    the suite; it was restaged from scratch and run again.
  - On the unmodified tree, with the suite skipped, every
    session-specific assertion failed, as it should.
- The tour's pty test didn't flake for me.

## Proposals

### A founding answer longer than a line, on a terminal

- **What:** let a profile question take several lines on a terminal (for
  example, a line ending in `\` continues, or a blank line ends the
  answer).
- **Why:** home-office's answers were paragraphs. Today the terminal
  takes one line per section, and anything longer needs the flag twin
  with a file, or the founding session's conversation.
- **Scope hints:** `ask_profile` in bin/office, and `ask` if the change
  is general. The answers file already keeps several lines.

### Close the founding folder with the founding

- **What:** when the founding session lands applied and the profile is
  complete, have `office land` offer to close the founding folder (or
  let the founding brief ask the session to write the folder's Next
  section as "close").
- **Why:** after the founding lands, the walk-in's Next line names
  `office start DATE-founding` (an open folder with nothing out), which
  is the open-folder rule doing its job. But a founding has nothing more
  to do.
- **Scope hints:** `cmd_land`'s applied branch, or the founding brief in
  `lib/office_door.py`. A small piece for the third trip.
