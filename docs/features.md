<!-- This file was generated -->
# Interactive Visualizer Features and User Guide

This document covers the advanced interaction, zooming, and metadata capabilities of the `Dice-GUI` application.

---

## 1. Node Selection and Multi-Selection

Nodes displayed on the circular coordinate space can be selected interactively using the mouse:
- **Single Node Selection**: Left-clicking directly on a node selects it and highlights it with a golden border. Clicking on empty space clears the selection.
- **Multi-Selection via Shift**:
  - **Toggle Select**: Hold **SHIFT** and click a node to add or remove it from the active selection.
  - **Shift-Drag Selection Box**: Hold **SHIFT** and left-click and drag to draw a transparent-gold rectangular selection box. Any nodes enclosed in this selection box will be added to the selection when the mouse is released.

Selecting nodes highlights them both on the circular visualization and highlights their records inside the interactive **Point Info Panel** table.

---

## 2. Coordinate Zooming (Non-Modal Views)

To inspect dense regions of nodes or coordinate intervals in detail, `Dice-GUI` supports interactive coordinate zooming:
- **Zoom Box Dragging**: Left-click and drag the mouse **without holding SHIFT**. A transparent-gold selection box is drawn over the coordinates.
- **Zoom Window Launch**: Upon releasing the mouse button, a new **non-modal window** opens. Inside this window, only the selected coordinate interval of the circle is rendered as a circular arc, scaled to fit the entire window size.
- **Recursive Zooming**: The zoomed circle view in the Zoom Window itself supports normal left-click dragging. Dragging a zoom box inside a Zoom Window will launch another, recursively nested Zoom Window showing that further magnified segment of the coordinate space.

---

## 3. Real-Time View Synchronization

All launched Zoom Windows are fully synchronized with the main application session in real-time:
- **Playback Control**: Stepping forward/backward or playing/pausing simulation animations in the main window updates the frame and time values across all open Zoom Windows simultaneously.
- **Selection Synchronization**: Selecting a node in the main window highlight-syncs it in all open Zoom Windows, and selecting a node in any Zoom Window syncs it back to the main window and the Point Info table.
- **Point ID Synchronization**: Editing custom node IDs in the Point Info table propagates the updated labels to all active circular and zoomed views.
- **Session Reset**: Loading a new simulation file automatically closes all active Zoom Windows to prevent coordinate system conflicts.

---

## 4. Point History Tracer

The Point History Tracer allows visualizing the coordinate history of selected simulation points over time in specialized, non-modal plotting windows:
- **Launching Traces**: Select one or more points in the main window or the Point Info Panel table, then click the **"Trace"** button inside the Point Info Panel.
- **Tracer Window Content**: For each tracked point, a window titled `"Point # <index>  Id: <id>"` opens, showing a plot of `Time` (horizontal axis) vs. `X` (vertical axis).
- **Dynamic X-Axis Range Scaling**: The vertical $X$ viewport is automatically centered and scaled around the coordinate range within the current time slice $[min_X - 0.05, max_X + 0.05]$ (clamped to the domain $[-1.0, 1.0]$).
- **Time-Window Bound Shifts**: The plot displays a time slice of size `2 * TIME_WINDOW` (100 frames total). If timeline progression or slider scrolling shifts the current frame outside the visible window, the bounds dynamically shift to center on the new frame.
- **Past vs. Future Color Coding**:
  - Time steps in the past (up to the current frame) are color-coded dynamically based on the particle's spin value at each frame (using the same red/blue/gray color scheme).
  - Time steps in the future (yet to be reached) are rendered in light gray.
  - A dashed vertical line marks the current playback time position.

---

## 5. Copying Table Data to Clipboard

Selected rows in the **Point Info Panel** table can be copied directly to the system clipboard:
- **Copy Shortcut**: Pressing **Ctrl+C** (or standard OS copy shortcut) while interacting with the Point Info Panel table copies all currently selected rows.
- **Tab-Separated Format**: Data is exported in tab-separated value format (`\t`), allowing seamless pasting into spreadsheet applications (such as Excel or LibreOffice Calc) or text editors.
- **Exported Fields**:
  - `#`: Displayed node index (adjusted according to the global indexing base).
  - `Id`: Node text identifier, enclosed in double quotes (e.g., `"node_A"`).
  - `Spin`: Particle spin configuration (`+1` or `-1`).
  - `X`: Floating-point coordinate value formatted to 6 decimal places.
  - `ΔX`: Coordinate step difference formatted to 6 decimal places.

---

## 6. Supported Metadata Schema

The application supports embedding machine-readable JSON metadata directly within simulation data files. This metadata defines settings such as the global indexing base, custom node IDs, simulation title, notes, and timestamp.

For full schema details, parser syntax, and console stream commands, refer to the [metadata-schema.md](file:///home/misha/Documents/projects/dicing/Dice-GUI/docs/metadata-schema.md) specification.

---

## 7. NDJSON (JSON Lines) Data Support & Automatic Format Detection

`Dice-GUI` supports simulation files formatted as NDJSON (Newline-Delimited JSON / JSON Lines):
- **NDJSON Format**: Each non-empty line in the file contains a self-contained JSON object. Sample records are designated with `"type": "sample"`, containing `"time"` and an `"r_spins"` array of `{"state": [spin, x]}` node objects. Metadata records (e.g. `"type": "node_indexing"`, `"node"`, `"title"`, `"created"`) can be freely interleaved.
- **Automatic Format Selection**: The input format selector defaults to **"Automatic"**. In this mode, `Dice-GUI` inspects the first non-whitespace character of the file:
  - If the first non-whitespace character is `{`, the **NDJSON** parser is automatically selected.
  - Otherwise, the **Raw + metadata** parser is selected.
- **Explicit Override**: Choosing a specific parser format in the dropdown menu overrides automatic detection. Drag-and-drop file imports respect the currently selected format mode.
- **Window Title Display**: The main window title bar displays the opened file name followed by the active parser name in parentheses (e.g. `simulation.ndjson (NDJSON (JSON Lines))`).

