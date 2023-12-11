"""
Module action.py

This module contains all the action dialog classes used in NeVer2

Author: Stefano Demarchi

"""

import torch
import torchvision.transforms as tr
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout

from never2 import RES_DIR
from never2.resources.styling.custom import CustomListBox, CustomButton, CustomLabel, CustomTextBox
from never2.utils import rep
from never2.utils.validator import ArithmeticValidator
from never2.view.ui.dialogs.dialog import TwoButtonsDialog


class ComposeTransformDialog(TwoButtonsDialog):
    """
    This class allows for the composition of a custom
    dataset transform.
    Attributes
    ----------
    trList : list
        List of transform objects selected by the user.
    Methods
    ----------
    initUI()
        Setup of graphical elements
    add_transform()
        Adds a transform object from a ListView to another
    rm_transform()
        Removes a transform object from a ListView
    ok()
        Fills the trList parameter to return
    """

    def __init__(self):
        super().__init__('Dataset transform - composition', '')
        # List to return
        self.trList = []

        # 2-level parameters of the transforms
        self.params_2level = {}

        # Widgets
        self.available = CustomListBox()
        self.selected = CustomListBox()
        self.add_btn = CustomButton('>')
        self.rm_btn = CustomButton('<')
        self.add_btn.clicked.connect(self.add_transform)
        self.rm_btn.clicked.connect(self.rm_transform)

        # Init data
        self.init_layout()

        # Buttons
        self.ok_btn.clicked.connect(self.ok)
        self.cancel_btn.clicked.connect(self.trList.clear)

        self.render_layout()

    def init_layout(self):
        """
        Initialize the dialog layout with two ListViews and two
        buttons in the middle for the composition
        """

        # Setup layouts
        tr_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        label1 = CustomLabel('Available', primary=True)
        left_layout.addWidget(label1)
        left_layout.addWidget(self.available)

        mid_layout = QVBoxLayout()
        mid_layout.addWidget(self.add_btn)
        mid_layout.addWidget(self.rm_btn)
        mid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout = QVBoxLayout()
        label2 = CustomLabel('Selected', primary=True)
        right_layout.addWidget(label2)
        right_layout.addWidget(self.selected)

        tr_layout.addLayout(left_layout)
        tr_layout.addLayout(mid_layout)
        tr_layout.addLayout(right_layout)
        self.layout.addLayout(tr_layout)

        transform = rep.read_json(RES_DIR + '/json/transform.json')
        for t in transform.keys():
            self.available.addItem(t)

            if transform[t]:
                self.params_2level[t] = {}
                for k, v in transform[t].items():
                    self.params_2level[t][k] = v

    def add_transform(self):
        """
        This method takes the selected transform in the 'available' list
        and moves it to the 'selected' one
        """

        item = self.available.currentItem()
        if item is not None:
            self.selected.addItem(item.text())
            self.available.setCurrentItem(None)
            item.setHidden(True)

            if item.text() in self.params_2level.keys():
                # If the transform has parameters, ask now
                d = Param2levelDialog(self.params_2level[item.text()], item.text())
                d.exec()

                for k in d.params.keys():
                    self.params_2level[item.text()][k]['value'] = d.params[k]

    def rm_transform(self):
        """
        This method removes the selected transform from the 'selected'
        list and re-enables it in the 'available' one
        """

        item = self.selected.currentItem()
        if item is not None:
            self.available.findItems(item.text(), Qt.MatchFlag.MatchExactly)[0].setHidden(False)
            self.selected.takeItem(self.selected.row(item))

    def ok(self):
        """
        This method reads the 'selected' list view and fills the
        trList list with the corresponding dataset transforms
        """

        for idx in range(self.selected.count()):
            t = self.selected.item(idx).text()
            if t == 'ToTensor':
                self.trList.append(tr.ToTensor())
            elif t == 'PILToTensor':
                self.trList.append(tr.PILToTensor())
            elif t == 'Normalize':
                self.trList.append(tr.Normalize(self.params_2level['Normalize']['Mean']['value'],
                                                self.params_2level['Normalize']['Std deviation']['value']))
            elif t == 'Flatten':
                self.trList.append(tr.Lambda(lambda x: torch.flatten(x)))
            elif t == 'ToPILImage':
                self.trList.append(tr.ToPILImage())


class Param2levelDialog(TwoButtonsDialog):
    """
    This class is a dialog for the further specification of some
    transform parameters
    Attributes
    ----------
    params : dict
        A dictionary of the required parameters to return
    Methods
    ----------
    update_param(str, str)
        Procedure to update the parameter 'k' with the value 'v'
    """

    def __init__(self, param_dict: dict, t_name: str):
        super(Param2levelDialog, self).__init__('Parameters required', '')
        g_layout = QGridLayout()
        self.layout.addLayout(g_layout)
        self.params = {}

        input_widgets = {}
        g_layout.addWidget(CustomLabel(t_name, primary=True), 0, 0, 1, 0)
        count = 1

        # Event connection
        def activation_f(key: str):
            return lambda: self.update_param(key, input_widgets[key].text())

        for name, val in param_dict.items():
            input_widgets[name] = CustomTextBox(str(val['value']))
            input_widgets[name].setValidator(ArithmeticValidator.FLOAT)

            g_layout.addWidget(CustomLabel(name), count, 0)
            g_layout.addWidget(input_widgets[name], count, 1)
            self.params[name] = val['value']

            input_widgets[name].textChanged.connect(activation_f(name))

            count += 1

        # Buttons
        self.cancel_btn.clicked.connect(lambda: self.reset(param_dict))

        self.render_layout()

    def update_param(self, key: str, val: str) -> None:
        self.params[key] = float(val)

    def reset(self, param_dict: dict):
        for name, val in param_dict.items():
            self.params[name] = val['value']


class MixedVerificationDialog(TwoButtonsDialog):
    """
    This class is a dialog for prompting the number of neurons to refine
    in the mixed approach
    """

    def __init__(self):
        super().__init__('Mixed Verification', '')
        g_layout = QGridLayout()
        self.layout.addLayout(g_layout)
        self.n_neurons = 0

        target_label = CustomLabel('Neurons number')
        target_edit = CustomTextBox()
        target_edit.setValidator(ArithmeticValidator.INT)
        target_edit.textChanged.connect(lambda: self.update_neurons(target_edit.text()))
        g_layout.addWidget(target_label, 0, 0)
        g_layout.addWidget(target_edit, 0, 1)

        # Buttons
        self.cancel_btn.clicked.connect(self.reset)

        self.render_layout()

    def update_neurons(self, n: str) -> None:
        if n != '':
            self.n_neurons = int(n)

    def reset(self):
        self.n_neurons = 0
