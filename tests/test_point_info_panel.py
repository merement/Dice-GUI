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
    assert headers == ["#", "Id", "Spin", "X", "ΔX"]


def test_point_info_panel_update_points(qapp):
    panel = PointInfoPanel()
    spins = [1, -1]
    x_values = [0.1, -0.2]
    point_ids = ["A", "B"]

    panel.update_points(spins, x_values, selected_indices={1}, point_ids=point_ids)

    # We should have 2 rows
    assert panel.table.rowCount() == 2

    # Row 0
    assert panel.table.item(0, 0).text() == "0"
    assert panel.table.item(0, 1).text() == "A"
    assert panel.table.item(0, 2).text() == "+1"
    assert panel.table.item(0, 3).text() == "0.100000"
    assert panel.table.item(0, 4).text() == "0.000000"

    # Row 1
    assert panel.table.item(1, 0).text() == "1"
    assert panel.table.item(1, 1).text() == "B"
    assert panel.table.item(1, 2).text() == "-1"
    assert panel.table.item(1, 3).text() == "-0.200000"
    assert panel.table.item(1, 4).text() == "0.000000"

    # Row 1 should be selected
    selected_ranges = panel.table.selectedRanges()
    assert len(selected_ranges) == 1
    assert selected_ranges[0].topRow() == 1

    # Now update with next_x_values
    next_x_values = [0.3, -0.05]
    panel.update_points(spins, x_values, selected_indices={1}, point_ids=point_ids, next_x_values=next_x_values)

    # Delta for A: 0.3 - 0.1 = 0.2
    assert panel.table.item(0, 4).text() == "0.200000"
    # Delta for B: -0.05 - (-0.2) = 0.15
    assert panel.table.item(1, 4).text() == "0.150000"


def test_point_info_panel_filter(qapp):
    panel = PointInfoPanel()
    spins = [1, -1]
    x_values = [0.1, -0.2]
    point_ids = ["A", "B"]

    panel.update_points(spins, x_values, selected_indices={1}, point_ids=point_ids)

    # Check "Show selected"
    panel.show_selected_radio.setChecked(True)
    assert panel.table.rowCount() == 1
    assert panel.table.item(0, 0).text() == "1"

    # Check "Show all" again
    panel.show_all_radio.setChecked(True)
    assert panel.table.rowCount() == 2


def test_point_info_panel_multi_selection(qapp):
    panel = PointInfoPanel()
    spins = [1, -1, 1]
    x_values = [0.1, -0.2, 0.3]
    point_ids = ["A", "B", "C"]

    # Select nodes 0 and 2
    panel.update_points(spins, x_values, selected_indices={0, 2}, point_ids=point_ids)

    # Check that rows 0 and 2 are selected
    assert panel.table.item(0, 0).isSelected()
    assert not panel.table.item(1, 0).isSelected()
    assert panel.table.item(2, 0).isSelected()

    # In "Show selected" mode, only 0 and 2 should be shown
    panel.show_selected_radio.setChecked(True)
    assert panel.table.rowCount() == 2
    assert panel.table.item(0, 0).text() == "0"
    assert panel.table.item(1, 0).text() == "2"
