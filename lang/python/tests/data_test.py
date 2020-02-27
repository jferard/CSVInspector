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

from csv_inspector import inspect


class DataTest(unittest.TestCase):
    def setUp(self) -> None:
        os.chdir("../../..")

    def test_something(self):
        print(os.getcwd())
        info = inspect("fixtures/datasets-2020-02-22-12-33.csv")
        data = info.open()
        data
        data.swap[0][1]
        print(data.df)


if __name__ == '__main__':
    unittest.main()
