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
all shipped with Ubuntu 24.04. No network, nothing to install.

`office version` prints the installed version and where it came from.

## Use

    office init ~/offices/home # build an office; prints the founding session's pack line
    office                     # walk in: the desk, this week, recent notes, slips
    office status              # version, skew, profile, survey age, hung items
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
    office open fix-login --title "Fix the login"    # a folder on the desk
    office open house-hunt --thread < thread.txt     # ...seeded with the thread that started it
    office desk                                      # open folders and their next moves
    office week                                      # this week's calendar and its gaps
    office close fix-login                           # to the filing cabinet
    office reopen fix-login                          # back to the desk, history and all

Each verb commits only the paths it touched. `office note` works in an
unfounded office and in one that needs an upgrade; it warns and writes.
A folder is named by the date and a slug and can be named by any unique
part of that name.

### Which sessions worked on a job

When you pack a session for a folder by hand, pipe bale's report into
the folder, so the id is never typed:

    bale pack --json --include desk/2026-09-24-fix-login "Fix the login redirect" | office sessions fix-login -

`office sessions fix-login` lists what is recorded. The folder keeps the
id and any words you add with `-m`; it never copies what bale records
about the session.

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
| lib/office_helper.py | TOML, profile, survey and migration helpers (python3, standard library) |
| doctrine/OFFICE.md | how every office works |
| share/spaces.toml | every space an office can have; the base ones are the default floor plan |
| share/profile-shape.toml | the profile's required sections |
| share/verbs.toml | what each verb ships and where it lands |
| templates/ | profile, folder, clipboard series and sheet, handbook chapter, rolodex card, suggestion slip, notepad page |
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
