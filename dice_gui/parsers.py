# dice_gui/parsers.py
#
# Implements the parsers for the simulation data files.
# TimeSpinXParser (raw data parser) parses files of the form:
#
#     time spin_0 x_0 spin_1 x_1 spin_2 x_2 ...
#
# Example:
#
#     0.011 1 0.305 1 -0.357 -1 0.800

from pathlib import Path

import numpy as np

from dice_gui.domain import LoadedSimulation, TimeSeriesData


class ParseError(Exception):
    pass


class TimeSpinXParser:
    """
    Parses files of the form:

        time spin_0 x_0 spin_1 x_1 spin_2 x_2 ...

    Example:

        0.011 1 0.305 1 -0.357 -1 0.800
    """

    id = "raw"
    name = "Raw time/spin/x data"
    file_dialog_filter = "Raw data (*.dat *.txt)"

    def parse_raw_file(self, file_path: str | Path) -> LoadedSimulation:
        file_path = Path(file_path)

        times: list[float] = []
        all_spins: list[list[int]] = []
        all_x_values: list[list[float]] = []

        expected_num_nodes: int | None = None

        with file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()

                if not stripped or stripped.startswith("#"):
                    continue

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

        return LoadedSimulation(
            dynamic_data=TimeSeriesData(
                times=np.array(times, dtype=float),
                spins=np.array(all_spins, dtype=np.int8),
                x_values=np.array(all_x_values, dtype=float),
            ),
        )


# class AggregatedSimulationParser:
#     id = "aggregated"
#     name = "Aggregated simulation file"
#     file_filter = "Aggregated simulation files (*.json *.yaml *.sim)"

#     def parse_file(self, file_path: str | Path) -> LoadedSimulation:
#         pass
