"""
Module graphics_socket.py

This module contains the graphical representation of a Socket element

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter
from PyQt6.QtWidgets import QGraphicsItem

import never2.resources.styling.dimension as dim
import never2.resources.styling.palette as palette
from never2 import get_classname


class GraphicsSocket(QGraphicsItem):
    """
    This class provides the graphics representation of a Socket object

    """

    def __init__(self, socket: 'Socket', parent=None):
        super().__init__(parent)
        # Reference to socket
        self.socket_ref = socket

        # Style parameters
        self.bg_color = QColor(palette.WHITE)
        self.outline_color = QColor(palette.WHITE)
        self.init_colors()

        self._pen = QPen(self.outline_color)
        self._pen.setWidth(dim.SOCKET_OUTLINE)
        self._brush = QBrush(self.bg_color)

        self.setZValue(-1)

    def init_colors(self):
        if get_classname(self.socket_ref.block_ref) == 'LayerBlock':
            self.bg_color = QColor(palette.DARK_BLUE)
            self.outline_color = QColor(palette.DARK_TEAL)

        elif get_classname(self.socket_ref.block_ref) == 'FunctionalBlock':
            self.bg_color = QColor(palette.GREY)
            self.outline_color = QColor(palette.DARK_ORANGE)

        elif get_classname(self.socket_ref.block_ref) == 'PropertyBlock':
            self.bg_color = QColor(palette.DARK_ORANGE)
            self.outline_color = QColor(palette.DARK_ORANGE)

    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget=None) -> None:
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(-dim.SOCKET_RADIUS, -dim.SOCKET_RADIUS, 2 * dim.SOCKET_RADIUS, 2 * dim.SOCKET_RADIUS)

    def boundingRect(self) -> QRectF:

        return QRectF(
            - dim.SOCKET_RADIUS - dim.SOCKET_OUTLINE,
            - dim.SOCKET_RADIUS - dim.SOCKET_OUTLINE,
            2 * (dim.SOCKET_RADIUS + dim.SOCKET_OUTLINE),
            2 * (dim.SOCKET_RADIUS + dim.SOCKET_OUTLINE),
        )
