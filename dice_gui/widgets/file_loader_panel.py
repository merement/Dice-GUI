# dice_gui/widgets/file_loader_panel.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal

from dice_gui.parsers import TimeSpinXParser, ParseError
from dice_gui.domain import SimulationData


class FileLoaderPanel(QWidget):
    data_loaded = pyqtSignal(object)  # emits SimulationData

    def __init__(self):
        super().__init__()

        self.read_button = QPushButton("Read .dat File", self)
        self.parser = TimeSpinXParser()

        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout()
        self.read_button.clicked.connect(self.choose_model_file)
        layout.addWidget(self.read_button)
        self.setLayout(layout)

    def choose_model_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Data File",
            "",
            "Text Files (*.dat *.txt);;All Files (*)",
        )

        if not file_path:
            return

        try:
            data = self.parser.parse_file(file_path)
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "File Not Found",
                f"Could not find file:\n{file_path}",
            )
            return
        except ParseError as exc:
            QMessageBox.critical(
                self,
                "Parse Error",
                str(exc),
            )
            return
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n{exc}",
            )
            return

        self.data_loaded.emit(data)
