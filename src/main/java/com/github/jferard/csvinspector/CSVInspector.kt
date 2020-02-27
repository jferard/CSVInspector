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

package com.github.jferard.csvinspector

import com.github.jferard.csvinspector.gui.CSVInspectorApplication
import javafx.application.Application
import java.io.File
import java.util.*

fun main(args: Array<String>) {
    val properties = Properties();
    println(listOf(System.getProperty("user.dir"), System.getProperty("user.home"), "."))
    for (dir in arrayOf(System.getProperty("user.dir"), System.getProperty("user.home"), ".")) {
        val propertiesFile = File(dir, ".csv_inspector.properties")
        if (propertiesFile.exists()) {
            propertiesFile.reader(Charsets.UTF_8).use {
                properties.load(it)
            }
            break
        }
    }
    if (properties.isEmpty) {
        properties.setProperty("python_exe", "python3.6")
    }
    Application.launch(CSVInspectorApplication::class.java, properties.getProperty("python_exe"))
}

