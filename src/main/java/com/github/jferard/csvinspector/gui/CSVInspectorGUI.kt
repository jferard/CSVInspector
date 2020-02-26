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

import com.google.common.eventbus.Subscribe
import javafx.beans.property.ReadOnlyStringWrapper
import javafx.scene.Scene
import javafx.scene.control.*
import javafx.scene.paint.Color.RED
import javafx.scene.text.Text
import javafx.scene.text.TextFlow
import javafx.util.Callback
import org.apache.commons.csv.CSVFormat
import org.apache.commons.csv.CSVParser
import java.io.StringReader


class CSVInspectorGUI(private val csvPane: TabPane,
                      private val outArea: TextFlow,
                      private val codeArea: TextArea,
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
        System.err.println(e.text)
        val node = Text(e.text + "\n")
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

    private fun tableView(parse: CSVParser): TableView<List<String>> {
        val tableView = TableView<List<String>>()
        val records = parse.records
        val types = records[0]
        val header = records[1]
        tableView.columns.addAll(header.zip(types).withIndex().map {
            val column = TableColumn<List<String>, String>("[${it.index}: ${it.value.second}]\n${it.value.first}")
            column.cellValueFactory =
                    Callback { row ->
                        ReadOnlyStringWrapper(row.value[it.index])
                    }
            column
        })
        tableView.items.addAll(records.subList(2, records.size).map { it.toList() })
        return tableView
    }
}
