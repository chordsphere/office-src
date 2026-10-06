# Rulings

The rulings ledger. Filed: one record per ruling, appended at the end,
and the bytes already here never change. Only a sitting writes a
ruling; scripts read them. A ruling's id is its date and a short slug
of its bold lead, minted by the sitting that writes it and never
changed; a second ruling with the same slug on the same day takes `-2`.
The ledger never quotes the occupant: `words` names the notepad page
that files them whole. A record (values illustrative):

```markdown
## 2026-09-29-kind-vocabulary

- ruled: 2026-09-29
- source: light block 2026-09-28-open-discussion-001 [2]
- words: notepad/2026-09-29-suite-merge.md
- landed: registers/README.md (nisaba-src)
- grounds: evidence N, folder N
- supersedes: YYYY-MM-DD-slug (scope: in words, how far)

**Keep the register's kind vocabulary at four values.** The ruling's
text, bold lead first.
```

The fields: `source` is one of a sid, `notepad/...` (words said in a
sitting or through `office note`), `light block SID [n]` (an answer to a
worker's light question block, "as assumed" included), or `brief of
SID` (a ruling transported in a request's brief). `words` is the notepad
page carrying the occupant's words verbatim. `landed` is where the
ruling took effect: a folder, a sid, or a project path and section.
`grounds` are evidence numbers, ADRs, folders. `supersedes` names an
earlier ruling and the scope in words; the superseded record is never
touched, and the back-pointer is derived by the reader, never written.

A ruling is reopened only by a sitting that names it, and a reopening
is a new ruling that supersedes. An amendment is a record too: its own
id on its own date, `amends: ID` naming the ruling as first minted
(never an amendment's id), and the amending text. When a ruling's text
lands in a project doc, a derivation record is appended, `## ID -
derived - YYYY-MM-DD` (the ruling's own id) with `- into: project path
section N`, and the ruling stays. `office rulings ID` renders a ruling
with its amendments, who supersedes it and where it was derived;
`office rulings --check` resolves every citation on the drafting table
and the desk.
