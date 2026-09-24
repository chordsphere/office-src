# 2026-09-24-office-src-verbs-002: notes

## Briefing

**The planner's page names chordsphere and docker.medgen, and office-src
must name no office. How do both hold?**
The record lives under `claude/`, where bale-src keeps its record (the
probe showed `claude/MASTER.md`, `claude/INDEX.md` and `claude/context/`
there), and where office-src's archived responses already sit.
`install.sh` ships only the tool's directories, so nothing in `claude/`
reaches an install or an office.

The agnostic rule is enforced two ways:

- The text test scans only the tool's directories.
- Validation adds a grep over everything shipped.

The page is at
`claude/context/sittings/2026-09-23-office-construction-001.md`. Its
sha256 matches `9c804c7d...a64` and is asserted in validation and in the
suite. The front sheet sits beside it, and `claude/INDEX.md` maps the
record. DOCS.md has no category for "a sitting's words, verbatim"; I made
`sittings/` one. Please ratify it or rename it.

**Is the include group legal?**
Yes, and it's done for newly built offices. The probe read bale-src's
`tests/test_include_group.py`, `bale_config.py`, `bale_pack.py` and
BALE.md's board-64 paragraph. What they establish:

- The group engages when a pack's includes intersect any trigger.
- Directory triggers cover their subtrees.
- A dangling pull refuses the pack, but only when the group engages.

I never needed `.` as a trigger, which is still unverified. init writes
`bale.toml` with:

- triggers: the office's spaces;
- pulls: the hung items;
- only paths that exist on disk.

So any pack that includes anything in the office ships `profile.md` and
the survey. The founding line is now `--include floor-plan --write
profile.md notepad floor-plan`. `office status` reports when `bale.toml`
drifts from the floor plan.

One assumption is untested by bale's suite: a *file* trigger
(`profile.md`). The tests exercise directory triggers only. The
implementation treats trigger entries as paths, so I expect it to work.
The founding line doesn't depend on it, because it includes
`floor-plan`, a directory.

**Why is 0.2.0 breaking when no office exists?**
Printed pack lines now rely on the include group. An office built by
0.1.0 has no `bale.toml`, so its packs would silently thin, and silently
thin is the thing to avoid. Migration 0.2.0 is a script. It writes
`bale.toml`, appends the group to an existing one, or leaves an existing
`[pack]` alone and says so.

It is the runner's first real exercise. The suite runs it on a
0.1.0-shaped office and checks four things:

- survey refuses while the office is behind;
- note warns and writes;
- upgrade lands one commit;
- status then reports the group matches the floor plan.

## Decisions to ratify

- **Recording session ids: `office sessions FOLDER -`.** It reads a `bale
  pack --json` report on stdin, and `-m` adds the occupant's words. A
  plain id also works. With no id it lists what's recorded. `record_session`
  in `bin/office` is the step the session verbs will call.
- **The pack report's key.** The probe saw `"session_id": sid` in
  `bale_pack.py`, but it did not read `format_pack_json`'s docstring,
  which owns the key contract. The reader tries `session_id`, then `sid`,
  then a single id-shaped value, with a warning. If it finds none it
  refuses and names the keys it saw. It never records a guess silently.
- **Capture skew.** `office note` warns and writes when the office is
  behind, as ruled, and also when it is ahead of the install. The ruling
  named only "behind". Its principle, "instant and dumb", seemed to cover
  both, and a note's format doesn't depend on the release.
- **ASCII.** Non-ASCII in the occupant's words becomes a backslash
  escape (`\xe9`, `\u2014`), with a warning. This is lossless and keeps
  the office ASCII. The alternative is verbatim UTF-8 in the notepad,
  which the constraint rules out as I read it.
- **Folder shape.** A folder is `desk/DATE-SLUG/` holding `folder.md`,
  plus `thread.md` when opened with `--thread`. `office desk` shows the
  Next section's first written line. The template's own placeholder
  shows as "(not written yet)".
- **Notepad shape.** `office note` appends `- HH:MM text` to
  `notepad/DATE.md`, dated in the floor plan's timezone. A sitting's
  words go on their own page, `notepad/DATE-SLUG.md`, per the doctrine.
- **Commits.** Every script verb commits exactly the paths it touched.
  `close` and `reopen` move whatever is in the folder, including
  uncommitted edits, as one commit. A verb that can't commit warns, and
  the change stays on disk.
- **The calendar format** is new, because `office week` needed one. It is
  two bullet pages:
  - `calendar/plan.md` holds `- DATE HH:MM title` and
    `- every DAY HH:MM title`;
  - `calendar/record.md` holds `- DATE [HH:MM] title: what happened`.
  
  A gap is a past planned item with no record that day starting with its
  title. Bullets that match neither shape are reported, never dropped.
  It's in doctrine §5. This is the design choice most likely to want
  changing once a real calendar exists.
- **The stamp rule.** A renovation migration must carry a `[landed]`
  table with `paths` and/or `profile_sections`; one without it refuses
  to load. There is no script form of the declaration. That would give a
  check a way to write, which is what the rule exists to prevent.
- **Walking in** is read-only. It shows:
  - the name and root;
  - the date and time in the office's zone;
  - whether the office is founded and current;
  - the desk, the week, the last three notes and the slip count;
  - the verbs to reach for.
  
  With no office anywhere it shows help plus one line pointing at `office
  init`.

## Watch on review

- `find_folder` matches any unique part of a folder's name, so `office
  close login` works. When more than one folder matches, it refuses and
  lists them.
- The founding goal is one sentence, as bale wants, but a long one.
- `office open` refuses in an office behind a breaking release; only
  capture is lenient. That follows the ruling's letter.
- shellcheck is still not installed on chordsphere (probe), so it's
  claimed `untested` and validation will `[SKIP]` it.

## What the probe established

It ran on chordsphere and pasted back complete: 585 lines, matching its
trailer.

- **The machine.** Ubuntu 24.04.2 on WSL. shellcheck is absent. bale is
  at `~/bale/bin/bale`.
- **bale-src's include group.** It is three flat `[pack]` keys:
  - `include_group` (the name);
  - `include_group_triggers` (repo-relative);
  - `include_group_pulls` (repo-relative).
  
  The rules:
  - engagement is read-side only;
  - the whole-tree default include engages every trigger and adds
    nothing;
  - a dangling pull refuses only on engagement;
  - a half-configured group refuses;
  - `--no-include-group NAME` opts out loudly.
  
  bale-src's own group is `release-surface`.
- **`--json`.** The pack report adds an `include_group` key (v0.4.40).
  `"session_id"` appears at `bale_pack.py:1237`. The key contract lives
  in `format_pack_json` in `bale_report.py`, which I did not read.
- **office-src.** On `master`, tagged
  `applied/2026-09-24-office-src-core-001`, tree clean apart from this
  session's telemetry file. `claude/responses` and `claude/telemetry`
  are tracked. No install exists yet at `~/.local/share/office-src`.
- **Probe scope.** The probe listed depth two with `.git`, `.bale` and
  `__pycache__` pruned. It grepped only named files and one-level globs,
  and ran no bale command.

## Front-sheet material

This now lives in office-src's own record, at
`claude/context/front-sheet.md`. It covers what the tool does, recent
changes for 0.1.0 and 0.2.0, known problems, and likely questions. It
replaces "lands in the workshop" from the core session's notes. The
seed's own front-sheet material moves in with its generic half.

## Proposals

**Show office session: build on the verbs, not beside them.**
*What:* seed the sample content through the verbs themselves:
`office note`, `office open`, `office sessions` with a fake
`--json`-shaped report, and a calendar in the two-page format with one
deliberate gap. *Why:* the show office then exercises the real formats,
and walking in shows every section populated. *Scope hints:*
`bin/office`, the calendar format in doctrine §5.

**Show office session: it must never take the default.**
*What:* `office init --no-default` exists already. The show office's
builder should pass it, and a test should pin it. *Why:* brief §7; on
chordsphere it will be the first office built. *Scope hints:* `cmd_init`
in `bin/office`.

**Show office session: walking in should mark a show office.**
*What:* a marker in the floor plan, say `[office] show = true`, that
walking in prints loudly. *Why:* the show office is "clearly marked", and
walking in is where you'd look. *Scope hints:* `walk_in` and
`render_manifest`.

**bale-src: name the pack report's session-id key in a doc the tools
ship.** *What:* state in TARBALL.md §3.4's `--json` row, or in a doc that
travels, which key carries the minted id. *Why:* office-src reads it and
had to infer it from source. The key contract lives in a docstring no
request carries. *Scope hints:* `format_pack_json` in `bin/bale_report.py`
and TARBALL.md §3.4.

**bale-src: say whether a file may be an include-group trigger.**
*What:* one test in `tests/test_include_group.py` with a file trigger.
*Why:* offices use `profile.md` as a trigger, and bale's suite pins only
directory triggers. *Scope hints:* `evaluate_include_group` in
`bin/bale_pack.py`.

**Next office-src session: renovations keep bale.toml in step.**
*What:* when a renovation adds a space or hangs an item, the renovation
session updates `bale.toml`. A helper verb such as `office rehang` could
regenerate it from the floor plan. *Why:* status reports the drift, but
fixing it is currently a hand edit, which is bookkeeping. *Scope hints:*
`include_group` in `lib/office_helper.py`.

**Next office-src session: the pack report's `include_group` key could
confirm hung items shipped.** *What:* when `office sessions` reads a
report, warn if `include_group` is null, meaning the pack never engaged
the group. *Why:* it would catch a pack from outside the office's spaces
that shipped without the profile. *Scope hints:* `sid_from_pack_report`.
