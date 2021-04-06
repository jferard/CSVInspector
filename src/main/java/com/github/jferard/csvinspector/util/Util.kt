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

const val SHOW_EXAMPLE = """#!/usr/bin/env python3.8

from csv_inspector import *

data = open_csv("fixtures/datasets-2020-02-22-12-33.csv")
data.show()
"""

const val SELECT_EXAMPLE = """#!/usr/bin/env python3.8

from csv_inspector import *

data = open_csv("fixtures/datasets-2020-02-22-12-33.csv")
data.show()

# shorten id
data[0].update(lambda t: t[:4])

# take the five first columns
data[:5].select()
data.show()

# remove one column
data[3].drop()
data.show()

# swap two columns
data[1].swap(data[2])
data.show()
"""

const val GROUPBY_EXAMPLE = """#!/usr/bin/env python3.8

from csv_inspector import *

data = open_csv("fixtures/datasets-2020-02-22-12-33.csv")

# shorten id
data[0].update(lambda c: c[:3])

# group 0 on len(1)
g = data[0].grouper()
g[1].agg(len, int)
g.group()

data.show()
"""

const val JOIN_EXAMPLE = """#!/usr/bin/env python3.8

from csv_inspector import *

data1 = open_csv("fixtures/datasets-2020-02-22-12-33.csv")
data1[0].select()
data2 = data1.copy()

# join on self: data1.second char = data2.third char
data1[0].ijoin(data2[0], lambda xs1, xs2: xs1[0][1] == xs2[0][2])
data1.show()
"""

const val SORT_FILTER_EXAMPLE = """#!/usr/bin/env python3.8

from csv_inspector import *

data = open_csv("fixtures/datasets-2020-02-22-12-33.csv")

# filter
data[0].filter(lambda v: v[1] == '8')
data.show()    

# sort
data[0].sort()
data.show()    
"""


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