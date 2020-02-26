#  CSVInspector - A graphical interactive tool to inspect and process CSV files.
#      Copyright (C) 2020 J. Férard <https://github.com/jferard>
#
#  This file is part of CSVInspector.
#
#  CSVInspector is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  CSVInspector is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys
import traceback

import pandas as pd
import csv_inspector

if len(sys.argv) > 1:
    TOKEN = sys.argv[1]
else:
    TOKEN = None

IGNORE = 0
SCRIPT = 1

state = IGNORE
script_lines = []

# This is the main server!
while True:
    line = sys.stdin.readline().strip()
    if state == IGNORE:
        if line == f"{TOKEN}begin script":
            state = SCRIPT
            script_lines = []
        else:
            print(f"Garbage {line}", file=sys.stderr)
    elif state == SCRIPT:
        if line == f"{TOKEN}end script":
            script = "\n".join(script_lines)
            print("server/execute script: {} chars", len(script))
            try:
                exec(script, {"TOKEN": TOKEN})
            except Exception as e:
                traceback.print_exc()

            print("server/script executed")
            print(f"{TOKEN}executed", flush=True)
            print(f"{TOKEN}executed", file=sys.stderr, flush=True)
            state = IGNORE
        else:
            script_lines.append(line)
