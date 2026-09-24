# Migrations

A release is breaking exactly when it ships a migration here. Additive
releases ship none, and every office keeps working without doing
anything.

One file per breaking release, named for the release:

    migrations/0.2.0.toml
    migrations/0.2.0.sh      (script kind only)

The TOML file:

    version = "0.2.0"          # must match the file name
    kind = "script"            # script | renovation
    summary = "One plain-language line; it goes in the upgrade commit."
    script = "0.2.0.sh"        # script kind: run by bash from the office root
    goal = "..."               # renovation kind: the renovation session's goal

A script migration runs with the office root as its working directory
and OFFICE_ROOT and OFFICE_MIGRATION set. It changes live structure
only. It must never touch filed paper (spaces with filed = true in the
office's floor plan); office upgrade checks after every migration and
refuses one that did. It must be safe to run on a scratch clone, because
office upgrade rehearses every migration there first.

A migration that needs judgment, such as a new required profile section,
is a renovation. office upgrade stops before it and prints the pack line
for a renovation session, which sets migrated_to when it lands.

A migration's version is never newer than the install's VERSION.
