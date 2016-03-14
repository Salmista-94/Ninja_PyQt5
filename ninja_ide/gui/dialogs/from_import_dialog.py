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



from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
#from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QCoreApplication


_translate = QCoreApplication.translate


class FromImportDialog(QDialog):

    def __init__(self, fromSection, editorWidget, parent=None):
        super(FromImportDialog, self).__init__(parent, Qt.Dialog)
        self.setWindowTitle('from ... import ...')
        self._editorWidget = editorWidget
        self._fromSection = fromSection

        hbox = QHBoxLayout(self)
        hbox.addWidget(QLabel('from'))
        self._lineFrom = QLineEdit()
        self._completer = QCompleter(fromSection)
        self._lineFrom.setCompleter(self._completer)
        hbox.addWidget(self._lineFrom)
        hbox.addWidget(QLabel('import'))
        self._lineImport = QLineEdit()
        hbox.addWidget(self._lineImport)
        self._btnAdd = QPushButton(_translate("FromImportDialog", 'Add'))
        hbox.addWidget(self._btnAdd)

        self._lineImport.returnPressed.connect(self._add_import)
        self._btnAdd.clicked['bool'].connect(self._add_import)

    def _add_import(self):
        fromItem = self._lineFrom.text()
        importItem = self._lineImport.text()
        if fromItem in self._fromSection:
            cursor = self._editorWidget.document().find(fromItem)
        elif self._fromSection:
            cursor = self._editorWidget.document().find(self._fromSection[-1])
        else:
            cursor = self._editorWidget.textCursor()
            cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.EndOfLine)
        if fromItem:
            importLine = '\nfrom {0} import {1}'.format(fromItem, importItem)
        else:
            importLine = '\nimport {0}'.format(importItem)
        if self._editorWidget.document().find(
        importLine[1:]).position() == -1:
            cursor.insertText(importLine)
        self.close()
