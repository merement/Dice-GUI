import pytest
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl
from dice_gui.widgets.main_window import MainWindow
from dice_gui.loading import ParserRegistry

class MockParser:
    def __init__(self, parser_id, name="Mock Parser"):
        self.id = parser_id
        self.name = name
        self.file_filter = "Mock Files (*.mock)"

    def parse_file(self, file_path):
        import numpy as np
        from dice_gui.domain import LoadedSimulation, TimeSeriesData
        times = np.array([0.0])
        spins = np.array([[1]])
        x_values = np.array([[0.0]])
        return LoadedSimulation(
            dynamic_data=TimeSeriesData(times=times, spins=spins, x_values=x_values),
            source_path=str(file_path),
            parser_id=self.id
        )

class MockMimeData:
    def __init__(self, urls):
        self._urls = urls

    def hasUrls(self):
        return bool(self._urls)

    def urls(self):
        return self._urls

class MockEvent:
    def __init__(self, urls):
        self._mime_data = MockMimeData(urls)
        self.accepted = False
        self.ignored = False

    def mimeData(self):
        return self._mime_data

    def acceptProposedAction(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_main_window_drag_enter_accept(qapp, tmp_path):
    registry = ParserRegistry()
    parser = MockParser("mock_id")
    registry.register(parser, default=True)

    window = MainWindow(registry)

    # Drag enter with URLs should be accepted
    url = QUrl.fromLocalFile(str(tmp_path / "test.mock"))
    event = MockEvent([url])
    window.dragEnterEvent(event)
    assert event.accepted
    assert not event.ignored


def test_main_window_drag_enter_ignore(qapp):
    registry = ParserRegistry()
    parser = MockParser("mock_id")
    registry.register(parser, default=True)

    window = MainWindow(registry)

    # Drag enter with no URLs should be ignored
    event = MockEvent([])
    window.dragEnterEvent(event)
    assert not event.accepted
    assert event.ignored


def test_main_window_drop_file(qapp, tmp_path):
    registry = ParserRegistry()
    parser = MockParser("mock_id")
    registry.register(parser, default=True)

    window = MainWindow(registry)

    # Create dummy file
    dummy_file = tmp_path / "test.mock"
    dummy_file.write_text("hello", encoding="utf-8")

    url = QUrl.fromLocalFile(str(dummy_file))
    event = MockEvent([url])

    # Verify file is not loaded yet
    assert window.loaded_simulation is None

    # Trigger drop
    window.dropEvent(event)

    # Verify drop was accepted and file loaded
    assert event.accepted
    assert not event.ignored
    assert window.loaded_simulation is not None
    assert window.loaded_simulation.parser_id == "mock_id"
    assert window.loaded_simulation.source_path == dummy_file
    assert window.windowTitle() == "test.mock"


def test_main_window_drop_non_file(qapp, tmp_path):
    registry = ParserRegistry()
    parser = MockParser("mock_id")
    registry.register(parser, default=True)

    window = MainWindow(registry)

    # Non-existent file should be ignored
    non_existent = tmp_path / "does_not_exist.mock"
    url = QUrl.fromLocalFile(str(non_existent))
    event = MockEvent([url])

    window.dropEvent(event)

    assert not event.accepted
    assert event.ignored
    assert window.loaded_simulation is None
