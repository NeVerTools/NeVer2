"""
Module custom.py

This module defines custom UI component with pre-defined style

Author: Stefano Demarchi

"""
import logging

from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QLabel, QComboBox, QLineEdit, QPlainTextEdit, QPushButton, QListWidget, QAbstractItemView, \
    QDialog, QVBoxLayout

import never2.resources.styling.display as disp
import never2.resources.styling.palette as palette


class CustomButton(QPushButton):
    def __init__(self, text: str = '', primary: bool = False, context: str = None):
        super(CustomButton, self).__init__(text)
        if primary:
            self.setStyleSheet(disp.PRIMARY_BUTTON_STYLE)
            self.setDefault(True)
        else:
            self.setStyleSheet(disp.BUTTON_STYLE)
            self.setDefault(False)

        if context == 'FunctionalBlock':
            if text == 'Add property':
                self.setStyleSheet(disp.PROPERTY_BUTTON_STYLE)
            elif text == 'Update':
                self.setStyleSheet(disp.UPDATE_FUNC_BUTTON_STYLE)
        elif context == 'LayerBlock':
            if primary:
                self.setStyleSheet(disp.SAVE_LAYER_BUTTON_STYLE)
            else:
                self.setStyleSheet(disp.BUTTON_STYLE)
        elif context == 'Property':
            if text == 'Add':
                self.setStyleSheet(disp.PRIMARY_BUTTON_STYLE)
            elif text == 'Save':
                self.setStyleSheet(disp.PROPERTY_BUTTON_STYLE)


class CustomLabel(QLabel):
    def __init__(self, text: str = '', color: str = 'white', primary: bool = False,
                 alignment=Qt.AlignmentFlag.AlignLeft, context: str = ''):
        super(CustomLabel, self).__init__(text)
        if primary:
            self.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.setStyleSheet(disp.NODE_LABEL_STYLE)
        else:
            self.setAlignment(alignment)
            self.setStyleSheet('color: ' + color + ';' +
                               'border: none;' +
                               'padding: 2px 0px 2px 2px;')

        if context == 'Property':
            self.setStyleSheet(disp.PROPERTY_LABEL_STYLE)


class CustomComboBox(QComboBox):
    def __init__(self, color: str = 'white', context: str = 'LayerBlock'):
        super(CustomComboBox, self).__init__()

        if context == 'LayerBlock':
            self.setStyleSheet('border: 2px solid' + palette.DARK_BLUE + ';')

        elif context == 'FunctionalBlock':
            self.setStyleSheet('border: 2px solid' + palette.GREY + ';')

        elif context == 'Property':
            self.setStyleSheet('border: 2px solid' + palette.DARK_ORANGE + ';')

    def text(self) -> str:
        return self.currentText()

    def setText(self, text: str) -> None:
        self.setCurrentText(text)


class CustomTextBox(QLineEdit):
    def __init__(self, text: str = '', color: str = 'white', context: str = None):
        super(CustomTextBox, self).__init__()
        self.setText(text)

        if context == 'LayerBlock':
            self.setStyleSheet('border: 2px solid' + palette.DARK_BLUE + ';')

        elif context == 'FunctionalBlock':
            self.setStyleSheet('border: 2px solid' + palette.GREY + ';')

        elif context == 'Property':
            self.setStyleSheet('border: 2px solid' + palette.DARK_ORANGE + ';')


class CustomTextArea(QPlainTextEdit):
    def __init__(self, color: str = palette.WHITE, parent=None):
        super(CustomTextArea, self).__init__(parent)
        self.setStyleSheet('color: ' + color + ';' +
                           'background-color: ' + palette.GREY_2 + ';' +
                           'border: none;' +
                           'padding: 2px;' +
                           'QPlainTextEdit::placeholder {' +
                           'color: ' + palette.GREY_4 + ';' +
                           '}')


class CustomLoggingHandler(QObject, logging.Handler):
    """Custom logging handler to emit signals."""

    log_signal = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)


class CustomLoggerDialog(QDialog):
    """Dialog to display log messages."""

    def __init__(self, title: str, parent=None):
        super(CustomLoggerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 300)

        self.log_text_edit = CustomTextArea(parent=parent)
        self.log_text_edit.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.log_text_edit)
        self.setLayout(layout)

    def add_log_message(self, message):
        self.log_text_edit.appendPlainText(message)


class CustomListBox(QListWidget):
    def __init__(self, color: str = palette.WHITE):
        super(QListWidget, self).__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setStyleSheet('color: ' + color + ';' +
                           'background-color: ' + palette.GREY_2 + ';' +
                           'border: none;' +
                           'padding: 2px;' +
                           'QListWidget::placeholder {' +
                           'color: ' + palette.GREY_4 + ';' +
                           '}')
