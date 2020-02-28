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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Tuple, List

import numpy
import pandas as pd
from typing.io import IO

try:
    TOKEN
except NameError:
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
    else:
        TOKEN = None


class DataSwap:
    def __init__(self, data: "Data"):
        self.data = data
        self._source = None

    def __getitem__(self, item: Union[tuple, int, slice]):
        if self._source is None:
            self._source = item
            return self
        else:
            columns = list(self.data.df.columns)
            length = len(columns)
            source_indices = _to_indices(length, self._source)
            dest_indices = _to_indices(length, item)
            for i, j in zip(source_indices, dest_indices):
                columns[i], columns[j] = columns[j], columns[i]
            self.data.df = self.data.df.reindex(columns=columns)
        return self.data


class DataMove(ABC):
    def __init__(self, data: "Data"):
        self._data = data
        self._index = None

    def __getitem__(self, item) -> Union["DataMove", "Data"]:
        if self._index is None:
            columns = list(self._data.df.columns)
            self._index = item % len(columns)
            return self
        else:
            return self._move(item)

    def _move(self, item):
        assert isinstance(item, (tuple, slice, int))
        columns = list(self._data.df.columns)
        length = len(columns)
        indices_to_move = _to_indices(length, item)
        new_indices = self._new_indices(indices_to_move, length)
        self._data.df = self._data.df.reindex(
            columns=[columns[ni] for ni in new_indices])
        return self._data

    @abstractmethod
    def _new_indices(self, indices_to_move, length):
        pass


def _to_indices(length: int,
                item: Union[Tuple[Union[slice, int]], slice, int]) -> List[int]:
    """
    >>> _to_indices(5, (0, slice(2, None, None)))
    [0, 2, 3, 4]
    """
    if isinstance(item, tuple):
        return sorted(
            set(i for it in item for i in _to_indices(length, it)))
    elif isinstance(item, slice):
        return list(range(*item.indices(length)))
    elif isinstance(item, int):
        return [item]
    else:
        raise ValueError(f"{item} is not a tuple, slice or int")


class DataMoveBefore(DataMove):
    def __init__(self, data):
        DataMove.__init__(self, data)

    def _new_indices(self, indices_to_move, length):
        S = set(indices_to_move)
        new_indices = ([k for k in range(self._index) if k not in S]
                       + indices_to_move
                       + [k for k in range(self._index, length) if
                          k not in S])
        return new_indices


class DataMoveAfter(DataMove):
    def __init__(self, data):
        DataMove.__init__(self, data)

    def _new_indices(self, indices_to_move, length):
        S = set(indices_to_move)
        new_indices = ([k for k in range(self._index + 1) if k not in S]
                       + indices_to_move
                       + [k for k in range(self._index + 1, length) if
                          k not in S])
        return new_indices


class DataSelect:
    def __init__(self, data: "Data"):
        self._data = data

    def __getitem__(self, item):
        columns = list(self._data.df.columns)
        length = len(columns)
        indices = set(_to_indices(length, item))
        cols = [i in indices for i in range(length)]
        self._data.df = self._data.df.iloc[:, cols]
        return self._data


class DataDrop(object):
    def __init__(self, data: "Data"):
        self._data = data

    def __getitem__(self, item):
        columns = list(self._data.df.columns)
        length = len(columns)
        indices = set(_to_indices(length, item))
        cols = [i not in indices for i in range(length)]
        self._data.df = self._data.df.iloc[:, cols]
        return self._data


class DataAdd:
    def __init__(self, data: "Data"):
        self._data = data

    def __getitem__(self, item):
        func, name, *index = item
        self._data.df[name] = func(self._data)
        if index:
            index = index[0]
            columns = list(self._data.df.columns)
            new_columns = columns[:index] + [name] + columns[index:-1]
            self._data.df = (self._data.df.reindex(columns=new_columns))
        return self._data


class DataMerge:
    def __init__(self, data: "Data"):
        self._data = data
        self._source = None

    def __getitem__(self, item):
        if self._source is None:
            self._source = item
            return self
        else:
            func, name = item
            columns = list(self._data.df.columns)
            self._data.df[name] = func(self._data)
            source_indices = _to_indices(len(columns), self._source)
            new_columns = [name if i == source_indices[0] else c for i, c in
                           enumerate(columns) if i not in source_indices[1:]]
            self._data.df = (self._data.df.reindex(columns=new_columns))
        return self._data


class DataGroupBy(object):
    def __init__(self, data: "Data"):
        self._data = data
        self._grouped = None

    def __getitem__(self, item):
        if self._grouped is None:
            self._grouped = item
            return self
        else:
            columns = list(self._data.df.columns)
            length = len(columns)
            grouped_indices = _to_indices(length, self._grouped)
            d = {}
            if isinstance(item, tuple):
                while len(item) > 1:
                    it, func, *item = item
                    for i in _to_indices(length, it):
                        if i not in grouped_indices and columns[i] not in d:
                            d[columns[i]] = func
                if len(item):
                    func = item[0]
                    for i in range(length):
                        if i not in grouped_indices and columns[i] not in d:
                            d[columns[i]] = func
            else:  # function
                for i in range(length):
                    if i not in grouped_indices:
                        d[columns[i]] = item

            self._data.df = self._data.df.groupby(
                [columns[g] for g in grouped_indices], as_index=False).agg(d)
            return self._data


class DataJoin:
    def __init__(self, data: "Data", how: str):
        self._data = data
        self._how = how
        self._other = None
        self._left_on = None

    def __getitem__(self, item):
        if self._other is None:
            assert isinstance(item, Data)
            self._other = item
            return self
        elif self._left_on is None:
            self._left_on = item
            return self
        else:
            if item == slice(None, None, None):
                right_on = self._left_on
            else:
                right_on = item
            left_columns = list(self._data.df.columns)
            left_indices = _to_indices(len(left_columns), self._left_on)
            right_columns = list(self._other.df.columns)
            right_indices = _to_indices(len(right_columns), right_on)
            lon = [left_columns[i] for i in left_indices]
            ron = [right_columns[i] for i in right_indices]
            self._data.df = self._data.df.merge(self._other.df, how=self._how,
                                                left_on=lon, right_on=ron)
            return self._data


class DataFilter:
    def __init__(self, data: "Data"):
        self._data = data

    def __getitem__(self, item):
        if isinstance(item, tuple):
            for func in item:
                self._data.df = self._data.df[func(self._data)]
        else:
            self._data.df = self._data.df[item(self._data)]
        return self._data


class DataMap:
    def __init__(self, data: "Data"):
        self._data = data
        self._target = None

    def __getitem__(self, item):
        if self._target is None:
            self._target = item
            return self
        else:
            columns = list(self._data.df.columns)
            target_indices = _to_indices(len(columns), self._target)
            for i in target_indices:
                column = columns[i]
                self._data.df[column] = item(self._data.df[column])
            return self._data


class DataSort:
    def __init__(self, data: "Data", reverse: bool):
        self._data = data
        self._reverse = reverse

    def __getitem__(self, item):
        columns = list(self._data.df.columns)
        indices = _to_indices(len(columns), item)
        self._data.df = self._data.df.sort_values([columns[i] for i in indices],
                                                  ascending=not self._reverse
                                                  ).reset_index(drop=True)
        return self._data


class Data:
    """
    """

    def __init__(self, df):
        self.df = df

    def __getitem__(self, item):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> Data(data[0] + data[3])
        0     5
        1    12
        2    11
        dtype: int64
        """
        return self.df.iloc[:, item]

    @property
    def swap(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.swap[0][1]
           B  A  C  D
        0  3  1  2  4
        1  2  5  2  7
        2  4  3  7  8
        """
        return DataSwap(self)

    @property
    def add(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":["1", "5", "3"], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.add[lambda x: x[0]*x[1], "A*B", 2]
           A  B   A*B  C  D
        0  1  3   111  2  4
        1  5  2    55  2  7
        2  3  4  3333  7  8
        """
        return DataAdd(self)

    @property
    def merge(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":["1", "5", "3"], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.merge[1,3][lambda x: x[1]*x[2], "B*D"]
           A  B*D  C
        0  1    6  2
        1  5    4  2
        2  3   28  7
        """
        return DataMerge(self)

    @property
    def groupby(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 1, 3, 3, 3], "B":[3, 2, 4, 7, 9],
        ...      "C":[2, 2, 7, 8, 9], "D":[4, 7, 8, 3, 5]}))
        >>> data.groupby[0][1, 'sum', 'max']
           A   B  C  D
        0  1   5  2  7
        1  3  20  9  8
        """
        return DataGroupBy(self)

    @property
    def ljoin(self):
        """
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
    def rjoin(self):
        """
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
    def ojoin(self):
        """
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
    def ijoin(self):
        """
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
    def filter(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 4, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.filter[lambda x: x[0] % 2 == 1, lambda x: x[1] % 2 == 1]
           A  B  C  D
        0  1  3  2  4
        """
        return DataFilter(self)

    @property
    def move_before(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.move_before[2][1,3]
           A  B  D  C
        0  1  3  4  2
        1  5  2  7  2
        2  3  4  8  7
        """
        return DataMoveBefore(self)

    @property
    def move_after(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.move_after[2][1,3]
           A  C  B  D
        0  1  2  3  4
        1  5  2  2  7
        2  3  7  4  8
        """
        return DataMoveAfter(self)

    @property
    def select(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.select[0, 2:]
           A  C  D
        0  1  2  4
        1  5  2  7
        2  3  7  8
        """
        return DataSelect(self)

    @property
    def drop(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.drop[0, 2:]
           B
        0  3
        1  2
        2  4
        """
        return DataDrop(self)

    @property
    def map(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.map[0,3][lambda c: c+2]
           A  B  C   D
        0  3  3  2   6
        1  7  2  2   9
        2  5  4  7  10
        """
        return DataMap(self)

    @property
    def sort(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.sort[1]
           A  B  C  D
        0  5  2  2  7
        1  1  3  2  4
        2  3  4  7  8
        """
        return DataSort(self, False)

    @property
    def rsort(self):
        """
        >>> data = Data(pd.DataFrame(
        ...     {"A":[1, 5, 3], "B":[3, 2, 4],
        ...      "C":[2, 2, 7], "D":[4, 7, 8]}))
        >>> data.rsort[1]
           A  B  C  D
        0  3  4  7  8
        1  1  3  2  4
        2  5  2  2  7
        """
        return DataSort(self, True)

    def show(self, limit=100):
        print(f"{TOKEN}begin show")
        if isinstance(self.df.dtypes, numpy.dtype):
            print(self.df.dtypes)
        else:
            print(",".join(map(str, self.df.dtypes)))
        self.df.iloc[:limit].to_csv(sys.stdout, encoding="utf-8", index=False)
        print(f"{TOKEN}end show", flush=True)

    def save(self, destination: Union[str, Path, IO]):
        self.df.to_csv(destination, index=False, encoding='utf-8')

    def __repr__(self):
        return repr(self.df)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
