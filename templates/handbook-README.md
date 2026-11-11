# The handbook

The private layer of documentation: what only the occupant and the
office's sessions may read about each project. Shareable documentation
lives in the projects themselves (README, docs/), and a chapter points at
it rather than restating it. One chapter per project, handbook/PROJECT.md,
in this shape (values illustrative):

```
# alpha

## Front sheet

<for the occupant, in plain language: what the project is and where it stands; replaced whole by a session's Front sheet>

## Conventions

None settled yet.

## Facts

- 2026-10-14: the login page is served by the api's static route (2026-10-14-alpha-login-error-001)
```

Three parts. The front sheet is for the occupant, in plain language: what
the project is and where it stands. A session that lands work on the
project writes one in the Handbook section of its notes.md, and office land
replaces the chapter's front sheet with it, whole. The conventions are the
project's own rules for what leaves it (the commit style, the review's
shape, which repository), settled with its reviewer once and written here
by hand or through a session in the office; where they speak they win over
the letterhead's voice page for the form, and the voice page keeps the
words. A chapter with none settled reads as none. The facts are for
sessions: each line is one thing a session learned about the project, or
that the occupant told it, dated and naming the session. office land
appends them at the end, and nobody rewrites them by hand, so the
occupant is never asked the same thing twice.

This page is hung: every office session carries it. A chapter rides with
every session whose folder's lane names its project, and every chapter
rides with the standalone sort (office start --sort). Nothing here is
filed: the handbook is live, and its facts grow at the end.
