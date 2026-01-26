"""
Module graphics_edge.py

This module contains the class GraphicsEdge and its concrete children
GraphicsDirectEdge and GraphicsBezierEdge for displaying edges connecting
the blocks

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

import abc
import math

import never2.resources.styling.dimension as dim
import never2.resources.styling.palette as palette
from never2.model.component.socket import SocketType

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QPainter, QPolygonF, QPainterPath
from PyQt6.QtWidgets import QGraphicsPathItem

class GraphicsEdge(QGraphicsPathItem):
    """
    This abstract class represents a general Graphics Edge for linking blocks.
    It provides positional parameters and painting methods

    """

    def __init__(self, edge: 'Edge', parent=None):
        super().__init__(parent)

        self.edge_ref = edge

        if self.edge_ref.view_dim:
            self._pen = QPen(QColor(palette.DARK_TEAL))
        else:
            self._pen = QPen(QColor(palette.DARK_ORANGE))
        self._pen.setWidth(2)
        self.setZValue(-1)

        # Edge dimension label
        self.label = ''

        # Position
        self.src_pos = [0, 0]
        self.dest_pos = [200, 200]

        self.update()

    @abc.abstractmethod
    def update_path(self):
        """
        Abstract method to be implemented

        """

        pass

    @abc.abstractmethod
    def calc_path(self) -> QPainterPath:
        """
        Abstract method to be implemented

        """

        pass

    def set_label(self, text):
        self.label = text
        self.update()

    def build_arrow(self) -> list:
        """
        Compute and return the three vertices of the arrow.
        Robust against vertical and horizontal edges.
        """

        radius = 7
        arrow_dimension = 5

        xs, ys = self.src_pos
        xd, yd = self.dest_pos[0] - radius, self.dest_pos[1]

        dx = xd - xs
        dy = yd - ys

        # Avoid division by zero and degenerate edges
        if dx == 0 and dy == 0:
            # Edge has zero length — draw a small default arrow
            return [
                QPointF(xd, yd),
                QPointF(xd - arrow_dimension, yd - arrow_dimension),
                QPointF(xd - arrow_dimension, yd + arrow_dimension)
            ]

        # Handle vertical and horizontal cases gracefully
        if abs(dx) < 1e-6:
            # Vertical line
            p_aux = QPointF(xd, yd - arrow_dimension)
            point2 = QPointF(p_aux.x() - arrow_dimension / 2, p_aux.y())
            point3 = QPointF(p_aux.x() + arrow_dimension / 2, p_aux.y())
            return [QPointF(xd, yd), point2, point3]

        ang_cf = dy / dx

        # Handle horizontal case explicitly
        if abs(ang_cf) < 1e-6:
            p_aux = QPointF(xd - arrow_dimension, yd)
            point2 = QPointF(p_aux.x(), p_aux.y() - arrow_dimension / 2)
            point3 = QPointF(p_aux.x(), p_aux.y() + arrow_dimension / 2)
            return [QPointF(xd, yd), point2, point3]

        # Generic oblique case
        theta = math.atan(ang_cf)
        p_aux = QPointF(xd - arrow_dimension * math.cos(theta),
                        yd - arrow_dimension * math.sin(theta))
        gamma = math.atan(-1 / ang_cf)
        point2 = QPointF(p_aux.x() - arrow_dimension * math.cos(gamma),
                        p_aux.y() - arrow_dimension * math.sin(gamma))
        point3 = QPointF(p_aux.x() + arrow_dimension * math.cos(gamma),
                        p_aux.y() + arrow_dimension * math.sin(gamma))

        return [QPointF(xd, yd), point2, point3]


    def paint(self, painter: QPainter, option: 'QStyleOptionGraphicsItem', widget=None) -> None:
        """
        Draw the edge, the arrow in the destination and the label

        """

        # Draw edge path
        self.update_path()
        painter.setPen(self._pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

        # Draw edge label
        painter.setBrush(QColor('yellow'))
        label_rect = QRectF((self.src_pos[0] + self.dest_pos[0]) / 2 - 48,
                            (self.src_pos[1] + self.dest_pos[1]) / 2, 100, 40)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.label)

        # Draw arrow
        painter.setBrush(QColor(palette.BLUE))

        if self.edge_ref.view_dim:
            polygon = QPolygonF(self.build_arrow())
            painter.drawPolygon(polygon)

    def shape(self) -> 'QtGui.QPainterPath':
        return self.calc_path()

    def boundingRect(self) -> 'QtCore.QRectF':
        return self.shape().boundingRect()


class GraphicsDirectEdge(GraphicsEdge):
    """
    This class implements a direct path for the edge

    """

    def __init__(self, edge, parent=None):
        super().__init__(edge, parent)

    def update_path(self):
        path = QPainterPath(QPointF(self.src_pos[0], self.src_pos[1]))
        path.lineTo(self.dest_pos[0], self.dest_pos[1])
        self.setPath(path)

    def calc_path(self) -> QPainterPath:
        """
        Compute the direct line connection

        Returns
        ----------
        QPainterPath
            The path of this edge

        """

        path = QPainterPath(QPointF(self.src_pos[0], self.src_pos[1]))
        path.lineTo(self.dest_pos[0], self.dest_pos[1])
        return path


class GraphicsBezierEdge(GraphicsEdge):
    """
    This class implements a bezier path for the edge

    """

    def __init__(self, edge, parent=None):
        super().__init__(edge, parent)

    def update_path(self):
        dist = (self.dest_pos[0] - self.src_pos[0]) * 0.5
        if self.src_pos[0] > self.dest_pos[0]:
            dist *= -1

        path = QPainterPath(QPointF(self.src_pos[0], self.src_pos[1]))
        path.cubicTo(
            self.src_pos[0] + dist, self.src_pos[1], self.dest_pos[0] - dist, self.dest_pos[1],
            self.dest_pos[0], self.dest_pos[1]
        )
        self.setPath(path)

    def calc_path(self) -> QPainterPath:
        """
        Compute the cubic Bezier line connection

        Returns
        ----------
        QPainterPath
            The path of this edge

        """

        s = self.src_pos
        d = self.dest_pos
        distance = (d[0] - s[0]) * 0.5

        cpx_s = distance
        cpx_d = - distance
        cpy_s = 0
        cpy_d = 0

        if self.edge_ref.start_skt is not None:
            ssin = self.edge_ref.start_skt.s_type == SocketType.INPUT
            ssout = self.edge_ref.start_skt.s_type == SocketType.OUTPUT

            if (s[0] > d[0] and ssout) or (s[0] < d[0] and ssin):
                cpx_d *= -1
                cpx_s *= -1

                cpy_d = ((s[1] - d[1]) / math.fabs((s[1] - d[1]) if (s[1] - d[1]) != 0
                                                   else 0.00001)) * dim.EDGE_CP_ROUNDNESS
                cpy_s = ((d[1] - s[1]) / math.fabs((d[1] - s[1]) if (d[1] - s[1]) != 0
                                                   else 0.00001)) * dim.EDGE_CP_ROUNDNESS

        path = QPainterPath(QPointF(self.src_pos[0], self.src_pos[1]))
        path.cubicTo(s[0] + cpx_s, s[1] + cpy_s, d[0] + cpx_d, d[1] + cpy_d,
                     self.dest_pos[0], self.dest_pos[1])

        return path
