"""
Module inspector.py

This module contains the InspectorDockToolbar class and the relative classes
involved in the visualization of the parameters for layers

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QScrollArea, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout

import never2.resources.styling.display as disp
from never2 import get_classname
from never2.resources.styling.custom import CustomLabel, CustomButton


class InspectorDockToolbar(QDockWidget):
    """
    This class is the block details inspector that is displayed as a side dock toolbar
    with the parameters describing the block.

    Attributes
    ----------
    block_dict : dict
        Container of block parameters

    property_dict : dict
        Container of property parameters

    scroll_area : QScrollArea
        Widget containing the parameters info

    """

    def __init__(self, block_dict: dict, property_dict: dict):
        super().__init__()

        # Hide by default
        self.hide()

        # Data dictionaries
        self.block_dict = block_dict
        self.property_dict = property_dict

        # Main content
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet(disp.SCROLL_AREA_STYLE)
        self.scroll_area.setWidgetResizable(True)

        # Scrollbars
        self.scroll_area.horizontalScrollBar().setEnabled(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().setStyleSheet(disp.VERTICAL_SCROLL_BAR)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Setup
        self.setWidget(self.scroll_area)
        self.setWindowTitle('Inspector')
        self.setStyleSheet(disp.DOCK_STYLE)

        self.setFloating(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def display(self, block: 'Block'):
        """
        This method displays the widget describing the block description

        Parameters
        ----------
        block : Block
            Block object for data

        """

        if block is None or get_classname(block) == 'FunctionalBlock':
            self.hide()

        else:
            self.show()
            keys = block.signature.split(':')
            if get_classname(block) == 'LayerBlock':
                self.scroll_area.setWidget(BlockInspector(block, self.block_dict[keys[1]][keys[2]]))
            else:
                self.scroll_area.setWidget(BlockInspector(block, self.block_dict[keys[1]]))

            self.scroll_area.setMinimumWidth(self.scroll_area.sizeHint().width())


class BlockInspector(QWidget):
    """
    This class is a widget for displaying the block info

    """

    def __init__(self, block: 'Block', description: dict):
        super().__init__()

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 10, 0)
        self.setLayout(self.layout)
        self.adjustSize()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        self.title_label = CustomLabel(block.title)
        self.title_label.setStyleSheet(disp.TITLE_LABEL_STYLE)

        # Description of the block
        self.description_label = CustomLabel()
        self.description_label.setStyleSheet(disp.DESCRIPTION_STYLE)
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.description_label.setText(description['description'])
        self.description_label.setSizePolicy(QSizePolicy.Policy.Preferred,
                                             QSizePolicy.Policy.Minimum)

        # Parameters section
        if 'parameters' in description.keys():
            if len(description['parameters'].items()) > 0:
                self.parameters_label = CustomLabel('Parameters')
                self.parameters_label.setStyleSheet(disp.NODE_LABEL_STYLE)

                self.parameters_layout = QVBoxLayout()
                self.parameters_layout.setSpacing(0)

                self.parameters = QWidget()
                self.parameters.setLayout(self.parameters_layout)
                self.parameters.setStyleSheet('padding: 0px')

                for par, values in description['parameters'].items():
                    self.parameters_layout.addWidget(DropDownLabel(par, values))

        if 'input' in description.keys():
            self.inputs_label = CustomLabel('Input')
            self.inputs_label.setStyleSheet(disp.NODE_LABEL_STYLE)

            self.inputs_layout = QVBoxLayout()
            self.inputs_layout.setSpacing(0)

            self.inputs = QWidget()
            self.inputs.setLayout(self.inputs_layout)
            self.inputs.setStyleSheet('padding: 0px')

            for par, values in description['input'].items():
                self.inputs_layout.addWidget(DropDownLabel(par, values))

        if 'output' in description.keys():
            self.outputs_label = CustomLabel('Output')
            self.outputs_label.setStyleSheet(disp.NODE_LABEL_STYLE)

            self.outputs_layout = QVBoxLayout()
            self.outputs_layout.setSpacing(0)

            self.outputs = QWidget()
            self.outputs.setLayout(self.outputs_layout)
            self.outputs.setStyleSheet('padding: 0px')

            for par, values in description['output'].items():
                self.outputs_layout.addWidget(DropDownLabel(par, values))

        # Compose widget
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.description_label)

        if 'input' in description.keys():
            self.layout.addWidget(self.inputs_label)
            self.layout.addWidget(self.inputs)

        if 'output' in description.keys():
            self.layout.addWidget(self.outputs_label)
            self.layout.addWidget(self.outputs)

        if 'parameters' in description.keys() and len(description['parameters'].items()) > 0:
            self.layout.addWidget(self.parameters_label)
            self.layout.addWidget(self.parameters)


class DropDownLabel(QWidget):
    """
    This widget displays a generic parameter name and value.
    It features a drop-down arrow button that shows or hides the description.

    Attributes
    ----------
    layout : QVBoxLayout
        Vertical main_layout of the widget.

    top : QWidget
        First part of the widget with name, type and default value of the
        parameter.

    top_layout : QHBoxLayout
        Horizontal main_layout of the top of the widget.

    name_label : CustomLabel
        ID and type of the object.

    type_label : CustomLabel
        Object type.

    down_button : CustomButton
        Arrow button to show/hide the description of the parameter.

    description : CustomLabel
        Description of the parameter.

    Methods
    ----------
    _toggle_visibility()
        This method shows or hides the description of the parameter.

    """

    def __init__(self, name: str, parameters: dict):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.setStyleSheet(disp.DROPDOWN_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Minimum,
                           QSizePolicy.Policy.Expanding)

        # Top bar with short info
        self.top = QWidget()
        self.top.setContentsMargins(0, 0, 0, 0)
        self.top.setStyleSheet(disp.DROPDOWN_TOP_STYLE)
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top.setLayout(self.top_layout)

        self.name_label = CustomLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.name_label.setStyleSheet(disp.DROPDOWN_NAME_STYLE)
        self.top_layout.addWidget(self.name_label, Qt.AlignmentFlag.AlignLeft)

        self.type_label = CustomLabel(parameters['type'])
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.type_label.setToolTip('Type')
        self.type_label.setStyleSheet(disp.DROPDOWN_TYPE_STYLE)
        self.top_layout.addWidget(self.type_label, Qt.AlignmentFlag.AlignLeft)

        self.down_button = CustomButton('\u25bc')
        self.down_button.setStyleSheet(disp.DROPDOWN_ARROW_STYLE)
        self.down_button.clicked.connect(lambda: self.__toggle_visibility())
        self.top_layout.addWidget(self.down_button, Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(self.top)

        self.description = CustomLabel(parameters['description'])
        self.description.setSizePolicy(QSizePolicy.Policy.Minimum,
                                       QSizePolicy.Policy.Maximum)
        self.description.setWordWrap(True)
        self.description.setStyleSheet(disp.DESCRIPTION_STYLE)
        self.description.hide()
        self.layout.addWidget(self.description)

    def __toggle_visibility(self):
        """
        This method toggles the visibility of the parameter description
        changing the arrow icon of the button.

        """

        if self.description.isHidden():
            self.description.show()
            self.down_button.setText('\u25b2')
        else:
            self.description.hide()
            self.down_button.setText('\u25bc')
