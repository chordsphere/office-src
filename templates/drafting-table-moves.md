# Desk moves

What a sitting decided about folders, written as data for the office
command to apply: open this, gate that, retire the other. The desk is
the office command's to write and folder numbers are minted by it
alone, so a sitting never touches the desk directly. One move per line,
in order, appended below; `office moves` applies every pending line
through the same code as `office open`, `office close` and the gate
flags, ticks it (`- [x] ... -> folder N`), writes the minted number onto
a blueprint's decomposition line, and stops at the first line it cannot
apply, naming it. A line that does not read is refused before anything
is applied. Until it is run, walking in says how many moves are pending
and which session wrote them.

The moves, each after `- [ ] YYYY-MM-DD ` (the day the sitting decided
it); a value with a space goes in double quotes:

- `open "TITLE" [key=value ...]`: a new folder, through `office open`.
  Keys: `slug`, `class`, `size`, `lane`, `source`, `blueprint` (and
  `line=N`, the blueprint's decomposition line it carries, when its goal
  is not the title word for word), `after`, `serializes-after`,
  `consumer`, `linked` (each of these four as often as needed), and
  `candidate=yes` for a candidate.
- `queue folder N`: a candidate becomes queued.
- `gate folder N after="X"`: a gate on a folder on the desk;
  `serializes-after="folder M"` and `consumer="X"` too, one or more.
- `close folder N`: done, to the filing cabinet.
- `absorb folder N into="folder M"`, `split folder N into="A,B"`,
  `retire folder N why="..."`: the other endings, as `office close`
  writes them.

Moves (values illustrative):

```markdown
- [ ] 2026-10-02 open "riders verbs" class=code size=small lane="office-src: bin/" blueprint=2026-09-29-drafting-table after="folder 141"
- [ ] 2026-10-02 gate folder 80 after="agenda 7"
- [ ] 2026-10-02 retire folder 57 why="premise corrected at evidence 212"
- [x] 2026-10-02 open "riders verbs" class=code size=small -> folder 142
```
