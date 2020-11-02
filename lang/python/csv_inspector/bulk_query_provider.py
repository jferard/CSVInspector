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
from abc import ABCMeta, abstractmethod
from encodings import normalize_encoding
from pathlib import Path
from typing import Sequence


class SQLBulkProvider(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, encoding: str, dialect: csv.Dialect, table_name: str,
                 force_null: Sequence[str]):
        pass

    @abstractmethod
    def drop_table(self):
        pass

    @abstractmethod
    def create_schema(self):
        pass

    @abstractmethod
    def prepare_copy(self):
        pass

    @abstractmethod
    def copy_stream(self):
        pass

    @abstractmethod
    def finalize_copy(self):
        pass


class PostgreSQLBulkProvider(SQLBulkProvider):
    def __init__(self, encoding: str, dialect: csv.Dialect, file: Path,
                 table_name: str, force_null: Sequence[str]):
        self._encoding = encoding
        self._dialect = dialect
        self._file = file
        self._table_name = table_name
        self._force_null = force_null

    def drop_table(self):
        return f'DROP TABLE IF EXISTS "{self._table_name}";'

    def create_schema(self):
        return f'not implemented yet;'

    def prepare_copy(self) -> str:
        return f'TRUNCATE "{self._table_name}";'

    def copy_stream(self) -> str:
        encoding = normalize_encoding(self._encoding).upper()
        options = {"FORMAT": "CSV",
                   "HEADER": "TRUE", "ENCODING": f"'{encoding}'"}
        if self._dialect.delimiter != ',':
            options["DELIMITER"] = self._escape_char(self._dialect.delimiter)
        if not self._dialect.doublequote:
            options["ESCAPE"] = self._escape_char(self._dialect.escapechar)
        if self._dialect.quotechar != '"':
            options["QUOTE"] = self._escape_char(self._dialect.quotechar)
        options["FORCE_NULL"] = '("{}")'.format('", "'.join(self._force_null))
        options_str = ", ".join(f"{k} {v}" for k, v in options.items())

        return (f'COPY "{self._table_name}" '
                f'FROM \'{self._file.absolute().as_posix()}\' '
                f'WITH ({options_str});')

    def _escape_char(self, text: str) -> str:
        """
        See 4.1.2.2. String Constants with C-style Escapes
        :ascending text:
        :return:
        """
        if text == "\\":
            return "E'\\\\'"
        elif text in "\b\f\n\r\t":
            return f"E'{text}'"
        elif text == "'":
            return "E'\\\''"
        return f"'{text}'"

    def finalize_copy(self) -> str:
        return f'ANALYZE "{self._table_name}";'


def get_provider(provider_name: str = 'pg') -> SQLBulkProvider:
    if provider_name in ('pg'):
        return PostgreSQLBulkProvider
    else:
        raise ValueError(provider_name)
