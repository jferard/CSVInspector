package com.github.jferard.csvinspector.gui

import javafx.scene.Node
import javafx.scene.control.ScrollPane
import javafx.scene.control.Tab
import org.fxmisc.richtext.CodeArea

class TabWrapper(val tab: Tab) {
    val scrollPaneContent: Node = (tab.content as ScrollPane).content
    val codeArea = scrollPaneContent as CodeArea
    var name = tab.text
    var handler = tab.userData as? FileHandler
    set(handler) {
        tab.userData = handler
        field = handler
    }

    var text: String = codeArea.text
    set(text) = codeArea.replaceText(text)
}