# dice_gui/parsers/ndjson.py
#
# Implements a parser for NDJSON (JSON Lines) simulation data files.
# Each non-empty line in an NDJSON file is a valid JSON object.
# Rows with "type": "sample" contain frame data (time, relaxed spins).
# All other JSON objects are processed as metadata records.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from dice_gui.domain import (
    LoadedSimulation,
    StaticSimulationData,
    TimeSeriesData,
)
from dice_gui.jsondata import JsonMetadataProcessor, MetadataContext
from dice_gui.parsers import ParseError

logger = logging.getLogger(__name__)


class NdjsonParser:
    """
    Parses NDJSON (JSON Lines) simulation files containing sample data records
    and embedded JSON metadata records.
    """

    id = "ndjson"
    name = "NDJSON (JSON Lines)"
    file_dialog_filter = "NDJSON Files (*.ndjson *.jsonl *.json)"

    def __init__(self, strict: bool = False):
        self.strict = strict

    def parse_file(self, file_path: str | Path) -> LoadedSimulation:
        return self._parse_ndjson_file(file_path)

    def parse_raw_file(self, file_path: str | Path) -> LoadedSimulation:
        """Alias for parse_file for compatibility with FileLoadService."""
        return self._parse_ndjson_file(file_path)

    def _parse_ndjson_file(self, file_path: str | Path) -> LoadedSimulation:
        path = Path(file_path)

        times: list[float] = []
        all_spins: list[list[int]] = []
        all_x_values: list[list[float]] = []

        active_num_nodes: int | None = None

        metadata_processor = JsonMetadataProcessor(strict=self.strict)
        data_warnings: list[str] = []

        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()

                if not stripped:
                    continue

                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    self._warning_or_raise(
                        f"File {path}, Line {line_number}: Invalid JSON line: {exc}",
                        data_warnings,
                    )
                    continue

                if not isinstance(record, dict):
                    self._warning_or_raise(
                        f"File {path}, Line {line_number}: Expected JSON object, "
                        f"got {type(record).__name__}; row ignored.",
                        data_warnings,
                    )
                    continue

                record_type = record.get("type")
                if record_type == "sample":
                    parsed_sample = self._parse_sample_record(
                        record,
                        source=str(path),
                        line_number=line_number,
                        active_num_nodes=active_num_nodes,
                        data_warnings=data_warnings,
                    )

                    if parsed_sample is None:
                        continue

                    time_val, spins, x_vals = parsed_sample

                    if active_num_nodes is None:
                        active_num_nodes = len(spins)

                    times.append(time_val)
                    all_spins.append(spins)
                    all_x_values.append(x_vals)
                else:
                    metadata_processor.process_record(
                        record,
                        context=MetadataContext(
                            source=str(path),
                            line_number=line_number,
                        ),
                    )

        if not times:
            raise ParseError(f"File {path} contains no usable sample data.")

        num_nodes = active_num_nodes if active_num_nodes is not None else 0

        static_metadata = metadata_processor.build_static_metadata(
            num_nodes=num_nodes,
        )

        if data_warnings:
            static_metadata.setdefault("warnings", []).extend(data_warnings)
            static_metadata.setdefault("data_warnings", []).extend(data_warnings)

        return LoadedSimulation(
            dynamic_data=TimeSeriesData(
                times=np.array(times, dtype=float),
                spins=np.array(all_spins, dtype=np.int8),
                x_values=np.array(all_x_values, dtype=float),
            ),
            static_data=StaticSimulationData(metadata=static_metadata),
        )

    def _parse_sample_record(
        self,
        record: dict[str, Any],
        *,
        source: str,
        line_number: int,
        active_num_nodes: int | None,
        data_warnings: list[str],
    ) -> tuple[float, list[int], list[float]] | None:
        time_raw = record.get("time")
        if time_raw is None or isinstance(time_raw, bool) or not isinstance(time_raw, (int, float)):
            self._warning_or_raise(
                f"{source}, Line {line_number}: sample missing valid numeric 'time' field.",
                data_warnings,
            )
            return None

        time_value = float(time_raw)

        spins_raw = record.get("r_spins")
        if not isinstance(spins_raw, list) or len(spins_raw) == 0:
            self._warning_or_raise(
                f"{source}, Line {line_number}: sample 'r_spins' must be a non-empty list.",
                data_warnings,
            )
            return None

        num_nodes = len(spins_raw)

        if active_num_nodes is not None and num_nodes != active_num_nodes:
            self._warning_or_raise(
                f"{source}, Line {line_number}: active data has {active_num_nodes} "
                f"nodes, but this sample has {num_nodes}; row ignored.",
                data_warnings,
            )
            return None

        spins: list[int] = []
        x_values: list[float] = []

        for idx, item in enumerate(spins_raw):
            if not isinstance(item, dict) or "state" not in item:
                self._warning_or_raise(
                    f"{source}, Line {line_number}: item at index {idx} in 'r_spins' "
                    "missing 'state' key.",
                    data_warnings,
                )
                return None

            state = item.get("state")
            if not isinstance(state, (list, tuple)) or len(state) != 2:
                self._warning_or_raise(
                    f"{source}, Line {line_number}: 'state' at index {idx} must be a "
                    f"2-element array [spin, x], got {state!r}.",
                    data_warnings,
                )
                return None

            spin_raw, x_raw = state

            if isinstance(spin_raw, bool) or not isinstance(spin_raw, int):
                self._warning_or_raise(
                    f"{source}, Line {line_number}: spin must be an integer -1 or 1, "
                    f"got {spin_raw!r} at index {idx}.",
                    data_warnings,
                )
                return None

            spin = int(spin_raw)
            if spin not in {-1, 1}:
                self._warning_or_raise(
                    f"{source}, Line {line_number}: spin must be -1 or 1, "
                    f"got {spin} at index {idx}.",
                    data_warnings,
                )
                return None

            if isinstance(x_raw, bool) or not isinstance(x_raw, (int, float)):
                self._warning_or_raise(
                    f"{source}, Line {line_number}: x must be a number in [-1, 1], "
                    f"got {x_raw!r} at index {idx}.",
                    data_warnings,
                )
                return None

            x = float(x_raw)
            if not -1.0 <= x <= 1.0:
                self._warning_or_raise(
                    f"{source}, Line {line_number}: x must be in [-1, 1], "
                    f"got {x} at index {idx}.",
                    data_warnings,
                )
                return None

            spins.append(spin)
            x_values.append(x)

        return time_value, spins, x_values

    def _warning_or_raise(
        self,
        message: str,
        data_warnings: list[str],
    ) -> None:
        logger.warning(message)

        if self.strict:
            raise ParseError(message)

        data_warnings.append(message)
