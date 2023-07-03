"""
Module graphics_block.py

This module contains the graphics elements of Block objects for representing the layers,
the IO and the properties

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QColor, QFont, QBrush, QPainterPath
from PyQt6.QtWidgets import QGraphicsItem, QWidget, QGraphicsProxyWidget, QGraphicsTextItem, QVBoxLayout, QGridLayout, \
    QHBoxLayout, QMessageBox

import never2.resources.styling.dimension as dim
import never2.resources.styling.palette as palette
from never2 import get_classname, RES_DIR
from never2.resources.styling.custom import CustomTextBox, CustomLabel, CustomComboBox, CustomButton
from never2.utils.validator import ArithmeticValidator
from never2.view.ui.dialog import ConfirmDialog, MessageDialog, MessageType


class GraphicsBlock(QGraphicsItem):
    def __init__(self, block: 'Block', parent=None):
        super().__init__(parent)
        # Reference to the block
        self.block_ref = block

        # Hover flag
        self.hover = False

        # Content widget
        self.content = None
        self.width = dim.BLOCK_BASE_WIDTH
        self.height = dim.BLOCK_BASE_HEIGHT

        # Init graphics content
        self.title_item = QGraphicsTextItem(self)
        self.graphics_content = QGraphicsProxyWidget(self)
        self.init_graphics_content()

        # Style parameters
        self.color_scheme = []
        self.init_colors()
        self._pen_default = QPen(QColor(self.color_scheme[0]))
        self._pen_default.setWidth(2)
        self._pen_hovered = QPen(QColor(self.color_scheme[1]))
        self._pen_hovered.setWidth(2)
        self._pen_selected = QPen(QColor(self.color_scheme[2]))
        self._pen_selected.setWidth(3)
        self._pen_selected.setStyle(Qt.PenStyle.DotLine)
        self._brush_title = QBrush(QColor(self.color_scheme[3]))
        self._brush_background = QBrush(QColor(self.color_scheme[4]))

        self.init_flags()

    def init_title(self):
        """
        This method sets up the title widget

        """

        self.title_item.setDefaultTextColor(QColor(palette.WHITE))
        self.title_item.setFont(QFont('Arial', 10))
        self.title_item.setPos(dim.TITLE_PAD, 0)
        self.title_item.setPlainText(self.block_ref.title)
        self.title_item.setTextWidth(self.width - 2 * dim.TITLE_PAD)

    def init_colors(self):
        """
        This method sets up the color scheme of the block
        depending on the block type

        """

        if get_classname(self.block_ref) == 'LayerBlock':
            self.color_scheme = [palette.DARK_BLUE, palette.BLUE, palette.BLUE,
                                 palette.DARK_BLUE, palette.DARK_GREY]
        elif get_classname(self.block_ref) == 'PropertyBlock':
            self.color_scheme = [palette.DARK_ORANGE, palette.ORANGE, palette.ORANGE,
                                 palette.DARK_ORANGE, palette.DARK_GREY]
        elif get_classname(self.block_ref) == 'FunctionalBlock':
            self.color_scheme = [palette.GREY, palette.LIGHT_GREY, palette.LIGHT_GREY,
                                 palette.GREY, palette.DARK_GREY]

    def init_graphics_content(self):
        """
        This method sets up the graphics properties of the block
        depending on the content

        """

        if self.block_ref.has_parameters():
            self.width = dim.BLOCK_PARAM_WIDTH
        elif get_classname(self.block_ref) == 'PropertyBlock':
            self.width = dim.BLOCK_PROPERTY_WIDTH

        if self.content is not None:
            self.content.setGeometry(dim.EDGE_ROUNDNESS, dim.TITLE_HEIGHT + dim.EDGE_ROUNDNESS,
                                     self.width - 2 * dim.EDGE_ROUNDNESS, 0)
            self.graphics_content.setWidget(self.content)

            self.width = self.content.size().width() + 2 * dim.EDGE_ROUNDNESS
            self.height = self.content.size().height() + 2 * dim.EDGE_ROUNDNESS + dim.TITLE_HEIGHT

        # Init title card after setting the correct widget width
        self.init_title()

    def init_flags(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

    def open_dock_params(self):
        self.block_ref.scene_ref.editor_widget_ref.show_inspector()

    def set_content(self, content: 'BlockContentWidget'):
        self.content = content
        self.init_graphics_content()

    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self.hover = True
        self.update()

    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self.hover = False
        self.update()

    def mouseMoveEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        super().mouseMoveEvent(event)

        for block in self.block_ref.scene_ref.blocks.values():
            if block.graphics_block.isSelected():
                block.update_edges()

        self.block_ref.update_edges()

    def mouseDoubleClickEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        self.open_dock_params()

    def paint(self, painter: 'QPainter', option: 'QStyleOptionGraphicsItem', widget=None) -> None:
        """
        This method draws the graphicsBlock item. It is a rounded rectangle divided in 3 sections:

        Outline section: draw the contours of the block
        Title section: a darker rectangle in which lays the title
        Content section: container for the block parameters

        """

        # Title section
        path_title = QPainterPath()
        path_title.setFillRule(Qt.FillRule.WindingFill)
        path_title.addRoundedRect(0, 0, self.width, dim.TITLE_HEIGHT, dim.EDGE_ROUNDNESS, dim.EDGE_ROUNDNESS)

        # Remove bottom rounded corners for title box
        path_title.addRect(0, dim.TITLE_HEIGHT - dim.EDGE_ROUNDNESS, dim.EDGE_ROUNDNESS, dim.EDGE_ROUNDNESS)
        path_title.addRect(self.width - dim.EDGE_ROUNDNESS, dim.TITLE_HEIGHT - dim.EDGE_ROUNDNESS,
                           dim.EDGE_ROUNDNESS, dim.EDGE_ROUNDNESS)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # Content
        path_content = QPainterPath()
        path_content.setFillRule(Qt.FillRule.WindingFill)
        path_content.addRoundedRect(0, dim.TITLE_HEIGHT, self.width,
                                    self.height - dim.TITLE_HEIGHT, dim.EDGE_ROUNDNESS, dim.EDGE_ROUNDNESS)

        # Remove top rounded corners for content box
        # left
        path_content.addRect(0, dim.TITLE_HEIGHT, dim.EDGE_ROUNDNESS, dim.EDGE_ROUNDNESS / 2)
        # right
        path_content.addRect(self.width - dim.EDGE_ROUNDNESS, dim.TITLE_HEIGHT,
                             dim.EDGE_ROUNDNESS, dim.EDGE_ROUNDNESS / 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # Outline
        path_outline = QPainterPath()
        path_outline.addRoundedRect(0, 0, self.width, self.height, dim.EDGE_ROUNDNESS, dim.EDGE_ROUNDNESS)
        painter.setPen(self._pen_default if not self.isSelected() else self._pen_selected)

        if self.hover and not self.isSelected():
            painter.setPen(self._pen_hovered)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path_outline.simplified())

    def boundingRect(self) -> QtCore.QRectF:
        """
        Defines the Qt bounding rectangle

        Returns
        ----------
        QRectF
            The area in which the click triggers the item

        """

        return QtCore.QRectF(0, 0, self.width, self.height).normalized()


class BlockContentWidget(QWidget):
    """
    This class provides a QGridLayout structure for the display
    of the Block object parameters inside the GraphicsBlock

    Attributes
    ----------
    block_ref : Block
        Reference to block object

    params_ref : dict
        Reference to block parameters

    wdg_param_dict : dict
        Dictionary of concrete block parameters and widgets

    """

    def __init__(self, block: 'Block', build_dict: dict = None, parent=None):
        super().__init__(parent)

        # Block and parameters reference
        self.block_ref = block
        self.params_ref = self.block_ref.attr_dict['parameters']

        # Concrete parameters
        self.wdg_param_dict = dict()

        # Set style
        with open(RES_DIR + '/styling/qss/blocks.qss') as qss_file:
            self.setStyleSheet(qss_file.read())

        # Layouts
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)

        if build_dict is None:
            self.init_content()
        else:
            self.load_content(build_dict)

        self.init_buttons()

        # Build
        self.layout.addLayout(self.grid_layout)
        self.layout.addLayout(self.buttons_layout)
        self.setLayout(self.layout)

        self.init_validators()

    def init_content(self):
        """
        This method reads the parameters and creates the corresponding objects

        """

        row_grid_count = 0

        for param_name in self.params_ref:
            # Set label
            self.grid_layout.addWidget(CustomLabel(param_name + ':'), row_grid_count, 0)

            # Switch component
            widget = None

            def_val = ''
            if 'default' in self.params_ref[param_name]:
                def_val = self.params_ref[param_name]['default']

            type_val = self.params_ref[param_name]['type']
            param_obj = self.params_ref[param_name]['object']

            if param_obj == 'QLabel':
                widget = CustomLabel(def_val)

            elif param_obj == 'QLineEdit':
                widget = CustomTextBox(def_val, context=get_classname(self.block_ref))

                if self.params_ref[param_name]['editable'] == 'False':
                    widget.setEnabled(False)

            elif param_obj == 'QComboBox':
                if get_classname(self.block_ref) == 'FunctionalBlock':
                    if not self.block_ref.has_input():
                        self.setObjectName('OutputBlockContent')

                    widget = CustomComboBox(context=get_classname(self.block_ref))
                    cb_fill = self.block_ref.scene_ref.editor_widget_ref.property_data.keys()
                    widget.addItems(cb_fill)

                    widget.view().setMinimumWidth(140)
                    widget.setCurrentText(def_val)
                else:
                    widget = CustomComboBox()
                    widget.addItems(['True', 'False'])
                    if def_val == '':
                        widget.setCurrentText('True')
                    else:
                        widget.setCurrentText(def_val)

                def_val = widget.currentText()

            self.grid_layout.addWidget(widget, row_grid_count, 1)
            self.wdg_param_dict[param_name] = [widget, def_val, type_val]

            # Increment for next parameter
            row_grid_count += 1

    def load_content(self, build_dict: dict):
        """
        This method loads the block content and displays the proper widgets

        Parameters
        ----------
        build_dict : dict
            Dictionary containing the block data already formatted

        """

        row_grid_count = 0

        for param_name, param_value in build_dict['parameters'].items():
            # Set label
            self.grid_layout.addWidget(CustomLabel(param_name + ':'), row_grid_count, 0)

            # Switch component
            widget = None

            def_val = ''
            if self.params_ref[param_name]['editable'] == 'True':
                def_val = param_value

            type_val = self.params_ref[param_name]['type']
            param_obj = self.params_ref[param_name]['object']

            if param_obj == 'QLabel':
                widget = CustomLabel(def_val)

            elif param_obj == 'QLineEdit':
                widget = CustomTextBox(def_val, context=get_classname(self.block_ref))

                if self.params_ref[param_name]['editable'] == 'False':
                    widget.setEnabled(False)

            elif param_obj == 'QComboBox':
                widget = CustomComboBox(context=get_classname(self.block_ref))
                widget.addItems(['True', 'False'])
                widget.setCurrentText(param_value)
                def_val = widget.currentText()

            self.grid_layout.addWidget(widget, row_grid_count, 1)
            self.wdg_param_dict[param_name] = [widget, def_val, type_val]

            # Increment for next parameter
            row_grid_count += 1

    def init_buttons(self):
        """
        This method adds to the bottom of the block buttons for saving the updates or to
        add some property

        """

        if get_classname(self.block_ref) == 'LayerBlock':
            if self.block_ref.has_parameters():
                # Create save and discard buttons
                discard = CustomButton('Restore defaults', context='LayerBlock')
                discard.clicked.connect(self.on_button_click)
                save = CustomButton('Save', primary=True, context='LayerBlock')
                save.clicked.connect(self.on_button_click)

                self.buttons_layout.addWidget(discard)
                self.buttons_layout.addWidget(save)

        elif get_classname(self.block_ref) == 'FunctionalBlock':
            # Create property and update buttons
            add_prop = CustomButton('Add property', context='FunctionalBlock')
            add_prop.clicked.connect(self.add_property)
            update = CustomButton('Update', context='FunctionalBlock')
            update.clicked.connect(self.on_button_click)

            self.buttons_layout.addWidget(add_prop)
            self.buttons_layout.addWidget(update)

        elif get_classname(self.block_ref) == 'PropertyBlock':
            # Create edit button
            edit = CustomButton('Edit', context='PropertyBlock')
            edit.clicked.connect(self.block_ref.edit)

            self.buttons_layout.addWidget(edit)

    def init_validators(self):
        """
        This method sets the proper validator for the parameters widgets

        """

        for param_name, param_info in self.params_ref.items():
            qt_wdg = self.wdg_param_dict[param_name][0]

            # Type check
            if isinstance(qt_wdg, CustomTextBox):
                prev = qt_wdg.text()
                qt_wdg.editingFinished.connect(lambda: self.check_values(param_name, prev))

                # Set proper validator
                validator = None
                param_type = param_info['type']
                if param_type == 'int':
                    validator = ArithmeticValidator.INT
                elif param_type == 'float':
                    validator = ArithmeticValidator.FLOAT
                elif param_type == 'Tensor' or param_type == 'list of ints':
                    validator = ArithmeticValidator.TENSOR
                qt_wdg.setValidator(validator)

    def on_button_click(self):
        """
        Handler for the button operations. It checks for properties before allowing modifications.

        """

        if self.block_ref.scene_ref.post_block is not None:
            dialog = ConfirmDialog('Confirmation required',
                                   'Editing the network will remove the output property.\nProceed?')
            dialog.exec()

            if dialog.confirm:
                self.block_ref.scene_ref.remove_out_prop()
        else:
            button_type = self.sender().text()

            if button_type == 'Update':  # Only for FunctionalBlocks
                if self.block_ref.title == 'Input' and self.block_ref.scene_ref.pre_block is not None:

                    dialog = ConfirmDialog('Confirmation required',
                                           'Editing the network will remove the input property.\nProceed?')
                    dialog.exec()

                    if dialog.confirm:
                        self.block_ref.scene_ref.remove_in_prop()
                        self.save_func_params()
                else:
                    self.save_func_params()

            elif button_type == 'Restore defaults':
                self.restore_default()
            elif button_type == 'Save':
                self.save_layer_params()

    def check_values(self, name, bk_value):
        """
        This method checks that all values written in Text Edit objects are sound w.r.t. their meaning

        """

        err_message = ''

        param_type = self.params_ref[name]['type']
        qt_widget = self.wdg_param_dict[name][0]
        param_value = qt_widget.text()

        if param_type == 'int':
            try:
                int(param_value)
            except ValueError:
                err_message = param_value + ' is not a ' + param_type + '. Please change it'

        elif param_type == 'float':
            try:
                float(param_value)
            except ValueError:
                err_message = param_value + ' is not a ' + param_type + '. Please change it'

        elif param_type == 'list of ints':
            list_of_strings = param_value.replace(' ', '').rstrip(',').split(',')
            comma = ', '
            qt_widget.setText(comma.join(list_of_strings))
            try:
                [int(x) for x in list_of_strings]
            except ValueError:
                err_message = param_value + ' is not a ' + param_type + '. Please change it'

        if err_message != '':
            error_msg = QMessageBox()
            error_msg.setWindowTitle('Error - ' + self.block_ref.title)
            error_msg.setText(name + ': ' + err_message)
            error_msg.exec()

            # Restore backup value
            qt_widget.setText(bk_value)

    def toggle_content_enabled(self, enable=False):
        """
        Enable/disable editing the content widget

        """

        widgets = [self.grid_layout.itemAt(i).widget() for i in range(self.grid_layout.count())]
        buttons = [self.buttons_layout.itemAt(i).widget() for i in range(self.buttons_layout.count())]

        for widget in widgets:
            if isinstance(widget, CustomTextBox) or isinstance(widget, CustomComboBox):
                # Free to add property
                if isinstance(widget, CustomComboBox) and get_classname(self.block_ref) == 'FunctionalBlock':
                    continue

                if enable:
                    widget.setEnabled(True)
                else:
                    widget.setEnabled(False)

        for button in buttons:
            # Free to add property
            if button.text() == 'Add property':
                continue
            elif enable:
                button.setEnabled(True)
            else:
                button.setEnabled(False)

    def add_property(self):
        """
        This method builds a property from the name in the combo box

        """

        wdg = self.wdg_param_dict['Property'][0]
        prop_name = wdg.currentText().strip()

        if prop_name in self.block_ref.scene_ref.editor_widget_ref.property_data.keys():
            self.wdg_param_dict['Property'][1] = prop_name
            self.block_ref.scene_ref.add_property_block(prop_name, self.block_ref)

    def missing_params(self) -> bool:
        """
        This function checks that all required parameters are set before updating

        Returns
        -------
        bool
            True if there are missing parameters to set, False otherwise

        """

        missing_parameters = []

        for parameter_name in self.wdg_param_dict:

            q_widget = self.wdg_param_dict[parameter_name][0]

            if 'editable' in self.params_ref[parameter_name]:
                if self.params_ref[parameter_name]['editable'] == 'True':
                    if 'required' in self.params_ref[parameter_name]:
                        if self.params_ref[parameter_name]['required'] == 'True':
                            if q_widget.text() == '':
                                missing_parameters.append(parameter_name)

                    q_widget.clearFocus()

        if missing_parameters:
            dialog = MessageDialog('Required parameter(s) ' + ', '.join(missing_parameters).upper()
                                   + ' missing.\nPlease add them.', MessageType.ERROR)
            dialog.exec()
            return True

        return False

    def save_func_params(self):
        """
        Update label and dimension

        """

        if not self.missing_params():

            name_wdg = self.wdg_param_dict['Name'][0]
            self.wdg_param_dict['Name'][1] = name_wdg.text()

            dim_wdg = self.wdg_param_dict['Dimension'][0]
            self.wdg_param_dict['Dimension'][1] = dim_wdg.text()

            # Update property variables if required
            if self.block_ref.get_property_block() is not None:
                self.block_ref.get_property_block().variables = self.block_ref.get_variables()

            # Update the network
            self.block_ref.scene_ref.project.reset_nn(name_wdg.text(), self.block_ref.id)

    def save_layer_params(self):
        """
        Read the parameters widgets and try to re-build the graphics block

        """

        node_ref = self.block_ref.scene_ref.project.nn.nodes[self.block_ref.id]

        try:
            # Check required parameters
            if not self.missing_params():
                for param_name, param_value in self.wdg_param_dict.items():
                    q_wdg = param_value[0]

                    if isinstance(q_wdg, CustomTextBox) or isinstance(q_wdg, CustomComboBox):
                        self.wdg_param_dict[param_name][1] = q_wdg.text()

                # Update pynever node
                self.block_ref.scene_ref.project.refresh_node(self.block_ref.id, self.wdg_param_dict)

                # Update graphics block
                self.block_ref.scene_ref.update_block_params(
                    self.block_ref, self.block_ref.scene_ref.project.nn.nodes[self.block_ref.id])

                # Update output block
                self.block_ref.scene_ref.update_out_dim()

        except Exception as e:
            dialog = MessageDialog(str(e), MessageType.ERROR)
            dialog.exec()

            if self.block_ref.id not in self.block_ref.scene_ref.project.nn.nodes:
                self.block_ref.scene_ref.project.link_to_nn(node_ref)

    def restore_default(self):
        """
        This method resets the graphics parameters without editing the network

        """

        for param_name, param_value in self.wdg_param_dict.items():
            if 'editable' in self.block_ref.attr_dict['parameters'][param_name]:

                if self.block_ref.attr_dict['parameters'][param_name]['editable'] == 'True':
                    q_widget = param_value[0]

                    if 'default' in self.block_ref.attr_dict['parameters'][param_name]:
                        default_value = self.block_ref.attr_dict['parameters'][param_name]['default']

                        if isinstance(q_widget, CustomTextBox) or isinstance(q_widget, CustomComboBox):
                            q_widget.setText(default_value)
                    else:
                        if isinstance(q_widget, CustomTextBox):
                            q_widget.setText('')
                        elif isinstance(q_widget, CustomComboBox):
                            q_widget.setText('True')

        self.block_ref.scene_ref.update_out_dim()
