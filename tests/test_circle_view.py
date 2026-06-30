import pytest
import numpy as np
from PyQt6.QtWidgets import QApplication
from dice_gui.widgets.circle_view import CircleView
from dice_gui.domain import DynamicFrame


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_circle_view_selection(qapp):
    view = CircleView()
    frame = DynamicFrame(
        time_index=0,
        time_value=0.0,
        spins=np.array([1, -1, 1], dtype=np.int8),
        x_values=np.array([0.0, 0.5, -0.5], dtype=float)
    )
    view.set_frame(frame)

    # Initial selection is empty
    assert len(view.selected_indices) == 0

    # Select node index 1
    view.set_selected_indices({1})
    assert view.selected_indices == {1}

    # Select multiple nodes (0 and 2)
    view.set_selected_indices({0, 2})
    assert view.selected_indices == {0, 2}

    # Verify invalid indices are filtered out
    view.set_selected_indices({0, 2, 5})
    assert view.selected_indices == {0, 2}

    # Clear selection
    view.clear_selection()
    assert len(view.selected_indices) == 0


def test_circle_view_point_ids(qapp):
    view = CircleView()
    frame = DynamicFrame(
        time_index=0,
        time_value=0.0,
        spins=np.array([1, -1, 1], dtype=np.int8),
        x_values=np.array([0.0, 0.5, -0.5], dtype=float)
    )
    view.set_frame(frame)

    view.set_point_ids(["node_A", "node_B", "node_C"])
    assert view.point_ids == ["node_A", "node_B", "node_C"]
