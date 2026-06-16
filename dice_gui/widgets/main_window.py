# app/widgets/main_window.py
# GUI layout
#  connects widgets
#  manages current loaded data

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer

from widgets.circle_view import CircleView
from widgets.file_loader_panel import FileLoaderPanel
from parsers import TimeSpinXParser, ParseError


class MainWindow(QWidget):
    def __init__(self, initial_file: str | None = None):
        super().__init__()

        self.setWindowTitle("Spin Reader")
        self.setGeometry(100, 100, 1300, 700)

        self.simulation_data = None

        self.parser = TimeSpinXParser()

        self.main_layout = QVBoxLayout()
        self.top_bar_layout = QHBoxLayout()

        self.circle_view = CircleView(self)
        self.file_loader_panel = FileLoaderPanel()
        self.file_loader_panel.data_loaded.connect(self.on_data_loaded)

        self.time_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.time_label = QLabel("0.000", self)

        self.progress_button = QPushButton("Increase Time", self)
        self.progress_button.clicked.connect(self.progress)

        self.regress_button = QPushButton("Decrease Time", self)
        self.regress_button.clicked.connect(self.regress)

        self.play_pause_button = QPushButton("Play", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.progress)

        self.setLayout(self.main_layout)
        self.init_ui()
        self.set_controls_enabled(False)

        if initial_file is not None:
            self.load_file(initial_file)

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

    def load_file(self, file_path: str):
        data = self.parser.parse_file(file_path)
        self.on_data_loaded(data)

    def on_data_loaded(self, data):
        self.simulation_data = data
        self.setup_time_slider()

    def set_controls_enabled(self, enabled: bool):
        self.progress_button.setEnabled(enabled)
        self.regress_button.setEnabled(enabled)
        self.play_pause_button.setEnabled(enabled)
        self.time_slider.setEnabled(enabled)

    def setup_time_slider(self):
        if self.simulation_data is None or self.simulation_data.num_frames == 0:
            self.set_controls_enabled(False)
            return

        self.set_controls_enabled(True)

        self.time_slider.setTracking(True)
        self.time_slider.setMaximum(self.simulation_data.num_frames - 1)
        self.time_slider.setValue(0)
        self.update_time(0)

    def update_time(self, time_index: int):
        if self.simulation_data is None:
            return

        frame = self.simulation_data.frame(time_index)
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
