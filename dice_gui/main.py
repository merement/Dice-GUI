# dice_gui/main.py
# command-line argument parsing
# (TODO) reading configuration file
# QApplication setup
# creates MainWindow

import argparse
import sys

from PyQt6.QtWidgets import QApplication

# from dice_gui import parsers
from dice_gui.loading import create_default_parser_registry
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

    parser.add_argument(
        "--parser",
        default="raw",
        help="Parser ID to use for the input file.",
    )

    parser.add_argument(
        "--list-parsers",
        action="store_true",
        help="List available parser IDs and exit.",
    )

    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    parser_registry = create_default_parser_registry()

    # Later:
    # discover_parser_plugins(parser_registry)
    #
    if args.list_parsers:
        print("Available parsers:")
        for parser in parser_registry.parsers():
            print(f"  {parser.id}\t{parser.name}")
        return 0

    if args.parser is not None and args.parser not in parser_registry:
        print(f"Unknown parser ID: {args.parser!r}", file=sys.stderr)
        print("Use --list-parsers to see available parsers.", file=sys.stderr)
        return 2

    parser_id = (
        args.parser if args.parser is not None else parser_registry.default_parser_id
    )
    qt_app = QApplication(sys.argv)

    window = MainWindow(
        parser_registry=parser_registry,
        initial_file=args.file,
        initial_parser_id=parser_id,
    )
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
