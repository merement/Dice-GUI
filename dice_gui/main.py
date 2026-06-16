# dice_gui/main.py
# command-line argument parsing
# (TODO) reading configuration file
# QApplication setup
# creates MainWindow

import argparse
import sys

from PyQt6.QtWidgets import QApplication

from dice_gui.widgets.main_window import MainWindow


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GUI frontend for visualizing time-dependent simulation data."
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="Optional data file to open on startup.",
    )

    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])

    qt_app = QApplication(sys.argv)

    window = MainWindow(initial_file=args.file)
    window.show()

    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

# import json

# CONFIG_NAME_DEFAULT = "config.json"
# # Load the configurable parameters at runtime
# with open(CONFIG_NAME_DEFAULT, "r") as f:
#     CONFIG = json.load(f)

# COLOR_SPIN_UP = QColor(255, 0, 0)
# COLOR_SPIN_DOWN = QColor(0, 0, 255)

# COLOR_SPIN_UP = CONFIG["COLOR_SPIN_UP"]
# COLOR_SPIN_DOWN = CONFIG["COLOR_SPIN_DOWN"]
