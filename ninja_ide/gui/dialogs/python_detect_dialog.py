# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
#from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.core import settings


_translate = QCoreApplication.translate


class PythonDetectDialog(QDialog):

    def __init__(self, suggested, parent=None):
        super(PythonDetectDialog, self).__init__(parent, Qt.Dialog)
        self.setMaximumSize(QSize(0, 0))
        self.setWindowTitle("Configure Python Path")

        vbox = QVBoxLayout(self)

        lblMessage = QLabel(_translate("PythonDetectDialog", "We have detected that you are using " +
            "Windows,\nplease choose the proper " +
            "Python application for you:"))
        vbox.addWidget(lblMessage)

        self.listPaths = QListWidget()
        self.listPaths.setSelectionMode(QListWidget.SingleSelection)
        vbox.addWidget(self.listPaths)

        hbox = QHBoxLayout()
        hbox.addSpacerItem(QSpacerItem(1, 0, QSizePolicy.Expanding))
        btnCancel = QPushButton(_translate("PythonDetectDialog", "Cancel"))
        btnAccept = QPushButton(_translate("PythonDetectDialog", "Accept"))
        hbox.addWidget(btnCancel)
        hbox.addWidget(btnAccept)
        vbox.addLayout(hbox)

        btnAccept.clicked['bool'].connect(self._set_python_path)
        btnCancel.clicked['bool'].connect(self.close)

        for path in suggested:
            self.listPaths.addItem(path)
        self.listPaths.setCurrentRow(0)

    def _set_python_path(self):
        python_path = self.listPaths.currentItem().text()

        qsettings = QSettings(resources.SETTINGS_PATH, QSettings.IniFormat)
        settings.PYTHON_PATH = python_path
        settings.PYTHON_PATH_CONFIGURED_BY_USER = True
        qsettings.setValue('preferences/execution/pythonPath', python_path)
        qsettings.setValue('preferences/execution/pythonPathConfigured', True)
        self.close()