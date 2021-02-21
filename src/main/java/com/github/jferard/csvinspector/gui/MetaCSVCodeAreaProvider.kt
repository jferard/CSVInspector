package com.github.jferard.csvinspector.gui

import org.fxmisc.richtext.CodeArea


class MetaCSVCodeAreaProvider {
    fun get(): CodeArea {
        val codeArea = CodeArea()
        codeArea.isWrapText = true
        val resource = CSVInspectorGUI::class.java.getResource("/metacsv.css")
        codeArea.stylesheets
                .add(resource.toExternalForm())
        return codeArea
    }
}
