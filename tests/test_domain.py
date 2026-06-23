import numpy as np
import pytest
from dice_gui.domain import TimeSeriesData, DynamicFrame, SimulationGraph, StaticSimulationData, LoadedSimulation

def test_time_series_data_valid():
    times = np.array([0.0, 0.1, 0.2])
    # 3 frames, 2 nodes
    spins = np.array([
        [1, -1],
        [-1, 1],
        [1, 1]
    ], dtype=np.int8)
    x_values = np.array([
        [0.0, 0.5],
        [-0.1, 0.4],
        [0.1, 0.3]
    ])
    
    data = TimeSeriesData(times=times, spins=spins, x_values=x_values)
    
    assert data.num_frames == 3
    assert data.num_nodes == 2
    
    # Retrieve frame
    frame0 = data.frame(0)
    assert isinstance(frame0, DynamicFrame)
    assert frame0.time_index == 0
    assert frame0.time_value == 0.0
    np.testing.assert_array_equal(frame0.spins, np.array([1, -1], dtype=np.int8))
    np.testing.assert_array_equal(frame0.x_values, np.array([0.0, 0.5]))


def test_time_series_data_invalid_times_dim():
    # times must be 1D
    times = np.array([[0.0, 0.1]])
    spins = np.array([[1, -1]])
    x_values = np.array([[0.0, 0.5]])
    
    with pytest.raises(ValueError, match="times must be a 1D array."):
        TimeSeriesData(times=times, spins=spins, x_values=x_values)


def test_time_series_data_invalid_spins_dim():
    # spins must be 2D
    times = np.array([0.0])
    spins = np.array([1, -1])
    x_values = np.array([[0.0, 0.5]])
    
    with pytest.raises(ValueError, match="spins must be a 2D array."):
        TimeSeriesData(times=times, spins=spins, x_values=x_values)


def test_time_series_data_invalid_x_values_dim():
    # x_values must be 2D
    times = np.array([0.0])
    spins = np.array([[1, -1]])
    x_values = np.array([0.0, 0.5])
    
    with pytest.raises(ValueError, match="x_values must be a 2D array."):
        TimeSeriesData(times=times, spins=spins, x_values=x_values)


def test_time_series_data_shape_mismatch():
    times = np.array([0.0])
    spins = np.array([[1, -1]])
    # x_values shape mismatched
    x_values = np.array([[0.0, 0.5, 0.6]])
    
    with pytest.raises(ValueError, match="spins and x_values must have the same shape."):
        TimeSeriesData(times=times, spins=spins, x_values=x_values)


def test_time_series_data_frame_count_mismatch():
    times = np.array([0.0, 0.1])
    # only 1 frame of spins/x_values
    spins = np.array([[1, -1]])
    x_values = np.array([[0.0, 0.5]])
    
    with pytest.raises(ValueError, match="number of frames must match number of time values."):
        TimeSeriesData(times=times, spins=spins, x_values=x_values)


def test_time_series_data_invalid_spin_values():
    times = np.array([0.0])
    # spin must be -1 or 1, not 0
    spins = np.array([[1, 0]])
    x_values = np.array([[0.0, 0.5]])
    
    with pytest.raises(ValueError, match="spins must contain only -1 or 1."):
        TimeSeriesData(times=times, spins=spins, x_values=x_values)


def test_time_series_data_invalid_x_ranges():
    times = np.array([0.0])
    spins = np.array([[1, -1]])
    # coordinate out of [-1, 1]
    x_values = np.array([[0.0, 1.5]])
    
    with pytest.raises(ValueError, match="x_values must be in \\[-1, 1\\]."):
        TimeSeriesData(times=times, spins=spins, x_values=x_values)


def test_time_series_data_frame_bounds():
    times = np.array([0.0, 0.1])
    spins = np.array([[1, -1], [-1, 1]])
    x_values = np.array([[0.0, 0.5], [-0.5, 0.5]])
    
    data = TimeSeriesData(times=times, spins=spins, x_values=x_values)
    
    # Valid indices
    assert data.frame(0).time_value == 0.0
    assert data.frame(1).time_value == 0.1
    
    # Out of bounds
    with pytest.raises(IndexError, match="time_index -1 out of range"):
        data.frame(-1)
    
    with pytest.raises(IndexError, match="time_index 2 out of range"):
        data.frame(2)
