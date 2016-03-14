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



import time
import re

from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QTextCursor
from PyQt5.QtGui import QTextCharFormat
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QProcess
from PyQt5.QtCore import QProcessEnvironment
from PyQt5.QtCore import QFile
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QCoreApplication


from ninja_ide import resources
from ninja_ide.core import settings
from ninja_ide.core import file_manager
from ninja_ide.gui.main_panel import main_container

_translate = QCoreApplication.translate


class RunWidget(QWidget):

    """Widget that show the execution output in the MiscContainer."""

    def __init__(self):
        super(RunWidget, self).__init__()
        vbox = QVBoxLayout(self)
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)
        self.output = OutputWidget(self)
        hbox = QHBoxLayout()
        self.input = QLineEdit()
        self.lblInput = QLabel(_translate("RunWidget", "Input:"))
        vbox.addWidget(self.output)
        hbox.addWidget(self.lblInput)
        hbox.addWidget(self.input)
        vbox.addLayout(hbox)

        self.set_font(settings.FONT_FAMILY, settings.FONT_SIZE)

        #process
        self.currentProcess = None
        self.__preScriptExecuted = False
        self._proc = QProcess(self)
        self._preExecScriptProc = QProcess(self)
        self._postExecScriptProc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self.output._refresh_output)
        self._proc.readyReadStandardError.connect(self.output._refresh_error)
        self._proc.finished[int, 'QProcess::ExitStatus'].connect(self.finish_execution)
        self._proc.error['QProcess::ProcessError'].connect(self.process_error)
        self.input.returnPressed.connect(self.insert_input)
        self._preExecScriptProc.finished[int, 'QProcess::ExitStatus'].connect(self.__main_execution)
        self._preExecScriptProc.readyReadStandardOutput.connect(self.output._refresh_output)
        self._preExecScriptProc.readyReadStandardError.connect(self.output._refresh_error)
        self._postExecScriptProc.finished[int, 'QProcess::ExitStatus'].connect(self.__post_execution_message)
        self._postExecScriptProc.readyReadStandardOutput.connect(self.output._refresh_output)
        self._postExecScriptProc.readyReadStandardError.connect(self.output._refresh_error)

    def set_font(self, family, size):
        font = QFont(family, size)
        self.output.document().setDefaultFont(font)
        self.output.plain_format.setFont(font)
        self.output.error_format.setFont(font)

    def process_error(self, error):
        """Listen to the error signals from the running process."""
        self.lblInput.hide()
        self.input.hide()
        self._proc.kill()
        format_ = QTextCharFormat()
        format_.setAnchor(True)
        format_.setForeground(QBrush(QColor(resources.CUSTOM_SCHEME.get(
            "error-underline", resources.COLOR_SCHEME["error-underline"]))))
        if error == 0:
            self.output.textCursor().insertText(_translate("RunWidget", 'Failed to start'),
                format_)
        else:
            self.output.textCursor().insertText(
                (_translate("RunWidget", 'Error during execution, QProcess error: %d') % error),
                format_)

    def finish_execution(self, exitCode, exitStatus):
        """Print a message and hide the input line when the execution ends."""
        self.lblInput.hide()
        self.input.hide()
        format_ = QTextCharFormat()
        format_.setAnchor(True)
        self.output.textCursor().insertText('\n\n')
        if exitStatus == QProcess.NormalExit:
            format_.setForeground(QBrush(QColor(resources.CUSTOM_SCHEME.get(
            "keyword", resources.COLOR_SCHEME["keyword"]))))
            self.output.textCursor().insertText(
                _translate("RunWidget", "Execution Successful!"), format_)
        else:
            format_.setForeground(QBrush(QColor(resources.CUSTOM_SCHEME.get(
            "error-underline", resources.COLOR_SCHEME["error-underline"]))))
            self.output.textCursor().insertText(
                _translate("RunWidget", "Execution Interrupted"), format_)
        self.output.textCursor().insertText('\n\n')
        self.__post_execution()

    def insert_input(self):
        """Take the user input and send it to the process."""
        text = self.input.text() + '\n'
        self._proc.writeData(text)
        self.output.textCursor().insertText(text, self.output.plain_format)
        self.input.setText("")
        self.set_font(settings.FONT_FAMILY, settings.FONT_SIZE)

    def start_process(self, fileName, pythonPath=False, PYTHONPATH=None,
        programParams='', preExec='', postExec=''):

        """Prepare the output widget and start the process."""
        self.lblInput.show()
        self.input.show()
        self.fileName = fileName
        self.pythonPath = pythonPath  # FIXME, this is python interpreter
        self.programParams = programParams
        self.preExec = preExec
        self.postExec = postExec
        self.PYTHONPATH = PYTHONPATH

        self.__pre_execution()

    def __main_execution(self):
        """Execute the project."""
        self.output.setCurrentCharFormat(self.output.plain_format)
        message = ''
        if self.__preScriptExecuted:
            self.__preScriptExecuted = False
            message = _translate("RunWidget", 
                "Pre Execution Script Successfully executed.\n\n")
        self.output.setPlainText(message + 'Running: %s (%s)\n\n' %
            (self.fileName, time.ctime()))
        self.output.moveCursor(QTextCursor.Down)
        self.output.moveCursor(QTextCursor.Down)
        self.output.moveCursor(QTextCursor.Down)

        #runner.run_code_from_file(fileName)
        if not self.pythonPath:
            self.pythonPath = settings.PYTHON_PATH
        #change the working directory to the fileName dir
        file_directory = file_manager.get_folder(self.fileName)
        self._proc.setWorkingDirectory(file_directory)
        #force python to unbuffer stdin and stdout
        options = ['-u'] + settings.EXECUTION_OPTIONS.split()
        self.currentProcess = self._proc

        env = QProcessEnvironment()
        system_environemnt = self._proc.systemEnvironment()
        for e in system_environemnt:
            key, value = e.split('=', 1)
            env.insert(key, value)
        if self.PYTHONPATH:
            envpaths = [path for path in self.PYTHONPATH.splitlines()]
            for path in envpaths:
                env.insert('PYTHONPATH', path)
        env.insert('PYTHONIOENCODING', 'utf-8')
        self._proc.setProcessEnvironment(env)

        self._proc.start(self.pythonPath, options + [self.fileName] +
            [p.strip() for p in self.programParams.split(',') if p])

    def __pre_execution(self):
        """Execute a script before executing the project."""
        filePreExec = QFile(self.preExec)
        if filePreExec.exists() and \
          bool(QFile.ExeUser & filePreExec.permissions()):
            ext = file_manager.get_file_extension(self.preExec)
            if not self.pythonPath:
                self.pythonPath = settings.PYTHON_PATH
            self.currentProcess = self._preExecScriptProc
            self.__preScriptExecuted = True
            if ext == 'py':
                self._preExecScriptProc.start(self.pythonPath, [self.preExec])
            else:
                self._preExecScriptProc.start(self.preExec)
        else:
            self.__main_execution()

    def __post_execution(self):
        """Execute a script after executing the project."""
        filePostExec = QFile(self.postExec)
        if filePostExec.exists() and \
          bool(QFile.ExeUser & filePostExec.permissions()):
            ext = file_manager.get_file_extension(self.postExec)
            if not self.pythonPath:
                self.pythonPath = settings.PYTHON_PATH
            self.currentProcess = self._postExecScriptProc
            if ext == 'py':
                self._postExecScriptProc.start(self.pythonPath,
                    [self.postExec])
            else:
                self._postExecScriptProc.start(self.postExec)

    def __post_execution_message(self):
        """Print post execution message."""
        self.output.textCursor().insertText('\n\n')
        format_ = QTextCharFormat()
        format_.setAnchor(True)
        format_.setForeground(Qt.green)
        self.output.textCursor().insertText(
            _translate("RunWidget", "Post Execution Script Successfully executed."), format_)

    def kill_process(self):
        """Kill the running process."""
        self._proc.kill()


class OutputWidget(QPlainTextEdit):

    def __init__(self, parent):
        super(OutputWidget, self).__init__(parent)
        self._parent = parent
        self.setReadOnly(True)
        self.maxValue = 0
        self.actualValue = 0
        #traceback pattern
        self.patLink = re.compile(r'(\s)*File "(.*?)", line \d.+')
        #formats
        font = QFont(settings.FONT_FAMILY, settings.FONT_SIZE)
        self.plain_format = QTextCharFormat()
        self.plain_format.setFont(font)
        self.plain_format.setForeground(QBrush(QColor(
            resources.CUSTOM_SCHEME.get("editor-text",
            resources.COLOR_SCHEME["editor-text"]))))
        self.error_format = QTextCharFormat()
        self.error_format.setFont(font)
        self.error_format.setAnchor(True)
        self.error_format.setFontUnderline(True)
        self.error_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.error_format.setUnderlineColor(Qt.red)
        self.error_format.setForeground(Qt.blue)
        self.error_format.setToolTip(_translate("OutputWidget", "Click to show the source"))

        self.blockCountChanged[int].connect(self._scroll_area)

        css = 'QPlainTextEdit {color: %s; background-color: %s;' \
            'selection-color: %s; selection-background-color: %s;}' \
            % (resources.CUSTOM_SCHEME.get('editor-text',
            resources.COLOR_SCHEME['editor-text']),
            resources.CUSTOM_SCHEME.get('editor-background',
                resources.COLOR_SCHEME['editor-background']),
            resources.CUSTOM_SCHEME.get('editor-selection-color',
                resources.COLOR_SCHEME['editor-selection-color']),
            resources.CUSTOM_SCHEME.get('editor-selection-background',
                resources.COLOR_SCHEME['editor-selection-background']))
        self.setStyleSheet(css)

    def _scroll_area(self):
        """When new text is added to the widget, move the scroll to the end."""
        if self.actualValue == self.maxValue:
            self.moveCursor(QTextCursor.End)

    def mousePressEvent(self, event):
        """
        When the execution fail, allow to press the links in the traceback,
        to go to the line when the error occur.
        """
        QPlainTextEdit.mousePressEvent(self, event)
        self.go_to_error(event)

    def _refresh_output(self):
        """Read the output buffer from the process and append the text."""
        #we should decode the bytes!
        currentProcess = self._parent.currentProcess
        text = currentProcess.readAllStandardOutput().data().decode('utf8')
        verticalScroll = self.verticalScrollBar()
        self.actualValue = verticalScroll.value()
        self.maxValue = verticalScroll.maximum()
        self.textCursor().insertText(text, self.plain_format)

    def _refresh_error(self):
        """Read the error buffer from the process and append the text."""
        #we should decode the bytes!
        cursor = self.textCursor()
        currentProcess = self._parent.currentProcess
        text = currentProcess.readAllStandardError().data().decode('utf8')
        text_lines = text.split('\n')
        verticalScroll = self.verticalScrollBar()
        self.actualValue = verticalScroll.value()
        self.maxValue = verticalScroll.maximum()
        for t in text_lines:
            cursor.insertBlock()
            if self.patLink.match(t):
                cursor.insertText(t, self.error_format)
            else:
                cursor.insertText(t, self.plain_format)

    def go_to_error(self, event):
        """Resolve the link and take the user to the error line."""
        cursor = self.cursorForPosition(event.pos())
        text = cursor.block().text()
        if self.patLink.match(text):
            file_path, lineno = self._parse_traceback(text)
            main = main_container.MainContainer()
            main.open_file(file_path)
            main.editor_jump_to_line(lineno=int(lineno) - 1)

    def _parse_traceback(self, text):
        """
        Parse a line of python traceback and returns
        a tuple with (file_name, lineno)
        """
        file_word_index = text.find('File')
        comma_min_index = text.find(',')
        comma_max_index = text.rfind(',')
        file_name = text[file_word_index + 6:comma_min_index - 1]
        lineno = text[comma_min_index + 7:comma_max_index]
        return (file_name, lineno)

    def contextMenuEvent(self, event):
        """Show a context menu for the Plain Text widget."""
        popup_menu = self.createStandardContextMenu()

        menuOutput = QMenu(_translate("OutputWidget", "Output"))
        cleanAction = menuOutput.addAction(_translate("OutputWidget", "Clean"))
        popup_menu.insertSeparator(popup_menu.actions()[0])
        popup_menu.insertMenu(popup_menu.actions()[0], menuOutput)

        # This is a hack because if we leave the widget text empty
        # it throw a violent segmentation fault in start_process
        cleanAction.triggered.connect(lambda: self.setPlainText('\n\n'))

        popup_menu.exec_(event.globalPos())
