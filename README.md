# Dice-GUI

A PyQt6-based graphical frontend for visualizing time-dependent simulation data from DICE/Ising-type simulations.

The application is intended to display dynamic variables living on a circular coordinate, evolving over simulation time. The current focus is file-based visualization; future versions are expected to support streaming data from simulation backends.

## Project Status

This project is currently in early development.

The initial proof-of-concept demonstrated the usefulness of the visualization and helped identify desired functionality. The current development effort is focused on improving the architecture so that the application can support:

- multiple input data formats (supported through parser plugins),
- interactive point selection,
- zooming and filtering,
- plotting selected point histories,
- optional static simulation metadata,
- communication with live simulation backends.

## What the Application Visualizes

The dynamic simulation data at each time step consists of an array of pairs:

```text
(s, X)
```

where:

```text
s ∈ {-1, 1}
X ∈ [-1, 1]
```

The endpoints of the `X` interval are identified, so `X` is naturally represented as a coordinate on a circle.

The current visualization displays each pair as a small circle positioned according to `X`, with color determined by `s`.

For example:

- `s = 1` may be shown in red,
- `s = -1` may be shown in blue.

Future visualization options may include arrows or combined color/arrow rendering.

## Supported Input Formats

### Raw data

The parser expects a text file where each line corresponds to one time step.

Each line has the format:

```text
time spin_0 x_0 spin_1 x_1 spin_2 x_2 ...
```

Example:

```text
0.000 1 0.011 1 0.305 -1 -0.357
0.010 1 0.015 -1 0.301 -1 -0.360
0.020 -1 0.020 -1 0.299 1 -0.365
```

The first value is the simulation time.

The remaining values are spin/coordinate pairs: `(s_i, x_i)`.

Lines starting with `#` are ignored (can be used for comments or metadata).


## Planned Features

Planned or desired functionality includes:

- [x] File-based loading of dynamic simulation data.
- [x] Time slider for moving through frames.
- [x] Play/pause animation.
- [x] Circular visualization of dynamic variables.
- [x] Parser abstraction for multiple file formats (registry & load service).
- [ ] Parser plugin support.
- [x] Point selection by mouse.
- [x] Point selection by index (implemented via interactive point list table).
- [x] Display of selected point state (time, index, spin, X coordinate, and ID).
- [ ] Zooming into a region of the circle.
- [ ] Hiding selected points.
- [x] Showing only selected points (implemented via "Show selected" table filter).
- [ ] Plotting selected point histories over time.
- [ ] Optional static graph/simulation metadata support.
- [ ] Backend streaming mode.
- [ ] Backend feedback/control messages.


## Installation

### 1. Clone the repository

```bash
git clone https://github.com/merement/Dice-GUI
cd Dice-GUI
```

### 2. Create a project-specific virtual environment

On Linux/macOS:

```bash
python3 -m venv .venv
```

A project-specific virtual environment is recommended. `.gitignore` contains a "default" location for the environment to prevent committing it.

```gitignore
.venv/
...
```

To activate the envirnoment, for `fish` shell:

```fish
source .venv/bin/activate.fish
```

For `bash` or `zsh`:

```bash
source .venv/bin/activate
```

### 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 4. Install dependencies

At the current development stage:

```bash
python -m pip install PyQt6 numpy
```

Additional dependencies may be added later, for example:

```bash
python -m pip install pyqtgraph pytest
```

Eventually this project may provide a `pyproject.toml` with installable dependencies.

## Running the Application

During development, run:

```bash
python -m dice_gui.main
```

or, depending on the current layout:

```bash
python dice_gui/main.py
```

If command-line file loading is enabled, the application may support direct loading the data file directly:

```bash
python -m dice_gui.main path/to/data.dat
```

## Testing

The project has a comprehensive test suite using `pytest`. The tests cover domain model validation, parser registration, simulation data parsing, and interactive widget behaviors.

To run all tests, activate the virtual environment and run `pytest`, or execute it directly via the virtual environment's python:

```bash
.venv/bin/python -m pytest
```

### Test Coverage

- **Domain Model**: Boundary checks, coordinate constraints ($X \in [-1, 1]$), spin values ($\sigma \in \{-1, 1\}$), node count consistency, and frame extraction.
- **Loading Service**: Registry registration, parser lookup, fallback behaviors, and load error scenarios.
- **Parsers**: Parsing of raw simulation files, comment and whitespace skipping, and error handling for malformed data formats.
- **Widgets**: UI layout rendering, interactive table updates, custom point ID editing, multi-selection synchronization, and `CircleView` geometry/selection behavior.

## Roadmap

Phase 0: Preparatory Phase (Completed)
- File-based loading, circular rendering, time slider, play/pause stepping.
- Registry-based parser loading.
- Mouse-based point selection.

Phase 1: Robustness & Verification (Completed)
- Packaging and dependencies setup (`pyproject.toml`).
- Domain validation boundary checks.
- Comprehensive unit testing suite (`test_domain`, `test_parsers`, `test_loading`).
- UI component modularization (custom `PointInfoPanel` widget).
- Visual warning dialogs for file load failures (`QMessageBox`).

Phase 2: Medium-Term Features (Feature Expansion)
1. Point selection by index.
2. Zooming and filtering (hiding/showing selected points).
3. Historical selected point plotting (using `pyqtgraph` or `matplotlib`).
4. Support for multiple text-based/structured data formats (JSON/YAML).

Phase 3: Long-Term Integration
1. Plugin infrastructure for external parsers.
2. Support for static graph topologies and simulation parameter metadata.
3. Backend live streaming mode (WebSockets/IPC).
4. Simulation feedback and control signaling.
5. Integration with workflow patterns in the Julia `Dice` library.

## Acknowledgments

This project builds on the proof-of-concept work from

- [dice-stack-GUI](https://github.com/gtsanyal/dice-stack-GUI)

- Displaying labels near selected nodes on the circle was suggested and tested in [logic](https://github.com/YilunUMichChen/logic).

Related simulation-side development and software references are collected in the Julia library:

- [Dice](https://github.com/merement/Dice)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
