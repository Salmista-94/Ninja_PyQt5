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
import math

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtGui import QLinearGradient
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtPrintSupport import QPrintPreviewDialog
from PyQt5.QtGui import QPalette
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QThread
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import QTimeLine
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.core import settings
from ninja_ide.core import file_manager
from ninja_ide.core.file_manager import NinjaIOException
from ninja_ide.tools import json_manager

_translate = QCoreApplication.translate


def load_table(table, headers, data, checkFirstColumn=True):
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setStretchLastSection(True)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    for i in range(table.rowCount()):
        table.removeRow(0)
    for r, row in enumerate(data):
        table.insertRow(r)
        for index, colItem in enumerate(row):
            item = QTableWidgetItem(colItem)
            table.setItem(r, index, item)
            if index == 0 and checkFirstColumn:
                item.setData(Qt.UserRole, row)
                item.setCheckState(Qt.Unchecked)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled |
                              Qt.ItemIsUserCheckable)
            else:
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)


def remove_get_selected_items(table, data):
    rows = table.rowCount()
    pos = rows - 1
    selected = []
    for i in range(rows):
        if (table.item(pos - i, 0) is not None and
                table.item(pos - i, 0).checkState() == Qt.Checked):
            selected.append(data.pop(pos - i))
            table.removeRow(pos - i)
    return selected


class LoadingItem(QLabel):

    def __init__(self):
        super(LoadingItem, self).__init__()
        self.movie = QMovie(resources.IMAGES['loading'])
        self.setMovie(self.movie)
        self.movie.setScaledSize(QSize(16, 16))
        self.movie.start()

    def add_item_to_tree(self, folder, tree, item_type=None, parent=None):
        if item_type is None:
            item = QTreeWidgetItem()
            item.setText(0, (_translate("LoadingItem", "       LOADING: '%s'") % folder))
        else:
            item = item_type(parent, (
                _translate("LoadingItem", "       LOADING: '%s'") % folder), folder)
        tree.addTopLevelItem(item)
        tree.setItemWidget(item, 0, self)
        return item


###############################################################################
# Thread with Callback
###############################################################################


class ThreadExecution(QThread):# this class hasn´t instanciate. Ignore It!
    executionFinished = pyqtSignal(object)
    def __init__(self, functionInit=None, args=None, kwargs=None):
        super(ThreadExecution, self).__init__()
        self.execute = functionInit
        self.result = None
        self.storage_values = None
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.signal_return = None# No changed this value no any methods

    def run(self):
        if self.execute:
            self.result = self.execute(*self.args, **self.kwargs)
        self.executionFinished.emit(self.signal_return)
        self.signal_return = None


class ThreadProjectExplore(QThread):
    folderDataRefreshed = pyqtSignal(tuple)
    folderDataAcquired = pyqtSignal(tuple)
    def __init__(self):
        super(ThreadProjectExplore, self).__init__()
        self.execute = lambda: None
        self._folder_path = None
        self._item = None
        self._extensions = None

    def open_folder(self, folder):
        self._folder_path = folder
        self.execute = self._thread_open_project
        self.start()

    def refresh_project(self, path, item, extensions):
        self._folder_path = path
        self._item = item
        self._extensions = extensions
        self.execute = self._thread_refresh_project
        self.start()

    def run(self):
        self.execute()

    def _thread_refresh_project(self):
        if self._extensions != settings.SUPPORTED_EXTENSIONS:
            folderStructure = file_manager.open_project_with_extensions(
                self._folder_path, self._extensions)
        else:
            try:
                folderStructure = file_manager.open_project(self._folder_path)
            except NinjaIOException:
                pass  # There is not much we can do at this point

        if folderStructure and (folderStructure.get(
                self._folder_path,
                [None, None])[1] is not None):
            folderStructure[self._folder_path][1].sort()
            values = (self._folder_path, self._item, folderStructure)
            self.folderDataRefreshed.emit(values)

    def _thread_open_project(self):
        try:
            project = json_manager.read_ninja_project(self._folder_path)
            extensions = project.get('supported-extensions',
                                     settings.SUPPORTED_EXTENSIONS)
            if extensions != settings.SUPPORTED_EXTENSIONS:
                structure = file_manager.open_project_with_extensions(
                    self._folder_path, extensions)
            else:
                structure = file_manager.open_project(self._folder_path)

            self.folderDataAcquired.emit((self._folder_path, structure))
        except:
            self.folderDataAcquired.emit((self._folder_path, None))


###############################################################################
# LOADING ANIMATION OVER THE WIDGET
###############################################################################


class Overlay(QWidget):

    def __init__(self, parent=None):
        super(Overlay, self).__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)
        self.counter = 0

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))

        for i in range(6):
            x_pos = self.width() / 2 + 30 * \
                math.cos(2 * math.pi * i / 6.0) - 10
            y_pos = self.height() / 2 + 30 * \
                math.sin(2 * math.pi * i / 6.0) - 10
            if (self.counter / 5) % 6 == i:
                linear_gradient = QLinearGradient(
                    x_pos + 10, x_pos, y_pos + 10, y_pos)
                linear_gradient.setColorAt(0, QColor(135, 206, 250))
                linear_gradient.setColorAt(1, QColor(0, 0, 128))
                painter.setBrush(QBrush(linear_gradient))
            else:
                linear_gradient = QLinearGradient(
                    x_pos - 10, x_pos, y_pos + 10, y_pos)
                linear_gradient.setColorAt(0, QColor(105, 105, 105))
                linear_gradient.setColorAt(1, QColor(0, 0, 0))
                painter.setBrush(QBrush(linear_gradient))
            painter.drawEllipse(
                x_pos,
                y_pos,
                20, 20)

        painter.end()

    def showEvent(self, event):
        self.timer = self.startTimer(50)

    def timerEvent(self, event):
        self.counter += 1
        self.update()


###############################################################################
# PRINT FILE
###############################################################################


def print_file(fileName, printFunction):
    """This method print a file

    This method print a file, fileName is the default fileName,
    and printFunction is a funcion that takes a QPrinter
    object and print the file,
    the print method
    More info on:http://doc.qt.nokia.com/latest/printing.html"""

    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPrinter.A4)
    printer.setOutputFileName(fileName)
    printer.setDocName(fileName)

    preview = QPrintPreviewDialog(printer)
    preview.paintRequested['QPrinter*'].connect(printFunction)
    size = QApplication.instance().desktop().screenGeometry()
    width = size.width() - 100
    height = size.height() - 100
    preview.setMinimumSize(width, height)
    preview.exec_()

###############################################################################
# FADING ANIMATION
###############################################################################


class FaderWidget(QWidget):

    def __init__(self, old_widget, new_widget):
        super(FaderWidget, self).__init__(new_widget)

        self.old_pixmap = QPixmap(new_widget.size())
        old_widget.render(self.old_pixmap)
        self.pixmap_opacity = 1.0

        self.timeline = QTimeLine()
        self.timeline.valueChanged.connect(self.animate)
        self.timeline.finished.connect(self.close)
        self.timeline.setDuration(500)
        self.timeline.start()

        self.resize(new_widget.size())
        self.show()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setOpacity(self.pixmap_opacity)
        painter.drawPixmap(0, 0, self.old_pixmap)
        painter.end()

    def animate(self, value):
        self.pixmap_opacity = 1.0 - value
        self.repaint()


###############################################################################
# ADD TO PROJECT
###############################################################################


class AddToProject(QDialog):

    def __init__(self, pathProjects, parent=None):
        #pathProjects must be a list
        super(AddToProject, self).__init__(parent)
        self.setWindowTitle(_translate("AddToProject", "Add File to Project"))
        self.pathSelected = ''
        vbox = QVBoxLayout(self)

        self._tree = QTreeWidget()
        self._tree.header().setHidden(True)
        self._tree.setSelectionMode(QTreeWidget.SingleSelection)
        self._tree.setAnimated(True)
        vbox.addWidget(self._tree)
        hbox = QHBoxLayout()
        btnAdd = QPushButton(_translate("AddToProject", "Add here!"))
        btnCancel = QPushButton(_translate("AddToProject", "Cancel"))
        hbox.addWidget(btnCancel)
        hbox.addWidget(btnAdd)
        vbox.addLayout(hbox)
        #load folders
        self._root = None
        self._loading_items = {}
        self.loading_projects(pathProjects)
        self._thread_execution = ThreadExecution(
            self._thread_load_projects, args=[pathProjects])
        self._thread_execution.finished.connect(self._callback_load_project)
        self._thread_execution.start()

        btnCancel.clicked['bool'].connect(self.close)
        btnAdd.clicked['bool'].connect(self._select_path)

    def loading_projects(self, projects):
        for project in projects:
            loadingItem = LoadingItem()
            item = loadingItem.add_item_to_tree(project, self._tree,
                                                parent=self)
            self._loading_items[project] = item

    def _thread_load_projects(self, projects):
        structures = []
        for pathProject in projects:
            folderStructure = file_manager.open_project(pathProject)
            structures.append((folderStructure, pathProject))
        self._thread_execution.storage_values = structures

    def _callback_load_project(self):
        structures = self._thread_execution.storage_values
        if structures:
            for structure, path in structures:
                item = self._loading_items.pop(path, None)
                if item is not None:
                    index = self._tree.indexOfTopLevelItem(item)
                    self._tree.takeTopLevelItem(index)
                self._load_project(structure, path)

    def _select_path(self):
        item = self._tree.currentItem()
        if item:
            self.pathSelected = item.toolTip(0)
            self.close()

    def _load_project(self, folderStructure, folder):
        if not folder:
            return

        name = file_manager.get_basename(folder)
        item = QTreeWidgetItem(self._tree)
        item.setText(0, name)
        item.setToolTip(0, folder)
        item.setIcon(0, QIcon(resources.IMAGES['tree-folder']))
        if folderStructure[folder][1] is not None:
            folderStructure[folder][1].sort()
        self._load_folder(folderStructure, folder, item)
        item.setExpanded(True)
        self._root = item

    def _load_folder(self, folderStructure, folder, parentItem):
        items = folderStructure[folder]

        if items[1] is not None:
            items[1].sort()
        for _file in items[1]:
            if _file.startswith('.'):
                continue
            subfolder = QTreeWidgetItem(parentItem)
            subfolder.setText(0, _file)
            subfolder.setToolTip(0, os.path.join(folder, _file))
            subfolder.setIcon(0, QIcon(resources.IMAGES['tree-folder']))
            self._load_folder(folderStructure,
                              os.path.join(folder, _file), subfolder)


###############################################################################
# PROFILE WIDGET
###############################################################################

class ProfilesLoader(QDialog):

    def __init__(self, load_func, create_func, save_func,
                 profiles, parent=None):
        super(ProfilesLoader, self).__init__(self, parent, Qt.Dialog)
        self.setWindowTitle(_translate("ProfilesLoader", "Profile Manager"))
        self.setMinimumWidth(400)
        self._profiles = profiles
        self.load_function = load_func
        self.create_function = create_func
        self.save_function = save_func
        self.ide = parent
        vbox = QVBoxLayout(self)
        vbox.addWidget(QLabel(_translate("ProfilesLoader", "Save your opened files and projects "
                                      "into a profile and change really"
                                      "quick between projects and"
                                      "files sessions.\n This allows you to "
                                      "save your working environment, "
                                      "keep working in another\n"
                                      "project and then go back "
                                      "exactly where you left.")))
        self.profileList = QListWidget()
        self.profileList.addItems([key for key in profiles])
        self.profileList.setCurrentRow(0)
        self.contentList = QListWidget()
        self.btnDelete = QPushButton(_translate("ProfilesLoader", "Delete Profile"))
        self.btnDelete.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnUpdate = QPushButton(_translate("ProfilesLoader", "Update Profile"))
        self.btnUpdate.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnCreate = QPushButton(_translate("ProfilesLoader", "Create New Profile"))
        self.btnCreate.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnOpen = QPushButton(_translate("ProfilesLoader", "Open Profile"))
        self.btnOpen.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnOpen.setDefault(True)
        hbox = QHBoxLayout()
        hbox.addWidget(self.btnDelete)
        hbox.addWidget(self.btnUpdate)
        hbox.addWidget(self.btnCreate)
        hbox.addWidget(self.btnOpen)

        vbox.addWidget(self.profileList)
        vbox.addWidget(self.contentList)
        vbox.addLayout(hbox)

        self.profileList.itemSelectionChanged.connect(self.load_profile_content)
        self.btnOpen.clicked['bool'].connect(self.open_profile)
        self.btnUpdate.clicked['bool'].connect(self.save_profile)
        self.btnCreate.clicked['bool'].connect(self.create_profile)
        self.btnDelete.clicked['bool'].connect(self.delete_profile)

    def load_profile_content(self):
        item = self.profileList.currentItem()
        self.contentList.clear()
        if item is not None:
            key = item.text()
            files = [_translate("ProfilesLoader", 'Files:')] + \
                [file[0] for file in self._profiles[key][0]]
            projects = [_translate("ProfilesLoader", 'Projects:')] + self._profiles[key][1]
            content = files + projects
            self.contentList.addItems(content)

    def create_profile(self):
        profileName = self.create_function()
        self.ide.Profile = profileName
        self.close()

    def save_profile(self):
        if self.profileList.currentItem():
            profileName = self.profileList.currentItem().text()
            self.save_function(profileName)
            self.ide.show_status_message(_translate("ProfilesLoader", "Profile %s Updated!") %
                                         profileName)
            self.load_profile_content()

    def open_profile(self):
        if self.profileList.currentItem():
            key = self.profileList.currentItem().text()
            self.load_function(key)
            self.ide.Profile = key
            self.close()

    def delete_profile(self):
        if self.profileList.currentItem():
            key = self.profileList.currentItem().text()
            self._profiles.pop(key)
            self.profileList.takeItem(self.profileList.currentRow())
            self.contentList.clear()


###############################################################################
# Enhanced UI Widgets
###############################################################################

class LineEditButton(object):

    def __init__(self, lineEdit, operation, icon=None):
        hbox = QHBoxLayout(lineEdit)
        hbox.setSpacing(0)#hbox.setMargin(0)
        lineEdit.setLayout(hbox)
        hbox.addStretch()
        btnOperation = QPushButton(lineEdit)
        btnOperation.setObjectName('line_button')
        if icon:
            btnOperation.setIcon(QIcon(icon))
        hbox.addWidget(btnOperation)
        btnOperation.clicked.connect(operation)


class ComboBoxButton(object):

    def __init__(self, combo, operation, icon=None):
        hbox = QHBoxLayout(combo)
        hbox.setDirection(hbox.RightToLeft)
        hbox.setSpacing(0)#hbox.setMargin(0)
        combo.setLayout(hbox)
        hbox.addStretch()
        btnOperation = QPushButton(combo)
        btnOperation.setObjectName('combo_button')
        if icon:
            btnOperation.setIcon(QIcon(icon))
        hbox.addWidget(btnOperation)
        btnOperation.clicked.connect(operation)


class LineEditCount(QObject):

    def __init__(self, lineEdit):
        super(LineEditCount, self).__init__()
        hbox = QHBoxLayout(lineEdit)
        hbox.setSpacing(0)#hbox.setMargin(0)
        lineEdit.setLayout(hbox)
        hbox.addStretch()
        self.counter = QLabel(lineEdit)
        hbox.addWidget(self.counter)
        lineEdit.setStyleSheet("padding-right: 2px;")
        lineEdit.setTextMargins(0, 0, 60, 0)

    def update_count(self, index, total, hasSearch=False):
        message = _translate("ProfilesLoader", "%s of %s") % (index, total)
        self.counter.setText(message)
        self.counter.setStyleSheet("background: none;color: gray;")
        if index == 0 and total == 0 and hasSearch:
            self.counter.setStyleSheet(
                "background: #e73e3e;color: white;border-radius: 5px;")


class LineEditTabCompleter(QLineEdit):

    def __init__(self, completer, type=QCompleter.PopupCompletion):
        super(LineEditTabCompleter, self).__init__()
        self.completer = completer
        self.setTextMargins(0, 0, 5, 0)
        self.completionType = type
        self.completer.setCompletionMode(self.completionType)

    def event(self, event):
        if (event.type() == QEvent.KeyPress) and (event.key() == Qt.Key_Tab):
            if self.completionType == QCompleter.InlineCompletion:
                eventTab = QKeyEvent(QEvent.KeyPress,
                                     Qt.Key_End, Qt.NoModifier)
                super(LineEditTabCompleter, self).event(eventTab)
            else:
                completion = self.completer.currentCompletion()
                if os.path.isdir(completion):
                    completion += os.path.sep
                self.selectAll()
                self.insert(completion)
                self.completer.popup().hide()
            return True
        return super(LineEditTabCompleter, self).event(event)

    def contextMenuEvent(self, event):
        popup_menu = self.createStandardContextMenu()

        if self.completionType == QCompleter.InlineCompletion:
            actionCompletion = QAction(
                _translate("LineEditTabCompleter", "Set completion type to: Popup Completion"), self)
        else:
            actionCompletion = QAction(
                _translate("LineEditTabCompleter", "Set completion type to: Inline Completion"), self)
        actionCompletion.triggered.connect(self.change_completion_type)
        popup_menu.insertSeparator(popup_menu.actions()[0])
        popup_menu.insertAction(popup_menu.actions()[0], actionCompletion)

        #show menu
        popup_menu.exec_(event.globalPos())

    def change_completion_type(self):
        if self.completionType == QCompleter.InlineCompletion:
            self.completionType = QCompleter.PopupCompletion
        else:
            self.completionType = QCompleter.InlineCompletion
        self.completer.setCompletionMode(self.completionType)
        self.setFocus()
