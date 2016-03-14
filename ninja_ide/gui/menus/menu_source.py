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
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QObject
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication

from ninja_ide import resources
from ninja_ide.core import settings
from ninja_ide.gui import actions


_translate = QCoreApplication.translate


class MenuSource(QObject):

    def __init__(self, menuSource):
        super(MenuSource, self).__init__()

        indentMoreAction = menuSource.addAction(
            QIcon(resources.IMAGES['indent-more']),
            (_translate("MenuSource", "Indent More (%s)") %
                QKeySequence(Qt.Key_Tab).toString(QKeySequence.NativeText)))
        indentLessAction = menuSource.addAction(
            QIcon(resources.IMAGES['indent-less']),
            (_translate("MenuSource", "Indent Less (%s)") %
                resources.get_shortcut("Indent-less").toString(
                    QKeySequence.NativeText)))
        menuSource.addSeparator()
        commentAction = menuSource.addAction(
            QIcon(resources.IMAGES['comment-code']),
            (_translate("MenuSource", "Comment (%s)") %
                resources.get_shortcut("Comment").toString(
                    QKeySequence.NativeText)))
        unCommentAction = menuSource.addAction(
            QIcon(resources.IMAGES['uncomment-code']),
            (_translate("MenuSource", "Uncomment (%s)") %
                resources.get_shortcut("Uncomment").toString(
                    QKeySequence.NativeText)))
        horizontalLineAction = menuSource.addAction(
            (_translate("MenuSource", "Insert Horizontal Line (%s)") %
                resources.get_shortcut("Horizontal-line").toString(
                    QKeySequence.NativeText)))
        titleCommentAction = menuSource.addAction(
            (_translate("MenuSource", "Insert Title Comment (%s)") %
                resources.get_shortcut("Title-comment").toString(
                    QKeySequence.NativeText)))
        countCodeLinesAction = menuSource.addAction(
            _translate("MenuSource", "Count Code Lines"))
        menuSource.addSeparator()
#        tellTaleAction = menuSource.addAction(
#            _translate("MenuSource", "Tell me a Tale of Code"))
#        tellTaleAction.setEnabled(False)
        goToDefinitionAction = menuSource.addAction(
            QIcon(resources.IMAGES['go-to-definition']),
            (_translate("MenuSource", "Go To Definition (%s or %s+Click)") %
                (resources.get_shortcut("Go-to-definition").toString(
                    QKeySequence.NativeText),
                settings.OS_KEY)))
        insertImport = menuSource.addAction(
            QIcon(resources.IMAGES['insert-import']),
            (_translate("MenuSource", "Insert &Import (%s)") %
                resources.get_shortcut("Import").toString(
                    QKeySequence.NativeText)))
        menu_debugging = menuSource.addMenu(_translate("MenuSource", "Debugging Tricks"))
        insertPrints = menu_debugging.addAction(
            _translate("MenuSource", "Insert Prints per selected line."))
        insertPdb = menu_debugging.addAction(
            _translate("MenuSource", "Insert pdb.set_trace()"))
#        organizeImportsAction = menuSource.addAction(
#            _translate("MenuSource", "&Organize Imports"))
#        removeUnusedImportsAction = menuSource.addAction(
#            _translate("MenuSource", "Remove Unused &Imports"))
#        extractMethodAction = menuSource.addAction(
#            _translate("MenuSource", "Extract selected &code as Method"))
        menuSource.addSeparator()
        removeTrailingSpaces = menuSource.addAction(
            _translate("MenuSource", "&Remove Trailing Spaces"))
        replaceTabsSpaces = menuSource.addAction(
            _translate("MenuSource", "Replace Tabs With &Spaces"))
        moveUp = menuSource.addAction((_translate("MenuSource", "Move &Up (%s)") %
            resources.get_shortcut("Move-up").toString(
                QKeySequence.NativeText)))
        moveDown = menuSource.addAction((_translate("MenuSource", "Move &Down (%s)") %
            resources.get_shortcut("Move-down").toString(
                QKeySequence.NativeText)))
        duplicate = menuSource.addAction(
            (_translate("MenuSource", "Duplica&te (%s)") %
                resources.get_shortcut("Duplicate").toString(
                    QKeySequence.NativeText)))
        remove = menuSource.addAction(
            (_translate("MenuSource", "&Remove Line (%s)") %
                resources.get_shortcut("Remove-line").toString(
                    QKeySequence.NativeText)))

        self.toolbar_items = {
            'indent-more': indentMoreAction,
            'indent-less': indentLessAction,
            'comment': commentAction,
            'uncomment': unCommentAction,
            'go-to-definition': goToDefinitionAction,
            'insert-import': insertImport}

        goToDefinitionAction.triggered.connect(actions.Actions().editor_go_to_definition)
        countCodeLinesAction.triggered.connect(actions.Actions().count_file_code_lines)
        insertImport.triggered.connect(actions.Actions().import_from_everywhere)
        indentMoreAction.triggered.connect(actions.Actions().editor_indent_more)
        indentLessAction.triggered.connect(actions.Actions().editor_indent_less)
        commentAction.triggered.connect(actions.Actions().editor_comment)
        unCommentAction.triggered.connect(actions.Actions().editor_uncomment)
        horizontalLineAction.triggered.connect(actions.Actions().editor_insert_horizontal_line)
        titleCommentAction.triggered.connect(actions.Actions().editor_insert_title_comment)
#        QObject.connect(removeUnusedImportsAction, SIGNAL("triggered()"),
#        lambda: self._main._central.obtain_editor().remove_unused_imports())
##        QObject.connect(addMissingImportsAction, SIGNAL("triggered()"),
#        lambda: self._main._central.obtain_editor().add_missing_imports())
#        QObject.connect(organizeImportsAction, SIGNAL("triggered()"),
#        lambda: self._main._central.obtain_editor().organize_imports())
#        QObject.connect(extractMethodAction, SIGNAL("triggered()"),
#        lambda: self._main._central.obtain_editor().extract_method())
        moveUp.triggered.connect(actions.Actions().editor_move_up)
        moveDown.triggered.connect(actions.Actions().editor_move_down)
        duplicate.triggered.connect(actions.Actions().editor_duplicate)
        replaceTabsSpaces.triggered.connect(actions.Actions().editor_replace_tabs_with_spaces)
        removeTrailingSpaces.triggered.connect(actions.Actions().editor_remove_trailing_spaces)
        remove.triggered.connect(actions.Actions().editor_remove_line)
        insertPrints.triggered.connect(actions.Actions().editor_insert_debugging_prints)
        insertPdb.triggered.connect(actions.Actions().editor_insert_pdb)
