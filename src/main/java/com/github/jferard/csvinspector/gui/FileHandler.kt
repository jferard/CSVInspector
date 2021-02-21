package com.github.jferard.csvinspector.gui

import com.github.jferard.csvsniffer.CSVSniffer
import com.github.jferard.javamcsv.MetaCSVData
import com.github.jferard.javamcsv.MetaCSVParser
import com.github.jferard.javamcsv.MetaCSVReader
import com.github.jferard.javamcsv.MetaCSVRenderer
import org.apache.commons.csv.CSVFormat
import org.apache.commons.csv.CSVParser
import org.apache.commons.csv.CSVPrinter
import java.io.File
import java.io.StringReader

interface FileHandler {
    fun save(text: String)
    fun load(): String
}

class CodeFileHandler(val file: File) : FileHandler {
    override fun save(text: String) {
        file.writeText(text, Charsets.UTF_8)
    }

    override fun load(): String {
        return file.readText(Charsets.UTF_8)
    }
}

class MetaCSVFileHandler(val csvFile: File, val metaCSVFile: File) : FileHandler {
    override fun save(text: String) {
        val metaReader = CSVParser(StringReader(text), CSVFormat.DEFAULT.withDelimiter('\t'))
        val data = MetaCSVParser(
                metaReader.toList<Iterable<String>>()
                        .filter { it.all(String::isNotEmpty) }).parse()
        val metaRenderer = MetaCSVRenderer.create(metaCSVFile.outputStream())
        metaRenderer.render(data)
    }

    override fun load(): String {
        return if (metaCSVFile.exists()) {
            readDirectives()
        } else {
            guessDirectives()
        }
    }

    private fun readDirectives(): String {
        metaCSVFile.inputStream().use {
            val parser = MetaCSVParser.create(it)
            val data = parser.parse()
            return directivesFromData(data)
        }
    }

    private fun guessDirectives(): String {
        csvFile.inputStream().use {
            val data = CSVSniffer.create().sniff(it)
            return directivesFromData(data)
        }
    }

    private fun directivesFromData(data: MetaCSVData): String {
        val sb = StringBuilder()
        val printer = CSVPrinter(sb, CSVFormat.DEFAULT.withDelimiter('\t'))
        MetaCSVRenderer.create(printer, false).render(data)
        csvFile.inputStream().use { stream ->
            MetaCSVReader.create(stream, data).use { reader ->
                reader.firstOrNull()?.let { rec ->
                    for (i in (0 until rec.size())) {
                        sb.append("data\tcol/$i/type\ttext\r\n")
                    }
                }
            }
        }
        return sb.toString()
    }
}