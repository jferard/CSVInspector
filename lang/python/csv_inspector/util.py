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
import sys
import string
from typing import (Union, Tuple, List, NewType, Callable, Any, Type,
                    Collection, Generic, TypeVar, Sequence, Sized, Iterable,
                    Iterator, Container)

from mcsv.field_description import FieldDescription, DataType, \
    data_type_to_python_type
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


# def _dtype_to_sql(self, dtype: np.dtype) -> str:
#     if dtype.name.startswith('date'):
#         return "TIMESTAMP"
#     elif dtype.name.startswith('int') or dtype.name.startswith('uint'):
#         return "INT"
#     elif dtype.name.startswith('float'):
#         return "DECIMAL"
#     elif dtype.name.startswith('bool'):
#         return "BOOL"
#     else:
#         return "TEXT"


# def _get_col_dtype(col):
#     """
#     Infer datatype of a pandas column_index, process only if the column_index dtype is object.
#     input:   col: a pandas Series representing a df column_index.
#     """
#
#     if col.dtype == "object":
#         # try numeric
#         unique_col = col.dropna().unique()
#         try:
#             col_new = pd.to_datetime(unique_col)
#             return col_new.dtype
#         except:
#             try:
#                 col_new = pd.to_numeric(unique_col)
#                 return col_new.dtype
#             except:
#                 try:
#                     col_new = pd.to_timedelta(unique_col)
#                     return col_new.dtype
#                 except:
#                     return "object"
#
#     return col.dtype


# def apply_vectorized(f: Callable, *arrs: Any) -> Any:
#     """
#     >>> import numpy as np
#     >>> arr = np.array([1, 2, 3])
#     >>> apply_vectorized(np.sqrt, arr)
#     array([1.        , 1.41421356, 1.73205081])
#     >>> apply_vectorized(str, arr)
#     vetoz
#     array(['1', '2', '3'], dtype='<U1')
#     >>> arr2 = np.array([[1, 2, 3], [4, 5, 6]])
#     >>> f = lambda x: x[0] + x[1]
#     >>> apply_vectorized(f, arr2)
#     array([5, 7, 9])
#     >>> f(arr2)
#     array([5, 7, 9])
#
#     """
#     if isinstance(f, (np.vectorize, np.ufunc)):
#         try:
#             return f(*arrs)
#         except TypeError:
#             pass
#
#     print("vetoz")
#     return np.vectorize(f)(arrs)


S = TypeVar('S')
ColInfo = Union[FieldDescription, DataType, Type]


class Column(Generic[S]):
    """
    We try to keed the column description.
    """

    def __init__(self, name: str, col_info: ColInfo,
                 col_values: Collection[S]):
        if isinstance(col_info, Type):
            self.col_type = col_info
        elif isinstance(col_info, DataType):
            self.col_type = data_type_to_python_type(col_info)
        elif isinstance(col_info, FieldDescription):
            self.col_type = col_info.get_python_type()
        else:
            self.col_type = Any
        if self.col_type != Any:
            assert all(isinstance(v, self.col_type) for v in
                       col_values if not (v is None or isinstance(v, ReadError))
                       ), f"Expected {self.col_type}, got {set(type(v) for v in col_values)}"
        self.name = name
        self.col_info = col_info
        self.col_values = col_values

    def standard_name(self):
        return to_standard(self.name)

    def __iter__(self) -> Iterator[S]:
        return iter(self.col_values)

    def __eq__(self, other: Any) -> bool:
        return (self.name == other.name
                and self.col_type == other.col_type
                and self.col_values == other.col_values)

    def __repr__(self):
        return f"Column({self.name}, {self.col_info}, {self.col_values}"

    def width(self):
        return max(len(self.name), *(len(str(v)) for v in self.col_values))

    def copy(self):
        return Column(self.name, self.col_info, list(self.col_values))


class ColumnGroup(Sized):
    @staticmethod
    def from_rows(descriptions: Sequence[FieldDescription],
                  rows: Iterable[Sequence[Any]]) -> "ColumnGroup":
        it_rows = iter(rows)
        header = next(it_rows)
        assert len(descriptions) == len(header)
        return ColumnGroup([Column(str(name), description, values)
                            for name, description, *values
                            in zip(header, descriptions, *it_rows)])

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

    def rows(self, indices: List[int] = None):
        if indices is None:
            return zip(*self.columns)
        else:
            indices = set(indices)
            return zip(*[col for i, col in enumerate(self.columns)
                         if i in indices])

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

    def replace_rows(self, new_rows):
        """
        Do not affect the column names or descriptions.
        """
        for col, col_values in zip(self.columns, zip(*new_rows)):
            col.col_values = col_values

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
