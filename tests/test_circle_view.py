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


def test_circle_view_drag_selection(qapp):
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtCore import QPointF, Qt

    view = CircleView()
    view.resize(500, 500)

    frame = DynamicFrame(
        time_index=0,
        time_value=0.0,
        spins=np.array([1, -1, 1], dtype=np.int8),
        x_values=np.array([0.0, 0.5, -0.5], dtype=float)
    )
    view.set_frame(frame)
    view._update_circle_geometry()

    pos0 = view._node_screen_position(0)
    pos1 = view._node_screen_position(1)
    pos2 = view._node_screen_position(2)

    # 1. Shift click toggle node 0 (press and release at the same position)
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        pos0,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ShiftModifier
    )
    view.mousePressEvent(press_event)

    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        pos0,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ShiftModifier
    )
    view.mouseReleaseEvent(release_event)
    assert view.selected_indices == {0}

    # 2. Shift-drag selection enclosing node 1 and 2 (using a box that covers the lower half of the circle)
    # Lower half has y >= cy.
    # cx, cy is the circle center.
    cx = view.circle_center.x()
    cy = view.circle_center.y()
    r = view.circle_radius

    # Box enclosing the bottom part of the circle (y >= cy - 10)
    drag_start = QPointF(cx - r - 20, cy - 20)
    drag_end = QPointF(cx + r + 20, cy + r + 20)

    press_drag = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        drag_start,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ShiftModifier
    )
    view.mousePressEvent(press_drag)

    move_drag = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        drag_end,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ShiftModifier
    )
    view.mouseMoveEvent(move_drag)

    # Union of {0} (pre-selected) and the points inside the rectangle ({0, 1, 2})
    assert view.selected_indices == {0, 1, 2}

    release_drag = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        drag_end,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ShiftModifier
    )
    view.mouseReleaseEvent(release_drag)
    assert view.selected_indices == {0, 1, 2}
