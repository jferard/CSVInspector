package com.github.jferard.csvinspector.gui

import com.github.jferard.csvsniffer.MetaCSVSniffer
import com.github.jferard.javamcsv.*
import org.apache.commons.csv.CSVFormat
import org.apache.commons.csv.CSVParser
import org.apache.commons.csv.CSVPrinter
import java.io.File
import java.io.FileInputStream
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
            val data = MetaCSVSniffer.create().sniff(it)
            return directivesFromData(data)
        }
    }

    private fun directivesFromData(data: MetaCSVData): String {
        val directives: MutableList<Array<String>> = mutableListOf()
        val regex = Regex("col/\\d+/type")
        val customPrinter = object : MetaCSVPrinter {
            override fun printRecord(domain: String, key: String, value: Any) {
                val directive = arrayOf(domain, key, value.toString())
                if (!key.matches(regex)) {
                    directives.add(directive)
                }
            }
            override fun flush() {
                // do nothing
            }
        }
        MetaCSVRenderer(customPrinter, false).render(data)
        val inputStream = FileInputStream(csvFile)
        val parser = CSVParser(inputStream.bufferedReader(data.encoding),
                CSVFormatHelper.getCSVFormat(data))
        parser.use {
            parser.first { rec ->
                directives.addAll(
                        (0 until rec.size()).map {
                            arrayOf("data", "col/$it/type",
                                    when (val description = data.getDescription(it)) {
                                        null -> "text"
                                        else -> {
                                            val out = StringBuilder();
                                            description.render(out);
                                            out.toString()
                                        }
                                    })
                        })
            }
        }
        val sb = StringBuilder()
        val printer = CSVPrinter(sb, CSVFormat.DEFAULT.withDelimiter('\t'))
        for (directive in directives) {
            printer.printRecord(*directive)
        }
        return sb.toString()
    }
}