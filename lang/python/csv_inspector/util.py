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

try:
    TOKEN
except NameError:
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
    else:
        TOKEN = None

BEGIN_SCRIPT = f"{TOKEN}begin script"
END_SCRIPT = f"{TOKEN}end script"


def begin_info():
    print(f"{TOKEN}begin info")


def end_info():
    print(f"{TOKEN}end info", flush=True)


def begin_csv():
    print(f"{TOKEN}begin csv")


def end_csv():
    print(f"{TOKEN}end csv", flush=True)


def executed():
    print(f"{TOKEN}executed", flush=True)
    print(f"{TOKEN}executed", file=sys.stderr, flush=True)


def execute_script(script):
    exec(script, {"TOKEN": TOKEN})


def sanitize(text: str) -> str:
    """
    Remove accents and special chars from a string

    >>> sanitize("Code Départ’ement")
    'Code Departement'


    @param text: the unicode string
    @return: the ascii string
    """
    import unicodedata
    try:
        text = unicodedata.normalize('NFKD', text).encode('ascii',
                                                          'ignore').decode(
            'ascii')
    except UnicodeError:
        pass
    return text


def to_standard(text: str) -> str:
    """
    >>> to_standard("Code Départ’ement")
    'code_departement'

    :param text:
    :return:
    """
    return sanitize(text.replace(" ", "_")).casefold()


