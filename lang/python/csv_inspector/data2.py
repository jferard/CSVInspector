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
        self._data_grouper._new_agg(self._indices, self._column_group, func,
                                    col_type)


class DataGrouper:
    def __init__(self, data_column_group: ColumnGroup, indices: List[int]):
        self._data_column_group = data_column_group
        self._indices = indices
        self._aggs = []

    def __getitem__(self, item):
        indices = to_indices(len(self._data_column_group), item)
        column_group = ColumnGroup(
            [self._data_column_group[i] for i in indices])
        return DataGrouperHandle(self, indices, column_group)

    def _new_agg(self, indices: List[int], column_group: ColumnGroup, func,
                 col_type):
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
        # self._column_group = column_group

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
        return islice(self._data_column_group.rows(self._indices), limit)

    def select(self):
        """
        Select the indices of the handle and drop the other indices.

        Syntax: `data[x].drop()`.

        `x` is an index, slice or tuple of slices/indices

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[0, 2].select()
        >>> print(test_data)
         A C
         1 2
         5 2
         3 7
        """
        self._data_column_group.replace_columns(
            [col for i, col in enumerate(self._data_column_group) if
             i in self._indices])

    def drop(self):
        """
        Drop the indices of the handle and select the other indices.

        Syntax: `data[x].drop()`.

        `x` is an index, slice or tuple of slices/indices

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[0, 2:].drop()
        >>> print(test_data)
         B
         3
         2
         4
        """
        columns = [c for i, c in enumerate(self._data_column_group)
                   if i not in self._indices]
        self._data_column_group.replace_columns(columns)

    def swap(self, other_handle: "DataHandle"):
        """
        Swap two handles. Those handles may be backed by the same data or not.

        Syntax: `data1[x].swap(data2[y])

        `x` and `y` are indices, slices or tuples of slices/indices

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[0, 2].swap(test_data[1, 3])
        >>> print(test_data)
         B A D C
         3 1 4 2
         2 5 7 2
         4 3 8 7
        """
        if other_handle._data_column_group == self._data_column_group:
            columns = self._data_column_group.columns
            for j, k in zip(self._indices, other_handle._indices):
                temp = columns[j]
                columns[j] = columns[k]
                columns[k] = temp
        else:
            columns = self._data_column_group.columns
            other_columns = other_handle._data_column_group.columns
            for j, k in zip(self._indices, other_handle._indices):
                temp = columns[j]
                columns[j] = other_columns[k]
                other_columns[k] = temp

    def update(self, func, col_name=None, col_type=None):
        """
        Update some column using a function.

        Syntax: `data[x].update(func)`

        * `x` is an index
        * `func` is a function of `data[x]` (use numeric indices)
        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[1].update(lambda x: x*3)
        >>> print(test_data)
         A  B C D
         1  9 2 4
         5  6 2 7
         3 12 7 8
        """
        assert len(self._indices) == 1
        index = self._indices[0]
        column = self._data_column_group[index]
        if col_type is None:
            col_type = self._get_new_col_type(func, column.col_type)

        if col_name is None:
            col_name = column.name

        columns = self._data_column_group.columns
        columns[index] = Column(col_name, col_type,
                                [func(v) for v in column.col_values])

    def create(self, func, col_name, col_type=None, index=None):
        """
        Create a new col

        Syntax: data[x].create(func, col_name, [col_type, [index]])

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[:3].create(lambda x, y, z: x+y+z, "E", int, 1)
        >>> print(test_data)
         A  E B C D
         1  6 3 2 4
         5  9 2 2 7
         3 14 4 7 8
        """
        if col_type is None:
            col_type = self._get_new_col_type(func, Any)

        columns = self._data_column_group.columns
        column = Column(col_name, col_type,
                        [func(*[v for i, v in enumerate(vs) if
                                i in self._indices]) for vs in
                         self._data_column_group.rows()])

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
        """
        Create a new col by merging some columns. Those columns are
        consumed during the process.

        Syntax: data[x].merge(func, col_name, [col_type])

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[:3].merge(lambda x, y, z: x+y+z, "E", int)
        >>> print(test_data)
          E D
          6 4
          9 7
         14 8
        """
        if col_type is None:
            col_type = self._get_new_col_type(func, Any)

        # TODO: check if indices are always sorted
        columns = [col for i, col in enumerate(self._data_column_group.columns)
                   if i not in self._indices[1:]]
        column = Column(col_name, col_type,
                        [func(*[v for i, v in enumerate(vs) if
                                i in self._indices]) for vs in
                         self._data_column_group.rows()])

        columns[self._indices[0]] = column

        self._data_column_group.replace_columns(columns)

    def move_after(self, index):
        """
        Move some column_group before a given index.

        Syntax `data[x].move_before(x)`

        * `x` is an index, slice or tuple of slices/indices of column_index that
        should move before `idx`.
        * `idx` is the destination index

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[-2:].move_after(0)
        >>> print(test_data)
         A C D B
         1 2 4 3
         5 2 7 2
         3 7 8 4
         """
        self._move_before(index + 1)

    def move_before(self, index):
        """
        Move some column_group before a given index.

        Syntax `data[x].move_before(x)`

        * `x` is an index, slice or tuple of slices/indices of column_index that
        should move before `idx`.
        * `idx` is the destination index

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[-2:].move_before(0)
        >>> print(test_data)
         C D A B
         2 4 1 3
         2 7 5 2
         7 8 3 4
        """
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
        """
        Filter data on a function.

        Syntax: `data[x].filter(func)`.

        * `x` is an index, slice or tuple of slices/indices.
        * `func` is a function

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[1:3].filter(lambda x, y: x == y)
        >>> print(test_data)
         A B C D
         5 2 2 7
        """
        new_rows = []
        for row in self._data_column_group.rows():
            handle_row = [row[i] for i in self._indices]
            if func(*handle_row):
                new_rows.append(row)

        self._data_column_group.replace_rows(new_rows)

    def sort(self, func=None, reverse=False):
        """
        Sort the rows in reverse order.

        Syntax: `data[x].rsort(func)`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[1].sort()
        >>> print(test_data)
         A B C D
         5 2 2 7
         1 3 2 4
         3 4 7 8
        """
        if func is None:
            def key_func(row):
                return tuple([row[i] for i in self._indices])
        else:
            def key_func(row):
                handle_row = [row[i] for i in self._indices]
                return func(*handle_row)

        new_rows = sorted(self._data_column_group.rows(), key=key_func,
                          reverse=reverse)
        self._data_column_group.replace_rows(new_rows)

    def rsort(self, func=None):
        """
        Sort the rows in reverse order.

        Syntax: `data[x].rsort(func)`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[1].rsort()
        >>> print(test_data)
         A B C D
         3 4 7 8
         1 3 2 4
         5 2 2 7
        """
        self.sort(func, reverse=True)

    def rename(self, names):
        """
        Rename one or more columns

        Syntax: `data[x].rename(names)`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[:].rename(["a", "b", "c", "d"])
        >>> print(test_data)
         a b c d
         1 3 2 4
         5 2 2 7
         3 4 7 8
        """
        assert len(self._indices) == len(names)
        for i, name in zip(self._indices, names):
            self._data_column_group.rename(i, name)

    def ijoin(self, other_handle: "DataHandle", func=None):
        """
        Make an inner join between two data sets.

        Syntax: `data1[x].ijoin(data2[y], func)`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> test_data1 = original_test_data.copy()
        >>> test_data2 = original_test_data.copy()
        >>> test_data2[:].rename(["A'", "B'", "C'", "D'"])
        >>> print(test_data1)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data1[1].ijoin(test_data2[2], lambda x, y: x[0] == y[0])
        >>> print(test_data1)
         A B C D A' B' C' D'
         5 2 2 7  1  3  2  4
         5 2 2 7  5  2  2  7
        """
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
        """
        Make an left join between two data sets.

        Syntax: `data1[x].ljoin(data2[y], func)`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> test_data1 = original_test_data.copy()
        >>> test_data2 = original_test_data.copy()
        >>> test_data2[:].rename(["A'", "B'", "C'", "D'"])
        >>> print(test_data1)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data1[1].ljoin(test_data2[2], lambda x, y: x[0] == y[0])
        >>> print(test_data1)
         A B C D   A'   B'   C'   D'
         1 3 2 4 None None None None
         5 2 2 7    1    3    2    4
         5 2 2 7    5    2    2    7
         3 4 7 8 None None None None
        """
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
        """
        Make an right join between two data sets.

        Syntax: `data1[x].rjoin(data2[y], func)`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> test_data1 = original_test_data.copy()
        >>> test_data2 = original_test_data.copy()
        >>> test_data2[:].rename(["A'", "B'", "C'", "D'"])
        >>> print(test_data1)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data1[1].rjoin(test_data2[2], lambda x, y: x[0] == y[0])
        >>> print(test_data1)
            A    B    C    D A' B' C' D'
            5    2    2    7  1  3  2  4
            5    2    2    7  5  2  2  7
         None None None None  3  4  7  8
         """
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
        self._data_column_group.replace_columns(column_group.columns)

    def ojoin(self, other_handle: "DataHandle", func=None):
        """
        Make an outer join between two data sets.

        Syntax: `data1[x].ojoin(data2[y], func)`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> test_data1 = original_test_data.copy()
        >>> test_data2 = original_test_data.copy()
        >>> test_data2[:].rename(["A'", "B'", "C'", "D'"])
        >>> print(test_data1)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data1[1].ojoin(test_data2[2], lambda x, y: x[0] == y[0])
        >>> print(test_data1)
            A    B    C    D   A'   B'   C'   D'
            1    3    2    4 None None None None
            5    2    2    7    1    3    2    4
            5    2    2    7    5    2    2    7
            3    4    7    8 None None None None
         None None None None    3    4    7    8
         """
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
        self._data_column_group.replace_columns(column_group.columns)

    def grouper(self):
        """
        Group some rows.

        Syntax: `g = data[x].grouper()`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> test_data = original_test_data.copy()
        >>> test_data[0].update(lambda x: x%2)
        >>> print(test_data)
         A B C D
         1 3 2 4
         1 2 2 7
         1 4 7 8
        >>> g = test_data[0].grouper()
        >>> g[1].agg(max)
        >>> g[2].agg(min)
        >>> g[3].agg(sum)
        >>> g.group()
        >>> print(test_data)
         A B C  D
         1 4 2 19
        """
        return DataGrouper(self._data_column_group, self._indices)


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

    def __str__(self) -> str:
        return str(self._column_group)

    def __repr__(self) -> str:
        return f"Data2{self._column_group}"


if __name__ == "__main__":
    import doctest

    doctest.testmod(extraglobs={'original_test_data': Data2(ColumnGroup([
        Column("A", int, [1, 5, 3]), Column("B", int, [3, 2, 4]),
        Column("C", int, [2, 2, 7]), Column("D", int, [4, 7, 8])
    ]), None)})
