"""The read side's fake bale, as a fixed module (0.27.0).

It replays lines a probe captured from a real bale, keyed by argv and the
directory it runs in: the fixture set a test routes to that directory
first, then the set for anywhere. Anything else is refused with exit 97.
Every call is recorded, one JSON line [cwd, argv], in the calls file.

A test never runs this file. tests/test_read_side.py FakeBale writes a
program named bale in the test's own tree (tests/test_office.py
fake_program) that imports this module and calls main with the test's
config: {"routes": {directory: fixture set, "*": fixture set}, "calls":
path}. Being a module, it is compiled once per run into the runner's
bytecode cache rather than on every call, as a script would be.
"""

import json
import os
import pathlib
import sys


def main(cfg, argv):
    routes = cfg["routes"]
    cwd = os.path.realpath(os.getcwd())
    with open(cfg["calls"], "a", encoding="utf-8") as log:
        log.write(json.dumps([cwd, argv]) + "\n")
    for d in ([routes[cwd]] if cwd in routes else []) + [routes["*"]]:
        for f in sorted(pathlib.Path(d).glob("*.json")):
            rec = json.loads(f.read_text(encoding="utf-8"))
            if rec["argv"] == argv:
                for line in rec["stdout"]:
                    print(line)
                for line in rec["stderr"]:
                    print(line, file=sys.stderr)
                return rec["exit"]
    print("fake bale: the probe captured no line for bale " + " ".join(argv) + " in " + cwd, file=sys.stderr)
    return 97
