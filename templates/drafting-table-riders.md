# Riders

Small work with a named carrier and no folder of its own. A rider is on
this page or in exactly one folder's Riders section, never both: when a
folder's next session carries it, its text moves into the folder and
one pointer line stays here (`- rider N -> folder M`). A pointer is not
a copy. Numbers are minted in order across this page and every folder,
and never reused. A rider (values illustrative):

```markdown
### rider N - the title, as the registry writes it

- source: proposal SID #n
- rides: bin/bale_pack.py
- status: queued

Text verbatim from the source, when the source is a worker's Proposal.

- YYYY-MM-DD queued: from the proposal above
```

`rides` is a path glob (the rider rides the next session that touches
it) or `folder N`. `status` is one of `queued`, `carried` (by folder
N), `consumed` (at a sid), `moot`, `stands`; each change is a dated
line under the rider. When the source is a Proposal, the body is the
Proposal's What, Why and Scope hints, byte for byte. There are no
buckets: a rider that must wait carries an `after:` line naming what it
waits for.
