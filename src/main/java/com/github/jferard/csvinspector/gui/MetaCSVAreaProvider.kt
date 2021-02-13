package com.github.jferard.csvinspector.gui

import javafx.beans.property.SimpleStringProperty
import javafx.event.EventHandler
import javafx.scene.control.TableColumn
import javafx.scene.control.TableView
import javafx.scene.control.cell.TextFieldTableCell
import javafx.util.Callback
import org.apache.commons.csv.CSVFormat
import java.io.File
import java.io.FileInputStream
import java.io.InputStreamReader

class MetaCSVAreaProvider {
    private val tableView = TableView<List<String>>()

    fun get(csvFile: File, metaCSVFile: File): TableView<List<String>> {
        addColumns()
        addRows(metaCSVFile)
        tableView.isEditable = true
        tableView.userData = csvFile
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
                if (it.tablePosition.row == tableView.items.size - 1) {
                    tableView.items.add(listOf("", "", ""))
                }
            }
            tableColumn
        })
    }

    private fun addRows(metaCSVFile: File) {
        val array = if (metaCSVFile.exists()) {
            readDirectives(metaCSVFile)
        } else {
            guessDirectives()
        }
        tableView.items.addAll(*array)
    }

    private fun guessDirectives(): Array<List<String>> {
        // TODO: guess the type
        // <dependency>
        //    <groupId>jchardet</groupId>
        //    <artifactId>jchardet</artifactId>
        //    <version>1.1.0</version>
        //</dependency>
        // copy python csv detector.
        return (1..10).map { listOf("", "", "") }.toTypedArray()
    }

    private fun readDirectives(
            metaCSVFile: File): Array<List<String>> {
        val reader = InputStreamReader(FileInputStream(metaCSVFile), Charsets.UTF_8)
        val records = CSVFormat.DEFAULT.parse(reader).records
        return reader.use {
            val header = records.take(1)
            if (header.isEmpty() || header[0].toList() != listOf("domain", "key", "value")) {
                arrayOf(listOf("invalid", "mcsv", "file"))
            }
            records.drop(1).map {
                it.toList()
            }.toTypedArray()
        }
    }
}
