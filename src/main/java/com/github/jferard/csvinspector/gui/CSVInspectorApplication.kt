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

import com.github.jferard.csvinspector.exec.PythonExecutor
import com.github.jferard.csvinspector.util.generateToken
import com.google.common.eventbus.EventBus
import javafx.application.Application
import javafx.stage.Stage

class CSVInspectorApplication : Application() {
    override fun start(primaryStage: Stage) {
        val token = generateToken()
        val eventBus = EventBus()
        val pythonExe = parameters.raw[0] ?: "python3.6"
        val executionContext = PythonExecutor(pythonExe, token, eventBus).start()

        val menuBarProvider = MenuBarProvider(eventBus)
        val gui = CSVInspectorGUIInitialProvider(eventBus, executionContext, menuBarProvider,
                primaryStage).get()
        eventBus.register(gui)
        eventBus.post(CSVEvent("TEXT\nPress F5\nTo execute\nthe code"))
        with(primaryStage) {
            this.isMaximized = true
            this.title = "CSVInspector (C) 2020 - J. Férard"
            this.scene = gui.scene
            this.show()
        }
    }
}
