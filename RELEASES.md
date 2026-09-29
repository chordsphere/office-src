# Releases

A release is breaking exactly when it ships a migration (migrations/).
Each breaking release's migration carries the plain-language summary
that office upgrade writes into the office's commit.

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
