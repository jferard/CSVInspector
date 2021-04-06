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
import itertools
import sys
from itertools import islice
from typing import List, Any

from csv_inspector.data import DataSource
from csv_inspector.util import begin_csv, end_csv, ColumnGroup, to_indices, \
    Column


class DataGrouperHandle:
    def __init__(self, data_grouper: "DataGrouper", indices: List[int],
                 column_group: ColumnGroup):
        self._data_grouper = data_grouper
        self._indices = indices
        self._column_group = column_group

    def agg(self, func, col_type=None):
        self._data_grouper._new_agg(self._indices, self._column_group, func, col_type)


class DataGrouper:
    def __init__(self, data_column_group: ColumnGroup, indices: List[int],
                 column_group: ColumnGroup):
        self._data_column_group = data_column_group
        self._column_group = column_group
        self._indices = indices
        self._aggs = []

    def __getitem__(self, item):
        indices = to_indices(len(self._data_column_group), item)
        column_group = ColumnGroup(
            [self._data_column_group[i] for i in indices])
        return DataGrouperHandle(self, indices, column_group)

    def _new_agg(self, indices: List[int], column_group: ColumnGroup, func, col_type):
        self._aggs.append((indices, column_group, func, col_type))

    def group(self):
        funcs = {}
        col_types = {}
        for agg in self._aggs:
            for c in agg[0]:
                funcs[c] = agg[2]
                col_type = agg[3]
                if col_type is not None:
                    col_types[c] = col_type
        agg_cols = sorted(funcs)
        for c in self._indices:
            if c in agg_cols:
                agg_cols.remove(c)

        d = {}
        for row in self._data_column_group.rows():
            key = tuple([row[i] for i in self._indices])
            if key not in d:
                d[key] = [[] for _ in agg_cols]
            for c, col in enumerate(agg_cols):
                d[key][c].append(row[col])

        new_rows = []
        for key, values in d.items():
            xs = []
            for i, vs in enumerate(values):
                func = funcs[agg_cols[i]]
                v = func(vs)
                xs.append(v)
            new_rows.append(key + tuple(xs))

        columns = [col for i, col in enumerate(self._data_column_group) if
                   i in self._indices or i in agg_cols]
        for i in agg_cols:
            if i in col_types:
                columns[i].col_type = col_types[i]
        for col, col_values in zip(columns, zip(*new_rows)):
            col.col_values = col_values

        self._data_column_group.replace_columns(columns)


class DataHandle:
    def __init__(self, data_column_group: ColumnGroup, indices: List[int],
                 column_group: ColumnGroup):
        self._indices = indices
        self._data_column_group = data_column_group
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
        self._data_column_group.replace_columns(self._column_group.columns)

    def drop(self):
        """
        Drop the indices of the handle and select the other indices.
        """
        columns = [c for i, c in enumerate(self._data_column_group)
                   if i not in self._indices]
        self._data_column_group.replace_columns(columns)

    def swap(self, other_handle: "DataHandle"):
        """
        Swap two handles. Those handles may be backed by the same data or not.
        """
        if other_handle._data_column_group == self._data_column_group:
            columns = list(self._data_column_group)
            for j, k in zip(self._indices, other_handle._indices):
                temp = columns[j]
                columns[j] = columns[k]
                columns[k] = temp

            self._data_column_group.replace_columns(columns)
        else:
            columns = list(self._data_column_group)
            other_columns = list(other_handle._data_column_group)
            for j, k in zip(self._indices, other_handle._indices):
                temp = columns[j]
                columns[j] = other_columns[k]
                other_columns[k] = temp

            self._data_column_group.replace_columns(columns)
            other_handle._data_column_group.replace_columns(other_columns)

    def update(self, func, col_name=None, col_type=None):
        assert len(self._indices) == 1
        column = self._column_group[0]
        index = self._indices[0]
        if col_type is None:
            col_type = self._get_new_col_type(func, column.col_type)

        if col_name is None:
            col_name = column.name

        columns = list(self._data_column_group)
        columns[index] = Column(col_name, col_type,
                                [func(v) for v in column.col_values])

        self._data_column_group.replace_columns(columns)

    def create(self, func, col_name, col_type=None, index=None):
        if col_type is None:
            col_type = self._get_new_col_type(func, Any)

        columns = list(self._data_column_group)
        column = Column(col_name, col_type,
                        [func(*vs) for vs in self._column_group.rows()])

        if index is None:
            columns.append(column)
        else:
            columns.insert(index, column)
        self._data_column_group.replace_columns(columns)

    def _get_new_col_type(self, func, default_col_type):
        try:
            col_type = func.__annotations__['return']
        except (KeyError, AttributeError):
            col_type = default_col_type
        return col_type

    def merge(self, func, col_name, col_type=None):
        if col_type is None:
            col_type = self._get_new_col_type(func, Any)

        columns = list(self._data_column_group)
        column = Column(col_name, col_type,
                        [func(*vs) for vs in self._column_group.rows()])

        columns[self._indices[0]] = column
        for i in self._indices[1:]:
            del columns[i]

        self._data_column_group.replace_columns(columns)

    def move_after(self, index):
        self._move_before(index + 1)

    def move_before(self, index):
        self._move_before(index)

    def _move_before(self, index):
        columns = list(self._data_column_group)
        new_index = index
        rev = []
        for i in reversed(self._indices):
            rev.append(columns[i])
            del columns[i]
            if i < index:
                new_index -= 1

        for col in rev:
            columns.insert(new_index, col)

        self._data_column_group.replace_columns(columns)

    def filter(self, func):
        new_rows = []
        for row in self._data_column_group.rows():
            handle_row = [row[i] for i in self._indices]
            if func(*handle_row):
                new_rows.append(row)

        self._data_column_group.replace_rows(new_rows)

    def sort(self, func=None):
        if func is None:
            def key_func(row):
                return tuple([row[i] for i in self._indices])
        else:
            def key_func(row):
                handle_row = [row[i] for i in self._indices]
                return func(*handle_row)

        new_rows = sorted(self._data_column_group.rows(), key=key_func)
        self._data_column_group.replace_rows(new_rows)

    def ijoin(self, other_handle: "DataHandle", func=None):
        if func is None:
            def func(vs1, vs2):
                return vs1 == vs2

        new_rows = []
        for row in self._data_column_group.rows():
            handle_row = tuple([row[i] for i in self._indices])
            for other_row in other_handle._data_column_group.rows():
                other_handle_row = tuple(
                    [other_row[i] for i in other_handle._indices])
                if func(handle_row, other_handle_row):
                    new_rows.append(row + other_row)

        columns = [Column(col.name, col.col_type, []) for col in
                   itertools.chain(self._data_column_group,
                                   other_handle._data_column_group)]
        column_group = ColumnGroup(columns)
        column_group.replace_rows(new_rows)
        self._data_column_group.replace_columns(column_group.columns)

    def ljoin(self, other_handle: "DataHandle", func=None):
        if func is None:
            def func(vs1, vs2):
                return vs1 == vs2

        new_rows = []
        for row in self._data_column_group.rows():
            handle_row = tuple([row[i] for i in self._indices])
            found = False
            for other_row in other_handle._data_column_group.rows():
                other_handle_row = tuple(
                    [other_row[i] for i in other_handle._indices])
                if func(handle_row, other_handle_row):
                    found = True
                    new_rows.append(row + other_row)
            if not found:
                new_rows.append(
                    row + tuple([None] * len(other_handle._data_column_group)))

        columns = [Column(col.name, col.col_type, []) for col in
                   itertools.chain(self._data_column_group,
                                   other_handle._data_column_group)]
        column_group = ColumnGroup(columns)
        column_group.replace_rows(new_rows)
        self._data_column_group.replace_columns(column_group.columns)

    def rjoin(self, other_handle: "DataHandle", func=None):
        if func is None:
            def func(vs1, vs2):
                return vs1 == vs2

        new_rows = []
        for other_row in other_handle._data_column_group.rows():
            other_handle_row = tuple(
                [other_row[i] for i in other_handle._indices])
            found = False
            for row in self._data_column_group.rows():
                handle_row = tuple([row[i] for i in self._indices])
                if func(handle_row, other_handle_row):
                    found = True
                    new_rows.append(row + other_row)
            if not found:
                new_rows.append(
                    tuple([None] * len(self._data_column_group)) + other_row)

        columns = [Column(col.name, col.col_type, []) for col in
                   itertools.chain(self._data_column_group,
                                   other_handle._data_column_group)]
        column_group = ColumnGroup(columns)
        column_group.replace_rows(new_rows)
        self._data_column_group = column_group

    def ojoin(self, other_handle: "DataHandle", func=None):
        if func is None:
            def func(vs1, vs2):
                return vs1 == vs2

        new_rows = []
        other_rows = list(other_handle._data_column_group.rows())
        other_rows_not_found = list(other_rows)
        for row in self._data_column_group.rows():
            handle_row = tuple([row[i] for i in self._indices])
            found = False
            for i, other_row in enumerate(other_rows):
                other_handle_row = tuple(
                    [other_row[i] for i in other_handle._indices])
                if func(handle_row, other_handle_row):
                    found = True
                    other_rows_not_found[i] = None
                    new_rows.append(row + other_row)
            if not found:
                new_rows.append(
                    row + tuple([None] * len(other_handle._data_column_group)))

        for other_row in filter(None, other_rows_not_found):
            new_rows.append(
                tuple([None] * len(self._data_column_group)) + other_row)

        columns = [Column(col.name, col.col_type, []) for col in
                   itertools.chain(self._data_column_group,
                                   other_handle._data_column_group)]
        column_group = ColumnGroup(columns)
        column_group.replace_rows(new_rows)
        self._data_column_group = column_group

    def grouper(self):
        return DataGrouper(self._data_column_group, self._indices,
                           self._column_group)


class Data2:
    def __init__(self, column_group: ColumnGroup, data_source: DataSource):
        self._column_group = column_group
        self._data_source = data_source

    def __getitem__(self, item):
        indices = to_indices(len(self._column_group), item)
        column_group = ColumnGroup(
            [self._column_group[i] for i in indices])
        return DataHandle(self._column_group, indices, column_group)

    def show(self, limit: int = 100):
        self.as_handle().show(limit)

    def as_handle(self) -> DataHandle:
        return DataHandle(self._column_group,
                          list(range(len(self._column_group))),
                          self._column_group)

    def copy(self) -> "Data2":
        return Data2(self._column_group.copy(), self._data_source)
