package com.github.jferard.csvinspector.gui

import com.github.jferard.javamcsv.MetaCSVParser
import com.github.jferard.javamcsv.MetaCSVRenderer
import org.apache.commons.csv.CSVFormat
import org.apache.commons.csv.CSVParser
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

class MetaCSVFileHandler(val csvFile: File, val metaCSVFile : File) : FileHandler {
    override fun save(text: String) {
        val metaReader = CSVParser(StringReader(text), CSVFormat.DEFAULT.withDelimiter('\t'))
        val data = MetaCSVParser(metaReader.toList<Iterable<String>>().filter { it.all { it.isNotEmpty() } }).parse()
        val metaRenderer = MetaCSVRenderer.create(metaCSVFile.outputStream())
        metaRenderer.render(data)
    }

    override fun load(): String {
        throw NotImplementedError() //To change body of created functions use File | Settings | File Templates.
    }
}