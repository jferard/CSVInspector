package com.github.jferard.csvinspector.gui

import com.github.jferard.csvsniffer.CSVSniffer
import com.github.jferard.javamcsv.*
import javafx.scene.control.TableView
import org.apache.commons.csv.CSVFormat
import org.apache.commons.csv.CSVPrinter
import org.fxmisc.richtext.CodeArea
import java.io.File
import java.io.FileInputStream


class MetaCSVAreaProvider2 {
    private val tableView = TableView<List<String>>()

    fun get(csvFile: File, metaCSVFile: File): CodeArea {
        val codeArea = CodeArea()
        codeArea.isWrapText = true
        val resource = CSVInspectorGUI::class.java.getResource("/metacsv.css")
        codeArea.stylesheets
                .add(resource.toExternalForm())
        codeArea.replaceText(getText(csvFile, metaCSVFile))
        return codeArea
    }

    private fun getText(csvFile: File, metaCSVFile: File) : String {
        return if (metaCSVFile.exists()) {
            readDirectives(metaCSVFile, csvFile)
        } else {
            guessDirectives(csvFile)
        }
    }

    private fun guessDirectives(csvFile: File): String {
        val inputStream = FileInputStream(csvFile)
        inputStream.use {
            val data = CSVSniffer.create().sniff(inputStream)
            return directivesFromData(data, csvFile)
        }
    }

    private fun directivesFromData(
            data: MetaCSVData,
            csvFile: File): String {
        val sb = StringBuilder()
        val printer = CSVPrinter(sb, CSVFormat.DEFAULT.withDelimiter('\t'))
        MetaCSVRenderer.create(printer, false).render(data)
        val inputStream = FileInputStream(csvFile)
        val reader = MetaCSVReader.create(inputStream, data)
        reader.use {
            reader.firstOrNull()?.let {
                for (i in (0 until it.size())) {
                    sb.append("data\tcol/$i/type\ttext\r\n")
                }
            }
        }
        return sb.toString()
    }

    private fun readDirectives(
            metaCSVFile: File, csvFile: File): String {
        val inputStream = FileInputStream(metaCSVFile)
        inputStream.use {
            val parser = MetaCSVParser.create(inputStream)
            val data = parser.parse()
            return directivesFromData(data, csvFile)
        }
    }
}
