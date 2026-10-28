# Delivery: {{title}}

The words the folder's landed work leaves with, in the occupant's voice:
the commit the audience reads, and the review request. A build session
writes this page as the Delivery section at the end of its notes.md,
every heading one level down (### Commit, ### Review); office land files
it in the folder as delivery.md, and office deliver reads it. Written by
hand, it is this file, in the folder. A `to:` line names the reviewer.
Nothing here names a model, a tool or a session: the letterhead check
reads the words that leave, the `to:` line and the Commit and Review
sections, before anything leaves (this heading and this paragraph stay in
the office, and are not read). When the office has a
letterhead, they follow its voice page (letterhead/voice.md) and hold no
em dash, en dash or ellipsis character unless the letterhead lifts one.
A Review that fills the repository's own pull-request template keeps the
template's lines as the repository holds them: those lines are not held
to the letterhead's phrasing rule, and every line written into or
around them is.

- to: {{to}}

## Commit

The subject, one line, then a blank line, then the body: what changed
and why, as the audience reads a commit. For several commits, repeat
this section; each but the last starts with a `paths:` line naming,
comma-separated and relative to the repo's top, what that commit takes
(a directory takes what is under it), and the last takes the rest.

## Review

The title, one line, then a blank line, then the body: what to look at,
what to try by hand, and what is deliberately untouched. A section ends
only at the next Commit or Review heading, so a pull-request template's
own `## ` headings, filled in here, are the review's words.
