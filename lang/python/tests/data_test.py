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

    def test_swap(self):
        c1 = ColumnGroup.from_rows((int, str),
                                   [("colA", "colB"), (1, "a"), (2, "b"),
                                    (3, "c")])
        c2 = ColumnGroup.from_rows((str, int),
                                   [("colB", "colA"), ("a", 1), ("b", 2),
                                    ("c", 3)])
        c1.swap(0, 1)
        self.assertEqual(c1, c2)

    def test_insert_col(self):
        c1 = ColumnGroup.from_rows((int, str),
                                   [("colA", "colB"), (1, "a"), (2, "b"),
                                    (3, "c")])
        c1.insert_col("col0", str, ["4", "5", "6"], 0)
        c2 = ColumnGroup.from_rows((str, int, str),
                                   [("col0", "colA", "colB"), ("4", 1, "a"),
                                    ("5", 2, "b"), ("6", 3, "c")])
        self.assertEqual(c1, c2)

    def test_insert_col_fail_type(self):
        c1 = ColumnGroup.from_rows((int, str),
                                   [("colA", "colB"), (1, "a"), (2, "b"),
                                    (3, "c")])
        with self.assertRaises(AssertionError):
            c1.insert_col("col0", int, ["4", "5", "6"], 0)

    def test_insert_col_big_index(self):
        c1 = ColumnGroup.from_rows((int, str),
                                   [("colA", "colB"), (1, "a"), (2, "b"),
                                    (3, "c")])
        c1.insert_col("col0", str, ["4", "5", "6"], 10)
        c2 = ColumnGroup.from_rows((int, str, str),
                                   [("colA", "colB", "col0"), (1, "a", "4"),
                                    (2, "b", "5"), (3, "c", "6")])
        self.assertEqual(c1, c2)


class DataIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        os.chdir("../../..")

    def test_something(self):
        print(os.getcwd())
        info = inspect("fixtures/datasets-2020-02-22-12-33.csv")
        data = info.open()


class DataTest(unittest.TestCase):
    def test_data_swap(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 11, "aa"), (2, "b", 22, "bb"),
                               (3, "c", 33, "cc")])
        print(data.swap[0::2][1::2])

    def test_data_add(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 11, "aa"), (2, "b", 22, "bb"),
                               (3, "c", 33, "cc")])

        def f(x: Sequence[Any]) -> str:
            return str(x[0]) + ": str"

        print(data.add[f, "colE"])

    def test_data_merge(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 11, "aa"), (2, "b", 22, "bb"),
                               (3, "c", 33, "cc")])

        def f(x: Sequence[Any]) -> str:
            return "-".join(map(str, x))

        print(data.merge[:][f, "colE"])

    def test_data_groupby(self):
        data = Data.from_rows((int, str, int),
                              [("colA", "colB", "colC"),
                               (1, "a", 10), (1, "b", 20),
                               (2, "c", 40)])

        def f(x: Sequence[str]) -> str:
            return "-".join(map(str, x))

        print(data.groupby[0][1, f, 1, len, sum])

    def test_data_ljoin(self):
        data1 = Data.from_rows((int, str, int),
                               [("colA1", "colB1", "colC1"),
                                (1, "a", 10), (1, "b", 20),
                                (2, "c", 40), (3, "d", 80)])
        data2 = Data.from_rows((int, str, int),
                               [("colA2", "colB2", "colC2"),
                                (1, "x", -10), (2, "y", -20),
                                (2, "z", -40)])
        print(data1.ljoin[data2][0])

    def test_data_filter(self):
        data = Data.from_rows((int, str, int),
                              [("colA", "colB", "colC"),
                               (1, "a", 10), (1, "b", 20),
                               (2, "c", 40), (3, "d", 80)])
        print(data.filter[lambda x: x[2] > 30])

    def test_move_before(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        print(data.move_before[0][1, 3])

    def test_move_after(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        print(data.move_after[2][1, 3])

    def test_select(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        print(data.select[::2])

    def test_drop(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        print(data.drop[::2])

    def test_map(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        print(data.map[:2][lambda x: x * 2])

    def test_map_if(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        print(
            data.mapif[0][lambda x: x >= 2, lambda x: x[1], lambda x: x[3]])

    def test_rsort(self):
        data = Data.from_rows((int, str, int, str),
                              [("colA", "colB", "colC", "colD"),
                               (1, "a", 10, "aa"), (1, "b", 20, "bb"),
                               (2, "c", 40, "cc"), (3, "d", 80, "dd")])
        print(data.rsort[0, 1])


if __name__ == '__main__':
    unittest.main()
