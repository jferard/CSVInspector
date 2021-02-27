/*
 * CSVInspector - A graphical interactive tool to inspect and process CSV files.
 *     Copyright (C) 2020 J. Férard <https://github.com/jferard>
 *
 * This file is part of CSVInspector.
 *
 * CSVInspector is free software: you can redistribute it and/or modify it under the
 * terms of the GNU General Public License as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option) any later
 * version.
 *
 * CSVInspector is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE. See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program. If not, see <http://www.gnu.org/licenses/>.
 *
 * BASED ON:
 * https://github.com/FXMisc/RichTextFX/blob/master/richtextfx-demos/src/main/java/org/fxmisc/richtext/demo/JavaKeywordsDemo.java
 */
package com.github.jferard.csvinspector.gui

import javafx.application.Platform
import javafx.scene.input.KeyCode
import javafx.scene.input.KeyEvent
import org.fxmisc.richtext.CodeArea
import org.fxmisc.richtext.LineNumberFactory
import org.fxmisc.richtext.NavigationActions
import org.fxmisc.richtext.model.StyleSpans
import org.fxmisc.richtext.model.StyleSpansBuilder
import java.time.Duration
import java.util.regex.Pattern

class CodeAreaProvider {
    fun get(): CodeArea {
        val codeArea = object: CodeArea() {
            override fun paragraphStart(selectionPolicy: NavigationActions.SelectionPolicy?) {
                println("move up")
            }
            override fun nextChar(selectionPolicy: NavigationActions.SelectionPolicy) {
                println("move")
            }
        }
        codeArea.paragraphGraphicFactory = LineNumberFactory.get(codeArea)
        val pattern = getPattern()
        codeArea.multiPlainChanges()
                .successionEnds(Duration.ofMillis(500))
                .subscribe {
                    codeArea.setStyleSpans(0, computeHighlighting(codeArea.text, pattern))
                }

        val whiteSpace = Pattern.compile("^\\s+")
        codeArea.addEventHandler(
                KeyEvent.KEY_PRESSED) {
            if (it.code == KeyCode.ENTER) {
                val caretPosition = codeArea.caretPosition
                val currentParagraph = codeArea.currentParagraph
                val m0 = whiteSpace
                        .matcher(codeArea.getParagraph(currentParagraph - 1).segments[0])
                if (m0.find()) {
                    Platform.runLater { codeArea.insertText(caretPosition, m0.group()) }
                }
            }
        }
        codeArea.isWrapText = true
        val cssResource = CSVInspectorGUI::class.java.getResource("/python.css")
        codeArea.stylesheets
                .add(cssResource.toExternalForm())
        return codeArea
    }

    private fun computeHighlighting(
            text: String,
            pattern: Pattern): StyleSpans<Collection<String?>> {
        val matcher = pattern.matcher(text)
        var lastKwEnd = 0
        val spansBuilder =
                StyleSpansBuilder<Collection<String?>>()
        while (matcher.find()) {
            val styleClass =
                    (when {
                        matcher.group("KEYWORD") != null -> "keyword"
                        matcher.group("PAREN") != null -> "paren"
                        matcher.group("BRACE") != null -> "brace"
                        matcher.group("BRACKET") != null -> "bracket"
                        matcher.group("SEMICOLON") != null -> "semicolon"
                        matcher.group("STRING") != null -> "string"
                        matcher.group("COMMENT") != null -> "comment"
                        matcher.group("OPERATOR") != null -> "operator"
                        else -> null
                    })!! /* never happens */
            spansBuilder.add(emptyList<String>(), matcher.start() - lastKwEnd)
            spansBuilder.add(setOf<String?>(styleClass), matcher.end() - matcher.start())
            lastKwEnd = matcher.end()
        }
        spansBuilder.add(emptyList<String>(), text.length - lastKwEnd)
        return spansBuilder.create()
    }

    private fun getPattern(): Pattern {
        // >>> import keyword
        // >>> keyword.kwlist
        val KEYWORDS =
                arrayOf("False", "None", "True", "and", "as", "assert", "break", "class",
                        "continue", "def", "del", "elif", "else", "except", "finally", "for",
                        "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
                        "not",
                        "or", "pass", "raise", "return", "try", "while", "with", "yield")
        val KEYWORD_PATTERN = """\b(${KEYWORDS.joinToString("|")})\b"""
        val PAREN_PATTERN = "\\(|\\)"
        val BRACE_PATTERN = "\\{|\\}"
        val BRACKET_PATTERN = "\\[|\\]"
        val SEMICOLON_PATTERN = "\\;"
        val STRING_PATTERN =
                "\"([^\"\\\\]|\\\\.)*\"" + "|" + "'([^\'\\\\]|\\\\.)*'" + "|" + "\"\"\"(.|\\R)*?\"\"\"" + "|" + "'''(.|\\R)*?'''"
        val COMMENT_PATTERN = "#[^\\n]*"
        return Pattern.compile(
                "(?<KEYWORD>" + KEYWORD_PATTERN + ")" + "|(?<PAREN>" + PAREN_PATTERN + ")" +
                        "|(?<BRACE>" + BRACE_PATTERN + ")" + "|(?<BRACKET>" + BRACKET_PATTERN + ")" +
                        "|(?<SEMICOLON>" + SEMICOLON_PATTERN + ")" + "|(?<STRING>" + STRING_PATTERN +
                        ")" + "|(?<COMMENT>" + COMMENT_PATTERN + ")")
    }
}