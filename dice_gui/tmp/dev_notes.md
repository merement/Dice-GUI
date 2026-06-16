# Development Notes

## Tentative Project Structure

The project is being refactored toward a structure like:

```text
Dice-GUI/
  README.md
  pyproject.toml
  .gitignore

  dice_gui/
    __init__.py
    main.py
    domain.py
    parsers.py

    widgets/
      __init__.py
      main_window.py
      circle_view.py
      file_loader_panel.py

    plugins/
      __init__.py

  tests/
    test_parsers.py
```

The intended responsibilities are:

```text
dice_gui/main.py
  Application entry point.
  Handles command-line arguments and starts QApplication.

dice_gui/widgets/main_window.py
  Main application window.
  Assembles GUI widgets and connects signals.

dice_gui/widgets/circle_view.py
  Custom PyQt6 widget for drawing the circular visualization.

dice_gui/widgets/file_loader_panel.py
  File-loading UI panel.

dice_gui/domain.py
  Core data structures such as SimulationData and DynamicFrame.

dice_gui/parsers.py
  File parsers for supported input formats.

dice_gui/plugins/
  Future parser/backend/plugin infrastructure.
```
### Code Style

The project aims to use conventional Python naming:

```python
snake_case_for_functions
snake_case_for_variables
PascalCaseForClasses
```

For PyQt6 widgets, class names should describe their GUI role, for example:

```python
CircleView
FileLoaderPanel
MainWindow
PlaybackControls
PointInfoPanel
```

### Architectural Direction

The GUI should avoid tightly coupling the visualization widget to the file format or backend.

The desired data flow is:

```text
data source → parser/adapter → domain model → playback/controller → widgets
```

For example:

```text
file → parser → SimulationData → DynamicFrame → CircleView
```

Future backend streaming should follow the same conceptual path:

```text
backend stream → adapter → DynamicFrame → CircleView
```

This keeps the visualization independent of whether data comes from a file, a mock source, or a live backend.
