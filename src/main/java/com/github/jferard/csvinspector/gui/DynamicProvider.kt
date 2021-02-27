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

import com.github.jferard.csvinspector.data.MetaCSVUtil
import com.github.jferard.javamcsv.MetaCSVData
import com.github.jferard.javamcsv.MetaCSVRecord
import javafx.application.Platform
import javafx.beans.property.ReadOnlyStringWrapper
import javafx.geometry.Insets
import javafx.scene.control.*
import javafx.scene.layout.GridPane
import javafx.util.Callback
import org.apache.commons.csv.CSVRecord
import java.io.File

class DynamicProvider {
    private val metaCSVUtil = MetaCSVUtil()

    fun createEmptyCodePane(codePane: TabPane) {
        val codeTab = createNamedCodeTab("Untitled")
        codePane.tabs.add(codePane.tabs.size - 1, codeTab)
        codePane.selectionModel.select(codeTab)
    }

    fun createCodeTab(file: File): Tab {
        val tab = createNamedCodeTab(file.name)
        tab.userData = CodeFileHandler(file)
        return tab
    }

    private fun createNamedCodeTab(name: String): Tab {
        val codeArea = CodeAreaProvider().get()
        val oneScriptPane = ScrollPane()
        oneScriptPane.content = codeArea

        oneScriptPane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        oneScriptPane.prefHeight = 500.0
        oneScriptPane.isFitToWidth = true
        oneScriptPane.isFitToHeight = true
        return Tab(name, oneScriptPane)
    }

    fun createTableViewFromCSVRecords(records: Iterable<CSVRecord>): TableView<List<String>> {
        val tableView = TableView<List<String>>()
        val headerAndTypes = records.take(2)
        val types = headerAndTypes.first()
        val header = headerAndTypes.last()

        tableView.columns.add(createFirstColumn())
        tableView.columns.addAll(createOtherColumns(header, types))
        tableView.items.addAll(createRowsFromCSVRecords(records, header.size()))
        return tableView
    }

    fun createMetaTableViewFromMetaCSVRecords(rows: List<MetaCSVRecord>,
                                              data: MetaCSVData): TableView<List<String>> {
        val tableView = TableView<List<String>>()
        val cssResource = CSVInspectorGUI::class.java.getResource("/table.css")
        tableView.stylesheets.add(cssResource.toExternalForm())
        val headerRecord = rows[0]
        val types = (0 until headerRecord.size()).map {
            when (val description = data.getDescription(
                    it)) {
                null -> "text"
                else -> description.dataType.toString()
            }
        }
        val header = (0 until headerRecord.size()).map { headerRecord.getText(it).toString() }

        tableView.columns.add(createFirstColumn())
        tableView.columns.addAll(createOtherColumns(header, types))
        tableView.items.addAll(createRowsFromMetaCSVRecords(rows, header.size))
        return tableView
    }

    private fun createFirstColumn(): TableColumn<List<String>, String> {
        val firstColumn = TableColumn<List<String>, String>("#")
        firstColumn.cellValueFactory = Callback { row ->
            ReadOnlyStringWrapper(row.value[0])
        }
        firstColumn.styleClass.add("right-align")
        return firstColumn
    }

    private fun createOtherColumns(header: Iterable<String>,
                                   types: Iterable<String>): List<TableColumn<List<String>, String>> {
        return header.zip(types).withIndex().map { (c, name_and_type) ->
            val (name, type) = name_and_type
            val column = TableColumn<List<String>, String>(
                    "[${c}: ${type}]\n${name}")
            column.cellValueFactory =
                    Callback { row ->
                        ReadOnlyStringWrapper(row.value[c + 1]) // c0 is for row number
                    }
            if (type != "TEXT" && type != "OBJECT") {
                column.styleClass.add("right-align")
            }
            column
        }
    }

    private fun createRowsFromCSVRecords(records: Iterable<CSVRecord>, size: Int) =
            records.withIndex()
                    .map { (r, record) ->
                        listOf(r.toString()) + record.toList() + (record.size() until size).map {
                            ""
                        }
                    }

    private fun createRowsFromMetaCSVRecords(records: List<MetaCSVRecord>, size: Int) =
            records.subList(1, records.size).withIndex()
                    .map { (r, record) ->
                        listOf(r.toString()) + record.map { value ->
                            value?.toString() ?: "<NULL>"
                        } + (record.size() until size).map {
                            "<NULL>"
                        }
                    }

    fun createFindDialog(): Dialog<Pair<String, String>> {
        val dialog: Dialog<Pair<String, String>> = Dialog()
        dialog.title = "Find/Replace"
        dialog.graphic = null
        val okButtonType = ButtonType("Ok", ButtonBar.ButtonData.OK_DONE)
        dialog.dialogPane.buttonTypes.addAll(okButtonType, ButtonType.CANCEL)
        val grid = GridPane()
        grid.hgap = 10.0
        grid.vgap = 10.0
        grid.padding = Insets(20.0, 150.0, 10.0, 10.0)

        val findText = TextField()
        findText.promptText = "Find"
        val replaceText = TextField()
        replaceText.promptText = "Replace"

        grid.add(Label("Find:"), 0, 0)
        grid.add(findText, 1, 0)
        grid.add(Label("Replace:"), 0, 1)
        grid.add(replaceText, 1, 1)

        val okButton = dialog.dialogPane.lookupButton(okButtonType)
        okButton.isDisable = true

        findText.textProperty().addListener { _, _, newValue ->
            okButton.isDisable = newValue.trim().isEmpty()
        }

        dialog.dialogPane.content = grid

        Platform.runLater { findText.requestFocus() }

        dialog.setResultConverter { dialogButton: ButtonType ->
            if (dialogButton == okButtonType) {
                Pair(findText.text, replaceText.text)
            } else {
                null
            }
        }
        return dialog
    }

    fun createMetaCSVTab(csvFile: File, metaCSVFile: File): Tab {
        val codeArea = MetaCSVCodeAreaProvider().get()
        val onePane = ScrollPane()
        onePane.content = codeArea

        onePane.vbarPolicy = ScrollPane.ScrollBarPolicy.ALWAYS
        onePane.prefHeight = 500.0
        onePane.isFitToWidth = true
        onePane.isFitToHeight = true
        val metaTab = Tab(metaCSVFile.name, onePane)
        val tab = TabWrapper(metaTab)
        val handler = MetaCSVFileHandler(metaCSVUtil, csvFile, metaCSVFile)
        tab.text = handler.load()
        tab.handler = handler
        return metaTab
    }
}