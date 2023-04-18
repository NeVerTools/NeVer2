"""
Module socket.py

This module contains the class Socket for connecting edges

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from enum import Enum

from never2 import get_classname
from never2.utils.rep import dump_exception
from never2.view.component.graphics_socket import GraphicsSocket


class SocketPosition(Enum):
    """
    Position enumeration

    """

    LEFT_TOP = 1
    RIGHT_TOP = 3


class SocketType(Enum):
    """
    Type enumeration

    """

    INPUT = 1
    OUTPUT = 2


class Socket:
    """
    This class represents a socket, i.e., a linking point for edges and blocks

    """

    def __init__(self, block: 'Block', idx: int = 0, pos=SocketPosition.LEFT_TOP, t=SocketType.INPUT):
        # Reference to the block
        self.block_ref = block

        # The socket index is a design abstraction for multidimensional inputs/outputs
        self.idx = idx

        self.position = pos
        self.s_type = t

        # Edge connected to the socket
        self.edge = None

        # Graphics socket
        self.graphics_socket = GraphicsSocket(self, self.block_ref.graphics_block)
        self.graphics_socket.setPos(*self.block_ref.get_socket_pos(self.idx, self.position, absolute=False))

    @property
    def abs_pos(self):
        return self.block_ref.get_socket_pos(self.idx, self.position, absolute=True)

    def remove(self):
        """
        Procedure to safely remove the Socket

        """

        try:
            if get_classname(self.block_ref) == 'FunctionalBlock':
                if self.block_ref.title == 'Input':
                    self.block_ref.input_sockets.remove(self)
                else:
                    self.block_ref.output_sockets.remove(self)

            self.graphics_socket.hide()
            self.block_ref.scene_ref.graphics_scene.update()

        except Exception as e:
            dump_exception(e)
