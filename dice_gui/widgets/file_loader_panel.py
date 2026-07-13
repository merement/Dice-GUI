from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QPushButton, QVBoxLayout, QWidget


class FileLoaderPanel(QWidget):
    """
    Panel for selecting the primary simulation data file.

    This widget is intentionally narrow in scope. It does not parse files and
    does not know about parser registries. MainWindow decides which file filter
    to use and what parser should handle the selected file.
    """

    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._dialog_title = "Select Simulation Data File"
        self._file_filter = "All Files (*)"

        self.open_button = QPushButton("Open Data File", self)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.open_button)
        self.setLayout(layout)

        self.open_button.clicked.connect(self.choose_file)

    def set_file_filter(self, file_filter: str):
        self._file_filter = file_filter or "All Files (*)"

    def set_dialog_title(self, dialog_title: str):
        self._dialog_title = dialog_title or "Select Simulation Data File"

    def choose_file(self):
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            self._dialog_title,
            "",
            self._file_filter,
        )

        if not file_path:
            return

        self.file_selected.emit(file_path)
