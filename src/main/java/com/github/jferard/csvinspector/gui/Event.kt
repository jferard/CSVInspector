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

package com.github.jferard.csvinspector.gui

import com.github.jferard.javamcsv.MetaCSVData
import com.github.jferard.javamcsv.MetaCSVRecord

interface ScriptEvent {
    val data: String
}
class RawCSVEvent(override val data: String) : ScriptEvent
class MetaCSVEvent(val rows: List<MetaCSVRecord>, val data: MetaCSVData)
class ErrEvent(override val data: String): ScriptEvent
class InfoEvent(override val data: String): ScriptEvent
class OutEvent(override val data: String): ScriptEvent
class SQLEvent(override val data: String): ScriptEvent
class MenuEvent(val name: String)
