# Notes: 2026-11-08-m10-status-more-001, what the read side has been missing (office-src 0.53.0)

Four of the ten items shipped: 1 and 2 (your own, the friction report's
items 10 and 16) whole, then 8 (the handoff offered) and 6 (one spelling
for an unreadable project). The seam is used: 5, 3, 4, 7, 9 and 10 are
not here, and each is a proposal below with what I read for it. That is a
deviation from the brief's seam in one place: it grouped "8, 5 and 6", and
I shipped 8 and 6 and left 5 (decision 9). Every path is inside the
forecast, so there are no departures to admit. There was no context
compaction this session.

The tree I was handed is 0.52.0, the whole tree. The anchors I used were
all there, moved as the brief warned: cmd_status 1419, status_lines 2560
(0.49.0's 2526), sandbox_status_line 2641, next_move 1757, unread_line
741-742, in_flight's line 927, the ledger 2151, landed 2192, versions 2239
(each about six lines on), the problems list 5597 (0.49.0's 4826), the
sessions line 2067, open_words 1359, delivery_move 1708, waiting_lines
2482, job_flag and job_waiting_words 2335-2346, office_home's item 723,
office_map's next_lines 475. None is gone.

## Decisions

Numbered so you can ratify or correct each by number.

1. **Which tools, and how they are asked.** The read asks a shell for
   node, npm, yarn, pnpm and bun (office_host.TOOLCHAIN_TOOLS), and only
   for those whose quoted name appears in package.json (node also for a
   .nvmrc). An engines key for anything else (vscode, say) is said under
   OFFICE_DEBUG only: the office does not guess how to ask an unknown
   program its version. One script (office_host._TOOLCHAIN_READ) prints
   the versions, the .nvmrc's first line and package.json's text; it uses
   shell builtins only, past the tools it asks for, so a login shell with
   a bare PATH still answers. On this machine it runs as `bash -lc SCRIPT
   office-toolchain PATH TOOLS...`; on a host as `sh -c ...` through the
   project's shell, which is the login shell already, riding after the
   sandbox read on status's `bale --version` call. Same connection count.
2. **The range reader is npm's grammar as projects write it**:
   comparators, bare and partial versions, x-ranges and `*`, carets
   (with npm's 0.x rules), tildes, hyphen ranges, a space meaning both
   and `||` meaning either. A pre-release tag, or anything else, is a
   RangeError, said as `proj: package.json engines says node "latest",
   which the office cannot read as a range, so it does not say whether
   its shell's meets it`. The version a tool prints is its first X.Y.Z.
3. **Cheap extra manifests: .nvmrc only.** A version (24, v24.1, 24.1.0)
   reads as a range for node; an nvm alias (lts/*, node, stable,
   lts/iron) is said as one the office cannot read. I left .tool-versions
   and pyproject's requires-python out: each needs a second grammar (asdf
   names, PEP 440) and a second tool vocabulary, and neither is in your
   friction report. A proposal below.
4. **A local project's read is a local process, every status.** For a
   clone with neither file the script exits at once; with one, it runs a
   login shell and one `--version` per tool named. It reads the machine's
   /etc/profile as bale's own `bash -lc` does, which is the point (the
   suite's tests run it with a ~/.bash_profile of their own that sets the
   whole PATH, so no node of the test machine's is found).
5. **The profile rule.** A line says something is not built when it has
   `not built`, `not yet built`, `not built yet`, `isn't built` (either
   apostrophe), `hasn't been built`, `not been built` or `unbuilt`. It
   names a verb or kind when it has `office VERB`, VERB in backticks
   (alone or after `office `), VERB followed by session(s), verb(s) or
   kind(s), or a session kind on its own (`project sessions`,
   `office-session`); a hyphen may be a space. A verb's bare word is not
   enough: open, land, desk, status, map, note and most of the others are
   ordinary words, and in a personal office that buys houses and
   renovates, "the desk is not built yet" is about furniture. The leftmost
   name wins. A kind is built when any verb of it is. The two kinds are
   office-session and project-session; script is not a capability anyone
   says is missing. Every line of the profile is read, comments included.
6. **The stale line's wording adds the line's words**, which the brief
   asked for and its template didn't show: `  profile.md line N says NAME
   is not built; office-src VERSION builds it (share/verbs.toml): WORDS`,
   under the `profile:` line. It's a new helper subcommand,
   `profile-built`, in status's one batch. A profile or catalog that
   can't be read says nothing more than the profile line already says (the
   call's stderr is dropped, as the other -q calls' are).
7. **Your own line may not match.** I could not find the work office's
   actual "not built yet" line in anything the request carried. If it said
   something like "a project on a host is not built yet", it names no verb
   or kind and is not said, as the pin requires. If it said "project
   sessions on docker.medgen are not built yet", it's said. Tell me the
   line's words and I'll say which. A proposal below (a `words` list per
   verb in verbs.toml) would catch the first form.
8. **The handoff offer names the response**: `office start N --handoff
   response-SID.tar.gz`, the name a browser saves it by. handoff_check
   resolves a bare name here and then in the downloads, so the line works
   from your home directory once the response is saved. A job's bailout
   counts only while its page names no session (job_bailed). I also
   changed deliver's waiting-job line (office_deliver waiting_merge_lines
   and waiting_undo_lines), which the brief didn't list but which is
   another place a waiting job is offered.
9. **Item 5 left at the seam with 3, 4, 7, 9 and 10.** Items 1, 2, 8 and
   6, with the docs and a suite run per stage, filled what I could verify
   with a margin. The asks' three lines are three different reads (a rank
   rule in next_move, a git log in the digest, a record scan in status)
   and would each need their own tests, so I stopped before them rather
   than ship a part of 5.
10. **The spelling is `NAME: not read: WHY`**, as the brief preferred.
    unread_line is now the one writer for the walk-in's In flight, the
    ledger, landed, versions, the land plan's problems and the digest's
    two lines. sessions' per-session `    cannot read: ...` under a
    recorded sid is about bale's records for one session, not a project,
    and is unchanged. Each rendering says a project once (each loop reads a
    project once). The paused line goes through the same helper, so the
    ledger, landed and versions now say a paused project's one line where
    they'd have said `cannot read: NAME: paused ...` if they ever got one.

## The suite

- Baseline, the unchanged 0.52.0 tree: the fast tier with test_read_side,
  393 tests, OK, 62 s. The whole suite at 0.52.0 is 1462 tests (the brief's
  count; I did not rerun it whole on the unchanged tree).
- After items 1 and 2: 1488 tests; one failure, test_suite_clock's rule
  that a module importing office_helper compiles no pattern at its top. I
  had used re.compile for NOT_BUILT_RE; it's a LazyPattern now.
- The finished tree: 1495 tests, 792 s on two CPUs, with one failure, a
  sixth pinned `office-src: cannot read:` in test_read_side's walk-in test
  that my first pass missed (its words end at the colon). Moved; that
  module, and the slow set below, pass on the finished tree.
- New: tests/test_status_more.py, 33 tests (the range reader, the lines,
  the read itself, status on a project here and on a host with the
  connection counted, the profile rule and status's line with the profile
  and HEAD unchanged, the handoff offer at each site and in status and the
  walk-in). Touched: tests/test_read_side.py, test_project_on_host.py and
  test_watches_digest.py, whose pinned `cannot read:` words moved to `not
  read:` (six lines). No test hard-codes a day or a VERSION, and nothing
  is named `m10_`. tests/fast-tier.toml is unchanged: no verb was added.
- validation.sh runs the fast tier with test_status_more and test_read_side,
  and behind `--slow` the whole of the nine modules this change reaches.
  In a staged copy (0.52.0, files/ overlaid, apply.sh run) every check
  passed: 1m12s without `--slow`, 3m44s with it. On the unmodified tree
  every change-dependent assertion fails, as do the tests; the four that
  pass there (the doctrine's core and banner, bin/office's exec bit, the
  new tests' pins, vacuous with no module) guard what must not move.
  Nothing was written in the staged tree but the script's own logs.

## Walkthrough

### What changed

- `office status` reads a project's toolchain: package.json's engines and
  a .nvmrc against what the project's own login shell finds, here under
  `bash -lc` and on a host in the connection that already reads bale's
  version (office_host toolchain_argv, read_toolchain, parse_range,
  satisfies, nvmrc_range; office_bale toolchain_lines, in status_lines).
- `office status` names a profile line that says a built verb or kind is
  not built (office_helper profile-built, stale_profile_lines,
  named_in_line, catalog_names; bin/office cmd_status prints it under the
  profile line).
- A merge or undo job a session bailed out of is offered its handoff, not
  a fresh session, on status, the walk-in's desk and Next lines, the home
  screen, the map and deliver's line (office_bale job_bailed,
  job_start_words, job_start_line).
- An unreadable project is `NAME: not read: WHY` everywhere (unread_line).

### Why

Setting up the work office's toolchain was hand steps with nothing to say
when they were missing: the first you'd hear was a validation failing in
bale's shell. A profile line written to be caught later was never caught.
A bailed job's offer sent a session from scratch while land's own line
said to hand it off. And two spellings for the same failure read as two
different things.

### How to explain each piece

- Status asks the project's shell what bale's shell will find, and only
  speaks up when something is missing or too old.
- Status reads the profile, never writes it, and only names a line that
  names something the install's catalog says it has.
- A job that knows its session bailed offers the handoff, the way land
  does.

### Questions a reviewer will ask

- *Why not read package.json on this machine for a local project, and
  only shell out for versions?* One script both ways keeps the local and
  hosted reads the same, and it costs one process.
- *Does a hosted status make another connection?* No: the read rides the
  `bale --version` call with the sandbox read; the hosted test counts it.
- *Why not match a verb's bare word?* Decision 5.
- *Why does the offer name response-SID.tar.gz when the file may not be
  saved yet?* That's the name handoff_check looks for, here and in the
  downloads; if it isn't there, start says so before anything runs.

### A hand test

1. In a project on this machine, put `"engines": {"node": ">=99"}` in its
   package.json. `office status` says `NAME: needs node >=99
   (package.json engines); its shell finds node X.Y.Z`. Change it to
   `">=1"`: nothing; `OFFICE_DEBUG=1 office status` says it meets it.
2. On the work office's hosted project, the same, and check with
   `OFFICE_DEBUG=1` that the read went in the one `bale --version`
   connection.
3. Add a line `- project sessions on a host are not built yet` to the
   profile's Site section, commit it, and run `office status`: the line is
   named with its number, and `git status` stays clean.
4. On a folder whose merge job a session bailed out of (its merge.md has
   `- bailed: SID`), check `office status`, `office`, the home screen and
   `office map N` all offer `office start N --handoff
   response-SID.tar.gz`.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: status-more

### Commit

Say a project's missing tools and a stale profile line in office status

office status now asks each project's own login shell for the tools its
package.json engines (or .nvmrc) names, here under bash -lc and on a host
in the connection status already makes, and says a tool that is missing
or outside its range; a range it cannot read is said, never guessed. It
names a profile line that says a verb or session kind is not built when
the install builds it, and never edits the profile. A merge or undo job a
session bailed out of is offered office start N --handoff on every screen
that offers a waiting job, in place of a session from scratch. A project
a rendering cannot read is said one way everywhere: NAME: not read: WHY.

### Review

Say a project's missing tools and a stale profile line in office status

Look at office_host's toolchain read and range reader, office_bale
toolchain_lines and status_lines, office_helper stale_profile_lines and
named_in_line, and office_bale job_start_words (notes, decisions 1, 2, 5
and 8). To try by hand, follow the walkthrough's hand test. Deliberately
untouched: the asks' three lines, the sandbox line in a container, the
listed offices, the map's paused folders, a host ride's size and the
walk-in's and home screen's tables, all proposed in the notes.

## Structure

- title: Say what the read side has been missing, first half
- size: medium
- goal: Say a project's toolchain and a stale profile line in office status, offer a bailed job its handoff, and spell an unreadable project one way: office-src 0.53.0

## Handbook

### office-src

- office status reads a project's toolchain (0.53.0): office_host.toolchain_argv runs one script with the clone's path (bash -lc on this machine; sh -c through the project's shell on a host, riding status's bale --version call after the sandbox read); read_toolchain parses it; office_bale.toolchain_lines says a tool missing or outside its range
- the tools asked for are office_host.TOOLCHAIN_TOOLS (node, npm, yarn, pnpm, bun), each only when package.json names it in quotes (node also for a .nvmrc)
- office_host.parse_range reads npm ranges (comparators, partials and x-ranges, ^, ~, hyphen ranges, spaces, ||); a pre-release or anything else is a RangeError, said as a range the office cannot read
- office status's profile-built call (office_helper.stale_profile_lines) names a profile line that says a verb or kind is not built when share/verbs.toml builds it; a verb is named as `office VERB`, in backticks, or followed by session, verb or kind, and a session kind on its own
- a waiting job's offer is office_bale.job_start_words: `--handoff response-SID.tar.gz` for a job page with `- bailed: SID` and no session, else job_flag
- an unreadable project is `NAME: not read: WHY` in every rendering (office_bale.unread_line)
- tests/test_status_more.py holds 0.53.0's tests

#### Front sheet

office-src 0.53.0 says more on `office status`. For each project whose
package.json names engines (or that has a .nvmrc), it asks the project's
own shell, the one bale runs in, for each tool and says a tool missing or
too old; on a host it rides the connection status already makes. It names
a line of the profile that says something is not built when the install
builds it, and never edits the profile. A job a session bailed out of is
offered its handoff everywhere, and an unreadable project reads `NAME: not
read: WHY` everywhere. Additive: no migration.

## Proposals

The six items left at the seam, each with what I read, then two of my own.

- **What:** item 5, the asks' three lines: next_move names an ask that is
  out when nothing on the desk outranks it; the digest lists the asks
  filed since the last sitting from their `office ask:` commits; status
  names an orphaned ask record with its removal line. **Why:** left at the
  seam (decision 9). The rank I'd propose: after the desk's moves and a
  waiting job or delivery (delivery_move), before a drop to sort, since an
  ask out is waiting on you, like a delivery. **Scope hints:**
  office_bale.next_move (1757) and delivery_move; office_digest render
  (the window's base, git log --grep '^office ask:'); office_ask asks_out
  and status_line, which status already calls as `ask:out-lines --status`.
- **What:** item 3, the sandbox line for a project on this machine when
  the survey's class says it is a container. **Why:** left at the seam.
  status_lines reads the sandbox for hosted projects only, through
  ohost.sandbox_argv; a local project could run the same argv with
  run_in (no host). I didn't read where the survey's class lives in the
  survey page. **Scope hints:** status_lines' local branch, beside the
  toolchain read; floor-plan/survey.md's `class:`.
- **What:** item 4, the listed offices in status. **Why:** left at the
  seam; office_helper.offices_fact (the survey's Machine fact) already
  reads listed_offices and skips a root that is no longer an office.
  **Scope hints:** a status line from listed_offices' second value.
- **What:** item 7, the map's paused folders. **Why:** left at the seam;
  not read. **Scope hints:** office_map Reading.state, project_row.
- **What:** item 9, a host ride's size on start's screen. **Why:** left
  at the seam; not read. **Scope hints:** office_host._RIDE_SCRATCH_SCRIPT,
  office_bale.pack_host_rides.
- **What:** item 10, the walk-in's In flight and the home screen's
  Projects block in the map's table shape. **Why:** left at the seam, as
  the brief said it would be. in_flight's lines now come through
  unread_line for an unreadable project, so a table's row for one can
  take that text. **Scope hints:** office_bale render_in_flight,
  office_home render_page.
- **What:** a `words` list per verb in share/verbs.toml, the phrases a
  profile might use for it ("a project on a host" for the hosted verbs),
  read by named_in_line beside the name. **Why:** decision 7: your own
  stale line may have named a capability, not a verb, and the rule can't
  see it. **Scope hints:** share/verbs.toml (and catalog-check's VERB_KEYS,
  which would take the key as optional), office_helper.named_in_line.
- **What:** .tool-versions and pyproject's requires-python beside
  engines. **Why:** decision 3: cheap to read, but each needs its own
  grammar; worth it once a project uses one. **Scope hints:**
  office_host._TOOLCHAIN_READ and a second parser beside parse_range.
