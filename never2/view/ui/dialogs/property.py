"""
Module property.py

This module contains all the property dialog classes used in NeVer2

Author: Stefano Demarchi

"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout

import never2.resources.styling.display as disp
from never2 import RES_DIR
from never2.resources.styling.custom import CustomLabel, CustomTextArea, CustomComboBox, CustomTextBox, CustomButton
from never2.utils.validator import ArithmeticValidator
from never2.view.ui.dialogs.dialog import TwoButtonsDialog, BaseDialog
from never2.view.ui.dialogs.message import MessageDialog, MessageType


class PropertyDialog(TwoButtonsDialog):
    """
    This class groups all common functionalities for property dialogs.

    Attributes
    ----------
    property_block : PropertyBlock
        Current property to edit.
    has_edits : bool
        Flag signaling if the property was edited.

    """

    def __init__(self, property_block: 'PropertyBlock'):
        super().__init__('Edit Property', '', context='Property')
        self.property_block = property_block
        self.has_edits = False

        # apply same QLineEdit and QComboBox style of the block contents
        qss_file = open(RES_DIR + '/styling/qss/blocks.qss').read()
        self.setStyleSheet(qss_file)


class EditSmtPropertyDialog(PropertyDialog):
    """
    This dialog allows to define a generic SMT property
    by writing directly in the SMT-LIB language.

    Attributes
    ----------
    new_property_str : str
        New SMT-LIB property string.
    smt_box : CustomTextArea
        Input box.

    Methods
    ----------
    save_data()
        Procedure to return the new property.

    """

    def __init__(self, property_block: 'PropertyBlock'):
        super().__init__(property_block)
        self.new_property_str = self.property_block.smt_string

        g_layout = QGridLayout()
        self.layout.addLayout(g_layout)

        # Build main_layout
        title_label = CustomLabel('SMT property', alignment=Qt.AlignmentFlag.AlignCenter, context='Property')
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
        List of independent statements.
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


class EditBoxPropertyDialog(PropertyDialog):
    """
    This dialog allows to define a bounded box defined by two lists
    for the lower bounds and the upper bounds.

    Attributes
    ----------
    lower_bounds : list
        Lower bounds of the property.
    upper_bounds : list
        Upper bounds of the property.
    lbs_box : CustomTextBox
        Input box for lower bounds.
    ubs_box : CustomTextBox
        Input box for upper bounds.

    Methods
    ----------
    save_data()
        Procedure to read input and save bounds.
    compile_smt()
        Procedure to translate the bounds in SMT-LIB.

    """

    def __init__(self, property_block: 'PropertyBlock'):
        super().__init__(property_block)
        self.property_block = property_block
        self.lower_bounds = []
        self.upper_bounds = []

        if self.property_block.label_string != '':
            bounds = self.property_block.label_string.split('::')
            self.lower_bounds = eval(bounds[0])
            self.upper_bounds = eval(bounds[1])

        g_layout = QGridLayout()
        self.layout.addLayout(g_layout)

        # Build main_layout
        title_label = CustomLabel('Box property', alignment=Qt.AlignmentFlag.AlignCenter, context='Property')
        g_layout.addWidget(title_label, 0, 0, 1, 2)

        # Hint
        hint_label = CustomLabel(f'Enter {len(self.property_block.variables)} comma separated values',
                                 alignment=Qt.AlignmentFlag.AlignCenter)
        g_layout.addWidget(hint_label, 1, 0, 1, 2)

        # Lower bounds
        lbs_label = CustomLabel('Lower bounds', alignment=Qt.AlignmentFlag.AlignRight)
        lbs_label.setStyleSheet(disp.PROPERTY_IN_DIM_LABEL_STYLE)
        g_layout.addWidget(lbs_label, 2, 0)

        self.lbs_box = CustomTextBox(f'{[lb for lb in self.lower_bounds]}'.replace('[', '').replace(']', ''))
        g_layout.addWidget(self.lbs_box, 2, 1)

        # Upper bounds
        ubs_label = CustomLabel('Upper bounds', alignment=Qt.AlignmentFlag.AlignRight)
        ubs_label.setStyleSheet(disp.PROPERTY_IN_DIM_LABEL_STYLE)
        g_layout.addWidget(ubs_label, 3, 0)

        self.ubs_box = CustomTextBox(f'{[ub for ub in self.upper_bounds]}'.replace('[', '').replace(']', ''))
        g_layout.addWidget(self.ubs_box, 3, 1)

        self.set_buttons_text('Discard', 'Apply')
        self.ok_btn.clicked.connect(self.save_data)

        self.render_layout()

    def save_data(self) -> None:
        """
        Method triggered by 'Apply' button

        """

        num_var = len(self.property_block.variables)

        try:
            self.lower_bounds = [float(b) for b in self.lbs_box.text().split(',')]
            self.upper_bounds = [float(b) for b in self.ubs_box.text().split(',')]
        except ValueError as e:
            dialog = MessageDialog(f'Illegal value found: {str(e)}', MessageType.ERROR)
            dialog.exec()

        if not (len(self.lower_bounds) == len(self.upper_bounds) == num_var):
            dialog = MessageDialog(f'The number of lower bounds and upper bounds must be {num_var}', MessageType.ERROR)
            dialog.exec()
        else:
            self.has_edits = True

    def compile_smt(self) -> str:
        """
        This method builds a SMT-LIB string starting from the bounds

        Returns
        ----------
        str
            The SMT-LIB formatted bounds

        """

        smt_string = ''
        symbol = self.property_block.ref_block.get_identifier()

        for i in range(len(self.lower_bounds)):
            smt_string += f'(assert (<= (* -1 {symbol}_{i}) {-self.lower_bounds[i]}))\n'
            smt_string += f'(assert (<= {symbol}_{i} {self.upper_bounds[i]}))\n'

        return smt_string


class EditClassificationPropertyDialog(PropertyDialog):
    """
    This dialog allows to define a classification property by selecting
    an output variable to be minimum or maximum.

    Attributes
    ----------


    """

    def __init__(self, property_block: 'PropertyBlock'):
        super().__init__(property_block)

        self.viewer = CustomTextBox(context='FunctionalBlock')
        self.viewer.setReadOnly(True)
        g_layout = QGridLayout()
        self.layout.addLayout(g_layout)

        self.min = True
        if self.property_block.label_string != '':
            self.min = self.property_block.label_string.split('#')[0] == True

        # Build main layout
        title_label = CustomLabel('Classification property',
                                  alignment=Qt.AlignmentFlag.AlignCenter,
                                  context='Property')
        g_layout.addWidget(title_label, 0, 0, 1, 2)

        # Variable selector
        var_label = CustomLabel('Variable', primary=True, context='Property')
        g_layout.addWidget(var_label, 1, 0)
        self.var_cb = CustomComboBox(context='Property')
        for v in self.property_block.variables:
            self.var_cb.addItem(v)
        g_layout.addWidget(self.var_cb, 2, 0)

        if self.property_block.label_string != '':
            self.var_cb.setCurrentText(self.property_block.label_string.split('#')[1])

        # Min/Max selector
        minmax_label = CustomLabel('Expected value', primary=True, context='Property')
        g_layout.addWidget(minmax_label, 1, 1)
        self.minmax = CustomComboBox(context='Property')
        self.minmax.addItems(['Min', 'Max'])
        g_layout.addWidget(self.minmax, 2, 1)

        if self.property_block.label_string != '':
            if not self.min:
                self.minmax.setCurrentText('Max')

        # Viewer
        self.var_cb.currentTextChanged.connect(self.update_self)
        self.minmax.currentTextChanged.connect(self.update_self)
        self.update_self()
        g_layout.addWidget(self.viewer, 3, 0, 1, 2)

        self.render_layout()

    def update_self(self) -> None:
        self.min = self.minmax.currentText() == 'Min'
        varname = self.property_block.ref_block.get_identifier()
        varnum = self.var_cb.currentText().split('_')[-1]
        operator = '<=' if self.min else '>='
        self.viewer.setText(f"{self.var_cb.currentText()} {operator} {varname}_j for all j != {varnum}")
        self.has_edits = True

    def compile_smt(self) -> str:
        """
        This method builds a SMT-LIB string for the classification
        specification

        Returns
        ----------
        str
            The SMT-LIB formatted statement

        """

        smt_string = ''
        varname = self.property_block.ref_block.get_identifier()
        varnum = self.var_cb.currentText().split('_')[-1]
        operator = '<=' if self.min else '>='

        for i in range(len(self.property_block.variables)):
            if i != int(varnum):
                smt_string += f'(assert ({operator} {varname}_{varnum} {varname}_{i}))\n'

        return smt_string
