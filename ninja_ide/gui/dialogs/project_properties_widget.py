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



import os
import sys

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtWidgets import QDirModel
from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QCheckBox
#from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.core import file_manager
from ninja_ide.core import settings
from ninja_ide.tools import json_manager
from ninja_ide.tools import ui_tools


from ninja_ide.tools.logger import NinjaLogger
logger = NinjaLogger('ninja_ide.gui.dialogs.project_properties_widget')
DEBUG = logger.debug


_translate = QCoreApplication.translate


class ProjectProperties(QDialog):

    def __init__(self, item, parent=None):
        super(ProjectProperties, self).__init__(parent, Qt.Dialog)
        self._item = item
        self.setWindowTitle(_translate("ProjectProperties", "Project Properties"))
        vbox = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.projectData = ProjectData(self)
        self.projectExecution = ProjectExecution(self)
        self.projectMetadata = ProjectMetadata(self)
        self.tab_widget.addTab(self.projectData, _translate("ProjectProperties", "Project Data"))
        self.tab_widget.addTab(self.projectExecution,
            _translate("ProjectProperties", "Project Execution"))
        self.tab_widget.addTab(self.projectMetadata,
            _translate("ProjectProperties", "Project Metadata"))

        vbox.addWidget(self.tab_widget)
        self.btnSave = QPushButton(_translate("ProjectProperties", "Save"))
        self.btnCancel = QPushButton(_translate("ProjectProperties", "Cancel"))
        hbox = QHBoxLayout()
        hbox.addWidget(self.btnCancel)
        hbox.addWidget(self.btnSave)

        vbox.addLayout(hbox)

        self.btnCancel.clicked['bool'].connect(self.close)
        self.btnSave.clicked['bool'].connect(self.save_properties)

    def save_properties(self):
        if self.projectData.name.text().strip() == '':
            QMessageBox.critical(self, _translate("ProjectProperties", "Properties Invalid"),
                _translate("ProjectProperties", "The Project must have a name."))
            return

        tempName = self._item.name
        self._item.name = self.projectData.name.text()
        self._item.description = self.projectData.description.toPlainText()
        self._item.license = self.projectData.cboLicense.currentText()
        self._item.mainFile = self.projectExecution.path.text()
        self._item.url = self.projectData.url.text()
        self._item.projectType = self.projectData.txtType.text()
        # FIXME
        self._item.pythonPath = self.projectExecution.txtPythonPath.text()
        self._item.PYTHONPATH = self.projectExecution.PYTHONPATH.toPlainText()
        self._item.additional_builtins = [e for e in self.projectExecution.additional_builtins.text().split(' ') if e]
        self._item.preExecScript = self.projectExecution.txtPreExec.text()
        self._item.postExecScript = self.projectExecution.txtPostExec.text()
        self._item.programParams = self.projectExecution.txtParams.text()
        self._item.venv = self.projectExecution.txtVenvPath.text()
        extensions = self.projectData.txtExtensions.text().split(', ')
        self._item.extensions = tuple(extensions)
        self._item.indentation = self.projectData.spinIndentation.value()
        self._item.useTabs = self.projectData.checkUseTabs.isChecked()
        related = self.projectMetadata.txt_projects.toPlainText()
        related = [path for path in related.split('\n') if path != '']
        self._item.related_projects = related
        #save project properties
        project = {}
        project['name'] = self._item.name
        project['description'] = self._item.description
        project['url'] = self._item.url
        project['license'] = self._item.license
        project['mainFile'] = self._item.mainFile
        project['project-type'] = self._item.projectType
        project['supported-extensions'] = self._item.extensions
        project['indentation'] = self._item.indentation
        project['use-tabs'] = self._item.useTabs
        project['pythonPath'] = self._item.pythonPath  # FIXME
        project['PYTHONPATH'] = self._item.PYTHONPATH
        project['additional_builtins'] = self._item.additional_builtins
        project['preExecScript'] = self._item.preExecScript
        project['postExecScript'] = self._item.postExecScript
        project['venv'] = self._item.venv
        project['programParams'] = self._item.programParams
        project['relatedProjects'] = self._item.related_projects
        if tempName != self._item.name and \
            file_manager.file_exists(self._item.path, tempName + '.nja'):
            file_manager.delete_file(self._item.path, tempName + '.nja')
        json_manager.create_ninja_project(
            self._item.path, self._item.name, project)
        self._item.setText(0, self._item.name)
        self._item.setToolTip(0, self._item.name)
        if self._item.extensions != settings.SUPPORTED_EXTENSIONS:
            self._item._parent._refresh_project(self._item)
        self._item.update_paths()
        self.close()


class ProjectData(QWidget):

    def __init__(self, parent):
        super(ProjectData, self).__init__()
        self._parent = parent
        grid = QGridLayout(self)
        grid.addWidget(QLabel(_translate("ProjectData", "Name:")), 0, 0)
        self.name = QLineEdit()
        if self._parent._item.name == '':
            self.name.setText(file_manager.get_basename(
                self._parent._item.path))
        else:
            self.name.setText(self._parent._item.name)
        grid.addWidget(self.name, 0, 1)
        grid.addWidget(QLabel(_translate("ProjectData", "Project Location:")), 1, 0)
        self.txtPath = QLineEdit()
        self.txtPath.setReadOnly(True)
        self.txtPath.setText(self._parent._item.path)
        grid.addWidget(self.txtPath, 1, 1)
        grid.addWidget(QLabel(_translate("ProjectData", "Project Type:")), 2, 0)
        self.txtType = QLineEdit()
        completer = QCompleter(sorted(settings.PROJECT_TYPES))
        completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.txtType.setCompleter(completer)
        self.txtType.setText(self._parent._item.projectType)
        grid.addWidget(self.txtType, 2, 1)
        grid.addWidget(QLabel(_translate("ProjectData", "Description:")), 3, 0)
        self.description = QPlainTextEdit()
        self.description.setPlainText(self._parent._item.description)
        grid.addWidget(self.description, 3, 1)
        grid.addWidget(QLabel(_translate("ProjectData", "URL:")), 4, 0)
        self.url = QLineEdit()
        self.url.setText(self._parent._item.url)
        grid.addWidget(self.url, 4, 1)
        grid.addWidget(QLabel(_translate("ProjectData", "Licence:")), 5, 0)
        self.cboLicense = QComboBox()
        self.cboLicense.addItem('Apache License 2.0')
        self.cboLicense.addItem('Artistic License/GPL')
        self.cboLicense.addItem('Eclipse Public License 1.0')
        self.cboLicense.addItem('GNU General Public License v2')
        self.cboLicense.addItem('GNU General Public License v3')
        self.cboLicense.addItem('GNU Lesser General Public License')
        self.cboLicense.addItem('MIT License')
        self.cboLicense.addItem('Mozilla Public License 1.1')
        self.cboLicense.addItem('Mozilla Public License 2.0')
        self.cboLicense.addItem('New BSD License')
        self.cboLicense.addItem('Other Open Source')
        self.cboLicense.addItem('Other')
        self.cboLicense.setCurrentIndex(4)
        index = self.cboLicense.findText(self._parent._item.license)
        self.cboLicense.setCurrentIndex(index)
        grid.addWidget(self.cboLicense, 5, 1)

        self.txtExtensions = QLineEdit()
        self.txtExtensions.setText(', '.join(self._parent._item.extensions))
        grid.addWidget(QLabel(_translate("ProjectData", "Supported Extensions:")), 6, 0)
        grid.addWidget(self.txtExtensions, 6, 1)

        grid.addWidget(QLabel(_translate("ProjectData", "Indentation: ")), 7, 0)
        self.spinIndentation = QSpinBox()
        self.spinIndentation.setValue(self._parent._item.indentation)
        self.spinIndentation.setMinimum(1)
        grid.addWidget(self.spinIndentation, 7, 1)
        self.checkUseTabs = QCheckBox(_translate("ProjectData", "Use Tabs."))
        self.checkUseTabs.setChecked(self._parent._item.useTabs)
        grid.addWidget(self.checkUseTabs, 7, 2)


class ProjectExecution(QWidget):

    def __init__(self, parent):
        super(ProjectExecution, self).__init__()
        self._parent = parent
        grid = QGridLayout(self)

        grid.addWidget(QLabel(_translate("ProjectExecution", "Main File:")), 0, 0)
        self.path = QLineEdit()
        ui_tools.LineEditButton(self.path, self.path.clear,
            self.style().standardPixmap(self.style().SP_TrashIcon))
        self.path.setText(self._parent._item.mainFile)
        self.path.setReadOnly(True)
        self.btnBrowse = QPushButton(QIcon(
            self.style().standardPixmap(self.style().SP_FileIcon)), '')
        grid.addWidget(self.path, 0, 1)
        grid.addWidget(self.btnBrowse, 0, 2)

        # this should be changed, and ALL pythonPath names to
        # python_custom_interpreter or something like that. this is NOT the
        # PYTHONPATH
        self.txtPythonPath = QLineEdit()
        self.txtPythonPath.setText(self._parent._item.pythonPath)
        self.btnPythonPath = QPushButton(QIcon(resources.IMAGES['open']), '')
        grid.addWidget(QLabel(_translate("ProjectExecution", "Python Custom Interpreter:")), 1, 0)
        grid.addWidget(self.txtPythonPath, 1, 1)
        grid.addWidget(self.btnPythonPath, 1, 2)

        # THIS IS THE MODAFUCKA REAL PYTHONPATH BRO, YEAH !!!
        grid.addWidget(QLabel(_translate("ProjectExecution", "Custom PYTHONPATH:")), 2, 0)
        self.PYTHONPATH = QPlainTextEdit()  # TODO : better widget
        self.PYTHONPATH.setPlainText(self._parent._item.PYTHONPATH)
        self.PYTHONPATH.setToolTip(_translate("ProjectExecution", "One path per line"))
        grid.addWidget(self.PYTHONPATH, 2, 1)

        # Additional builtins/globals for pyflakes
        grid.addWidget(QLabel(_translate("ProjectExecution", "Additional builtins/globals:")), 3, 0)
        self.additional_builtins = QLineEdit()
        self.additional_builtins.setText(
                ' '.join(self._parent._item.additional_builtins))
        self.additional_builtins.setToolTip(_translate("ProjectExecution", 
                "Space-separated list of symbols that will be considered as "
                "builtin in every file"))
        grid.addWidget(self.additional_builtins, 3, 1)

        self.txtPreExec = QLineEdit()
        ui_tools.LineEditButton(self.txtPreExec, self.txtPreExec.clear,
            self.style().standardPixmap(self.style().SP_TrashIcon))
        self.txtPreExec.setReadOnly(True)
        self.txtPreExec.setText(self._parent._item.preExecScript)
        self.btnPreExec = QPushButton(QIcon(resources.IMAGES['open']), '')
        grid.addWidget(QLabel(_translate("ProjectExecution", "Pre-exec Script:")), 4, 0)
        grid.addWidget(self.txtPreExec, 4, 1)
        grid.addWidget(self.btnPreExec, 4, 2)
        self.txtPostExec = QLineEdit()
        ui_tools.LineEditButton(self.txtPostExec, self.txtPostExec.clear,
            self.style().standardPixmap(self.style().SP_TrashIcon))
        self.txtPostExec.setReadOnly(True)
        self.txtPostExec.setText(self._parent._item.postExecScript)
        self.btnPostExec = QPushButton(QIcon(resources.IMAGES['open']), '')
        grid.addWidget(QLabel(_translate("ProjectExecution", "Post-exec Script:")), 5, 0)
        grid.addWidget(self.txtPostExec, 5, 1)
        grid.addWidget(self.btnPostExec, 5, 2)

        grid.addItem(QSpacerItem(5, 10, QSizePolicy.Expanding,
            QSizePolicy.Expanding), 6, 0)

        # Properties
        grid.addWidget(QLabel(_translate("ProjectExecution", "Properties:")), 7, 0)
        self.txtParams = QLineEdit()
        self.txtParams.setToolTip(
            _translate("ProjectExecution", "Separate the params with commas (ie: help, verbose)"))
        self.txtParams.setText(self._parent._item.programParams)
        grid.addWidget(QLabel(_translate("ProjectExecution", "Params (comma separated):")), 8, 0)
        grid.addWidget(self.txtParams, 8, 1)
        #Widgets for virtualenv properties
        self.txtVenvPath = QLineEdit()
        ui_tools.LineEditButton(self.txtVenvPath, self.txtVenvPath.clear,
            self.style().standardPixmap(self.style().SP_TrashIcon))
        self.txtVenvPath.setText(self._parent._item.venv)
        self._dir_completer = QCompleter()
        self._dir_completer.setModel(QDirModel(self._dir_completer))
        self.txtVenvPath.setCompleter(self._dir_completer)
        self.btnVenvPath = QPushButton(QIcon(resources.IMAGES['open']), '')
        grid.addWidget(QLabel(_translate("ProjectExecution", "Virtualenv Folder:")), 9, 0)
        grid.addWidget(self.txtVenvPath, 9, 1)
        grid.addWidget(self.btnVenvPath, 9, 2)

        self.btnBrowse.clicked['bool'].connect(self.select_file)
        self.btnPythonPath.clicked['bool'].connect(self._load_python_path)
        self.btnVenvPath.clicked['bool'].connect(self._load_python_venv)
        self.btnPreExec.clicked['bool'].connect(self.select_pre_exec_script)
        self.btnPostExec.clicked['bool'].connect(self.select_post_exec_script)

    def _load_python_path(self):
        path = QFileDialog.getOpenFileName(
            self, _translate("ProjectExecution", "Select Python Path"))
        self.txtPythonPath.setText(path)

    def _load_python_venv(self):
        venv = QFileDialog.getExistingDirectory(
            self, _translate("ProjectExecution", "Select Virtualenv Folder"))
        if sys.platform == 'win32':
            venv = os.path.join(venv, 'Scripts', 'python.exe')
        else:
            venv = os.path.join(venv, 'bin', 'python')
        #check if venv folder exists
        if not os.path.exists(venv):
            QMessageBox.information(self,
                _translate("ProjectExecution", "Virtualenv Folder"),
                _translate("ProjectExecution", "This is not a valid Virtualenv Folder"))
            self.txtVenvPath.setText("")
        else:
            self.txtVenvPath.setText(venv)

    def select_file(self):
        fileName = QFileDialog.getOpenFileName(
            self, _translate("ProjectExecution", "Select Main File"),
                        self._parent._item.path, '(*.py);;(*.*)')
        if fileName != '':
            fileName = file_manager.convert_to_relative(
                self._parent._item.path, fileName)
            self.path.setText(fileName)

    def select_pre_exec_script(self):
        fileName = QFileDialog.getOpenFileName(
            self, _translate("ProjectExecution", "Select Pre Execution Script File"),
                        self._parent._item.path, '(*.*)')
        if fileName != '':
            fileName = file_manager.convert_to_relative(
                self._parent._item.path, fileName)
            self.txtPreExec.setText(fileName)

    def select_post_exec_script(self):
        fileName = QFileDialog.getOpenFileName(
            self, _translate("ProjectExecution", "Select Post Execution Script File"),
                        self._parent._item.path, '(*.*)')
        if fileName != '':
            fileName = file_manager.convert_to_relative(
                self._parent._item.path, fileName)
            self.txtPostExec.setText(fileName)


class ProjectMetadata(QWidget):

    def __init__(self, parent):
        super(ProjectMetadata, self).__init__()
        self._parent = parent

        vbox = QVBoxLayout(self)
        vbox.addWidget(QLabel(_translate("ProjectExecution", 
                        "Insert the path of Python Projects related"
                        "to this one in order\nto improve Code Completion.")))
        self.txt_projects = QPlainTextEdit()
        vbox.addWidget(self.txt_projects)
        vbox.addWidget(QLabel(
            _translate("ProjectMetadata", "Split your paths using newlines [ENTER].")))

        paths = '\n'.join(self._parent._item.related_projects)
        self.txt_projects.setPlainText(paths)
