# Brief: sort the dropped message, then do what it asks

Folder {{number}}, "{{title}}", on {{project}}. `office start --drop`
opened it from one page of the office's in-tray, which now sits in the
folder as {{page}}, and sent this session out in the same command. Nobody
has read the message for you: the occupant dropped it as it came and sent
it straight out, so this brief is the office's standing instructions and
the message itself, and the goal is one sentence on purpose.

## First, sort

Read the drop below before anything else, then decide:

1. What it means: what the sender asks for, in a sentence of your own.
2. Which part of {{project}} it concerns: the paths, as far as the code
   shows you.
3. Whether it is one job. One session's work: do it. More than one, or
   not {{project}}'s at all: do not start it; say so in the Sort section
   and stop with a light question block, or with a rescope offer that
   splits it, as the session's contract docs describe.
4. What the occupant must be told, and whom he tells: the `tell:` line.

Write what you decided as the Sort section of your notes.md, `## Sort`,
with one subsection for this drop, `### {{name}}`, in the format below:
`folder:` is {{number}}, this folder, and `#### Brief` may be left out.
Then do the work, and end notes.md with the Walkthrough and Delivery
sections, as every build session does.

Other unsorted drops from the in-tray may ride beside this session, in
the office's context; the doctrine's section 4 says what you owe them.

## The drop

{{begin}}
{{drop}}
{{end}}

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
