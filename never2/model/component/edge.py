"""
Module edge.py

This module contains the class Edge for connecting blocks

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from enum import Enum

from never2.model.component.block import PropertyBlock
from never2.view.component.graphics_edge import GraphicsDirectEdge, GraphicsBezierEdge


class EdgeType(Enum):
    """
    Different edge styles

    """

    DIRECT_EDGE = 1
    BEZIER_EDGE = 2


class GraphicsEdgeFactory:
    """
    This class is a factory for different graphics edge objects

    Methods
    ----------
    create_edge(Edge, EdgeType)
        Return the correct graphics edge associated to the input edge

    """

    @staticmethod
    def create_edge(e: 'Edge', t: EdgeType):
        if t == EdgeType.DIRECT_EDGE:
            return GraphicsDirectEdge(e)
        elif t == EdgeType.BEZIER_EDGE:
            return GraphicsBezierEdge(e)
        else:
            # Fallback
            return GraphicsDirectEdge(e)


class Edge:
    """
    This class represents a connection between two blocks in the Scene.
    It links the two blocks and then draws a GraphicsEdge connected to their sockets

    """

    def __init__(self, scene: 'Scene', start_block: 'Block', end_block: 'Block', edge_type=EdgeType.BEZIER_EDGE):
        # Reference to the scene
        self.scene_ref = scene

        self.view_dim = True
        if isinstance(start_block, PropertyBlock) or isinstance(end_block, PropertyBlock):
            self.view_dim = False

        # Link to sockets
        if len(start_block.output_sockets) == 0:
            self.start_skt = end_block.output_sockets[0]
            self.end_skt = start_block.input_sockets[0]
        else:
            self.start_skt = start_block.output_sockets[0]
            self.end_skt = end_block.input_sockets[0]

        self.start_skt.edge = self
        self.end_skt.edge = self

        # Create graphics edge
        self.graphics_edge = GraphicsEdgeFactory().create_edge(self, edge_type)
        self.update_pos()
        self.scene_ref.graphics_scene.addItem(self.graphics_edge)

    def update_pos(self):
        """
        This method updates dynamically the start and end positions of the edge

        """

        if self.start_skt is not None:
            self.graphics_edge.src_pos = self.start_skt.abs_pos
        if self.end_skt is not None:
            self.graphics_edge.dest_pos = self.end_skt.abs_pos

        self.graphics_edge.update()

    def update_label(self, text):
        self.graphics_edge.set_label(text)

    def detach(self):
        self.start_skt = None
        self.end_skt = None

    def remove(self):
        """
        Remove the edge object along with the graphics edge reference

        """

        self.graphics_edge.hide()

        self.start_skt.edge = None
        self.end_skt.edge = None
        self.detach()

        self.scene_ref.graphics_scene.removeItem(self.graphics_edge)
        self.scene_ref.graphics_scene.update()
