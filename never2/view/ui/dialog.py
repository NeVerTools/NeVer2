"""
Module dialog.py

This module contains all the dialog classes used in CoCoNet

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from enum import Enum
from typing import Callable

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout

import never2.resources.styling.display as disp
from never2 import RES_DIR
from never2.resources.styling.custom import CustomLabel, CustomButton, CustomTextArea, CustomComboBox, CustomTextBox
from never2.utils.validator import ArithmeticValidator


class MessageType(Enum):
    """
    This class collects the different types of messages.

    """

    ERROR = 0
    MESSAGE = 1


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

        if self.title == "":
            self.setWindowTitle("\u26a0")
        else:
            self.setWindowTitle(self.title)
        self.setModal(True)

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

    def __init__(self, title: str = 'Dialog', message: str = '', context: str = "None"):
        super(TwoButtonsDialog, self).__init__(title, message)

        self.has_been_closed = False

        if context == "None":
            self.ok_btn = CustomButton('Ok', primary=True)
        elif context == "Property":
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


class MessageDialog(SingleButtonDialog):
    """
    This class is a Dialog displaying a message to the user.

    """

    def __init__(self, message: str, message_type: MessageType):
        super().__init__('', message)

        # Set the dialog stile depending on message_type
        if message_type == MessageType.MESSAGE:
            title_label = CustomLabel('Message', alignment=Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet(disp.NODE_LABEL_STYLE)
        else:
            title_label = CustomLabel('Error', alignment=Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet(disp.ERROR_LABEL_STYLE)

        # Set content label
        mess_label = CustomLabel(f"\n{self.content}\n", alignment=Qt.AlignmentFlag.AlignCenter)

        # Compose widgets
        self.layout.addWidget(title_label)
        self.layout.addWidget(mess_label)

        self.render_layout()


class FuncDialog(TwoButtonsDialog):
    """
    This class is a parametric Dialog displaying a message
    to the user and executing a function if the user clicks
    'Ok'.

    """

    def __init__(self, message: str, ok_fun: Callable):
        super().__init__('', message)
        title_label = CustomLabel('Message', alignment=Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(disp.NODE_LABEL_STYLE)
        # Set content label
        mess_label = CustomLabel(f"\n{self.content}\n", alignment=Qt.AlignmentFlag.AlignCenter)

        # Connect function
        self.ok_btn.clicked.connect(lambda: ok_fun)

        self.layout.addWidget(title_label)
        self.layout.addWidget(mess_label)

        self.render_layout()


class ConfirmDialog(TwoButtonsDialog):
    """
    This dialog asks the user the confirmation to clear the
    unsaved workspace before continue.

    Attributes
    ----------
    confirm : bool
        Boolean value to store user decision

    """

    def __init__(self, title, message):
        super().__init__(title, message)

        # Set title label
        title_label = CustomLabel('Warning', alignment=Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(disp.NODE_LABEL_STYLE)

        # Set message label
        mess_label = CustomLabel(f"\n{self.content}\n", alignment=Qt.AlignmentFlag.AlignCenter)

        self.confirm = False
        self.has_been_closed = False

        # Add buttons to close the dialog
        self.ok_btn.clicked.connect(self.ok)
        self.cancel_btn.clicked.connect(self.deny)

        # Compose widgets
        self.layout.addWidget(title_label)
        self.layout.addWidget(mess_label)

        self.render_layout()

    def ok(self):
        self.confirm = True

    def deny(self):
        self.confirm = False

    def closeEvent(self, event):
        self.has_been_closed = True
        self.close()


class EditSmtPropertyDialog(TwoButtonsDialog):
    """
    This dialog allows to define a generic SMT property
    by writing directly in the SMT-LIB language.

    Attributes
    ----------
    property_block : PropertyBlock
        Current property to edit.
    new_property_str : str
        New SMT-LIB property string.
    smt_box : CustomTextArea
        Input box.
    has_edits : bool
        Flag signaling if the property was edited.

    Methods
    ----------
    save_data()
        Procedure to return the new property.

    """

    def __init__(self, property_block: 'PropertyBlock', context: str = 'Property'):
        super().__init__('Edit property', '', context=context)
        self.property_block = property_block
        self.new_property_str = self.property_block.smt_string
        self.has_edits = False

        g_layout = QGridLayout()
        self.layout.addLayout(g_layout)

        # apply same QLineEdit and QComboBox style of the block contents
        qss_file = open(RES_DIR + '/styling/qss/blocks.qss').read()
        self.setStyleSheet(qss_file)

        # Build main_layout
        title_label = CustomLabel('SMT property', context='Property')
        title_label.setStyleSheet(disp.PROPERTY_LABEL_STYLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        g_layout.addWidget(title_label, 0, 0, 1, 2)

        # Input box
        smt_label = CustomLabel('SMT-LIB definition', context='Property')
        smt_label.setStyleSheet(disp.PROPERTY_IN_DIM_LABEL_STYLE)
        smt_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        g_layout.addWidget(smt_label, 1, 0)

        self.smt_box = CustomTextArea()
        self.smt_box.insertPlainText(self.new_property_str)
        g_layout.addWidget(self.smt_box, 1, 1)

        self.set_buttons_text('Discard', 'Apply')
        self.ok_btn.clicked.connect(self.save_data)

        self.render_layout()

    def save_data(self):
        self.has_edits = True
        self.new_property_str = self.smt_box.toPlainText().strip()


class EditPolyhedralPropertyDialog(BaseDialog):
    """
    This dialog allows to define a polyhedral property
    within a controlled environment.

    Attributes
    ----------
    property_block : PropertyBlock
        Current property to edit.
    property_list : list
        List of given properties.
    has_edits : bool
        Flag signaling if the property was edited.
    viewer : CustomTextArea
        A CustomTextArea that shows the constraints

    Methods
    ----------
    add_entry(str, str, str)
        Procedure to append the current constraint to the property list.

    save_property()
        Procedure to return the defined property.

    show_properties_viewer()
        Show the viewer, a TextArea, listing the constraints

    """

    def __init__(self, property_block: 'PropertyBlock'):
        super().__init__('Edit property', '')
        self.property_block = property_block
        self.has_edits = False
        self.property_list = []
        self.viewer = CustomTextArea()
        self.viewer.setReadOnly(True)
        self.viewer.setMinimumHeight(100)
        self.show_properties_viewer()
        grid = QGridLayout()

        # apply same QLineEdit and QComboBox style of the block contents
        qss_file = open(RES_DIR + '/styling/qss/blocks.qss').read()
        self.setStyleSheet(qss_file)

        # Build main_layout
        title_label = CustomLabel('Polyhedral property', primary=True, context='Property')
        grid.addWidget(title_label, 0, 0, 1, 3)

        # Labels
        var_label = CustomLabel('Variable', primary=True, context='Property')
        grid.addWidget(var_label, 1, 0)

        relop_label = CustomLabel('Operator', primary=True, context='Property')
        grid.addWidget(relop_label, 1, 1)

        value_label = CustomLabel('Value', primary=True, context='Property')
        grid.addWidget(value_label, 1, 2)

        self.var_cb = CustomComboBox(context='Property')
        for v in property_block.variables:
            self.var_cb.addItem(v)
        grid.addWidget(self.var_cb, 2, 0)

        self.op_cb = CustomComboBox(context='Property')
        operators = ['<=', '<', '>', '>=']
        for o in operators:
            self.op_cb.addItem(o)
        grid.addWidget(self.op_cb, 2, 1)

        self.val = CustomTextBox(context='Property')
        self.val.setValidator(ArithmeticValidator.FLOAT)
        grid.addWidget(self.val, 2, 2)

        add_button = CustomButton('Add', context='Property')
        add_button.clicked.connect(self.add_entry)
        grid.addWidget(add_button, 3, 0)

        # 'Cancel' button which closes the dialog without saving
        cancel_button = CustomButton('Cancel')
        cancel_button.clicked.connect(self.close)
        grid.addWidget(cancel_button, 3, 1)

        # 'Save' button which saves the state
        save_button = CustomButton('Save', primary=True, context='Property')
        save_button.clicked.connect(self.save_property)
        grid.addWidget(save_button, 3, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        self.layout.addLayout(grid)
        self.layout.addWidget(self.viewer, 3)
        self.render_layout()

    def add_entry(self) -> None:
        self.val.clearFocus()
        var = self.var_cb.currentText()
        op = self.op_cb.currentText()
        val = self.val.text()
        if val == '':
            dialog = MessageDialog('Value not added. Please try again', MessageType.ERROR)
            dialog.exec()
            return
        self.property_list.append((var, op, val))
        self.viewer.appendPlainText(f'{var} {op} {val}')
        self.var_cb.setCurrentIndex(0)
        self.op_cb.setCurrentIndex(0)
        self.val.setText('')

    def save_property(self) -> None:
        self.has_edits = True
        if self.val.text() != '':
            self.add_entry()
        self.close()

    def show_properties_viewer(self):
        if self.property_block.label_string:
            self.viewer.appendPlainText(self.property_block.label_string)
