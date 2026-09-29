# Evidence

The evidence ledger. Filed: numbered, appended at the end, cited by
number as `evidence N`; the bytes already here never change. Numbers
are the identity: minted in order, never reused, never renumbered. Only
a sitting writes here. The ledger admits only what live traffic earned:
an entry names at least one session (`from:` a sid) or a notepad page,
and a record without one is refused. Provenance is per record, never
per batch, because a batch header is lost the moment an entry is cited
alone. An entry and an occurrence (values illustrative):

```markdown
## 220. Title, as a sentence.

- filed: 2026-10-02 by 2026-10-02-sitting-001
- from: 2026-10-01-board-141-riders-003

Body: what happened, what it shows.

## 13 - occurrence - 2026-10-03

- from: 2026-10-03-retry-002
- attributed-to: planner

What recurred, in a line or two.
```

An occurrence is a new record pointing at its entry, never text added
to the entry; `attributed-to` is one of planner, worker, operator,
courier. The reader counts occurrences per entry. When an entry's
lesson lands in a project doc, a record `## N - derived - YYYY-MM-DD`
with `- into: project path section N` is appended and the entry stays.
