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

## 4. Supported Metadata Schema

The application supports embedding machine-readable JSON metadata directly within simulation data files. This metadata defines settings such as the global indexing base, custom node IDs, simulation title, notes, and timestamp.

For full schema details, parser syntax, and console stream commands, refer to the [metadata-schema.md](file:///home/misha/Documents/projects/dicing/Dice-GUI/docs/metadata-schema.md) specification.
