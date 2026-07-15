# tests/test_history.py

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication

from dice_gui.domain import DynamicFrame, LoadedSimulation, TimeSeriesData
from dice_gui.loading import ParserRegistry
from dice_gui.widgets.main_window import MainWindow
from dice_gui.widgets.history_window import HistoryWindow, HistoryPlotWidget, TIME_WINDOW
from dice_gui.widgets.circle_view import COLOR_SPIN_UP, COLOR_SPIN_DOWN, COLOR_SPIN_NONE


class MockParser:
    def __init__(self, parser_id, name="Mock Parser"):
        self.id = parser_id
        self.name = name

    def parse_file(self, file_path):
        times = np.arange(150, dtype=float) * 0.1
        spins = np.ones((150, 3), dtype=np.int8)
        spins[:, 1] = -1
        x_values = np.zeros((150, 3), dtype=float)
        x_values[:, 0] = -0.5
        x_values[:, 2] = 0.5
        return LoadedSimulation(
            dynamic_data=TimeSeriesData(times=times, spins=spins, x_values=x_values)
        )


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_history_window_bounds_calculation(qapp):
    times = np.arange(150, dtype=float) * 0.1
    spins = np.ones((150, 3), dtype=np.int8)
    x_values = np.zeros((150, 3), dtype=float)
    data = TimeSeriesData(times=times, spins=spins, x_values=x_values)

    registry = ParserRegistry()
    parser = MockParser("mock_id")
    registry.register(parser, default=True)
    window = MainWindow(registry)

    # Initialize a mock simulation loaded state
    loaded_sim = LoadedSimulation(dynamic_data=data)
    window.on_simulation_loaded(loaded_sim)

    # 1. Test initial bounds with frame = 0
    window.time_slider.setValue(0)
    hw = HistoryWindow(node_index=1, point_id="test_id", simulation_data=data, parent_window=window)
    
    assert hw.node_index == 1
    assert hw.point_id == "test_id"
    assert hw.windowTitle() == "Point # 1  Id: test_id"
    assert hw.bound_left == 0
    assert hw.bound_right == TIME_WINDOW  # 50
    assert hw.current_frame == 0

    # 2. Update frame within bounds (e.g. 30): bounds should not change
    hw.set_frame_index(30)
    assert hw.bound_left == 0
    assert hw.bound_right == TIME_WINDOW
    assert hw.current_frame == 30

    # 3. Update frame out of bounds (e.g. 60): bounds should shift
    hw.set_frame_index(60)
    assert hw.bound_left == 60 - TIME_WINDOW  # 10
    assert hw.bound_right == 60 + TIME_WINDOW  # 110
    assert hw.current_frame == 60

    # 4. Check boundaries limits at the end of frames (e.g. 145)
    hw.set_frame_index(145)
    assert hw.bound_left == 145 - TIME_WINDOW  # 95
    assert hw.bound_right == 149  # min(149, 195)
    assert hw.current_frame == 145

    hw.close()


def test_history_plot_widget_colors(qapp):
    times = np.arange(10, dtype=float)
    spins = np.array([[1, -1, 1]] * 10, dtype=np.int8)
    x_values = np.zeros((10, 3), dtype=float)
    data = TimeSeriesData(times=times, spins=spins, x_values=x_values)

    plot_widget = HistoryPlotWidget(simulation_data=data, node_index=0)
    assert plot_widget._spin_to_color(1) == COLOR_SPIN_UP
    assert plot_widget._spin_to_color(-1) == COLOR_SPIN_DOWN
    assert plot_widget._spin_to_color(0) == COLOR_SPIN_NONE


def test_main_window_trace_handling(qapp):
    registry = ParserRegistry()
    parser = MockParser("mock_id")
    registry.register(parser, default=True)

    window = MainWindow(registry)
    times = np.arange(120, dtype=float)
    spins = np.ones((120, 3), dtype=np.int8)
    x_values = np.zeros((120, 3), dtype=float)
    data = TimeSeriesData(times=times, spins=spins, x_values=x_values)
    loaded_sim = LoadedSimulation(dynamic_data=data)
    window.on_simulation_loaded(loaded_sim)

    # 1. No selected points: clicking Trace should do nothing and show message
    window.set_app_selection(set())
    window.on_trace_clicked()
    assert window.status_bar.currentMessage() == "No points are selected"
    assert len(window.history_windows) == 0

    # 2. Selected points: clicking Trace should open windows
    window.set_app_selection({0, 2})
    window.on_trace_clicked()
    assert len(window.history_windows) == 2
    
    node_indices = {hw.node_index for hw in window.history_windows}
    assert node_indices == {0, 2}

    # 3. Duplicate trace click should raise window instead of opening duplicate
    window.on_trace_clicked()
    assert len(window.history_windows) == 2

    # 4. Loading a new simulation should close all history windows
    window.on_simulation_loaded(loaded_sim)
    assert len(window.history_windows) == 0


def test_history_plot_widget_x_bounds(qapp):
    times = np.arange(5, dtype=float)
    spins = np.ones((5, 1), dtype=np.int8)
    
    # Case A: Constant X in the middle
    x_values = np.array([[0.5]] * 5, dtype=float)
    data = TimeSeriesData(times=times, spins=spins, x_values=x_values)
    plot_widget = HistoryPlotWidget(simulation_data=data, node_index=0)
    plot_widget.update_plot_data(current_frame=2, bound_left=0, bound_right=4)
    
    # Emulate the calculation logic
    x_slice = [plot_widget.simulation_data.x_values[t, plot_widget.node_index] for t in range(plot_widget.bound_left, plot_widget.bound_right + 1)]
    min_X = min(x_slice)
    max_X = max_X = max(x_slice)
    shown_min_x = max(-1.0, min_X - 0.05)
    shown_max_x = min(1.0, max_X + 0.05)
    assert shown_min_x == pytest.approx(0.45)
    assert shown_max_x == pytest.approx(0.55)

    # Case B: Close to upper limit (clamping to 1.0)
    x_values = np.array([[0.95]] * 5, dtype=float)
    data = TimeSeriesData(times=times, spins=spins, x_values=x_values)
    plot_widget = HistoryPlotWidget(simulation_data=data, node_index=0)
    plot_widget.update_plot_data(current_frame=2, bound_left=0, bound_right=4)
    x_slice = [plot_widget.simulation_data.x_values[t, plot_widget.node_index] for t in range(plot_widget.bound_left, plot_widget.bound_right + 1)]
    min_X = min(x_slice)
    max_X = max(x_slice)
    shown_min_x = max(-1.0, min_X - 0.05)
    shown_max_x = min(1.0, max_X + 0.05)
    assert shown_min_x == pytest.approx(0.90)
    assert shown_max_x == pytest.approx(1.0)
