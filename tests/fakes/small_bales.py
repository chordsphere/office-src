"""Three small fake bales, as one fixed module (0.27.0; until then script
texts in tests/test_project_on_host.py and tests/test_out_trip_to_host.py).

- old: the bale on an older host, 0.4.40 to --version and nothing else
  (tests/test_project_on_host.py FakeSsh puts it in that host's bin/).
- install: a bale release install's bin/bale, answering --version from
  the VERSION file beside the program that ran (tests/test_out_trip_to_host.py
  fake_install), so a release copied over an install answers its own.
- asking: a bale that asks one question on its stdin, as apply's
  walkthrough does, and says what it was answered and whether stdin was a
  terminal (tests/test_out_trip_to_host.py AttendedCase).

A test never runs this file: tests/test_office.py fake_program writes a
program in the test's own tree that imports this module and calls one of
these with its arguments. Each refuses what it was not built for with
exit 97, as the scripts did.
"""

import pathlib
import sys


def old(cfg, argv):
    if argv == ["--version"]:
        print("bale 0.4.40")
        return 0
    print("old fake bale: only --version is answered", file=sys.stderr)
    return 97


def install(cfg, argv):
    here = pathlib.Path(sys.argv[0]).resolve().parent
    v = (here / "VERSION").read_text().strip()
    if argv == ["--version"]:
        print("bale " + v)
        return 0
    print("install fake bale " + v + ": only --version", file=sys.stderr)
    return 97


def asking(cfg, argv):
    if argv[:1] == ["apply"]:
        sys.stdout.write("Merge the session? [y/N] "); sys.stdout.flush()
        answer = sys.stdin.readline().strip()
        print("answered:" + (answer or "(nothing: stdin closed)"))
        print("terminal:" + ("yes" if sys.stdin.isatty() else "no"))
        return 0 if answer else 3
    print("asking fake bale: only apply", file=sys.stderr)
    return 97
