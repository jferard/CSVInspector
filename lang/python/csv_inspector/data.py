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
import statistics
import sys
from itertools import islice
from pathlib import Path
from typing import List, Any, Mapping, Type, Union

from mcsv import data_type_to_field_description, open_csv
from mcsv.field_description import (DataType, FieldDescription,
                                    python_type_to_data_type)
from mcsv.field_descriptions import TextFieldDescription
from mcsv.meta_csv_data import MetaCSVData, MetaCSVDataBuilder

from csv_inspector.util import (begin_csv, end_csv, ColumnGroup, to_indices,
                                Column, ColInfo)


class DataSource:
    @staticmethod
    def create(table_name: str, path: str,
               meta_csv_data: MetaCSVData) -> "DataSource":
        desc_by_dt = {
            desc.get_data_type(): desc
            for desc in meta_csv_data.field_description_by_index.values()
        }
        if DataType.DECIMAL not in desc_by_dt:
            try:
                desc_by_dt[DataType.DECIMAL] = desc_by_dt[
                    DataType.CURRENCY_DECIMAL]._decimal_description
            except KeyError:
                pass
            try:
                desc_by_dt[DataType.DECIMAL] = desc_by_dt[
                    DataType.PERCENTAGE_DECIMAL]._decimal_description
            except KeyError:
                pass
        if DataType.FLOAT not in desc_by_dt:
            try:
                desc_by_dt[DataType.FLOAT] = desc_by_dt[
                    DataType.PERCENTAGE_FLOAT]._float_description
            except KeyError:
                pass
        if DataType.INTEGER not in desc_by_dt:
            try:
                desc_by_dt[DataType.INTEGER] = desc_by_dt[
                    DataType.CURRENCY_INTEGER]._integer_description
            except KeyError:
                pass
        return DataSource(table_name, path, meta_csv_data, desc_by_dt)

    def __init__(self, table_name: str, path: str,
                 meta_csv_data: MetaCSVData,
                 desc_by_dt: Mapping[
                     DataType, FieldDescription]) -> "DataSource":
        self._table_name = table_name
        self._path = path
        self.meta_csv_data = meta_csv_data
        self._description_by_data_type = desc_by_dt

    def get_description(self, col_info: ColInfo) -> FieldDescription:
        if isinstance(col_info, FieldDescription):
            return col_info
        if isinstance(col_info, DataType):
            data_type = col_info
        else:
            data_type = python_type_to_data_type(col_info)

        try:
            return self._description_by_data_type[data_type]
        except KeyError:  # datatype not present
            return data_type_to_field_description(data_type)


class Agg:
    def __init__(self, indices: List[int], column_group: ColumnGroup, func,
                 col_type):
        self.indices = indices
        self.column_group = column_group
        self.func = func
        self.col_type = col_type


class DataGrouperHandle:
    def __init__(self, data_grouper: "DataGrouper", indices: List[int],
                 column_group: ColumnGroup):
        self._data_grouper = data_grouper
        self._indices = indices
        self._column_group = column_group

    def agg(self, func, col_type=None):
        """
        Add a new aggregation.
        """
        self._data_grouper._new_agg(Agg(
            self._indices, self._column_group, func, col_type))


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

    def _new_agg(self, agg: Agg):
        self._aggs.append(agg)

    def group(self):
        """
        Group the agg columns by Grouper columns.
        """
        indices = set(self._indices)
        funcs = {}
        col_types = {}
        for agg in self._aggs:
            for c in agg.indices:
                funcs[c] = agg.func
                col_type = agg.col_type
                if col_type is not None:
                    col_types[c] = col_type
        agg_cols = sorted(funcs)
        for c in self._indices:
            if c in agg_cols:
                agg_cols.remove(c)

        vs_list_by_key = {}
        for row in self._data_column_group.rows():
            key = tuple([row[i] for i in indices])
            if key not in vs_list_by_key:
                vs_list_by_key[key] = [[] for _ in agg_cols]
            for c, col in enumerate(agg_cols):
                vs_list_by_key[key][c].append(row[col])

        new_rows = []
        for key, vs_list in vs_list_by_key.items():
            xs = [None] * len(agg_cols)
            for c, vs in enumerate(vs_list):
                func = funcs[agg_cols[c]]
                xs[c] = func(vs)
            new_rows.append(key + tuple(xs))

        columns = [col for i, col in enumerate(self._data_column_group) if
                   i in indices or i in agg_cols]
        for c in agg_cols:
            if c in col_types:
                columns[c].col_type = col_types[c]
        for col, col_values in zip(columns, zip(*new_rows)):
            col.col_values = col_values

        self._data_column_group.replace_columns(columns)


class DataHandle:
    def __init__(self, data_column_group: ColumnGroup, indices: List[int]):
        self._indices = indices
        self._data_column_group = data_column_group

    def show(self, limit: int = 100):
        """
        Show the first rows of this DataHandle.
        Expected format: CSV with comma
        """
        writer = csv.writer(sys.stdout, delimiter=',')
        begin_csv()
        writer.writerow(
            [col.col_type for i, col in enumerate(self._data_column_group) if
             i in self._indices])
        writer.writerow(
            [col.name for i, col in enumerate(self._data_column_group) if
             i in self._indices])
        writer.writerows(self._rows(limit))
        sys.stdout.flush()
        end_csv()

    # TODO: __getitem__ -> row

    def _rows(self, limit: int = 100):
        return islice(self._data_column_group.rows(self._indices), limit)

    def select(self):
        """
        Select the indices of the handle and drop the other indices.

        Syntax: `data[x].select()`

        * `x` is an index, slice or tuple of slices/indices

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

        Syntax: `data[x].drop()`

        * `x` is an index, slice or tuple of slices/indices

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

        Syntax: `data1[x].swap(data2[y])`

        * `x` and `y` are indices, slices or tuples of slices/indices

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

        Syntax: `data[x].create(func, col_name, [col_type, [index]])`

        * `x` is an index, slice or tuple of slices/indices of column_index
        * `func` is the function to apply to `x` values
        * `col_name` is the name of the new column
        * `col_type` is the type of the new column
        * `index` is the index of the new column
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
                        [func(*vs) for vs in
                         self._data_column_group.rows(self._indices)])

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

        Syntax: `data[x].merge(func, col_name, [col_type])`

        * `x` is an index, slice or tuple of slices/indices of column_index
        * `func` is the function to apply to `x` values
        * `col_name` is the name of the new column
        * `col_type` is the type of the new column

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
                        [func(*vs) for vs in
                         self._data_column_group.rows(self._indices)])

        columns[self._indices[0]] = column

        self._data_column_group.replace_columns(columns)

    def move_after(self, index):
        """
        Move some column_group after a given index.

        Syntax `data[x].move_after(idx)`

        * `x` is an index, slice or tuple of slices/indices of column_index
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

        Syntax `data[x].move_before(idx)`

        * `x` is an index, slice or tuple of slices/indices of column_index
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

        Syntax: `data[x].filter(func)`

        * `x` is an index, slice or tuple of slices/indices.
        * `func` is a function that takes the `x` values and returns a boolean

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
        indices = set(self._indices)
        new_rows = []
        for row in self._data_column_group.rows():
            vs = [row[i] for i in indices]
            if func(*vs):
                new_rows.append(row)

        self._data_column_group.replace_rows(new_rows)

    def sort(self, func=None, reverse=False):
        """
        Sort the rows.

        Syntax: `data[x].rsort(func)`

        * `x` is the index, slice or tuple of slices/indices of the key
        * `func` is the key function

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
        indices = set(self._indices)
        if func is None:
            def key_func(row):
                return tuple([row[i] for i in indices])
        else:
            def key_func(row):
                handle_row = [row[i] for i in indices]
                return func(*handle_row)

        new_rows = sorted(self._data_column_group.rows(), key=key_func,
                          reverse=reverse)
        self._data_column_group.replace_rows(new_rows)

    def rsort(self, func=None):
        """
        Sort the rows in reverse order.

        Syntax: `data[x].rsort(func)`

        * `x` is the index, slice or tuple of slices/indices of the key
        * `func` is the key function

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

        * `x` is the index, slice or tuple of slices/indices of the key
        * `names` is a list of new names

        >>> test_data = original_test_data.copy()
        >>> print(test_data)
         A B C D
         1 3 2 4
         5 2 2 7
         3 4 7 8
        >>> test_data[1, 3].rename(["b", "d"])
        >>> print(test_data)
         A b C d
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

        * `x` is the index, slice or tuple of slices/indices of the key
        * `data2` is another `Data` object
        * `y` is the index, slice or tuple of slices/indices of the other key
        * `func` is the function to compare the `x` and `y` values

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

        indices = set(self._indices)
        other_indices = set(other_handle._indices)
        new_rows = []
        for row in self._data_column_group.rows():
            key = tuple([row[i] for i in indices])
            for other_row in other_handle._data_column_group.rows():
                other_key = tuple([other_row[i] for i in other_indices])
                if func(key, other_key):
                    new_rows.append(row + other_row)

        self._append_other_columns_and_put_rows(other_handle, new_rows)

    def _append_other_columns_and_put_rows(self, other_handle: "DataHandle",
                                           new_rows):
        columns = [Column(col.name, col.col_type, []) for col in
                   itertools.chain(self._data_column_group,
                                   other_handle._data_column_group)]
        column_group = ColumnGroup(columns)
        column_group.replace_rows(new_rows)
        self._data_column_group.replace_columns(column_group.columns)

    def ljoin(self, other_handle: "DataHandle", func=None):
        """
        Make an inner join between two data sets.

        Syntax: `data1[x].ljoin(data2[y], func)`

        * `x` is the index, slice or tuple of slices/indices of the key
        * `data2` is another `Data` object
        * `y` is the index, slice or tuple of slices/indices of the other key
        * `func` is the function to compare the `x` and `y` values

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

        indices = set(self._indices)
        other_indices = set(other_handle._indices)
        new_rows = []
        for row in self._data_column_group.rows():
            key = tuple([row[i] for i in indices])
            found = False
            for other_row in other_handle._data_column_group.rows():
                other_key = tuple(
                    [other_row[i] for i in other_indices])
                if func(key, other_key):
                    found = True
                    new_rows.append(row + other_row)
            if not found:
                new_rows.append(
                    row + tuple([None] * len(other_handle._data_column_group)))

        self._append_other_columns_and_put_rows(other_handle, new_rows)

    def rjoin(self, other_handle: "DataHandle", func=None):
        """
        Make an right join between two data sets.

        Syntax: `data1[x].rjoin(data2[y], func)`

        * `x` is the index, slice or tuple of slices/indices of the key
        * `data2` is another `Data` object
        * `y` is the index, slice or tuple of slices/indices of the other key
        * `func` is the function to compare the `x` and `y` values

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

        indices = set(self._indices)
        other_indices = set(other_handle._indices)
        new_rows = []
        for other_row in other_handle._data_column_group.rows():
            other_key = tuple([other_row[i] for i in other_indices])
            found = False
            for row in self._data_column_group.rows():
                key = tuple([row[i] for i in indices])
                if func(key, other_key):
                    found = True
                    new_rows.append(row + other_row)
            if not found:
                new_rows.append(
                    tuple([None] * len(self._data_column_group)) + other_row)

        self._append_other_columns_and_put_rows(other_handle, new_rows)

    def ojoin(self, other_handle: "DataHandle", func=None):
        """
        Make an outer join between two data sets.

        Syntax: `data1[x].ojoin(data2[y], func)`

        * `x` is the index, slice or tuple of slices/indices of the key
        * `data2` is another `Data` object
        * `y` is the index, slice or tuple of slices/indices of the other key
        * `func` is the function to compare the `x` and `y` values

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

        indices = set(self._indices)
        other_indices = set(other_handle._indices)
        new_rows = []
        other_rows = list(other_handle._data_column_group.rows())
        other_rows_not_found = list(other_rows)
        for row in self._data_column_group.rows():
            key = tuple([row[i] for i in indices])
            found = False
            for i, other_row in enumerate(other_rows):
                other_key = tuple([other_row[i] for i in other_indices])
                if func(key, other_key):
                    found = True
                    other_rows_not_found[i] = None
                    new_rows.append(row + other_row)
            if not found:
                new_rows.append(
                    row + tuple([None] * len(other_handle._data_column_group)))

        for other_row in filter(None, other_rows_not_found):
            new_rows.append(
                tuple([None] * len(self._data_column_group)) + other_row)

        self._append_other_columns_and_put_rows(other_handle, new_rows)

    def grouper(self) -> DataGrouper:
        """
        Create a grouper on some rows.

        ```
        g = data[x].grouper()
        g[y].agg(func)
        g.group()
        ```

        Syntax: `g = data[x].grouper()`

        * `x` is the index, slice or tuple of slices/indices of the rows
        * `y` is the index, slice or tuple of slices/indices of the aggregate columns
        * `func` is aggregate function

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

    def stats(self):
        """
        Show stats on the data

        Syntax: `data.stats()`
        """

        def aggregate(func, vs):
            try:
                return func(vs)
            except:
                return "-"

        writer = csv.writer(sys.stdout, delimiter=',')
        begin_csv()
        writer.writerow(
            ["str", "object", "type", "int", "comparable", "comparable",
             "comparable", "comparable"])
        writer.writerow(
            ["key", "value", "type", "null count", "min", "max", "mean",
             "median"])
        writer.writerow(
            ["line count", len(self._data_column_group.columns[0]),
             "-", "-", "-", "-", "-"])
        writer.writerow(
            ["column count", len(self._data_column_group),
             "-", "-", "-", "-", "-"])
        for i, column in enumerate(self._data_column_group):
            vs = [v for v in column.col_values if v is not None]
            null_count = len(column.col_values) - len(vs)
            if column.col_type == str:
                writer.writerow(
                    [f"column {i}", column.name, column.col_type, null_count,
                     "-", "-", "-", "-"])
            else:
                vs_min = aggregate(min, vs)
                vs_max = aggregate(max, vs)
                vs_mean = aggregate(statistics.mean, vs)
                vs_median = aggregate(statistics.median, vs)
                writer.writerow(
                    [f"column {i}", column.name, column.col_type, null_count,
                     vs_min, vs_max, vs_mean, vs_median])

        sys.stdout.flush()
        end_csv()


class Data:
    def __init__(self, column_group: ColumnGroup, data_source: DataSource):
        self._column_group = column_group
        self._data_source = data_source

    def __getitem__(self, item):
        indices = to_indices(len(self._column_group), item)
        column_group = ColumnGroup(
            [self._column_group[i] for i in indices])
        return DataHandle(self._column_group, indices)

    def show(self, limit: int = 100):
        """
        Show the first rows of this DataHandle.
        Expected format: CSV with comma
        """
        self.as_handle().show(limit)

    def stats(self):
        """
        Show stats on the data
        """
        self.as_handle().stats()

    def grouper(self) -> DataGrouper:
        """
        Return a grouper
        """
        return DataGrouper(self._column_group, [])

    def as_handle(self) -> DataHandle:
        return DataHandle(self._column_group,
                          list(range(len(self._column_group))))

    def copy(self) -> "Data":
        """
        Return a copy of this data object.
        """
        return Data(self._column_group.copy(), self._data_source)

    def __str__(self) -> str:
        return str(self._column_group)

    def __repr__(self) -> str:
        return f"Data{self._column_group}"

    def save_as(self, path: Union[str, Path], canonical=True):
        """
        :param canonical: if true, fields format is canonical. If false,
        CSVInspector will try to keep the data in the original format.
        """
        if isinstance(path, str):
            path = Path(path)

        meta_csv_data = self._get_meta_csv_data(canonical)

        with open_csv(path, "w", data=meta_csv_data) as writer:
            writer.writeheader([col.name for col in self._column_group])
            for row in self._column_group.rows():
                writer.writerow(row)

    def _get_meta_csv_data(self, canonical):
        if canonical:
            b = MetaCSVDataBuilder()
            for i, col in enumerate(self._column_group):
                if isinstance(col.col_info, FieldDescription):
                    description = col.col_info
                elif isinstance(col.col_info, DataType):
                    description = data_type_to_field_description(col.col_info)
                elif isinstance(col.col_info, Type):
                    description = data_type_to_field_description(
                        python_type_to_data_type(col.col_info))
                else:
                    description = TextFieldDescription.INSTANCE
                b.description_by_col_index(i, description)
            meta_csv_data = b.build()
        else:
            b = MetaCSVDataBuilder()
            cur_data = self._data_source.meta_csv_data
            b.encoding(cur_data.encoding)
            b.bom(cur_data.bom)
            b._dialect = cur_data.dialect
            for i, col in enumerate(self._column_group):
                description = self._data_source.get_description(col.col_info)
                b.description_by_col_index(i, description)
            meta_csv_data = b.build()
        return meta_csv_data


if __name__ == "__main__":
    import doctest

    doctest.testmod(
        extraglobs={'original_test_data': Data(ColumnGroup([
            Column("A", int, [1, 5, 3]),
            Column("B", int, [3, 2, 4]),
            Column("C", int, [2, 2, 7]),
            Column("D", int, [4, 7, 8])
        ]), None)})
