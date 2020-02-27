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
        val loadMenuItem = MenuItem("Load");
        loadMenuItem.onAction = EventHandler {
            eventBus.post(MenuEvent("LOAD"))
        }
        val saveMenuItem = MenuItem("Save");
        saveMenuItem.onAction = EventHandler {
            eventBus.post(MenuEvent("SAVE"))
        }
        val executeMenuItem = MenuItem("Execute");
        executeMenuItem.onAction = EventHandler {
            eventBus.post(MenuEvent("EXECUTE"))
        }
        val quitMenuItem = MenuItem("Quit");
        quitMenuItem.onAction = EventHandler {
            eventBus.post(MenuEvent("QUIT"))
        }
        val menuFile = Menu("File")
        menuFile.items.add(loadMenuItem)
        menuFile.items.add(saveMenuItem)
        menuFile.items.add(executeMenuItem)
        menuFile.items.add(quitMenuItem)
        return menuFile
    }

    private fun createEditMenu(): Menu {
        val menuEdit = Menu("Edit")
        return menuEdit
    }

    private fun createHelpMenu(): Menu {
        val menuHelp = Menu("Help")
        return menuHelp
    }
}