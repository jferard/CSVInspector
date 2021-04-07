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
import itertools
import sys
import string
import types
from typing import (Union, Tuple, List, NewType, Callable, Any, Type,
                    Collection, Generic, TypeVar, Sequence, Sized, Iterable,
                    Iterator, Container)

import numpy as np
import pandas as pd
from mcsv.field_processors import ReadError

try:
    TOKEN
except NameError:
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
    else:
        TOKEN = None

BEGIN_SCRIPT = f"{TOKEN}begin script"
END_SCRIPT = f"{TOKEN}end script"


def begin_info():
    print(f"{TOKEN}begin info")


def end_info():
    print(f"{TOKEN}end info", flush=True)


def begin_csv():
    print(f"{TOKEN}begin csv")


def end_csv():
    print(f"{TOKEN}end csv", flush=True)


def executed():
    print(f"{TOKEN}executed", flush=True)
    print(f"{TOKEN}executed", file=sys.stderr, flush=True)


def missing_mcsv(csv_path):
    print(f"{TOKEN}missing csv:{csv_path}")


def execute_script(script, vars):
    vars["TOKEN"] = TOKEN
    exec(script, vars)


def sanitize(text: str) -> str:
    """
    Remove accents and special chars from a string

    >>> sanitize("Code Départ’ement")
    'Code Departement'


    @ascending text: the unicode string
    @return: the ascii string
    """
    import unicodedata
    try:
        text = unicodedata.normalize('NFKD', text).encode('ascii',
                                                          'ignore').decode(
            'ascii')
    except UnicodeError:
        pass
    return text


def to_standard(text: str) -> str:
    """
    >>> to_standard("Code Départ'ement")
    'code_departement'

    :ascending text:
    :return:
    """

    def remove_chars(c):
        return c in string.ascii_letters + string.digits + "_"

    text = sanitize(text.replace(" ", "_")).casefold()
    return "".join(filter(remove_chars, text))


SomeIndices = NewType("SomeIndices",
                      Union[Tuple[Union[slice, int]], slice, int])

T = TypeVar("T")


def is_some_indices(o: Any) -> bool:
    return isinstance(o, (tuple, slice, int))


def to_indices(length: int,
               item: SomeIndices) -> List[int]:
    """
    >>> to_indices(5, (0, slice(2, None, None)))
    [0, 2, 3, 4]
    >>> to_indices(5, (33, slice(2, None, None)))
    [33, 2, 3, 4]
    """
    if isinstance(item, tuple):
        indices = list()
        for it in item:
            for i in to_indices(length, it):
                if i not in indices:
                    indices.append(i)
        return indices
    elif isinstance(item, slice):
        return list(range(*item.indices(length)))
    elif isinstance(item, int):
        return [item]
    else:
        raise ValueError(f"{item} is not a tuple, slice or int")


def _dtype_to_sql(self, dtype: np.dtype) -> str:
    if dtype.name.startswith('date'):
        return "TIMESTAMP"
    elif dtype.name.startswith('int') or dtype.name.startswith('uint'):
        return "INT"
    elif dtype.name.startswith('float'):
        return "DECIMAL"
    elif dtype.name.startswith('bool'):
        return "BOOL"
    else:
        return "TEXT"


def _get_col_dtype(col):
    """
    Infer datatype of a pandas column_index, process only if the column_index dtype is object.
    input:   col: a pandas Series representing a df column_index.
    """

    if col.dtype == "object":
        # try numeric
        unique_col = col.dropna().unique()
        try:
            col_new = pd.to_datetime(unique_col)
            return col_new.dtype
        except:
            try:
                col_new = pd.to_numeric(unique_col)
                return col_new.dtype
            except:
                try:
                    col_new = pd.to_timedelta(unique_col)
                    return col_new.dtype
                except:
                    return "object"

    return col.dtype


def apply_vectorized(f: Callable, *arrs: Any) -> Any:
    """
    >>> import numpy as np
    >>> arr = np.array([1, 2, 3])
    >>> apply_vectorized(np.sqrt, arr)
    array([1.        , 1.41421356, 1.73205081])
    >>> apply_vectorized(str, arr)
    vetoz
    array(['1', '2', '3'], dtype='<U1')
    >>> arr2 = np.array([[1, 2, 3], [4, 5, 6]])
    >>> f = lambda x: x[0] + x[1]
    >>> apply_vectorized(f, arr2)
    array([5, 7, 9])
    >>> f(arr2)
    array([5, 7, 9])

    """
    if isinstance(f, (np.vectorize, np.ufunc)):
        try:
            return f(*arrs)
        except TypeError:
            pass

    print("vetoz")
    return np.vectorize(f)(arrs)


S = TypeVar('S')


class Column(Generic[S]):
    def __init__(self, name: str, col_type: Type[S], col_values: Collection[S]):
        if col_type != Any:
            assert all(isinstance(v, col_type) for v in
                       col_values if not (v is None or isinstance(v, ReadError))
                       ), f"Expected {col_type}, got {set(type(v) for v in col_values)}"
        self.name = name
        self.col_type = col_type
        self.col_values = col_values

    def standard_name(self):
        return to_standard(self.name)

    def __iter__(self) -> Iterator[S]:
        return iter(self.col_values)

    def __eq__(self, other: Any) -> bool:
        return (self.name == other.name and self.col_type == other.col_type
                and self.col_values == other.col_values)

    def __repr__(self):
        return f"Column({self.name}, {self.col_type}, {self.col_values}"

    def width(self):
        return max(len(self.name), *(len(str(v)) for v in self.col_values))

    def copy(self):
        return Column(self.name, self.col_type, list(self.col_values))


class ColumnGroup(Sized):
    @staticmethod
    def from_rows(types: Sequence[Type],
                  rows: Iterable[Sequence[Any]]) -> "ColumnGroup":
        it_rows = iter(rows)
        header = next(it_rows)
        assert len(types) == len(header)
        return ColumnGroup([Column(str(name), t, values) for name, t, *values in
                            zip(header, types, *it_rows)])

    def __init__(self, columns: List[Column]):
        self.columns = columns
        self.columns_by_name = {c.name: c for c in columns}

    def __getitem__(self, item: Union[int, str]):
        if isinstance(item, str):
            return self.columns_by_name[item]
        elif isinstance(item, int):
            return self.columns[item]
        else:
            raise TypeError(item)

    def __len__(self) -> int:
        return len(self.columns)

    def __iter__(self):
        return iter(self.columns)

    def swap(self, i: int, j: int):
        c = self.columns[i]
        self.columns[i] = self.columns[j]
        self.columns[j] = c

    def select_indices(self, js: Iterable[int]):
        self.columns = [col for i, col in enumerate(self.columns) if i in js]

    def drop_indices(self, js: Iterable[int]):
        self.columns = [col for i, col in enumerate(self.columns) if
                        i not in js]

    def move_before(self, pivot_index: int, indices: Collection[int]):
        r = range(pivot_index, len(self.columns))
        self.columns = (
                self.columns[:pivot_index] +
                [self.columns[i] for i in indices if i in r] +
                [self.columns[i] for i in r if i not in indices])

    def move_after(self, pivot_index: int, indices: Collection[int]):
        r = range(0, pivot_index + 1)
        self.columns = (
                [self.columns[i] for i in r if i not in indices] +
                [self.columns[i] for i in indices if i in r] +
                self.columns[pivot_index + 1:]
        )

    def apply(self, func: Callable[[Sequence[Any]], T]) -> List[T]:
        return [func(values) for values in
                zip(*[c.col_values for c in self.columns])]

    def insert_col(self, name: str, col_type: Type[T], values: List[T],
                   index: int):
        column = Column(name, col_type, values)
        self.columns = (
                self.columns[:index] + [column] + self.columns[index:])
        self.columns_by_name[name] = column

    def rows(self, indices: List[int] = None):
        if indices is None:
            return zip(*self.columns)
        else:
            return zip(*[col for i, col in enumerate(self.columns)])

    def __eq__(self, other):
        return self.columns == other.columns

    def __repr__(self):
        return f"ColumnGroup({self.columns})"

    def __str__(self):
        widths = [col.width() for col in self.columns]
        header = "".join(
            [col.name.rjust(w + 1) for col, w in zip(self.columns, widths)])
        rows = ["".join(
            [str(row[i]).rjust(widths[i] + 1) for i in range(len(widths))])
            for row in self.rows()]
        return "\n".join([header, *rows])

    def merge(self, other: "ColumnGroup", how: str, lon: List[int],
              ron: List[int]):
        if len(lon) > len(ron):
            lon = lon[:len(ron)]
        elif len(lon) < len(ron):
            ron = ron[:len(lon)]
        assert len(lon) == len(ron)
        llength = len(self.columns)
        row_by_l = {}
        for row in self.rows():
            row_by_l.setdefault(tuple([row[i] for i in lon]), []).append(
                row)

        rlength = len(other)
        row_by_r = {}
        for row in other.rows():
            row_by_r.setdefault(tuple([row[i] for i in ron]), []).append(
                row)

        new_rows = []
        if how == "inner":
            for lkey, lrows in row_by_l.items():
                rrows = row_by_r.get(lkey, [])
                for rrow in rrows:
                    for lrow in lrows:
                        new_rows.append(lrow + rrow)
        elif how == "left":
            R_EMPTY = (None,) * rlength
            for lkey, lrows in row_by_l.items():
                rrows = row_by_r.get(lkey, [])
                if rrows:
                    for rrow in rrows:
                        for lrow in lrows:
                            new_rows.append(lrow + rrow)
                else:
                    for lrow in lrows:
                        new_rows.append(lrow + R_EMPTY)
        elif how == "right":
            L_EMPTY = (None,) * llength
            for rkey, rrows in row_by_r.items():
                lrows = row_by_l.get(rkey, [])
                if lrows:
                    for lrow in lrows:
                        for rrow in rrows:
                            new_rows.append(lrow + rrow)
                else:
                    for rrow in rrows:
                        new_rows.append(L_EMPTY + rrow)
        elif how == "outer":
            pass  # TODO
        else:
            raise ValueError(f"Unknown join type: {how}")

        self.columns += other.columns
        self.replace_rows(new_rows)

    def filter(self, func: Callable[[Sequence], bool]):
        new_rows = [row for row in self.rows() if func(row)]
        self.replace_rows(new_rows)

    def replace_rows(self, new_rows):
        for col, col_values in zip(self.columns, zip(*new_rows)):
            col.col_values = col_values

    def map_if(self, index: int, test, if_true, if_false):
        self.columns[index].col_values = [
            if_true(row) if test(row[index]) else if_false(row)
            for row in self.rows()]

    def sort_values(self, indices, ascending):
        if ascending:
            new_rows = sorted(self.rows(),
                              key=lambda row: tuple(row[i] for i in indices))
        else:
            new_rows = sorted(self.rows(),
                              key=lambda row: tuple(row[i] for i in indices),
                              reverse=True)
        self.replace_rows(new_rows)

    def copy(self):
        return ColumnGroup([col.copy() for col in self.columns])

    def replace_columns(self, columns):
        self.columns = columns

    def rename(self, i, name):
        self.columns[i].name = name


class ColumnFactory:
    def create(self, name: str, values: Collection[str]) -> Column:
        col_type = str
        col_values = values
        return Column(name, col_type, col_values)


if __name__ == "__main__":
    import doctest

    doctest.testmod(optionflags=doctest.ELLIPSIS)

