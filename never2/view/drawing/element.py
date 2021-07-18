import abc
import math
import sys

import numpy as np
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QLineF, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPen, QPolygonF
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsPolygonItem, QLabel, \
    QVBoxLayout, QWidget, QGridLayout, QGraphicsProxyWidget, QAction
from pynever.tensor import Tensor

import never2.view.styles as style
import never2.view.util.utility as u

MAX_FLOAT_LABEL_LENGTH = 5


class GraphicLine(QGraphicsLineItem):
    """
    This class is a graphic line with an arrow which connects
    two blocks in the scene.

    Attributes
    ----------
    origin : QGraphicsRectItem
        Origin rect of the line.
    destination : QGraphicsRectItem
        Destination rect of the line.
    scene : QGraphicsScene
        Current drawing scene.
    brush : QBrush
        Brush to draw the arrow.
    pen : QPen
        Pen to draw the arrow.
    arrow_head : QGraphicsPolygonItem
        Final arrow of the line.
    arrow_size : int
        Size of the head of the arrow.
    dim_label : QGraphicsTextItem
        Text showing the dimensions of the edge.
    is_valid : bool
        Flag monitoring whether the connection is consistent.

    Methods
    ----------
    gen_endpoints(QRectF, QRectF)
        Returns the shortest connection between the two rects.
    draw_arrow()
        Draws the polygon for the arrow.
    set_valid(bool)
        Assign validity for this line.
    update_dims(tuple)
        Update the line dimensions.
    update_pos(QRectF)
        Update the line position given the new rect position.
    remove_self()
        Delete this line.

    """

    def __init__(self, origin: QGraphicsRectItem, destination: QGraphicsRectItem, scene):
        super(GraphicLine, self).__init__()
        self.origin = origin
        self.destination = destination
        self.scene = scene

        # This flag confirms a legal connection
        self.is_valid = True

        # Get the four sides of the rects
        destination_lines = u.get_sides_of(self.destination.sceneBoundingRect())
        origin_lines = u.get_sides_of(self.origin.sceneBoundingRect())

        # Get the shortest edge between the two blocks
        self.setLine(self.gen_endpoints(origin_lines, destination_lines))

        self.brush = QBrush(QColor(style.GREY_0))
        self.pen = QPen(QColor(style.GREY_0))
        self.pen.setWidth(4)
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)
        self.setPen(self.pen)

        # Dimensions labels
        self.dim_label = QGraphicsTextItem()
        self.dim_label.setZValue(6)
        self.scene.addItem(self.dim_label)

        # Arrow head
        self.arrow_head = QGraphicsPolygonItem()
        self.arrow_head.setPen(self.pen)
        self.arrow_head.setBrush(self.brush)
        self.arrow_size = 15.0

        self.draw_arrow()

    @staticmethod
    def gen_endpoints(origin_sides: dict, destination_sides: dict) -> QLineF:
        """
        This method finds the shortest path between two rectangles.

        Parameters
        ----------
        origin_sides : dict
            The dictionary {side_label: side_size} of the starting rect.
        destination_sides : dict
            The dictionary {side_label: side_size} of the ending rect.

        Returns
        ----------
        QLineF
            The shortest line.

        """

        # Init the line with the maximum possible value
        shortest_line = QLineF(-sys.maxsize / 2, -sys.maxsize / 2,
                               sys.maxsize / 2, sys.maxsize / 2)
        for o_side, origin_side in origin_sides.items():
            o_mid_x, o_mid_y = u.get_midpoint(o_side, origin_side)

            for d_side, destination_side in destination_sides.items():
                d_mid_x, d_mid_y = u.get_midpoint(d_side, destination_side)

                # Update line
                line = QLineF(o_mid_x, o_mid_y, d_mid_x, d_mid_y)
                if line.length() < shortest_line.length():
                    shortest_line = line

        return shortest_line

    def draw_arrow(self) -> None:
        """
        This method draws an arrow at the end of the line.

        """

        polygon_arrow_head = QPolygonF()

        # Compute the arrow angle
        angle = math.acos(self.line().dx() / self.line().length())
        angle = ((math.pi * 2) - angle)

        # Compute the direction where the arrow points (1 up, -1 down)
        arrow_direction = 1
        if math.asin(self.line().dy() / self.line().length()) < 0:
            arrow_direction = -1

        # First point of the arrow tail
        arrow_p1 = self.line().p2() - arrow_direction * QPointF(
            arrow_direction * math.sin(angle + math.pi / 2.5) * self.arrow_size,
            math.cos(angle + math.pi / 2.5) * self.arrow_size)
        # Second point of the arrow tail
        arrow_p2 = self.line().p2() - arrow_direction * QPointF(
            arrow_direction * math.sin(angle + math.pi - math.pi / 2.5) * self.arrow_size,
            math.cos(angle + math.pi - math.pi / 2.5) * self.arrow_size)

        # Third point is the line end
        polygon_arrow_head.append(self.line().p2())
        polygon_arrow_head.append(arrow_p2)
        polygon_arrow_head.append(arrow_p1)

        # Add the arrow to the scene
        self.arrow_head.setZValue(1)
        self.arrow_head.setParentItem(self)
        self.arrow_head.setPolygon(polygon_arrow_head)

    def set_valid(self, valid: bool) -> None:
        """
        This method changes the arrow style: if the connection 
        is not valid the arrow becomes red, otherwise it 
        remains grey with dimensions displayed. 

        Parameters
        ----------
        valid : bool
            New value for the legality flag.

        """

        if valid:
            self.is_valid = True
            self.pen.setColor(QColor(style.GREY_0))
            self.brush.setColor(QColor(style.GREY_0))
            self.dim_label.setVisible(False)
        else:
            self.is_valid = False
            self.pen.setColor(QColor(style.RED_2))
            self.brush.setColor(QColor(style.RED_2))

            if self.scene.is_dim_visible:
                self.dim_label.setVisible(True)

    def update_dims(self, dims: tuple) -> None:
        """
        This method updates the input & output dimensions.

        Parameters
        ----------
        dims : tuple
            The new dimensions to update.

        """

        self.dim_label.setHtml("<div style = 'background-color: " + style.RED_2 +
                               "; color: white; font-family: consolas;'>" +
                               str(dims) + "</div>")
        self.dim_label.setPos(self.line().center())

    def update_pos(self, new_target: QRectF):
        """
        This method updates the line as it origin or its destination has
        changed location.

        Parameters
        ----------
        new_target : QRectF

        """

        if new_target == self.destination:
            self.destination = new_target
        elif new_target == self.origin:
            self.origin = new_target

        # Get the four sides of the rects
        destination_lines = u.get_sides_of(self.destination.sceneBoundingRect())
        origin_lines = u.get_sides_of(self.origin.sceneBoundingRect())

        # Get the shortest edge between the two blocks
        self.setLine(self.gen_endpoints(origin_lines, destination_lines))
        self.draw_arrow()
        self.dim_label.setPos(self.line().center())

    def remove_self(self) -> None:
        """
        The line is removed from the scene along with origin and destination
        pointers.

        """

        self.scene.removeItem(self)
        self.scene.edges.remove(self)
        self.scene.removeItem(self.dim_label)
        self.origin = None
        self.destination = None


class GraphicBlock(QtWidgets.QWidget):
    """
    This class works as a base class for graphical block objects in
    CoCoNet. It provides a rectangle widget that can be customized
    by inheriting from this class.

    Attributes
    ----------
    block_id : str
        String unique identifier for the block.
    main_layout : QVBoxLayout
        Block layout, vertical by default.
    content_layout : QGridLayout
        Block content layout, a grid with <param, value>
        entries.
    rect : QGraphicsRectItem
        pyQt rectangle object associated to the block.
    proxy_control : QGraphicsProxyWidget
        pyQt proxy holding the widget inside the scene.
    title_label : QLabel
        pyQt label for the block head.
    context_actions : dict
        Dictionary of context menu actions.

    Methods
    ----------
    init_layout()
        Abstract method that builds the block layout.
    set_proxy(QGraphicsProxyWidget)
        Procedure to assign a proxy controller to the block.
    set_rect(QGraphicsRectItem)
        Procedure to assign a rect item to the block.
    set_context_menu(dict)
        Procedure to assign a context menu to the block.
    resizeEvent(QtGui.QResizeEvent)
        Procedure to handle the resizing of the widget.
    x()
        Top-left x coordinate getter.
    y()
        Top-left y coordinate getter.

    """

    def __init__(self, block_id: str):
        super(GraphicBlock, self).__init__()
        self.block_id = block_id
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.title_label = QLabel("Graphic block")
        self.content_layout = QGridLayout()
        self.rect = None
        self.proxy_control = None
        self.context_actions = dict()

        self.setLayout(self.main_layout)

        # Set style and transparent background for the rounded corners
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(style.GRAPHIC_BLOCK_STYLE)

    @abc.abstractmethod
    def init_layout(self):
        """
        Abstract method to implement in child class(es).

        """
        pass

    def init_grid(self):
        """
        This method builds a grid layout for displaying
        the block parameters in an ordered way.

        """
        grid = QWidget()
        grid.setLayout(self.content_layout)
        self.main_layout.addWidget(grid)

    def set_proxy(self, proxy: QGraphicsProxyWidget) -> None:
        """
        This method assigns a pyQt proxy controller to the
        graphic block.

        Parameters
        ----------
        proxy : QGraphicsProxyWidget
            The controller to set.

        """

        self.proxy_control = proxy

    def set_rect_item(self, rect: QGraphicsRectItem) -> None:
        """
        This method assigns a pyQt rect object to the
        graphic block.

        Parameters
        ----------
        rect : QGraphicsRectItem
            The rectangle widget associated to the block.

        """

        self.rect = rect

    def set_context_menu(self, actions: dict) -> None:
        """
        This method builds a context menu with the given actions.

        Parameters
        ----------
        actions : dict
            The menu actions to display.

        """

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        for k, v in actions.items():
            self.context_actions[k] = v
            self.addAction(v)

    def resizeEvent(self, evt: QtGui.QResizeEvent) -> None:
        """
        This method resizes the selection rectangle when a
        QResizeEvent happens.

        Parameters
        ----------
        evt : QResizeEvent
            The resize event.

        """

        if self.proxy_control is not None:
            # The new dimensions of the rect are given by the new dimensions
            # of the proxy widget
            x = self.proxy_control.geometry().x() + 10
            y = self.proxy_control.geometry().y() + 10
            width = self.proxy_control.geometry().width() - 20
            height = self.proxy_control.geometry().height() - 20

            self.rect.setRect(QRectF(x, y, width, height))

    def x(self) -> float:
        """
        Returns the x coordinate top-left corner of the rect.

        Returns
        ----------
        float
            The absolute coordinate.

        """

        return self.rect.x()

    def y(self) -> float:
        """
        Returns the y coordinate top-left corner of the rect.

        Returns
        ----------
        float
            The absolute coordinate.

        """

        return self.rect.y()


class NodeBlock(GraphicBlock):
    """
    This class is a widget for drawing the network nodes as
    blocks in the Canvas scene.

    Attributes
    ----------
    node : NetworkNode
        Node associated to the block.
    block_data : dict
        Dictionary holding the node parameters, with string
        keys and numerical values.
    in_dim : tuple
        Copy of node input for visualization.
    out_dim : tuple
        Copy of node output for visualization.
    dim_labels : dict
        Dictionary with parameter dimension labels.
    is_head : bool
        Tells if the node is the head of the network.
    edits : dict
        Dictionary storing the parameters to update.

    Methods
    ----------
    text_to_tuple(str)
        Procedure to convert a string in a tuple.
    update_labels()
        Procedure to update the labels after a change.

    """

    edited = pyqtSignal()

    def __init__(self, block_id, node):
        super().__init__(block_id)
        self.node = node
        self.block_data = dict()
        self.in_dim = (1,)
        self.out_dim = (1,)

        self.is_head = True
        self.edits = None
        self.dim_labels = dict()

        # Override title label
        self.title_label.setText(self.node.name)
        self.title_label.setStyleSheet(style.NODE_TITLE_STYLE)
        self.main_layout.addWidget(self.title_label)

        if self.node.param:
            self.init_layout()
        else:
            self.title_label.setStyleSheet(style.EMPTY_NODE_TITLE)

        self.init_context_menu()

    def init_layout(self) -> None:
        """
        This method sets up the the node block main_layout with
        attributes and values.

        """

        self.init_grid()

        # Iterate and display parameters, count rows
        par_labels = dict()
        count = 1
        for name, param in self.node.param.items():
            # Set the label
            par_labels[name] = QLabel(name)
            par_labels[name].setAlignment(Qt.AlignLeft)
            par_labels[name].setStyleSheet(style.PAR_NODE_STYLE)

            self.dim_labels[name] = QLabel()
            self.dim_labels[name].setAlignment(Qt.AlignCenter)
            self.dim_labels[name].setStyleSheet(style.DIM_NODE_STYLE)

            self.content_layout.addWidget(par_labels[name], count, 0)
            self.content_layout.addWidget(self.dim_labels[name], count, 1)
            count += 1

            # Init block data with default values
            if "default" in param.keys() and param["default"] == "None":
                self.block_data[name] = None
            elif param["type"] == "Tensor":
                if "shape" in param.keys():
                    shape = self.text_to_tuple(param["shape"])
                    self.block_data[name] = Tensor(shape=shape, buffer=np.random.normal(size=shape))
                else:
                    self.block_data[name] = Tensor(shape=(1, 1), buffer=np.random.normal(size=(1, 1)))
            elif param["type"] == "int":
                if "default" in param.keys():
                    if param["default"] == "rand":
                        self.block_data[name] = 1
                    else:
                        self.block_data[name] = int(param["default"])
                else:
                    self.block_data[name] = 1
            elif param["type"] == "list of ints":
                if "default" in param.keys():
                    self.block_data[name] = tuple(map(int, param["default"].split(', ')))
                else:
                    self.block_data[name] = (1, 1)
            elif param["type"] == "float":
                if "default" in param.keys():
                    if param["default"] == "rand":
                        self.block_data[name] = 1
                    else:
                        self.block_data[name] = float(param["default"])
                else:
                    self.block_data[name] = 0.1
            elif param["type"] == "boolean":
                if "default" in param.keys():
                    self.block_data[name] = bool(param["default"])
                else:
                    self.block_data[name] = False

        self.update_labels()
        self.edited.connect(lambda: self.update_labels())

    def init_context_menu(self):
        """
        This method sets up the context menu actions that
        are available for the block.

        """

        block_actions = dict()
        block_actions["Copy"] = QAction("Copy", self)
        block_actions["Cut"] = QAction("Cut", self)
        block_actions["Delete"] = QAction("Delete", self)
        block_actions["Edit"] = QAction("Edit", self)
        block_actions["Parameters"] = QAction("Parameters", self)
        self.set_context_menu(block_actions)

    def text_to_tuple(self, text: str) -> tuple:
        """
        This method creates a tuple from a string, provided
        the string represents a tuple of dimensions.

        Parameters
        ----------
        text : str
            The dimension description string.

        Returns
        ----------
        tuple
            The tuple containing the dimensions.

        """

        str_shape = tuple(map(str, text.split(', ')))
        shape = tuple()
        for dim in str_shape:
            if isinstance(self.block_data[dim], tuple):
                shape += self.block_data[dim]
            else:
                shape += (self.block_data[dim],)
        return shape

    def update_labels(self) -> None:
        """
        This method updates the labels displaying the
        parameters dimension.

        """

        for name, param in self.node.param.items():
            value = self.block_data[name]

            # If the parameter is a Tensor write Shape
            if isinstance(value, Tensor) or isinstance(value, np.ndarray):  # TODO Necessary?
                self.dim_labels[name].setText("<" + 'x'.join(map(str, value.shape)) + ">")

            # If the floating-point digits are too many truncate it
            elif isinstance(value, float):
                if len(str(value)) <= MAX_FLOAT_LABEL_LENGTH + 3:  # The "+ 3" is used to take into account the "..."
                    self.dim_labels[name].setText("<" + str(value) + ">")
                else:
                    string = u.truncate(value, MAX_FLOAT_LABEL_LENGTH)
                    self.dim_labels[name].setText("<" + string + "...>")

            elif isinstance(value, int) or isinstance(value, bool):
                self.dim_labels[name].setText("<" + str(value) + ">")

            elif isinstance(value, tuple):
                self.dim_labels[name].setText("<" + 'x'.join(map(str, value)) + ">")


class PropertyBlock(GraphicBlock):
    """
    This class represents the widget associated to a
    SMTLIB property in CoCoNet.

    Attributes
    ----------
    property_type : str
        The property type (SMT, Polyhedral...).
    smt_string : str
        The SMT-LIB expression of the property.
    property_label : QLabel
        The visible label of the property.
    condition_label : QLabel
        The POST or PRE label of the property.
    variables : list
        The list of admissible variables
        for the property.

    """

    def __init__(self, block_id: str, p_type: str):
        super().__init__(block_id)
        self.property_type = p_type
        self.pre_condition = True
        self.smt_string = ""
        if p_type == "Generic SMT":
            self.label_string = "-"
        elif p_type == "Polyhedral":
            self.label_string = "Ax - b <= 0"

        self.condition_label = QLabel("PRE")
        self.property_label = QLabel(self.label_string)
        self.variables = []
        self.init_layout()
        self.init_context_menu()

    def init_layout(self) -> None:
        """
        This method sets up the the property block main_layout with
        the property parameters.

        """

        # Override title label
        self.title_label.setText(self.property_type)
        self.title_label.setStyleSheet(style.PROPERTY_TITLE_STYLE)
        self.condition_label.setStyleSheet(style.PROPERTY_CONDITION_STYLE)
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.condition_label)

        self.init_grid()

        formula_label = QLabel("Formula")
        formula_label.setStyleSheet(style.PAR_NODE_STYLE)
        self.property_label.setStyleSheet(style.DIM_NODE_STYLE)
        self.content_layout.addWidget(formula_label, 1, 0)
        self.content_layout.addWidget(self.property_label, 1, 1)

    def init_context_menu(self):
        """
        This method sets up the context menu actions that
        are available for the block.

        """

        block_actions = dict()
        block_actions["Define"] = QAction("Define...", self)
        self.set_context_menu(block_actions)

    def set_label(self):
        self.property_label.setText(self.label_string)

    def set_smt_label(self):
        self.property_label.setText(self.smt_string)

    def update_condition_label(self):
        if self.pre_condition:
            self.condition_label.setText("PRE")
        else:
            self.condition_label.setText("POST")
