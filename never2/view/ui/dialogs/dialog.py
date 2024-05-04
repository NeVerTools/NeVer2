"""
Module dialog.py

This module contains all the base dialog classes used in NeVer2

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout

from never2 import RES_DIR
from never2.resources.styling.custom import CustomLabel, CustomButton, CustomComboBox, CustomTextBox


class BaseDialog(QtWidgets.QDialog):
    """
    Base class for grouping common elements of the dialogs.
    Each dialog shares a main_layout (vertical by default), a title
    and a string content.

    Attributes
    ----------
    layout : QVBoxLayout
        The main main_layout of the dialog.
    title : str
        The dialog title.
    content : str
        The dialog content.

    Methods
    ----------
    render_layout()
        Procedure to update the main_layout.

    """

    def __init__(self, title='Dialog', message='Message', parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.title = title
        self.content = message

        if self.title == '':
            self.setWindowTitle("\u26a0")
        else:
            self.setWindowTitle(self.title)
        self.setModal(True)

        # apply same QLineEdit and QComboBox style of the block contents
        qss_file = open(RES_DIR + '/styling/qss/blocks.qss').read()
        self.setStyleSheet(qss_file)

    def set_title(self, title: str) -> None:
        """
        This method updates the dialog title.

        Parameters
        ----------
        title : str
            New title to display.

        """

        self.title = title
        self.setWindowTitle(self.title)

    def set_content(self, content: str) -> None:
        """
        This method updates the dialog content.

        Parameters
        ----------
        content : str
            New content to display.

        """

        self.content = content

    def render_layout(self) -> None:
        """
        This method updates the main_layout with the changes done
        in the child class(es).

        """

        self.setLayout(self.layout)


class SingleButtonDialog(BaseDialog):
    """
    This class is a generic dialog with a single button
    at the bottom of the main layout. It also provides
    a method for imposing the button text ('Ok' by default)

    Attributes
    ----------
    button : CustomButton
        A single button for leaving the dialog

    Methods
    ----------
    set_button_text(str)
        A method for setting the button text

    """

    def __init__(self, title: str = 'Dialog', message: str = ''):
        super(SingleButtonDialog, self).__init__(title, message)
        self.button = CustomButton('Ok', primary=True)
        self.button.clicked.connect(self.close)

    def set_button_text(self, text: str):
        self.button.setText(text)

    def render_layout(self) -> None:
        """
        Override with a button at the end

        """

        self.layout.addWidget(self.button)
        self.setLayout(self.layout)


class TwoButtonsDialog(BaseDialog):
    """
    This class is a generic dialog with two buttons
    at the bottom of the main layout, for accepting or
    refusing the operations of the dialog. It also provides
    a method for imposing the buttons text ('Cancel' and 'Ok'
    by default)

    Attributes
    ----------
    cancel_btn : CustomButton
        A single button for leaving the dialog without applying
        the changes
    ok_btn : CustomButton
        A single button for leaving the dialog and applying
        the changes

    Methods
    ----------
    set_buttons_text(str, str)
        A method for setting the buttons text

    """

    def __init__(self, title: str = 'Dialog', message: str = '', context: str = 'None'):
        super(TwoButtonsDialog, self).__init__(title, message)

        self.has_been_closed = False

        if context == 'None':
            self.ok_btn = CustomButton('Ok', primary=True)
        elif context == 'Property':
            self.ok_btn = CustomButton('Save', context=context)
        self.cancel_btn = CustomButton('Cancel')
        self.cancel_btn.clicked.connect(self.accept)
        self.ok_btn.clicked.connect(self.reject)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.cancel_btn)
        self.button_layout.addWidget(self.ok_btn)

    def set_buttons_text(self, cancel_text: str, ok_text: str):
        self.cancel_btn.setText(cancel_text)
        self.ok_btn.setText(ok_text)

    def render_layout(self) -> None:
        """
        Override with a button at the end

        """

        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)


class GenericDatasetDialog(TwoButtonsDialog):
    """
    This class is a simple dialog asking for additional
    parameters of a generic file dataset.
    Attributes
    ----------
    params : dict
        Dictionary of parameters to ask.
    Methods
    ----------
    update_dict(str, str)
        Procedure to read the given input and save it
    reset()
        Procedure to restore the parameters to default

    """

    def __init__(self):
        super().__init__('Dataset - additional parameters', '')
        g_layout = QGridLayout()
        self.layout.addLayout(g_layout)
        self.params = {'data_type': float,
                       'delimiter': ','}

        data_type_label = CustomLabel('Data type')
        data_type_edit = CustomComboBox()
        data_type_edit.addItems(['float', 'int'])
        data_type_edit.activated. \
            connect(lambda: self.update_dict('data_type', data_type_edit.currentText()))
        g_layout.addWidget(data_type_label, 0, 0)
        g_layout.addWidget(data_type_edit, 0, 1)

        delimiter_label = CustomLabel('Delimiter character')
        delimiter_edit = CustomTextBox(',')
        delimiter_edit.textChanged. \
            connect(lambda: self.update_dict('delimiter', delimiter_edit.text()))
        g_layout.addWidget(delimiter_label, 1, 0)
        g_layout.addWidget(delimiter_edit, 1, 1)

        self.cancel_btn.clicked.connect(self.reset)
        self.render_layout()

    def update_dict(self, key: str, value: str):
        if key in self.params.keys():
            if key == "delimiter":
                self.params[key] = value
            else:
                if value != '':
                    self.params[key] = eval(value)

    def reset(self):
        self.params = {'data_type': float,
                       'delimiter': ','}
