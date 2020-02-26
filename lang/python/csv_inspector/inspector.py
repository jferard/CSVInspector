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

import csv
import io
import sys
from pathlib import Path
from typing import (Union)

import chardet
import pandas as pd
from csv_inspector.data import Data

sniffer = csv.Sniffer()

try:
    TOKEN
except NameError:
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
    else:
        TOKEN = None


class Inspection:
    def __init__(self, path: Path, data: bytes):
        self._path = path
        self._data = data
        self._encoding = "utf-8"
        self._csvdialect = csv.unix_dialect
        self._coltypes = []

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding
        self._guess_dialect()
        self._guess_coltypes()

    def _guess_dialect(self):
        self._csvdialect = sniffer.sniff(
            self._data.decode(self._encoding, errors="ignore"))

    @property
    def delimiter(self):
        return self._csvdialect.delimiter

    @delimiter.setter
    def delimiter(self, delimiter):
        self._csvdialect.delimiter = delimiter
        self._guess_coltypes()

    @property
    def quotechar(self):
        return self._csvdialect.quotechar

    @quotechar.setter
    def quotechar(self, quotechar):
        self._csvdialect.quotechar = quotechar
        self._guess_coltypes()

    @property
    def doublequote(self):
        return self._csvdialect.doublequote

    @doublequote.setter
    def doublequote(self, doublequote):
        self._csvdialect.doublequote = doublequote
        self._guess_coltypes()

    @property
    def skipinitialspace(self):
        return self._csvdialect.skipinitialspace

    @skipinitialspace.setter
    def skipinitialspace(self, skipinitialspace):
        self._csvdialect.skipinitialspace = skipinitialspace
        self._guess_coltypes()

    @property
    def lineterminator(self):
        return self._csvdialect.lineterminator

    @lineterminator.setter
    def lineterminator(self, lineterminator):
        self._csvdialect.lineterminator = lineterminator
        self._guess_coltypes()

    @property
    def quoting(self):
        return self._csvdialect.quoting

    @quoting.setter
    def quoting(self, quoting):
        self._csvdialect.quoting = quoting
        self._guess_coltypes()

    def _guess_coltypes(self):
        sample = self._data.decode(self._encoding, errors="ignore")
        self._df = pd.read_csv(io.StringIO(sample), index_col=False,
                               nrows=100, delimiter=self._csvdialect.delimiter,
                               dialect=self._csvdialect)
        self._set_col_types()
        self._coltypes = list(self._df.dtypes)

    def _set_col_types(self):
        for col in self._df.columns:
            if self._df[col].dtype == object:
                try:
                    self._df[col] = pd.to_datetime(self._df[col])
                except ValueError:
                    self._df[col] = self._df[col].astype('str')

    @property
    def coltypes(self):
        return self._coltypes

    @coltypes.setter
    def coltypes(self, coltypes):
        self._coltypes = coltypes

    def open(self) -> Data:
        self._df = pd.read_csv(self._path, encoding=self._encoding,
                               index_col=False,
                               delimiter=self._csvdialect.delimiter,
                               dialect=self._csvdialect)
        self._set_col_types()
        return Data(self._df)

    def show(self):
        print(f"{TOKEN}begin info")
        print(f"encoding: '{self.encoding}'")
        print(f"csvdialect.delimiter: {repr(self.delimiter)}")
        print(f"csvdialect.quotechar: {repr(self.quotechar)}")
        print(f"csvdialect.doublequote: {self.doublequote}")
        print(f"csvdialect.skipinitialspace: {self.skipinitialspace}")
        print(f"csvdialect.lineterminator: {repr(self.lineterminator)}")
        print(f"csvdialect.quoting: {self.quoting}")
        print(f"coltypes:\n{self.coltypes}")
        print(f"dtype:\n{self._df.dtypes}")
        print(f"{TOKEN}end info", flush=True)


def inspect(file: Union[str, Path], chunk_size=1024 * 1024) -> Inspection:
    if isinstance(file, str):
        path = Path(file)
    else:
        path = file
    with path.open("rb") as source:
        data = source.read(chunk_size)
        inspection = Inspection(path, data)
        inspection.encoding = chardet.detect(data)["encoding"]

    return inspection
