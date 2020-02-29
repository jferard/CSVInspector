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
        val loadMenuItem = createItem("Open", "OPEN", KeyCode.O, KeyCombination.CONTROL_DOWN)
        val saveMenuItem = createItem("Save", "SAVE", KeyCode.S, KeyCombination.CONTROL_DOWN)
        val saveAsMenuItem =
                createItem("Save as", "SAVE_AS", KeyCode.S, KeyCombination.CONTROL_DOWN,
                        KeyCombination.SHIFT_DOWN)
        val executeMenuItem = createItem("Execute", "EXECUTE", KeyCode.F5)
        val quitMenuItem = createItem("Quit", "QUIT", KeyCode.Q, KeyCombination.CONTROL_DOWN)
        val menuFile = Menu("File")
        menuFile.items
                .addAll(loadMenuItem, saveMenuItem, saveAsMenuItem, executeMenuItem, quitMenuItem)
        return menuFile
    }

    private fun createEditMenu(): Menu {
        val menuEdit = Menu("Edit")
        val cutMenuItem = createItem("Cut", "CUT", KeyCode.X, KeyCombination.CONTROL_DOWN)
        val copyMenuItem = createItem("Copy", "COPY", KeyCode.C, KeyCombination.CONTROL_DOWN)
        val pasteMenuItem = createItem("Paste", "PASTE", KeyCode.V, KeyCombination.CONTROL_DOWN)
        menuEdit.items.addAll(cutMenuItem, copyMenuItem, pasteMenuItem)
        return menuEdit
    }

    private fun createItem(itemText: String, itemCode: String,
                           itemKey: KeyCode,
                           vararg modifiers: KeyCombination.Modifier): MenuItem {
        val menuItem = MenuItem(itemText)
        menuItem.onAction = EventHandler {
            eventBus.post(MenuEvent(itemCode))
        }
        menuItem.accelerator = KeyCodeCombination(itemKey, *modifiers)
        return menuItem
    }

    private fun createHelpMenu(): Menu {
        val menuHelp = Menu("Help")
        return menuHelp
    }
}