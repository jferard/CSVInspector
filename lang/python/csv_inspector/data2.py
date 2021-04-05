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
import sys
from itertools import islice
from typing import List, Any

from csv_inspector.data import DataSource
from csv_inspector.util import begin_csv, end_csv, ColumnGroup, to_indices, \
    Column


class DataHandle:
    def __init__(self, data: "Data", indices: List[int],
                 column_group: ColumnGroup):
        self._data = data
        self._indices = indices
        self._column_group = column_group

    def show(self, limit: int = 100):
        """
        Show the first rows of this DataHandle.
        Expected format: CSV with comma
        """
        writer = csv.writer(sys.stdout, delimiter=',')
        begin_csv()
        writer.writerow([col.col_type for col in self._column_group])
        writer.writerow([col.name for col in self._column_group])
        writer.writerows(self._rows(limit))
        sys.stdout.flush()
        end_csv()

    # TODO: __getitem__ -> row

    def _rows(self, limit: int = 100):
        return islice(self._column_group.rows(), limit)

    def select(self):
        """
        Select the indices of the handle and drop the other indices.
        """
        self._data._column_group = self._column_group

    def drop(self):
        """
        Drop the indices of the handle and select the other indices.
        """
        columns = [c for i, c in enumerate(self._data._column_group)
                   if i not in self._indices]
        self._data._column_group = ColumnGroup(columns)

    def swap(self, other_handle: "DataHandle"):
        """
        Swap two handles. Those handles may be backed by the same data or not.
        """
        if other_handle._data == self._data:
            columns = list(self._data._column_group)
            for j, k in zip(self._indices, other_handle._indices):
                temp = columns[j]
                columns[j] = columns[k]
                columns[k] = temp

            self._data._column_group = ColumnGroup(columns)
        else:
            columns = list(self._data._column_group)
            other_columns = list(other_handle._data._column_group)
            for j, k in zip(self._indices, other_handle._indices):
                temp = columns[j]
                columns[j] = other_columns[k]
                other_columns[k] = temp

            self._data._column_group = ColumnGroup(columns)
            other_handle._data._column_group = ColumnGroup(other_columns)

    def update(self, func, col_name=None, col_type=None):
        assert len(self._indices) == 1
        column = self._column_group[0]
        index = self._indices[0]
        if col_type is None:
            try:
                col_type = func.__annotations__['return']
            except (KeyError, AttributeError):
                col_type = column.col_type

        if col_name is None:
            col_name = column.name

        columns = list(self._data._column_group)
        columns[index] = Column(col_name, col_type,
                                [func(v) for v in column.col_values])

        self._data._column_group = ColumnGroup(columns)

    def create(self, func, col_name, col_type=None, index=None):
        if col_type is None:
            try:
                col_type = func.__annotations__['return']
            except (KeyError, AttributeError):
                col_type = Any

        columns = list(self._data._column_group)
        column = Column(col_name, col_type,
                        [func(*vs) for vs in self._column_group.rows()])

        if index is None:
            columns.append(column)
        else:
            columns.insert(index, column)
        self._data._column_group = ColumnGroup(columns)

    def merge(self, func, col_name, col_type=None):
        if col_type is None:
            try:
                col_type = func.__annotations__['return']
            except (KeyError, AttributeError):
                col_type = Any

        columns = list(self._data._column_group)
        column = Column(col_name, col_type,
                        [func(*vs) for vs in self._column_group.rows()])

        columns[self._indices[0]] = column
        for i in self._indices[1:]:
            del columns[i]

        self._data._column_group = ColumnGroup(columns)


class Data2:
    def __init__(self, column_group: ColumnGroup, data_source: DataSource):
        self._column_group = column_group
        self._data_source = data_source

    def __getitem__(self, item):
        indices = to_indices(len(self._column_group), item)
        column_group = ColumnGroup(
            [self._column_group[i] for i in indices])
        return DataHandle(self, indices, column_group)

    def show(self, limit: int = 100):
        self.as_handle().show(limit)

    def as_handle(self) -> DataHandle:
        return DataHandle(self, list(range(len(self._column_group))),
                          self._column_group)

