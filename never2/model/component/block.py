"""
Module block.py

This module contains the logic class Block and its children LayerBlock, FunctionalBlock and PropertyBlock

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from typing import Optional, Iterable
from uuid import uuid4

import never2.resources.styling.dimension as dim
import never2.utils.rep as rep
from never2.model.component.socket import Socket, SocketPosition, SocketType
from never2.resources.styling.custom import CustomLabel
from never2.view.component.graphics_block import GraphicsBlock, BlockContentWidget
from never2.view.ui.dialog import EditSmtPropertyDialog, EditPolyhedralPropertyDialog


class Block:
    """
    This class is the logic representation of a Block. It stores the block data
    and references the graphics representation in the GraphicsBlock class.

    Attributes
    ----------
    _id : str
        Identifier of the block

    scene_ref : Scene
        Reference to the scene

    title : str
        Title of the block in the editor

    signature : str
        String used for the key name in dictionaries

    attr_dict : dict
        Dictionary containing all the block parameters

    input_sockets : list
        Sockets for input connection

    output_sockets : list
        Sockets for output connection

    graphics_block : GraphicsBlock
        Graphics block representation of this object

    is_newline : bool
        Flag used when rendering large networks

    Methods
    ----------
    has_parameters()
        Returns True if the block has some parameters, False otherwise

    has_input()
        Returns True if the block has a connection in input, False otherwise

    has_output()
        Returns True if the block has a connection in output, False otherwise

    init_sockets(list, list)
        Draws the sockets corresponding to the inputs and outputs

    get_socket_pos(int, SocketPosition, bool)
        Returns the coordinates of a given socket

    previous()
        Returns the previous block, if it exists

    set_rel_to(Block)
        Sets this block position aligned to another one

    update_edges()
        Update the edges position

    """

    def __init__(self, scene: 'Scene'):
        # Reference to the scene
        self.scene_ref = scene

        # Block identifier
        self._id = str(uuid4())

        # Block title
        self.title = ''

        # Block signature
        self.signature = 'Block'

        # Block attributes dict
        self.attr_dict = dict()

        # Sockets
        self.input_sockets = []
        self.output_sockets = []

        # Graphics representation of the block
        self.graphics_block = None

        # Utility attributes
        self.is_newline = False

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def pos(self):
        return self.graphics_block.pos()

    @property
    def width(self):
        return self.graphics_block.width

    @property
    def height(self):
        return self.graphics_block.height

    @property
    def content(self):
        return self.graphics_block.content

    def has_parameters(self) -> bool:
        return len(self.attr_dict['parameters']) > 0

    def has_input(self) -> bool:
        if self.input_sockets:
            return self.input_sockets[-1].edge is not None

    def has_output(self) -> bool:
        if self.output_sockets:
            return self.output_sockets[-1].edge is not None

    def init_sockets(self, inputs, outputs) -> None:
        """
        Draw the sockets given the inputs and outputs of the block

        """

        for i in range(len(inputs)):
            socket = Socket(self, i, SocketPosition.LEFT_TOP, SocketType.INPUT)
            self.input_sockets.append(socket)

        for i in range(len(outputs)):
            socket = Socket(self, i, SocketPosition.RIGHT_TOP, SocketType.OUTPUT)
            self.output_sockets.append(socket)

    def get_socket_pos(self, index: int, position: SocketPosition, absolute: bool) -> list:
        """
        Method to return the relative or absolute position of the sockets of this block

        Returns
        ----------
        list
            The x and y coordinates in a list

        """

        if position == SocketPosition.LEFT_TOP:
            x = 0
        else:
            x = self.graphics_block.width

        if self.has_parameters():
            y = dim.TITLE_HEIGHT + dim.TITLE_PAD + dim.EDGE_ROUNDNESS + index * dim.SOCKET_SPACING
        else:
            y = self.graphics_block.height / 2

        if absolute:
            return [x + self.pos.x(), y + self.pos.y()]
        else:
            return [x, y]

    def previous(self) -> Optional['Block']:
        """
        Utility method to retrieve the previous block

        Returns
        ----------
        Block, Optional
            The previous block, if it exists, None otherwise

        """

        prev = None

        if self.has_input():
            prev_block_idx = self.scene_ref.sequential_list.index(self.id) - 1
            prev_block_id = self.scene_ref.sequential_list[prev_block_idx]
            prev = self.scene_ref.blocks[prev_block_id]

        return prev

    def set_rel_to(self, other: 'Block') -> None:
        """
        Utility method to set the block position with respect to another one

        Parameters
        ----------
        other : Block
            The relative block

        """

        if self.scene_ref.input_block is not None:
            if self.previous() == self.scene_ref.input_block:
                self.is_newline = True
        else:
            self.is_newline = False

        new_pos_width = other.pos.x() + other.width + dim.ABS_BLOCK_DISTANCE

        if other.height != self.height:
            new_pos_height = other.pos.y() - self.height / 2 + other.height / 2
        else:
            new_pos_height = other.pos.y()

        if new_pos_width > dim.SCENE_BORDER:
            self.is_newline = True

            # Newline
            prev = self.previous()
            highest = prev

            while not prev.is_newline:
                prev = prev.previous()
                if prev.height > highest.height:
                    highest = prev

            new_pos_width = prev.pos.x()
            new_pos_height = highest.pos.y() + highest.height + dim.NEXT_BLOCK_DISTANCE

        self.graphics_block.setPos(new_pos_width, new_pos_height)

        # Move the output block
        end_pos_width = self.pos.x() + self.width + dim.ABS_BLOCK_DISTANCE

        if self.height != self.scene_ref.output_block:
            end_pos_height = self.pos.y() - self.scene_ref.output_block.height / 2 + self.height / 2
        else:
            end_pos_height = other.pos.y()

        self.scene_ref.output_block.graphics_block.setPos(end_pos_width, end_pos_height)

        self.update_edges()

    def update_edges(self) -> None:
        """
        This method updates the edges connected to the block

        """

        for socket in self.input_sockets + self.output_sockets:
            if socket.edge is not None:
                socket.edge.update_pos()


class LayerBlock(Block):
    """
    This class represents a block for the definition of a neural network layer

    Methods
    ----------
    remove()
        Procedure to safely remove this block and the network node associated

    """

    def __init__(self, scene: 'Scene', inputs: list, outputs: list, build_dict: dict,
                 key_signature: str = '', block_id: str = None, load_dict: dict = None):
        super().__init__(scene)

        # Signature for dictionary map
        self.signature = 'layers:' + key_signature
        self.title = self.signature.split(':')[-1]

        # If an ID is provided use it
        if block_id is not None:
            self._id = block_id

        # Copy parameters and create block layout
        self.attr_dict = build_dict

        # Init graphics block
        self.graphics_block = GraphicsBlock(self)

        if self.has_parameters():
            self.graphics_block.set_content(BlockContentWidget(self, load_dict))

        self.scene_ref.graphics_scene.addItem(self.graphics_block)

        self.init_sockets(inputs, outputs)

    def remove(self) -> None:
        """
        Procedure to remove this block

        """

        end_block = self.scene_ref.blocks['END']
        end_pos_width = self.pos.x()

        if self.height != end_block.height:
            end_pos_height = self.pos.y() - end_block.height / 2 + self.height / 2
        else:
            end_pos_height = self.pos.y()

        end_block.graphics_block.setPos(end_pos_width, end_pos_height)

        # Remove connected edges
        for socket in self.input_sockets + self.output_sockets:
            if socket.edge is not None:
                socket.edge.remove()
                socket.edge = None

        # Remove from graphics scene
        self.scene_ref.graphics_scene.removeItem(self.graphics_block)
        self.graphics_block = None
        del self


class FunctionalBlock(Block):
    """
    This class represents a block for the input and output of the neural network

    Methods
    ----------
    get_identifier()
        Returns the identifier associated to this block

    get_dimension()
        Returns the dimension associated to this block

    get_property_block()
        Returns the property block connected to this block, if it exists

    get_variables()
        Returns the variables associated to the dimension

    add_property_socket()
        Draws the socket for a property added

    remove()
        Is ignored since this block is permanent

    """

    def __init__(self, scene: 'Scene', is_input: bool = True):
        super().__init__(scene)

        # I/O data
        if is_input:
            self.title = 'Input'
            sockets = [[], [1]]

        else:
            self.title = 'Output'
            sockets = [[1], []]

        # Id from data
        self._id = self.scene_ref.editor_widget_ref.functional_data[self.title]['id']
        self.signature = 'functional:' + self.title

        self.attr_dict = self.scene_ref.editor_widget_ref.functional_data[self.title]

        # Init content
        self.graphics_block = GraphicsBlock(self)
        self.graphics_block.set_content(BlockContentWidget(self))
        self.scene_ref.graphics_scene.addItem(self.graphics_block)

        self.init_sockets(*sockets)

    def get_identifier(self) -> str:
        """
        Get the identifier of the input or the output

        Returns
        ----------
        str
            The identifier name

        """

        return self.content.wdg_param_dict['Name'][1]

    def set_identifier(self, identifier: str) -> None:
        """
        Set the identifier of the block

        """

        self.content.wdg_param_dict['Name'][0].setText(identifier)
        self.content.wdg_param_dict['Name'][1] = identifier

    def get_dimension(self) -> tuple:
        """
        Get the dimension in input or output

        Returns
        ----------
        tuple
            The shape in input or output

        """

        return rep.text2tuple(self.content.wdg_param_dict['Dimension'][1])

    def set_dimension(self, dimension: tuple) -> None:
        """
        Set the dimension of the block

        """

        self.content.wdg_param_dict['Dimension'][0].setText(rep.tuple2text(dimension, prod=False))
        self.content.wdg_param_dict['Dimension'][1] = str(dimension)

    def get_property_block(self) -> 'PropertyBlock':
        """
        Get the property block associated to this functional block

        Returns
        ----------
        PropertyBlock
            The pre-condition or post-condition block

        """

        return self.scene_ref.pre_block if self.title == 'Input' else self.scene_ref.post_block

    def get_variables(self) -> Iterable:
        """
        Get the variables associated to this block dimension

        Returns
        ----------
        list
            The list of input or output variables

        """

        return rep.create_variables_from(self.get_identifier(), self.get_dimension())

    def add_property_socket(self) -> None:
        """
        Method to add a socket only when a property is connected

        """

        if self.title == 'Input':
            socket = Socket(self, 1, SocketPosition.LEFT_TOP, SocketType.INPUT)
            self.input_sockets.append(socket)
        else:
            socket = Socket(self, 1, SocketPosition.RIGHT_TOP, SocketType.OUTPUT)
            self.output_sockets.append(socket)

    def remove(self):
        """
        Prevent deletion of this block

        """
        pass


class PropertyBlock(Block):
    """
    This class represents a block for the specification of a VNN-LIB property

    Attributes
    ----------
    ref_block : FunctionalBlock
        Reference to the input or output block

    property_label : CustomLabel
        Label of the block

    label_string : str
        String displayed on the label

    smt_string : str
        String containing the property definition

    variables : list
        Variables associated to the dimension of ref_block

    Methods
    ----------
    init_position()
        Setup this block position

    draw()
        Draw the block content

    edit()
        Call the edit dialog for the property

    remove()
        Safely remove this block

    """

    def __init__(self, scene: 'Scene', name: str, ref_block: FunctionalBlock):
        super().__init__(scene)

        self.title = name
        self.signature = 'properties:' + self.title

        self.id = self.scene_ref.editor_widget_ref.property_data[self.title]['id']
        self.attr_dict = self.scene_ref.editor_widget_ref.property_data[self.title]

        self.ref_block = ref_block

        # Display attributes
        self.label_string = ''
        self.smt_string = ''
        self.variables = self.ref_block.get_variables()

        self.property_label = CustomLabel(self.label_string)

    def init_position(self) -> None:
        """
        This method sets the positions of the properties respect to the FunctionalBlocks

        """

        if self.ref_block.title == 'Input':
            self.graphics_block.setPos(self.ref_block.pos.x() - 80 - self.width,
                                       self.ref_block.pos.y() + self.ref_block.height / 2 - self.height / 2)
        else:
            self.graphics_block.setPos(self.ref_block.pos.x() + self.ref_block.width + 80,
                                       self.ref_block.pos.y() + self.ref_block.height / 2 - self.height / 2)

    def draw(self) -> None:
        """
        Draw this block and add the corresponding sockets in the functional block

        """

        # Init content
        self.graphics_block = GraphicsBlock(self)
        self.graphics_block.set_content(BlockContentWidget(self))
        self.scene_ref.graphics_scene.addItem(self.graphics_block)

        # Init sockets
        if self.ref_block.title == 'Input':
            sockets = [[], [1]]
        else:
            sockets = [[1], []]

        self.init_sockets(*sockets)

        # Add socket to the related functional block
        self.ref_block.add_property_socket()

        # Init position close to the functional block
        self.init_position()

        # Create edge between Input node and property
        self.scene_ref.add_edge(self, self.ref_block)

    def edit(self) -> bool:
        """
        This method invokes the proper dialog to edit the property

        Returns
        ----------
        bool
            True if there are edits, False otherwise

        """

        dialog = None

        if self.title == 'Generic SMT':
            dialog = EditSmtPropertyDialog(self)
            dialog.exec()

            if dialog.has_edits:
                self.smt_string = dialog.new_property_str
                self.property_label.setText(self.smt_string)

        elif self.title == 'Polyhedral':
            dialog = EditPolyhedralPropertyDialog(self)
            dialog.exec()

            if dialog.has_edits:
                if self.label_string == 'Ax - b <= 0':
                    self.label_string = ''

                for p in dialog.property_list:
                    self.label_string += f'{p[0]} {p[1]} {p[2]}\n'
                    self.smt_string += f'(assert ({p[1]} {p[0]} {float(p[2])}))\n'

                self.property_label.setText(self.smt_string)

        return dialog.has_edits if dialog is not None else False

    def remove(self) -> None:
        """
        Remove this block and the corresponding sockets

        """

        for socket in self.input_sockets + self.output_sockets:
            # Remove the functional socket
            if self.ref_block.title == 'Input':
                socket.edge.end_skt.remove()
            else:
                socket.edge.start_skt.remove()

            # Remove the edge
            socket.edge.remove()

        self.scene_ref.graphics_scene.removeItem(self.graphics_block)
        self.graphics_block = None
        del self
