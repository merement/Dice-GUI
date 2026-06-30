import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from dice_gui.widgets.point_info_panel import PointInfoPanel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_point_info_panel_init(qapp):
    panel = PointInfoPanel()
    assert panel.title() == "Point Info"
    assert panel.table.columnCount() == 5
    assert panel.show_all_radio.isChecked()
    headers = [panel.table.horizontalHeaderItem(i).text() for i in range(5)]
    assert headers == ["#", "Id", "Sigma", "X", "Delta"]


def test_point_info_panel_update_points(qapp):
    panel = PointInfoPanel()
    spins = [1, -1]
    x_values = [0.1, -0.2]
    point_ids = ["A", "B"]

    panel.update_points(spins, x_values, selected_index=1, point_ids=point_ids)

    # We should have 2 rows
    assert panel.table.rowCount() == 2

    # Row 0
    assert panel.table.item(0, 0).text() == "0"
    assert panel.table.item(0, 1).text() == "A"
    assert panel.table.item(0, 2).text() == "+1"
    assert panel.table.item(0, 3).text() == "0.100000"

    # Row 1
    assert panel.table.item(1, 0).text() == "1"
    assert panel.table.item(1, 1).text() == "B"
    assert panel.table.item(1, 2).text() == "-1"
    assert panel.table.item(1, 3).text() == "-0.200000"

    # Row 1 should be selected
    selected_ranges = panel.table.selectedRanges()
    assert len(selected_ranges) == 1
    assert selected_ranges[0].topRow() == 1


def test_point_info_panel_filter(qapp):
    panel = PointInfoPanel()
    spins = [1, -1]
    x_values = [0.1, -0.2]
    point_ids = ["A", "B"]

    panel.update_points(spins, x_values, selected_index=1, point_ids=point_ids)

    # Check "Show selected"
    panel.show_selected_radio.setChecked(True)
    assert panel.table.rowCount() == 1
    assert panel.table.item(0, 0).text() == "1"

    # Check "Show all" again
    panel.show_all_radio.setChecked(True)
    assert panel.table.rowCount() == 2
