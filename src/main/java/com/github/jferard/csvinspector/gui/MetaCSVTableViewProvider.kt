package com.github.jferard.csvinspector.gui

import com.github.jferard.csvinspector.data.MetaCSVUtil
import javafx.beans.property.SimpleStringProperty
import javafx.event.EventHandler
import javafx.scene.control.TableColumn
import javafx.scene.control.TableView
import javafx.scene.control.cell.TextFieldTableCell
import javafx.util.Callback
import java.io.File


/** Not used */
class MetaCSVTableViewProvider {
    private val tableView = TableView<List<String>>()

    fun get(csvFile: File, metaCSVFile: File): TableView<List<String>> {
        addColumns()
        addRows(csvFile, metaCSVFile)
        tableView.isEditable = true
        tableView.userData = MetaCSVFileHandler(MetaCSVUtil(), csvFile, metaCSVFile)
        return tableView
    }

    private fun addColumns() {
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
                val row: Int
                val col: Int
                if (it.tablePosition.column == tableView.columns.size - 1) {
                    if (it.tablePosition.row == tableView.items.size - 1) {
                        tableView.items.add(listOf("", "", ""))
                    }
                    row = it.tablePosition.row + 1
                    col = 0
                } else {
                    row = it.tablePosition.row
                    col = it.tablePosition.column + 1
                }
                tableView.selectionModel.clearAndSelect(row, tableView.columns[col])
            }
            tableColumn
        })
    }

    private fun addRows(csvFile: File, metaCSVFile: File) {
        val rows = if (metaCSVFile.exists()) {
            MetaCSVUtil().readDirectives(metaCSVFile, csvFile)
        } else {
            MetaCSVUtil().guessDirectives(csvFile)
        }
        tableView.items.addAll(rows)
    }
}
