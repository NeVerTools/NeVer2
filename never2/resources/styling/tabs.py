"""
Module tabs.py

This module contains the custom widget and methods for a tab layout

Author: Stefano Demarchi

"""

from PyQt6.QtWidgets import QTabWidget, QWidget, QFormLayout, QLineEdit


class CustomTabWidget(QTabWidget):

    def __init__(self, content: dict = None, parent=None):
        super().__init__(parent)
        self.content_dict = content

        # Init tabs
        self.build_tabs()

    def build_tabs(self):
        """
        This method builds the widget layout based on the provided content dictionary

        """

        page = QWidget(self)
        layout = QFormLayout()
        page.setLayout(layout)
        layout.addRow('Phone Number:', QLineEdit(self))
        layout.addRow('Email Address:', QLineEdit(self))
        layout.addRow('Email Address:', QLineEdit(self))

        self.addTab(page, 'Tab 1')

    def get_params(self) -> tuple:
        pass

