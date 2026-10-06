# The drafting table

Blueprints for work too big for one folder, and the ledgers around
them. Nothing here is a job: jobs are folders on the desk. What lives
here, page by page:

- blueprints/YYYY-MM-DD-slug/blueprint.md, one arc each: its charter,
  its decomposition into folders, its watch list and its history. Live
  until the arc closes; the charter freezes once it is ratified. The
  ratified line is the charter's last, `- ratified: YYYY-MM-DD, words at
  notepad/PAGE.md` (or `at SID`), with a `ratified` History line; from
  then on the charter's bytes never change, and a charter that must
  change is a new blueprint whose History opens `supersedes: blueprint
  ID`.
- blueprints/YYYY-MM-DD-slug/close.md, the arc's close report, written
  once at close and filed.
- agenda.md, rulings awaiting a sitting. Live.
- rulings.md, the rulings ledger. Filed: append-only.
- evidence.md, the evidence ledger. Filed: append-only.
- watches.md, the watches register, one entry per watch. Live.
- watch-log.md, every firing, re-arm and closure, one record each.
  Filed: append-only.
- riders.md, small work with a named carrier and no folder yet. Live.
- moves.md, desk moves a sitting decided, for the office command to
  apply. Live.
- digest.md, the sitting-open page. Derived: `office digest` rewrites
  it whole on every run, and `office start` runs it just before it packs
  a sitting, so a sitting opens on it; nobody edits it.

Filed pages grow at their end and the bytes already there never change
(doctrine section 15). A fact lands once, on the folder, blueprint or
ledger record it belongs to; everything else cites it by id. Closed
blueprints stay here; nothing is condensed.

## Citations, for sessions

One form per kind of thing, so every pointer resolves.

| thing | cited as | resolves to |
|---|---|---|
| a folder | `folder N` | the folder whose number is N, desk or cabinet |
| a blueprint | `blueprint YYYY-MM-DD-slug` | `drafting-table/blueprints/YYYY-MM-DD-slug/` |
| a ruling | `ruling YYYY-MM-DD-slug` | its record in `rulings.md` |
| an evidence entry | `evidence N` | its entry in `evidence.md` |
| a watch | `watch WN` (or `WN` in the log) | its entry in `watches.md` |
| a rider | `rider N` | the page or the folder holding it |
| an agenda item | `agenda N` | `agenda.md`, or the ruling that disposed it |
| a session | the sid, in backticks | bale's registry, per project |
| a notepad page | `notepad/YYYY-MM-DD-slug.md` | the page |
