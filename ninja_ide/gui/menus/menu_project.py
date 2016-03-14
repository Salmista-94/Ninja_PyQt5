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
#from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.gui import actions


_translate = QCoreApplication.translate


class MenuProject(QObject):

    def __init__(self, menuProject, toolbar):
        super(MenuProject, self).__init__()

        runAction = menuProject.addAction(QIcon(resources.IMAGES['play']),
            (_translate("MenuProject", "Run Project (%s)") %
                resources.get_shortcut("Run-project").toString(
                    QKeySequence.NativeText)))
#        debugAction = menuProject.addAction(
#            QIcon(resources.IMAGES['debug']),
#            _translate("MenuProject", "Debug Project (%s)" %
#                resources.get_shortcut("Debug").toString(
#                    QKeySequence.NativeText)))
        runFileAction = menuProject.addAction(
            QIcon(resources.IMAGES['file-run']),
            (_translate("MenuProject", "Run File (%s)") %
                resources.get_shortcut("Run-file").toString(
                    QKeySequence.NativeText)))
        stopAction = menuProject.addAction(QIcon(resources.IMAGES['stop']),
            (_translate("MenuProject", "Stop (%s)") %
                resources.get_shortcut("Stop-execution").toString(
                    QKeySequence.NativeText)))
        menuProject.addSeparator()
        projectPropertiesAction = menuProject.addAction(
            _translate("MenuProject", "Open Project Properties"))
        menuProject.addSeparator()
        previewAction = menuProject.addAction(
            QIcon(resources.IMAGES['preview-web']),
            _translate("MenuProject", "Preview Web in Default Browser"))
#        diagramView = menuProject.addAction(_translate("MenuProject", "Diagram View"))

        self.toolbar_items = {
            'run-project': runAction,
            'run-file': runFileAction,
            'stop': stopAction,
            'preview-web': previewAction}

        runAction.triggered.connect(actions.Actions().execute_project)
        runFileAction.triggered.connect(actions.Actions().execute_file)
        stopAction.triggered.connect(actions.Actions().kill_execution)
        previewAction.triggered.connect(actions.Actions().preview_in_browser)
        projectPropertiesAction.triggered.connect(actions.Actions().open_project_properties)
#        self.connect(debugAction, SIGNAL("triggered()"),
#            actions.Actions().debug_file)
#        self.connect(diagramView, SIGNAL("triggered()"),
#            actions.Actions().open_class_diagram)
