from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFormLayout, QGroupBox, QLabel


class PointInfoPanel(QGroupBox):
    """
    Dedicated widget for displaying details of the selected simulation node.
    """

    def __init__(self, parent=None):
        super().__init__("Point Info", parent)
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.time_val_label = QLabel("-", self)
        self.index_val_label = QLabel("-", self)
        self.spin_val_label = QLabel("-", self)
        self.coord_val_label = QLabel("-", self)

        # Stylized visual labels
        label_style = "font-weight: bold; color: #4a4a4a;"
        value_style = "font-family: monospace; font-size: 12px;"

        self.time_val_label.setStyleSheet(value_style)
        self.index_val_label.setStyleSheet(value_style)
        self.spin_val_label.setStyleSheet(value_style)
        self.coord_val_label.setStyleSheet(value_style)

        t_lbl = QLabel("Time:", self)
        t_lbl.setStyleSheet(label_style)
        i_lbl = QLabel("Node Index:", self)
        i_lbl.setStyleSheet(label_style)
        s_lbl = QLabel("Spin (s):", self)
        s_lbl.setStyleSheet(label_style)
        c_lbl = QLabel("Coordinate (X):", self)
        c_lbl.setStyleSheet(label_style)

        layout.addRow(t_lbl, self.time_val_label)
        layout.addRow(i_lbl, self.index_val_label)
        layout.addRow(s_lbl, self.spin_val_label)
        layout.addRow(c_lbl, self.coord_val_label)

        self.setLayout(layout)

    def update_info(self, time_value: float, index: int, spin: int, x_value: float):
        self.time_val_label.setText(f"{time_value:.3f}")
        self.index_val_label.setText(str(index))

        if spin == 1:
            self.spin_val_label.setText('<span style="color: #d32f2f; font-weight: bold;">+1 (Up)</span>')
        elif spin == -1:
            self.spin_val_label.setText('<span style="color: #1976d2; font-weight: bold;">-1 (Down)</span>')
        else:
            self.spin_val_label.setText(str(spin))

        self.coord_val_label.setText(f"{x_value:.6f}")

    def clear_info(self, message: str = "No point selected"):
        self.time_val_label.setText("-")
        self.index_val_label.setText(message)
        self.spin_val_label.setText("-")
        self.coord_val_label.setText("-")
