# -*- coding: utf-8 -*-
#
# This file is part of NINJA-IDE (http://ninja-ide.org).
#
# NINJA-IDE is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# NINJA-IDE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NINJA-IDE; If not, see <http://www.gnu.org/licenses/>.



from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMessageBox

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.gui import actions


_translate = QCoreApplication.translate


class TreeResult(QTreeWidget):

    def __init__(self):
        super(TreeResult, self).__init__()
        self.setHeaderLabels((_translate("TreeResult", 'Description'), _translate("TreeResult", 'Shortcut')))
        #columns width
        self.setColumnWidth(0, 175)
        self.header().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)


class ShortcutDialog(QDialog):
    """
    Dialog to set a shortcut for an action
    this class emit the follow signals:
        shortcutChanged(QKeySequence)
    """
    shortcutChanged = pyqtSignal('QKeySequence*')

    def __init__(self, parent):
        super(ShortcutDialog, self).__init__(parent)
        self.keys = 0
        #Keyword modifiers!
        self.keyword_modifiers = (Qt.Key_Control, Qt.Key_Meta, Qt.Key_Shift,
            Qt.Key_Alt, Qt.Key_Menu)
        #main layout
        main_vbox = QVBoxLayout(self)
        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        #layout for buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton(_translate("ShortcutDialog", "Accept"))
        cancel_button = QPushButton(_translate("ShortcutDialog", "Cancel"))
        #add widgets
        main_vbox.addWidget(self.line_edit)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        main_vbox.addLayout(buttons_layout)
        self.line_edit.installEventFilter(self)
        #buttons signals
        ok_button.clicked['bool'].connect(self.save_shortcut)
        cancel_button.clicked['bool'].connect(self.close)

    def save_shortcut(self):
        self.hide()
        shortcut = QKeySequence(self.line_edit.text())
        self.shortcutChanged.emit(shortcut)

    def set_shortcut(self, txt):
        self.line_edit.setText(txt)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress:
            self.keyPressEvent(event)
            return True

        return False

    def keyPressEvent(self, evt):
        #modifier can not be used as shortcut
        if evt.key() in self.keyword_modifiers:
            return

        #save the key
        if evt.key() == Qt.Key_Backtab and evt.modifiers() & Qt.ShiftModifier:
            self.keys = Qt.Key_Tab
        else:
            self.keys = evt.key()

        if evt.modifiers() & Qt.ShiftModifier:
            self.keys += Qt.SHIFT
        if evt.modifiers() & Qt.ControlModifier:
            self.keys += Qt.CTRL
        if evt.modifiers() & Qt.AltModifier:
            self.keys += Qt.ALT
        if evt.modifiers() & Qt.MetaModifier:
            self.keys += Qt.META
        #set the keys
        self.set_shortcut(QKeySequence(self.keys).toString())


class ShortcutConfiguration(QWidget):
    """
    Dialog to manage ALL shortcuts
    """

    def __init__(self):
        super(ShortcutConfiguration, self).__init__()

        self.shortcuts_text = {
            "Duplicate": _translate("ShortcutConfiguration", "Duplicate the line/selection"),
            "Remove-line": _translate("ShortcutConfiguration", "Remove the line/selection"),
            "Move-up": _translate("ShortcutConfiguration", "Move the line/selection up"),
            "Move-down": _translate("ShortcutConfiguration", "Move the line/selection down"),
            "Close-tab": _translate("ShortcutConfiguration", "Close the current tab"),
            "New-file": _translate("ShortcutConfiguration", "Create a New tab"),
            "New-project": _translate("ShortcutConfiguration", "Create a new Project"),
            "Open-file": _translate("ShortcutConfiguration", "Open a File"),
            "Open-project": _translate("ShortcutConfiguration", "Open a Project"),
            "Save-file": _translate("ShortcutConfiguration", "Save the current file"),
            "Save-project": _translate("ShortcutConfiguration", "Save the current project opened files"),
            "Print-file": _translate("ShortcutConfiguration", "Print current file"),
            "Redo": _translate("ShortcutConfiguration", "Redo"),
            "Comment": _translate("ShortcutConfiguration", "Comment line/selection"),
            "Uncomment": _translate("ShortcutConfiguration", "Uncomment line/selection"),
            "Horizontal-line": _translate("ShortcutConfiguration", "Insert Horizontal line"),
            "Title-comment": _translate("ShortcutConfiguration", "Insert comment Title"),
            "Indent-less": _translate("ShortcutConfiguration", "Indent less"),
            "Hide-misc": _translate("ShortcutConfiguration", "Hide Misc Container"),
            "Hide-editor": _translate("ShortcutConfiguration", "Hide Editor Area"),
            "Hide-explorer": _translate("ShortcutConfiguration", "Hide Explorer"),
            "Run-file": _translate("ShortcutConfiguration", "Execute current file"),
            "Run-project": _translate("ShortcutConfiguration", "Execute current project"),
            "Debug": _translate("ShortcutConfiguration", "Debug"),
            "Switch-Focus": _translate("ShortcutConfiguration", "Switch keyboard focus"),
            "Stop-execution": _translate("ShortcutConfiguration", "Stop Execution"),
            "Hide-all": _translate("ShortcutConfiguration", "Hide all (Except Editor)"),
            "Full-screen": _translate("ShortcutConfiguration", "Full Screen"),
            "Find": _translate("ShortcutConfiguration", "Find"),
            "Find-replace": _translate("ShortcutConfiguration", "Find & Replace"),
            "Find-with-word": _translate("ShortcutConfiguration", "Find word under cursor"),
            "Find-next": _translate("ShortcutConfiguration", "Find Next"),
            "Find-previous": _translate("ShortcutConfiguration", "Find Previous"),
            "Help": _translate("ShortcutConfiguration", "Show Python Help"),
            "Split-vertical": _translate("ShortcutConfiguration", "Split Tabs Vertically"),
            "Split-horizontal": _translate("ShortcutConfiguration", "Split Tabs Horizontally"),
            "Follow-mode": _translate("ShortcutConfiguration", "Activate/Deactivate Follow Mode"),
            "Reload-file": _translate("ShortcutConfiguration", "Reload File"),
            "Jump": _translate("ShortcutConfiguration", "Jump to line"),
            "Find-in-files": _translate("ShortcutConfiguration", "Find in Files"),
            "Import": _translate("ShortcutConfiguration", "Import from everywhere"),
            "Go-to-definition": _translate("ShortcutConfiguration", "Go to definition"),
            "Complete-Declarations": _translate("ShortcutConfiguration", "Complete Declarations"),
            "Code-locator": _translate("ShortcutConfiguration", "Show Code Locator"),
            "File-Opener": _translate("ShortcutConfiguration", "Show File Opener"),
            "Navigate-back": _translate("ShortcutConfiguration", "Navigate Back"),
            "Navigate-forward": _translate("ShortcutConfiguration", "Navigate Forward"),
            "Open-recent-closed": _translate("ShortcutConfiguration", "Open recent closed file"),
            "Change-Tab": _translate("ShortcutConfiguration", "Change to the next Tab"),
            "Change-Tab-Reverse": _translate("ShortcutConfiguration", "Change to the previous Tab"),
            "Move-Tab-to-right": _translate("ShortcutConfiguration", "Move tab to right"),
            "Move-Tab-to-left": _translate("ShortcutConfiguration", "Move tab to left"),
            "Show-Code-Nav": _translate("ShortcutConfiguration", "Activate History Navigation"),
            "Show-Bookmarks-Nav": _translate("ShortcutConfiguration", "Activate Bookmarks Navigation"),
            "Show-Breakpoints-Nav": _translate("ShortcutConfiguration", "Activate Breakpoints Navigation"),
            "Show-Paste-History": _translate("ShortcutConfiguration", "Show copy/paste history"),
            "History-Copy": _translate("ShortcutConfiguration", "Copy into copy/paste history"),
            "History-Paste": _translate("ShortcutConfiguration", "Paste from copy/paste history"),
            "change-split-focus": _translate("ShortcutConfiguration", 
                "Change the keyboard focus between the current splits"),
            "Add-Bookmark-or-Breakpoint": _translate("ShortcutConfiguration", 
                "Insert Bookmark/Breakpoint"),
            "move-tab-to-next-split": _translate("ShortcutConfiguration", 
                "Move the current Tab to the next split."),
            "change-tab-visibility": _translate("ShortcutConfiguration", 
                "Show/Hide the Tabs in the Editor Area."),
            "Highlight-Word": _translate("ShortcutConfiguration", 
                "Highlight occurrences for word under cursor")
        }

        self.shortcut_dialog = ShortcutDialog(self)
        #main layout
        main_vbox = QVBoxLayout(self)
        #layout for buttons
        buttons_layout = QVBoxLayout()
        #widgets
        self.result_widget = TreeResult()
        load_defaults_button = QPushButton(_translate("ShortcutConfiguration", "Load defaults"))
        #add widgets
        main_vbox.addWidget(self.result_widget)
        buttons_layout.addWidget(load_defaults_button)
        main_vbox.addLayout(buttons_layout)
        main_vbox.addWidget(QLabel(
            _translate("ShortcutConfiguration", "The Shortcut's Text in the Menus are "
            "going to be refreshed on restart.")))
        #load data!
        self.result_widget.setColumnWidth(0, 400)
        self._load_shortcuts()
        #signals
        #open the set shortcut dialog
        self.result_widget.itemDoubleClicked['QTreeWidgetItem*', int].connect(self._open_shortcut_dialog)
        #load defaults shortcuts
        load_defaults_button.clicked['bool'].connect(self._load_defaults_shortcuts)
        #one shortcut has changed
        self.shortcut_dialog.shortcutChanged.connect(self._shortcut_changed)

    def _shortcut_changed(self, keysequence):
        """
        Validate and set a new shortcut
        """
        if self.__validate_shortcut(keysequence):
            self.result_widget.currentItem().setText(1, keysequence.toString())

    def __validate_shortcut(self, keysequence):
        """
        Validate a shortcut
        """
        if keysequence.isEmpty():
            return True

        keyname = self.result_widget.currentItem().text(0)
        keystr = keysequence

        for top_index in range(self.result_widget.topLevelItemCount()):
            top_item = self.result_widget.topLevelItem(top_index)

            if top_item.text(0) != keyname:
                itmseq = top_item.text(1)
                if keystr == itmseq:
                    val = QMessageBox.warning(self,
                            _translate("ShortcutConfiguration", 'Shortcut is already in use'),
                            _translate("ShortcutConfiguration", "Do you want to remove it?"),
                            QMessageBox.Yes, QMessageBox.No)
                    if val == QMessageBox.Yes:
                        top_item.setText(1, "")
                        return True
                    else:
                        return False
                if not itmseq:
                    continue

        return True

    def _open_shortcut_dialog(self, item, column):
        """
        Open the dialog to set a shortcut
        """
        if item.childCount():
            return

        self.shortcut_dialog.set_shortcut(
            QKeySequence(item.text(1)).toString())
        self.shortcut_dialog.exec_()

    def save(self):
        """
        Save all shortcuts to settings
        """
        settings = QSettings(resources.SETTINGS_PATH, QSettings.IniFormat)
        settings.beginGroup("shortcuts")
        for index in range(self.result_widget.topLevelItemCount()):
            item = self.result_widget.topLevelItem(index)
            shortcut_keys = item.text(1)
            shortcut_name = item.text(2)
            settings.setValue(shortcut_name, shortcut_keys)
        settings.endGroup()
        actions.Actions().update_shortcuts()

    def _load_shortcuts(self):
        for action in resources.CUSTOM_SHORTCUTS:
            shortcut_action = resources.get_shortcut(action)
            #populate the tree widget
            tree_data = [self.shortcuts_text[action],
                shortcut_action.toString(QKeySequence.NativeText), action]
            item = QTreeWidgetItem(self.result_widget, tree_data)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def _load_defaults_shortcuts(self):
        #clean custom shortcuts and UI widget
        resources.clean_custom_shortcuts()
        self.result_widget.clear()
        for name, action in list(resources.SHORTCUTS.items()):
            shortcut_action = action
            #populate the tree widget
            tree_data = [self.shortcuts_text[name],
                shortcut_action.toString(QKeySequence.NativeText), name]
            item = QTreeWidgetItem(self.result_widget, tree_data)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
