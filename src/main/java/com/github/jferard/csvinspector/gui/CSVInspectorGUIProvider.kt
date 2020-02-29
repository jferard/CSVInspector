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

import com.github.jferard.csvinspector.exec.ExecutionEnvironment
import com.github.jferard.csvinspector.util.CODE_EXAMPLE
import javafx.event.EventHandler
import javafx.scene.Scene
import javafx.scene.control.*
import javafx.scene.layout.ColumnConstraints
import javafx.scene.layout.GridPane
import javafx.scene.layout.RowConstraints
import javafx.scene.layout.VBox
import javafx.scene.text.TextFlow
import javafx.stage.Stage
import org.fxmisc.richtext.CodeArea


class CSVInspectorGUIProvider(
        private val executionEnvironment: ExecutionEnvironment,
        private val menuBarProvider: MenuBarProvider,
        private val primaryStage: Stage) {

    fun get(): CSVInspectorGUI {
        val outArea = outArea()
        val codeArea = CodeAreaProvider().get()
        val csvPane = csvPane()

        val outPane = outPane(outArea)
        val menuBar = menuBarProvider.get()
        val codePane = codePane(codeArea)
        val workbench = createWorkbench(csvPane, outPane, codePane)
        val scene = createScene(menuBar, workbench)
        return CSVInspectorGUI(executionEnvironment, primaryStage, csvPane, outArea, codeArea,
                scene)
    }

    private fun outArea(): TextFlow {
        val outArea = TextFlow()
        outArea.prefWidth = 500.0
//        outArea.e.isEditable = false
        return outArea
    }

    private fun createScene(menuBar: MenuBar,
                            workbench: GridPane): Scene {
        val root = createRoot(menuBar, workbench)
        val scene = Scene(root, 1000.0, 1000.0)
        val resource = CSVInspectorGUI::class.java.getResource("/python.css")
        scene.stylesheets
                .add(resource.toExternalForm())
        return scene
    }

    private fun createRoot(menuBar: MenuBar,
                           workbench: GridPane): VBox {
        val root = VBox()
        root.children.add(menuBar)
        root.children.add(workbench)
        return root
    }

    private fun createWorkbench(csvPane: TabPane,
                                outPane: ScrollPane,
                                codePane: TabPane): GridPane {
        val root = GridPane()
        val colConstraints = ColumnConstraints()
        colConstraints.percentWidth = 50.0
        val rowConstraints = RowConstraints()
        rowConstraints.percentHeight = 50.0
        root.columnConstraints.add(colConstraints)
        root.columnConstraints.add(colConstraints)
        root.rowConstraints.add(rowConstraints)
        root.rowConstraints.add(rowConstraints)
        root.add(csvPane, 0, 0, 2, 1)
        root.add(codePane, 0, 1)
        root.add(outPane, 1, 1)
        return root
    }

    private fun csvPane(): TabPane {
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

    private fun codePane(codeArea: CodeArea): TabPane {
        val codePane = ScrollPane()
        codeArea.replaceText(CODE_EXAMPLE)
        codePane.content = codeArea

        codePane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        codePane.prefHeight = 500.0
        codePane.isFitToWidth = true
        codePane.isFitToHeight = true
        val tab = Tab("Code", codePane)
        val tabPlus = Tab("+")
        tabPlus.isClosable = false
        tabPlus.onSelectionChanged = EventHandler{
            println("++")
        }
        val codePane0 = TabPane()
        codePane0.tabs.addAll(tab, tabPlus)
        codePane0.selectionModel.select(tab)
        return codePane0
    }
}