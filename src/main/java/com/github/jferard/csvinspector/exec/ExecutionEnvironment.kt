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
import javafx.concurrent.Task
import java.io.BufferedReader
import java.io.Writer

/** An execution environment for Python scripts */
class ExecutionEnvironment(private val executor: PythonExecutor,
                           private var process: Process,
                           private val token: String,
                           private val eventBus: EventBus,
                           private var stdinWriter: Writer,
                           private var stdoutReader: BufferedReader,
                           private var stderrReader: BufferedReader) {
    fun createTask(code: String): Task<Unit> {
        return ExecutionContext(token, eventBus, code, stdinWriter, stdoutReader, stderrReader)
    }

    fun restart() {
        val newEnvironment = executor.start()
        val oldProcess = process
        process = newEnvironment.process
        stdinWriter = newEnvironment.stdinWriter
        stdoutReader = newEnvironment.stdoutReader
        stderrReader = newEnvironment.stderrReader
        oldProcess.destroy()
    }
}