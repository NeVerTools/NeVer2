"""
Module tabs.py

This module contains the custom widget and methods for a tab layout

Author: Stefano Demarchi

"""

from PyQt6.QtWidgets import QTabWidget, QWidget, QFormLayout

from never2.resources.styling.custom import CustomComboBox, CustomTextBox
from never2.utils.validator import ArithmeticValidator


class VerificationTabWidget(QTabWidget):

    def __init__(self, content: dict = None, parent=None):
        super().__init__(parent)
        self.content_dict = content
        self.widgets_dict = {}

        # Init tabs
        self.build_tabs()

    def build_tabs(self):
        """
        This method builds the widget layout based on the provided content dictionary

        """

        tabs = []
        layouts = []

        # Add a new tab for each algorithm (key of the values for 'Verification Strategy')
        algo_names = [name for name in self.content_dict['Verification strategy'].keys()]

        for name in algo_names:
            # Make a new layout and tab
            layouts.append(QFormLayout())
            tabs.append(QWidget(self))

            cur_layout = layouts[-1]

            # Refer to the last added in the loop
            tabs[-1].setLayout(cur_layout)

            params_dict = self.content_dict['Verification strategy'][name]['params']

            # Populate the tab
            for param in params_dict.keys():
                param_name = params_dict[param]['name']

                # Create the correct widget for entry (ComboBox or Line)
                if 'allowed' in params_dict[param].keys():
                    self.widgets_dict[f'{name}:{param_name}'] = CustomComboBox()
                    self.widgets_dict[f'{name}:{param_name}'].addItems(params_dict[param]['allowed'])
                    self.widgets_dict[f'{name}:{param_name}'].setCurrentIndex(
                        params_dict[param]['allowed'].index(params_dict[param]['value']))

                elif params_dict[param]['type'] == 'int':
                    self.widgets_dict[f'{name}:{param_name}'] = CustomTextBox()
                    self.widgets_dict[f'{name}:{param_name}'].setText(str(params_dict[param]['value']))
                    self.widgets_dict[f'{name}:{param_name}'].setValidator(ArithmeticValidator.INT)

                # Add the widget
                cur_layout.addRow(param, self.widgets_dict[f'{name}:{param_name}'])

            # Add the tab to the widget
            self.addTab(tabs[-1], name)

    def get_params(self) -> tuple[str, dict]:
        """
        This method returns a clean dictionary associating the parameters value
        of the current tab, as well as the tab name

        Returns
        -------
        tuple[str, dict]

        """

        params = {}
        strategy_name = list(self.content_dict['Verification strategy'].keys())[self.currentIndex()]

        for k, v in self.widgets_dict.items():
            if strategy_name in k:
                params[k.replace(f'{strategy_name}:', '')] = v.text()

        return strategy_name, params
