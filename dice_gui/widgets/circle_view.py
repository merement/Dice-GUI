# dice_gui/widgets/circle_view.py

import math

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from dice_gui.domain import DynamicFrame

COLOR_CIRCLE = QColor(125, 125, 125)
COLOR_SPIN_UP = QColor(255, 0, 0)
COLOR_SPIN_DOWN = QColor(0, 0, 255)
COLOR_SPIN_NONE = QColor(100, 100, 100)

NODE_RADIUS = 7.5
NODE_HIT_RADIUS = 12.0


class CircleView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(500)

        self.circle_center = QPointF(0, 0)
        self.circle_radius = 0.0
        self.frame: DynamicFrame | None = None
        self.selected_index: int | None = None

        self.reserved_left_space = 150

    def set_frame(self, frame: DynamicFrame):
        self.frame = frame
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        if not painter.isActive():
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        self._draw_base_circle(painter)

        if self.frame is not None:
            self._draw_frame(painter, self.frame)

        painter.end()

    def _draw_base_circle(self, painter: QPainter):
        pen = QPen(COLOR_CIRCLE)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        width = self.width() - self.reserved_left_space
        height = self.height()

        self.circle_radius = max(float(min(width, height) / 2.25), 155.0)
        self.circle_center = QPointF(
            self.rect().center().x(),
            self.rect().center().y(),
        )

        painter.drawEllipse(
            self.circle_center,
            self.circle_radius,
            self.circle_radius,
        )

        # Boundary marker
        marker_x = self.circle_center.x()
        marker_y = self.circle_center.y() - self.circle_radius
        painter.drawLine(
            int(marker_x),
            int(marker_y - 10),
            int(marker_x),
            int(marker_y + 10),
        )

        # 0 marker
        boundary_center = QPointF(
            self.circle_center.x(),
            self.circle_center.y() + self.circle_radius,
        )
        painter.setBrush(QBrush(QColor(125, 125, 125)))
        painter.drawEllipse(boundary_center, 3, 3)

        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_frame(self, painter: QPainter, frame: DynamicFrame):
        for spin, x_value in zip(frame.spins, frame.x_values):
            self._draw_node(painter, int(spin), float(x_value))

    def _draw_node(self, painter: QPainter, spin: int, x_value: float):
        if spin == 1:
            color = COLOR_SPIN_UP
        elif spin == -1:
            color = COLOR_SPIN_DOWN
        else:
            color = COLOR_SPIN_NONE

        node_pos = self._x_to_screen_position(x_value)

        # node_radius = 7.5

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color))
        painter.drawEllipse(node_pos, NODE_RADIUS, NODE_RADIUS)

    def _x_to_screen_position(self, x_value: float) -> QPointF:
        """
        Maps x in [-1, 1] to a position on the circle.

            NodeX = cx - R * cos(pi * x + pi/2)
            NodeY = cy + R * sin(pi * x + pi/2)

        This is equivalent to a rotated circle coordinate system.
        """

        angle = math.pi * x_value + math.pi / 2

        node_x = self.circle_center.x() - self.circle_radius * math.cos(angle)
        node_y = self.circle_center.y() + self.circle_radius * math.sin(angle)

        return QPointF(node_x, node_y)


# it accepts a DynamicFrame.
# Later, this can evolve into:
#     CircleView.set_view_state(view_state)
# where view_state includes selected points, highlighted points,
# viewport, visibility filters, and render mode.
