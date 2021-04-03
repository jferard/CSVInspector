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
import com.github.jferard.csvinspector.util.*
import com.github.jferard.javamcsv.MetaCSVParser
import com.github.jferard.javamcsv.MetaCSVParserBuilder
import com.github.jferard.javamcsv.MetaCSVReader
import com.google.common.eventbus.Subscribe
import javafx.concurrent.Task
import javafx.geometry.Insets
import javafx.scene.Scene
import javafx.scene.control.*
import javafx.scene.paint.Color.RED
import javafx.scene.text.Text
import javafx.scene.text.TextFlow
import javafx.stage.FileChooser
import javafx.stage.Stage
import org.apache.commons.csv.CSVFormat
import org.apache.commons.csv.CSVParser
import org.fxmisc.richtext.CodeArea
import java.io.File
import java.io.FileInputStream
import java.io.StringReader


class CSVInspectorGUI(
        private val dynamicProvider: DynamicProvider,
        private val executionEnvironment: ExecutionEnvironment,
        private val primaryStage: Stage,
        private val csvPane: TabPane,
        private val outArea: TextFlow,
        private val codePane: TabPane,
        val scene: Scene) {

    init {
        this.executeOneScript("print('Python server ready...')")
    }

    @Subscribe
    private fun display(e: MetaCSVEvent) {
        val tabPane = ScrollPane()
        tabPane.hbarPolicy = ScrollPane.ScrollBarPolicy.NEVER
        tabPane.vbarPolicy = ScrollPane.ScrollBarPolicy.NEVER
        tabPane.prefHeight = 500.0
        tabPane.isFitToHeight = true
        tabPane.isFitToWidth = true
        val tableView =
                dynamicProvider.createMetaTableViewFromMetaCSVRecords(e.rows, e.data)
        tableView.columns.last().style = "-fx-padding: 0 15 0 0;"
        tabPane.content = tableView
        val tab = Tab("show ${csvPane.tabs.size}", tabPane)
        tab.isClosable = true
        csvPane.tabs.add(tab)
        csvPane.selectionModel.select(tab)
    }

    @Subscribe
    private fun display(e: RawCSVEvent) {
        val tabPane = ScrollPane()
        tabPane.hbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        tabPane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        tabPane.prefHeight = 500.0
        tabPane.isFitToHeight = true
        tabPane.isFitToWidth = true
        tabPane.content =
                dynamicProvider.createTableViewFromCSVRecords(
                        CSVFormat.DEFAULT.parse(StringReader(e.data)))
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
        node.style = "-fx-font-family: 'monospaced'"
        outArea.children.add(node)
    }

    @Subscribe
    private fun display(e: OutEvent) {
        System.err.println(e.data)
        val node = Text(e.data + "\n")
        node.style = "-fx-font-family: 'monospaced'"
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

    @Subscribe
    fun menuEventHandler(menuEvent: MenuEvent) {
        when (menuEvent.name) {
            /* File */
            "OPEN" -> openScript()
            "OPEN_CSV" -> openCSV()
            "SAVE" -> saveScript()
            "SAVE_AS" -> saveAsScript()

            "EXECUTE" -> executeScript()
            "RESTART" -> restartInterpreter()

            "QUIT" -> quitApplication()

            /* Edit */
            "NEW_TAB" -> dynamicProvider.createEmptyCodePane(codePane)

            "COPY" -> copy()
            "CUT" -> cut()
            "PASTE" -> paste()

            "FIND" -> find()

            /* Help */
            "HELP" -> help()
            "SNIPPET_1" -> snippet(SHOW_SQL_EXAMPLE)
            "SNIPPET_2" -> snippet(SELECT_EXAMPLE)
            "SNIPPET_3" -> snippet(GROUPBY_EXAMPLE)
            "SNIPPET_4" -> snippet(JOIN_EXAMPLE)
            "SNIPPET_5" -> snippet(CODE_EXAMPLE)
            "ABOUT" -> about()
            else -> throw IllegalArgumentException("menu: ${menuEvent.name}")
        }
    }

    private fun executeScript() {
        csvPane.tabs.clear()
        val tab = getCurTab()
        when (tab.handler) {
            is MetaCSVFileHandler -> showCSV(tab)
            is CodeFileHandler, is UntitledCodeFileHandler -> {
                executeOneScript(tab.text)
            }
            else -> {
                println("Can't execute $tab")
            }
        }
    }

    private fun showCSV(tab: TabWrapper) {
        val metaReader = CSVParser(StringReader(tab.text), CSVFormat.DEFAULT.withDelimiter('\t'))
        val data = MetaCSVParser(metaReader, true, MetaCSVParserBuilder.DEFAULT_OBJECT_PARSER).parse()
        val reader =
                MetaCSVReader.create(FileInputStream((tab.handler as MetaCSVFileHandler).csvFile),
                        data)
        val rows = reader.toMutableList()
        val task: Task<Unit> = executionEnvironment.createCSV(rows, data)
        Thread(task).start()
    }

    private fun restartInterpreter() {
        executionEnvironment.restart()
    }

    private fun executeOneScript(code: String) {
        val task: Task<Unit> = executionEnvironment.createTask(code)
        Thread(task).start()
    }

    //    private fun getCodeArea(): CodeArea {
//        val node = getCurScrollPaneContent()
//        return node as CodeArea
//    }
//
//    private fun getCurScrollPaneContent(): Node {
//        val tab = getCurTab()
//        val pane = tab.content as ScrollPane
//        return pane.content
//    }

    private fun getCurTab() = TabWrapper(codePane.selectionModel.selectedItem)

//    private fun getCodeTabName(): String {
//        val tab = getCurTab()
//        return tab.text
//    }
//
//    private fun getCodeTabFileHandler(): FileHandler? {
//        val tab = getCurTab()
//        return tab.userData as? FileHandler
//    }

    private fun openCSV() {
        val fileChooser = FileChooser()
        fileChooser.title = "Open CSV File"
        val selectedFile = fileChooser.showOpenDialog(primaryStage) ?: return
        addCSVPane(selectedFile)
    }

    private fun snippet(code: String) {
        dynamicProvider.createEmptyCodePane(codePane)
        getCurTab().text = code
    }

    private fun find() {
        val dialog: Dialog<Pair<String, String>> = dynamicProvider.createFindDialog()
        val result = dialog.showAndWait()
        result.ifPresent { findReplace ->
            val toFind = findReplace.first
            val replacement = findReplace.second
            if (replacement.isBlank()) {
                highlightToFind(toFind)
            } else {
                highlightReplaced(toFind, replacement)
            }
        }
    }

    private fun highlightToFind(toFind: String) {
        val codeArea = getCurTab().codeArea
        val ranges = Regex(toFind).findAll(codeArea.text).map { it.range }
        highlightRanges(codeArea, ranges)
    }

    private fun highlightReplaced(toFind: String, replacement: String) {
        val codeArea = getCurTab().codeArea
        val ranges = mutableListOf<IntRange>()
        var match = Regex(toFind).find(codeArea.text)
        while (match != null) {
            val from = match.range.first
            codeArea.replaceText(from, match.range.last + 1, replacement)
            ranges.add(IntRange(from, from + replacement.length))
            match = Regex(toFind).find(codeArea.text, from + replacement.length)
        }
        highlightRanges(codeArea, ranges.asSequence())
    }

    private fun highlightRanges(codeArea: CodeArea,
                                ranges: Sequence<IntRange>) {
        ranges.take(1).forEach {
            codeArea.setStyleClass(it.first, it.last + 1, "highlight")
        }
        ranges.drop(1).forEach {
            codeArea.selectRange(it.first, it.last + 1)
            codeArea.setStyleClass(it.first, it.last + 1, "highlight")
        }
    }

    private fun about() {
        val alert = Alert(Alert.AlertType.INFORMATION)

        alert.title = "About CSVInspector"
        alert.graphic = null
        alert.headerText = "CSVInspector (C) 2020 J. Férard"
        alert.contentText = """https://github.com/jferard/CSVInspector
            
License: GPLv3""".trimIndent()
        alert.showAndWait()
    }

    private fun help() {
        executeOneScript("""from csv_inspector import *

begin_info()
print(help(inspect))
print(help(data.Data))
end_info()""")
    }

    private fun copy() {
        val codeArea = getCurTab().codeArea
        when (scene.focusOwner) {
            codeArea -> codeArea.copy()
            else -> throw NotImplementedError()
        }
    }

    private fun cut() {
        val codeArea = getCurTab().codeArea
        when (scene.focusOwner) {
            codeArea -> codeArea.cut()
            else -> throw NotImplementedError()
        }
    }

    private fun paste() {
        val codeArea = getCurTab().codeArea
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
        val selectedFile = fileChooser.showOpenDialog(primaryStage) ?: return
        addCodePane(selectedFile)
    }

    private fun addCSVPane(selectedFile: File) {
        if (selectedFile.extension == ".mcsv") {
            // TODO: display error message
            return
        }
        val metaCSVFile = File(selectedFile.parent, selectedFile.nameWithoutExtension + ".mcsv")
        val cur =
                codePane.tabs.find { (it.userData as? MetaCSVFileHandler)?.csvFile == selectedFile }
        if (cur != null) {
            codePane.selectionModel.select(cur)
            return
        }
        val codeTab = dynamicProvider.createMetaCSVTab(selectedFile, metaCSVFile)
        codePane.tabs.add(codePane.tabs.size - 1, codeTab)
        codePane.selectionModel.select(codeTab)
        val tabWrapper = TabWrapper(codeTab)
        showCSV(tabWrapper)
        /**
        val code = selectedFile.readText(Charsets.UTF_8)
        val codeArea = getCodeArea()
        codeArea.replaceText(code)
         */
    }

    private fun addCodePane(selectedFile: File) {
        val cur = codePane.tabs.find { it.userData == selectedFile }
        if (cur != null) {
            codePane.selectionModel.select(cur)
            return
        }
        val codeTab = dynamicProvider.createCodeTab(selectedFile)
        val tabWrapper = TabWrapper(codeTab)
        tabWrapper.text = tabWrapper.handler!!.load()
        codePane.tabs.add(codePane.tabs.size - 1, codeTab)
        codePane.selectionModel.select(codeTab)
    }

    private fun saveScript() {
        val tab = getCurTab()
        val handler = tab.handler ?: run {
            val file = saveTo() ?: return
            val h = CodeFileHandler(file)
            tab.handler = h
            h
        }
        handler.save(tab.text)
    }

    private fun saveAsScript() {
        val tab = getCurTab()
        val selectedFile = saveTo() ?: return
        val handler = CodeFileHandler(selectedFile)
        handler.save(tab.text)
        tab.handler = handler
        tab.name = selectedFile.name
    }

    private fun saveTo(): File? {
        val fileChooser = FileChooser()
        fileChooser.title = "Save Script File"
        return fileChooser.showSaveDialog(primaryStage)
    }
}
