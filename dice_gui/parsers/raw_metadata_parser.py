# dice_gui/parsers/raw_metadata_parser.py
#
# Implements a metadata-aware parser for DICE/Ising-type simulation data.
# It parses JSON-formatted metadata in `#@`-prefixed comment lines,
# while reading raw time/spin/x values from data lines.

import json
import logging
import warnings as py_warnings
from pathlib import Path
import numpy as np

from dice_gui.domain import (
    LoadedSimulation,
    TimeSeriesData,
    StaticSimulationData,
)
from .base import ParseError

logger = logging.getLogger(__name__)


class RawMetadataParser:
    """
    Parses time-dependent simulation files containing `#@` metadata comment records
    and raw numeric data rows.
    """

    id = "raw-metadata"
    name = "Raw data with metadata"
    file_dialog_filter = "Raw data with metadata (*.dat *.txt)"

    def __init__(self, strict: bool = False):
        self.strict = strict

    def parse_raw_file(self, file_path: str | Path) -> LoadedSimulation:
        file_path = Path(file_path)

        times: list[float] = []
        all_spins: list[list[int]] = []
        all_x_values: list[list[float]] = []

        base_index = None
        base_index_resolved = False
        node_names: dict[int, str] = {}
        warnings: list[str] = []
        has_metadata = False
        raw_records = []

        title = None
        notes = None
        created = None

        expected_num_nodes: int | None = None

        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()

                if not stripped:
                    continue

                # Check for metadata line
                if stripped.startswith("#@"):
                    has_metadata = True
                    json_str = stripped[2:].strip()
                    try:
                        record = json.loads(json_str)
                    except json.JSONDecodeError as exc:
                        warn_msg = f"Line {line_number}: Invalid JSON metadata: {exc}"
                        logger.warning(warn_msg)
                        warnings.append(warn_msg)
                        continue

                    if not isinstance(record, dict):
                        warn_msg = f"Line {line_number}: Metadata record is not a JSON object"
                        logger.warning(warn_msg)
                        warnings.append(warn_msg)
                        continue

                    rec_type = record.get("type")
                    if not rec_type:
                        warn_msg = f"Line {line_number}: Metadata record missing 'type' field"
                        logger.warning(warn_msg)
                        warnings.append(warn_msg)
                        continue

                    if rec_type != "node":
                        raw_records.append(record)

                    if rec_type == "format":
                        # Ignored or checked in later phases
                        continue

                    elif rec_type == "node_indexing":
                        base_val = record.get("base")
                        if base_val is None or base_val not in (0, 1):
                            warn_msg = f"Line {line_number}: Invalid index base {base_val!r}, defaulting to 1"
                            logger.warning(warn_msg)
                            warnings.append(warn_msg)
                            resolved_base = 1
                        else:
                            resolved_base = int(base_val)

                        if base_index is not None:
                            warn_msg = f"Line {line_number}: Indexing base redefined, ignoring"
                            logger.warning(warn_msg)
                            warnings.append(warn_msg)
                        elif node_names:
                            warn_msg = f"Line {line_number}: Indexing base defined after node records, ignoring"
                            logger.warning(warn_msg)
                            warnings.append(warn_msg)
                        else:
                            base_index = resolved_base
                            base_index_resolved = True

                    elif rec_type == "node":
                        if base_index is None:
                            base_index = 1  # default base
                            base_index_resolved = True

                        raw_idx = record.get("index")
                        name_val = record.get("name")

                        if raw_idx is None or not isinstance(raw_idx, (int, float)) or isinstance(raw_idx, bool):
                            warn_msg = f"Line {line_number}: Node record missing or invalid 'index' field"
                            logger.warning(warn_msg)
                            warnings.append(warn_msg)
                            continue

                        if name_val is None:
                            warn_msg = f"Line {line_number}: Node record missing 'name' field"
                            logger.warning(warn_msg)
                            warnings.append(warn_msg)
                            continue

                        idx = int(raw_idx)
                        python_index = idx - base_index
                        if python_index < 0:
                            warn_msg = f"Line {line_number}: Node index {idx} is invalid for base {base_index}"
                            logger.warning(warn_msg)
                            warnings.append(warn_msg)
                            continue

                        node_names[python_index] = str(name_val)

                    elif rec_type in ("created", "title", "notes"):
                        val = record.get("value")
                        if val is None:
                            warn_msg = f"Line {line_number}: Metadata record type {rec_type!r} missing 'value' field"
                            logger.warning(warn_msg)
                            warnings.append(warn_msg)
                            continue

                        if rec_type == "created":
                            created = str(val)
                        elif rec_type == "title":
                            title = str(val)
                        elif rec_type == "notes":
                            notes = str(val)

                    else:
                        # Ignore unknown record types in permissive mode
                        continue

                elif stripped.startswith("#"):
                    # Regular comment, ignore
                    continue

                else:
                    # Data line
                    values = stripped.split()
                    if len(values) < 3:
                        raise ParseError(
                            f"Line {line_number}: expected at least one time value "
                            f"and one spin/x pair."
                        )

                    try:
                        time_value = float(values[0])
                    except ValueError as exc:
                        raise ParseError(
                            f"Line {line_number}: invalid time value {values[0]!r}."
                        ) from exc

                    data_values = values[1:]
                    if len(data_values) % 2 != 0:
                        raise ParseError(
                            f"Line {line_number}: expected an even number of spin/x values "
                            f"after the time column, got {len(data_values)}."
                        )

                    num_nodes = len(data_values) // 2
                    if expected_num_nodes is None:
                        expected_num_nodes = num_nodes
                    elif num_nodes != expected_num_nodes:
                        raise ParseError(
                            f"Line {line_number}: expected {expected_num_nodes} nodes, "
                            f"got {num_nodes}."
                        )

                    spins: list[int] = []
                    x_values: list[float] = []

                    for i in range(0, len(data_values), 2):
                        raw_spin = data_values[i]
                        raw_x = data_values[i + 1]

                        try:
                            spin = int(raw_spin)
                        except ValueError as exc:
                            raise ParseError(
                                f"Line {line_number}: invalid spin value {raw_spin!r}."
                            ) from exc

                        if spin not in {-1, 1}:
                            raise ParseError(
                                f"Line {line_number}: spin must be -1 or 1, got {spin}."
                            )

                        try:
                            x = float(raw_x)
                        except ValueError as exc:
                            raise ParseError(
                                f"Line {line_number}: invalid x value {raw_x!r}."
                            ) from exc

                        if not -1.0 <= x <= 1.0:
                            raise ParseError(
                                f"Line {line_number}: x must be in [-1, 1], got {x}."
                            )

                        spins.append(spin)
                        x_values.append(x)

                    times.append(time_value)
                    all_spins.append(spins)
                    all_x_values.append(x_values)

        if not times:
            raise ParseError(f"File {file_path} contains no data.")

        # Compute indexing base if not resolved
        final_base = base_index if base_index is not None else 1

        # Post-parse: validate and construct node ID list
        num_nodes = expected_num_nodes if expected_num_nodes is not None else 0
        node_ids = [""] * num_nodes

        for py_idx, name in node_names.items():
            if 0 <= py_idx < num_nodes:
                node_ids[py_idx] = name
            else:
                warn_msg = (
                    f"Node index {py_idx + final_base} (calculated from index {py_idx + final_base} "
                    f"and base {final_base}) is out of bounds for simulation containing {num_nodes} nodes"
                )
                logger.warning(warn_msg)
                warnings.append(warn_msg)

        static_metadata = {
            "node_ids": node_ids,
            "warnings": warnings,
            "has_metadata": has_metadata,
            "base": final_base,
            "raw_records": raw_records,
        }
        if title is not None:
            static_metadata["title"] = title
        if notes is not None:
            static_metadata["notes"] = notes
        if created is not None:
            static_metadata["created"] = created

        static_data = StaticSimulationData(metadata=static_metadata)

        return LoadedSimulation(
            dynamic_data=TimeSeriesData(
                times=np.array(times, dtype=float),
                spins=np.array(all_spins, dtype=np.int8),
                x_values=np.array(all_x_values, dtype=float),
            ),
            static_data=static_data,
        )
