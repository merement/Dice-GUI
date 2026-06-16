# app/domain.py

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class DynamicFrame:
    time_index: int
    time_value: float
    spins: np.ndarray      # shape: (num_nodes,)
    x_values: np.ndarray   # shape: (num_nodes,)


@dataclass
class SimulationData:
    times: np.ndarray      # shape: (num_frames,)
    spins: np.ndarray      # shape: (num_frames, num_nodes)
    x_values: np.ndarray   # shape: (num_frames, num_nodes)

    @property
    def num_frames(self) -> int:
        return self.times.shape[0]

    @property
    def num_nodes(self) -> int:
        if self.spins.ndim != 2:
            return 0
        return self.spins.shape[1]

    def frame(self, time_index: int) -> DynamicFrame:
        return DynamicFrame(
            time_index=time_index,
            time_value=float(self.times[time_index]),
            spins=self.spins[time_index],
            x_values=self.x_values[time_index],
        )

# instead of
# data.spins[timeIndex * data.num_nodes + i]
# we can use
# frame.spins[i]
# frame.x_values[i]
