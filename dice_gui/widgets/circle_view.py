# dice_gui/widgets/circle_view.py

import math

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
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
        self.selected_indices: set[int] = set()
        self.point_ids: list[str] = []

        self.node_radius = NODE_RADIUS
        self.node_hit_radius = NODE_HIT_RADIUS
        self.selected_node_radius = SELECTED_NODE_RADIUS

        self.reserved_left_space = 25

        self._drag_start_pos = None
        self._drag_current_pos = None
        self._is_dragging = False
        self._selection_at_drag_start = set()

        self._update_circle_geometry()

    def set_point_ids(self, point_ids: list[str]):
        """
        Set the point IDs for the simulation.
        """
        self.point_ids = list(point_ids)
        self.update()

    def set_frame(self, frame: DynamicFrame):
        """
        Set the frame currently displayed by this view.

        Selection is preserved for valid indices. Invalid indices are filtered out.
        """
        self.frame = frame

        if not self._selected_index_is_valid():
            valid_indices = {idx for idx in self.selected_indices if 0 <= idx < self._num_nodes()}
            self.set_selected_indices(valid_indices)

        self.update()

    def set_selected_indices(self, indices: set[int] | list[int] | None):
        """
        Set the selected node indices.
        """
        if indices is None:
            new_indices = set()
        else:
            new_indices = set()
            for idx in indices:
                idx = int(idx)
                if self.frame is not None and 0 <= idx < self._num_nodes():
                    new_indices.add(idx)

        if self.selected_indices == new_indices:
            return

        self.selected_indices = new_indices
        self.selection_changed.emit(self.selected_indices)
        self.update()

    def set_selected_index(self, index: int | None):
        """
        Set a single selected node index. Provided for backward compatibility.
        """
        if index is None:
            self.set_selected_indices(set())
        else:
            self.set_selected_indices({index})

    def clear_selection(self):
        """
        Clear the selected node indices.
        """
        self.set_selected_indices(set())

    def paintEvent(self, event):  # pyright: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)

        if not painter.isActive():
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        self._update_circle_geometry()
        self._draw_base_circle(painter)

        if self.frame is not None:
            self._draw_frame(painter, self.frame)

        # Draw stylish rubber band selection box
        if self._is_dragging and self._drag_start_pos is not None and self._drag_current_pos is not None:
            rect = QRectF(self._drag_start_pos, self._drag_current_pos).normalized()
            pen = QPen(COLOR_SELECTED_OUTLINE)
            pen.setWidth(1)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            brush = QBrush(QColor(255, 215, 0, 30))  # transparent gold
            painter.setBrush(brush)
            painter.drawRect(rect)

        painter.end()

    def resizeEvent(self, event):  # pyright: ignore[reportIncompatibleMethodOverride]
        super().resizeEvent(event)
        self._update_circle_geometry()

    def mousePressEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        if self.frame is None or self._num_nodes() == 0:
            self.clear_selection()
            event.accept()
            return

        modifiers = event.modifiers()
        has_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if has_shift:
            self._is_dragging = True
            self._drag_start_pos = event.position()
            self._drag_current_pos = event.position()
            self._selection_at_drag_start = set(self.selected_indices)
        else:
            self._is_dragging = False
            clicked_pos = event.position()
            nearest_index, nearest_distance = self._nearest_node(clicked_pos)
            if nearest_distance is not None and nearest_distance <= self.node_hit_radius:
                assert nearest_index is not None
                self.set_selected_indices({nearest_index})
            else:
                self.clear_selection()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        if self._is_dragging and self._drag_start_pos is not None:
            self._drag_current_pos = event.position()
            rect = QRectF(self._drag_start_pos, self._drag_current_pos).normalized()
            points_in_rect = self._get_nodes_in_rect(rect)
            new_selection = self._selection_at_drag_start | points_in_rect
            self.set_selected_indices(new_selection)
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            if self._drag_start_pos is not None:
                diff = event.position() - self._drag_start_pos
                distance = math.hypot(diff.x(), diff.y())
                if distance < 5.0:
                    nearest_index, nearest_distance = self._nearest_node(self._drag_start_pos)
                    if nearest_distance is not None and nearest_distance <= self.node_hit_radius:
                        assert nearest_index is not None
                        new_indices = set(self._selection_at_drag_start)
                        if nearest_index in new_indices:
                            new_indices.remove(nearest_index)
                        else:
                            new_indices.add(nearest_index)
                        self.set_selected_indices(new_indices)
                    else:
                        self.set_selected_indices(self._selection_at_drag_start)
            self._is_dragging = False
            self._drag_start_pos = None
            self._drag_current_pos = None
            self._selection_at_drag_start = set()
            self.update()
        else:
            super().mouseReleaseEvent(event)

    def _get_nodes_in_rect(self, rect: QRectF) -> set[int]:
        if self.frame is None:
            return set()
        indices = set()
        for idx in range(self._num_nodes()):
            pos = self._node_screen_position(idx)
            if rect.contains(pos):
                indices.add(idx)
        return indices

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
            is_selected = index in self.selected_indices
            self._draw_node(
                painter=painter,
                spin=int(spin),
                x_value=float(x_value),
                selected=is_selected,
                index=index,
            )

    def _draw_node(
        self,
        painter: QPainter,
        spin: int,
        x_value: float,
        selected: bool = False,
        index: int | None = None,
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

        if selected and index is not None and index < len(self.point_ids):
            node_id = self.point_ids[index]
            if node_id:
                self._draw_node_id(painter, node_pos, node_id)

    def _draw_node_id(self, painter: QPainter, node_pos: QPointF, node_id: str):
        dx = node_pos.x() - self.circle_center.x()
        dy = node_pos.y() - self.circle_center.y()
        dist = math.hypot(dx, dy)

        if dist > 0:
            offset_dist = self.selected_node_radius + 10.0
            text_x = node_pos.x() + (dx / dist) * offset_dist
            text_y = node_pos.y() + (dy / dist) * offset_dist
        else:
            text_x = node_pos.x() + 15
            text_y = node_pos.y() - 15

        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)

        painter.setPen(QColor(50, 50, 50))

        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(node_id)
        text_height = metrics.height()

        rect_x = text_x - text_width / 2.0
        rect_y = text_y - text_height / 2.0

        painter.drawText(QPointF(rect_x, rect_y + metrics.ascent()), node_id)

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
        if self.frame is None:
            return not self.selected_indices

        return all(0 <= idx < self._num_nodes() for idx in self.selected_indices)
