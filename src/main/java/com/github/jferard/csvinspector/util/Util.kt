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

const val CODE_EXAMPLE = """#!/usr/bin/env python3.7

from csv_inspector import *

info = inspect("fixtures/datasets-2020-02-22-12-33.csv")
info.show()

data = info.open()
data.swap[0][1]
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