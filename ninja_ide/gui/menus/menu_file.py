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
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources


_translate = QCoreApplication.translate


class MenuFile(QObject):

###############################################################################
# MENU FILE SIGNALS
###############################################################################
    """
    openFile(QString)
    """
    openFile = pyqtSignal(str)
###############################################################################

    def __init__(self, menuFile, toolbar, ide):
        super(MenuFile, self).__init__()

        newAction = menuFile.addAction(QIcon(resources.IMAGES['new']),
            (_translate("MenuFile", "&New File (%s)") %
                resources.get_shortcut("New-file").toString(
                    QKeySequence.NativeText)))
        newProjectAction = menuFile.addAction(
            QIcon(resources.IMAGES['newProj']),
            (_translate("MenuFile", "New Pro&ject (%s)") %
                resources.get_shortcut("New-project").toString(
                    QKeySequence.NativeText)))
        menuFile.addSeparator()
        saveAction = menuFile.addAction(QIcon(resources.IMAGES['save']),
            (_translate("MenuFile", "&Save (%s)") %
                resources.get_shortcut("Save-file").toString(
                    QKeySequence.NativeText)))
        saveAsAction = menuFile.addAction(QIcon(resources.IMAGES['saveAs']),
            _translate("MenuFile", "Save &As"))
        saveAllAction = menuFile.addAction(QIcon(resources.IMAGES['saveAll']),
            _translate("MenuFile", "Save All"))
        saveProjectAction = menuFile.addAction(QIcon(
            resources.IMAGES['saveAll']),
            (_translate("MenuFile", "Save Pro&ject  (%s)") %
                resources.get_shortcut("Save-project").toString(
                    QKeySequence.NativeText)))
        menuFile.addSeparator()
        reloadFileAction = menuFile.addAction(
            QIcon(resources.IMAGES['reload-file']),
            (_translate("MenuFile", "Reload File (%s)") %
                resources.get_shortcut("Reload-file").toString(
                    QKeySequence.NativeText)))
        menuFile.addSeparator()
        openAction = menuFile.addAction(QIcon(resources.IMAGES['open']),
            (_translate("MenuFile", "&Open (%s)") %
                resources.get_shortcut("Open-file").toString(
                    QKeySequence.NativeText)))
        openProjectAction = menuFile.addAction(
            QIcon(resources.IMAGES['openProj']),
            (_translate("MenuFile", "Open &Project (%s)") %
                resources.get_shortcut("Open-project").toString(
                    QKeySequence.NativeText)))
        self.recent_files = menuFile.addMenu(_translate("MenuFile", 'Open Recent Files'))
        menuFile.addSeparator()
        activateProfileAction = menuFile.addAction(
            QIcon(resources.IMAGES['activate-profile']),
            _translate("MenuFile", "Activate Profile"))
        deactivateProfileAction = menuFile.addAction(
            QIcon(resources.IMAGES['deactivate-profile']),
            _translate("MenuFile", "Deactivate Profile"))
        menuFile.addSeparator()
        printFile = menuFile.addAction(QIcon(resources.IMAGES['print']),
            (_translate("MenuFile", "Pr&int File (%s)") %
                resources.get_shortcut("Print-file").toString(
                    QKeySequence.NativeText)))
        closeAction = menuFile.addAction(
            ide.style().standardIcon(QStyle.SP_DialogCloseButton),
            (_translate("MenuFile", "&Close Tab (%s)") %
                resources.get_shortcut("Close-tab").toString(
                    QKeySequence.NativeText)))
        closeProjectsAction = menuFile.addAction(
            ide.style().standardIcon(QStyle.SP_DialogCloseButton),
            _translate("MenuFile", "&Close All Projects"))
        menuFile.addSeparator()
        exitAction = menuFile.addAction(
            ide.style().standardIcon(QStyle.SP_DialogCloseButton),
            _translate("MenuFile", "&Exit"))

        self.toolbar_items = {
            'new-file': newAction,
            'new-project': newProjectAction,
            'save-file': saveAction,
            'save-as': saveAsAction,
            'save-all': saveAllAction,
            'save-project': saveProjectAction,
            'reload-file': reloadFileAction,
            'open-file': openAction,
            'open-project': openProjectAction,
            'activate-profile': activateProfileAction,
            'deactivate-profile': deactivateProfileAction,
            'print-file': printFile,
            'close-file': closeAction,
            'close-projects': closeProjectsAction}

        newAction.triggered['bool'].connect(lambda: ide.mainContainer.add_editor())
        newProjectAction.triggered['bool'].connect(lambda: ide.explorer.create_new_project())
        openAction.triggered['bool'].connect(lambda: ide.mainContainer.open_file())
        saveAction.triggered['bool'].connect(lambda: ide.mainContainer.save_file())
        saveAsAction.triggered['bool'].connect(lambda: ide.mainContainer.save_file_as())
        saveAllAction.triggered['bool'].connect(lambda: ide.actions.save_all())
        saveProjectAction.triggered['bool'].connect(lambda: ide.actions.save_project())
        openProjectAction.triggered['bool'].connect(lambda: ide.explorer.open_project_folder())
        closeAction.triggered['bool'].connect(lambda: ide.mainContainer.actualTab.close_tab())
        exitAction.triggered['bool'].connect(lambda: ide.close())
        reloadFileAction.triggered['bool'].connect(lambda: ide.mainContainer.reload_file())
        printFile.triggered['bool'].connect(lambda: ide.actions.print_file())
        closeProjectsAction.triggered['bool'].connect(lambda: ide.explorer.close_opened_projects())
        deactivateProfileAction.triggered['bool'].connect(lambda: ide.actions.deactivate_profile())
        activateProfileAction.triggered['bool'].connect(lambda: ide.actions.activate_profile())
        self.recent_files.triggered['QAction*'].connect(self._open_file)

    def update_recent_files(self, files):
        """Recreate the recent files menu."""
        self.recent_files.clear()
        for file_ in files:
            self.recent_files.addAction(file_)

    def _open_file(self, action):
        """Open the file selected in the recent files menu."""
        path = action.text()
        self.openFile.emit(path)
