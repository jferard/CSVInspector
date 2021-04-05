# coding: utf-8
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

from csv_inspector.util import (executed, execute_script, END_SCRIPT,
                                BEGIN_SCRIPT)

IGNORE = 0
SCRIPT = 1

state = IGNORE
script_lines = []

# REPL version, but need one dict per window.
vars = {}

# This is the main server!
while True:
    line = sys.stdin.readline().rstrip()
    stripped_line = line.lstrip()
    if state == IGNORE:
        # here: read the window id and the mode (REPL or not)
        if stripped_line == BEGIN_SCRIPT:
            state = SCRIPT
            script_lines = []
        else:
            print(f"Garbage {stripped_line}", file=sys.stderr)
    elif state == SCRIPT:
        if stripped_line == END_SCRIPT:
            script = "\n".join(script_lines)
            print("server/execute script: {} chars".format(len(script)))
            try:
                execute_script(script, vars)
            except Exception as e:
                traceback.print_exc()

            print("server/script executed")
            executed()
            state = IGNORE
        else:
            script_lines.append(line)
