# coding= utf-8
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
from pathlib import Path
from typing import (Union)

import chardet
import pandas as pd

from csv_inspector.data import Data
from csv_inspector.util import begin_info, end_info, to_standard

sniffer = csv.Sniffer()


class Inspection:
    def __init__(self, path: Path, data: bytes, **kwargs):
        self._path = path
        self._data = data
        self._kwargs = kwargs
        self._encoding = self._kwargs.get("encoding", "utf-8")
        self._csvdialect = self._kwargs.get("dialect", csv.unix_dialect)
        self._kwargs.setdefault("engine", "python")
        self._kwargs.setdefault("nrows", 100)

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding
        self._guess_dialect()

    def _guess_dialect(self):
        self._csvdialect = sniffer.sniff(
                self._data.decode(self._encoding, errors="ignore"))

    @property
    def delimiter(self):
        return self._csvdialect.delimiter

    @delimiter.setter
    def delimiter(self, delimiter):
        self._csvdialect.delimiter = delimiter

    @property
    def quotechar(self):
        return self._csvdialect.quotechar

    @quotechar.setter
    def quotechar(self, quotechar):
        self._csvdialect.quotechar = quotechar

    @property
    def doublequote(self):
        return self._csvdialect.doublequote

    @doublequote.setter
    def doublequote(self, doublequote):
        self._csvdialect.doublequote = doublequote

    @property
    def skipinitialspace(self):
        return self._csvdialect.skipinitialspace

    @skipinitialspace.setter
    def skipinitialspace(self, skipinitialspace):
        self._csvdialect.skipinitialspace = skipinitialspace

    @property
    def lineterminator(self):
        return self._csvdialect.lineterminator

    @lineterminator.setter
    def lineterminator(self, lineterminator):
        self._csvdialect.lineterminator = lineterminator

    @property
    def quoting(self):
        return self._csvdialect.quoting

    @quoting.setter
    def quoting(self, quoting):
        self._csvdialect.quoting = quoting

    def open(self, **kwargs) -> Data:
        self._df = pd.read_csv(self._path, encoding=self._encoding,
                               index_col=False,
                               delimiter=self._csvdialect.delimiter,
                               dialect=self._csvdialect,
                               keep_default_na=False, **kwargs)
        self._df.columns = [to_standard(c) for c in self._df.columns]
        return Data(self._df, to_standard(self._path.stem),
                    self._path, self._encoding, self._csvdialect)

    def show(self):
        begin_info()
        print(f"encoding: '{self.encoding}'")
        print(f"csvdialect.delimiter: {repr(self.delimiter)}")
        print(f"csvdialect.quotechar: {repr(self.quotechar)}")
        print(f"csvdialect.doublequote: {self.doublequote}")
        print(f"csvdialect.skipinitialspace: {self.skipinitialspace}")
        print(f"csvdialect.lineterminator: {repr(self.lineterminator)}")
        print(f"csvdialect.quoting: {self.quoting}")
        end_info()


def inspect(file: Union[str, Path], chunk_size=1024 * 1024,
            **kwargs) -> Inspection:
    if isinstance(file, str):
        path = Path(file)
    else:
        path = file
    with path.open("rb") as source:
        data = source.read(chunk_size)
        inspection = Inspection(path, data, **kwargs)
        inspection.encoding = chardet.detect(data)["encoding"]

    return inspection
