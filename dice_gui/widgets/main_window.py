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
    QMessageBox,
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
from dice_gui.widgets.point_info_panel import PointInfoPanel
from dice_gui.widgets.metadata_panel import MetadataPanel


class MainWindow(QMainWindow):
    def __init__(
        self,
        parser_registry: ParserRegistry,
        initial_file: str | None = None,
        initial_parser_id: str = "raw",
    ):
        super().__init__()

        self.setWindowTitle("Dice GUI")
        self.resize(1100, 800)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.parser_registry = parser_registry
        self.file_load_service = FileLoadService(parser_registry)
        initial_parser_id = parser_registry.default_parser_id

        self.loaded_simulation = None
        self.selected_point_indices: set[int] = set()
        self.point_ids: list[str] = []

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

        # Metadata display panel
        self.metadata_panel = MetadataPanel(self)

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

        # Point info panel
        self.point_info_panel = PointInfoPanel(self)

    def _build_layout(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        # Top section layout holding Input and Metadata horizontally
        top_layout = QHBoxLayout()

        # ----- Input group -----
        input_group = QGroupBox("Input", self)
        input_layout = QHBoxLayout(input_group)

        input_layout.addWidget(QLabel("Format:", self))
        input_layout.addWidget(self.parser_combo_box)
        input_layout.addWidget(self.file_loader_panel)

        # Add to top horizontal layout
        top_layout.addWidget(input_group, stretch=0)
        top_layout.addWidget(self.metadata_panel, stretch=1)

        root_layout.addLayout(top_layout)

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
        right_sidebar_layout.setContentsMargins(0, 0, 0, 0)

        right_sidebar_layout.addWidget(self.point_info_panel)

        content_splitter.addWidget(self.circle_view)
        content_splitter.addWidget(right_sidebar)

        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)
        content_splitter.setSizes([760, 320])

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

        self.circle_view.selection_changed.connect(self.on_point_selection_changed)
        self.point_info_panel.point_selected.connect(
            self.on_point_selection_changed_from_table
        )
        self.point_info_panel.point_id_changed.connect(
            self.on_point_id_changed
        )

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
            QMessageBox.critical(
                self,
                "Loading Error",
                f"Failed to load simulation file:\n{file_path}\n\nReason: {e}"
            )
            return

        self.on_simulation_loaded(loaded)

    def on_simulation_loaded(self, loaded_simulation):
        self.loaded_simulation = loaded_simulation
        self.selected_point_indices = set()
        self.circle_view.clear_selection()

        # Initialize point IDs from static_data metadata or default to empty strings
        num_nodes = loaded_simulation.dynamic_data.num_nodes
        self.point_ids = [""] * num_nodes
        if (loaded_simulation.static_data is not None and 
                loaded_simulation.static_data.metadata is not None and 
                "node_ids" in loaded_simulation.static_data.metadata):
            loaded_ids = loaded_simulation.static_data.metadata["node_ids"]
            for i, p_id in enumerate(loaded_ids):
                if i < num_nodes:
                    self.point_ids[i] = str(p_id)

        self.circle_view.set_point_ids(self.point_ids)
        self.point_info_panel.clear_info("No point selected")

        self.timer.stop()
        self.play_pause_button.setText("Play")
        self.setup_time_slider()

        source = loaded_simulation.source_path
        source_str = f"Loaded: {source}" if source is not None else "Loaded simulation"

        warnings_list = []
        has_metadata = False
        if loaded_simulation.static_data is not None and loaded_simulation.static_data.metadata is not None:
            warnings_list = loaded_simulation.static_data.metadata.get("warnings", [])
            has_metadata = loaded_simulation.static_data.metadata.get("has_metadata", False)

        if warnings_list:
            self.status_bar.showMessage(f"{source_str} with {len(warnings_list)} metadata warnings")
        elif has_metadata:
            self.status_bar.showMessage(f"{source_str} (metadata loaded successfully)")
        else:
            self.status_bar.showMessage(f"{source_str} (no metadata found)")

        metadata = None
        if loaded_simulation.static_data is not None:
            metadata = loaded_simulation.static_data.metadata
        self.metadata_panel.set_metadata(metadata)

    # Example placeholder showing how metadata can be updated dynamically
    # programmatically and propagate automatically to the MetadataPanel:
    #
    # def simulate_dynamic_metadata_update(self, new_records: list[dict]):
    #     if self.loaded_simulation is None or self.loaded_simulation.static_data is None:
    #         return
    #
    #     meta = self.loaded_simulation.static_data.metadata
    #     meta["raw_records"] = new_records
    #
    #     # Extract and update standard fields
    #     for rec in new_records:
    #         r_type = rec.get("type")
    #         if r_type in ("title", "notes", "created"):
    #             meta[r_type] = rec.get("value")
    #         elif r_type == "node_indexing":
    #             meta["base"] = rec.get("base", 1)
    #
    #     # Propagate the updates to the MetadataPanel
    #     self.metadata_panel.set_metadata(meta)

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
        self._update_point_info_label()

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

    def on_point_selection_changed(self, selected_indices: set[int] | list[int] | None):
        """
        Receive selection updates from CircleView.

        MainWindow owns the app-level selected point indices because future
        widgets, such as PointInfoPanel, will also need this state.
        """
        if selected_indices is None:
            new_indices = set()
        else:
            new_indices = set(selected_indices)

        if self.selected_point_indices == new_indices:
            return

        self.selected_point_indices = new_indices
        self._update_point_info_label()

        if not new_indices:
            self.status_bar.showMessage("Point selection cleared")
        elif len(new_indices) == 1:
            self.status_bar.showMessage(f"Selected point {next(iter(new_indices))}")
        else:
            self.status_bar.showMessage(f"Selected {len(new_indices)} points")

    def _update_point_info_label(self):
        """
        Update the PointInfoPanel widget.
        """
        data = self.simulation_data
        if data is None:
            self.point_info_panel.clear_info("No simulation loaded")
            return

        time_index = self.time_slider.value()
        try:
            frame = data.frame(time_index)
        except IndexError:
            self.point_info_panel.clear_info("Invalid frame index")
            return

        next_x_values = None
        if time_index + 1 < data.num_frames:
            next_x_values = data.x_values[time_index + 1]

        self.point_info_panel.update_points(
            spins=frame.spins,
            x_values=frame.x_values,
            selected_indices=self.selected_point_indices,
            point_ids=self.point_ids,
            next_x_values=next_x_values,
        )

    def on_point_selection_changed_from_table(self, selected_indices: set[int] | list[int] | None):
        if selected_indices is None:
            new_indices = set()
        else:
            new_indices = set(selected_indices)

        if self.selected_point_indices == new_indices:
            return
        self.selected_point_indices = new_indices

        self.circle_view.blockSignals(True)
        self.circle_view.set_selected_indices(new_indices)
        self.circle_view.blockSignals(False)

        self._update_point_info_label()

        if not new_indices:
            self.status_bar.showMessage("Point selection cleared")
        elif len(new_indices) == 1:
            self.status_bar.showMessage(f"Selected point {next(iter(new_indices))}")
        else:
            self.status_bar.showMessage(f"Selected {len(new_indices)} points")

    def on_point_id_changed(self, node_index: int, new_id: str):
        if 0 <= node_index < len(self.point_ids):
            self.point_ids[node_index] = new_id
            self.circle_view.set_point_ids(self.point_ids)

    def selected_parser_id(self) -> str | None:
        if self.parser_combo_box.count() == 0:
            return None

        return self.parser_combo_box.currentData()
