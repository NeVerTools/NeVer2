import json
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDockWidget, QScrollArea, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QToolBar, QToolButton

import never2.view.styles as style
from never2 import ROOT_DIR
from never2.core.model.network import NetworkNode
from never2.view.drawing.element import NodeBlock
from never2.view.widget.custom import CustomLabel, CustomButton


class ParamToolbar(QDockWidget):
    """
    This class is a widget for inspecting the parameters of a given
    block. It is anchored to the right side of the window and can be
    moved.

    Attributes
    ----------
    scroll_area : QScrollArea
        Scrollable area that contains a widget with the description of
        the block.

    Methods
    ----------
    display(NodeBlock)
        This method displays in the scroll area the full description of the
        given graphic block.

    """

    def __init__(self):
        super().__init__()
        self.hide()  # Create hidden

        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet(style.SCROLL_AREA_STYLE)
        self.scroll_area.setWidgetResizable(True)

        # Setting scrollbars
        self.scroll_area.horizontalScrollBar().setEnabled(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().setStyleSheet(style.VERTICAL_SCROLL_BAR)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.setWidget(self.scroll_area)
        self.setWindowTitle("Parameters")
        self.setStyleSheet(style.DOCK_STYLE)

        # The user can move this bar away
        self.setFloating(True)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def display(self, block: NodeBlock):
        """
        This method displays the widget containing the description of the given
        block in the Toolbar.

        Parameters
        ----------
        block : NodeBlock
            The selected block to display info of.

        """

        # Show toolbar and fit dimensions
        self.show()
        self.scroll_area.setWidget(BlockInspector(block))
        self.scroll_area.setMinimumWidth(self.scroll_area.sizeHint().width())


class BlockInspector(QWidget):
    """
    This class contains the widget for displaying the description of a network
    block in the ParamToolbar. Each block attribute is labeled and wrapped
    in a drop-down box.

    Attributes
    ----------
    layout : QVBoxLayout
        Vertical main_layout of the widget.
    title_label : CustomLabel
        Title of the widget.
    description_label : CustomLabel
        Description of the block.
    parameters : QWidget
        Container of parameters.
    parameters_label : CustomLabel
        Label of parameters.
    parameters_layout : QVBoxLayout
        Vertical main_layout of parameters.
    inputs : QWidget
        Container of inputs.
    inputs_label : CustomLabel
        Label of inputs.
    inputs_layout : QVBoxLayout
        Vertical main_layout of inputs.
    outputs : QWidget
        Container of outputs.
    outputs_label : CustomLabel
        Label of outputs.
    outputs_layout : QVBoxLayout
        Vertical main_layout of outputs.

    """

    def __init__(self, block: NodeBlock):
        super().__init__()
        self.setStyleSheet(style.BLOCK_BOX_STYLE)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 10, 0)
        self.setLayout(self.layout)
        self.adjustSize()
        self.setSizePolicy(QSizePolicy.Minimum,
                           QSizePolicy.Maximum)

        # Widget title
        self.title_label = CustomLabel()
        self.title_label.setStyleSheet(style.TITLE_LABEL_STYLE)
        self.title_label.setText(block.block_id + ":" + block.node.name)

        # NodeBlock description
        self.description_label = CustomLabel()
        self.description_label.setStyleSheet(style.DESCRIPTION_STYLE)
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignLeft)
        self.description_label.setText(block.node.descr)
        self.description_label.setSizePolicy(QSizePolicy.Preferred,
                                             QSizePolicy.Minimum)

        # Parameters section
        if block.node.param:
            self.parameters_label = CustomLabel("Parameters")
            self.parameters_label.setStyleSheet(style.NODE_LABEL_STYLE)
            self.parameters = QWidget()
            self.parameters_layout = QVBoxLayout()
            self.parameters_layout.setSpacing(0)
            self.parameters.setLayout(self.parameters_layout)
            self.parameters.setStyleSheet("padding: 0px")

            for par, values in block.node.param.items():
                self.parameters_layout.addWidget(DropDownLabel(par, values))

        # Inputs section
        if block.node.input:
            self.inputs_label = CustomLabel("Input")
            self.inputs_label.setStyleSheet(style.NODE_LABEL_STYLE)
            self.inputs = QWidget()
            self.inputs_layout = QVBoxLayout()
            self.inputs_layout.setSpacing(0)
            self.inputs.setLayout(self.inputs_layout)
            self.inputs.setStyleSheet("padding: 0px")

            for par, values in block.node.input.items():
                self.inputs_layout.addWidget(DropDownLabel(par, values))

        # Outputs section
        if block.node.output:
            self.outputs_label = CustomLabel("Output")
            self.outputs_label.setStyleSheet(style.NODE_LABEL_STYLE)
            self.outputs = QWidget()
            self.outputs_layout = QVBoxLayout()
            self.outputs_layout.setSpacing(0)
            self.outputs.setLayout(self.outputs_layout)
            self.outputs.setStyleSheet("padding: 0px")

            for par, values in block.node.output.items():
                self.outputs_layout.addWidget(DropDownLabel(par, values))

        # Compose widget
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.description_label)

        if block.node.param:
            self.layout.addWidget(self.parameters_label)
            self.layout.addWidget(self.parameters)

        if block.node.input:
            self.layout.addWidget(self.inputs_label)
            self.layout.addWidget(self.inputs)

        if block.node.output:
            self.layout.addWidget(self.outputs_label)
            self.layout.addWidget(self.outputs)


class DropDownLabel(QWidget):
    """
    This widget displays a generic parameter name and value.
    It features a drop-down arrow button that shows or hides
    the description.

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
        Id and type of the object.
    type_label : CustomLabel
        Object type.
    default_label : CustomLabel
        Eventual default value.
    down_button : CustomButton
        Arrow button to show/hide the description of the parameter.
    description : CustomLabel
        Description of the parameter.

    Methods
    ----------
    change_description_mode()
        This method shows or hides the description of the parameter.

    """

    def __init__(self, name: str, parameters: dict):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.setStyleSheet(style.DROPDOWN_STYLE)
        self.setSizePolicy(QSizePolicy.Minimum,
                           QSizePolicy.Expanding)

        # Top bar with short info
        self.top = QWidget()
        self.top.setContentsMargins(0, 0, 0, 0)
        self.top.setStyleSheet(style.DROPDOWN_TOP_STYLE)
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top.setLayout(self.top_layout)

        self.name_label = CustomLabel(name)
        self.name_label.setAlignment(Qt.AlignLeft)
        self.name_label.setStyleSheet(style.DROPDOWN_NAME_STYLE)
        self.top_layout.addWidget(self.name_label, Qt.AlignLeft)

        self.type_label = CustomLabel(parameters["type"])
        self.type_label.setAlignment(Qt.AlignLeft)
        self.type_label.setToolTip("Type")
        self.type_label.setStyleSheet(style.DROPDOWN_TYPE_STYLE)
        self.top_layout.addWidget(self.type_label, Qt.AlignLeft)

        if "default" in parameters:
            self.default_label = CustomLabel(parameters["default"])
            self.default_label.setStyleSheet(style.DROPDOWN_DEFAULT_STYLE)
            self.default_label.setToolTip("Default value")
            self.default_label.setAlignment(Qt.AlignCenter)
            self.top_layout.addWidget(self.default_label, Qt.AlignRight)

        self.down_button = CustomButton("\u25bc")
        self.down_button.setStyleSheet(style.DROPDOWN_ARROW_STYLE)
        self.down_button.clicked.connect(lambda: self.__toggle_visibility())
        self.top_layout.addWidget(self.down_button, Qt.AlignRight)

        self.layout.addWidget(self.top)

        self.description = CustomLabel(parameters["description"])
        self.description.setSizePolicy(QSizePolicy.Minimum,
                                       QSizePolicy.Maximum)
        self.description.setWordWrap(True)
        self.description.setStyleSheet(style.DESCRIPTION_STYLE)
        self.description.hide()
        self.layout.addWidget(self.description)

    def __toggle_visibility(self):
        """
        This method toggles the visibility of the parameter description
        changing the arrow icon of the button.

        """

        if self.description.isHidden():
            self.description.show()
            self.down_button.setText("\u25b2")
        else:
            self.description.hide()
            self.down_button.setText("\u25bc")


class NodeButton(CustomButton):
    """
    Graphical button that carries information related to a type of node.

    Attributes
    ----------
    name : str
        The string appearing on the button.
    node_type : NetworkNode
        The type of node that will be displayed if the user clicks on the
        button.

    """

    def __init__(self, name: str, node_type: NetworkNode):
        self.name = name
        self.node_type = node_type
        super(NodeButton, self).__init__(name)


class PropertyButton(CustomButton):
    """
    Graphic button that carries information related to a property.

    Attributes
    ----------
    name : str
        The string appearing on the button.

    """

    def __init__(self, name: str):
        self.name = name
        super(PropertyButton, self).__init__(name)


class BlocksToolbar(QToolBar):
    """
    This class defines a toolbar containing all the blocks available to draw a
    neural network: each type of block is read from a file in order to build a list
    of NetworkNode objects to be displayed.

    Attributes
    ----------
    NODE_FILE_PATH : str
        Path of the JSON file containing all information about the implemented
        nodes available to displaying.
    blocks : dict
        Dictionary of blocks connecting each block name with a NetworkNode.
    properties : dict
        Dictionary of properties connecting each property name with a NetworkProperty.
    f_buttons : dict
        Dictionary of buttons connecting a function name to a CustomButton.
    b_buttons : dict
        Dictionary connecting each block name to a CustomButton, which
        makes the corresponding node appear.
    p_buttons : dict
        Dictionary connecting each property name to a CustomButton, which
        makes the corresponding property appear.
    toolbar_tools_label : CustomLabel
        Label of the toolbar introducing tools.
    toolbar_blocks_label : CustomLabel
        Label of the toolbar introducing blocks types.
    toolbar_properties_label : CustomLabel
        Label of the toolbar introducing property names.
    isToolbar_tools_label_visible : bool
        Tells if the tools button are visible in the toolbar.
    isToolbar_blocks_label_visible : bool
        Tells if the blocks button are visible in the toolbar.
    isToolbar_properties_label_visible : bool
        Tells if the properties button are visible in the toolbar.

    Methods
    ----------
    __display_tools()
        This method displays on the toolbar the CustomButtons related to
        available tools.
    __init_blocks()
        This method reads from file all types of blocks storing them.
    __display_blocks()
        This method displays on the toolbar all buttons related to types of
        blocks.
    change_tools_mode()
        This method changes the visibility of the tools section of the toolbar.
    change_blocks_mode()
        This method changes the visibility of the blocks section of the toolbar.
    show_section(CustomLabel, dict)
        This method shows the given objects.
    hide_section(CustomLabel, dict)
        This method hides the given objects.

    """

    def __init__(self, node_file_path: str):
        super().__init__()
        self.NODE_FILE_PATH = node_file_path
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.blocks = dict()
        self.properties = dict()

        # Graphic buttons
        self.f_buttons = dict()
        self.b_buttons = dict()
        self.p_buttons = dict()

        # Labels
        self.toolbar_tools_label = CustomLabel("Tools")
        self.toolbar_blocks_label = CustomLabel("Nodes")
        self.toolbar_properties_label = CustomLabel("Properties")
        self.isToolbar_tools_label_visible = True
        self.isToolbar_blocks_label_visible = True
        self.isToolbar_properties_label_visible = True

        # Setup view
        self.__display_tools()
        self.__init_blocks()
        self.__display_blocks()
        self.__init_properties()
        self.__display_properties()

        # Toolbar style
        for item in self.children():
            if type(item) is QToolButton:
                item.setStyleSheet("background-color: " + style.GREEN_2)
        self.setStyleSheet(style.TOOLBAR_STYLE)

        self.setOrientation(Qt.Vertical)
        self.setMovable(False)
        self.setFloatable(False)

    def __init_blocks(self):
        """
        Uploading blocks from a JSON file storing them in a dictionary of
        NetworkNode objects.

        """

        with open(self.NODE_FILE_PATH) as json_file:
            blocks_dict = json.loads(json_file.read())

        for k, b in blocks_dict.items():
            self.blocks[k] = NetworkNode(k, b["name"], b["input"], b["parameters"],
                                         b["output"], b["description"])
            button = NodeButton(k, self.blocks[k])
            button.setToolTip(b["description"])
            self.b_buttons[k] = button

    def __init_properties(self):
        props = ("Generic SMT", "Polyhedral")

        for k in props:
            button = PropertyButton(k)
            button.setToolTip(k)
            self.p_buttons[k] = button

    def __display_tools(self):
        """
        This method adds to the toolbar all buttons related to available tools,
        displaying them in rows in order to have a flexible main_layout in every
        position of the toolbar.

        """

        # Setting the label of the toolbar
        self.addWidget(self.toolbar_tools_label)
        self.toolbar_tools_label.setAlignment(Qt.AlignCenter)
        self.toolbar_tools_label.setStyleSheet(style.NODE_LABEL_STYLE)

        # Setting the first row with horizontal main_layout
        row_1 = QWidget()
        row_1_layout = QHBoxLayout()
        row_1_layout.setSpacing(0)
        row_1_layout.setContentsMargins(0, 0, 0, 0)
        row_1_layout.setAlignment(Qt.AlignCenter)
        row_1.setLayout(row_1_layout)

        # DrawLine mode button
        draw_line_button = CustomButton()
        draw_line_button.setIcon(QIcon(ROOT_DIR + "/res/icons/line.png"))
        draw_line_button.setFixedSize(40, 40)
        draw_line_button.setToolTip("Draw line")

        # Insert block button
        insert_block_button = CustomButton()
        insert_block_button.setIcon(QIcon(ROOT_DIR + "/res/icons/insert.png"))
        insert_block_button.setFixedSize(40, 40)
        insert_block_button.setToolTip("Insert block in edge")

        # Save in a dictionary button references and add the rows to the
        # toolbar
        row_1_layout.addWidget(draw_line_button)
        row_1_layout.addWidget(insert_block_button)
        self.f_buttons["draw_line"] = draw_line_button
        self.f_buttons["insert_block"] = insert_block_button
        self.addWidget(row_1)
        self.addSeparator()

    def __display_blocks(self):
        """
        Graphical blocks are displayed in a vertical main_layout, which is put in
        a movable toolbar of fixed size.

        """

        # Labels
        self.toolbar_blocks_label.setAlignment(Qt.AlignCenter)
        self.toolbar_blocks_label.setStyleSheet(style.NODE_LABEL_STYLE)

        # Buttons
        self.addWidget(self.toolbar_blocks_label)
        for b in self.b_buttons.values():
            self.addWidget(b)

    def __display_properties(self):
        """
        Graphical properties are displayed in a vertical main_layout, which is put in
        a movable toolbar of fixed size.

        """

        # Labels
        self.toolbar_properties_label.setAlignment(Qt.AlignCenter)
        self.toolbar_properties_label.setStyleSheet(style.NODE_LABEL_STYLE)

        # Buttons
        self.addWidget(self.toolbar_properties_label)
        for p in self.p_buttons.values():
            self.addWidget(p)

    def change_tools_mode(self):
        """
        This method handles the visibility of the tool section of the toolbar.
        If all sections are not visible, then the toolbar itself is hidden,
        while if the toolbar was hidden, it is shown with the tools section.

        """

        if not self.isToolbar_tools_label_visible:
            self.show_section(self.toolbar_tools_label, self.f_buttons)
            self.isToolbar_tools_label_visible = True

            if not self.isToolbar_blocks_label_visible:
                self.show()
        else:
            self.hide_section(self.toolbar_tools_label, self.f_buttons)
            self.isToolbar_tools_label_visible = False

            if not self.isToolbar_blocks_label_visible:
                self.hide()

    def change_blocks_mode(self):
        """
        This method handles the visibility of the blocks section of the toolbar.
        If all sections are not visible, then the toolbar itself is hidden,
        while if the toolbar was hidden, it is shown with the blocks section.

        """

        if not self.isToolbar_blocks_label_visible:
            self.show_section(self.toolbar_blocks_label, self.b_buttons)
            self.isToolbar_blocks_label_visible = True

            if not self.isToolbar_tools_label_visible:
                self.show()
        else:
            self.hide_section(self.toolbar_blocks_label, self.b_buttons)
            self.isToolbar_blocks_label_visible = False

            if not self.isToolbar_tools_label_visible:
                self.hide()

    @staticmethod
    def show_section(label: CustomLabel, buttons: dict):
        """
        This method shows the given dictionary of buttons with its label.

        Parameters
        ----------
        label: CustomLabel
        buttons: dict

        """

        label.show()
        label.setStyleSheet(style.NODE_LABEL_STYLE)
        for tool in buttons.values():
            tool.show()

    @staticmethod
    def hide_section(label: CustomLabel, buttons: dict):
        """
        This method hides the given dictionary of buttons with its label.

        Parameters
        ----------
        label: CustomLabel
        buttons: dict

        """

        label.hide()
        label.setStyleSheet(style.HIDDEN_LABEL_STYLE)
        for tool in buttons.values():
            tool.hide()
            if type(tool) is NodeButton:
                tool.setStyleSheet(style.HIDDEN_LABEL_STYLE)
