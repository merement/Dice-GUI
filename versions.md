# Versions History

## [0.1.2] - 2026-08-12
- Updated `MainWindow` window title to display the open simulation file name (basename).
- Added `file name` record (with full file path) as the first record displayed in the "Metadata Overview" window (`MetadataDialog`).

## [0.1.1] - 2026-08-12
- Fixed 0-based node index leaking into GUI display components (`PointInfoPanel`, `HistoryWindow`, status bar selection messages) by respecting `node_indexing` base (defaulting to 1).
- Updated `MetadataPanel.set_metadata` to default `base` display label to `1` when omitted or `None` in loaded metadata.
