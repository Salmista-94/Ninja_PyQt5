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

from ninja_ide.tools.logger import NinjaLogger
logger = NinjaLogger('ninja_ide.gui.explorer.tree_projects_widget')
DEBUG = logger.debug

from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.core import settings
from ninja_ide.core import file_manager
from ninja_ide.core.filesystem_notifications import NinjaFileSystemWatcher
from ninja_ide.core.filesystem_notifications.base_watcher import ADDED,\
    DELETED, REMOVE, RENAME
from ninja_ide.tools import json_manager
from ninja_ide.tools import ui_tools
from ninja_ide.gui.main_panel import main_container
from ninja_ide.gui.dialogs import project_properties_widget
from ninja_ide.tools.completion import completion_daemon


_translate = QCoreApplication.translate


class TreeProjectsWidget(QTreeWidget):

###############################################################################
# TreeProjectsWidget SIGNALS
###############################################################################

    """
    runProject()
    closeProject(QString)
    closeFilesFromProjectClosed(QString)
    addProjectToConsole(QString)
    removeProjectFromConsole(QString)
    projectPropertiesUpdated(QTreeWidgetItem)
    """
    runProject = pyqtSignal()
    closeProject = pyqtSignal(str)
    closeFilesFromProjectClosed = pyqtSignal(str)
    addProjectToConsole = pyqtSignal(str)
    removeProjectFromConsole = pyqtSignal(str)
    projectPropertiesUpdated = pyqtSignal('QTreeWidgetItem*')
    refreshProject = pyqtSignal()


###############################################################################

    #Extra context menu 'all' indicate a menu for ALL LANGUAGES!
    extra_menus = {'all': []}
    #Extra context menu by scope all is for ALL the TREE ITEMS!
    extra_menus_by_scope = {'project': [], 'folder': [], 'file': []}

    images = {
        'py': resources.IMAGES['tree-python'],
        'jpg': resources.IMAGES['tree-image'],
        'png': resources.IMAGES['tree-image'],
        'html': resources.IMAGES['tree-html'],
        'css': resources.IMAGES['tree-css'],
        'ui': resources.IMAGES['designer']}

    def __init__(self, state_index=list()):
        super(TreeProjectsWidget, self).__init__()

        self.header().setHidden(True)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setAnimated(True)

        self._actualProject = None
        #self._projects -> key: [Item, folderStructure]
        self._projects = {}
        self._loading_items = {}
        self._thread_execution = {}
        self.__enableCloseNotification = True
        self._fileWatcher = NinjaFileSystemWatcher
        self._refresh_projects_queue = []
        self._timer_running = False

        self.header().setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested['const QPoint &'].connect(self._menu_context_tree)

        #signal_name = "itemClicked(QTreeWidgetItem *, int)"
        # For windows double click instead of single click
        if settings.IS_WINDOWS:
            #signal_name = "itemDoubleClicked(QTreeWidgetItem *, int)"
            self.itemDoubleClicked['QTreeWidgetItem*', int].connect(self._open_file)
        else:
            self.itemClicked['QTreeWidgetItem*', int].connect(self._open_file)

        #self.connect(self, SIGNAL(signal_name), self._open_file)
        self._fileWatcher.fileChanged[int, str].connect(self._refresh_project_by_path)
        self.itemExpanded['QTreeWidgetItem*'].connect(self._item_expanded)
        self.itemCollapsed['QTreeWidgetItem*'].connect(self._item_collapsed)
        self.mute_signals = False
        self.state_index = list()
        self._folding_menu = FoldingContextMenu(self)

    def _item_collapsed(self, tree_item):
        """Store status of item when collapsed"""
        if not self.mute_signals:
            path = tree_item.get_full_path()
            if path in self.state_index:
                path_index = self.state_index.index(path)
                self.state_index.pop(path_index)

    def _item_expanded(self, tree_item):
        """Store status of item when expanded"""
        if not self.mute_signals:
            path = tree_item.get_full_path()
            if path not in self.state_index:
                self.state_index.append(path)

    def shutdown(self):
        self._fileWatcher.shutdown_notification()

    def add_extra_menu(self, menu, lang='all'):
        '''
        Add an extra menu for the given language
        @lang: string with the form 'py', 'php', 'json', etc
        '''
        #remove blanks and replace dots Example(.py => py)
        lang = lang.strip().replace('.', '')
        self.extra_menus.setdefault(lang, [])
        self.extra_menus[lang].append(menu)

    def add_extra_menu_by_scope(self, menu, scope):
        '''
        Add an extra menu for the given language
        @scope: string with the menu scope (all, project, folder, item)
        '''
        if scope.project:
            self.extra_menus_by_scope['project'].append(menu)
        if scope.folder:
            self.extra_menus_by_scope['folder'].append(menu)
        if scope.file:
            self.extra_menus_by_scope['file'].append(menu)

    def _menu_context_tree(self, point):
        index = self.indexAt(point)
        if not index.isValid():
            return

        item = self.itemAt(point)
        handler = None
        menu = QMenu(self)
        if item.isFolder or item.parent() is None:
            self._add_context_menu_for_folders(menu, item)
        elif not item.isFolder:
            self._add_context_menu_for_files(menu, item)
        if item.parent() is None:
            #get the extra context menu for this projectType
            if isinstance(item, ProjectItem):
                return
            handler = settings.get_project_type_handler(item.projectType)
            self._add_context_menu_for_root(menu, item)

        menu.addMenu(self._folding_menu)

        #menu for all items (legacy API)!
        extra_menus = self.extra_menus.get('all', ())
        #menu for all items!
        for m in extra_menus:
            if isinstance(m, QMenu):
                menu.addSeparator()
                menu.addMenu(m)
        #menu for the Project Type(if present)
        if handler:
            for m in handler.get_context_menus():
                if isinstance(m, QMenu):
                    menu.addSeparator()
                    menu.addMenu(m)
        #show the menu!
        menu.exec_(QCursor.pos())

    def _add_context_menu_for_root(self, menu, item):
        menu.addSeparator()
        actionRunProject = menu.addAction(QIcon(
            resources.IMAGES['play']), _translate("TreeProjectsWidget", "Run Project"))
        actionRunProject.triggered.connect(self.runProject.emit)
        actionMainProject = menu.addAction(_translate("TreeProjectsWidget", "Set as Main Project"))
        actionMainProject.triggered.connect(lambda: self.set_default_project(item))
        if item.addedToConsole:
            actionRemoveFromConsole = menu.addAction(
                _translate("TreeProjectsWidget", "Remove this Project from the Python Console"))
            actionRemoveFromConsole.triggered.connect(self._remove_project_from_console)
        else:
            actionAdd2Console = menu.addAction(
                _translate("TreeProjectsWidget", "Add this Project to the Python Console"))
            actionAdd2Console.triggered.connect(self._add_project_to_console)
        actionProperties = menu.addAction(QIcon(resources.IMAGES['pref']),
                                          _translate("TreeProjectsWidget", "Project Properties"))
        action_remove_file.triggered.connect(self.open_project_properties)

        menu.addSeparator()
        action_refresh = menu.addAction(
            self.style().standardIcon(QStyle.SP_BrowserReload),
            _translate("TreeProjectsWidget", "Refresh Project"))
        action_refresh.triggered.connect(self._refresh_project)
        action_close = menu.addAction(
            self.style().standardIcon(QStyle.SP_DialogCloseButton),
            _translate("TreeProjectsWidget", "Close Project"))
        action_close.triggered.connect(self._close_project)
        #menu for the project
        for m in self.extra_menus_by_scope['project']:
            if isinstance(m, QMenu):
                menu.addSeparator()
                menu.addMenu(m)

    def _add_context_menu_for_folders(self, menu, item):
        action_add_file = menu.addAction(QIcon(resources.IMAGES['new']),
                                         _translate("TreeProjectsWidget", "Add New File"))
        action_add_file.triggered.connect(self._add_new_file)
        action_add_folder = menu.addAction(QIcon(
            resources.IMAGES['openProj']), _translate("TreeProjectsWidget", "Add New Folder"))
        action_add_folder.triggered.connect(self._add_new_folder)
        action_create_init = menu.addAction(
            _translate("TreeProjectsWidget", "Create '__init__' Complete"))
        action_create_init.triggered.connect(self._create_init)
        if item.isFolder and (item.parent() is not None):
            action_remove_folder = menu.addAction(_translate("TreeProjectsWidget", "Remove Folder"))
            action_remove_folder.triggered.connect(self._delete_folder)
        #Folders but not the root
        if item.isFolder and item.parent() is not None:
            for m in self.extra_menus_by_scope['folder']:
                if isinstance(m, QMenu):
                    menu.addSeparator()
                    menu.addMenu(m)

    def _add_context_menu_for_files(self, menu, item):
        action_rename_file = menu.addAction(_translate("TreeProjectsWidget", "Rename File"))
        action_move_file = menu.addAction(_translate("TreeProjectsWidget", "Move File"))
        action_copy_file = menu.addAction(_translate("TreeProjectsWidget", "Copy File"))
        action_remove_file = menu.addAction(
            self.style().standardIcon(QStyle.SP_DialogCloseButton),
            _translate("TreeProjectsWidget", "Delete File"))
        action_remove_file.triggered.connect(self._delete_file)
        action_rename_file.triggered.connect(self._rename_file)
        action_copy_file.triggered.connect(self._copy_file)
        action_move_file.triggered.connect(self._move_file)
        #Allow to edit Qt UI files with the appropiate program
        if item.lang() == 'ui':
            action_edit_ui_file = menu.addAction(_translate("TreeProjectsWidget", "Edit UI File"))
            action_edit_ui_file.triggered.connect(self._edit_ui_file)
        #menu per file language (legacy plugin API)!
        for m in self.extra_menus.get(item.lang(), ()):
            if isinstance(m, QMenu):
                menu.addSeparator()
                menu.addMenu(m)
        #menu for files
        for m in self.extra_menus_by_scope['file']:
            if isinstance(m, QMenu):
                menu.addSeparator()
                menu.addMenu(m)

    def _add_project_to_console(self):
        item = self.currentItem()
        if isinstance(item, ProjectTree):
            self.addProjectToConsole.emit(item.path)
            item.addedToConsole = True

    def _remove_project_from_console(self):
        item = self.currentItem()
        if isinstance(item, ProjectTree):
            self.removeProjectFromConsole.emit(item.path)
            item.addedToConsole = False

    def _open_file(self, item, column):
        if item.childCount() == 0 and not item.isFolder:
            fileName = os.path.join(item.path, item.text(column))
            main_container.MainContainer().open_file(fileName)

    def _get_project_root(self, item=None):
        if item is None:
            item = self.currentItem()
        while item is not None and item.parent() is not None:
            item = item.parent()
        return item

    def set_default_project(self, item):
        item.setForeground(0, QBrush(QColor(0, 204, 82)))
        if self._actualProject:
            item.setForeground(0, QBrush(QColor(255, 165, 0)))
        self._actualProject = item

    def open_project_properties(self):
        item = self._get_project_root()
        if item is None:
            QMessageBox.information(None, "Project info", "No project was loaded!")
            return
        proj = project_properties_widget.ProjectProperties(item, self)
        proj.show()

    def _timeout(self):
        projects = set(self._refresh_projects_queue)
        self._refresh_projects_queue = []
        self._timer_running = False
        for prefresh in projects:
            self._refresh_project(prefresh)

    def _refresh_project_by_path(self, event, folder):
        if event not in (DELETED, ADDED, REMOVE, RENAME):
            return
        oprojects = self.get_open_projects()
        for each_project in oprojects:
            p_path = each_project.path
            if file_manager.belongs_to_folder(p_path, folder) and \
               file_manager.is_supported_extension(folder,
                                                   each_project.extensions) \
               and folder[:1] != '.':
                self._refresh_projects_queue.append(each_project)
                break
        if not self._timer_running:
            self._timeout()
            QTimer.singleShot(3000, self._timeout)
            self._timer_running = True

    def _refresh_project(self, item=None):
        if item is None:
            item = self.currentItem()
        parentItem = self._get_project_root(item)
        if parentItem is None:
            return
        if item.parent() is None:
            path = item.path
        else:
            path = file_manager.create_path(item.path, item.text(0))

        thread = ui_tools.ThreadProjectExplore()
        self._thread_execution[path] = thread
        thread.folderDataRefreshed.connect(self._callback_refresh_project)
        thread.finished.connect(self._clean_threads)
        thread.refresh_project(path, item, parentItem.extensions)

    def _clean_threads(self):
        paths_to_delete = []
        for path in self._thread_execution:
            thread = self._thread_execution.get(path, None)
            if thread and not thread.isRunning():
                paths_to_delete.append(path)
        for path in paths_to_delete:
            thread = self._thread_execution.pop(path, None)
            if thread:
                thread.wait()

    def _callback_refresh_project(self, value):
        path, item, structure = value
        item.takeChildren()
        self._load_folder(structure, path, item)
        #todo: refresh completion
        item.setExpanded(True)
        if isinstance(item, ProjectTree):
            self.projectPropertiesUpdated.emit(item)

    def _close_project(self):
        item = self.currentItem()
        index = self.indexOfTopLevelItem(item)
        pathKey = item.path
        self._fileWatcher.remove_watch(pathKey)
        self.takeTopLevelItem(index)
        self._projects.pop(pathKey, None)
        if self.__enableCloseNotification:
            self.closeProject.emit(pathKey)
        self.closeFilesFromProjectClosed.emit(pathKey)
        item = self.currentItem()
        if item:
            self.set_default_project(item)
            self._actualProject = item
        else:
            self._actualProject = None

    def _create_init(self):
        item = self.currentItem()
        if item.parent() is None:
            pathFolder = item.path
        else:
            pathFolder = os.path.join(item.path, str(item.text(0)))
        try:
            file_manager.create_init_file_complete(pathFolder)
        except file_manager.NinjaFileExistsException as ex:
            QMessageBox.information(self, _translate("TreeProjectsWidget", "Create INIT fail"),
                                    ex.message)
        self._refresh_project(item)

    def _add_new_file(self):
        item = self.currentItem()
        if item.parent() is None:
            pathForFile = item.path
        else:
            pathForFile = os.path.join(item.path, item.text(0))
        result = QInputDialog.getText(self, _translate("TreeProjectsWidget", "New File"),
                                      _translate("TreeProjectsWidget", "Enter the File Name:"))
        fileName = result[0]

        if result[1] and fileName.strip() != '':
            try:
                fileName = os.path.join(pathForFile, fileName)
                fileName = file_manager.store_file_content(
                    fileName, '', newFile=True)
                name = file_manager.get_basename(fileName)
                subitem = ProjectItem(item, name, pathForFile)
                subitem.setToolTip(0, name)
                subitem.setIcon(0, self._get_file_icon(name))
                mainContainer = main_container.MainContainer()
                mainContainer.open_file(fileName)
            except file_manager.NinjaFileExistsException as ex:
                QMessageBox.information(self, _translate("TreeProjectsWidget", "File Already Exists"),
                    (_translate("TreeProjectsWidget", "Invalid Path: the file '%s' already exists.") %
                     ex.filename))

    def add_existing_file(self, path):
        relative = file_manager.convert_to_relative(
            self._actualProject.path, path)
        paths = relative.split(os.sep)[:-1]
        itemParent = self._actualProject
        for p in paths:
            for i in range(itemParent.childCount()):
                item = itemParent.child(i)
                if item.text(0) == p:
                    itemParent = item
                    break
        itemParent.setSelected(True)
        name = file_manager.get_basename(path)
        subitem = ProjectItem(itemParent, name, file_manager.get_folder(path))
        subitem.setToolTip(0, name)
        subitem.setIcon(0, self._get_file_icon(name))
        itemParent.setExpanded(True)

    def _add_new_folder(self):
        item = self.currentItem()
        if item.parent() is None:
            pathForFolder = item.path
        else:
            pathForFolder = os.path.join(item.path, item.text(0))
        result = QInputDialog.getText(self, _translate("TreeProjectsWidget", "New Folder"),
                                      _translate("TreeProjectsWidget", "Enter the Folder Name:"))
        folderName = result[0]

        if result[1] and folderName.strip() != '':
            folderName = os.path.join(pathForFolder, folderName)
            file_manager.create_folder(folderName)
            name = file_manager.get_basename(folderName)
            subitem = ProjectItem(item, name, pathForFolder)
            subitem.setToolTip(0, name)
            subitem.setIcon(0, QIcon(resources.IMAGES['tree-folder']))
            self._refresh_project(item)

    def _delete_file(self):
        item = self.currentItem()
        val = QMessageBox.question(self, _translate("TreeProjectsWidget", "Delete File"),
                       _translate("TreeProjectsWidget", "Do you want to delete the following file: ")
                       + os.path.join(item.path, item.text(0)),
                       QMessageBox.Yes, QMessageBox.No)
        if val == QMessageBox.Yes:
            path = file_manager.create_path(item.path, item.text(0))
            file_manager.delete_file(item.path, item.text(0))
            index = item.parent().indexOfChild(item)
            item.parent().takeChild(index)
            mainContainer = main_container.MainContainer()
            if mainContainer.is_open(path):
                mainContainer.close_deleted_file(path)

    def _delete_folder(self):
        item = self.currentItem()
        val = QMessageBox.question(self, _translate("TreeProjectsWidget", "Delete Folder"),
                       _translate("TreeProjectsWidget", "Do you want to delete the following folder: ")
                       + os.path.join(item.path, item.text(0)),
                       QMessageBox.Yes, QMessageBox.No)
        if val == QMessageBox.Yes:
            file_manager.delete_folder(item.path, item.text(0))
            index = item.parent().indexOfChild(item)
            item.parent().takeChild(index)

    def _rename_file(self):
        item = self.currentItem()
        if item.parent() is None:
            pathForFile = item.path
        else:
            pathForFile = os.path.join(item.path, item.text(0))
        result = QInputDialog.getText(self, _translate("TreeProjectsWidget", "Rename File"),
                          _translate("TreeProjectsWidget", "Enter New File Name:"), text=item.text(0))
        fileName = result[0]

        if result[1] and fileName.strip() != '':
            fileName = os.path.join(
                file_manager.get_folder(pathForFile), fileName)
            if pathForFile == fileName:
                return
            try:
                fileName = file_manager.rename_file(pathForFile, fileName)
                name = file_manager.get_basename(fileName)
                mainContainer = main_container.MainContainer()
                if mainContainer.is_open(pathForFile):
                    mainContainer.change_open_tab_name(pathForFile, fileName)
                subitem = ProjectItem(item.parent(), name,
                                      file_manager.get_folder(fileName))
                subitem.setToolTip(0, name)
                subitem.setIcon(0, self._get_file_icon(name))
                index = item.parent().indexOfChild(item)
                subitem.parent().takeChild(index)
            except file_manager.NinjaFileExistsException as ex:
                QMessageBox.information(self, _translate("TreeProjectsWidget", "File Already Exists"),
                    (_translate("TreeProjectsWidget", "Invalid Path: the file '%s' already exists.") %
                     ex.filename))

    def _copy_file(self):
        #get the selected QTreeWidgetItem
        item = self.currentItem()
        if item.parent() is None:
            pathForFile = item.path
        else:
            pathForFile = os.path.join(item.path, item.text(0))
        pathProjects = [p.path for p in self.get_open_projects()]
        addToProject = ui_tools.AddToProject(pathProjects, self)
        addToProject.setWindowTitle(_translate("TreeProjectsWidget", "Copy File to"))
        addToProject.exec_()
        if not addToProject.pathSelected:
            return
        name = QInputDialog.getText(self, _translate("TreeProjectsWidget", "Copy File"),
                                    _translate("TreeProjectsWidget", "File Name:"), text=item.text(0))[0]
        if not name:
            QMessageBox.information(self, _translate("TreeProjectsWidget", "Invalid Name"),
                        _translate("TreeProjectsWidget", "The file name is empty, please enter a name"))
            return
        path = file_manager.create_path(addToProject.pathSelected, name)
        try:
            content = file_manager.read_file_content(pathForFile)
            path = file_manager.store_file_content(path, content, newFile=True)
            self.add_existing_file(path)
        except file_manager.NinjaFileExistsException as ex:
                QMessageBox.information(self, _translate("TreeProjectsWidget", "File Already Exists"),
                    (_translate("TreeProjectsWidget", "Invalid Path: the file '%s' already exists.") %
                     ex.filename))

    def _move_file(self):
        item = self.currentItem()
        if item.parent() is None:
            pathForFile = item.path
        else:
            pathForFile = os.path.join(item.path, item.text(0))
        pathProjects = [p.path for p in self.get_open_projects()]
        addToProject = ui_tools.AddToProject(pathProjects, self)
        addToProject.setWindowTitle(_translate("TreeProjectsWidget", "Copy File to"))
        addToProject.exec_()
        if not addToProject.pathSelected:
            return
        name = file_manager.get_basename(pathForFile)
        path = file_manager.create_path(addToProject.pathSelected, name)
        try:
            content = file_manager.read_file_content(pathForFile)
            path = file_manager.store_file_content(path, content, newFile=True)
            file_manager.delete_file(pathForFile)
            index = item.parent().indexOfChild(item)
            item.parent().takeChild(index)
            self.add_existing_file(path)
            # Update path of opened file
            main = main_container.MainContainer()
            if main.is_open(pathForFile):
                widget = main.get_widget_for_path(pathForFile)
                if widget:
                    widget.ID = path
        except file_manager.NinjaFileExistsException as ex:
                QMessageBox.information(self, _translate("TreeProjectsWidget", "File Already Exists"),
                    (_translate("TreeProjectsWidget", "Invalid Path: the file '%s' already exists.") %
                     ex.filename))

    def _edit_ui_file(self):
        item = self.currentItem()
        if item.parent() is None:
            pathForFile = item.path
        else:
            pathForFile = os.path.join(item.path, item.text(0))
        pathForFile = "file://%s" % pathForFile
        #open the correct program to edit Qt UI files!
        QDesktopServices.openUrl(QUrl(pathForFile, QUrl.TolerantMode))

    def loading_project(self, folder, reload_item=None):
        loadingItem = ui_tools.LoadingItem()
        if reload_item is None:
            parent = self
        else:
            parent = reload_item.parent()
        item = loadingItem.add_item_to_tree(folder, self, ProjectItem, parent)
        self._loading_items[folder] = item

    def remove_loading_icon(self, folder):
        item = self._loading_items.pop(folder, None)
        if item is not None:
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)

    def load_project(self, folderStructure, folder):
        if not folder:
            return

        self.remove_loading_icon(folder)

        name = file_manager.get_basename(folder)
        item = ProjectTree(self, name, folder)
        item.isFolder = True
        item.setToolTip(0, folder)
        item.setIcon(0, QIcon(resources.IMAGES['tree-app']))
        self._projects[folder] = item
        if folderStructure[folder][1] is not None:
            folderStructure[folder][1].sort()
        self._load_folder(folderStructure, folder, item)
        item.setExpanded(True)
        if len(self._projects) == 1:
            self.set_default_project(item)
        if self.currentItem() is None:
            item.setSelected(True)
            self.setCurrentItem(item)
        self._fileWatcher.add_watch(folder)
        completion_daemon.add_project_folder(folder)
        self.sortItems(0, Qt.AscendingOrder)

    def _load_folder(self, folderStructure, folder, parentItem):
        """Load the Tree Project structure recursively."""
        # Avoid failing if for some reason folder is not found
        # Might be the case of special files, as links or versioning files
        files, folders = folderStructure.get(folder, [None, None])

        if files is not None:
            files.sort()
            for i in files:
                subitem = ProjectItem(parentItem, i, folder)
                subitem.setToolTip(0, i)
                subitem.setIcon(0, self._get_file_icon(i))
        if folders is not None:
            folders.sort()
            for _folder in folders:
                if _folder.startswith('.'):
                    continue
                subfolder = ProjectItem(parentItem, _folder, folder, True)
                subfolder.setToolTip(0, _folder)
                subfolder.setIcon(0, QIcon(resources.IMAGES['tree-folder']))
                subFolderPath = os.path.join(folder, _folder)
                if subFolderPath in self.state_index:
                    subfolder.setExpanded(True)
                self._load_folder(folderStructure,
                                  subFolderPath, subfolder)

    def _get_file_icon(self, fileName):
        return QIcon(self.images.get(file_manager.get_file_extension(fileName),
                                     resources.IMAGES['tree-generic']))

    def get_item_for_path(self, path):
        items = self.findItems(file_manager.get_basename(path),
                               Qt.MatchRecursive, 0)
        folder = file_manager.get_folder(path)
        for item in items:
            if file_manager.belongs_to_folder(folder, item.path):
                return item

    def get_project_by_name(self, projectName):
        """Return the name of the project item based on the project name."""
        # Return the item or None if it's not found
        for item in list(self._projects.values()):
            if item.name == projectName:
                return item

    def get_selected_project_path(self):
        if self._actualProject:
            return self._actualProject.path
        return None

    def get_project_main_file(self):
        if self._actualProject:
            return self._actualProject.mainFile
        return ''

    def get_selected_project_type(self):
        rootItem = self._get_project_root()
        return rootItem.projectType

    def get_selected_project_lang(self):
        rootItem = self._get_project_root()
        return rootItem.lang()

    def get_open_projects(self):
        return list(self._projects.values())

    def is_open(self, path):
        return len([True for item in list(self._projects.values())
                    if item.path == path]) != 0

    def _set_current_project(self, path):
        for item in list(self._projects.values()):
            if item.path == path:
                self.set_default_project(item)
                break

    def _close_open_projects(self):
        self.__enableCloseNotification = False
        for i in range(self.topLevelItemCount()):
            self.setCurrentItem(self.topLevelItem(0))
            self._close_project()
        self.__enableCloseNotification = True
        self._projects = {}

    def keyPressEvent(self, event):
        item = self.currentItem()
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._open_file(item, 0)
        elif event.key() in (Qt.Key_Space, Qt.Key_Slash) and item.isFolder:
            expand = not item.isExpanded()
            item.setExpanded(expand)
        elif event.key() == Qt.Key_Left and not item.isExpanded():
            parent = item.parent()
            if parent:
                parent.setExpanded(False)
                self.setCurrentItem(parent)
                return
        super(TreeProjectsWidget, self).keyPressEvent(event)


class ProjectItem(QTreeWidgetItem):

    def __init__(self, parent, name, path, isFolder=False):
        super(ProjectItem, self).__init__(parent)
        self.setText(0, name)
        self.path = path
        self.isFolder = isFolder

    @property
    def isProject(self):
        #flag to check if the item is a project ALWAYS FALSE
        return False

    def lang(self):
        return file_manager.get_file_extension(self.text(0))

    def get_full_path(self):
        '''
        Returns the full path of the file
        '''
        return os.path.join(self.path, self.text(0))

    def set_item_icon(self, icon):
        self.setIcon(0, icon)

    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()
        my_text = ('1%s' % self.text(column).lower() if
                   self.isFolder else '0%s' % self.text(column).lower())
        other_text = ('1%s' % otherItem.text(column).lower() if
                      otherItem.isFolder else '0%s'
                      % otherItem.text(column).lower())
        return my_text < other_text


class ProjectTree(QTreeWidgetItem):

    def __init__(self, parent, _name, path):
        super(ProjectTree, self).__init__(parent)
        self._parent = parent
        self.setText(0, _name)
        self.path = path
        self.isFolder = True
        self.setForeground(0, QBrush(QColor(255, 165, 0)))
        project = json_manager.read_ninja_project(path)
        self.name = project.get('name', '')
        if self.name == '':
            self.name = _name
        self.setText(0, self.name)
        self.projectType = project.get('project-type', '')
        self.description = project.get('description', '')
        self.url = project.get('url', '')
        self.license = project.get('license', '')
        self.mainFile = project.get('mainFile', '')
        self.preExecScript = project.get('preExecScript', '')
        self.postExecScript = project.get('postExecScript', '')
        self.indentation = project.get('indentation', settings.INDENT)
        self.useTabs = project.get('use-tabs', settings.USE_TABS)
        self.extensions = project.get('supported-extensions',
                                      settings.SUPPORTED_EXTENSIONS)
        self.pythonPath = project.get('pythonPath', settings.PYTHON_PATH)
        self.PYTHONPATH = project.get('PYTHONPATH', '')
        self.additional_builtins = project.get('additional_builtins', [])
        self.programParams = project.get('programParams', '')
        self.venv = project.get('venv', '')
        self.related_projects = project.get('relatedProjects', [])
        self.update_paths()
        self.addedToConsole = False

    def update_paths(self):
        for path in self.related_projects:
            completion_daemon.add_project_folder(path)

    @property
    def isProject(self):
        #flag to check if the item is a project ALWAYS TRUE
        return True

    def lang(self):
        if self.mainFile != '':
            return file_manager.get_file_extension(self.mainFile)
        return 'py'

    def get_full_path(self):
        '''
        Returns the full path of the project
        '''
        project_file = json_manager.get_ninja_project_file(self.path)
        if not project_file:  # FIXME: If we dont have a project file
            project_file = ''     # we should do SOMETHING! like kill zombies!
        return os.path.join(self.path, project_file)


class FoldingContextMenu(QMenu):
    """
    This class represents a menu for Folding/Unfolding task
    """

    def __init__(self, tree):
        super(FoldingContextMenu, self).__init__()
        self.setTitle(_translate("FoldingContextMenu", "Fold/Unfold"))
        self._tree = tree
        fold_project = self.addAction(_translate("FoldingContextMenu", "Fold the project"))
        unfold_project = self.addAction(_translate("FoldingContextMenu", "Unfold the project"))
        self.addSeparator()
        fold_all_projects = self.addAction(_translate("FoldingContextMenu", "Fold all projects"))
        unfold_all_projects = self.addAction(_translate("FoldingContextMenu", "Unfold all projects"))

        fold_project.triggered.connect(lambda: self._fold_unfold_project(False))
        unfold_project.triggered.connect(lambda: self._fold_unfold_project(True))
        fold_all_projects.triggered.connect(self._fold_all_projects)
        unfold_all_projects.triggered.connect(self._unfold_all_projects)

    def _recursive_fold_unfold(self, item, expand):
        if item.isFolder:
            item.setExpanded(expand)
        for index in range(item.childCount()):
            child = item.child(index)
            self._recursive_fold_unfold(child, expand)

    def _fold_unfold_project(self, expand):
        """
        Fold the current project
        """
        root = self._tree._get_project_root(item=self._tree.currentItem())
        childs = root.childCount()
        if childs:
            root.setExpanded(expand)

        for index in range(childs):
            item = root.child(index)
            self._recursive_fold_unfold(item, expand)

    def _fold_all_projects(self):
        """
        Fold all projects
        """
        self._tree.collapseAll()

    def _unfold_all_projects(self):
        """
        Unfold all project
        """
        self._tree.expandAll()
