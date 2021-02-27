package com.github.jferard.csvinspector.data

import com.github.jferard.csvsniffer.MetaCSVSniffer
import com.github.jferard.javamcsv.*
import org.apache.commons.csv.CSVParser
import java.io.File
import java.io.FileInputStream

class MetaCSVUtil {
    fun guessDirectives(csvFile: File): List<List<String>> {
        csvFile.inputStream().use {
            val data = MetaCSVSniffer.create().sniff(it)
            return MetaCSVUtil().directivesFromData(data, csvFile)
        }
    }

    fun readDirectives(
            metaCSVFile: File, csvFile: File): List<List<String>> {
        val inputStream = FileInputStream(metaCSVFile)
        inputStream.use {
            val parser = MetaCSVParser.create(inputStream)
            val data = parser.parse()
            return MetaCSVUtil().directivesFromData(data, csvFile)
        }
    }

    fun directivesFromData(data: MetaCSVData,
                           csvFile: File): List<List<String>> {
        val directives: MutableList<List<String>> = fileAndCSVDirectivesFromData(data)
        val inputStream = FileInputStream(csvFile)
        val parser = CSVParser(inputStream.bufferedReader(data.encoding),
                CSVFormatHelper.getCSVFormat(data))
        parser.use {
            parser.first { rec ->
                directives.addAll(
                        (0 until rec.size()).map {
                            listOf("data", "col/$it/type",
                                    when (val description = data.getDescription(it)) {
                                        null -> "text"
                                        else -> {
                                            val out = StringBuilder()
                                            description.render(out)
                                            out.toString()
                                        }
                                    })
                        })
            }
        }
        return directives
    }

    private fun fileAndCSVDirectivesFromData(
            data: MetaCSVData): MutableList<List<String>> {
        val directives: MutableList<List<String>> = mutableListOf()
        val regex = Regex("col/\\d+/type")

        val customPrinter = object : MetaCSVPrinter {
            override fun printRecord(domain: String, key: String, value: Any) {
                val directive = listOf(domain, key, value.toString())
                if (!key.matches(regex)) {
                    directives.add(directive)
                }
            }

            override fun flush() {
                // do nothing
            }
        }
        MetaCSVRenderer(customPrinter, false).render(data)
        return directives
    }
}