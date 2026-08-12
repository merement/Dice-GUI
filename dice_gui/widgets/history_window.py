# dice_gui/widgets/history_window.py

import math
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QMainWindow, QWidget

from dice_gui.domain import TimeSeriesData
from dice_gui.widgets.circle_view import COLOR_SPIN_UP, COLOR_SPIN_DOWN, COLOR_SPIN_NONE

TIME_WINDOW = 50
X_PADDING = 0.05


class HistoryPlotWidget(QWidget):
    def __init__(self, simulation_data: TimeSeriesData, node_index: int, parent=None):
        super().__init__(parent)
        self.simulation_data = simulation_data
        self.node_index = node_index

        self.current_frame = 0
        self.bound_left = 0
        self.bound_right = 0

    def update_plot_data(self, current_frame: int, bound_left: int, bound_right: int) -> None:
        self.current_frame = current_frame
        self.bound_left = bound_left
        self.bound_right = bound_right
        self.update()

    def _spin_to_color(self, spin: int) -> QColor:
        if spin == 1:
            return COLOR_SPIN_UP
        elif spin == -1:
            return COLOR_SPIN_DOWN
        else:
            return COLOR_SPIN_NONE

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Sleek dark background for high visual contrast
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        margin_left = 60
        margin_right = 30
        margin_top = 30
        margin_bottom = 50

        width = self.width()
        height = self.height()

        plot_w = width - margin_left - margin_right
        plot_h = height - margin_top - margin_bottom

        if plot_w <= 0 or plot_h <= 0:
            painter.end()
            return

        plot_rect = QRectF(margin_left, margin_top, plot_w, plot_h)

        # Extract X values in the current frame window to calculate shown X interval
        x_slice = [self.simulation_data.x_values[t, self.node_index] for t in range(self.bound_left, self.bound_right + 1)]
        min_X = min(x_slice)
        max_X = max(x_slice)
        shown_min_x = max(-1.0, min_X - X_PADDING)
        shown_max_x = min(1.0, max_X + X_PADDING)

        # 1. Draw Grid Lines & Y-axis labels using the dynamic range shown_min_x to shown_max_x
        grid_pen = QPen(QColor(60, 60, 60))
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        grid_pen.setWidth(1)

        text_pen = QPen(QColor(200, 200, 200))

        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        # Draw 5 evenly spaced grid lines between shown_min_x and shown_max_x
        for i in range(5):
            v = shown_min_x + i * (shown_max_x - shown_min_x) / 4.0
            py = plot_rect.top() + (shown_max_x - v) / (shown_max_x - shown_min_x) * plot_h

            # Grid line
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(plot_rect.left(), py), QPointF(plot_rect.right(), py))

            # Label on the left
            painter.setPen(text_pen)
            label_rect = QRectF(margin_left - 55, py - 8, 45, 16)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{v:.2f}")

        # Draw axis bounding rectangle
        border_pen = QPen(QColor(100, 100, 100))
        border_pen.setWidth(1)
        painter.setPen(border_pen)
        painter.drawRect(plot_rect)

        # 2. Time variables mapping
        t_left = float(self.simulation_data.times[self.bound_left])
        t_right = float(self.simulation_data.times[self.bound_right])
        t_curr = float(self.simulation_data.times[self.current_frame])

        if t_right > t_left:
            px_curr = plot_rect.left() + (t_curr - t_left) / (t_right - t_left) * plot_w
        else:
            px_curr = plot_rect.left() + plot_w / 2.0

        # Draw Time Labels underneath the Time axis
        painter.setPen(text_pen)
        # Left Time
        rect_left = QRectF(plot_rect.left() - 25, plot_rect.bottom() + 5, 50, 16)
        painter.drawText(rect_left, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, f"{t_left:.3f}")
        # Right Time
        rect_right = QRectF(plot_rect.right() - 25, plot_rect.bottom() + 5, 50, 16)
        painter.drawText(rect_right, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, f"{t_right:.3f}")
        # Current Time
        rect_curr = QRectF(px_curr - 30, plot_rect.bottom() + 5, 60, 16)
        painter.drawText(rect_curr, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, f"{t_curr:.3f}")

        # Draw small ticks under time axis
        tick_pen = QPen(QColor(100, 100, 100))
        tick_pen.setWidth(1)
        painter.setPen(tick_pen)
        painter.drawLine(QPointF(plot_rect.left(), plot_rect.bottom()), QPointF(plot_rect.left(), plot_rect.bottom() + 4))
        painter.drawLine(QPointF(plot_rect.right(), plot_rect.bottom()), QPointF(plot_rect.right(), plot_rect.bottom() + 4))
        painter.drawLine(QPointF(px_curr, plot_rect.bottom()), QPointF(px_curr, plot_rect.bottom() + 4))

        # Axis Titles (X & Time)
        title_font = painter.font()
        title_font.setPointSize(9)
        title_font.setBold(True)
        painter.setFont(title_font)

        # X Title (top of vertical axis)
        painter.drawText(QRectF(10, plot_rect.top() - 20, 40, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "X")
        # Time Title (centered below bottom ticks)
        painter.drawText(
            QRectF(plot_rect.left(), plot_rect.bottom() + 25, plot_w, 20),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "Time"
        )

        # 3. Draw vertical dashed indicator line at the current frame position
        indicator_pen = QPen(QColor(150, 150, 150))
        indicator_pen.setStyle(Qt.PenStyle.DashLine)
        indicator_pen.setWidth(1)
        painter.setPen(indicator_pen)
        painter.drawLine(QPointF(px_curr, plot_rect.top()), QPointF(px_curr, plot_rect.bottom()))

        # 4. Extract and map screen coordinates for points in [bound_left, bound_right]
        plot_points = []
        for t in range(self.bound_left, self.bound_right + 1):
            time_val = float(self.simulation_data.times[t])
            x_val = float(self.simulation_data.x_values[t, self.node_index])
            spin_val = int(self.simulation_data.spins[t, self.node_index])

            if t_right > t_left:
                px = plot_rect.left() + (time_val - t_left) / (t_right - t_left) * plot_w
            else:
                px = plot_rect.left() + plot_w / 2.0

            py = plot_rect.top() + (shown_max_x - x_val) / (shown_max_x - shown_min_x) * plot_h
            plot_points.append((px, py, spin_val, t))

        # 5. Draw connecting lines
        for i in range(len(plot_points) - 1):
            px1, py1, spin1, t1 = plot_points[i]
            px2, py2, spin2, t2 = plot_points[i + 1]

            if t1 < self.current_frame:
                color = self._spin_to_color(spin1)
            else:
                color = QColor(160, 160, 160)  # Future unreached segment in light grey

            line_pen = QPen(color)
            line_pen.setWidth(2)
            painter.setPen(line_pen)
            painter.drawLine(QPointF(px1, py1), QPointF(px2, py2))

        # 6. Draw dot markers
        for px, py, spin, t in plot_points:
            if t <= self.current_frame:
                color = self._spin_to_color(spin)
            else:
                color = QColor(160, 160, 160)  # Future unreached points in light grey

            painter.setPen(QPen(color))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), 3.0, 3.0)

        painter.end()


class HistoryWindow(QMainWindow):
    def __init__(
        self,
        node_index: int,
        point_id: str,
        simulation_data: TimeSeriesData,
        parent_window: QMainWindow,
        node_indexing: int = 1,
    ):
        super().__init__(parent_window)
        self.node_index = node_index
        self.point_id = point_id
        self.simulation_data = simulation_data
        self.parent_window = parent_window
        self.node_indexing = node_indexing

        id_str = point_id if point_id else ""
        displayed_idx = node_index + node_indexing
        self.setWindowTitle(f"Point # {displayed_idx}  Id: {id_str}")
        self.resize(600, 400)

        self.plot_widget = HistoryPlotWidget(simulation_data, node_index, self)
        self.setCentralWidget(self.plot_widget)

        self.time_window = TIME_WINDOW

        initial_frame = parent_window.time_slider.value()
        self.set_frame_index(initial_frame)

    def set_frame_index(self, frame_index: int) -> None:
        self.current_frame = frame_index
        max_frame = self.simulation_data.num_frames - 1

        if not hasattr(self, "bound_left") or frame_index < self.bound_left or frame_index > self.bound_right:
            self.bound_left = max(0, frame_index - self.time_window)
            self.bound_right = min(max_frame, frame_index + self.time_window)

        self.plot_widget.update_plot_data(
            current_frame=self.current_frame,
            bound_left=self.bound_left,
            bound_right=self.bound_right
        )

    def closeEvent(self, event) -> None:
        if hasattr(self.parent_window, "history_windows"):
            if self in self.parent_window.history_windows:
                self.parent_window.history_windows.remove(self)
        super().closeEvent(event)
