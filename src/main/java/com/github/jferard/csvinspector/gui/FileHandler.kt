package com.github.jferard.csvinspector.gui

import com.github.jferard.csvinspector.data.MetaCSVUtil
import com.github.jferard.javamcsv.*
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

class MetaCSVFileHandler(val metaCSVUtil: MetaCSVUtil, val csvFile: File, val metaCSVFile: File) : FileHandler {
    override fun save(text: String) {
        val metaReader = CSVParser(StringReader(text), CSVFormat.DEFAULT.withDelimiter('\t'))
        val data = MetaCSVParser(
                metaReader.toList<Iterable<String>>()
                        .filter { it.all(String::isNotEmpty) }).parse()
        val metaRenderer = MetaCSVRenderer.create(metaCSVFile.outputStream())
        metaRenderer.render(data)
    }

    override fun load(): String {

        val directives = if (metaCSVFile.exists()) {
            metaCSVUtil.readDirectives(metaCSVFile, csvFile)
        } else {
            metaCSVUtil.guessDirectives(csvFile)
        }
        val sb = StringBuilder()
        val printer = CSVPrinter(sb, CSVFormat.DEFAULT.withDelimiter('\t'))
        for (directive in directives) {
            printer.printRecord(*directive.toTypedArray())
        }
        return sb.toString()
    }
}