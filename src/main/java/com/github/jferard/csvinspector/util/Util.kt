/*
 * CSVInspector - A graphical interactive tool to inspect and process CSV files.
 *     Copyright (C) 2020 J. Férard <https://github.com/jferard>
 *
 * This file is part of CSVInspector.
 *
 * CSVInspector is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option) any later
 * version.
 *
 * CSVInspector is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE. See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program. If not, see <http://www.gnu.org/licenses/>.
 *
 */

package com.github.jferard.csvinspector.util

import java.util.concurrent.ThreadLocalRandom
import kotlin.streams.asSequence

const val TOKEN_LENGTH = 100L
const val charPool: String = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

const val SHOW_SQL_EXAMPLE = """#!/usr/bin/env python3.6

from csv_inspector import *

info = inspect("fixtures/datasets-2020-02-22-12-33.csv")
info.show()
info.open().show_sql()
"""

const val SELECT_EXAMPLE = """#!/usr/bin/env python3.6

from csv_inspector import *

data = inspect("fixtures/datasets-2020-02-22-12-33.csv").open()
data.show()
# swap two columns
data.swap[0][1]
data.show()
# shorten id
data.map[1][lambda c: c.str[:4]]
data.show()
# select
data.select[0:4, 10]
data.show()
"""

const val GROUPBY_EXAMPLE = """#!/usr/bin/env python3.6

from csv_inspector import *

data = inspect("fixtures/datasets-2020-02-22-12-33.csv").open()
# shorten id
data.map[0][lambda c: c.str[:3]]
data.groupby[0]['count']
data.show()
"""

const val JOIN_EXAMPLE = """#!/usr/bin/env python3.6

from csv_inspector import *

data = inspect("fixtures/datasets-2020-02-22-12-33.csv").open()
# join on self
data.ijoin[data][0][0]
data.show()
"""

const val CODE_EXAMPLE = """#!/usr/bin/env python3.6

from csv_inspector import *

info = inspect("fixtures/datasets-2020-02-22-12-33.csv")
info.show()

data = info.open()
data.show_sql()
data.show()
# swap two columns
data.swap[0][1]
data.show()
# shorten id
data.map[1][lambda c: c.str[:4]]
data.show()
# select
data.select[0:4, 10]
data.show()
# join on self
data.ijoin[data][1][1]
data.show()
# groupby
data.groupby[1][0:4, 'count', 'max']
data.show()
# merge
data.merge[0,4][V(lambda x: x[0] + " (" + pd.to_datetime(x[4]).dt.year.astype('str') + ")"), "new"]
data.show()"""


/**
 * Generate a token for communication with script language.
 */
fun generateToken(length: Long = TOKEN_LENGTH): String {
    val token = ThreadLocalRandom.current()
            .ints(length, 0, charPool.length)
            .asSequence()
            .map(charPool::get)
            .joinToString("")
    return "--$token--"
}