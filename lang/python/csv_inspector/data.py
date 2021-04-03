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
import csv
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (Union, Callable, Tuple, Iterable, Any, List, Sequence,
                    Mapping, Type, Optional, Collection)

from typing.io import IO

from csv_inspector.bulk_query_provider import get_provider
from csv_inspector.util import (end_csv, begin_csv, to_standard, begin_info,
                                end_info, to_indices, SomeIndices,
                                _get_col_dtype, is_some_indices, ColumnGroup,
                                Column, T)


class DataSwap:
    """
    Swap two column_group or ranges [first range][second range].
    """

    def __init__(self, data: "Data"):
        self._data = data
        self._source = None

    def __getitem__(self, item: SomeIndices) -> Union[
        "DataSwap", "Data"]:
        assert is_some_indices(item)
        if self._source is None:
            return self._init_source(item)
        else:
            return self._swap_source_with(item)

    def _init_source(self, item: SomeIndices):
        self._source = item
        return self

    def _swap_source_with(self, item: SomeIndices):
        source_indices = self._data._to_indices(self._source)
        dest_indices = self._data._to_indices(item)
        for i, j in zip(source_indices, dest_indices):
            self._data._swap_cols(i, j)
        return self._data


class DataMove(ABC):
    def __init__(self, data: "Data"):
        self._data = data
        self._pivot_index = None

    def __getitem__(self, item: Union[int, SomeIndices]) -> Union[
        "DataMove", "Data"]:
        if self._pivot_index is None:
            assert isinstance(item, int)
            return self._init_pivot(item)
        else:
            assert is_some_indices(item)
            return self._move_before(item)

    def _init_pivot(self, item: int):
        self._pivot_index = item % self._data.column_count()
        return self

    def _move_before(self, item: SomeIndices):
        indices_to_move = self._data._to_indices(item)
        self._move_columns(self._pivot_index, indices_to_move)
        return self._data

    @abstractmethod
    def _move_columns(self, pivot_index: int, new_indices: Collection[int]):
        pass


class DataMoveBefore(DataMove):
    """
    Move indices before: [index][to_move]
    """

    def __init__(self, data):
        DataMove.__init__(self, data)

    def _move_columns(self, pivot_index: int, indices: Collection[int]):
        self._data._move_before(pivot_index, indices)


class DataMoveAfter(DataMove):
    """
    Move indices after: [index][to_move]
    """

    def __init__(self, data):
        DataMove.__init__(self, data)

    def _move_columns(self, pivot_index: int, indices: Collection[int]):
        self._data._move_after(pivot_index, indices)


class DataSelect:
    """
    Select indices: [indices]
    """

    def __init__(self, data: "Data"):
        self._data = data

    def __getitem__(self, item: SomeIndices) -> "Data":
        indices = self._data._to_indices(item)
        self._data._select_indices(indices)
        return self._data


class DataDrop(object):
    """
    Drop indices: [indices]
    """

    def __init__(self, data: "Data"):
        self._data = data

    def __getitem__(self, item: SomeIndices) -> "Data":
        indices = self._data._to_indices(item)
        self._data._drop_indices(indices)
        return self._data


class DataAdd:
    """
    Add a column_index: [func, name, index]
    """

    def __init__(self, data: "Data"):
        self._data = data

    def __getitem__(self, item: Union[
        Tuple[Callable, str], Tuple[Callable, str, int]]) -> "Data":
        func, name, *index = item
        col_type = func.__annotations__.get('return', Any)
        if index:
            index = index[0]
            self._data._insert_col(name, col_type, self._data._apply(func), index)
        else:
            self._data._append_col(name, col_type, self._data._apply(func))
        return self._data


class DataMerge:
    """
    Merge some indices: [indices][func, name]
    """

    def __init__(self, data: "Data"):
        self._data = data
        self._source = None

    def __getitem__(self, item: Union[SomeIndices, Tuple[Callable, str]]
                    ) -> Union["DataMerge", "Data"]:
        if self._source is None:
            assert is_some_indices(item)
            return self._init_to_merge(item)
        else:
            assert isinstance(item, Tuple)
            return self._merge(item)

    def _init_to_merge(self, item: SomeIndices) -> "DataMerge":
        self._source = self._data._to_indices(item)
        return self

    def _merge(self, item: Tuple[Callable, str]) -> "Data":
        func, name = item

        def f(vs):
            return func([v for i, v in enumerate(vs) if i in self._source])

        col_type = func.__annotations__.get('return', Any)

        self._data._append_col(name, col_type, self._data._apply(f))
        self._data._drop_indices(self._source)
        return self._data


class DataGroupBy:
    """
    Group by index: [grouped][fun
    """

    def __init__(self, data: "Data"):
        self._data = data
        self._grouped = None

    def __getitem__(self, item):
        if self._grouped is None:
            self._grouped = item
            return self
        else:
            grouped_indices = self._data._to_indices(self._grouped)
            func_by_colindex = self._get_func_by_colindex(grouped_indices, item)
            self._data._group_by(grouped_indices, func_by_colindex)
            return self._data

    def _get_func_by_colindex(self, grouped_indices: List[int],
                              item: Union[Tuple[SomeIndices, ...], Callable]
                              ) -> Mapping[int, Callable]:
        columns = self._data.columns()
        length = len(columns)
        func_by_colindex = {}
        if isinstance(item, tuple):
            while len(item) >= 2:
                indices, func, *item = item
                for i in self._data._to_indices(indices):
                    if not (i in grouped_indices or i in func_by_colindex):
                        func_by_colindex[i] = func
            if len(item):  # a last func for remaining indices
                func = item[0]
                for i in range(length):
                    if not (i in grouped_indices or i in func_by_colindex):
                        func_by_colindex[i] = func
        else:  # a single function
            for i in range(length):
                if i not in grouped_indices:
                    func_by_colindex[i] = item
        return func_by_colindex


class DataJoin:
    """
    Make a join between two tables: [other][left][right]
    """

    def __init__(self, data: "Data", how: str):
        self._data = data
        self._how = how
        self._other = None

    def __getitem__(self, item: Union["Data", SomeIndices, SomeIndices]
                    ) -> Union["DataJoin", "Data"]:
        if self._other is None:
            assert isinstance(item, Data)
            self._other = item
            return self
        else:
            if isinstance(item, tuple):
                left_on, right_on = item
            else:
                left_on = right_on = item
            left_indices = self._data._to_indices(left_on)
            right_indices = self._other._to_indices(right_on)
            self._data._merge_data(self._other, self._how, left_indices,
                                   right_indices)
            return self._data


class DataFilter:
    def __init__(self, data: "Data"):
        self._data = data

    def __getitem__(self, item: Union[Tuple[Callable], Callable]) -> "Data":
        if isinstance(item, tuple):
            for func in item:
                self._data._filter(func)
        else:
            self._data._filter(item)
        return self._data


class DataMap:
    def __init__(self, data: "Data"):
        self._data = data
        self._target = None

    def __getitem__(self, item: SomeIndices) -> Union["DataMap", "Data"]:
        if self._target is None:
            return self._init_target(item)
        else:
            target_indices = self._data._to_indices(self._target)
            for i in target_indices:
                self._data._map_col(i, item)
            return self._data

    def _init_target(self, item):
        self._target = item
        return self


class DataMapIf:
    def __init__(self, data: "Data"):
        self._data = data
        self._target = None

    def __getitem__(self, item: Union[SomeIndices,
                                      Tuple[Callable, Callable, Callable]]
                    ) -> Union["DataMapIf", "Data"]:
        if self._target is None:
            self._target = item
            return self
        else:
            test, if_true, if_false = item
            target_indices = self._data._to_indices(self._target)
            for i in target_indices:
                self._data._map_if(i, test, if_true, if_false)
            return self._data


class DataSort:
    def __init__(self, data: "Data", reverse: bool):
        self._data = data
        self._reverse = reverse

    def __getitem__(self, item: SomeIndices) -> "Data":
        indices = self._data._to_indices(item)
        self._data._sort_values(indices, not self._reverse)
        return self._data


class DataSource:
    def __init__(self, table_name: str, path: str,
                 encoding: str, csvdialect: csv.Dialect) -> "DataSource":
        self._table_name = table_name
        self._path = path
        self._encoding = encoding
        self._csvdialect = csvdialect


class Data:
    """
    """
    @staticmethod
    def create(column_group: ColumnGroup, table_name: str, path: str,
                 encoding: str, csvdialect: csv.Dialect) -> "Data":
        data_source = DataSource(table_name, path, encoding, csvdialect)
        return Data(column_group, data_source)

    @staticmethod
    def from_rows(types: Sequence[Type],
                  rows: Iterable[Sequence[Any]]) -> "Data":
        return Data(ColumnGroup.from_rows(types, rows), None)

    def __init__(self, column_group: ColumnGroup, data_source: Optional[DataSource]) -> "Data":
        self._column_group = column_group
        self._data_source = data_source

    def __getitem__(self, item: Union[int, str]) -> Column:
        """
        >>> _data = Data(ColumnGroup([
        ...         Column[int]("A", int, [1, 5, 3]),
        ...         Column[int]("B", int, [3, 2, 4]),
        ...         Column[int]("C", int, [2, 2, 7]),
        ...         Column[str]("D", str, ["a", "b", "c"])))
        >>> Data(_data[0] + _data[3], "t", None, None, None)
        0     5
        1    12
        2    11
        """
        return self._column_group[item]

    def columns(self):
        return self._column_group

    def column_count(self):
        return len(self._column_group)

    @property
    def swap(self) -> DataSwap:
        """
        Swap two sets of column_group.

        Syntax: `_data.swap[x][y]`

        `x` and `y` are indices, slices or tuples of slices/indices

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.swap[0][1]
           B  A  C  D
        0  3  1  2  4
        1  2  5  2  7
        2  4  3  7  8
        """
        return DataSwap(self)

    @property
    def add(self) -> DataAdd:
        """
        Add a new column_index.

        Syntax: `_data.add[func, name, index]`

        * `func` is a function of `Data` (use numeric indices)
        * `name` is the name of the new column_index
        * `index` (opt) is the index of the new column_index

        >>> _data = Data(pd.DataFrame(
        ...     {"A":["1", "5", "3"], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.add[lambda x: x[0]*x[1], "A*B", 2]
           A  B   A*B  C  D
        0  1  3   111  2  4
        1  5  2    55  2  7
        2  3  4  3333  7  8
        """
        return DataAdd(self)

    @property
    def merge(self) -> DataMerge:
        """
        Same as `add`, but removes the merged column_group and place the new column_index
        at the first merged index.

        Syntax: `_data.merge[x][func, name]`

        * `x` is an index, a slice or a tuple of slices/indices
        * `func` is a function of `Data` (use numeric indices)
        * `name` is the name of the new column_index

        >>> _data = Data(pd.DataFrame(
        ...     {"A":["1", "5", "3"], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.merge[1,3][lambda x: x[1]*x[2], "B*D"]
           A  B*D  C
        0  1    6  2
        1  5    4  2
        2  3   28  7
        """
        return DataMerge(self)

    @property
    def groupby(self) -> DataGroupBy:
        """
        Group _data on some column_group. using an aggregation function.

        Syntax: `_data.groupby[w][x, func_x, y, func_y, ..., last_func]`

        * `w`, `x` and `y` are indices, slices or tuples of slices/indices
        * `func_x`, `func_y`, ... are functions of `Data` (use numeric indices)
        * `last_func` (opt) is a function for the remaining cols

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 1, 3, 3, 3], "B":[3, 2, 4, 7, 9],
        ...      "C":[2, 2, 7, 8, 9], "D":[4, 7, 8, 3, 5]}))
        >>> _data.groupby[0][1, 'sum', 'max']
           A   B  C  D
        0  1   5  2  7
        1  3  20  9  8
        """
        return DataGroupBy(self)

    @property
    def ljoin(self) -> DataJoin:
        """
        A left join.

        Syntax: `data1.ijoin[data2][x][y]`

        * `x` and `y` are indices, slices or tuples of slices/indices
        * `data1` and `data2` are `Data` instances

        >>> data1 = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4]}))
        >>> data2 = Data(pd.DataFrame(
        ...     {"C":[5, 2, 7], "D":[4, 7, 8]}))
        >>> data1.ljoin[data2][0][0]
           A  B    C    D
        0  1  3  NaN  NaN
        1  5  2  5.0  4.0
        2  3  4  NaN  NaN
        """
        return DataJoin(self, 'left')

    @property
    def rjoin(self) -> DataJoin:
        """
        A right join. See `ljoin`.

        >>> data1 = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4]}))
        >>> data2 = Data(pd.DataFrame(
        ...     {"C":[5, 2, 7], "D":[4, 7, 8]}))
        >>> data1.rjoin[data2][0][0]
             A    B  C  D
        0  5.0  2.0  5  4
        1  NaN  NaN  2  7
        2  NaN  NaN  7  8
        """

        return DataJoin(self, 'right')

    @property
    def ojoin(self) -> DataJoin:
        """
        An outer join. See `ljoin`.

        >>> data1 = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4]}))
        >>> data2 = Data(pd.DataFrame(
        ...     {"C":[5, 2, 7], "D":[4, 7, 8]}))
        >>> data1.ojoin[data2][0][0]
             A    B    C    D
        0  1.0  3.0  NaN  NaN
        1  5.0  2.0  5.0  4.0
        2  3.0  4.0  NaN  NaN
        3  NaN  NaN  2.0  7.0
        4  NaN  NaN  7.0  8.0
        """
        return DataJoin(self, 'outer')

    @property
    def ijoin(self) -> DataJoin:
        """
        An inner join. See `ljoin`.

        >>> data1 = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4]}))
        >>> data2 = Data(pd.DataFrame(
        ...     {"C":[5, 2, 7], "D":[4, 7, 8]}))
        >>> data1.ijoin[data2][0][0]
           A  B  C  D
        0  5  2  5  4
         """
        return DataJoin(self, 'inner')

    @property
    def filter(self) -> DataFilter:
        """
        Filter _data on a sequence of functions.

        Syntax: `_data.filter[func1, ...]`.

        `func1`, ... are functions of `Data` (use numeric indices)

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 4, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.filter[lambda x: x[0] % 2 == 1, lambda x: x[1] % 2 == 1]
           A  B  C  D
        0  1  3  2  4
        """
        return DataFilter(self)

    @property
    def move_before(self) -> DataMoveBefore:
        """
        Move some column_group before a given index.

        Syntax `_data.move_before[idx][x]`

        * `idx` is the destination index
        * `x` is an index, slice or tuple of slices/indices of column_index that
        should move before `idx`.

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.move_before[2][1,3]
           A  B  D  C
        0  1  3  4  2
        1  5  2  7  2
        2  3  4  8  7
        """
        return DataMoveBefore(self)

    @property
    def move_after(self) -> DataMoveAfter:
        """
        Move some column_group before a given index. See `move_before`.

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.move_after[2][1,3]
           A  C  B  D
        0  1  2  3  4
        1  5  2  2  7
        2  3  7  4  8
        """
        return DataMoveAfter(self)

    @property
    def select(self) -> DataSelect:
        """
        Select some of the columns.

        Syntax: `_data.select[x]`.

        `x` is an index, slice or tuple of slices/indices

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.select[0, 2:]
           A  C  D
        0  1  2  4
        1  5  2  7
        2  3  7  8
        """
        return DataSelect(self)

    @property
    def drop(self) -> DataDrop:
        """
        Drop some of the column_group.

        Syntax: `_data.drop[x]`.

        `x` is an index, slice or tuple of slices/indices

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.drop[0, 2:]
           B
        0  3
        1  2
        2  4
        """
        return DataDrop(self)

    @property
    def map(self) -> DataMap:
        """
        Map some column_group using a function.

        Syntax: `_data.map[x][func]`

        * `x` is an index, slice or tuple of slices/indices
        * `func` is a function of `Data` (use numeric indices)

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.map[0,3][lambda c: c+2]
           A  B  C   D
        0  3  3  2   6
        1  7  2  2   9
        2  5  4  7  10
        """
        return DataMap(self)

    @property
    def mapif(self) -> DataMapIf:
        """
        Map some column_group using a function.

        Syntax: `_data.mapif[x][test, if_true, if_false]

        * `x` is an index, slice or tuple of slices/indices
        * `test` is a test
        * `if_true`
        * `if_false`

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.mapif[0][_data[1]>2, _data[0], _data[1]]
           A  B  C   D
        0  3  3  2   6
        1  7  2  2   9
        2  5  4  7  10
        """
        return DataMapIf(self)

    @property
    def sort(self) -> DataSort:
        """
        Sort the rows

        Syntax: `_data.sort[x]`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.sort[1]
           A  B  C  D
        0  5  2  2  7
        1  1  3  2  4
        2  3  4  7  8
        """
        return DataSort(self, False)

    @property
    def rsort(self) -> DataSort:
        """
        Sort the rows in reverse order.

        Syntax: `_data.rsort[x]`

        `x` is the index, slice or tuple of slices/indices of the key

        >>> _data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> _data.rsort[1]
           A  B  C  D
        0  3  4  7  8
        1  1  3  2  4
        2  5  2  2  7
        """
        return DataSort(self, True)

    def __str__(self):
        return str(self._column_group)

    def show(self, limit: int = 100):
        """
        Show the first rows of Data.
        Expected format: CSV with comma
        """
        writer = csv.writer(sys.stdout, delimiter=',')
        begin_csv()
        writer.writerow([col.col_type for col in self.columns()])
        writer.writerow([col.name for col in self.columns()])
        writer.writerows(self._rows())
        sys.stdout.flush()
        end_csv()

    def save(self, destination: Union[str, Path, IO]):
        """
        Save Data to a csv file.
        """
        self.df.to_csv(destination, index=False, encoding='utf-8')

    def guess_types(self):
        for col in self.df.columns:
            dt = _get_col_dtype(self.df[col])
            print(f"Col {col} -> {dt}")
            self.df[col] = self.df[col].astype(dt, errors='ignore')

    def show_sql(self, table_name=None, provider_name: str = 'pg'):
        if table_name is None:
            table_name = self._data_source._table_name
        else:
            table_name = to_standard(table_name)
        force_null = [col.name for col in self.columns()]

        provider = get_provider(provider_name)(self._data_source._encoding, self._data_source._csvdialect,
                                               self._data_source._path, table_name,
                                               force_null)

        begin_info()
        print(provider.drop_table())
        print(provider.create_schema())
        print(provider.prepare_copy())
        print(provider.copy_stream())
        print(provider.finalize_copy())
        end_info()

    def __repr__(self) -> str:
        return repr(self._column_group)

    def _to_indices(self, item: SomeIndices) -> List[int]:
        return to_indices(len(self._column_group), item)

    def _swap_cols(self, i, j):
        self._column_group.swap(i, j)

    def _move_before(self, pivot_index: int, indices: Collection[int]):
        self._column_group.move_before(pivot_index, indices)

    def _move_after(self, pivot_index: int, indices: Collection[int]):
        self._column_group.move_after(pivot_index, indices)

    def _select_indices(self, js: Iterable[int]):
        self._column_group.select_indices(js)

    def _drop_indices(self, js: Iterable[int]):
        self._column_group.drop_indices(js)

    def _insert_col(self, name: str, col_type: Type[T], values: List[T], index: int):
        self._column_group.insert_col(name, col_type, values, index)

    def _append_col(self, name: str, col_type: Type[T], values: List[T]):
        self._column_group.insert_col(name, col_type, values, self.column_count())

    def _apply(self, func: Callable[[Sequence[Any]], T]) -> List[T]:
        return self._column_group.apply(func)

    def _group_by(self, grouped_indices, func_by_colindex):
        def create_col(i: int, col_values: Collection[Any]):
            col = self._column_group[i]
            try:
                col_type = func_by_colindex[i].__annotations__['return']
            except (KeyError, AttributeError):
                col_type = Any

            return Column(col.name, col_type, col_values)

        rows_by_key = {}
        for row in self._rows():
            key = tuple(row[i] for i in grouped_indices)
            rows_by_key.setdefault(key, []).append(row)

        new_rows = []
        for _, rows in rows_by_key.items():
            cols = zip(*rows)
            new_row = [col[0] if j in grouped_indices
                       else func_by_colindex[j](col)
                       for j, col in enumerate(cols)]
            new_rows.append(new_row)

        cols = zip(*new_rows)


        self._column_group = ColumnGroup(
            [create_col(i, col) for i, col in enumerate(cols)])

    def _rows(self):
        return self._column_group.rows()

    def _merge_data(self, other: "Data", how: str, lon: List[int],
                    ron: List[int]):
        self._column_group.merge(other._column_group, how, lon, ron)

    def _map_col(self, column_index: int, func: Callable):
        col = self._column_group[column_index]
        col.col_values = [func(v) for v in col.col_values]
        col.col_type = func.__annotations__.get('return', Any)

    def _filter(self, func: Callable[[Sequence], bool]):
        self._column_group.filter(func)

    def _map_if(self, index: int, test, if_true, if_false):
        self._column_group.map_if(index, test, if_true, if_false)

    def _sort_values(self, indices, ascending):
        self._column_group.sort_values(indices, ascending)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
