# Releases

A release is breaking exactly when it ships a migration (migrations/).
Each breaking release's migration carries the plain-language summary
that office upgrade writes into the office's commit.

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
