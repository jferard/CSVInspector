package com.github.jferard.csvinspector.gui

import javafx.beans.property.SimpleStringProperty
import javafx.event.EventHandler
import javafx.scene.control.TableColumn
import javafx.scene.control.TableView
import javafx.scene.control.cell.TextFieldTableCell
import javafx.util.Callback
import java.io.File

class MetaCSVAreaProvider {
    fun get(metaCSVFile: File): TableView<List<String>> {
        val tableView = TableView<List<String>>()
        tableView.columns.addAll(arrayOf("domain", "key", "value").withIndex().map { indexedCol ->
            val tableColumn = TableColumn<List<String>, String>(indexedCol.value)
            tableColumn.isEditable = true
            tableColumn.cellValueFactory = Callback { row ->
                val stringProperty = SimpleStringProperty()
                stringProperty.set(row.value[indexedCol.index])
                stringProperty
            }
            tableColumn.cellFactory = TextFieldTableCell.forTableColumn()
            tableColumn.onEditCommit = EventHandler {
                tableView.items[it.tablePosition.row] =
                        tableView.items[it.tablePosition.row].withIndex().map { indexedValue ->
                            if (indexedValue.index == it.tablePosition.column) {
                                it.newValue
                            } else {
                                indexedValue.value
                            }
                        }
                if (it.tablePosition.row == tableView.items.size - 1) {
                    tableView.items.add(listOf("", "", ""))
                }
            }
            tableColumn
        })
        tableView.isEditable = true
        val array = if (metaCSVFile.exists()) {
            arrayOf(listOf("file", "key", "value"), listOf("", "", ""))
        } else {
            // TODO: guess the type
            (1..10).map { listOf("", "", "") }.toTypedArray()
        }
        tableView.items.addAll(*array)
        return tableView
    }
}
