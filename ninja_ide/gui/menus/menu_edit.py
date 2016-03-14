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


from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QTextCursor
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.core import settings
from ninja_ide.gui.main_panel import main_container
from ninja_ide.gui.misc import misc_container
from ninja_ide.gui import status_bar
from ninja_ide.gui.dialogs import preferences


_translate = QCoreApplication.translate


class MenuEdit(QObject):

    def __init__(self, menuEdit, toolbar):
        super(MenuEdit, self).__init__()

        undoAction = menuEdit.addAction(QIcon(resources.IMAGES['undo']),
            (_translate("MenuEdit", "Undo (%s+Z)") % settings.OS_KEY))
        redoAction = menuEdit.addAction(QIcon(resources.IMAGES['redo']),
            (_translate("MenuEdit", "Redo (%s)") % resources.get_shortcut("Redo").toString(
                    QKeySequence.NativeText)))
        cutAction = menuEdit.addAction(QIcon(resources.IMAGES['cut']),
            (_translate("MenuEdit", "&Cut (%s+X)") % settings.OS_KEY))
        copyAction = menuEdit.addAction(QIcon(resources.IMAGES['copy']),
            (_translate("MenuEdit", "&Copy (%s+C)") % settings.OS_KEY))
        pasteAction = menuEdit.addAction(QIcon(resources.IMAGES['paste']),
            (_translate("MenuEdit", "&Paste (%s+V)") % settings.OS_KEY))
        menuEdit.addSeparator()
        findAction = menuEdit.addAction(QIcon(resources.IMAGES['find']),
            (_translate("MenuEdit", "Find (%s)") % resources.get_shortcut("Find").toString(
                    QKeySequence.NativeText)))
        findReplaceAction = menuEdit.addAction(
            QIcon(resources.IMAGES['findReplace']),
            (_translate("MenuEdit", "Find/Replace (%s)") %
                resources.get_shortcut("Find-replace").toString(
                    QKeySequence.NativeText)))
        findWithWordAction = menuEdit.addAction(
            (_translate("MenuEdit", "Find using word under cursor (%s)") %
                resources.get_shortcut("Find-with-word").toString(
                    QKeySequence.NativeText)))
        findInFilesAction = menuEdit.addAction(QIcon(resources.IMAGES['find']),
            (_translate("MenuEdit", "Find in Files (%s)") %
                resources.get_shortcut("Find-in-files").toString(
                    QKeySequence.NativeText)))
        locatorAction = menuEdit.addAction(QIcon(resources.IMAGES['locator']),
            (_translate("MenuEdit", "Code Locator (%s)") %
                resources.get_shortcut("Code-locator").toString(
                    QKeySequence.NativeText)))
        menuEdit.addSeparator()
        upperAction = menuEdit.addAction(
            _translate("MenuEdit", "Convert selected Text to: UPPER"))
        lowerAction = menuEdit.addAction(
            _translate("MenuEdit", "Convert selected Text to: lower"))
        titleAction = menuEdit.addAction(
            _translate("MenuEdit", "Convert selected Text to: Title Word"))
        menuEdit.addSeparator()
        prefAction = menuEdit.addAction(QIcon(resources.IMAGES['pref']),
            _translate("MenuEdit", "Preference&s"))

        self.toolbar_items = {
            'undo': undoAction,
            'redo': redoAction,
            'cut': cutAction,
            'copy': copyAction,
            'paste': pasteAction,
            'find': findAction,
            'find-replace': findReplaceAction,
            'find-files': findInFilesAction,
            'code-locator': locatorAction}

        cutAction.triggered.connect(self._editor_cut)
        copyAction.triggered.connect(self._editor_copy)
        pasteAction.triggered.connect(self._editor_paste)
        redoAction.triggered.connect(self._editor_redo)
        undoAction.triggered.connect(self._editor_undo)
        upperAction.triggered.connect(self._editor_upper)
        lowerAction.triggered.connect(self._editor_lower)
        titleAction.triggered.connect(self._editor_title)
        findAction.triggered.connect(status_bar.StatusBar().show)
        findWithWordAction.triggered.connect(status_bar.StatusBar().show_with_word)
        findReplaceAction.triggered.connect(status_bar.StatusBar().show_replace)
        findInFilesAction.triggered.connect(self._show_find_in_files)
        locatorAction.triggered.connect(status_bar.StatusBar().show_locator)
        prefAction.triggered.connect(self._show_preferences)

    def _editor_upper(self):
        editorWidget = main_container.MainContainer().get_actual_editor()
        if editorWidget:
            editorWidget.textCursor().beginEditBlock()
            if editorWidget.textCursor().hasSelection():
                text = editorWidget.textCursor().selectedText().upper()
            else:
                text = editorWidget._text_under_cursor().upper()
                editorWidget.moveCursor(QTextCursor.StartOfWord)
                editorWidget.moveCursor(QTextCursor.EndOfWord,
                    QTextCursor.KeepAnchor)
            editorWidget.textCursor().insertText(text)
            editorWidget.textCursor().endEditBlock()

    def _editor_lower(self):
        editorWidget = main_container.MainContainer().get_actual_editor()
        if editorWidget:
            editorWidget.textCursor().beginEditBlock()
            if editorWidget.textCursor().hasSelection():
                text = editorWidget.textCursor().selectedText().lower()
            else:
                text = editorWidget._text_under_cursor().lower()
                editorWidget.moveCursor(QTextCursor.StartOfWord)
                editorWidget.moveCursor(QTextCursor.EndOfWord,
                    QTextCursor.KeepAnchor)
            editorWidget.textCursor().insertText(text)
            editorWidget.textCursor().endEditBlock()

    def _editor_title(self):
        editorWidget = main_container.MainContainer().get_actual_editor()
        if editorWidget:
            editorWidget.textCursor().beginEditBlock()
            if editorWidget.textCursor().hasSelection():
                text = editorWidget.textCursor().selectedText().title()
            else:
                text = editorWidget._text_under_cursor().title()
                editorWidget.moveCursor(QTextCursor.StartOfWord)
                editorWidget.moveCursor(QTextCursor.EndOfWord,
                    QTextCursor.KeepAnchor)
            editorWidget.textCursor().insertText(text)
            editorWidget.textCursor().endEditBlock()

    def _editor_cut(self):
        editorWidget = main_container.MainContainer().get_actual_editor()
        if editorWidget:
            editorWidget.cut()

    def _editor_copy(self):
        editorWidget = main_container.MainContainer().get_actual_editor()
        if editorWidget:
            editorWidget.copy()

    def _editor_paste(self):
        editorWidget = main_container.MainContainer().get_actual_editor()
        if editorWidget:
            editorWidget.paste()

    def _editor_redo(self):
        editorWidget = main_container.MainContainer().get_actual_editor()
        if editorWidget:
            editorWidget.redo()

    def _editor_undo(self):
        editorWidget = main_container.MainContainer().get_actual_editor()
        if editorWidget:
            editorWidget.undo()

    def _show_preferences(self):
        pref = preferences.PreferencesWidget(main_container.MainContainer())
        pref.show()

    def _show_find_in_files(self):
        misc_container.MiscContainer().show_find_in_files_widget()
