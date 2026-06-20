# dice_gui/widgets/circle_view.py

import math

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from dice_gui.domain import DynamicFrame

COLOR_CIRCLE = QColor(125, 125, 125)
COLOR_SPIN_UP = QColor(255, 0, 0)
COLOR_SPIN_DOWN = QColor(0, 0, 255)
COLOR_SPIN_NONE = QColor(100, 100, 100)

COLOR_SELECTED_OUTLINE = QColor(255, 215, 0)
COLOR_SELECTED_INNER = QColor(0, 0, 0)

NODE_RADIUS = 7.5
NODE_HIT_RADIUS = 12.0
SELECTED_NODE_RADIUS = NODE_RADIUS + 4.0


class CircleView(QWidget):
    """
    View widget for rendering one DynamicFrame on a circle.

    CircleView intentionally does not own SimulationData. It only owns:
      - the current frame being displayed
      - lightweight view state, such as selected_index

    The app-level selected point index should be mirrored/owned by MainWindow.
    """

    selection_changed = pyqtSignal(object)
    """
    Emitted when the selected point changes.

    Payload:
        int   -> selected point index
        None  -> no point selected
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(500)

        self.circle_center = QPointF(0, 0)
        self.circle_radius = 0.0

        self.frame: DynamicFrame | None = None
        self.selected_index: int | None = None

        self.node_radius = NODE_RADIUS
        self.node_hit_radius = NODE_HIT_RADIUS
        self.selected_node_radius = SELECTED_NODE_RADIUS

        self.reserved_left_space = 25

        self._update_circle_geometry()

    def set_frame(self, frame: DynamicFrame):
        """
        Set the frame currently displayed by this view.

        Selection is preserved if the selected index is still valid for the new
        frame. If not, selection is cleared and selection_changed is emitted.
        """
        self.frame = frame

        if not self._selected_index_is_valid():
            self.set_selected_index(None)

        self.update()

    def set_selected_index(self, index: int | None):
        """
        Set the selected node index.

        This method is the central place for changing selection state inside
        CircleView, so signal emission and repainting stay consistent.
        """
        if index is not None:
            index = int(index)

            if self.frame is None or index < 0 or index >= self._num_nodes():
                index = None

        if self.selected_index == index:
            return

        self.selected_index = index
        self.selection_changed.emit(self.selected_index)
        self.update()

    def clear_selection(self):
        """
        Clear the selected node index.
        """
        self.set_selected_index(None)

    def paintEvent(self, event):
        painter = QPainter(self)

        if not painter.isActive():
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        self._update_circle_geometry()
        self._draw_base_circle(painter)

        if self.frame is not None:
            self._draw_frame(painter, self.frame)

        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_circle_geometry()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        if self.frame is None or self._num_nodes == 0:
            self.clear_selection()
            event.accept()
            return

        clicked_pos = event.position()
        nearest_index, nearest_distance = self._nearest_node(clicked_pos)
        if nearest_distance is not None and nearest_distance <= self.node_hit_radius:
            self.set_selected_index(nearest_index)
        else:
            self.clear_selection()
        event.accept()

    def _calculate_circle_geometry(self):
        """
        Calculate circle center/radius from current widget geometry.

        This method is pure with respect to CircleView state, so geometry can be
        queried independently of painting.
        """
        available_width = max(0, self.width() - self.reserved_left_space)
        available_height = max(0, self.height())

        radius = max(float(min(available_width, available_height) / 2.25), 155.0)

        center = QPointF(
            self.rect().center().x(),
            self.rect().center().y(),
        )

        return center, radius

    def _update_circle_geometry(self):
        self.circle_center, self.circle_radius = self._calculate_circle_geometry()

    def _draw_base_circle(self, painter: QPainter):
        pen = QPen(COLOR_CIRCLE)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # width = self.width() - self.reserved_left_space
        # height = self.height()

        # self.circle_radius = max(float(min(width, height) / 2.25), 155.0)
        # self.circle_center = QPointF(
        #     self.rect().center().x(),
        #     self.rect().center().y(),
        # )

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
        painter.setBrush(QBrush(COLOR_CIRCLE))
        painter.drawEllipse(boundary_center, 3, 3)

        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_frame(self, painter: QPainter, frame: DynamicFrame):
        for index, (spin, x_value) in enumerate(zip(frame.spins, frame.x_values)):
            is_selected = index == self.selected_index
            self._draw_node(
                painter=painter,
                spin=int(spin),
                x_value=float(x_value),
                selected=is_selected,
            )

    def _draw_node(
        self,
        painter: QPainter,
        spin: int,
        x_value: float,
        selected: bool = False,
    ):
        if spin == 1:
            color = COLOR_SPIN_UP
        elif spin == -1:
            color = COLOR_SPIN_DOWN
        else:
            color = COLOR_SPIN_NONE

        node_pos = self._x_to_screen_position(x_value)

        if selected:
            self._draw_selected_node_highlight(painter, node_pos)

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color))
        painter.drawEllipse(node_pos, self.node_radius, self.node_radius)

    def _draw_selected_node_highlight(self, painter: QPainter, node_pos: QPointF):
        """
        Draw selection highlight behind the node.

        The actual node is drawn afterward, so its spin color remains visible.
        """
        highlight_pen = QPen(COLOR_SELECTED_OUTLINE)
        highlight_pen.setWidth(3)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(highlight_pen)
        painter.drawEllipse(
            node_pos, self.selected_node_radius, self.selected_node_radius
        )

        inner_pen = QPen(COLOR_SELECTED_INNER)
        inner_pen.setWidth(1)
        painter.setPen(inner_pen)
        painter.drawEllipse(
            node_pos,
            self.node_radius + 1.5,
            self.node_radius + 1.5,
        )

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

    def _node_screen_position(self, index: int) -> QPointF:
        """
        Return the screen position for a node in the current frame.
        """
        if self.frame is None:
            raise ValueError("Cannot calculate node position without a frame.")

        x_value = float(self.frame.x_values[index])
        return self._x_to_screen_position(x_value)

    def _nearest_node(self, position: QPointF) -> tuple[int | None, float]:
        """
        Return the nearest node index and distance to the given screen position.

        If there is no current frame, returns:

            (None, inf)
        """
        if self.frame is None or self._num_nodes() == 0:
            return None, math.inf

        self._update_circle_geometry()

        nearest_index: int | None = None
        nearest_distance = math.inf

        for index in range(self._num_nodes()):
            node_pos = self._node_screen_position(index)

            dx = position.x() - node_pos.x()
            dy = position.y() - node_pos.y()
            distance = math.hypot(dx, dy)

            if distance < nearest_distance:
                nearest_index = index
                nearest_distance = distance

        return nearest_index, nearest_distance

    def _num_nodes(self) -> int:
        if self.frame is None:
            return 0

        return len(self.frame.x_values)

    def _selected_index_is_valid(self) -> bool:
        if self.selected_index is None:
            return True

        if self.frame is None:
            return False

        return 0 <= self.selected_index < self._num_nodes()
