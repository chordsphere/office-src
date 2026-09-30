# Releases

A release is breaking exactly when it ships a migration (migrations/).
Each breaking release's migration carries the plain-language summary
that office upgrade writes into the office's commit.

## 0.4.0

Additive: no migration, nothing to do in any office. An office without
a [projects] table keeps working and says it scopes no projects.

The read side. An office names the projects it scopes in its floor
plan's new [projects] table, a name and the path of each project's repo
on this machine, written by the new verb: `office projects` lists them
and `office projects add NAME PATH` adds one, a wizard on a terminal
that asks for what it was not given, refuses without it when piped, and
checks the path is the top of a git repo bale runs in (a .bale/
directory or a bale.toml), saying which it found. office init writes no
table; the founding session or the occupant adds the projects.

lib/office_bale.py is the reader: the only code that runs bale, through
its --json surfaces only (status, stats, a session's dossier), in the
project's directory with stdin closed, never reading .bale/ and never
writing. share/bale-consumption.toml is its contract with bale: every
verb, flag and key it reads, written from a probe of bale 0.4.45, which
is the floor. office status reports the installed bale against it, a
line and never a refusal, and whether each project in scope can be
read. On it, the renderings: walking in shows the sessions in flight in
the office's projects, each with the folder that names it; `office
sessions FOLDER` shows each recorded session's outcome, dates, claims
beside verdicts and exchange rounds; `office projects --ledger`,
`--landed PATH` and `--versions` render the trust ledger per work class,
the last applied session that landed a path, and the version trail.
Nothing rendered is ever written into an office. The pack report's
session id is read from its `sid` key, which bale's pack contract names;
the guess at an id-shaped value is gone. The doctrine says that reading
is not copying, that where a report and the records part the records
stand, and that a number that can go stale is computed where it is shown.

## 0.3.1

Additive: no migration, nothing to do in any office.

Every verb in share/verbs.toml declares three more keys: lands, what
is guaranteed to exist after the verb succeeds; attended, whether a
person must be present; and trigger, what may set it off, from a closed
vocabulary (manual, before-sitting, after-sitting, after-build, on-hold,
on-correctable-hold, schedule). The rule they carry: a session kind
with attended = false must declare a landing. The catalog also
registers the session kinds the drafting-table blueprint declares
ahead of the command, sitting, chat, blueprint-close, digest, review,
check and retry, every one built = false; cleanup now ships and writes
drafting-table/riders.md. Nothing in the command consumes the keys yet
beyond the check: they are a registry for the shell and for whoever
spawns sessions. The test suite refuses a catalog that breaks the rule,
names a trigger outside the vocabulary or lands a path outside the
verb's writes, and refuses a space catalog whose filed or hung lists
hold anything but pages or globs inside the space, or a hung page that
is also filed. office status reports both from the installed catalogs
in one more line.

## 0.3.0

Additive: no migration, nothing to do in any office.

The drafting-table gets its contents in the install. The space catalog
files a list of paths inside the space (the rulings and evidence
ledgers, the watch log, every blueprint's close report), the first
space that is part live, part filed; office upgrade's filed-paper check
reads the list. Templates for a blueprint and its close report, and a
page skeleton for each drafting-table page: the front page with its
citation table, the agenda, rulings, evidence, watches, the watch log,
riders and desk moves. A renovation copies them into an office when the
space arrives; nothing copies them yet. The folder template gains a
field block under its title, a Riders section and a History section;
office open writes the status and the queued date, the fields it can
fill without guessing, and the first History line. doctrine/checks/
ships filed-append-only.sh, the check a session pastes into its
validation for every filed page it writes: the page's first bytes, as
many as the shipped copy had, hash to what the request stamped. The
doctrine says what the drafting table is, that appending is not
rewriting, that a fact has one home and is cited by id, and that a verb
is a wizard on a terminal with a flag twin for every question.

## 0.2.0

Breaking: ships migration 0.2.0, a script. Offices built by 0.1.0 gain a
bale.toml whose include group makes every pack from the office ship its
hung items. Run office upgrade in each one; office note works before you
do.

The everyday verbs: note, open, desk, week, close, reopen, and sessions,
which records the ids of the sessions that worked on a folder, read from
a bale pack --json report. office with no verb is walking in. office
init writes bale.toml and prints a scoped founding session that lands
the profile, the occupant's words as a notepad page, and the office's
real timezone. Only office upgrade writes the version stamp: a
renovation migration declares what must be true once it has landed, and
a re-run of office upgrade checks it and stamps the office. office
status reports when bale.toml's include group no longer matches the
floor plan.

## 0.1.0

First release: the doctrine, the templates, the profile's required
shape, the space catalog and verb declarations, office init, survey,
status, upgrade, where and default, and the migration runner. No
migrations.
