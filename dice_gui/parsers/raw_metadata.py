# dice_gui/parsers/raw_metadata.py
#
# Implements a metadata-aware parser for DICE/Ising-type simulation data.
# It parses legacy raw DICE/Ising-type simulation files that may contain
# JSON-formatted metadata in '#@'-prefixed comment lines.
#
# RawMetadataParser is responsible only for the legacy raw file format:
#
#   - blank lines
#   - normal comments
#   - '#@' metadata decorations
#   - numeric time/spin/x data rows
#
# JSON metadata interpretation is delegated to JsonMetadataProcessor.

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from dice_gui.domain import (
    LoadedSimulation,
    StaticSimulationData,
    TimeSeriesData,
)
from dice_gui.jsondata import JsonMetadataProcessor, MetadataContext
from dice_gui.parsers import ParseError

logger = logging.getLogger(__name__)


class RawMetadataParser:
    """
    Parses time-dependent simulation files containing '#@' metadata comment
    records and raw numeric data rows.
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

        active_num_nodes: int | None = None

        metadata_processor = JsonMetadataProcessor(strict=self.strict)
        data_warnings: list[str] = []

        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()

                if not stripped:
                    continue

                if stripped.startswith("#@"):
                    metadata_processor.process_json_string(
                        stripped[2:].strip(),
                        context=MetadataContext(
                            source=str(file_path),
                            line_number=line_number,
                        ),
                    )
                    continue

                if stripped.startswith("#"):
                    continue

                parsed_row = self._parse_data_line(
                    stripped,
                    source=str(file_path),
                    line_number=line_number,
                    active_num_nodes=active_num_nodes,
                    data_warnings=data_warnings,
                )

                if parsed_row is None:
                    continue

                time_value, spins, x_values = parsed_row

                if active_num_nodes is None:
                    active_num_nodes = len(spins)

                times.append(time_value)
                all_spins.append(spins)
                all_x_values.append(x_values)

        if not times:
            raise ParseError(f"File {file_path} contains no usable data.")

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

    def _parse_data_line(
        self,
        stripped: str,
        *,
        source: str,
        line_number: int,
        active_num_nodes: int | None,
        data_warnings: list[str],
    ) -> tuple[float, list[int], list[float]] | None:
        values = stripped.split()

        if len(values) < 3:
            self._data_warning_or_raise(
                f"{source}, Line {line_number}: expected at least one time value "
                "and one spin/x pair; row ignored.",
                data_warnings,
            )
            return None

        try:
            time_value = float(values[0])
        except ValueError:
            self._data_warning_or_raise(
                f"{source}, Line {line_number}: invalid time value "
                f"{values[0]!r}; row ignored.",
                data_warnings,
            )
            return None

        data_values = values[1:]

        if len(data_values) % 2 != 0:
            self._data_warning_or_raise(
                f"{source}, Line {line_number}: expected an even number of spin/x "
                f"values after the time column, got {len(data_values)}; row ignored.",
                data_warnings,
            )
            return None

        num_nodes = len(data_values) // 2

        # Current domain model expects rectangular arrays. Future frame-based or
        # segmented dynamic data can relax this policy. For now, permissive mode
        # skips incompatible rows rather than failing the whole load.
        if active_num_nodes is not None and num_nodes != active_num_nodes:
            self._data_warning_or_raise(
                f"{source}, Line {line_number}: active data has {active_num_nodes} "
                f"nodes, but this row has {num_nodes}; row ignored.",
                data_warnings,
            )
            return None

        spins: list[int] = []
        x_values: list[float] = []

        for pair_index, i in enumerate(range(0, len(data_values), 2)):
            raw_spin = data_values[i]
            raw_x = data_values[i + 1]

            try:
                spin = int(raw_spin)
            except ValueError:
                self._data_warning_or_raise(
                    f"{source}, Line {line_number}: invalid spin value "
                    f"{raw_spin!r} for node position {pair_index}; row ignored.",
                    data_warnings,
                )
                return None

            if spin not in {-1, 1}:
                self._data_warning_or_raise(
                    f"{source}, Line {line_number}: spin must be -1 or 1, "
                    f"got {spin} for node position {pair_index}; row ignored.",
                    data_warnings,
                )
                return None

            try:
                x = float(raw_x)
            except ValueError:
                self._data_warning_or_raise(
                    f"{source}, Line {line_number}: invalid x value "
                    f"{raw_x!r} for node position {pair_index}; row ignored.",
                    data_warnings,
                )
                return None

            if not -1.0 <= x <= 1.0:
                self._data_warning_or_raise(
                    f"{source}, Line {line_number}: x must be in [-1, 1], "
                    f"got {x} for node position {pair_index}; row ignored.",
                    data_warnings,
                )
                return None

            spins.append(spin)
            x_values.append(x)

        return time_value, spins, x_values

    def _data_warning_or_raise(
        self,
        message: str,
        data_warnings: list[str],
    ) -> None:
        logger.warning(message)

        if self.strict:
            raise ParseError(message)

        data_warnings.append(message)
