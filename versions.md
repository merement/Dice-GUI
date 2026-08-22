# Versions History

## [0.1.4] - 2026-08-22
- Implemented `NdjsonParser` (`dice_gui/parsers/ndjson.py`) supporting NDJSON (JSON Lines) simulation data files (`id = "ndjson"`, `name = "NDJSON (JSON Lines)"`).
- Added "Automatic" (`auto`) option as default format selection in `FileLoaderPanel` / `MainWindow`, which automatically detects NDJSON if file starts with `{` or falls back to Raw + metadata.
- Updated main window title bar to display parser name in parentheses after filename (e.g. `simulation.ndjson (NDJSON (JSON Lines))`).
- Documented NDJSON format support in `docs/features.md` and `README.md`.

## [0.1.3] - 2026-08-21
- Refactored `history_window` to `trace_window`, updating classes (`TraceWindow`, `TracePlotWidget`), attributes, and test suite.
- Feature 1: Replaced playback control button text labels with vector SVG icons (`triangle-right.svg`, `pause.svg`, `step-right.svg`, `step-left.svg`) and tooltips.
- Feature 2: Replaced `"More..."` text button in `MetadataPanel` with `arrow-bold-filled-right.svg` icon and tooltip `"Show full set of metadata records"`.
- Feature 3: Replaced single `Trace` button in `PointInfoPanel` with 3 icon buttons (Trace, Mean value, Close all). Implemented `Mean Value Trace` window plotting average X coordinates across selected nodes. Added Close All Tracing Windows action.
- Feature 4: Implemented `Ctrl+C` shortcut on `PointInfoPanel` table to copy selected rows formatted as tab-separated fields per line with the `Id` (label) cell in double quotes.

## [0.1.2] - 2026-08-12
- Updated `MainWindow` window title to display the open simulation file name (basename).
- Added `file name` record (with full file path) as the first record displayed in the "Metadata Overview" window (`MetadataDialog`).

## [0.1.1] - 2026-08-12
- Fixed 0-based node index leaking into GUI display components (`PointInfoPanel`, `HistoryWindow`, status bar selection messages) by respecting `node_indexing` base (defaulting to 1).
- Updated `MetadataPanel.set_metadata` to default `base` display label to `1` when omitted or `None` in loaded metadata.
