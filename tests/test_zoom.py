# tests/test_zoom.py

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QMouseEvent

from dice_gui.domain import DynamicFrame, LoadedSimulation, TimeSeriesData
from dice_gui.loading import ParserRegistry
from dice_gui.widgets.main_window import MainWindow
from dice_gui.widgets.zoom_window import (
    ZoomedCircleView,
    ZoomWindow,
    _is_x_in_interval,
    _sample_interval,
)

class MockParser:
    def __init__(self, parser_id, name="Mock Parser"):
        self.id = parser_id
        self.name = name

    def parse_file(self, file_path):
        times = np.array([0.0])
        spins = np.array([[1]])
        x_values = np.array([[0.0]])
        return LoadedSimulation(
            dynamic_data=TimeSeriesData(times=times, spins=spins, x_values=x_values)
        )


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_is_x_in_interval():
    # Simple interval
    assert _is_x_in_interval(0.0, -0.5, 0.5) is True
    assert _is_x_in_interval(-0.6, -0.5, 0.5) is False
    assert _is_x_in_interval(0.6, -0.5, 0.5) is False

    # Boundaries
    assert _is_x_in_interval(-0.5, -0.5, 0.5) is True
    assert _is_x_in_interval(0.5, -0.5, 0.5) is True

    # Wrap-around interval
    assert _is_x_in_interval(0.9, 0.8, -0.8) is True
    assert _is_x_in_interval(-0.9, 0.8, -0.8) is True
    assert _is_x_in_interval(0.0, 0.8, -0.8) is False


def test_sample_interval():
    # Standard interval
    samples = list(_sample_interval(-0.5, 0.5, 4))
    assert len(samples) == 5
    assert pytest.approx(samples[0]) == -0.5
    assert pytest.approx(samples[2]) == 0.0
    assert pytest.approx(samples[4]) == 0.5

    # Wrap-around interval
    samples_wrap = list(_sample_interval(0.8, -0.8, 4))
    assert len(samples_wrap) == 5
    assert pytest.approx(samples_wrap[0]) == 0.8
    # Total length is (1.0 - 0.8) + (-0.8 - (-1.0)) = 0.2 + 0.2 = 0.4
    # Step size is 0.4 / 4 = 0.1
    assert pytest.approx(samples_wrap[1]) == 0.9
    assert pytest.approx(samples_wrap[2]) == 1.0  # wraps to -1.0
    assert pytest.approx(samples_wrap[3]) == -0.9
    assert pytest.approx(samples_wrap[4]) == -0.8


def test_zoomed_circle_view_rendering_logic(qapp):
    frame = DynamicFrame(
        time_index=0,
        time_value=0.0,
        # nodes at x = -0.5 (left), 0.0 (bottom), 0.5 (right)
        spins=np.array([1, -1, 1], dtype=np.int8),
        x_values=np.array([-0.5, 0.0, 0.5], dtype=float)
    )

    # Zoomed view from -0.6 to 0.1. Should contain nodes at -0.5 and 0.0, but not 0.5
    view = ZoomedCircleView(x_min=-0.6, x_max=0.1)
    view.resize(500, 500)
    view.set_frame(frame)

    # Verify _nearest_node respects interval
    # Pos near node 2 (x=0.5, which is right: 3 o'clock)
    # The normal CircleView nearest node would be 2. But ZoomedCircleView should ignore it!
    view._update_circle_geometry()

    pos2 = view._node_screen_position(2)
    idx, dist = view._nearest_node(pos2)
    assert idx != 2

    # Verify node 0 (x=-0.5) is within range and can be selected
    pos0 = view._node_screen_position(0)
    idx0, dist0 = view._nearest_node(pos0)
    assert idx0 == 0


def test_drag_to_zoom_interaction(qapp):
    view = ZoomedCircleView(x_min=-1.0, x_max=1.0)
    view.resize(500, 500)

    frame = DynamicFrame(
        time_index=0,
        time_value=0.0,
        spins=np.array([1, -1, 1], dtype=np.int8),
        x_values=np.array([-0.5, 0.0, 0.5], dtype=float)
    )
    view.set_frame(frame)
    view._update_circle_geometry()

    # Track signal emission
    zoom_args = []
    view.zoom_requested.connect(lambda xmin, xmax: zoom_args.append((xmin, xmax)))

    # Trigger normal drag (without Shift)
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(100, 100),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    view.mousePressEvent(press_event)
    assert view._is_zoom_dragging is False

    # Move mouse to drag
    move_event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(200, 200),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    view.mouseMoveEvent(move_event)
    assert view._is_zoom_dragging is True

    # Release mouse to trigger zoom
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(200, 200),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    view.mouseReleaseEvent(release_event)

    assert view._is_zoom_dragging is False
    assert len(zoom_args) == 1
    xmin, xmax = zoom_args[0]
    assert -1.0 <= xmin <= 1.0
    assert -1.0 <= xmax <= 1.0


def test_zoom_window_creation_and_sync(qapp):
    registry = ParserRegistry()
    parser = MockParser("mock_id")
    registry.register(parser, default=True)

    window = MainWindow(registry)
    frame = DynamicFrame(
        time_index=0,
        time_value=0.0,
        spins=np.array([1, -1, 1], dtype=np.int8),
        x_values=np.array([-0.5, 0.0, 0.5], dtype=float)
    )
    window.circle_view.set_frame(frame)
    window.point_ids = ["A", "B", "C"]
    window.circle_view.set_point_ids(window.point_ids)
    window.set_app_selection({1})

    # Open zoom window
    window.open_zoom_window(-0.2, 0.2)
    assert len(window.zoom_windows) == 1
    zoom_win = window.zoom_windows[0]

    # Verify state matches
    assert zoom_win.x_min == -0.2
    assert zoom_win.x_max == 0.2
    assert zoom_win.zoomed_view.point_ids == ["A", "B", "C"]
    assert zoom_win.zoomed_view.selected_indices == {1}

    # Check selection change propagation
    zoom_win.zoomed_view.set_selected_indices({2})
    assert window.selected_point_indices == {2}
    assert window.circle_view.selected_indices == {2}

    # Close window
    zoom_win.close()
    assert len(window.zoom_windows) == 0
