# tests/test_playback_icons.py

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication

from dice_gui.domain import LoadedSimulation, TimeSeriesData
from dice_gui.loading import ParserRegistry
from dice_gui.widgets.main_window import MainWindow


class MockParser:
    def __init__(self, parser_id="mock_id"):
        self.id = parser_id
        self.name = "Mock Parser"

    def parse_file(self, file_path):
        times = np.array([0.0, 0.1, 0.2])
        spins = np.array([[1], [1], [1]], dtype=np.int8)
        x_values = np.array([[0.0], [0.1], [0.2]])
        return LoadedSimulation(
            dynamic_data=TimeSeriesData(times=times, spins=spins, x_values=x_values)
        )


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_playback_button_icons_and_tooltips(qapp):
    registry = ParserRegistry()
    registry.register(MockParser(), default=True)
    window = MainWindow(registry)

    # Initial state verification
    assert window.play_pause_button.toolTip() == "Play"
    assert window.progress_button.toolTip() == "Step forward"
    assert window.regress_button.toolTip() == "Step backward"
    assert not window.play_pause_button.icon().isNull()
    assert not window.progress_button.icon().isNull()
    assert not window.regress_button.icon().isNull()

    # Toggle play/pause
    window.toggle_play_pause()
    assert window._is_playing is True
    assert window.play_pause_button.toolTip() == "Pause"

    window.toggle_play_pause()
    assert window._is_playing is False
    assert window.play_pause_button.toolTip() == "Play"
