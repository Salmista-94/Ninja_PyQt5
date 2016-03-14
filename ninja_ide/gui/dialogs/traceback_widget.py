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
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QCoreApplication


_translate = QCoreApplication.translate


class PluginErrorDialog(QDialog):
    """
    Dialog with tabs each tab is a python traceback
    """
    def __init__(self):
        super(PluginErrorDialog, self).__init__()
        self.setWindowTitle(_translate("PluginErrorDialog", "Plugin error report"))
        self.resize(525, 400)
        vbox = QVBoxLayout(self)
        label = QLabel(_translate("PluginErrorDialog", 'Some plugins have errors and were removed'))
        vbox.addWidget(label)
        self._tabs = QTabWidget()
        vbox.addWidget(self._tabs)
        hbox = QHBoxLayout()
        btnAccept = QPushButton(_translate("PluginErrorDialog", "Accept"))
        btnAccept.setMaximumWidth(100)
        hbox.addWidget(btnAccept)
        vbox.addLayout(hbox)
        #signals
        btnAccept.clicked['bool'].connect(self.close)

    def add_traceback(self, plugin_name, traceback_msg):
        traceback_widget = TracebackWidget(traceback_msg)
        self._tabs.addTab(traceback_widget, plugin_name)


class TracebackWidget(QWidget):
    """
    Represents a python traceback
    """

    def __init__(self, traceback_msg):
        super(TracebackWidget, self).__init__()
        vbox = QVBoxLayout(self)
        self._editor = QPlainTextEdit()
        vbox.addWidget(QLabel(_translate("TracebackWidget", 'Traceback')))
        vbox.addWidget(self._editor)
        self._editor.setReadOnly(True)
        self._editor.insertPlainText(traceback_msg)
