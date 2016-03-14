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
from PyQt5.QtGui import QWheelEvent
#from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QObject
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources


_translate = QCoreApplication.translate


class MenuView(QObject):

    def __init__(self, menuView, toolbar, ide):
        super(MenuView, self).__init__()
        self.__ide = ide

        self.hideConsoleAction = menuView.addAction(
            (_translate("MenuView", "Show/Hide &Console (%s)") %
                resources.get_shortcut("Hide-misc").toString(
                    QKeySequence.NativeText)))
        self.hideConsoleAction.setCheckable(True)
        self.hideEditorAction = menuView.addAction(
            (_translate("MenuView", "Show/Hide &Editor (%s)") %
                resources.get_shortcut("Hide-editor").toString(
                    QKeySequence.NativeText)))
        self.hideEditorAction.setCheckable(True)
        self.hideAllAction = menuView.addAction(
            (_translate("MenuView", "Show/Hide &All (%s)") %
                resources.get_shortcut("Hide-all").toString(
                    QKeySequence.NativeText)))
        self.hideAllAction.setCheckable(True)
        self.hideExplorerAction = menuView.addAction(
            (_translate("MenuView", "Show/Hide &Explorer (%s)") %
                resources.get_shortcut("Hide-explorer").toString(
                    QKeySequence.NativeText)))
        self.hideExplorerAction.setCheckable(True)
        self.hideToolbarAction = menuView.addAction(
            _translate("MenuView", "Show/Hide &Toolbar"))
        self.hideToolbarAction.setCheckable(True)
        self.fullscreenAction = menuView.addAction(
            QIcon(resources.IMAGES['fullscreen']),
            (_translate("MenuView", "Full Screen &Mode (%s)") %
                resources.get_shortcut("Full-screen").toString(
                    QKeySequence.NativeText)))
        menuView.addSeparator()
        splitTabHAction = menuView.addAction(
            QIcon(resources.IMAGES['splitH']),
            (_translate("MenuView", "Split Tabs Horizontally (%s)") %
                resources.get_shortcut("Split-horizontal").toString(
                    QKeySequence.NativeText)))
        splitTabVAction = menuView.addAction(
            QIcon(resources.IMAGES['splitV']),
            (_translate("MenuView", "Split Tabs Vertically (%s)") %
                resources.get_shortcut("Split-vertical").toString(
                    QKeySequence.NativeText)))
        followModeAction = menuView.addAction(
            QIcon(resources.IMAGES['follow']),
            (_translate("MenuView", "Follow Mode (%s)") %
                resources.get_shortcut("Follow-mode").toString(
                    QKeySequence.NativeText)))
        groupTabsAction = menuView.addAction(
            _translate("MenuView", "Group Tabs by Project"))
        deactivateGroupTabsAction = menuView.addAction(
            _translate("MenuView", "Deactivate Group Tabs"))
        menuView.addSeparator()
        #Zoom
        zoomInAction = menuView.addAction(QIcon(resources.IMAGES['zoom-in']),
            _translate("MenuView", "Zoom &In (Ctrl+Wheel-Up)"))
        zoomOutAction = menuView.addAction(QIcon(resources.IMAGES['zoom-out']),
            _translate("MenuView", "Zoom &Out (Ctrl+Wheel-Down)"))
        menuView.addSeparator()
        fadeInAction = menuView.addAction(
            _translate("MenuView", "Fade In (Alt+Wheel-Up)"))
        fadeOutAction = menuView.addAction(
            _translate("MenuView", "Fade Out (Alt+Wheel-Down)"))

        self.toolbar_items = {
            'splitv': splitTabVAction,
            'splith': splitTabHAction,
            'follow-mode': followModeAction,
            'zoom-in': zoomInAction,
            'zoom-out': zoomOutAction}

        self.hideConsoleAction.triggered.connect(self.__ide.actions.view_misc_visibility)
        self.hideEditorAction.triggered.connect(self.__ide.actions.view_main_visibility)
        self.hideExplorerAction.triggered.connect(self.__ide.actions.view_explorer_visibility)
        self.hideAllAction.triggered.connect(self.__ide.actions.hide_all)
        self.fullscreenAction.triggered.connect(self.__ide.actions.fullscreen_mode)

        splitTabHAction.triggered.connect(lambda: self.__ide.mainContainer.split_tab(True))
        splitTabVAction.triggered.connect(lambda: self.__ide.mainContainer.split_tab(False))
        followModeAction.triggered.connect(self.__ide.mainContainer.show_follow_mode)
        zoomInAction.triggered.connect(self.zoom_in_editor)
        zoomOutAction.triggered.connect(self.zoom_out_editor)
        fadeInAction.triggered.connect(self._fade_in)
        fadeOutAction.triggered.connect(self._fade_out)
        self.hideToolbarAction.triggered.connect(self._hide_show_toolbar)
        groupTabsAction.triggered.connect(self.__ide.actions.group_tabs_together)
        deactivateGroupTabsAction.triggered.connect(self.__ide.actions.deactivate_tabs_groups)

        #Set proper MenuView checks values:
        self.hideAllAction.setChecked(True)
        self.hideConsoleAction.setChecked(False)
        self.hideEditorAction.setChecked(True)
        self.hideExplorerAction.setChecked(True)
        self.hideToolbarAction.setChecked(True)

    def _hide_show_toolbar(self):
        if self.__ide.toolbar.isVisible():
            self.__ide.toolbar.hide()
        else:
            self.__ide.toolbar.show()

    def zoom_in_editor(self):
        editor = self.__ide.mainContainer.get_actual_editor()
        if editor:
            editor.zoom_in()

    def zoom_out_editor(self):
        editor = self.__ide.mainContainer.get_actual_editor()
        if editor:
            editor.zoom_out()

    def _fade_in(self):
        event = QWheelEvent(QPoint(), 120, Qt.NoButton, Qt.AltModifier)
        self.__ide.wheelEvent(event)

    def _fade_out(self):
        event = QWheelEvent(QPoint(), -120, Qt.NoButton, Qt.AltModifier)
        self.__ide.wheelEvent(event)
