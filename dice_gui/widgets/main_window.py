# app/widgets/main_window.py
# GUI layout
#  connects widgets
#  manages current loaded data

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from dice_gui.loading import FileLoadService, ParserRegistry
from dice_gui.widgets.circle_view import CircleView
from dice_gui.widgets.file_loader_panel import FileLoaderPanel


class MainWindow(QWidget):
    def __init__(
        self,
        parser_registry: ParserRegistry,
        initial_file: str | None = None,
        initial_parser_id: str = "raw",
    ):
        super().__init__()

        self.loaded_simulation = None

        self.parser_registry = parser_registry
        self.file_load_service = FileLoadService(parser_registry)
        if initial_parser_id is None:
            initial_parser_id = parser_registry._default_parser_id

        self.file_loader_panel = FileLoaderPanel(self)
        self.file_loader_panel.file_selected.connect(self.load_selected_file)

        self.setWindowTitle("Dice GUI")
        self.setGeometry(100, 100, 1300, 700)

        self.main_layout = QVBoxLayout()
        self.top_bar_layout = QHBoxLayout()

        self.circle_view = CircleView(self)

        self.parser_combo_box = QComboBox(self)
        self._populate_parser_combo_box()
        self.parser_combo_box.currentIndexChanged.connect(
            self._update_file_loader_filter
        )

        self.file_loader_panel = FileLoaderPanel()
        self.file_loader_panel.file_selected.connect(self.load_file)

        self.time_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.time_label = QLabel("0.000", self)

        self.progress_button = QPushButton("Step Forward", self)
        self.progress_button.clicked.connect(self.progress)

        self.regress_button = QPushButton("Step Backward", self)
        self.regress_button.clicked.connect(self.regress)

        self.play_pause_button = QPushButton("Play", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.progress)

        self.setLayout(self.main_layout)
        self.init_ui()
        self.set_controls_enabled(False)

        if initial_file is not None:
            self.load_file(initial_file, initial_parser_id)

    @property
    def simulation_data(self):
        if self.loaded_simulation is None:
            return None
        return self.loaded_simulation.dynamic_data

    def init_ui(self):
        timeslider_layout = QHBoxLayout()
        timeslider_layout.addWidget(QLabel("Time:"))
        timeslider_layout.addWidget(self.time_slider)
        timeslider_layout.addWidget(self.time_label)

        timebutton_layout = QHBoxLayout()
        timebutton_layout.addWidget(self.regress_button)
        timebutton_layout.addWidget(self.play_pause_button)
        timebutton_layout.addWidget(self.progress_button)

        left_controls_layout = QVBoxLayout()
        left_controls_layout.addLayout(timeslider_layout)
        left_controls_layout.addLayout(timebutton_layout)

        self.top_bar_layout.addLayout(left_controls_layout)
        self.top_bar_layout.addStretch(1)

        self.main_layout.addLayout(self.top_bar_layout)
        self.main_layout.addWidget(self.circle_view)
        self.main_layout.addWidget(self.file_loader_panel)

        self.time_slider.setMinimum(0)
        self.time_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.time_slider.valueChanged.connect(self.update_time)

    def load_file(self, file_path: str, parser_id: str | None = None):
        loaded_simulation = self.file_load_service.load_file(
            file_path=file_path,
            parser_id=parser_id,
        )

        self.on_simulation_loaded(loaded_simulation)

        self.setWindowTitle(f"Dice GUI - {file_path}")

    def _populate_parser_combo_box(self):
        self.parser_combo_box.clear()

        for parser in self.parser_registry.parsers():
            self.parser_combo_box.addItem(parser.name, parser.id)

        default_index = self.parser_combo_box.findData(
            self.parser_registry.default_parser_id
        )

        if default_index >= 0:
            self.parser_combo_box.setCurrentIndex(default_index)

        self._update_file_loader_filter()

    def selected_parser_id(self) -> str | None:
        if self.parser_combo_box.count() == 0:
            return None

        return self.parser_combo_box.currentData()

    def selected_parser(self):
        parser_id = self.selected_parser_id()

        if parser_id is None:
            return None

        return self.parser_registry.get(parser_id)

    def _update_file_loader_filter(self):
        parser = self.selected_parser()

        if parser is None:
            self.file_loader_panel.set_file_filter("All Files (*)")
            return

        file_filter = getattr(parser, "file_filter", "All Files (*)")

        if "All Files (*)" not in file_filter:
            file_filter = f"{file_filter};;All Files (*)"

        self.file_loader_panel.set_file_filter(file_filter)

    def load_selected_file(self, file_path: str):
        self.load_file(
            file_path=file_path,
            parser_id=self.selected_parser_id(),
        )

    def on_simulation_loaded(self, loaded_simulation):
        self.loaded_simulation = loaded_simulation
        self.setup_time_slider()

    def set_controls_enabled(self, enabled: bool):
        self.progress_button.setEnabled(enabled)
        self.regress_button.setEnabled(enabled)
        self.play_pause_button.setEnabled(enabled)
        self.time_slider.setEnabled(enabled)

    def setup_time_slider(self):
        data = self.simulation_data
        if data is None or data.num_frames == 0:
            self.set_controls_enabled(False)
            return

        self.set_controls_enabled(True)

        self.time_slider.setTracking(True)
        self.time_slider.setMaximum(data.num_frames - 1)
        self.time_slider.setValue(0)
        self.update_time(0)

    def update_time(self, time_index: int):
        data = self.simulation_data
        if data is None:
            return

        frame = data.frame(time_index)
        self.time_label.setText(f"{frame.time_value:.3f}")
        self.circle_view.set_frame(frame)

    def progress(self):
        if self.time_slider.value() < self.time_slider.maximum():
            self.time_slider.setValue(self.time_slider.value() + 1)
        else:
            if self.play_pause_button.text() == "Pause":
                self.toggle_play_pause()

    def regress(self):
        if self.time_slider.value() > self.time_slider.minimum():
            self.time_slider.setValue(self.time_slider.value() - 1)

    def toggle_play_pause(self):
        if self.play_pause_button.text() == "Play":
            self.play_pause_button.setText("Pause")
            self.timer.start(100)
        else:
            self.play_pause_button.setText("Play")
            self.timer.stop()
