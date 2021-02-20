package com.github.jferard.csvinspector.gui

import com.github.jferard.csvsniffer.CSVSniffer
import com.github.jferard.javamcsv.*
import javafx.beans.property.SimpleStringProperty
import javafx.event.EventHandler
import javafx.scene.control.TableColumn
import javafx.scene.control.TableView
import javafx.scene.control.cell.TextFieldTableCell
import javafx.util.Callback
import java.io.File
import java.io.FileInputStream


class MetaCSVAreaProvider {
    private val tableView = TableView<List<String>>()

    fun get(csvFile: File, metaCSVFile: File): TableView<List<String>> {
        addColumns()
        addRows(csvFile, metaCSVFile)
        tableView.isEditable = true
        tableView.userData = MetaCSVUserData(csvFile)
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
        val array = if (metaCSVFile.exists()) {
            readDirectives(metaCSVFile, csvFile)
        } else {
            guessDirectives(csvFile)
        }
        tableView.items.addAll(*array)
    }

    private fun guessDirectives(csvFile: File): Array<List<String>> {
        val inputStream = FileInputStream(csvFile)
        inputStream.use {
            val data = CSVSniffer.create().sniff(inputStream)
            return directivesFromData(data, csvFile)
        }
    }

    private fun directivesFromData(
            data: MetaCSVData,
            csvFile: File): Array<List<String>> {
        val directives: MutableList<List<String>> = mutableListOf()
        val printer = object : MetaCSVPrinter {
            override fun printRecord(domain: String, key: String, value: Any) {
                val directive = listOf(domain, key, value.toString())
                directives.add(directive)
            }

            override fun flush() {
                // do nothing
            }
        }
        MetaCSVRenderer(printer, false).render(data)
        val inputStream = FileInputStream(csvFile)
        val reader = MetaCSVReader.create(inputStream, data)
        reader.use {
            reader.first { rec ->
                directives.addAll(
                        (0 until rec.size()).map { listOf("data", "col/$it/type", "text") })
            }
        }
        return directives.drop(1).toTypedArray()
    }

    private fun readDirectives(
            metaCSVFile: File, csvFile: File): Array<List<String>> {
        val inputStream = FileInputStream(metaCSVFile)
        inputStream.use {
            val parser = MetaCSVParser.create(inputStream)
            val data = parser.parse()
            return directivesFromData(data, csvFile)
        }
    }
}
