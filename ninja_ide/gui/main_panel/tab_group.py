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


from PyQt5.QtWidgets import QWidget
#from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtCore import QCoreApplication

from ninja_ide.core import file_manager
from ninja_ide.gui.main_panel import itab_item


_translate = QCoreApplication.translate


class TabGroup(QWidget, itab_item.ITabItem):

    def __init__(self, project, name, actions):
        super(TabGroup, self).__init__()
        vbox = QVBoxLayout(self)
        self.actions = actions
        self.project = project
        self.ID = self.project
        self.name = name
        self.tabs = []
        self.listWidget = QListWidget()
        hbox = QHBoxLayout()
        btnExpand = QPushButton(_translate("TabGroup", "Expand this Files"))
        btnExpandAll = QPushButton(_translate("TabGroup", "Expand all Groups"))
        hbox.addWidget(btnExpandAll)
        hbox.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding))
        hbox.addWidget(btnExpand)
        vbox.addLayout(hbox)
        vbox.addWidget(self.listWidget)

        btnExpand.clicked['bool'].connect(self.expand_this)
        btnExpandAll.clicked['bool'].connect(self.actions.deactivate_tabs_groups)

    def add_widget(self, widget):
        self.tabs.append(widget)
        self.listWidget.addItem(widget.ID)

    def expand_this(self):
        self.actions.group_tabs_together()
        for tab in self.tabs:
            tabName = file_manager.get_basename(tab.ID)
            self.actions.ide.mainContainer.add_tab(tab, tabName)
        index = self.actions.ide.mainContainer._tabMain.indexOf(self)
        self.actions.ide.mainContainer._tabMain.removeTab(index)
        self.tabs = []
        self.listWidget.clear()

    def only_expand(self):
        for tab in self.tabs:
            tabName = file_manager.get_basename(tab.ID)
            self.actions.ide.mainContainer.add_tab(tab, tabName)
        index = self.actions.ide.mainContainer._tabMain.indexOf(self)
        self.actions.ide.mainContainer._tabMain.removeTab(index)
        self.tabs = []
        self.listWidget.clear()
