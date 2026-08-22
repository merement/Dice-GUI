# tests/test_copy_panel_info.py

import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication

from dice_gui.widgets.point_info_panel import PointInfoPanel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_point_info_panel_clipboard_copy(qapp):
    panel = PointInfoPanel()
    spins = np.array([1, -1, 1], dtype=np.int8)
    x_values = np.array([0.123456, -0.654321, 0.0], dtype=float)
    point_ids = ["node_A", "node_B", ""]
    selected_indices = {0, 1}

    panel.update_points(
        spins=spins,
        x_values=x_values,
        selected_indices=selected_indices,
        point_ids=point_ids,
        node_indexing=1,
    )

    # Perform copy
    panel.copy_selected_rows_to_clipboard()

    clipboard = QApplication.clipboard()
    copied_text = clipboard.text()

    lines = copied_text.splitlines()
    assert len(lines) == 2

    # Check row 1 format: 1\t"node_A"\t+1\t0.123456\t0.000000
    fields_0 = lines[0].split("\t")
    assert fields_0[0] == "1"
    assert fields_0[1] == '"node_A"'
    assert fields_0[2] == "+1"
    assert fields_0[3] == "0.123456"

    # Check row 2 format: 2\t"node_B"\t-1\t-0.654321\t0.000000
    fields_1 = lines[1].split("\t")
    assert fields_1[0] == "2"
    assert fields_1[1] == '"node_B"'
    assert fields_1[2] == "-1"
    assert fields_1[3] == "-0.654321"
