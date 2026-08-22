# Feature: support for NDJSON-based data files

Add support for data files containing information in the NDSON format by implementing and incorporating a new parser `ndjson.py` with

    id = "ndjson"
    name = "NDJSON (JSON Lines)".

Ask clarifying questions if needed. Implementation suggestions are welcome.

## Parser for the NDSON files

Content-wise, these files contain the same information as `raw_metadata` files (simulation data and supplementing metadata) with the important exception: the new files are NDJSON files with each line representing individual JSON objects. Consequently, these files do not have lines starting with "#". The format of these files follows the specification described in `docs/metadata-specification.md`. An example of the file to parse is shown in the subsection "Complete Minimal Stream (NDJSON)" of section "5. Consolidated Examples" of `docs/metadata-specification.md`.

The simulation data is represented in the JSON object with `"type": "sample"`. The field `"time"` contains the simulation time value (see the subsection "Raw data" of section "Supported Input Formats" in the project's `README.md`). The field `"r_spins"` contains an array of objects describing individual relaxed spin. The field `"state"` in these objects is a spin/coordinate pair `(s_i, x_i)`.

For example, the line

```json
{"type": "sample", "time": 0.0, "r_spins": [{"state": [1, 0.12]}, {"state": [-1, 0.44]}]}
```

describes the state of two relaxed spins at the simulation time `0.0`. The first	relaxed spin has spin `1` and coordinate `0.12`. The second relaxed spin has spin `-1` and coordinate `0.44`.

## New interface for selecting file formats

Currently the `file_loader_panel` has a selector with the states determined by the registered parsers. We need to add one more state: "Automatic" that makes a decision about the format of the input file based on its syntax. If the selector allows tooltips, add the following one

"Automatic uses NDJSON when the file begins with a JSON object; otherwise it uses Raw + metadata. Choose a specific format to disable automatic detection."

The selection follows the rule

```text
first non-whitespace character in the file == "{"
    → use ndjson parser
otherwise
    → use raw_metadata parser
```

Conceptually:

```python
def select_parser(prefix: str, requested_format: str) -> str:
    if requested_format != "auto":
        return requested_format

    if first_non_whitespace_character(prefix) == "{":
        return "ndjson"

    return "raw_metadata"
```

When the user explicitly chooses another format, the respective parser should be used without attempting to guess the actual format.

The format selected in the `file_loader_panel` also determines the parser used for intepretting files that are passed to the app through drag-and-drop. If "Automatic" is selected then the decision is made according to the rule outlined above. Otherwise, the specific selected parser will be used.

In any case, if detection fails, the error identifies both the selected mode and the parser. For example, by messaging

```text
Could not load “simulation.ndjson” as NDJSON:
```

## Providing info about the parser

Display information about used parser in the title bar of the main window. Currently, it shows only the file name. Add afterwards the parser name in parentheses.

# Documenting new parser

Add the description of the new parsers as a new section in `features.md`.

Add a section on the new parser to the section "Supported Input Formats" of the project's `README.md`.

# Versioning

Update the patch number and add the explanatory text (about the new parser) to `versions.md`. 