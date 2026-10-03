# office-src: development record

office-src keeps its own record here, the way bale-src does: how the tool
came to be, what its planners said, and what is known about it now. None
of this is installed; `install.sh` ships the tool's directories only, so
nothing here reaches an office. This record may name the machines and
offices the tool was built for; the tool itself never does.

| path | what | lifecycle |
|---|---|---|
| context/front-sheet.md | the plain-language front sheet: what office-src does, recent changes, known problems, likely questions | edited by every session that changes the tool |
| context/sittings/ | each planning sitting's words, verbatim, one page per sitting, named by its session id; a sitting that outlives its first page continues on SID-2.md, SID-3.md, never by editing the first | write-once; never edited, reflowed or corrected |
| fixtures/bale-VERSION/ | real bale output captured by a probe, verbatim with each line's sha256, one directory per project it ran in (pack/: the throwaway repos a probe packed in, for office start); the test suite's fake bales replay it | added by the session that probes a new bale or a new surface; never edited |
| responses/ | bale's archive of each session's notes | written by bale at apply |
| telemetry/ | bale's per-session telemetry | written by bale |

Due to move in from the seed (a later session): the design, the
construction plan, the history, the slips about the tool, and the design
sitting's notepad page.
