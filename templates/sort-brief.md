# Brief: sort the in-tray's drops

`office start --sort` sent this session out from the office for the
{{count}} drop(s) in the in-tray that nothing has sorted yet. It belongs to
no folder: the in-tray is its job. Nobody has read these messages for
you: the occupant dropped each as it came. This brief is the office's
standing instructions, the drops themselves, and the desk as `office
desk` prints it, so you route each drop to a folder that exists, by its
number.

## What to do

Read every drop below, then decide for each:

1. What it means: what the sender asks for, in a sentence of your own.
2. Which project it is for: one of the office's projects by name (the
   floor plan names them), or none.
3. Which folder: one on the desk below whose job it belongs to, by its
   number, or `new` when it is a job of its own.
4. What it spawns: the goal of the session that will do it, in one
   sentence, and its size (small, medium or high).
5. What the occupant must be told, and whom he tells: the `tell:` line,
   or `nobody`.

Write one Sort subsection per drop under `## Sort` in your notes.md, in
the format below, and a `#### Brief` for every `folder: new`: the brief
the new folder's first session goes out with, written from the thread,
so nobody has to read the thread again. A drop you cannot judge gets no
subsection: say why in a line, and it waits for the occupant.

What you learn about a project, and every fact the occupant gives you,
goes under `## Handbook`, `### PROJECT`, as `- ` lines. The handbook
chapters you carry say what is known already: read them before you ask
anything. Record each light block you send, and the occupant's answer,
under `## Questions and answers`, one `- DATE question? answer` line each.

{{moves}}

You write notes.md, and the moves page when you have one, and nothing
else. office land files the Sort on each drop's page, mints the folders
`new` asks for, moves each drop into its folder with its brief, puts each
`tell:` on its folder's Next, and files the facts in the handbook.

## The drops

{{drops}}

## The desk

```
{{desk}}
```

## The Sort format

One subsection per drop, named by the page's file name wherever the page
sits (the in-tray, or a folder's drops/), every key on its own line, in
this order (values illustrative):

```
### 2026-10-14-login-error.md

- project: alpha
- folder: new
- goal: Fix the login page's error on narrow screens
- size: small
- tell: the sender, in reply: fixed in the next release
- facts: none

#### Brief

<the next session's brief, written from the thread>
```

`folder:` is `new` or a folder number; `tell:` is `nobody` or who and
what; `facts:` is `none` or one or more lines for the project's handbook
chapter, each starting with `- `; `#### Brief` is present when `folder:`
is `new` and may be present otherwise.
Fact lines follow an empty `- facts:` line, one `- ` line each, before
the blank line above `#### Brief`.
