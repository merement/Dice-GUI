# dice_gui/widgets/zoom_window.py

import math
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QMainWindow

from dice_gui.widgets.circle_view import CircleView, COLOR_CIRCLE

def _is_x_in_interval(x: float, x_min: float, x_max: float) -> bool:
    """
    Check if coordinate x (in [-1.0, 1.0]) lies within the interval [x_min, x_max],
    accounting for circular wrap-around.
    """
    if x_min <= x_max:
        return x_min <= x <= x_max
    else:
        return x >= x_min or x <= x_max

def _sample_interval(x_min: float, x_max: float, num_samples: int):
    """
    Generate num_samples + 1 points from x_min to x_max, wrapping around boundaries.
    """
    if x_min <= x_max:
        for i in range(num_samples + 1):
            yield x_min + i * (x_max - x_min) / num_samples
    else:
        total_len = 2.0 - x_min + x_max
        for i in range(num_samples + 1):
            val = x_min + i * total_len / num_samples
            if val > 1.0:
                val -= 2.0
            yield val


class ZoomedCircleView(CircleView):
    def __init__(self, x_min: float, x_max: float, parent=None):
        self.x_min = x_min
        self.x_max = x_max
        super().__init__(parent)

    def _calculate_circle_geometry(self) -> tuple[QPointF, float]:
        """
        Calculate scaled center and radius to fit the selected arc segment.
        """
        num_samples = 100
        u_vals = []
        v_vals = []
        for x in _sample_interval(self.x_min, self.x_max, num_samples):
            angle = math.pi * x + math.pi / 2.0
            u = -math.cos(angle)
            v = math.sin(angle)
            u_vals.append(u)
            v_vals.append(v)

        u_min, u_max = min(u_vals), max(u_vals)
        v_min, v_max = min(v_vals), max(v_vals)

        u_ctr = (u_min + u_max) / 2.0
        v_ctr = (v_min + v_max) / 2.0

        w_unit = max(u_max - u_min, 0.01)
        h_unit = max(v_max - v_min, 0.01)

        padding = 40.0
        available_width = max(0.0, float(self.width() - 2.0 * padding))
        available_height = max(0.0, float(self.height() - 2.0 * padding))

        radius = min(available_width / w_unit, available_height / h_unit)
        radius = max(radius, 1.0)

        cx = self.width() / 2.0 - radius * u_ctr
        cy = self.height() / 2.0 - radius * v_ctr

        return QPointF(cx, cy), radius

    def _draw_base_circle(self, painter: QPainter) -> None:
        pen = QPen(COLOR_CIRCLE)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw the arc
        if self.x_min <= self.x_max:
            span_deg = 180.0 * (self.x_max - self.x_min)
        else:
            span_deg = 180.0 * (self.x_max - self.x_min + 2.0)

        start_deg = 270.0 + 180.0 * self.x_min

        rect = QRectF(
            self.circle_center.x() - self.circle_radius,
            self.circle_center.y() - self.circle_radius,
            self.circle_radius * 2.0,
            self.circle_radius * 2.0
        )
        painter.drawArc(rect, int(start_deg * 16), int(span_deg * 16))

        # Draw boundary markers if within interval
        if _is_x_in_interval(1.0, self.x_min, self.x_max):
            pos = self._x_to_screen_position(1.0)
            dx = pos.x() - self.circle_center.x()
            dy = pos.y() - self.circle_center.y()
            dist = math.hypot(dx, dy)
            if dist > 0:
                ux, uy = dx / dist, dy / dist
                painter.drawLine(
                    QPointF(pos.x() - 10 * ux, pos.y() - 10 * uy).toPoint(),
                    QPointF(pos.x() + 10 * ux, pos.y() + 10 * uy).toPoint()
                )

        if _is_x_in_interval(0.0, self.x_min, self.x_max):
            zero_pos = self._x_to_screen_position(0.0)
            painter.setBrush(QBrush(COLOR_CIRCLE))
            painter.drawEllipse(zero_pos, 3, 3)

    def _draw_node(
        self,
        painter: QPainter,
        spin: int,
        x_value: float,
        selected: bool = False,
        index: int | None = None,
    ) -> None:
        # Only render node if it lies inside the zoom interval
        if not _is_x_in_interval(x_value, self.x_min, self.x_max):
            return
        super()._draw_node(painter, spin, x_value, selected, index)

    def _nearest_node(self, position: QPointF) -> tuple[int | None, float]:
        if self.frame is None or self._num_nodes() == 0:
            return None, math.inf

        self._update_circle_geometry()

        nearest_index: int | None = None
        nearest_distance = math.inf

        for index in range(self._num_nodes()):
            x_value = float(self.frame.x_values[index])
            if not _is_x_in_interval(x_value, self.x_min, self.x_max):
                continue

            node_pos = self._node_screen_position(index)

            dx = position.x() - node_pos.x()
            dy = position.y() - node_pos.y()
            distance = math.hypot(dx, dy)

            if distance < nearest_distance:
                nearest_index = index
                nearest_distance = distance

        return nearest_index, nearest_distance

    def _get_nodes_in_rect(self, rect: QRectF) -> set[int]:
        if self.frame is None:
            return set()
        indices = set()
        for idx in range(self._num_nodes()):
            x_val = float(self.frame.x_values[idx])
            if not _is_x_in_interval(x_val, self.x_min, self.x_max):
                continue
            pos = self._node_screen_position(idx)
            if rect.contains(pos):
                indices.add(idx)
        return indices


class ZoomWindow(QMainWindow):
    def __init__(self, x_min: float, x_max: float, parent_window: QMainWindow):
        super().__init__(parent_window)
        self.x_min = x_min
        self.x_max = x_max
        self.parent_window = parent_window

        self.setWindowTitle(f"Zoomed Circle View: [{x_min:.3f}, {x_max:.3f}]")

        orig_view = parent_window.circle_view
        self.resize(orig_view.size())

        self.zoomed_view = ZoomedCircleView(x_min, x_max, self)
        self.setCentralWidget(self.zoomed_view)

        # Propagate selection changes from zoomed view back to parent window
        self.zoomed_view.selection_changed.connect(parent_window.on_point_selection_changed)

        self.sync_from_parent()

    def sync_from_parent(self) -> None:
        if self.parent_window.circle_view.frame is not None:
            self.zoomed_view.set_frame(self.parent_window.circle_view.frame)

        if hasattr(self.parent_window.circle_view, "point_ids"):
            self.zoomed_view.set_point_ids(self.parent_window.circle_view.point_ids)

        if hasattr(self.parent_window, "selected_point_indices"):
            self.zoomed_view.set_selected_indices(self.parent_window.selected_point_indices)

    def closeEvent(self, event) -> None:
        if hasattr(self.parent_window, "zoom_windows"):
            if self in self.parent_window.zoom_windows:
                self.parent_window.zoom_windows.remove(self)
        super().closeEvent(event)
