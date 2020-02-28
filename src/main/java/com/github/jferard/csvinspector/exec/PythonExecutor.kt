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

package com.github.jferard.csvinspector.exec

import com.google.common.eventbus.EventBus
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.nio.file.Paths
import kotlin.system.exitProcess

class PythonExecutor(private val pythonExe: String, private val token: String,
                     private val eventBus: EventBus) {
    fun start(): ExecutionEnvironment {
        val cmdarray = arrayOf(pythonExe, "-m", "csv_inspector", token)
        println("start python server: ${cmdarray.toList()}")
        try {
            val process = Runtime.getRuntime().exec(cmdarray,
                    arrayOf("PYTHONPATH=${getPythonPath()}", "PYTHONIOENCODING=utf-8"))
            val stdinWriter = OutputStreamWriter(process.outputStream, Charsets.UTF_8)
            val stdoutReader =
                    BufferedReader(InputStreamReader(process.inputStream, Charsets.UTF_8))
            val stderrReader =
                    BufferedReader(InputStreamReader(process.errorStream, Charsets.UTF_8))
            return ExecutionEnvironment(token, eventBus, stdinWriter, stdoutReader, stderrReader)
        } catch (e: Exception) {
            System.err.println("python server crashed")
            exitProcess(-1)
        }
    }

    private fun getPythonPath(): String {
        val curPythonPath = System.getenv("PYTHONPATH")
        val inspectorPythonPath = Paths.get("lang", "python").toString()
        return if (curPythonPath == null) {
            inspectorPythonPath
        } else {
            val sep = File.pathSeparator
            "$curPythonPath${sep}${inspectorPythonPath}"
        }
    }
}
