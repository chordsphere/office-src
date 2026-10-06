# Notes: 2026-10-06-drafting-table-digest-001 (office-src 0.11.0)

This is the second and last half of blueprint session 4b, built as one
additive release, 0.11.0. One probe ran before any building. You pasted
it back whole: 377 lines, the trailer intact, and all 133 hashed lines
re-verified here. Everything below about bale comes from that probe, not
from bale's docs. The pre-flight said the work fit one session, so I
didn't split it. Nothing was written outside the forecast.

One thing to push back on first, because the brief contradicts itself.
It asks the front sheet to list "the watches' four `cannot evaluate`
lines". The probe shows only two:

- watch 15, the HOLD cause class;
- watch 17, the amendment-accept marker.

The other two are evaluable:

- **Watch 24** reads the aggregate's `members.clarification_self_only`,
  which is the condition itself. bale-src's corpus lists nine sessions
  there, past the threshold of four.
- **Watch 13** was never missing. The read side already corrected it.

So the front sheet names two lines, plus the per-session round count
the watch-24 slip still waits on. If you meant something else by four,
say which, and it's a two-line change.

## What the probe established (2026-10-06, 19:13 UTC)

- **The machine.** WSL2, bale 0.4.45 at ~/.local/bin/bale, Python
  3.12.3, zone America/Indianapolis.
- **office-src** is 0.10.0. HEAD is `9791d95`, 4b-1's sweep, and the
  install is 0.10.0 from that commit (installed 2026-10-06T16:37:24Z), so
  4b-1's `office land` ran `./install.sh`. The tree is clean apart from
  this session's telemetry record. This session is the only one open,
  scope `["."]`. The outbox lists 16 requests; 11 are applied.
- **home-office**: only the plan-4b sitting is open, read-only. Three
  sessions in all, and no `drafting-table/` yet.
  - The notepad holds the founding page and the sitting's three pages.
  - Each sitting page was filed by a commit titled `office start: the
    sitting's words from SID's brief`. The third page went in at
    15:06:27 EDT, when this session went out.
- **`bale stats --json --since DATE`**:
  - It takes an ISO date only. A timestamp is refused with exit 1:
    `--since must be an ISO date (YYYY-MM-DD); got '2026-10-06T00:00:00'`.
  - `filters.since` echoes the date bale applied.
  - Membership is by `created_at`. The 2026-10-05 window holds 4b-1, its
    HOLD and its apply. The 2026-10-06 window holds this session alone.
    The 2026-10-07 window is empty: `classes` is `{}` and `doc_epochs`
    is `{}`.
  - It composes with `--work-class`, in that order.
- **What the catalog reads, in real numbers:**
  - office-src has 4 forecast entries untouched since 2026-10-01, which
    would fire watch 13's threshold of 3.
  - ironwood's unparsed share is 0.07 (4 of 55); bale-src's is 0.08
    (22 of 284).
  - bale-src lists 9 self-reported rounds with no promoted stamp.
  - bale-src's aggregate prints one stderr warning and exits 0: record
    `2026-07-21-retirement-cleanup-007` carries the agreement word
    `unclaimed`. That is bale-src's data, not ours.
- **bale's commit subjects** have three shapes, in both repos: `[bale
  SID] summary`, `Merge bale SID`, and `[bale sweep SID] REASON`. The
  reason is `applied`, `closed-read-only` or `swept_by SID`.
- **The other projects** home-office scopes are bale-src, ironwood,
  nisaba-src and twine-src, each at ~/NAME.
- **Kept as fixtures:** everything under
  `claude/fixtures/bale-0.4.45/watches/` (with a README):
  - every bale line, in one set per repo;
  - office-src's commit subjects.
- **Read but not kept:** home-office's git lines (its subjects, its
  notepad filings, its page list). They carry the office's own context,
  such as folder names and the founding session's summary, and the
  constraint says office context never lands here. What they showed is
  recorded above.

## Decisions to ratify

1. **The window: from the day after the last `fired` record.** bale's
   `--since` takes a day, so a firing is never counted twice. The cost is
   that a session packed later on the firing day is never seen by that
   watch.
   - A watch that never fired looks from the day of its `opened` record.
   - A watch with neither record looks over bale's whole corpus.
   - Days are the office's; bale compares them with its UTC stamps.
   - Because the window starts after the last fire, a second `--record`
     on the same day finds nothing new, so the filed log never gets a
     duplicate.
2. **Watches are checked once per place.** Each open query watch runs
   for the office's own registry and for each project, one line each:
   `W1 unparsed-share in ironwood: fired: 0.07 (4 of 55) ...`.
   - A query bale cannot answer gets one line for the watch, since no
     place can answer it.
   - One fired record per watch names every place that fired and its
     evidence: the member sids where the catalog names an evidence key,
     otherwise the value.
3. **The catalog's shape.**
   - Each query names its watch number, a `says` line and the surface.
   - `value` is a closed set: share, sum, count, class-rate, class-basis.
     It extracts from declared keys only.
   - `compare` is `above` or `at-least`.
   - A watch's threshold is a number, or `any` (above zero).
   - A query bale cannot answer carries `needs = "<datum>"` and nothing
     else, so the check prints the brief's line verbatim.
4. **Standing lines.** These are the catalog's `standing` queries
   (`claim-basis-split`, `hold-rate-by-class`), computed over bale's
   whole corpus per place. A register entry with `re-trigger: none` that
   evaluates a query is a standing line too (blueprint 1.4, "kept for
   its record"). It is printed as `observed`, never fired, and the
   catalog's own line for the same query is then dropped, so nothing
   prints twice.
5. **"Since the last sitting", as you leaned.** The window opens at the
   commit that filed the latest `notepad/DATE-SLUG.md` page, and the page
   names that page and commit.
   - Note that the founding page (`2026-09-30-founding.md`) has the same
     shape and counts as a sitting's page. I think that is right, since
     the founding was a sitting, but it is your call.
   - An office with no such page counts from its first commit, and says
     so.
6. **How the digest finds the sessions since then.**
   - The candidates are the sids in bale's commit subjects since the
     window opened, plus the sessions open now.
   - Each one's outcome and times come from its dossier, never from the
     subject. Each attempt is placed by its timestamp, so the window is
     exact.
   - Reading every session's dossier would have meant 251 bale calls in
     bale-src before every sitting. That is why I used the subjects as an
     index.
   - A long window reads at most 60 dossiers per place and says how many
     it left unread.
7. **The digest's Versions section** shows:
   - each project's latest release: the last commit that changed a
     VERSION file, the version it wrote, and the session from its
     `[bale SID]` subject;
   - the bale contract-doc epoch its latest sessions were packed under;
   - the installed bale against the floor.

   The bale version per session is still slip 5 ("not on bale's
   dossier"). The blueprint's "version stamped on its latest request"
   is not readable without that slip.
8. **The digest brings the drafting table.** It is a verb that writes
   `drafting-table/digest.md`, so by 0.10.0's rule its first run brings
   the table into an office, in the same commit. In practice the first
   sitting `office start` packs in home-office brings it. Every run is a
   commit, because `written_at` changes each time, as the survey's does.
9. **Only a sitting gets the digest before its pack.** That means a
   read-only office session, including a bundle whose forecast is empty.
   A scoped office session gets none, as the sitting leaned.
   - When the office has a drafting table, a non-bundle sitting carries
     it as `--include drafting-table`.
   - A bundle's pack line is the planner's and the office adds nothing
     to it. The digest is still written, and rides if the bundle includes
     the table.
   - The order is the survey, then the digest, then the pack. Each step
     commits alone and never fails a start.
   - An open session whose forecast holds the drafting table leaves the
     digest as it was, with a warning (tested).
10. **The Next line's order changed, as ruled.** After a session out and
    before unfounded comes `office moves`, which is the order change you
    asked to ratify at review. I also send `office moves` when
    `moves.md` holds lines that do not read, because moves is the verb
    that names them.
11. **Exit codes.** `office watches check` and `office digest` exit 0,
    or 3 when a place could not be read or a log record does not read
    (the reader's convention). `--record` still records what fired when
    another place could not be read.
12. **Catalog keys go through one door.** `Reader.reach` reads a declared
    key path generically, since the queries name their keys as data. It
    refuses an undeclared key, exactly as `Reader.key` does. The read
    side's "declared but never read" test now counts the catalog's keys
    as read. The catalog refuses to load if it names a key the manifest
    does not declare.
13. **The `[bale SID]` subject is declared** under `[surfaces.commits]`,
    `calls = false`. `Consumption.subject_sid` is the one parser, and
    `office_drafting.move_sources` now goes through it. A test reads it
    against the captured subjects: every merged session's work commit
    and sweep is present, and each merged one is applied by its dossier.
14. **The sitting's third page** (in the brief) is home-office's to
    file, and `office start` filed it. It does not land under
    `claude/context/sittings/`, because that is for office-src's own
    sittings.

## Look closely on review

- `office_digest.sessions_since`. The candidates come from the subject
  index, then each attempt's `at` is compared with the window. A session
  held and applied in the window shows under both, which is honest.
- `refresh_digest` in bin/office, and the include it adds in
  `office_bale.start`. The include is added only after the digest ran,
  so the drafting table exists when bale is asked.
- `Consumption.subject_sid`. The work shape `[bale ` is also a prefix of
  the sweep shape, and it is rejected there only because `sweep SID`
  isn't a sid. A test pins that.
- `office_drafting.move_sources` imports `office_bale` inside the
  function, because office_bale imports office_drafting at the top.
- `office_watches.record`. It adds a blank line before the first record
  when the page ends in the template's fence, and appends directly after
  a record. The shell's `check_page` (append-check) runs on it before
  the commit.
- The eye-watch count reads the office's zone through Python's
  `zoneinfo`. The bash side hands it a zone it already resolved (or UTC).
  On this build machine Python has no `America/Indianapolis` link, so
  the tests use a fixed offset, never the machine's zone.

## Slips for bale-src

- **New:** `stats --since` takes a day, not an instant. A window that
  should open at a firing or at a sitting cannot be exact through the
  aggregate. The digest works around it honestly by reading dossiers;
  the watches cannot, since their values exist only in the aggregate.
  Accepting an ISO timestamp would close it.
- **Touched; already in home-office's box, not re-filed:**
  - `suggestion-box/2026-10-03-2-a-hold-cause-class-watch-15-confirmed.md`
    (watch 15 cannot evaluate).
  - `suggestion-box/2026-10-03-4-a-marker-telling-a-deliberate.md`
    (watch 17 cannot evaluate).
  - `suggestion-box/2026-10-03-3-a-real-round-s-self-report-watch-24.md`,
    which narrows again: the aggregate answers watch 24, so only the
    per-session count on the dossier is left, and no watch needs it.
- **Waiting, unfiled, from earlier notes:**
  - `bale unlock --help` and the sweep commit;
  - no after-land hook on bale's side;
  - the `[bale SID]` commit subject is a convention, not a contract. The
    office now declares it in its manifest, so a change fails a test,
    but the slip stands.
- **Seen, maybe nothing:** bale-src's own record
  `2026-07-21-retirement-cleanup-007` carries the agreement word
  `unclaimed`, which bale's aggregate warns about on every run.

## Paths outside the forecast

None. The forecast is the whole repo.

## The suite

`validation.sh` runs the whole suite and says so in
`validation_will_run`, as the brief asks. `VALIDATION_SKIP_SUITE=1`
skips it loudly. Nothing new depends on the machine: the tests set git's
clock where a date matters (`GIT_COMMITTER_DATE`), use a fixed offset
for the one zone sum, and build their own HOME.

The final run: this response's `validation.sh` in a fresh staging copy
of the packed tree, with the response applied and this machine's
`/etc/timezone` and `/etc/localtime` set to America/New_York, so a
non-UTC machine is what the suite met. Every check passed, all ten
claims agree, and all 454 tests passed in 1005 seconds, about 17
minutes. Before the response was applied, every session-specific
assertion failed, with the suite skipped, as they should. Python here
has no `America/Indianapolis` link, which is why New York stood in for
your zone.
After that run I changed one progress line in `validation.sh` (it named
the runtime twice). The script re-ran with the suite skipped and every
other check still passed.

- **New:** `tests/test_watches_digest.py`, 47 tests. They cover the
  captures, the manifest's `--since`, keys and subjects, every query over
  every captured aggregate, the register and log, `office watches` and
  `watches check` end to end, `--record` and the one-writer rule, the
  digest's sections and window, the digest before a sitting (and not
  before a scoped session), and the Next line.
- **Changed:** `test_office.py` (`DECLARED_KINDS` loses `digest`; the
  drafting table's attended and trigger table), `test_read_side.py`
  (catalog keys count as read; `--since` in the argv and coverage
  tests), `test_front_door.py` (`watches-check` is a two-word verb) and
  `test_drafting_table.py` (digest built).
- **Flaky:** my first full run had one failure,
  `test_front_door.TestTourOnATerminal.test_an_interrupt_deletes_the_office_and_says_so`
  ("still running after its last step"). It passed three times alone on
  this tree and twice on the unmodified tree. It drives the tour on a
  pty and sends ^C at a moment that is timing-sensitive. Nothing here
  touches the tour.

## Proposals

### Run the suite's modules side by side by default

- **What:** have `validation.sh` (and a `tests/run.sh` beside it) start
  each test module as its own process, about four at a time, and keep
  the pty-driven classes (the tour, the wizards, the terminal starts) in
  one serial group. A flag (`--serial`) keeps today's one-process run.
- **Why:** the modules share nothing: each test builds its own temporary
  HOME, offices, installs and fake bales. Almost all of the 17 minutes is
  git and `bin/office` subprocesses waiting on each other, not CPU. Four
  ways should bring the run near five minutes and still run the whole
  suite. The pty tests stay serial because the one flaky failure above
  is a timing test.
- **Scope hints:** `validation.sh`'s suite step, a small runner script,
  the README's Tests section. No test changes, except naming the serial
  group.

### A sitting writes the first watches on home-office's drafting table

- **What:** the next sitting that opens on the digest writes the
  watches register from MASTER.md's open watches 1, 13 (closed, kept
  for its record), 15, 17 and 24, with `opened` records on the log. 21
  and 22 need no entry: the digest's standing lines already show them.
- **Why:** until a register exists, `office watches check` prints only
  the standing lines, and the check has nothing to fire on. The catalog
  is the half office-src owns; the entries are the sitting's.
- **Scope hints:** home-office's `drafting-table/watches.md` and
  `watch-log.md`, written by a sitting. This is a content move, not
  office-src work.

### Let `office land` run `watches check` after an applied landing

- **What:** after the after-land actions, `office land` runs `office
  watches check` (no `--record`) and prints any `fired` line.
- **Why:** `watches-check` is declared `after-build` in `verbs.toml`, and
  nothing triggers it yet. A watch on HOLDs is most useful the moment a
  landing changes the count.
- **Scope hints:** `bin/office` `cmd_land`'s end and
  `after_land_summary`. The founding door's session reworks land's
  neighbours, so either that session or the one after it.
