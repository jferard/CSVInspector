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
import os
import unittest
from typing import (Any, Sequence)

from csv_inspector import read_csv
from csv_inspector.data import Data
from csv_inspector.util import ColumnGroup, Column


class ColumnTest(unittest.TestCase):
    def test_col_eq(self):
        self.assertEqual(Column("colA", int, [1, 2, 3]),
                         Column("colA", int, [1, 2, 3]))


class ColumnGroupTest(unittest.TestCase):
    def test_from_rows(self):
        c = ColumnGroup.from_rows((int, str),
                                  [("colA", "colB"), (1, "a"), (2, "b"),
                                   (3, "c")])
        self.assertEqual(ColumnGroup([Column("colA", int, [1, 2, 3]),
                                      Column("colB", str, ["a", "b", "c"])]), c)


class DataIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        os.chdir("../../..")

    def test_something(self):
        print(os.getcwd())
        data = read_csv("fixtures/datasets-2020-02-22-12-33.csv")


def data_from_rows(col_types, rows):
    columns = list(zip(*rows))
    return Data(
        ColumnGroup([Column(col[0], col_type, col[1:]) for col_type, col in
                     zip(col_types, columns)]), None)


class DataTest(unittest.TestCase):
    def test_data_swap(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 11, "aa"), (2, "b", 22, "bb"),
                               (3, "c", 33, "cc")])
        data[0::2].swap(data[1::2])
        print(data)

    def test_data_add(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 11, "aa"), (2, "b", 22, "bb"),
                               (3, "c", 33, "cc")])

        def f(x: int) -> str:
            return str(x) + ": str"

        data[0].create(f, "colE")
        print(data)

    def test_data_merge(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 11, "aa"), (2, "b", 22, "bb"),
                               (3, "c", 33, "cc")])

        def f(*xs) -> str:
            return "-".join(map(str, xs))

        data[:].merge(f, "colE")
        print(data)

    def test_data_groupby(self):
        data = data_from_rows((int, str, int),
                              [("colA", "colB", "colC"),
                               (1, "a", 10), (1, "b", 20),
                               (2, "c", 40)])

        def f(x: Sequence[str]) -> str:
            return "-".join(map(str, x))

        g = data[0].grouper()
        g[1].agg(f)
        g[2].agg(len)
        g.group()
        print(data)

    def test_data_ljoin(self):
        data1 = data_from_rows((int, str, int),
                               [("colA1", "colB1", "colC1"),
                                (1, "a", 10), (1, "b", 20),
                                (2, "c", 40), (3, "d", 80)])
        data2 = data_from_rows((int, str, int),
                               [("colA2", "colB2", "colC2"),
                                (1, "x", -10), (2, "y", -20),
                                (2, "z", -40)])
        data1[0].ljoin(data2[0])
        print(data1)

    def test_data_filter(self):
        data = data_from_rows((int, str, int),
                              [("colA", "colB", "colC"),
                               (1, "a", 10), (1, "b", 20),
                               (2, "c", 40), (3, "d", 80)])
        data[2].filter(lambda x: x > 30)
        print(data)

    def test_move_before(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        data[1, 3].move_before(0)
        print(data)

    def test_move_after(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        data[1, 3].move_after(2)
        print(data)

    def test_select(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        data[::2].select()
        print(data)

    def test_drop(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        data[::2].drop()
        print(data)

    def test_update(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        data[2].update(lambda x: x * 2)
        print(data)

    def test_rsort(self):
        data = data_from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        data[0, 1].rsort()
        print(data)


if __name__ == '__main__':
    unittest.main()
