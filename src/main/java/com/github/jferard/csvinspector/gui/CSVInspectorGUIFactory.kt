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

import com.github.jferard.csvinspector.exec.ExecutionContext
import com.github.jferard.csvinspector.util.CODE_EXAMPLE
import javafx.event.EventHandler
import javafx.scene.Scene
import javafx.scene.control.*
import javafx.scene.input.KeyCode
import javafx.scene.layout.ColumnConstraints
import javafx.scene.layout.GridPane
import javafx.scene.layout.RowConstraints
import javafx.scene.text.TextFlow


class CSVInspectorGUIFactory(private val executionContext: ExecutionContext) {
    fun create(): CSVInspectorGUI {
        val outArea = outArea()
        //val list: ObservableList<List<String>> = FXCollections.observableArrayList()
        val codeArea = TextArea()
        val csvPane = tabPane()

        val outPane = outPane(outArea)
        val scene = createScene(csvPane, outArea, outPane, codeArea)
        return CSVInspectorGUI(csvPane, outArea, codeArea, scene)
    }

    private fun outArea(): TextFlow {
        val outArea = TextFlow()
        outArea.prefWidth = 500.0
//        outArea.e.isEditable = false
        return outArea
    }

    private fun createScene(csvPane: TabPane,
                            outArea: TextFlow,
                            outPane: ScrollPane,
                            codeArea: TextArea): Scene {
        val root = GridPane()
        val colConstraints = ColumnConstraints()
        colConstraints.percentWidth = 50.0
        val rowConstraints = RowConstraints()
        rowConstraints.percentHeight = 50.0
        root.columnConstraints.add(colConstraints)
        root.columnConstraints.add(colConstraints)
        root.rowConstraints.add(rowConstraints)
        root.rowConstraints.add(rowConstraints)
        val codePane = codePane(codeArea)
        root.add(csvPane, 0, 0, 2, 1)
        root.add(codePane, 0, 1)
        root.add(outPane, 1, 1)

        val scene = Scene(root, 1000.0, 1000.0)
        scene.onKeyReleased = EventHandler {
            if (it.code == KeyCode.F5) {
                csvPane.tabs.clear()
                val code = codeArea.text
                executionContext.executeScript(code)
                executionContext.listen()
            }
        }
        return scene
    }

    private fun tabPane(): TabPane {
        val csvPane = TabPane()
        csvPane.prefHeight = 500.0
        return csvPane
    }

    private fun outPane(outArea: TextFlow): ScrollPane {
        val outPane = ScrollPane(Label("out"))
        outPane.content = outArea
        outPane.prefHeight = 500.0
        outPane.isFitToWidth = true
        outPane.isFitToHeight = true
        return outPane
    }

    private fun codePane(codeArea: TextArea): ScrollPane {
        val codePane = ScrollPane()
        codeArea.isWrapText = true
        codeArea.text = CODE_EXAMPLE
        codePane.content = codeArea

        codePane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        codePane.prefHeight = 500.0
        codePane.isFitToWidth = true
        codePane.isFitToHeight = true
        return codePane
    }
}
