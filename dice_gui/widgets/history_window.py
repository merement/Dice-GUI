# dice_gui/widgets/history_window.py

import math

from dataclasses import dataclass
from typing import Sequence

from PyQt6.QtCore import QEvent, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPalette, QPen
from PyQt6.QtWidgets import QMainWindow, QWidget

from dice_gui.domain import TimeSeriesData
from dice_gui.widgets.circle_view import (
    COLOR_SPIN_DOWN,
    COLOR_SPIN_NONE,
    COLOR_SPIN_UP,
)

DEFAULT_TIME_WINDOW = 50
DEFAULT_WINDOW_SIZE = (600, 400)


@dataclass(frozen=True)
class PlotConfig:
    minimum_x: float = -1.0
    maximum_x: float = 1.0
    x_padding: float = 0.05

    grid_line_count: int = 5
    marker_radius: float = 3.0

    axis_width: float = 1.0
    series_width: float = 2.0
    tick_length: float = 4.0

    horizontal_spacing: float = 8.0
    vertical_spacing: float = 6.0

    value_decimals: int = 2
    time_decimals: int = 3


@dataclass(frozen=True)
class PlotTheme:
    background: QColor
    text: QColor
    grid: QColor
    border: QColor
    indicator: QColor
    future: QColor

    @classmethod
    def from_palette(cls, palette: QPalette) -> "PlotTheme":
        """
        Use semantic palette roles rather than explicitly deciding whether the
        application is using a light or dark theme.
        """
        return cls(
            background=palette.color(QPalette.ColorRole.Window),
            text=palette.color(QPalette.ColorRole.WindowText),
            grid=palette.color(QPalette.ColorRole.Mid),
            border=palette.color(QPalette.ColorRole.Mid),
            indicator=palette.color(QPalette.ColorRole.Highlight),
            future=palette.color(QPalette.ColorRole.PlaceholderText),
        )


@dataclass(frozen=True)
class PlotSample:
    frame: int
    time: float
    value: float
    spin: int


@dataclass(frozen=True)
class ScreenSample:
    frame: int
    position: QPointF
    spin: int


@dataclass(frozen=True)
class PlotGeometry:
    plot_rect: QRectF
    shown_min_value: float
    shown_max_value: float
    time_left: float
    time_right: float
    time_current: float
    current_x: float


class HistoryPlotWidget(QWidget):
    def __init__(
        self,
        simulation_data: TimeSeriesData,
        node_index: int,
        parent=None,
        config: PlotConfig | None = None,
    ):
        super().__init__(parent)

        self.simulation_data = simulation_data
        self.node_index = node_index
        self.config = config or PlotConfig()

        self.current_frame = 0
        self.bound_left = 0
        self.bound_right = 0

    def update_plot_data(
        self,
        current_frame: int,
        bound_left: int,
        bound_right: int,
    ) -> None:
        max_frame = self.simulation_data.num_frames - 1

        self.current_frame = min(max(current_frame, 0), max_frame)
        self.bound_left = min(max(bound_left, 0), max_frame)
        self.bound_right = min(max(bound_right, self.bound_left), max_frame)

        self.update()

    def changeEvent(self, event: QEvent) -> None:
        """
        Repaint when the application palette or style changes.

        PlotTheme is not cached, so the next paint operation will use the new
        palette automatically.
        """
        if event.type() in {
            QEvent.Type.PaletteChange,
            QEvent.Type.ApplicationPaletteChange,
            QEvent.Type.StyleChange,
        }:
            self.update()

        super().changeEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if not painter.isActive():
            return

        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            theme = PlotTheme.from_palette(self.palette())
            painter.fillRect(self.rect(), theme.background)

            samples = self._extract_samples()
            if not samples:
                return

            geometry = self._calculate_geometry(painter, samples)
            if geometry is None:
                return

            screen_samples = self._map_samples(samples, geometry)

            self._draw_grid(painter, geometry, theme)
            self._draw_time_axis(painter, geometry, theme)
            self._draw_axis_titles(painter, geometry, theme)
            self._draw_current_time_indicator(painter, geometry, theme)
            self._draw_series(painter, screen_samples, theme)
            self._draw_markers(painter, screen_samples, theme)
        finally:
            painter.end()

    # ------------------------------------------------------------------
    # Data preparation
    # ------------------------------------------------------------------

    def _extract_samples(self) -> list[PlotSample]:
        if self.simulation_data.num_frames <= 0:
            return []

        return [
            PlotSample(
                frame=frame,
                time=float(self.simulation_data.times[frame]),
                value=float(
                    self.simulation_data.x_values[frame, self.node_index]
                ),
                spin=int(
                    self.simulation_data.spins[frame, self.node_index]
                ),
            )
            for frame in range(self.bound_left, self.bound_right + 1)
        ]

    def _calculate_geometry(
        self,
        painter: QPainter,
        samples: Sequence[PlotSample],
    ) -> PlotGeometry | None:
        plot_rect = self._calculate_plot_rect(painter)
        if plot_rect.width() <= 0 or plot_rect.height() <= 0:
            return None

        shown_min, shown_max = self._calculate_value_range(samples)

        time_left = samples[0].time
        time_right = samples[-1].time
        time_current = float(
            self.simulation_data.times[self.current_frame]
        )

        current_x = self._map_time_to_x(
            time_current,
            time_left,
            time_right,
            plot_rect,
        )

        return PlotGeometry(
            plot_rect=plot_rect,
            shown_min_value=shown_min,
            shown_max_value=shown_max,
            time_left=time_left,
            time_right=time_right,
            time_current=time_current,
            current_x=current_x,
        )

    def _calculate_plot_rect(self, painter: QPainter) -> QRectF:
        """
        Derive margins primarily from font metrics rather than relying on
        fixed pixel coordinates.
        """
        config = self.config
        metrics = painter.fontMetrics()

        value_example = (
            f"{config.minimum_x:.{config.value_decimals}f}"
        )
        label_width = metrics.horizontalAdvance(value_example)

        margin_left = label_width + 2 * config.horizontal_spacing
        margin_right = 2 * config.horizontal_spacing
        margin_top = metrics.height() + 2 * config.vertical_spacing
        margin_bottom = (
            2 * metrics.height() + 4 * config.vertical_spacing
        )

        return QRectF(
            margin_left,
            margin_top,
            self.width() - margin_left - margin_right,
            self.height() - margin_top - margin_bottom,
        )

    def _calculate_value_range(
        self,
        samples: Sequence[PlotSample],
    ) -> tuple[float, float]:
        config = self.config

        minimum = max(
            config.minimum_x,
            min(sample.value for sample in samples) - config.x_padding,
        )
        maximum = min(
            config.maximum_x,
            max(sample.value for sample in samples) + config.x_padding,
        )

        # Avoid division by zero for a constant series or a zero padding.
        if math.isclose(minimum, maximum):
            expansion = max(config.x_padding, 0.01)
            minimum = max(config.minimum_x, minimum - expansion)
            maximum = min(config.maximum_x, maximum + expansion)

        # This can still happen if both configured limits are identical.
        if math.isclose(minimum, maximum):
            maximum = minimum + 1.0

        return minimum, maximum

    # ------------------------------------------------------------------
    # Coordinate transforms
    # ------------------------------------------------------------------

    @staticmethod
    def _map_time_to_x(
        time: float,
        time_left: float,
        time_right: float,
        plot_rect: QRectF,
    ) -> float:
        if math.isclose(time_left, time_right):
            return plot_rect.center().x()

        fraction = (time - time_left) / (time_right - time_left)
        return plot_rect.left() + fraction * plot_rect.width()

    @staticmethod
    def _map_value_to_y(
        value: float,
        minimum: float,
        maximum: float,
        plot_rect: QRectF,
    ) -> float:
        if math.isclose(minimum, maximum):
            return plot_rect.center().y()

        fraction = (maximum - value) / (maximum - minimum)
        return plot_rect.top() + fraction * plot_rect.height()

    def _map_samples(
        self,
        samples: Sequence[PlotSample],
        geometry: PlotGeometry,
    ) -> list[ScreenSample]:
        return [
            ScreenSample(
                frame=sample.frame,
                position=QPointF(
                    self._map_time_to_x(
                        sample.time,
                        geometry.time_left,
                        geometry.time_right,
                        geometry.plot_rect,
                    ),
                    self._map_value_to_y(
                        sample.value,
                        geometry.shown_min_value,
                        geometry.shown_max_value,
                        geometry.plot_rect,
                    ),
                ),
                spin=sample.spin,
            )
            for sample in samples
        ]

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _draw_grid(
        self,
        painter: QPainter,
        geometry: PlotGeometry,
        theme: PlotTheme,
    ) -> None:
        config = self.config
        plot_rect = geometry.plot_rect

        grid_pen = QPen(theme.grid, config.axis_width)
        grid_pen.setStyle(Qt.PenStyle.DotLine)

        text_pen = QPen(theme.text)
        metrics = painter.fontMetrics()

        count = max(config.grid_line_count, 2)

        for index in range(count):
            fraction = index / (count - 1)
            value = (
                geometry.shown_min_value
                + fraction
                * (
                    geometry.shown_max_value
                    - geometry.shown_min_value
                )
            )
            y = self._map_value_to_y(
                value,
                geometry.shown_min_value,
                geometry.shown_max_value,
                plot_rect,
            )

            painter.setPen(grid_pen)
            painter.drawLine(
                QPointF(plot_rect.left(), y),
                QPointF(plot_rect.right(), y),
            )

            label = f"{value:.{config.value_decimals}f}"
            label_rect = QRectF(
                0,
                y - metrics.height() / 2,
                plot_rect.left() - config.horizontal_spacing,
                metrics.height(),
            )

            painter.setPen(text_pen)
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
                label,
            )

        painter.setPen(QPen(theme.border, config.axis_width))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(plot_rect)

    def _draw_time_axis(
        self,
        painter: QPainter,
        geometry: PlotGeometry,
        theme: PlotTheme,
    ) -> None:
        config = self.config
        plot_rect = geometry.plot_rect
        metrics = painter.fontMetrics()

        painter.setPen(QPen(theme.text))

        label_top = (
            plot_rect.bottom()
            + config.tick_length
            + config.vertical_spacing
        )
        label_height = metrics.height()
        label_width = max(metrics.horizontalAdvance("-000.000"), 60)

        self._draw_time_label(
            painter,
            geometry.time_left,
            QRectF(
                plot_rect.left(),
                label_top,
                label_width,
                label_height,
            ),
            Qt.AlignmentFlag.AlignLeft,
        )
        self._draw_time_label(
            painter,
            geometry.time_right,
            QRectF(
                plot_rect.right() - label_width,
                label_top,
                label_width,
                label_height,
            ),
            Qt.AlignmentFlag.AlignRight,
        )
        self._draw_time_label(
            painter,
            geometry.time_current,
            QRectF(
                geometry.current_x - label_width / 2,
                label_top,
                label_width,
                label_height,
            ),
            Qt.AlignmentFlag.AlignHCenter,
        )

        painter.setPen(QPen(theme.border, config.axis_width))

        for x in (
            plot_rect.left(),
            geometry.current_x,
            plot_rect.right(),
        ):
            painter.drawLine(
                QPointF(x, plot_rect.bottom()),
                QPointF(x, plot_rect.bottom() + config.tick_length),
            )

    def _draw_time_label(
        self,
        painter: QPainter,
        value: float,
        rect: QRectF,
        horizontal_alignment: Qt.AlignmentFlag,
    ) -> None:
        painter.drawText(
            rect,
            horizontal_alignment | Qt.AlignmentFlag.AlignTop,
            f"{value:.{self.config.time_decimals}f}",
        )

    def _draw_axis_titles(
        self,
        painter: QPainter,
        geometry: PlotGeometry,
        theme: PlotTheme,
    ) -> None:
        config = self.config
        plot_rect = geometry.plot_rect

        original_font = painter.font()
        title_font = painter.font()
        title_font.setBold(True)

        painter.setFont(title_font)
        painter.setPen(QPen(theme.text))

        metrics = painter.fontMetrics()

        painter.drawText(
            QRectF(
                0,
                plot_rect.top() - metrics.height(),
                plot_rect.left() - config.horizontal_spacing,
                metrics.height(),
            ),
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
            "X",
        )

        painter.drawText(
            QRectF(
                plot_rect.left(),
                self.height() - metrics.height() - config.vertical_spacing,
                plot_rect.width(),
                metrics.height(),
            ),
            Qt.AlignmentFlag.AlignHCenter
            | Qt.AlignmentFlag.AlignVCenter,
            "Time",
        )

        painter.setFont(original_font)

    def _draw_current_time_indicator(
        self,
        painter: QPainter,
        geometry: PlotGeometry,
        theme: PlotTheme,
    ) -> None:
        pen = QPen(theme.indicator, self.config.axis_width)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)

        painter.drawLine(
            QPointF(geometry.current_x, geometry.plot_rect.top()),
            QPointF(geometry.current_x, geometry.plot_rect.bottom()),
        )

    def _draw_series(
        self,
        painter: QPainter,
        samples: Sequence[ScreenSample],
        theme: PlotTheme,
    ) -> None:
        for first, second in zip(samples, samples[1:]):
            color = (
                self._spin_to_color(first.spin)
                if first.frame < self.current_frame
                else theme.future
            )

            painter.setPen(QPen(color, self.config.series_width))
            painter.drawLine(first.position, second.position)

    def _draw_markers(
        self,
        painter: QPainter,
        samples: Sequence[ScreenSample],
        theme: PlotTheme,
    ) -> None:
        radius = self.config.marker_radius

        for sample in samples:
            color = (
                self._spin_to_color(sample.spin)
                if sample.frame <= self.current_frame
                else theme.future
            )

            painter.setPen(QPen(color))
            painter.setBrush(color)
            painter.drawEllipse(sample.position, radius, radius)

    @staticmethod
    def _spin_to_color(spin: int) -> QColor:
        return {
            1: COLOR_SPIN_UP,
            -1: COLOR_SPIN_DOWN,
        }.get(spin, COLOR_SPIN_NONE)


class HistoryWindow(QMainWindow):
    def __init__(
        self,
        node_index: int,
        point_id: str,
        simulation_data: TimeSeriesData,
        parent_window: QMainWindow,
        node_indexing: int = 1,
        # time_window: int = DEFAULT_TIME_WINDOW,
        plot_config: PlotConfig | None = None,
    ):
        super().__init__(parent_window)

        self.node_index = node_index
        self.point_id = point_id
        self.simulation_data = simulation_data
        self.parent_window = parent_window
        self.node_indexing = node_indexing
        # self.time_window = time_window
        self.time_window = DEFAULT_TIME_WINDOW

        self.bound_left: int | None = None
        self.bound_right: int | None = None
        self.current_frame = 0

        displayed_index = node_index + node_indexing
        identifier = point_id or ""
        self.setWindowTitle(
            f"Point # {displayed_index}  Id: {identifier}"
        )
        self.resize(*DEFAULT_WINDOW_SIZE)

        self.plot_widget = HistoryPlotWidget(
            simulation_data,
            node_index,
            self,
            config=plot_config,
        )
        self.setCentralWidget(self.plot_widget)

        self.set_frame_index(parent_window.time_slider.value())

    def set_frame_index(self, frame_index: int) -> None:
        max_frame = self.simulation_data.num_frames - 1
        self.current_frame = min(max(frame_index, 0), max_frame)

        outside_window = (
            self.bound_left is None
            or self.bound_right is None
            or self.current_frame < self.bound_left
            or self.current_frame > self.bound_right
        )

        if outside_window:
            self.bound_left = max(
                0,
                self.current_frame - self.time_window,
            )
            self.bound_right = min(
                max_frame,
                self.current_frame + self.time_window,
            )

        self.plot_widget.update_plot_data(
            current_frame=self.current_frame,
            bound_left=self.bound_left,
            bound_right=self.bound_right,
        )
