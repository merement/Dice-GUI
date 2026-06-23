# dice_gui/domain.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class DynamicFrame:
    time_index: int
    time_value: float
    spins: np.ndarray  # shape: (num_nodes,)
    x_values: np.ndarray  # shape: (num_nodes,)


@dataclass
class TimeSeriesData:
    times: np.ndarray  # shape: (num_frames,)
    spins: np.ndarray  # shape: (num_frames, num_nodes)
    x_values: np.ndarray  # shape: (num_frames, num_nodes)

    @property
    def num_frames(self) -> int:
        return self.times.shape[0]

    @property
    def num_nodes(self) -> int:
        if self.spins.ndim != 2:
            return 0
        return self.spins.shape[1]

    def frame(self, time_index: int) -> DynamicFrame:
        if not 0 <= time_index < self.num_frames:
            raise IndexError(
                f"time_index {time_index} out of range for {self.num_frames} frames."
            )

        return DynamicFrame(
            time_index=time_index,
            time_value=float(self.times[time_index]),
            spins=self.spins[time_index],
            x_values=self.x_values[time_index],
        )

    def __post_init__(self):
        self.times = np.asarray(self.times, dtype=float)
        self.spins = np.asarray(self.spins, dtype=np.int8)
        self.x_values = np.asarray(self.x_values, dtype=float)

        if self.times.ndim != 1:
            raise ValueError("times must be a 1D array.")

        if self.spins.ndim != 2:
            raise ValueError("spins must be a 2D array.")

        if self.x_values.ndim != 2:
            raise ValueError("x_values must be a 2D array.")

        if self.spins.shape != self.x_values.shape:
            raise ValueError("spins and x_values must have the same shape.")

        if self.spins.shape[0] != self.times.shape[0]:
            raise ValueError("number of frames must match number of time values.")

        if not np.all(np.isin(self.spins, [-1, 1])):
            raise ValueError("spins must contain only -1 or 1.")

        if not np.all((-1.0 <= self.x_values) & (self.x_values <= 1.0)):
            raise ValueError("x_values must be in [-1, 1].")


@dataclass
class SimulationGraph:
    """
    Optional static graph data.

    This can stay deliberately vague until your graph format settles.
    """

    num_nodes: int
    edges: list[tuple[int, int]] = field(default_factory=list)
    node_labels: list[str] | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class StaticSimulationData:
    """
    Optional static simulation information.

    Keep this lightweight for now. You can specialize fields later.
    """

    parameters: dict[str, Any] = field(default_factory=dict)
    graph: SimulationGraph | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedSimulation:
    """
    Complete result of loading a simulation file.

    dynamic_data is required.
    static_data is optional.
    """

    dynamic_data: TimeSeriesData
    static_data: StaticSimulationData | None = None
    source_path: Path | None = None
    parser_id: str | None = None

    @property
    def has_static_data(self) -> bool:
        return self.static_data is not None
