package com.github.jferard.csvinspector.gui

import com.github.jferard.csvsniffer.CSVSniffer
import com.github.jferard.javamcsv.MetaCSVPrinter
import com.github.jferard.javamcsv.MetaCSVRenderer
import javafx.beans.property.SimpleStringProperty
import javafx.event.EventHandler
import javafx.scene.control.TableColumn
import javafx.scene.control.TableView
import javafx.scene.control.cell.TextFieldTableCell
import javafx.util.Callback
import org.apache.commons.csv.CSVFormat
import org.apache.commons.csv.CSVPrinter
import org.mozilla.intl.chardet.HtmlCharsetDetector
import org.mozilla.intl.chardet.HtmlCharsetDetector.found
import org.mozilla.intl.chardet.nsDetector
import org.mozilla.intl.chardet.nsICharsetDetectionObserver
import java.io.*
import java.nio.charset.Charset


class MetaCSVAreaProvider {
    private val tableView = TableView<List<String>>()

    fun get(csvFile: File, metaCSVFile: File): TableView<List<String>> {
        addColumns()
        addRows(csvFile, metaCSVFile)
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

    private fun addRows(csvFile: File, metaCSVFile: File) {
        val array = if (metaCSVFile.exists()) {
            readDirectives(metaCSVFile)
        } else {
            guessDirectives(csvFile)
        }
        tableView.items.addAll(*array)
    }

    private fun guessDirectives(csvFile: File): Array<List<String>> {
        val inputStream = FileInputStream(csvFile)
        inputStream.use {
            val data = CSVSniffer.create().sniff(inputStream)
            val directives: MutableList<List<String>>  = mutableListOf()
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
            return directives.drop(1).toTypedArray()
        }
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
