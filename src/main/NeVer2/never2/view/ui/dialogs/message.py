"""
Module message.py

This module contains all the message dialog classes used in NeVer2

Author: Stefano Demarchi

"""

from enum import Enum
from typing import Callable

import never2.resources.styling.display as disp
from never2.resources.styling.custom import CustomLabel
from never2.view.ui.dialogs.dialog import SingleButtonDialog, TwoButtonsDialog

from PyQt6.QtCore import Qt

class MessageType(Enum):
    """
    This class collects the different types of messages.

    """

    ERROR = 0
    MESSAGE = 1


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

class YesNoDialog(TwoButtonsDialog):
    """
    This class is a Dialog displaying a Yes/No choice
    to the user and returning the result of the choice
    """
    def __init__(self, message: str):
        super().__init__('', message)
        title_label = CustomLabel('Message', alignment=Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(disp.NODE_LABEL_STYLE)

        # Change button texts
        self.set_buttons_text("No", "Yes")

        # Set content label
        mess_label = CustomLabel(f"\n{self.content}\n", alignment=Qt.AlignmentFlag.AlignCenter)

        # Replace default signal behavior
        self.ok_btn.clicked.disconnect()
        self.cancel_btn.clicked.disconnect()

        # Result attribute
        self.result = None

        # Connect new signals
        self.ok_btn.clicked.connect(self.on_yes)
        self.cancel_btn.clicked.connect(self.on_no)

        self.layout.addWidget(title_label)
        self.layout.addWidget(mess_label)

        self.render_layout()

    def on_yes(self):
        self.result = True
        self.accept()  # closes the dialog

    def on_no(self):
        self.result = False
        self.reject()  # closes the dialog

    def get_result(self):
        return self.result

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
