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

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QSettings
from PyQt5.QtCore import QDateTime
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.core import settings
from ninja_ide.core import file_manager
from ninja_ide.gui.explorer import tree_projects_widget
from ninja_ide.gui.explorer import tree_symbols_widget
from ninja_ide.gui.explorer import errors_lists
from ninja_ide.gui.explorer import migration_lists
from ninja_ide.gui.main_panel import main_container
from ninja_ide.gui.dialogs import wizard_new_project
from ninja_ide.tools import json_manager
from ninja_ide.tools import ui_tools

try:
    from PyQt5.QtWebKit import QWebInspector
except:
    settings.WEBINSPECTOR_SUPPORTED = False

from ninja_ide.tools.logger import NinjaLogger

logger = NinjaLogger('ninja_ide.gui.explorer.explorer_container')

__explorerContainerInstance = None

_translate = QCoreApplication.translate

def ExplorerContainer(*args, **kw):
    global __explorerContainerInstance
    if __explorerContainerInstance is None:
        __explorerContainerInstance = _s_ExplorerContainer(*args, **kw)
    return __explorerContainerInstance


class _s_ExplorerContainer(QTabWidget):

###############################################################################
# ExplorerContainer SIGNALS
###############################################################################

    """
    updateLocator()
    goToDefinition(int)
    projectOpened(QString)
    projectClosed(QString)
    """

    updateLocator = pyqtSignal()
    goToDefinition = pyqtSignal(int)
    projectOpened = pyqtSignal(str)
    projectClosed = pyqtSignal(str)

###############################################################################

    def __init__(self, parent=None):
        super(_s_ExplorerContainer, self).__init__(parent)
        self.setTabPosition(QTabWidget.East)
        self.__ide = parent
        self._thread_execution = {}

        #Searching the Preferences
        self._treeProjects = None
        if settings.SHOW_PROJECT_EXPLORER:
            self.add_tab_projects()
        self._treeSymbols = None
        if settings.SHOW_SYMBOLS_LIST:
            self.add_tab_symbols()
        self._inspector = None
        if settings.SHOW_WEB_INSPECTOR and settings.WEBINSPECTOR_SUPPORTED:
            self.add_tab_inspector()
        self._listErrors = None
        if settings.SHOW_ERRORS_LIST:
            self.add_tab_errors()
        self._listMigration = None
        if settings.SHOW_MIGRATION_LIST:
            self.add_tab_migration()

    def update_symbols(self, symbols, fileName):
        if self._treeSymbols:
            self._treeSymbols.update_symbols_tree(symbols, filename=fileName)

    def update_errors(self, errors, pep8):
        if self._listErrors:
            self._listErrors.refresh_lists(errors, pep8)

    def update_migration(self, migration):
        if self._listMigration:
            self._listMigration.refresh_lists(migration)

    def addTab(self, tab, title):
        QTabWidget.addTab(self, tab, title)

    def add_tab_migration(self):
        if not self._listMigration:
            self._listMigration = migration_lists.MigrationWidget()
            self.addTab(self._listMigration, _translate("_s_ExplorerContainer", "Migration 2to3"))

    def add_tab_projects(self):
        if not self._treeProjects:
            self._treeProjects = tree_projects_widget.TreeProjectsWidget()
            self.addTab(self._treeProjects, _translate("_s_ExplorerContainer", 'Projects'))
            self._treeProjects.runProject.connect(self.__ide.actions.execute_project)
            self.__ide.goingDown.connect(self._treeProjects.shutdown)
            self._treeProjects.addProjectToConsole[str].connect(self.__ide.actions.add_project_to_console)
            self._treeProjects.removeProjectFromConsole[str].connect(self.__ide.actions.remove_project_from_console)
  
            def close_project_signal():
                self.updateLocator.emit()

            def close_files_related_to_closed_project(project):
                if project:
                    self.projectClosed.emit(project)

            self._treeProjects.closeProject[str].connect(close_project_signal)
            self._treeProjects.refreshProject.connect(close_project_signal)
            self._treeProjects.closeFilesFromProjectClosed[str].connect(close_files_related_to_closed_project)
            

    def add_tab_symbols(self):
        if not self._treeSymbols:
            self._treeSymbols = tree_symbols_widget.TreeSymbolsWidget()
            self.addTab(self._treeSymbols, _translate("_s_ExplorerContainer", 'Symbols'))

            def _go_to_definition(lineno):
                self.goToDefinition.emit(lineno)

            self._treeSymbols.goToDefinition.connect(_go_to_definition)

    def update_current_symbol(self, line, col):
        """Select the proper item in the symbols list."""
        if self._treeSymbols is not None:
            self._treeSymbols.select_current_item(line, col)

    def add_tab_inspector(self):
        if not settings.WEBINSPECTOR_SUPPORTED:
            QMessageBox.information(self,
                _translate("_s_ExplorerContainer", "Web Inspector not Supported"),
                _translate("_s_ExplorerContainer", "Your Qt version doesn't support the Web Inspector"))
        if not self._inspector:
            self._inspector = WebInspector(self)
            self.addTab(self._inspector, _translate("_s_ExplorerContainer", "Web Inspector"))
            self._inspector.btnDock.clicked['bool'].connect(self._dock_inspector)

    def add_tab_errors(self):
        if not self._listErrors:
            self._listErrors = errors_lists.ErrorsWidget()
            self.addTab(self._listErrors, _translate("_s_ExplorerContainer", "Errors"))
            self._listErrors.pep8Activated.connect(self.__ide.mainContainer.reset_pep8_warnings)
            self._listErrors.lintActivated.connect(self.__ide.mainContainer.reset_lint_warnings)

    def remove_tab_migration(self):
        if self._listMigration:
            self.removeTab(self.indexOf(self._listMigration))
            self._listMigration = None

    def remove_tab_errors(self):
        if self._listErrors:
            self.removeTab(self.indexOf(self._listErrors))
            self._listErrors = None

    def remove_tab_projects(self):
        if self._treeProjects:
            self.removeTab(self.indexOf(self._treeProjects))
            self._treeProjects = None

    def remove_tab_symbols(self):
        if self._treeSymbols:
            self.removeTab(self.indexOf(self._treeSymbols))
            self._treeSymbols = None

    def remove_tab_inspector(self):
        if self._inspector:
            self.removeTab(self.indexOf(self._inspector))
            self._inspector = None

    def _dock_inspector(self):
        if self._inspector.parent():
            self._inspector.btnDock.setText(_translate("_s_ExplorerContainer", "Dock"))
            self._inspector.setParent(None)
            self._inspector.resize(500, 500)
            self._inspector.show()
        else:
            self.addTab(self._inspector, _translate("_s_ExplorerContainer", "Web Inspector"))
            self._inspector.btnDock.setText(_translate("_s_ExplorerContainer", "Undock"))

    def add_tab(self, widget, name, icon):
        self.addTab(widget, QIcon(icon), name)

    def rotate_tab_position(self):
        if self.tabPosition() == QTabWidget.East:
            self.setTabPosition(QTabWidget.West)
        else:
            self.setTabPosition(QTabWidget.East)

    def show_project_tree(self):
        if self._treeProjects:
            self.setCurrentWidget(self._treeProjects)

    def show_symbols_tree(self):
        if self._treeSymbols:
            self.setCurrentWidget(self._treeSymbols)

    def show_web_inspector(self):
        if self._inspector:
            self.setCurrentWidget(self._inspector)

    def refresh_inspector(self):
        if self._inspector:
            self._inspector._webInspector.hide()
            self._inspector._webInspector.show()

    def set_inspection_page(self, page):
        if self._inspector:
            self._inspector._webInspector.setPage(page)
            self._inspector._webInspector.setVisible(True)

    def open_project_folder(self, folderName='', notIDEStart=True):
        if not self._treeProjects and notIDEStart:
            QMessageBox.information(self, _translate("_s_ExplorerContainer", "Projects Disabled"),
                _translate("_s_ExplorerContainer", "Project support has been disabled from Preferences"))
            return
        if not folderName:
            if settings.WORKSPACE:
                directory = settings.WORKSPACE
            else:
                directory = os.path.expanduser("~")
                current_project = self.get_actual_project()
                mainContainer = main_container.MainContainer()
                editorWidget = mainContainer.get_actual_editor()
                if current_project is not None:
                    directory = current_project
                elif editorWidget is not None and editorWidget.ID:
                    directory = file_manager.get_folder(editorWidget.ID)
            folderName = QFileDialog.getExistingDirectory(self,
                                  _translate("_s_ExplorerContainer", "Open Project Directory"), directory)
        try:
            if not folderName:
                return
            if not self._treeProjects.is_open(folderName):
                self._treeProjects.mute_signals = True
                self._treeProjects.loading_project(folderName)
                thread = ui_tools.ThreadProjectExplore()
                self._thread_execution[folderName] = thread
                thread.folderDataAcquired.connect(self._callback_open_project)
                thread.finished.connect(self._unmute_tree_signals_clean_threads)

                thread.open_folder(folderName)
            else:
                self._treeProjects._set_current_project(folderName)
        except Exception as reason:
            logger.error('open_project_folder: %s', reason)
            if not notIDEStart:
                QMessageBox.information(self, _translate("_s_ExplorerContainer", "Incorrect Project"),
                                _translate("_s_ExplorerContainer", "The project could not be loaded!"))

    def _unmute_tree_signals_clean_threads(self):
        paths_to_delete = []
        for path in self._thread_execution:
            thread = self._thread_execution.get(path, None)
            if thread and not thread.isRunning():
                paths_to_delete.append(path)
        for path in paths_to_delete:
            thread = self._thread_execution.pop(path, None)
            if thread:
                thread.wait()
        if len(self._thread_execution) == 0:
            self._treeProjects.mute_signals = False

    def _callback_open_project(self, value):
        path, structure = value
        if structure is None:
            self._treeProjects.remove_loading_icon(path)
            return

        self._treeProjects.load_project(structure, path)
        self.save_recent_projects(path)
        self.projectOpened.emit(path)
        self.updateLocator.emit()

    def create_new_project(self):
        if not self._treeProjects:
            QMessageBox.information(self, _translate("_s_ExplorerContainer", "Projects Disabled"),
                _translate("_s_ExplorerContainer", "Project support has been disabled from Preferences"))
            return
        wizard = wizard_new_project.WizardNewProject(self)
        wizard.show()

    def add_existing_file(self, path):
        if self._treeProjects:
            self._treeProjects.add_existing_file(path)

    def get_actual_project(self):
        if self._treeProjects:
            return self._treeProjects.get_selected_project_path()
        return None

    def get_project_main_file(self):
        if self._treeProjects:
            return self._treeProjects.get_project_main_file()
        return ''

    def get_project_given_filename(self, filename):
        projects = self.get_opened_projects()
        for project in projects:
            if filename.startswith(project.path):
                return project
        return None

    def get_opened_projects(self):
        if self._treeProjects:
            return self._treeProjects.get_open_projects()
        return []

    def open_session_projects(self, projects, notIDEStart=True):
        if not self._treeProjects:
            return
        for project in projects:
            if file_manager.folder_exists(project):
                self.open_project_folder(project, notIDEStart)

    def open_project_properties(self):
        if self._treeProjects:
            self._treeProjects.open_project_properties()

    def close_opened_projects(self):
        if self._treeProjects:
            self._treeProjects._close_open_projects()

    def save_recent_projects(self, folder):
        recent_project_list = QSettings(
            resources.SETTINGS_PATH,
            QSettings.IniFormat).value('recentProjects', {})
        #if already exist on the list update the date time
        projectProperties = json_manager.read_ninja_project(folder)
        name = projectProperties.get('name', '')
        description = projectProperties.get('description', '')

        if name == '':
            name = file_manager.get_basename(folder)

        if description == '':
            description = _translate("_s_ExplorerContainer", 'no description available')

        if folder in recent_project_list:
            properties = recent_project_list[folder]
            properties["lastopen"] = QDateTime.currentDateTime()
            properties["name"] = name
            properties["description"] = description
            recent_project_list[folder] = properties
        else:
            recent_project_list[folder] = {
                "name": name,
                "description": description,
                "isFavorite": False, "lastopen": QDateTime.currentDateTime()}
            #if the length of the project list it's high that 10 then delete
            #the most old
            #TODO: add the length of available projects to setting
            if len(recent_project_list) > 10:
                del recent_project_list[self.find_most_old_open()]
        QSettings(resources.SETTINGS_PATH, QSettings.IniFormat).setValue(
            'recentProjects', recent_project_list)

    def find_most_old_open(self):
        recent_project_list = QSettings(
            resources.SETTINGS_PATH,
            QSettings.IniFormat).value('recentProjects', {})
        listFounder = []
        for recent_project_path, content in list(recent_project_list.items()):
            listFounder.append((recent_project_path, int(
                content["lastopen"].toString("yyyyMMddHHmmzzz"))))
        listFounder = sorted(listFounder, key=lambda date: listFounder[1],
                             reverse=True)   # sort by date last used
        return listFounder[0][0]

    def get_project_name(self, path):
        if self._treeProjects:
            item = self._treeProjects._projects.get(path, None)
            if item is not None:
                return item.name

    def cleanup_tabs(self):
        """
        Cleans depending on what objects are visible
        """
        # Clean up tabs
        if self._treeSymbols:
            self._treeSymbols.clean()
        if self._listErrors:
            self._listErrors.clear()
        if self._listMigration:
            self._listMigration.clear()


class WebInspector(QWidget):

    def __init__(self, parent):
        super(WebInspector, self).__init__(parent)
        vbox = QVBoxLayout(self)
        self._webInspector = QWebInspector(self)
        vbox.addWidget(self._webInspector)
        self.btnDock = QPushButton(_translate("WebInspector", "Undock"))
        vbox.addWidget(self.btnDock)
