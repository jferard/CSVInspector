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

from itertools import islice
from pathlib import Path
from typing import (Union, Optional)

import mcsv

from csv_inspector.data import Data, DataSource
from csv_inspector.util import to_standard, ColumnGroup, missing_mcsv, Column

def read_csv(csv_path: Union[str, Path],
             mcsv_path: Optional[Union[str, Path]] = None,
             nrows=100) -> Optional[Data]:
    if isinstance(csv_path, str):
        csv_path = Path(csv_path)
    if mcsv_path is None:
        mcsv_path = csv_path.with_suffix(".mcsv")

    if not mcsv_path.is_file():
        missing_mcsv(csv_path)  # util command to open a window
        return None

    with mcsv.open_csv(csv_path, "r", mcsv_path) as mcsv_reader:
        if nrows >= 0:
            reader = islice(mcsv_reader, nrows)
        else:
            reader = mcsv_reader
        header = [to_standard(n) for n in next(reader)]
        column_group = ColumnGroup([Column(name, description, values)
                                    for name, description, *values in
                                    zip(header, mcsv_reader.descriptions,
                                        *reader)])

        return Data(column_group, DataSource.create(to_standard(csv_path.stem),
                                                    csv_path,
                                                    mcsv_reader.meta_csv_data))
