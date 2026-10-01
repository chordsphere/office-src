# office-src

The tool that builds and keeps offices. An office is where you go to
begin work on the projects in its scope: a git repo organized like a
physical office, holding what only you and your sessions may read.
Projects hold what their audience may read. bale carries the sessions;
the office supplies the context that is not the project's own.

office-src is project agnostic. Every office is specific and says why it
exists in its required profile. How offices work is doctrine/OFFICE.md,
which ships with every office session.

## Install

From a clone of this repo:

    ~/office-src/install.sh

That installs the committed tree (HEAD) to ~/.local/share/office-src and
links ~/.local/bin/office to it. `--prefix DIR`, `--bin-dir DIR` and
`--no-link` change that. Run it again to upgrade the install; it replaces
the previous install whole, and refuses a prefix that is not one.

On another machine, clone and run the same line:

    git clone <remote> ~/office-src && ~/office-src/install.sh

Requirements: bash, coreutils, git, python3 (3.11 or later, for tomllib),
all shipped with Ubuntu 24.04. No network, nothing to install. The read
side (below) runs bale when it is on the PATH; without it, every
rendering says bale is missing and the rest of the command works.

`office version` prints the installed version and where it came from.

## Use

    office init ~/offices/home # build an office; prints the founding session's pack line
    office                     # walk in: sessions in flight, the desk, this week, recent notes, slips
    office status              # version, skew, profile, survey age, hung items, catalogs, folders, filed pages, bale, projects
    office survey              # rewrite floor-plan/survey.md, report what changed
    office upgrade             # run pending migrations: dry run, then one commit
    office where               # the office a command here acts on
    office default [PATH]      # this machine's default office

A command acts on OFFICE_ROOT if set, else the office around the working
directory (found by walking up to floor-plan/manifest.toml), else the
machine's default, kept in ~/.config/office-src/default-office. The
first `office init` on a machine sets it.

### Every day

    office note called the bank; rate locks Friday   # a timed line on today's notepad page
    office open                                      # a folder on the desk; asks for what it needs
    office open house-hunt --thread < thread.txt     # ...seeded with the thread that started it
    office desk                                      # in flight, ready in order, parked, candidates
    office week                                      # this week's calendar and its gaps
    office close fix-login                           # to the filing cabinet, done
    office reopen fix-login                          # back to the desk, history and all

Each verb commits only the paths it touched. `office note` works in an
unfounded office and in one that needs an upgrade; it warns and writes.
A folder is named by the date and a slug, and can be named by any unique
part of that name or by its number, `folder 12`.

### Folders: numbers, fields, statuses and gates

On a terminal, `office open` walks you through what you left out: the
title, the size, the lane and the source, four answers, each skippable
with a plain return but the title. Type `?` at any question to have the
field explained. Every question has a flag, so the same folder opens in
one line, and piped input is never asked anything:

    office open fix-login --title "Fix the login" --size small \
        --lane "office-src: bin/" --source "notepad/2026-09-30.md"

| flag | what it records |
|---|---|
| `--size small\|medium\|high` | how big the job is; the desk puts small jobs first |
| `--lane "project: paths"` | the project and paths the job will touch |
| `--source TEXT` | where the job came from: `proposal SID #n`, `rider N`, `ruling ID`, `blueprint ID`, `notepad/...`, or a person |
| `--class CLASS` | bale's work class: code, doc, contract-doc, meta, mixed |
| `--blueprint ID` | the blueprint the folder belongs to |
| `--after GATE` | not before GATE is done: `folder N` (or just N), `blueprint ID`, `agenda N`, `ruling ID`; repeatable |
| `--serializes-after N` | never beside folder N; when both are ready, N goes first |
| `--consumer GATE` | parked for the blueprint or folder that will carry it |
| `--linked N` | related to folder N, without waiting for it |
| `--candidate` | not queued yet: an idea on the desk |
| `--filed --sid SID` | a job done inside a session, filed straight into the cabinet |

`office open --help` explains each. Every folder gets a number, one more
than the highest on the desk and in the filing cabinet, and is cited as
`folder N`; folders from before 0.5.0 keep their names and are never
numbered. While a session open in the office's own bale registry
forecasts the desk, `office open` refuses and names it, so a number is
never minted beside a session that could mint one too.

A folder's status follows its job, and each change is a dated line in
its History:

    office sessions fix-login SID              # the first session recorded opens it
    office sessions fix-login SID --ratified   # the planner ratified its judgment calls
    office sessions fix-login SID --ratified --except "the slug rule, moved to folder 14"
    office close fix-login                     # done
    office close fix-login --into 14           # absorbed into folder 14, which points back
    office close fix-login --split 14,15       # split into those folders
    office close fix-login --retired "premise was wrong"
    office reopen fix-login                    # a done folder, back on the desk, open

`office desk` computes the order; nobody writes one. In flight: the
folders a session is open for. Ready: queued folders whose gates are all
met, by `serializes after`, then small first, then number, each saying
when a gate cleared since you last walked in. Parked: grouped under what
each waits for, with that gate's own status; a gate on a blueprint, an
agenda item or a ruling waits until the drafting-table verbs can read
them. Candidates last. A gate that names nothing, or a cycle, prints as
an error line naming the folders; no folder is ever dropped. Walking in
shows In flight and the first three ready folders.

`office status` checks that every folder's status agrees with the last
line of its History that changed it, and walks git's history of every
filed page (the notepad, and the drafting table's ledgers once an office
has one) for a commit that did more than add at the end. It reports and
exits 0; `office init` refuses to build from an install whose catalogs
have a defect.

### Which sessions worked on a job

When you pack a session for a folder by hand, pipe bale's report into
the folder, so the id is never typed:

    bale pack --json --include desk/2026-09-24-fix-login "Fix the login redirect" | office sessions fix-login -

`office sessions fix-login` lists what is recorded, and under each id
what bale records about the session: its outcome, dates, claims beside
verdicts and exchange rounds. The folder keeps the id and any words you
add with `-m`; it never copies what bale records about the session.

### The projects an office scopes, and what bale records about them

    office projects                          # the projects this office scopes
    office projects add office-src ~/office-src   # add one (asks on a terminal for what it was not given)
    office projects --ledger                 # trust ledger per project and work class
    office projects --landed bin/office      # the last applied session that landed a path
    office projects office-src --versions    # the version trail of one project

The floor plan's [projects] table names each project and the path of its
repo on this machine; `office projects add` writes it, and checks the
path is the top of a git repo bale runs in. Walking in shows the sessions
open in those projects and the folder whose Sessions section names each.
Everything here is read from bale's `--json` surfaces in each project and
rendered on every run, never copied into the office; the bale verbs,
flags and keys it reads are listed in share/bale-consumption.toml, with
the bale version they were written against, and `office status` says
when the installed bale is older than that.

### Hung items

`office init` writes a `bale.toml` whose include group pulls the office's
hung items (the profile and the survey, and whatever a renovation hangs)
into any pack whose includes touch the office. Pack lines need no
`--include` list for them. `office status` says when bale.toml no longer
matches the floor plan.

## Layout

| path | what |
|---|---|
| bin/office | the command (bash) |
| lib/office_helper.py | TOML, profile, survey, migration and floor-plan helpers (python3, standard library) |
| lib/office_bale.py | the read side: the only code that runs bale, through its --json surfaces, and the renderings built on it, the desk's groups and the one-writer rule among them |
| doctrine/OFFICE.md | how every office works |
| doctrine/checks/ | checks a session pastes into its validation; rides with the doctrine into every office session. filed-append-only.sh proves a filed page only grew at its end |
| share/spaces.toml | every space an office can have; the base ones are the default floor plan; a space files itself whole or as a list of paths |
| share/profile-shape.toml | the profile's required sections |
| share/bale-consumption.toml | every bale verb, flag and JSON key the office reads, and the bale version they were written against |
| share/verbs.toml | what each verb ships, where it lands, whether a person must be present and what may set it off; a session kind with no declared landing may not run unattended |
| templates/ | profile, folder, clipboard series and sheet, handbook chapter, rolodex card, suggestion slip, notepad page; blueprint and close report; the drafting-table pages (drafting-table-*.md), copied in by the renovation that adds the space |
| migrations/ | one file per breaking release; format in migrations/README.md |
| RELEASES.md | release notes |
| tests/ | the test suite |

Nothing here is copied into an office except the profile stub, which is
the office's own from the moment it is written.

## Versions

VERSION holds the release, MAJOR.MINOR.PATCH. A release is breaking
exactly when it ships a migration; every other release needs nothing
done in any office. Each office records the release it was built from
and the one it was last migrated to, and the command refuses loudly when
the two sides disagree in a way it cannot work across.

Only `office upgrade` writes an office's version stamp. A breaking
release that needs judgment ships a renovation migration declaring what
must be true once the renovation has landed; upgrade prints the
renovation's pack line, the session does the work, and the next run of
`office upgrade` checks the declaration and stamps the office.

## Tests

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

The suite builds offices, installs and synthetic migrations under
temporary directories and never touches your home directory or offices.
bale need not be installed: the read side's tests put a fake bale first
on the PATH that replays real bale output captured by a probe, kept in
the development record, and refuses anything it did not capture.
