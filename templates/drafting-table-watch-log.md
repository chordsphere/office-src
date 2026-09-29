# Watch log

Every event on every watch, one record per line, appended at the end.
Filed: the bytes already here never change. The verbs are a closed set:
`opened`, `fired`, `not-fired`, `re-armed`, `reworded`, `closed`. A
`fired` line names its evidence (a sid or `evidence N`); a `reworded`
line carries the old condition verbatim, while the entry on watches.md
takes the new wording; a `closed` line names the ruling that disposed
the watch. A script may append `fired` records; everything else is a
sitting's. Records (values illustrative):

```markdown
- 2026-09-10 W15 fired: evidence 109; 2026-09-01 sitting's three fixture defects
- 2026-09-10 W15 re-armed: same threshold
- 2026-08-31 W13 closed: ruling 2026-08-31-no-packaging-trio
```
