#!/usr/bin/env python

import sys

import circle_model
import data_processing

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import Qt, QTimer


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Spin Reader")
        self.setGeometry(100, 100, 1300, 700)

        if len(sys.argv) != 1:
            print("Ising machine GUI\n")
            print("Usage: python main.py")
            sys.exit(1)

        self.simulation_data = None

        self.main_layout = QVBoxLayout()
        self.top_bar_layout = QHBoxLayout()

        self.circle_model = circle_model.CircleModel(self)
        self.data_processing = data_processing.DataProcessing()
        self.data_processing.data_loaded.connect(self.on_data_loaded)

        self.time_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.time_label = QLabel("0.000", self)

        self.ProgressButton = QPushButton("Increase Time", self)
        self.ProgressButton.clicked.connect(self.Progress)

        self.RegressButton = QPushButton("Decrease Time", self)
        self.RegressButton.clicked.connect(self.Regress)

        self.PlayPauseButton = QPushButton("Play", self)
        self.PlayPauseButton.clicked.connect(self.PlayPauseControl)

        self.ProgressButton.setEnabled(False)
        self.RegressButton.setEnabled(False)
        self.PlayPauseButton.setEnabled(False)
        self.time_slider.setEnabled(False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.Progress)

        self.setLayout(self.main_layout)
        self.initUI()

    def initUI(self):
        timeslider_layout = QHBoxLayout()
        timeslider_layout.addWidget(QLabel("Time:"))
        timeslider_layout.addWidget(self.time_slider)
        timeslider_layout.addWidget(self.time_label)

        timebutton_layout = QHBoxLayout()
        timebutton_layout.addWidget(self.RegressButton)
        timebutton_layout.addWidget(self.PlayPauseButton)
        timebutton_layout.addWidget(self.ProgressButton)

        left_controls_layout = QVBoxLayout()
        left_controls_layout.addLayout(timeslider_layout)
        left_controls_layout.addLayout(timebutton_layout)

        self.top_bar_layout.addLayout(left_controls_layout)
        self.top_bar_layout.addStretch(1)

        self.main_layout.addLayout(self.top_bar_layout)
        self.main_layout.addWidget(self.circle_model)
        self.main_layout.addWidget(self.data_processing)

        self.time_slider.setMinimum(0)
        self.time_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.time_slider.valueChanged.connect(self.update_time)

    def on_data_loaded(self, data):
        self.simulation_data = data
        self.setup_time_slider()

    def Progress(self):
        if self.time_slider.value() < self.time_slider.maximum():
            self.time_slider.setValue(self.time_slider.value() + 1)
        else:
            # Optional: stop at the end.
            if self.PlayPauseButton.text() == "Pause":
                self.PlayPauseControl()

    def Regress(self):
        if self.time_slider.value() > self.time_slider.minimum():
            self.time_slider.setValue(self.time_slider.value() - 1)

    def setup_time_slider(self):
        if self.simulation_data is not None and self.simulation_data.num_frames > 0:
            self.ProgressButton.setEnabled(True)
            self.RegressButton.setEnabled(True)
            self.PlayPauseButton.setEnabled(True)
            self.time_slider.setEnabled(True)

            self.time_slider.setTracking(True)

            max_time_index = self.simulation_data.num_frames - 1
            self.time_slider.setMaximum(max_time_index)
            self.time_slider.setValue(0)

            self.update_time(0)
        else:
            self.time_slider.setEnabled(False)
            self.ProgressButton.setEnabled(False)
            self.RegressButton.setEnabled(False)
            self.PlayPauseButton.setEnabled(False)

    def update_time(self, time_index):
        if self.simulation_data is None:
            return

        frame = self.simulation_data.frame(time_index)
        self.time_label.setText(f"{frame.time_value:.3f}")
        self.circle_model.set_frame(frame)

    def PlayPauseControl(self):
        if self.PlayPauseButton.text() == "Play":
            self.PlayPauseButton.setText("Pause")
            self.timer.start(100)
        else:
            self.PlayPauseButton.setText("Play")
            self.timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())

    
