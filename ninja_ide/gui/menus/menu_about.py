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


import webbrowser

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QObject
#from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.gui.main_panel import main_container
from ninja_ide.gui.main_panel import browser_widget
from ninja_ide.gui.dialogs import about_ninja


_translate = QCoreApplication.translate


class MenuAbout(QObject):

    def __init__(self, menuAbout):
        super(MenuAbout, self).__init__()

        startPageAction = menuAbout.addAction(_translate("MenuAbout", "Show Start Page"))
        helpAction = menuAbout.addAction(_translate("MenuAbout", "Python Help (%s)") %
            resources.get_shortcut("Help").toString(QKeySequence.NativeText))
        menuAbout.addSeparator()
        reportBugAction = menuAbout.addAction(_translate("MenuAbout", "Report Bugs!"))
        pluginsDocAction = menuAbout.addAction(
                                        _translate("MenuAbout", "Plugins Documentation"))
        menuAbout.addSeparator()

        aboutNinjaAction = menuAbout.addAction(_translate("MenuAbout", "About NINJA-IDE"))
        aboutQtAction = menuAbout.addAction(_translate("MenuAbout", "About Qt"))

        #Connect Action SIGNALs to proper functions
        startPageAction.triggered.connect(main_container.MainContainer().show_start_page)

        startPageAction.triggered.connect(self.show_report_bugs)
        aboutQtAction.triggered.connect(self._show_about_qt)
        helpAction.triggered.connect(main_container.MainContainer().show_python_doc)
        helpAction.triggered.connect(self._show_about_ninja)
        pluginsDocAction.triggered.connect(self.show_plugins_doc)

    def show_report_bugs(self):
        webbrowser.open(resources.BUGS_PAGE)

    def show_plugins_doc(self):
        bugsPage = browser_widget.BrowserWidget(resources.PLUGINS_DOC,
            parent=main_container.MainContainer())
        main_container.MainContainer().add_tab(
            bugsPage, _translate("MenuAbout", "How to Write NINJA-IDE plugins"))

    def _show_about_qt(self):
        QMessageBox.aboutQt(main_container.MainContainer(),
            _translate("MenuAbout", "About Qt"))

    def _show_about_ninja(self):
        self.about = about_ninja.AboutNinja(main_container.MainContainer())
        self.about.show()
