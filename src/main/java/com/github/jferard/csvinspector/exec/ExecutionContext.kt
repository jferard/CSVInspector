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

import com.github.jferard.csvinspector.gui.*
import com.google.common.eventbus.EventBus
import java.io.BufferedReader
import java.io.IOException
import java.io.Writer

class ExecutionContext(private val token: String,
                       private val eventBus: EventBus,
                       private val stdinWriter: Writer,
                       private val stdoutReader: BufferedReader,
                       private val stderrReader: BufferedReader) {
    private lateinit var state: State

    fun executeScript(code: String) {
        stdinWriter.write("${token}begin script\n")
        stdinWriter.write(code)
        stdinWriter.write("\n${token}end script\n")
        try {
            stdinWriter.flush()
        } catch (e: IOException) {
            System.err.println("Script error")
        }
    }

    fun listen() {
        this.state = NormalState(token)
        var line = this.stdoutReader.readLine()
        while (line != null) {
            if (line == "${token}executed") {
                break
            }
            if (!this.state.handle(this, line)) {
                break
            }
            line = this.stdoutReader.readLine()
        }
        val errLines = mutableListOf<String>()
        var errLine = this.stderrReader.readLine()
        while (errLine != null) {
            if (errLine == "${token}executed") {
                break
            }
            errLines.add(errLine)
            errLine = this.stderrReader.readLine()
        }
        eventBus.post(ErrEvent(errLines.joinToString("\n")))
    }

    fun setState(state: State) {
        this.state = state
    }

    fun info(line: String) {
        eventBus.post(InfoEvent(line))
    }

    fun out(line: String) {
        eventBus.post(OutEvent(line))
    }

    fun show(data: String) {
        eventBus.post(CSVEvent(data))
    }

    fun sql(sql: String) {
        eventBus.post(SQLEvent(sql))
    }
}

interface State {
    fun handle(context: ExecutionContext, line: String): Boolean
}

class NormalState(private val token: String) : State {
    override fun handle(context: ExecutionContext, line: String): Boolean {
        if (line.startsWith(token)) {
            when (val directive = line.substring(token.length)) {
                "executed" -> return false
                "begin show" -> context.setState(ShowState(token))
                "begin info" -> context.setState(InfoState(token))
                "begin sql" -> context.setState(SQLState(token))
                else -> System.err.println("Unknown directive: $directive")
            }
        } else {
            context.out(line)
        }
        return true
    }
}

class ShowState(private val token: String) : State {
    private var cur = mutableListOf<String>()

    override fun handle(context: ExecutionContext, line: String): Boolean {
        if (line.startsWith(token)) {
            when (val directive = line.substring(token.length)) {
                "executed" -> return false
                "end show" -> {
                    context.show(cur.joinToString("\n"))
                    context.setState(NormalState(token))
                }
                else -> System.err.println("Unknown directive: $directive")
            }
        } else {
            cur.add(line)
        }
        return true
    }

}

class InfoState(private val token: String) : State {
    private var cur = mutableListOf<String>()

    override fun handle(context: ExecutionContext, line: String): Boolean {
        if (line.startsWith(token)) {
            when (val directive = line.substring(token.length)) {
                "executed" -> return false
                "end info" -> {
                    context.info(cur.joinToString("\n"))
                    context.setState(NormalState(token))
                }
                else -> System.err.println("Unknown directive: $directive")
            }
        } else {
            cur.add(line)
        }
        return true
    }
}

class SQLState(private val token: String) : State {
    private var cur = mutableListOf<String>()

    override fun handle(context: ExecutionContext, line: String): Boolean {
        if (line.startsWith(token)) {
            when (val directive = line.substring(token.length)) {
                "executed" -> return false
                "end sql" -> {
                    context.sql(cur.joinToString("\n"))
                    context.setState(NormalState(token))
                }
                else -> System.err.println("Unknown directive: $directive")
            }
        } else {
            cur.add(line)
        }
        return true
    }
}
