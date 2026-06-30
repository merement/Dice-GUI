from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QRadioButton,
    QButtonGroup,
    QHBoxLayout,
    QVBoxLayout,
    QHeaderView,
)


class PointInfoPanel(QGroupBox):
    """
    Dedicated widget for displaying details of the simulation nodes in a table.
    """
    point_selected = pyqtSignal(object)  # Emits node_index (int or None)
    point_id_changed = pyqtSignal(int, str)  # Emits (node_index, new_id)

    def __init__(self, parent=None):
        super().__init__("Point Info", parent)

        self._last_spins = None
        self._last_x_values = None
        self._last_selected_index = None
        self._last_point_ids = []
        self._updating_table = False

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Filter buttons/checklist (Show all / selected)
        filter_layout = QHBoxLayout()
        self.show_all_radio = QRadioButton("Show all", self)
        self.show_selected_radio = QRadioButton("Show selected", self)
        self.show_all_radio.setChecked(True)

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.show_all_radio)
        self.button_group.addButton(self.show_selected_radio)

        filter_layout.addWidget(self.show_all_radio)
        filter_layout.addWidget(self.show_selected_radio)
        filter_layout.addStretch(1)

        main_layout.addLayout(filter_layout)

        # Table Widget
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["#", "Id", "Sigma", "X", "Delta"])

        # Configure Table properties
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        # Connect signals
        self.show_all_radio.toggled.connect(self._on_filter_changed)
        self.show_selected_radio.toggled.connect(self._on_filter_changed)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.table.itemChanged.connect(self._on_item_changed)

    def update_info(self, time_value: float, index: int, spin: int, x_value: float):
        """
        Compatibility method. Handled by update_points now.
        """
        pass

    def clear_info(self, message: str = "No point selected"):
        """
        Clears the table and cached data.
        """
        self._last_spins = None
        self._last_x_values = None
        self._last_selected_index = None
        self._last_point_ids = []
        self._refresh_table()

    def update_points(self, spins, x_values, selected_index, point_ids):
        """
        Updates the table with data from the current frame.
        """
        self._last_spins = spins
        self._last_x_values = x_values
        self._last_selected_index = selected_index
        self._last_point_ids = point_ids

        self._refresh_table()

    def _on_filter_changed(self):
        self._refresh_table()

    def _refresh_table(self):
        if self._last_spins is None or self._last_x_values is None:
            self._updating_table = True
            self.table.blockSignals(True)
            self.table.setRowCount(0)
            self.table.blockSignals(False)
            self._updating_table = False
            return

        self._updating_table = True
        self.table.blockSignals(True)

        self.table.clearSelection()

        show_all = self.show_all_radio.isChecked()

        rows_to_show = []
        num_nodes = len(self._last_spins)
        for i in range(num_nodes):
            spin = self._last_spins[i]
            x_val = self._last_x_values[i]
            p_id = self._last_point_ids[i] if i < len(self._last_point_ids) else ""

            if show_all or (self._last_selected_index == i):
                rows_to_show.append((i, spin, x_val, p_id))

        self.table.setRowCount(len(rows_to_show))

        highlighted_row = None

        for row_idx, (node_idx, spin, x_val, p_id) in enumerate(rows_to_show):
            # Column 0: Number (index)
            item_num = QTableWidgetItem(str(node_idx))
            item_num.setData(Qt.ItemDataRole.UserRole, node_idx)
            item_num.setFlags(item_num.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 0, item_num)

            # Column 1: Id
            item_id = QTableWidgetItem(str(p_id))
            item_id.setData(Qt.ItemDataRole.UserRole, node_idx)
            item_id.setFlags(item_id.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 1, item_id)

            # Column 2: Sigma (spin)
            sigma_str = "+1" if spin == 1 else "-1" if spin == -1 else str(spin)
            item_sigma = QTableWidgetItem(sigma_str)
            item_sigma.setData(Qt.ItemDataRole.UserRole, node_idx)
            item_sigma.setFlags(item_sigma.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 2, item_sigma)

            # Column 3: X (coordinate)
            item_x = QTableWidgetItem(f"{x_val:.6f}")
            item_x.setData(Qt.ItemDataRole.UserRole, node_idx)
            item_x.setFlags(item_x.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 3, item_x)

            # Column 4: Delta
            item_delta = QTableWidgetItem("")
            item_delta.setData(Qt.ItemDataRole.UserRole, node_idx)
            item_delta.setFlags(item_delta.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_idx, 4, item_delta)

            if self._last_selected_index == node_idx:
                highlighted_row = row_idx

        if highlighted_row is not None:
            self.table.selectRow(highlighted_row)

        self.table.blockSignals(False)
        self._updating_table = False

    def _on_item_changed(self, item):
        if self._updating_table:
            return
        if item.column() == 1:  # Id column
            node_index = item.data(Qt.ItemDataRole.UserRole)
            if node_index is not None:
                new_id = item.text()
                if self._last_point_ids is not None and node_index < len(self._last_point_ids):
                    self._last_point_ids[node_index] = new_id
                self.point_id_changed.emit(node_index, new_id)

    def _on_table_selection_changed(self):
        if self._updating_table:
            return

        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            self.point_selected.emit(None)
            return

        row = selected_ranges[0].topRow()
        item = self.table.item(row, 0)
        if item is not None:
            node_index = item.data(Qt.ItemDataRole.UserRole)
            self.point_selected.emit(node_index)
