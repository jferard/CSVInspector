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
 */

package com.github.jferard.csvinspector.gui

import com.google.common.eventbus.EventBus
import javafx.event.EventHandler
import javafx.scene.control.Menu
import javafx.scene.control.MenuBar
import javafx.scene.control.MenuItem
import javafx.scene.control.SeparatorMenuItem
import javafx.scene.input.KeyCode
import javafx.scene.input.KeyCodeCombination
import javafx.scene.input.KeyCombination

class MenuBarProvider(private val eventBus: EventBus) {
    fun get(): MenuBar {
        val menuBar = MenuBar()
        val fileMenu = createFileMenu()
        val editMenu = createEditMenu()
        val helpMenu = createHelpMenu()
        menuBar.menus.add(fileMenu)
        menuBar.menus.add(editMenu)
        menuBar.menus.add(helpMenu)
        return menuBar
    }

    private fun createFileMenu(): Menu {
        val openCSVMenuItem =
                createItem("Open CSV", "OPEN_CSV", KeyCode.O, KeyCombination.CONTROL_DOWN)
        val openMenuItem = createItem("Open", "OPEN", KeyCode.O, KeyCombination.CONTROL_DOWN,
                KeyCodeCombination.SHIFT_DOWN)
        val saveMenuItem = createItem("Save", "SAVE", KeyCode.S, KeyCombination.CONTROL_DOWN)
        val saveAsMenuItem =
                createItem("Save as", "SAVE_AS", KeyCode.S, KeyCombination.CONTROL_DOWN,
                        KeyCombination.SHIFT_DOWN)
        val executeMenuItem = createItem("Execute", "EXECUTE", KeyCode.F5)
        val restartMenuItem = createItem("Restart interpreter", "RESTART", KeyCode.F10)
        val quitMenuItem = createItem("Quit", "QUIT", KeyCode.Q, KeyCombination.CONTROL_DOWN)
        val menuFile = Menu("File")
        menuFile.items
                .addAll(openCSVMenuItem, openMenuItem, saveMenuItem, saveAsMenuItem,
                        SeparatorMenuItem(),
                        executeMenuItem, restartMenuItem, SeparatorMenuItem(), quitMenuItem)
        return menuFile
    }

    private fun createEditMenu(): Menu {
        val menuEdit = Menu("Edit")
        val tabMenuItem =
                createItem("Add new tab", "NEW_TAB", KeyCode.T, KeyCombination.CONTROL_DOWN)
        val cutMenuItem = createItem("Cut", "CUT", KeyCode.X, KeyCombination.CONTROL_DOWN)
        val copyMenuItem = createItem("Copy", "COPY", KeyCode.C, KeyCombination.CONTROL_DOWN)
        val pasteMenuItem = createItem("Paste", "PASTE", KeyCode.V, KeyCombination.CONTROL_DOWN)
        val findMenuItem =
                createItem("Find/Replace", "FIND", KeyCode.F, KeyCombination.CONTROL_DOWN)
        menuEdit.items.addAll(tabMenuItem, SeparatorMenuItem(), cutMenuItem, SeparatorMenuItem(),
                copyMenuItem, pasteMenuItem, SeparatorMenuItem(), findMenuItem)
        return menuEdit
    }

    private fun createItem(itemText: String, itemCode: String,
                           itemKey: KeyCode?,
                           vararg modifiers: KeyCombination.Modifier): MenuItem {
        val menuItem = MenuItem(itemText)
        menuItem.onAction = EventHandler {
            eventBus.post(MenuEvent(itemCode))
        }
        if (itemKey != null) {
            menuItem.accelerator = KeyCodeCombination(itemKey, *modifiers)
        }
        return menuItem
    }

    private fun createHelpMenu(): Menu {
        val helpMenuItem = createItem("CSVInspector Help", "HELP", KeyCode.F1)
        val snippetMenu = Menu("Snippets")
        val snippet1Menu =
                createItem("Open", "SNIPPET_1", KeyCode.NUMPAD1, KeyCombination.CONTROL_DOWN)
        val snippet2Menu =
                createItem("Select", "SNIPPET_2", KeyCode.NUMPAD2, KeyCombination.CONTROL_DOWN)
        val snippet3Menu =
                createItem("GroupBy", "SNIPPET_3", KeyCode.NUMPAD3, KeyCombination.CONTROL_DOWN)
        val snippet4Menu =
                createItem("Join", "SNIPPET_4", KeyCode.NUMPAD4, KeyCombination.CONTROL_DOWN)
        val snippet5Menu = createItem("Sort/Filter", "SNIPPET_5", KeyCode.NUMPAD5,
                KeyCombination.CONTROL_DOWN)
        snippetMenu.items
                .addAll(snippet1Menu, snippet2Menu, snippet3Menu, snippet4Menu, snippet5Menu)
        val aboutMenuItem = createItem("About CSVInspector", "ABOUT", null)
        val menuHelp = Menu("Help")
        menuHelp.items.addAll(helpMenuItem, SeparatorMenuItem(), snippetMenu, SeparatorMenuItem(),
                aboutMenuItem)
        return menuHelp
    }
}