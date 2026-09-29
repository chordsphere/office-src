# Watches

The watches register: a watch is a named re-trigger with no work
attached. One entry per watch, live. Ids are `W1`, `W2`, ..., minted in
order and never reused. State is never edited into an entry: every
event (opened, fired, not-fired, re-armed, reworded, closed) is a record
on watch-log.md, and a closed watch stays on this page. The one edit an
entry allows is a rewording, and the log keeps the wording it replaced.
An entry (values illustrative):

```markdown
## W13 - Forecast precision

- source: 2026-08-07-board-13b-epoch-ledger-005 (notes)
- scope: office
- condition: unused forecast entries, packer-side, accruing
- evaluates: query unused-forecast-entries
- threshold: 3
- re-trigger: three accruals since the last fired record

What is known, in prose.
```

The fields: `source` is required, a sid, a close report path or a
notepad page. `scope` is `office` or `blueprint YYYY-MM-DD-slug`.
`evaluates` is `query NAME` for a condition a script can compute, or
`eye` for one someone has to notice; an eye-watch no sitting has looked
at is reported, never silently aged. `re-trigger` may be `none` for a
watch kept for its record. A watch with no re-trigger and no action is
not a watch; it is a standing line of the digest.
