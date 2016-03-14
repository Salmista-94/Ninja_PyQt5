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



import re

from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.core import settings
from ninja_ide.tools import locator
from ninja_ide.tools import ui_tools
from ninja_ide.gui.main_panel import main_container
from ninja_ide.tools.logger import NinjaLogger

logger = NinjaLogger('ninja_ide.gui.status_bar')
DEBUG = logger.debug

__statusBarInstance = None

_translate = QCoreApplication.translate

def StatusBar(*args, **kw):
    global __statusBarInstance
    if __statusBarInstance is None:
        __statusBarInstance = _s_StatusBar(*args, **kw)
    return __statusBarInstance


class _s_StatusBar(QStatusBar):

    def __init__(self, parent=None):
        super(_s_StatusBar, self).__init__(parent)

        self._widgetStatus = QWidget()
        vbox = QVBoxLayout(self._widgetStatus)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        #Search Layout
        self._searchWidget = SearchWidget(self)
        vbox.addWidget(self._searchWidget)
        #Replace Layout
        self._replaceWidget = ReplaceWidget(self)
        vbox.addWidget(self._replaceWidget)
        self._replaceWidget.setVisible(False)
        #Code Locator
        self._codeLocator = locator.CodeLocatorWidget(self)
        vbox.addWidget(self._codeLocator)
        self._codeLocator.setVisible(False)
        #File system completer
        self._fileSystemOpener = FileSystemOpener()
        vbox.addWidget(self._fileSystemOpener)
        self._fileSystemOpener.setVisible(False)

        self.addWidget(self._widgetStatus)

        self.messageChanged[str].connect(self.message_end)
        self._replaceWidget._btnCloseReplace.clicked['bool'].connect(lambda: self._replaceWidget.setVisible(False))
        self._replaceWidget._btnReplace.clicked['bool'].connect(self.replace)
        self._replaceWidget._btnReplaceAll.clicked['bool'].connect(self.replace_all)
        self._replaceWidget._btnReplaceSelection.clicked['bool'].connect(self.replace_selected)
        self._fileSystemOpener.btnClose.clicked['bool'].connect(self.hide_status)
        self._fileSystemOpener.requestHide.connect(self.hide_status)

    def handle_tab_changed(self, new_tab):
        """
        Re-run search if tab changed, we use the find of search widget because
        we want the widget to be updated.
        """
        editor = main_container.MainContainer().get_actual_editor()
        if self._searchWidget.isVisible():
            self._searchWidget.find_matches(editor)
        if editor:
            try:
                editor.textChanged.disconnect(self._notify_editor_changed)
            except Exception:
                pass# ignorar la desconexión
            editor.textChanged.connect(self._notify_editor_changed)

    def _notify_editor_changed(self):
        """
        Lets search widget know that the editor contents changed and find
        needs to be re-run
        """
        if self._searchWidget.isVisible():
            editor = main_container.MainContainer().get_actual_editor()
            self._searchWidget.contents_changed(editor)

    def explore_code(self):
        self._codeLocator.explore_code()

    def explore_file_code(self, path):
        self._codeLocator.explore_file_code(path)

    def show(self):
        self.clearMessage()
        QStatusBar.show(self)
        editor = main_container.MainContainer().get_actual_editor()
        if editor and editor.textCursor().hasSelection():
            text = editor.textCursor().selectedText()
            self._searchWidget._line.setText(text)
            self._searchWidget.find_matches(editor, True)
        if self._widgetStatus.isVisible():
            self._searchWidget._line.setFocus()
            self._searchWidget._line.selectAll()

    def show_replace(self):
        self.clearMessage()
        self.show()
        editor = main_container.MainContainer().get_actual_editor()
        if editor:
            if editor.textCursor().hasSelection():
                word = editor.textCursor().selectedText()
                self._searchWidget._line.setText(word)
        self._replaceWidget.setVisible(True)

    def show_with_word(self):
        self.clearMessage()
        editor = main_container.MainContainer().get_actual_editor()
        if editor:
            word = editor._text_under_cursor()
            self._searchWidget._line.setText(word)
            editor = main_container.MainContainer().get_actual_editor()
            editor.moveCursor(QTextCursor.WordLeft)
            self._searchWidget.find_matches(editor)
            self.show()

    def show_locator(self):
        if not self._codeLocator.isVisible():
            self.clearMessage()
            self._searchWidget.setVisible(False)
            self.show()
            self._codeLocator.setVisible(True)
            self._codeLocator._completer.setFocus()
            self._codeLocator.show_suggestions()

    def show_file_opener(self):
        self.clearMessage()
        self._searchWidget.setVisible(False)
        self._fileSystemOpener.setVisible(True)
        self.show()
        self._fileSystemOpener.pathLine.setFocus()

    def hide_status(self):
        self._searchWidget._checkSensitive.setCheckState(Qt.Unchecked)
        self._searchWidget._checkWholeWord.setCheckState(Qt.Unchecked)
        self.hide()
        self._searchWidget.setVisible(True)
        self._replaceWidget.setVisible(False)
        self._codeLocator.setVisible(False)
        self._fileSystemOpener.setVisible(False)
        widget = main_container.MainContainer().get_actual_widget()
        if widget:
            widget.setFocus()

    def replace(self):
        s = 0 if not self._searchWidget._checkSensitive.isChecked() \
            else QTextDocument.FindCaseSensitively
        w = 0 if not self._searchWidget._checkWholeWord.isChecked() \
            else QTextDocument.FindWholeWords
        flags = 0 + s + w
        editor = main_container.MainContainer().get_actual_editor()
        if editor:
            editor.replace_match(
                self._searchWidget._line.text(),
                self._replaceWidget._lineReplace.text(), flags)
        if not editor.textCursor().hasSelection():
            self.find()

    def replace_selected(self):
        self.replace_all(True)

    def replace_all(self, selected=False):
        s = 0 if not self._searchWidget._checkSensitive.isChecked() \
            else QTextDocument.FindCaseSensitively
        w = 0 if not self._searchWidget._checkWholeWord.isChecked() \
            else QTextDocument.FindWholeWords
        flags = 0 + s + w
        editor = main_container.MainContainer().get_actual_editor()
        if editor:
            editor.replace_match(self._searchWidget._line.text(),
                                 self._replaceWidget._lineReplace.text(),
                                 flags, True, selected)

    def find(self):
        s = 0 if not self._searchWidget._checkSensitive.isChecked() \
            else QTextDocument.FindCaseSensitively
        w = 0 if not self._searchWidget._checkWholeWord.isChecked() \
            else QTextDocument.FindWholeWords
        flags = s + w
        editor = main_container.MainContainer().get_actual_editor()
        if editor:
            editor.find_match(self._searchWidget._line.text(), flags)

    def find_next(self):
        s = 0 if not self._searchWidget._checkSensitive.isChecked() \
            else QTextDocument.FindCaseSensitively
        w = 0 if not self._searchWidget._checkWholeWord.isChecked() \
            else QTextDocument.FindWholeWords
        flags = 0 + s + w
        editor = main_container.MainContainer().get_actual_editor()
        if editor:
            editor.find_match(self._searchWidget._line.text(), flags, True)

    def find_previous(self):
        s = 0 if not self._searchWidget._checkSensitive.isChecked() \
            else QTextDocument.FindCaseSensitively
        w = 0 if not self._searchWidget._checkWholeWord.isChecked() \
            else QTextDocument.FindWholeWords
        flags = 1 + s + w
        editor = main_container.MainContainer().get_actual_editor()
        if editor:
            editor.find_match(self._searchWidget._line.text(), flags, True)

    def showMessage(self, message, timeout):
        if settings.SHOW_STATUS_NOTIFICATIONS:
            self._widgetStatus.hide()
            self._replaceWidget.setVisible(False)
            self.show()
            QStatusBar.showMessage(self, message, timeout)

    def message_end(self, message):
        if message == '':
            self.hide()
            QStatusBar.clearMessage(self)
            self._widgetStatus.show()


class SearchWidget(QWidget):

    def __init__(self, parent):
        super(SearchWidget, self).__init__(parent)
        self._parent = parent
        hSearch = QHBoxLayout(self)
        hSearch.setContentsMargins(0, 0, 0, 0)
        self._checkSensitive = QCheckBox(_translate("SearchWidget", "Respect Case Sensitive"))
        self._checkWholeWord = QCheckBox(_translate("SearchWidget", "Find Whole Words"))
        self._line = TextLine(self)
        self._line.setMinimumWidth(250)
        self._btnClose = QPushButton(
            self.style().standardIcon(QStyle.SP_DialogCloseButton), '')
        self._btnFind = QPushButton(QIcon(resources.IMAGES['find']), '')
        self.btnPrevious = QPushButton(
            self.style().standardIcon(QStyle.SP_ArrowLeft), '')
        self.btnPrevious.setToolTip(_translate("SearchWidget", "Press %s") %
                                    resources.get_shortcut("Find-previous").toString(
                                        QKeySequence.NativeText))
        self.btnNext = QPushButton(
            self.style().standardIcon(QStyle.SP_ArrowRight), '')
        self.btnNext.setToolTip(_translate("SearchWidget", "Press %s") %
                                resources.get_shortcut("Find-next").toString(
                                    QKeySequence.NativeText))
        hSearch.addWidget(self._btnClose)
        hSearch.addWidget(self._line)
        hSearch.addWidget(self._btnFind)
        hSearch.addWidget(self.btnPrevious)
        hSearch.addWidget(self.btnNext)
        hSearch.addWidget(self._checkSensitive)
        hSearch.addWidget(self._checkWholeWord)

        self.totalMatches = 0
        self.index = 0
        self._line.counter.update_count(self.index, self.totalMatches)

        self._btnClose.clicked['bool'].connect(self._parent.hide_status)
        self._btnFind.clicked['bool'].connect(self.find_next)
        self.btnNext.clicked['bool'].connect(self.find_next)
        self.btnPrevious.clicked['bool'].connect(self.find_previous)
        self._checkSensitive.stateChanged[int].connect(self._checks_state_changed)
        self._checkWholeWord.stateChanged[int].connect(self._checks_state_changed)

    def _checks_state_changed(self):
        editor = main_container.MainContainer().get_actual_editor()
        editor.moveCursor(QTextCursor.Start)
        self.find_matches(editor)

    def contents_changed(self, editor):
        #TODO: Find where the cursor is when finding to position the index
        current_index = self.find_matches(editor, True)
        if self.totalMatches >= current_index:
            self.index = current_index
        self._line.counter.update_count(self.index, self.totalMatches)

    def find_next(self):
        self._parent.find_next()
        if self.totalMatches > 0 and self.index < self.totalMatches:
            self.index += 1
        elif self.totalMatches > 0:
            self.index = 1
        self._line.counter.update_count(self.index, self.totalMatches)

    def find_previous(self):
        self._parent.find_previous()
        if self.totalMatches > 0 and self.index > 1:
            self.index -= 1
        elif self.totalMatches > 0:
            self.index = self.totalMatches
            editor = main_container.MainContainer().get_actual_editor()
            editor.moveCursor(QTextCursor.End)
            self._parent.find_previous()
        self._line.counter.update_count(self.index, self.totalMatches)

    def find_matches(self, editor, in_place=False):
        if editor is None:
            return
        text = editor.toPlainText()
        search = self._line.text()
        hasSearch = len(search) > 0
        current_index = 0
        if self._checkWholeWord.isChecked():
            pattern = r'\b%s\b' % search
            temp_text = ' '.join(re.findall(pattern, text, re.IGNORECASE))
            text = temp_text if temp_text != '' else text
        if self._checkSensitive.isChecked():
            self.totalMatches = text.count(search)
        else:
            self.totalMatches = text.lower().count(search.lower())
        if hasSearch and self.totalMatches > 0:
            cursor = editor.textCursor()
            cursor_position = cursor.position()

            cursor.movePosition(QTextCursor.WordLeft)
            cursor.movePosition(QTextCursor.Start,
                                QTextCursor.KeepAnchor)
            current_index = text[:cursor_position].count(search)
            text = cursor.selectedText()
            if current_index <= self.totalMatches:
                self.index = current_index
            else:
                self.index = text.count(search) + 1
        else:
            self.index = 0
            self.totalMatches = 0
        self._line.counter.update_count(self.index, self.totalMatches,
                                        hasSearch)
        if hasSearch and not in_place:
            self._parent.find()
        return current_index


class ReplaceWidget(QWidget):

    def __init__(self, parent):
        super(ReplaceWidget, self).__init__(parent)
        hReplace = QHBoxLayout(self)
        hReplace.setContentsMargins(0, 0, 0, 0)
        self._lineReplace = QLineEdit()
        self._lineReplace.setMinimumWidth(250)
        self._btnCloseReplace = QPushButton(
            self.style().standardIcon(QStyle.SP_DialogCloseButton), '')
        self._btnReplace = QPushButton(_translate("ReplaceWidget", "Replace"))
        self._btnReplaceAll = QPushButton(_translate("ReplaceWidget", "Replace All"))
        self._btnReplaceSelection = QPushButton(
            _translate("ReplaceWidget", "Replace Selection"))
        hReplace.addWidget(self._btnCloseReplace)
        hReplace.addWidget(self._lineReplace)
        hReplace.addWidget(self._btnReplace)
        hReplace.addWidget(self._btnReplaceAll)
        hReplace.addWidget(self._btnReplaceSelection)


class TextLine(QLineEdit):

    def __init__(self, parent):
        super(TextLine, self).__init__(parent)
        self._parent = parent
        self.counter = ui_tools.LineEditCount(self)

    def keyPressEvent(self, event):
        editor = main_container.MainContainer().get_actual_editor()
        if editor is None:
            super(TextLine, self).keyPressEvent(event)
            return
        if editor and event.key() in \
           (Qt.Key_Enter, Qt.Key_Return):
            self._parent.find_next()
            return
        super(TextLine, self).keyPressEvent(event)
        if int(event.key()) in range(32, 162) or \
           event.key() == Qt.Key_Backspace:
            has_replace = self._parent._parent._replaceWidget.isVisible()
            if not has_replace:
                self._parent.find_matches(editor)


class FileSystemOpener(QWidget):
    requestHide = pyqtSignal()
    def __init__(self):
        super(FileSystemOpener, self).__init__()
        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.btnClose = QPushButton(
            self.style().standardIcon(QStyle.SP_DialogCloseButton), '')
        self.completer = QCompleter(self)
        self.pathLine = ui_tools.LineEditTabCompleter(self.completer)
        fileModel = QFileSystemModel(self.completer)
        fileModel.setRootPath("")
        self.completer.setModel(fileModel)
        self.pathLine.setCompleter(self.completer)
        self.btnOpen = QPushButton(
            self.style().standardIcon(QStyle.SP_ArrowRight), 'Open!')
        hbox.addWidget(self.btnClose)
        hbox.addWidget(QLabel(_translate("FileSystemOpener", "Path:")))
        hbox.addWidget(self.pathLine)
        hbox.addWidget(self.btnOpen)

        self.pathLine.returnPressed.connect(self._open_file)
        self.btnOpen.clicked['bool'].connect(self._open_file)

    def _open_file(self):
        path = self.pathLine.text()
        main_container.MainContainer().open_file(path)
        self.requestHide.emit()

    def showEvent(self, event):
        super(FileSystemOpener, self).showEvent(event)
        self.pathLine.selectAll()
