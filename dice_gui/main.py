# app/main.py
# command-line argument parsing
# QApplication setup
# creates MainWindow

import sys
import argparse

from PyQt6.QtWidgets import QApplication

from widgets.main_window import MainWindow


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
