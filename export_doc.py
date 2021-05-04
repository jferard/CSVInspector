# coding: utf-8
"""
A simple tool to export a part of the documentation.
"""
import re
import subprocess
import io
import threading

import sys

IGNORE = 0
FUNC_DOC = 1

if __name__ == "__main__":
    sys.path.insert(0, "./lang/python")
    import csv_inspector.data;

    stdout_bkp = sys.stdout
    string = io.StringIO()
    sys.stdout = string
    help(csv_inspector.data.DataHandle)
    sys.stdout = stdout_bkp
    text = string.getvalue()
    state = IGNORE
    description = []
    for line in text.split("\n"):
        if state == IGNORE:
            m = re.match("^ \| {2}([^A-Z_ ].*)$", line)
            if m:
                state = FUNC_DOC
        elif state == FUNC_DOC:
            line = line[2:].strip()
            if line.startswith("Syntax"):
                print(f"### {line[7:].strip()}")
                while description and not description[0]:
                    del description[0]
                while description and not description[-1]:
                    del description[-1]
                print("> "+"\n> ".join(description))
                print()
                description = []
            elif line.startswith("*"):
                print(line)
            elif line.startswith(">>>"):
                print()
                state = IGNORE
            else:
                description.append(line)

