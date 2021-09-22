from enum import Enum
from typing import Optional

import numpy as np
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt, QPoint, QRectF, pyqtSignal, QRect
from PyQt5.QtGui import QBrush, QColor, QPen, QPainter
from PyQt5.QtWidgets import QGraphicsRectItem, QWidget, QGraphicsScene, QApplication, QGraphicsItem, \
    QGraphicsSceneMouseEvent
from pynever import nodes
from pynever.networks import SequentialNetwork, NeuralNetwork
from pynever.tensor import Tensor

import never2.view.styles as style
from never2.core.controller.nodewrapper import NodeOps
from never2.core.controller.project import Project
from never2.core.model.network import NetworkNode
from never2.view.drawing.element import NodeBlock, GraphicLine, PropertyBlock, GraphicBlock
from never2.view.drawing.renderer import SequentialNetworkRenderer
from never2.view.util import utility
from never2.view.widget.dialog.dialogs import MessageDialog, MessageType, EditSmtPropertyDialog, \
    EditPolyhedralPropertyDialog, EditNodeDialog, FuncDialog
from never2.view.widget.dialog.windows import TrainingWindow, VerificationWindow


class DrawingMode(Enum):
    """
    This class represents the possible drawing modes in the scene.

    """

    IDLE = 0
    DRAW_LINE = 1
    DRAW_BLOCK = 2


class Canvas(QWidget):
    """
    This class displays the neural network combining the graphic blocks with
    their logical meaning.

    Attributes
    ----------
    zooms : int
        This number tracks how many times the view is zoomed in (if positive)
        or zoomed out (negative)
    num_nodes : int
        Number of node blocks in the scene.
    num_props : int
        Number of property blocks in the scene.
    blocks : dict
        Dictionary of the blocks in the scene that have as key the rects, and
        as value the widget block.
    block_to_show : NodeBlock
        Holds the eventual block whose description has to be displayed.
    renderer : SequentialNetworkRenderer
        Object which checks the network and build the logical network in
        parallel.
    scene : NetworkScene
        Graphic scene which holds all graphic items.
    copied_items : list
        Auxiliary variable used for the copy of items.
    view : QGraphicsView
        View of the scene.

    Methods
    ----------
    update_scene()
        Update canvas drawing.
    insert_node()
        Insert a block between two blocks already connected.
    draw_line_between_selected()
        Draw a connection between two blocks.
    draw_line_between(QGraphicsRectItem, QGraphicsRectItem)
        Draw a connection between the two given blocks.
    draw_node(NetworkNode, GraphicBlock, QPoint)
        Add to the scene a new block of the given type or copy an
        existing one, possibly at a defined location.
    draw_property(NetworkProperty, GraphicBlock, QPoint)
        Add to the scene a new property or copy an existing one.
    show_parameters(QGraphicBlock)
        Emit a signal to show parameters of a block.
    edit_node(QGraphicBlock)
        Let the user change the parameters of a block.
    delete_selected()
        Delete the selected block.
    copy_selected(GraphicBlock)
        Copy the selected block or the one passed as parameter.
    cut_selected()
        Copy and delete the selected block.
    paste_selected()
        Paste the block copied.
    clear_scene()
        Remove all blocks and connections from the scene.
    draw_network(SequentialNetworkRender)
        Draw the given network.
    zoom_in()
        Zoom in view.
    zoom_out()
        Zoom out view.

    """

    # This signal is emitted when the description box should appear
    param_requested = pyqtSignal()

    # Zoom scale
    ZOOM_FACTOR = 1.1

    # Max number of zoom allowed
    MAX_ZOOM = 100

    def __init__(self, blocks: dict):
        super(Canvas, self).__init__()
        self.zooms = 0
        self.num_nodes = 0
        self.num_props = 0

        self.project = Project()
        self.project.opened_net.connect(lambda: self.draw_network(self.project.network))
        self.project.opened_property.connect(lambda: self.draw_properties())

        self.renderer = SequentialNetworkRenderer(self.project.network, blocks)

        self.scene = NetworkScene(self)
        self.scene.selectionChanged.connect(lambda: self.update_scene())

        self.copied_items = list()
        self.block_to_show = None

        # Set up the canvas view
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.view.setStyleSheet(style.VIEW_STYLE)
        self.view.verticalScrollBar().setStyleSheet(style.VERTICAL_SCROLL_BAR)
        self.view.horizontalScrollBar().setStyleSheet(style.HORIZONTAL_SCROLL_BAR)
        self.view.setRenderHints(QPainter.Antialiasing)

        self.scene.addWidget(self)
        self.setStyleSheet(style.CANVAS_STYLE)

    def get_input_variables(self) -> list:
        head = self.renderer.NN.get_first_node()
        return utility.create_variables_from(self.renderer.NN.input_id, head.in_dim)

    def update_scene(self):
        """
        This method calls a drawing method according to the current mode.

        """

        if self.scene.mode == DrawingMode.DRAW_LINE:
            self.draw_line_between_selected()
        elif self.scene.mode == DrawingMode.DRAW_BLOCK:
            self.insert_node()

    def insert_node(self):
        """
        This method inserts a block inside the network. The selected
        edge is split in two edges.

        """

        result = self.scene.add_node()
        if result is not None:
            # Nodes
            prev_node = self.scene.blocks[result[0]]
            middle_node = self.scene.blocks[result[1]]

            # Edges
            old_line = result[2]
            l1 = result[3]
            l2 = result[4]

            try:
                # The logical network is modified
                legal = self.renderer.insert_node(prev_node.block_id, middle_node.block_id)
            except Exception as e:
                # In case of error, the new edges are deleted
                l1.remove_self()
                l2.remove_self()
                # a Message is displayed
                dialog = MessageDialog(str(e), MessageType.ERROR)
                dialog.exec()
                return

            try:
                if not legal:
                    # If the modification is not possible, the new edges are
                    # removed
                    l1.remove_self()
                    l2.remove_self()
                    dialog = MessageDialog("Sequential network : illegal operation.",
                                           MessageType.ERROR)
                    dialog.exec()
                else:
                    # Otherwise the old edge is removed
                    old_line.remove_self()

                    # inputs and dimensions labels are updated
                    out_dim_1 = self.renderer.NN.nodes[prev_node.block_id].out_dim
                    out_dim_2 = self.renderer.NN.nodes[middle_node.block_id].out_dim

                    # Dimension labels are updated
                    l1.update_dims(out_dim_1)
                    l2.update_dims(out_dim_2)
                    self.scene.blocks[result[0]].out_dim = out_dim_1

                    # Scene blocks are updated
                    self.scene.blocks[l2.origin].in_dim = out_dim_1
                    self.scene.blocks[l2.destination].in_dim = out_dim_2

                    self.scene.blocks[l2.origin].is_head = False
            except Exception as e:
                next_node = self.scene.blocks[l2.destination]
                if prev_node.out_dim is not middle_node.in_dim:
                    l1.set_valid(False)
                if middle_node.out_dim is not next_node.in_dim:
                    l2.set_valid(False)

                dialog = MessageDialog(str(e) + "\nPlease check dimensions.",
                                       MessageType.ERROR)
                dialog.exec()

    def draw_line_between_selected(self):
        """
        This method draws a line if an item was selected in draw_line mode.
        If the connection is legal, the network is updated, otherwise the edge
        is deleted.

        """

        # The method draw_line returns a tuple of the two blocks connected
        conn_nodes = self.scene.add_line()
        if conn_nodes is not None:
            origin = self.scene.blocks[conn_nodes[0]]
            destination = self.scene.blocks[conn_nodes[1]]

            if isinstance(origin, NodeBlock) and isinstance(destination, PropertyBlock):
                conn_nodes[2].remove_self()
                dialog = MessageDialog("Illegal property connection.", MessageType.ERROR)
                dialog.exec()
                return

            if isinstance(origin, PropertyBlock) and isinstance(destination, NodeBlock):
                origin.variables = utility.create_variables_from(destination.block_id, destination.out_dim)
                origin.pre_condition = False
                origin.condition_label.setText("POST")

                # Properties dict is {node_id: property}
                if origin in self.project.properties.values():
                    # Find key of origin
                    key = list(self.project.properties.keys())[list(self.project.properties.values()).index(origin)]
                    del self.project.properties[key]

                self.project.properties[destination.block_id] = origin
                return

            try:
                # Add the new node to the network
                legal = self.renderer.add_edge(origin.block_id,
                                               destination.block_id)
                if legal:
                    if self.renderer.NN.get_first_node().identifier == origin.block_id:
                        origin.is_head = True

                    # Draw dimensions
                    in_dim = self.renderer.NN.nodes[destination.block_id].in_dim

                    if isinstance(self.renderer.NN.nodes[destination.block_id], nodes.FullyConnectedNode):
                        out_dim = self.renderer.NN.nodes[destination.block_id].out_features
                    else:
                        out_dim = self.renderer.NN.nodes[destination.block_id].out_dim

                    self.scene.blocks[conn_nodes[0]].out_dim = in_dim
                    self.scene.blocks[conn_nodes[1]].out_dim = out_dim
                    destination.in_dim = in_dim
                    destination.is_head = False

                    drawn_edge = conn_nodes[2]
                    drawn_edge.update_dims(in_dim)

                else:
                    # If the edge is illegal for a legal network, it is removed
                    conn_nodes[2].remove_self()
                    dialog = MessageDialog("Sequential network : illegal edge.",
                                           MessageType.ERROR)
                    dialog.exec()
            except Exception as e:
                # If an error occurs, the edge is removed
                conn_nodes[2].remove_self()
                dialog = MessageDialog(str(e), MessageType.ERROR)
                dialog.exec()

    def draw_line_between(self, origin_id: str, destination_id: str):
        """
        This method connects automatically the two rects given with an edge.

        Parameters
        ----------
        origin_id : str
            The origin node for the edge
        destination_id : str
            The destination node for the edge

        """

        origin_item = None
        destination_item = None

        # Find the rects corresponding to the given ids
        for rect, block in self.scene.blocks.items():
            if block.block_id == origin_id:
                origin_item = rect
            if block.block_id == destination_id:
                destination_item = rect

            if origin_item is not None and destination_item is not None:
                if "Pr" in origin_id:
                    self.scene.auto_add_line(origin_item, destination_item)
                    return
                try:
                    # Update the node input
                    NodeOps.update_node_input(
                        self.renderer.NN.nodes[destination_id],
                        self.renderer.NN.nodes[origin_id].out_dim)

                    # Update sequential nodes, if any
                    if len(self.renderer.NN.edges[destination_id]) > 1:
                        self.renderer.update_network_from(destination_id, origin_id)

                    # The new line is drawn
                    line = self.scene.auto_add_line(origin_item, destination_item)
                    out_dim = self.renderer.NN.nodes[
                        self.scene.blocks[origin_item].block_id].out_dim
                    line.update_dims(out_dim)

                    self.scene.blocks[origin_item].out_dim = out_dim
                    self.scene.blocks[destination_item].in_dim = out_dim
                    self.scene.blocks[destination_item].out_dim = self.renderer.NN.nodes[
                        self.scene.blocks[destination_item].block_id].out_dim
                    return

                except Exception as e:
                    self.renderer.delete_edge_from(origin_id)
                    dialog = MessageDialog(str(e) + "\nPlease check dimensions.",
                                           MessageType.ERROR)
                    dialog.exec()
                    return

    def set_position(self, pos: QPoint, offset: int) -> QPoint:
        """
        This method computes the position for a new Graphic
        Block to insert in the scene. A starting point can be
        provided, along with the offset.

        Parameters
        ----------
        pos : QPoint
            The given position for the block.
        offset : int
            The offset to move the new computed point.

        Returns
        -------
        QPoint
            The new position for the block.

        """

        if pos is not None:
            return pos

        # Get the visible area of the scene
        viewport_rect = QRect(0, 0, self.view.viewport().width(),
                              self.view.viewport().height())
        viewport = self.view.mapToScene(viewport_rect).boundingRect()
        start_x = viewport.x()
        start_y = viewport.y()

        # The initial point of each block is translated of 20px in order not to
        # overlap them (always in the visible area)
        return QPoint(start_x + 20 * (offset % 20) + 20,
                      start_y + 20 * (offset % 20) + 20)

    def create_rect(self, block: GraphicBlock, pos: QPoint) -> None:
        """
        This method manages the pyQt operations to build
        and add the rectangle item that represents the
        given Graphic Block.

        Parameters
        ----------
        block : GraphicBlock
            The block to which the rectangle is associated.
        pos : QPoint
            The insertion point in the view.

        """

        proxy = self.scene.addWidget(block)

        # Create the parent rect
        rect = QRectF(pos.x() + 10, pos.y() + 10,
                      block.width() - 20, block.height() - 20)

        # Add rect
        transparent = QColor(0, 0, 0, 0)
        rect = self.scene.addRect(rect, QPen(transparent), QBrush(transparent))
        rect.setFlag(QGraphicsItem.ItemIsMovable, True)
        rect.setFlag(QGraphicsItem.ItemIsSelectable, True)
        rect.setZValue(10)
        proxy.setParentItem(rect)
        proxy.setPos(pos.x(), pos.y())
        block.set_proxy(proxy)
        block.set_rect_item(rect)
        self.scene.blocks[rect] = block

    def draw_node(self, block_type: NetworkNode = None, copy: NodeBlock = None,
                  pos: QPoint = None) -> NodeBlock:
        """
        This method draws a new block, either by the selection of
        a toolbar item or by the copy of an existing one.

        Parameters
        ----------
        block_type : NetworkNode
            The concrete network block (new graphical item)
        copy : NodeBlock
            The graphical block (copy item)
        pos : QPoint
            Position to draw the block

        Returns
        ----------
        NodeBlock
            The new block created

        """

        assert block_type is None or copy is None, \
            "Improper use of method, only a block must be specified."

        # Create a new block or copy the given one
        block = None
        if copy is not None:
            block = NodeBlock("", copy.node)
            block.block_data = copy.block_data
            block.in_dim = copy.in_dim
            block.update_labels()
        else:
            block = NodeBlock("", block_type)

        # Create the identifier
        if copy is not None and \
                copy not in self.scene.blocks.values():
            block.block_id = copy.block_id
        else:
            new_block_id = str(self.num_nodes) + block.node.name[0:2]
            block.block_id = new_block_id

        # Create block in view
        point = self.set_position(pos, self.num_nodes)
        self.create_rect(block, point)

        # Finalize block and update scene
        block.context_actions["Copy"].triggered \
            .connect(lambda: self.copy_selected(block))
        block.context_actions["Cut"].triggered \
            .connect(lambda: self.cut_selected())
        block.context_actions["Delete"].triggered \
            .connect(lambda: self.delete_selected())
        block.context_actions["Edit"].triggered \
            .connect(lambda: self.scene.edit_block(block))
        block.context_actions["Parameters"].triggered \
            .connect(lambda: self.show_parameters(block))

        block.edited.connect(lambda: self.edit_node(block))

        self.num_nodes += 1
        self.update_scene()
        self.renderer.add_disconnected_block(block)

        return block

    def draw_property(self, property_type: str = "", copy: PropertyBlock = None,
                      pos: QPoint = None, add_dict_entry: bool = True) -> PropertyBlock:
        """
        This method creates a graphic PropertyBlock for representing
        the property to draw. If the property is legal, the PropertyBlock
        is created and returned.

        Parameters
        ----------
        property_type : str, optional
            The property to draw on the canvas.
        copy : PropertyBlock, optional
            The property to copy in the canvas.
        pos : QPoint, optional
            The position to draw the property.
        add_dict_entry : boolean, optional
            Flag that allows to add an entry in the
            properties dictionary.

        Returns
        -------
        PropertyBlock
            The graphical property block to add.

        """

        assert property_type == "" or copy is None, \
            "Improper use of method, only a block must be specified."

        # Create a new block or copy the given one
        if copy is not None:
            block = PropertyBlock("", copy.property_type)
            block.smt_string = copy.smt_string
        else:
            block = PropertyBlock("", property_type)

        # Create the identifier
        if copy is not None and \
                copy not in self.scene.blocks.values():
            block.block_id = copy.block_id
        else:
            new_block_id = str(self.num_props) + "Pr"
            block.block_id = new_block_id

        # Create block in view
        point = self.set_position(pos, self.num_props)
        self.create_rect(block, point)

        # Finalize block and update scene
        block.context_actions["Define"].triggered \
            .connect(lambda: Canvas.define_property(block))
        self.num_props += 1
        block.variables = self.get_input_variables()
        if add_dict_entry:
            self.project.properties[f"{self.num_props - 1}Pr"] = block
        self.renderer.add_property_block(block)

        return block

    @staticmethod
    def define_property(item: PropertyBlock) -> None:
        if item.property_type == "Generic SMT":
            dialog = EditSmtPropertyDialog(item)
            dialog.exec()

            if dialog.has_edits:
                item.smt_string = dialog.new_property
                item.set_smt_label()
        elif item.property_type == "Polyhedral":
            dialog = EditPolyhedralPropertyDialog(item)
            dialog.exec()

            if dialog.has_edits:
                if item.label_string == 'Ax - b <= 0':
                    item.label_string = ''
                for p in dialog.property_list:
                    item.label_string += f"{p[0]} {p[1]} {p[2]}\n"
                    item.smt_string += '(assert (' + f"{p[1]} {p[0]} {float(p[2])}" + '))\n'
                item.set_label()

    def show_parameters(self, block: NodeBlock = None):
        """
        If no block is specified, the last element in the object list is selected.
        If an element is selected, the request for details is emitted.

        Parameters
        ----------
        block : NodeBlock
            Optional selected block to show info of.

        """

        if block is None:
            # Get the first selected element
            if len(self.scene.selectedItems()) > 0:
                rect = self.scene.selectedItems().pop()
                # Check it is not a line
                while type(rect) == GraphicLine and len(self.scene.selectedItems()) > 0:
                    rect = self.scene.selectedItems().pop()

                block = self.scene.blocks[rect]

        # Check again
        if block is not None:
            self.block_to_show = block
            self.param_requested.emit()

    def edit_node(self, block: NodeBlock):
        """
        This method propagates the changes stored in the block.edits
        attribute.

        Parameters
        ----------
        block : NodeBlock
            The block to update.

        """

        edits = block.edits
        if edits is not None and block.block_id in self.renderer.disconnected_network.keys():
            edit_node_id = edits[0]
            edit_data = edits[1]
            new_in_dim = None
            if "in_dim" in edit_data.keys():
                new_in_dim = edit_data["in_dim"]

            # If in_dim changes to fully connected, update in_features
            if block.node.name == "Fully Connected" and new_in_dim is not None:
                edit_data["in_features"] = new_in_dim[-1]

            for block_par, info in block.node.param.items():
                if "shape" in info:
                    str_shape = tuple(map(str, info["shape"].split(', ')))
                    new_shape = tuple()  # Confront
                    for dim in str_shape:
                        new_dim = block.block_data[dim]
                        if dim in edit_data:
                            new_dim = edit_data[dim]
                        if isinstance(new_dim, tuple):
                            new_shape += new_dim
                        else:
                            new_shape += (new_dim,)

                    # Add new Tensor value to edit_data
                    edit_data[block_par] = Tensor(shape=new_shape, buffer=np.random.normal(size=new_shape))

            try:  # Check if the network has changed
                self.renderer.edit_node(edit_node_id, edit_data)
            except Exception as e:
                dialog = MessageDialog(str(e) + "\nChanges not applied.",
                                       MessageType.ERROR)
                dialog.exec()

            # Update the graphic block
            self.renderer.disconnected_network[edit_node_id].update_labels()

            # Update dimensions in edges & nodes
            for line in self.scene.edges:
                if isinstance(self.scene.blocks[line.origin], NodeBlock):
                    origin_id = self.scene.blocks[line.origin].block_id
                    new_dim = self.renderer.NN.nodes[origin_id].out_dim
                    line.update_dims(new_dim)
                    self.scene.blocks[line.origin].out_dim = new_dim
                    self.scene.blocks[line.destination].in_dim = new_dim

            # Empty changes buffer
            block.edits = None

    def delete_selected(self):
        """
        This method deletes the selected block or edge.

        """

        if self.scene.mode != DrawingMode.IDLE:
            dialog = MessageDialog("Cannot delete items in draw or insert mode.",
                                   MessageType.MESSAGE)
            dialog.exec()
        else:
            # Get selected item to delete
            item = self.scene.delete_selected()
            if item is not None:
                if type(item) == QGraphicsRectItem:
                    if self.scene.blocks[item].block_id in self.project.properties.keys():
                        self.project.properties.pop(self.scene.blocks[item].block_id)
                    if self.scene.blocks[item].block_id in self.renderer.NN.nodes.keys():
                        # Get the first node
                        first_node = self.renderer.NN.get_first_node()

                        # If the node is in the network, delete it
                        new_tuple = self.renderer.delete_node(self.scene.blocks[item].block_id)

                        # If there was a connection, preserve it
                        if new_tuple is not None:
                            self.draw_line_between(new_tuple[0], new_tuple[1])

                            # New first node
                            new_first_node = self.renderer.NN.get_first_node()
                            # If the first node is changed
                            if first_node is not new_first_node:
                                self.renderer.disconnected_network[new_first_node.identifier] \
                                    .is_head = True

                    # Delete block if not in connected network
                    if self.scene.blocks[item].block_id in self.renderer.disconnected_network:
                        self.renderer.disconnected_network.pop(self.scene.blocks[item].block_id)

                    # Remove item
                    self.scene.removeItem(item)
                    self.scene.blocks.pop(item)

                elif type(item) == GraphicLine:
                    # Deleting an edge makes the network non sequential
                    block_before = self.scene.blocks[item.origin]
                    block_after = self.scene.blocks[item.destination]

                    if isinstance(block_before, PropertyBlock):
                        if block_after.block_id in self.project.properties.keys():
                            del self.project.properties[block_after.block_id]
                        self.scene.removeItem(block_before.rect)
                        self.scene.blocks.pop(block_before.rect)
                    else:
                        block_after.is_head = True

                    self.renderer.delete_edge_from(block_before.block_id)
                    item.remove_self()

            # Delete other selected items
            if self.scene.selectedItems():
                self.delete_selected()

    def copy_selected(self, item: NodeBlock = None):
        """
        Save the selected item or the parameter in order to paste it.

        """

        self.copied_items.clear()

        if item is not None:
            self.copied_items.append(item)
        elif len(self.scene.selectedItems()) > 0:
            for sel_item in self.scene.selectedItems():
                if type(sel_item) == QGraphicsRectItem:
                    self.copied_items.append(self.scene.blocks[sel_item])

    def cut_selected(self):
        """
        This method deletes the selected node after copy.

        """

        self.copy_selected()
        self.delete_selected()

    def paste_selected(self):
        """
        Create new item from the copy list, if any.

        """

        if self.copied_items:
            for copied_item in self.copied_items:
                if isinstance(copied_item, NodeBlock):
                    self.draw_node(None, copied_item)
                elif isinstance(copied_item, PropertyBlock):
                    self.draw_property("", copied_item)

    def clear_scene(self):
        """
        This method deletes all blocks and connections.

        """

        self.renderer.disconnected_network = {}
        self.project.network = SequentialNetwork("", "X")
        self.renderer.NN = self.project.network

        # Recreate the scene
        self.scene = NetworkScene(self)
        self.scene.selectionChanged.connect(lambda: self.update_scene())
        self.block_to_show = None
        self.num_nodes = 0

        # Set the canvas view
        self.view.setScene(self.scene)
        self.scene.set_mode(DrawingMode.IDLE)
        self.view.update()

    def draw_network(self, network: NeuralNetwork):
        """
        This method draws in the canvas the given Neural Network,
        associating nodes and edges with blocks and edges.

        Parameters
        ----------
        network: NeuralNetwork
            The given network to draw.

        """

        # Renderer returns the elements to draw
        self.renderer.NN = network
        to_draw = self.renderer.render()
        nodes = to_draw[0]
        edges = to_draw[1]

        # Track the total height for ordering the network
        tot_height = 0

        for block in nodes.values():
            # For each block draw the corresponding graphic
            new_block = self.draw_node(copy=block,
                                       pos=QPoint(50, tot_height))
            # Increment height as block.h + 50
            tot_height += (new_block.rect.rect().height() + 50)

        for edge in edges:
            # Draw connections
            if edge[0] is not None and edge[1] is not None:
                self.draw_line_between(edge[0], edge[1])

    def draw_properties(self):
        tot_height = 0
        for n, p in self.project.properties.items():
            for node in self.project.network.nodes.values():
                if n == self.project.network.input_id:
                    new_p = self.draw_property(copy=p, pos=QPoint(350, tot_height), add_dict_entry=False)
                    new_p.set_smt_label()
                    new_p.pre_condition = True
                    new_p.update_condition_label()
                    tot_height += (new_p.rect.rect().height() + 50)
                    self.draw_line_between(new_p.block_id, n)
                    break
                if n == node.identifier:
                    new_p = self.draw_property(copy=p, pos=QPoint(350, tot_height), add_dict_entry=False)
                    new_p.set_smt_label()
                    new_p.pre_condition = False
                    new_p.update_condition_label()
                    tot_height += (new_p.rect.rect().height() + 50)
                    self.draw_line_between(new_p.block_id, n)
                    break

    def train_network(self):
        if not self.renderer.NN.nodes:
            dialog = MessageDialog("No network to train.", MessageType.ERROR)
            dialog.exec()
        else:
            window = TrainingWindow(self.renderer.NN)
            window.exec()
            if window.is_nn_trained:
                dialog = FuncDialog("Training completed. Weights and biases updated.\nSave network?",
                                    self.project.save)
                dialog.exec()

    def verify_network(self):
        if not self.renderer.NN.nodes:
            dialog = MessageDialog("No network to verify.", MessageType.ERROR)
            dialog.exec()
        elif not self.project.properties:
            dialog = MessageDialog("No property to verify.", MessageType.ERROR)
            dialog.exec()
        else:
            window = VerificationWindow(self.renderer.NN, self.project.properties)
            window.exec()

    @QtCore.pyqtSlot()
    def zoom_in(self):
        """
        Zoom in canvas

        """

        if self.zooms < self.MAX_ZOOM:
            self.zooms += 1

            scale_tr = QtGui.QTransform()
            scale_tr.scale(self.ZOOM_FACTOR, self.ZOOM_FACTOR)

            tr = self.view.transform() * scale_tr
            self.view.setTransform(tr)

    @QtCore.pyqtSlot()
    def zoom_out(self):
        """
        Zoom out canvas

        """

        if self.zooms > - self.MAX_ZOOM:
            self.zooms -= 1

            scale_tr = QtGui.QTransform()
            scale_tr.scale(self.ZOOM_FACTOR, self.ZOOM_FACTOR)

            scale_inverted, invertible = scale_tr.inverted()
            if invertible:
                tr = self.view.transform() * scale_inverted
                self.view.setTransform(tr)


class NetworkScene(QGraphicsScene):
    """
    This class represents the graphic scene where the
    network is drawn, selected and updated.

    Attributes
    ----------
    blocks: dict
        Dictionary that uses rects as keys connected to the related blocks.
    edges: list
        List of edges between blocks.
    mode: DrawingMode
        Current mode, that can be idle or in drawing.
    prev_item: element
        Optional previous item to select.
    selected_item: element
        Optional item to select.
    is_dim_visible: bool
        Boolean storing the visibility of dimensions.

    Methods
    ----------
    set_mode(CanvasMode)
        This method changes the canvas mode.
    switch_dim_visibility()
        Transition function for is_dim_visible parameter.
    add_block()
        Ths method lets the user insert a block in the middle of a connection.
    add_line()
        This method lets the user draw a connection between two blocks.
    auto_add_line(QGraphicsRectItem, QGraphicsRectItem)
        This method draws a connection between two blocks.
    delete_select_item()
        This method deletes from the canvas the selected item.
    remove_lines(dict)
        This method removes from the canvas the edged corresponding to the
        blocks in th given dictionary.
    mouseDoubleClickEvent(event)
        This method reacts to a double click on a block.
    mouseReleaseEvent(event)
        This method reacts to the moving of a block.
    edit_block(NodeBlock)
        This methods lets the user change the parameters of a block.

    """

    # This signal is emitted when the canvas mode changes
    has_changed_mode = pyqtSignal()

    def __init__(self, widget):
        super(QGraphicsScene, self).__init__(widget)

        # List of edges and blocks
        self.edges = list()
        self.blocks = dict()

        # Pre-selected rect
        self.prev_item = None
        self.selected_item = None

        # Setting default mode
        self.mode = DrawingMode.IDLE

        # Dimensions visibility
        self.is_dim_visible = True

    def set_mode(self, mode: DrawingMode):
        """
        This method updates the canvas mode
        changing the cursor and the status bar.

        Parameters
        ----------
        mode: DrawingMode
            The new mode to update.

        """

        self.mode = mode
        if self.mode == DrawingMode.IDLE:
            self.prev_item = None
            QApplication.restoreOverrideCursor()
            self.clearSelection()
        else:
            # Cross-shaped cursor in DRAW_LINE or DRAW_BLOCK mode
            self.prev_item = None
            self.selected_item = None
            QApplication.restoreOverrideCursor()
            QApplication.setOverrideCursor(Qt.CrossCursor)
            self.clearSelection()

        self.has_changed_mode.emit()

    def switch_dim_visibility(self):
        """
        This method shows the input and output dimensions if they are hidden,
        and hides them if they are visible.

        """

        if self.is_dim_visible:
            for line in self.edges:
                line.dim_label.setVisible(False)
            self.is_dim_visible = False
        else:
            for line in self.edges:
                if line.is_valid:
                    line.dim_label.setVisible(True)
            self.is_dim_visible = True

    def add_node(self) -> Optional[tuple]:
        """
        This method inserts the block created by the interface in the
        NetworkScene. The block may be inserted alone or in an existing
        connection.

        Returns
        ----------
        tuple
            A tuple consisting of the middle node, the following one,
            the old edge and the new edges in order to restore the
            scene in case of errors.

        """

        if self.mode == DrawingMode.DRAW_BLOCK and len(self.selectedItems()) > 0:
            self.selected_item = self.selectedItems().pop()
            new_connections = None
            # Select the current item and the previous
            if isinstance(self.selected_item, QGraphicsRectItem):
                if self.prev_item is None:  # No previous items
                    self.prev_item = self.selected_item
                else:
                    if isinstance(self.prev_item, GraphicLine):  # If the previous item is a line, break it
                        prev_rect = self.prev_item.origin
                        new_connections = prev_rect, self.selected_item
                    else:  # No connections between nodes
                        new_connections = None
            elif isinstance(self.selected_item, GraphicLine):
                if self.prev_item is None:  # No previous items
                    self.prev_item = self.selected_item
                else:
                    if isinstance(self.prev_item, QGraphicsRectItem):  # If the previous item is a node, break line
                        prev_rect = self.selected_item.origin
                        new_connections = prev_rect, self.prev_item
                    else:  # If both are edges, stop
                        new_connections = None

            # Check selection
            if new_connections is None:
                return None
            else:
                old_line = None
                next_rect = None

                # Search components to edit
                for line in self.edges:
                    if new_connections[0] == line.origin:
                        old_line = line
                        next_rect = line.destination
                        break

                # Draw new connections
                l1 = GraphicLine(new_connections[0], new_connections[1], self)
                self.edges.append(l1)
                l1.setFlag(QGraphicsItem.ItemIsSelectable, True)
                l1.setZValue(5)
                l2 = GraphicLine(new_connections[1], next_rect, self)
                self.edges.append(l2)
                l2.setFlag(QGraphicsItem.ItemIsSelectable, True)
                l2.setZValue(5)

                # Add edges to scene
                self.addItem(l1)
                self.addItem(l2)

                # Restore IDLE mode
                self.prev_item = None
                self.set_mode(DrawingMode.IDLE)

                # Return a tuple with the middle node and the following
                # one, the old edge and the new edges to restore the scene
                # in case of errors
                return new_connections[0], new_connections[1], old_line, l1, l2

    def add_line(self) -> Optional[tuple]:
        """
        This method adds a new edge between two blocks, if selected
        correctly. It returns the new edge and the connected blocks
        wrapped in a tuple.

        Returns
        ----------
        tuple
            The two nodes connected and the new inserted edge, if the method succeeded.

        """

        if self.mode is DrawingMode.DRAW_LINE and len(self.selectedItems()) > 0:
            # Check if a block is selected
            self.selected_item = self.selectedItems().pop()
            if type(self.selected_item) == QGraphicsRectItem:
                # Check it is a rect
                if self.prev_item is None:
                    self.prev_item = self.selected_item
                else:
                    next_rect_item = self.selectedItems().pop()
                    if self.prev_item != next_rect_item:
                        line = GraphicLine(self.prev_item, next_rect_item, self)
                        items_tuple = (self.prev_item, next_rect_item, line)

                        # Add line to scene
                        self.addItem(line)
                        self.edges.append(line)
                        line.setFlag(QGraphicsItem.ItemIsSelectable, True)
                        line.setZValue(5)

                        # Restore IDLE mode
                        self.prev_item = None
                        self.set_mode(DrawingMode.IDLE)

                        # Return a tuple with the two blocks connected
                        # and their edge, to restore the scene in case of errors
                        return items_tuple
        else:
            return None

    def auto_add_line(self, prev_rect_item, next_rect_item) -> Optional[GraphicLine]:
        """
        This methods adds directly an edge between two given blocks.

        Parameters
        ----------
        prev_rect_item: QGraphicsRectItem
            The source block.
        next_rect_item: QGraphicsREctItem
            The destination block.

        Returns
        ----------
        GraphicLine
            The new line created, if the method succeeded.

        """

        if prev_rect_item != next_rect_item:
            line = GraphicLine(prev_rect_item, next_rect_item, self)
            # Add to list of edges
            self.edges.append(line)
            line.setFlag(QGraphicsItem.ItemIsSelectable, True)
            line.setZValue(0)

            # Add to scene
            self.addItem(line)

            return line
        else:
            return None

    def delete_selected(self) -> Optional[QGraphicsItem]:
        """
        This method deletes the last selected element from
        the scene.

        Returns
        ----------
        QGraphicsItem
            The deleted element, if selected.

        """

        if len(self.selectedItems()) > 0:
            item = self.selectedItems().pop()
            if type(item) is QGraphicsRectItem:
                # If the item is a block, save the edges...
                lines_to_del = list()
                for line in self.edges:
                    if line.origin == item or line.destination == item:
                        lines_to_del.append(line)

                # ...and delete them too
                for line in lines_to_del:
                    line.remove_self()

            # Return the item in order to remove it from the network
            # (if the item is a GraphicLine it is just deleted)
            return item
        else:
            return None

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """
        This method reacts to a double click, allowing to edit the clicked block.
        :param event: QGraphicsSceneMouseEvent
        """
        self.edit_block()

        super(NetworkScene, self).mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        """
        This method reacts to a mouse release: if a rect is selected, it has
        been moved and its edges have to are updated.
        :param event: QGraphicsSceneMouseEvent
        """
        if len(self.selectedItems()) > 0:
            item = self.selectedItems().pop()
            if type(item) is QGraphicsRectItem:
                for line in self.edges:
                    line.update_pos(item)

        super(NetworkScene, self).mouseReleaseEvent(event)

    def edit_block(self, item: GraphicBlock = None):
        """
        This method displays a window in order to let the user edit
        the block parameters. Eventually, a signal is emitted to
        update the corresponding node.

        Parameters
        ----------
        item : GraphicBlock
            The optional block to edit, if None look for selected.

        """

        if (len(self.selectedItems()) == 1 and type(
                self.selectedItems().pop()) == QGraphicsRectItem) or item is not None:

            if item is None:
                item_rect = self.selectedItems().pop()
                item = self.blocks[item_rect]

            if isinstance(item, NodeBlock):
                dialog = EditNodeDialog(item)
                dialog.exec()
                # Catch new parameters
                if dialog.has_edits:
                    # The block emits a signal
                    item.edits = item.block_id, dialog.edited_data
                    item.edited.emit()
            else:
                Canvas.define_property(item)
