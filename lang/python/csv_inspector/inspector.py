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
from itertools import islice
from pathlib import Path
from typing import (Union, Optional)

import chardet
import mcsv

from csv_inspector.data import Data, DataSource
from csv_inspector.util import begin_info, end_info, to_standard, ColumnFactory, \
    ColumnGroup, missing_mcsv

sniffer = csv.Sniffer()


class Inspection:
    def __init__(self, path: Path, encoding: str,
                 csvdialect: csv.Dialect) -> "Inspection":
        self._path = path
        self._encoding = encoding
        self._csvdialect = csvdialect
        self._col_factory = ColumnFactory()

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding

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

    def __repr__(self):
        return f"Inspection({repr(self._path)}, {repr(self._encoding)}, {repr(self._csvdialect)})"

    def write(self, output_path: Path):
        pass

    def open(self, nrows=100) -> Data:
        with self._path.open('r', encoding=self._encoding) as s:
            reader = islice(csv.reader(s, self._csvdialect), nrows)
            header = [to_standard(n) for n in next(reader)]
            column_groups = ColumnGroup([self._col_factory.create(name, values)
                                   for name, *values in zip(header, *reader)])

        return Data(column_groups, DataSource(to_standard(self._path.stem),
                                        self._path, self._encoding,
                                        self._csvdialect))

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
            encoding: str = None, lineterminator: str = None,
            delimiter: bytes = None, quotechar: bytes = None,
            doublequote: bytes = None, skipinitialspace: bool = None,
            quoting: bool = None) -> Inspection:
    def _wrap_path(f: Union[str, Path]):
        if isinstance(f, str):
            return Path(f)
        else:
            return f

    def _sniff_terminator(data: bytes):
        terminator_count = {b'\r\n': 0, b'\n': 0, b'\r': 0, b'\n\r': 0}
        last = None
        for b in data:
            if b == b'\n':
                if last == b'\r':
                    terminator_count[b'\r\n'] += 1
                    last = None
                else:
                    terminator_count[b'\n'] += 1
            elif b == b'\r':
                if last == b'\n':
                    terminator_count[b'\n\r'] += 1
                    last = None
                else:
                    terminator_count[b'\r'] += 1
            else:
                last = None

        return max(terminator_count.keys(), key=terminator_count.get).decode("ascii")

    path = _wrap_path(file)
    with path.open("rb") as source:
        data = source.read(chunk_size)
        if encoding is None:
            encoding = chardet.detect(data)["encoding"]
        if lineterminator is None:
            lineterminator = _sniff_terminator(data)
        csvdialect = sniffer.sniff(
            data.decode(encoding, errors="ignore"))
        if delimiter is not None:
            csvdialect.delimiter = delimiter
        if quotechar is not None:
            csvdialect.quotechar = quotechar
        if doublequote is not None:
            csvdialect.doublequote = doublequote
        if skipinitialspace is not None:
            csvdialect.skipinitialspace = skipinitialspace
        if quoting is not None:
            csvdialect.quoting = quoting
        if csvdialect.lineterminator != lineterminator:
            csvdialect.lineterminator = lineterminator

        inspection = Inspection(path, encoding, csvdialect)

    return inspection


def open_csv(csv_path: Union[str, Path],
             mcsv_path: Optional[Union[str, Path]]=None) -> Optional[Data]:
    if isinstance(csv_path, str):
        csv_path = Path(csv_path)
    if mcsv_path is None:
        mcsv_path = csv_path.with_suffix(".mcsv")

    if not mcsv_path.is_file():
        missing_mcsv(csv_path)  # util command to open a window
        return None

    mcsv_reader = mcsv.reader.open_csv(csv_path, mcsv_path)
    print(mcsv_reader.get_types())
