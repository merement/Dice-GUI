# tests/test_feature3.py

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication

from dice_gui.domain import LoadedSimulation, TimeSeriesData
from dice_gui.loading import ParserRegistry
from dice_gui.widgets.main_window import MainWindow
from dice_gui.widgets.trace_window import TraceWindow, TracePlotWidget


class MockParser:
    def __init__(self, parser_id="mock_id"):
        self.id = parser_id
        self.name = "Mock Parser"

    def parse_file(self, file_path):
        times = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
        spins = np.ones((5, 3), dtype=np.int8)
        # Node 0: [0.0, 0.2, 0.4, 0.6, 0.8]
        # Node 1: [1.0, 1.0, 1.0, 1.0, 1.0]
        # Node 2: [-0.5, -0.5, -0.5, -0.5, -0.5]
        x_values = np.zeros((5, 3), dtype=float)
        x_values[:, 0] = np.array([0.0, 0.2, 0.4, 0.6, 0.8])
        x_values[:, 1] = 1.0
        x_values[:, 2] = -0.5
        return LoadedSimulation(
            dynamic_data=TimeSeriesData(times=times, spins=spins, x_values=x_values)
        )


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_point_info_panel_trace_icons(qapp):
    registry = ParserRegistry()
    registry.register(MockParser(), default=True)
    window = MainWindow(registry)

    panel = window.point_info_panel
    assert panel.trace_button.toolTip() == "Trace selected nodes"
    assert panel.mean_trace_button.toolTip() == "Show the trace of the mean value of selected nodes (COM)"
    assert panel.close_all_traces_button.toolTip() == "Close all tracing windows"
    assert not panel.trace_button.icon().isNull()
    assert not panel.mean_trace_button.icon().isNull()
    assert not panel.close_all_traces_button.icon().isNull()


def test_mean_value_trace_window(qapp):
    registry = ParserRegistry()
    registry.register(MockParser(), default=True)
    window = MainWindow(registry)
    loaded_sim = MockParser().parse_file("dummy.txt")
    window.on_simulation_loaded(loaded_sim)

    # 1. Click Mean Value Trace with no selection
    window.set_app_selection(set())
    window.on_mean_trace_clicked()
    assert window.status_bar.currentMessage() == "No points are selected"
    assert len(window.trace_windows) == 0

    # 2. Select points 0 and 2 (1-based displayed: 1 and 3)
    window.set_app_selection({0, 2})
    window.on_mean_trace_clicked()
    assert len(window.trace_windows) == 1

    tw = window.trace_windows[0]
    assert isinstance(tw, TraceWindow)
    assert tw.is_mean is True
    assert tw.windowTitle() == "Mean X of Points # 1, 3"

    # Test mean values calculated in plot widget
    tw.set_frame_index(0)
    samples = tw.plot_widget._extract_samples()
    # At frame 0: node 0 is 0.0, node 2 is -0.5 -> mean is -0.25
    assert samples[0].value == pytest.approx(-0.25)
    # At frame 2: node 0 is 0.4, node 2 is -0.5 -> mean is -0.05
    assert samples[2].value == pytest.approx(-0.05)


def test_close_all_tracing_windows(qapp):
    registry = ParserRegistry()
    registry.register(MockParser(), default=True)
    window = MainWindow(registry)
    loaded_sim = MockParser().parse_file("dummy.txt")
    window.on_simulation_loaded(loaded_sim)

    window.set_app_selection({0, 1})
    window.on_trace_clicked()
    assert len(window.trace_windows) == 2

    window.on_mean_trace_clicked()
    assert len(window.trace_windows) == 3

    window.on_close_all_traces_clicked()
    assert len(window.trace_windows) == 0
    assert window.status_bar.currentMessage() == "Closed all tracing windows"
