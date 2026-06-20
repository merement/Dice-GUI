# app/widgets/main_window.py
# GUI layout
#  connects widgets
#  manages current loaded data

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from dice_gui.loading import FileLoadService, ParserRegistry
from dice_gui.widgets.circle_view import CircleView
from dice_gui.widgets.file_loader_panel import FileLoaderPanel


class MainWindow(QMainWindow):
    def __init__(
        self,
        parser_registry: ParserRegistry,
        initial_file: str | None = None,
        initial_parser_id: str = "raw",
    ):
        super().__init__()

        self.setWindowTitle("Dice GUI")
        self.resize(1300, 800)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.parser_registry = parser_registry
        self.file_load_service = FileLoadService(parser_registry)
        if initial_parser_id is None:
            initial_parser_id = parser_registry._default_parser_id

        self.loaded_simulation = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.progress)

        self._create_widgets()
        self._build_layout()
        self._connect_signals()
        self._populate_parser_combo_box()
        self.set_controls_enabled(False)

        if initial_file is not None:
            self.load_file(initial_file, initial_parser_id)

    def _create_widgets(self):
        # Input/loading controls
        self.parser_combo_box = QComboBox(self)
        self.file_loader_panel = FileLoaderPanel()

        # Playback controls
        self.time_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.time_slider.setMinimum(0)
        self.time_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.time_label = QLabel("0.000", self)

        self.progress_button = QPushButton("Step Forward", self)
        self.regress_button = QPushButton("Step Backward", self)
        self.play_pause_button = QPushButton("Play", self)

        # Main visualization
        self.circle_view = CircleView(self)

        # Placeholder side panel for now
        self.point_info_label = QLabel("No point selected", self)
        self.point_info_label.setWordWrap(True)

    def _build_layout(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        # ----- Input group -----
        input_group = QGroupBox("Input", self)
        input_layout = QHBoxLayout(input_group)

        input_layout.addWidget(QLabel("Format:", self))
        input_layout.addWidget(self.parser_combo_box)
        input_layout.addWidget(self.file_loader_panel)
        input_layout.addStretch(1)

        # ----- Playback group -----
        playback_group = QGroupBox("Playback", self)
        playback_layout = QHBoxLayout(playback_group)

        playback_layout.addWidget(self.regress_button)
        playback_layout.addWidget(self.play_pause_button)
        playback_layout.addWidget(self.progress_button)

        playback_layout.addSpacing(16)
        playback_layout.addWidget(QLabel("Time:", self))
        playback_layout.addWidget(self.time_slider, stretch=1)
        playback_layout.addWidget(self.time_label)

        # ----- Main content splitter -----
        content_splitter = QSplitter(Qt.Orientation.Horizontal, self)

        right_sidebar = QWidget(self)
        right_sidebar_layout = QVBoxLayout(right_sidebar)

        point_group = QGroupBox("Point Info", self)
        point_layout = QVBoxLayout(point_group)
        point_layout.addWidget(self.point_info_label)

        right_sidebar_layout.addWidget(point_group)
        right_sidebar_layout.addStretch(1)

        content_splitter.addWidget(self.circle_view)
        content_splitter.addWidget(right_sidebar)

        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)
        content_splitter.setSizes([950, 250])

        root_layout.addWidget(input_group)
        root_layout.addWidget(playback_group)
        root_layout.addWidget(content_splitter, stretch=1)

        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        self.file_loader_panel.file_selected.connect(self.load_selected_file)

        self.parser_combo_box.currentIndexChanged.connect(
            self._update_file_loader_filter
        )

        self.time_slider.valueChanged.connect(self.update_time)

        self.progress_button.clicked.connect(self.progress)
        self.regress_button.clicked.connect(self.regress)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

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

    def selected_parser(self) -> str | None:
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

    def load_file(self, file_path: str, parser_id: str | None = None):
        try:
            loaded = self.file_load_service.load_file(
                file_path=file_path,
                parser_id=parser_id,
            )
        except Exception as e:
            self.status_bar.showMessage(f"Error loading file: {e}")
            # Later: use QMessageBox here.
            return

        self.on_simulation_loaded(loaded)

    def on_simulation_loaded(self, loaded_simulation):
        self.loaded_simulation = loaded_simulation
        self.timer.stop()
        self.play_pause_button.setText("Play")
        self.setup_time_slider()

        source = loaded_simulation.source_path
        if source is not None:
            self.status_bar.showMessage(f"Loaded: {source}")
        else:
            self.status_bar.showMessage("Loaded simulation")

    @property
    def simulation_data(self):
        if self.loaded_simulation is None:
            return None
        return self.loaded_simulation.dynamic_data

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

    def selected_parser_id(self) -> str | None:
        if self.parser_combo_box.count() == 0:
            return None

        return self.parser_combo_box.currentData()
