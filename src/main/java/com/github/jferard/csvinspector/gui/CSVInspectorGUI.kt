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
import com.google.common.eventbus.Subscribe
import javafx.beans.property.ReadOnlyStringWrapper
import javafx.beans.value.ChangeListener
import javafx.collections.ListChangeListener
import javafx.collections.ObservableList
import javafx.concurrent.Task
import javafx.scene.Scene
import javafx.scene.control.*
import javafx.scene.paint.Color.RED
import javafx.scene.text.Text
import javafx.scene.text.TextFlow
import javafx.stage.FileChooser
import javafx.stage.Stage
import javafx.util.Callback
import org.apache.commons.csv.CSVFormat
import org.apache.commons.csv.CSVParser
import org.apache.commons.csv.CSVRecord
import org.fxmisc.richtext.CodeArea
import java.io.StringReader


class CSVInspectorGUI(
        private val executionEnvironment: ExecutionEnvironment,
        val primaryStage: Stage,
        private val csvPane: TabPane,
        private val outArea: TextFlow,
        private val codeArea: CodeArea,
        val scene: Scene) {

    @Subscribe
    private fun display(e: CSVEvent) {
        val tabPane = ScrollPane()
        tabPane.hbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        tabPane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        tabPane.prefHeight = 500.0
        tabPane.isFitToHeight = true
        tabPane.isFitToWidth = true
        tabPane.content = tableView(CSVFormat.DEFAULT.parse(StringReader(e.data)))
        val tab = Tab("show ${csvPane.tabs.size}", tabPane)
        tab.isClosable = true
        csvPane.tabs.add(tab)
        csvPane.selectionModel.select(tab)
    }

    @Subscribe
    private fun display(e: InfoEvent) {
        val outArea = TextArea()
        outArea.isEditable = false
        outArea.text = e.data

        val tabPane = ScrollPane()
        tabPane.hbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        tabPane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        tabPane.prefHeight = 500.0
        tabPane.isFitToHeight = true
        tabPane.isFitToWidth = true
        tabPane.content = outArea
        val tab = Tab("out ${csvPane.tabs.size}", tabPane)
        tab.isClosable = true
        csvPane.tabs.add(tab)
        csvPane.selectionModel.select(tab)
    }

    @Subscribe
    private fun display(e: ErrEvent) {
        System.err.println(e.data)
        val node = Text(e.data + "\n")
        node.fill = RED
        outArea.children.add(node)
    }

    @Subscribe
    private fun display(e: OutEvent) {
        System.err.println(e.data)
        val node = Text(e.data + "\n")
        outArea.children.add(node)
    }

    @Subscribe
    private fun display(e: SQLEvent) {
        val sqlArea = TextArea()
        sqlArea.isEditable = false
        sqlArea.text = e.data

        val tabPane = ScrollPane()
        tabPane.hbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        tabPane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        tabPane.prefHeight = 500.0
        tabPane.isFitToHeight = true
        tabPane.isFitToWidth = true
        tabPane.content = sqlArea
        val tab = Tab("sql ${csvPane.tabs.size}", tabPane)
        tab.isClosable = true
        csvPane.tabs.add(tab)
        csvPane.selectionModel.select(tab)
    }

    private fun executeScript() {
        csvPane.tabs.clear()
        val code = codeArea.text
        val task: Task<Unit> = executionEnvironment.createTask(code)
        Thread(task).start()
    }

    @Subscribe
    fun menuEventHandler(menuEvent: MenuEvent) {
        when (menuEvent.name) {
            "LOAD" -> loadScript()
            "SAVE" -> saveScript()
            "EXECUTE" -> executeScript()
            "QUIT" -> quitApplication()
            "COPY" -> copy()
            "CUT" -> cut()
            "PASTE" -> paste()
            else -> throw IllegalArgumentException("menu: ${menuEvent.name}")
        }
    }

    private fun copy() {
        when (scene.focusOwner) {
            codeArea -> codeArea.copy()
            else -> throw NotImplementedError()
        }
    }

    private fun cut() {
        when (scene.focusOwner) {
            codeArea -> codeArea.cut()
            else -> throw NotImplementedError()
        }
    }

    private fun paste() {
        when (scene.focusOwner) {
            codeArea -> codeArea.paste()
            else -> throw NotImplementedError()
        }
    }

    private fun quitApplication() {
        primaryStage.close()
    }

    private fun loadScript() {
        val fileChooser = FileChooser()
        fileChooser.title = "Open Script File"
        val selectedFile = fileChooser.showOpenDialog(primaryStage)
        val code = selectedFile.readText(Charsets.UTF_8)
        codeArea.replaceText(code)
    }

    private fun saveScript() {
        val fileChooser = FileChooser()
        fileChooser.title = "Save Script File"
        val selectedFile = fileChooser.showSaveDialog(primaryStage)
        selectedFile.writeText(codeArea.text, Charsets.UTF_8)
    }

    private fun tableView(parse: CSVParser): TableView<List<String>> {
        val tableView = TableView<List<String>>()
        val records = parse.records
        val types = records[0]
        val header = records[1]

        tableView.columns.add(createFirstColumn())
        tableView.columns.addAll(createOtherColumns(header, types))
        tableView.items.addAll(createRows(records))
        return tableView
    }

    private fun createFirstColumn(): TableColumn<List<String>, String> {
        val firstColumn = TableColumn<List<String>, String>("#")
        firstColumn.cellValueFactory = Callback { row ->
            ReadOnlyStringWrapper(row.value[0])
        }
        return firstColumn
    }

    private fun createOtherColumns(header: CSVRecord,
                                   types: CSVRecord): List<TableColumn<List<String>, String>> {
        return header.zip(types).withIndex().map {
            val column = TableColumn<List<String>, String>(
                    "[${it.index}: ${it.value.second}]\n${it.value.first}")
            column.cellValueFactory =
                    Callback { row ->
                        ReadOnlyStringWrapper(row.value[it.index + 1])
                    }
            column
        }
    }

    private fun createRows(records: MutableList<CSVRecord>) =
            records.subList(2, records.size).withIndex()
                    .map { listOf(it.index.toString()) + it.value.toList() }
}
