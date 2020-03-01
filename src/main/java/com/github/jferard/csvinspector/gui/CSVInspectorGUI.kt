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
import java.io.File
import java.io.StringReader


class CSVInspectorGUI(
        private val executionEnvironment: ExecutionEnvironment,
        val primaryStage: Stage,
        private val csvPane: TabPane,
        private val outArea: TextFlow,
        private val codePane: TabPane,
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
        val codeArea = getCodeArea()
        val code = codeArea.text
        val task: Task<Unit> = executionEnvironment.createTask(code)
        Thread(task).start()
    }

    private fun getCodeArea(): CodeArea {
        val tab = codePane.selectionModel.selectedItem
        val pane = tab.content as ScrollPane
        return pane.content as CodeArea
    }

    private fun getCodeTabName(): String {
        val tab = codePane.selectionModel.selectedItem
        return tab.text
    }

    private fun getCodeTabFile(): File? {
        val tab = codePane.selectionModel.selectedItem
        return tab.userData as File?
    }

    @Subscribe
    fun menuEventHandler(menuEvent: MenuEvent) {
        when (menuEvent.name) {
            "OPEN" -> openScript()
            "SAVE" -> saveScript()
            "SAVE_AS" -> saveAsScript()
            "EXECUTE" -> executeScript()
            "QUIT" -> quitApplication()
            "NEW_TAB" -> addEmptyCodePane()
            "COPY" -> copy()
            "CUT" -> cut()
            "PASTE" -> paste()
            else -> throw IllegalArgumentException("menu: ${menuEvent.name}")
        }
    }

    private fun copy() {
        val codeArea = getCodeArea()
        when (scene.focusOwner) {
            codeArea -> codeArea.copy()
            else -> throw NotImplementedError()
        }
    }

    private fun cut() {
        val codeArea = getCodeArea()
        when (scene.focusOwner) {
            codeArea -> codeArea.cut()
            else -> throw NotImplementedError()
        }
    }

    private fun paste() {
        val codeArea = getCodeArea()
        when (scene.focusOwner) {
            codeArea -> codeArea.paste()
            else -> throw NotImplementedError()
        }
    }

    private fun quitApplication() {
        primaryStage.close()
    }

    private fun openScript() {
        val fileChooser = FileChooser()
        fileChooser.title = "Open Script File"
        val selectedFile = fileChooser.showOpenDialog(primaryStage)
        addCodePane(selectedFile)
    }

    private fun addCodePane(selectedFile: File) {
        val cur = codePane.tabs.find { it.userData == selectedFile }
        if (cur != null) {
            codePane.selectionModel.select(cur)
            return
        }
        val code = selectedFile.readText(Charsets.UTF_8)
        val codeTab = codeTab(selectedFile)
        codePane.tabs.add(codePane.tabs.size - 1, codeTab)
        codePane.selectionModel.select(codeTab)
        val codeArea = getCodeArea()
        codeArea.replaceText(code)
    }

    private fun codeTab(file: File): Tab {
        val tab = codeTab(file.name)
        tab.userData = file
        return tab
    }

    private fun codeTab(name: String): Tab {
        val codeArea = CodeAreaProvider().get()
        val oneScriptPane = ScrollPane()
        oneScriptPane.content = codeArea

        oneScriptPane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        oneScriptPane.prefHeight = 500.0
        oneScriptPane.isFitToWidth = true
        oneScriptPane.isFitToHeight = true
        return Tab(name, oneScriptPane)
    }

    private fun addEmptyCodePane() {
        val codeTab = codeTab("Untitled")
        codePane.tabs.add(codePane.tabs.size - 1, codeTab)
        codePane.selectionModel.select(codeTab)
    }

    private fun saveScript() {
        var selectedFile = getCodeTabFile()
        if (selectedFile == null) {
            selectedFile = saveTo() ?: return
        }
        val codeArea = getCodeArea()
        selectedFile.writeText(codeArea.text, Charsets.UTF_8)
        setCodeTabFile(selectedFile)
    }

    private fun saveAsScript() {
        val selectedFile = saveTo() ?: return
        val codeArea = getCodeArea()
        selectedFile.writeText(codeArea.text, Charsets.UTF_8)
        setCodeTabFile(selectedFile)
    }

    private fun setCodeTabFile(selectedFile: File) {
        val tab = codePane.selectionModel.selectedItem
        tab.userData = selectedFile
        tab.text = selectedFile.name
    }

    private fun saveTo(): File? {
        val fileChooser = FileChooser()
        fileChooser.title = "Save Script File"
        return fileChooser.showSaveDialog(primaryStage)
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
