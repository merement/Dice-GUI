import pytest
from pathlib import Path
from dice_gui.parsers import TimeSpinXParser, ParseError
from dice_gui.domain import LoadedSimulation

def test_parse_valid_data(tmp_path: Path):
    file_path = tmp_path / "valid.dat"
    content = (
        "0.000 1 0.011 -1 -0.357\n"
        "0.010 -1 0.015 1 0.301\n"
        "\n"  # blank line
        "0.020 1 0.020 -1 0.299\n"
    )
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    loaded = parser.parse_file(file_path)
    
    assert isinstance(loaded, LoadedSimulation)
    data = loaded.dynamic_data
    assert data.num_frames == 3
    assert data.num_nodes == 2
    
    # Check times
    assert list(data.times) == [0.0, 0.010, 0.020]
    
    # Check frame 0
    frame0 = data.frame(0)
    assert list(frame0.spins) == [1, -1]
    assert list(frame0.x_values) == [0.011, -0.357]


def test_parse_too_few_values(tmp_path: Path):
    file_path = tmp_path / "invalid.dat"
    # only time and spin, missing x coordinate
    content = "0.000 1\n"
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="Line 1: expected at least one time value and one spin/x pair."):
        parser.parse_file(file_path)


def test_parse_invalid_time(tmp_path: Path):
    file_path = tmp_path / "invalid.dat"
    content = "abc 1 0.5\n"
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="Line 1: invalid time value 'abc'."):
        parser.parse_file(file_path)


def test_parse_uneven_spin_x_columns(tmp_path: Path):
    file_path = tmp_path / "invalid.dat"
    content = "0.000 1 0.5 -1\n"  # time, spin, x, spin (missing last x)
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="Line 1: expected an even number of spin/x values after the time column, got 3."):
        parser.parse_file(file_path)


def test_parse_mismatched_node_counts(tmp_path: Path):
    file_path = tmp_path / "invalid.dat"
    content = (
        "0.000 1 0.5\n"  # 1 node
        "0.010 1 0.5 -1 -0.2\n"  # 2 nodes
    )
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="Line 2: expected 1 nodes, got 2."):
        parser.parse_file(file_path)


def test_parse_invalid_spin_value(tmp_path: Path):
    file_path = tmp_path / "invalid.dat"
    content = "0.000 abc 0.5\n"
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="Line 1: invalid spin value 'abc'."):
        parser.parse_file(file_path)


def test_parse_out_of_bounds_spin(tmp_path: Path):
    file_path = tmp_path / "invalid.dat"
    content = "0.000 0 0.5\n"  # spin must be -1 or 1, not 0
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="Line 1: spin must be -1 or 1, got 0."):
        parser.parse_file(file_path)


def test_parse_invalid_x_value(tmp_path: Path):
    file_path = tmp_path / "invalid.dat"
    content = "0.000 1 abc\n"
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="Line 1: invalid x value 'abc'."):
        parser.parse_file(file_path)


def test_parse_out_of_bounds_x(tmp_path: Path):
    file_path = tmp_path / "invalid.dat"
    content = "0.000 1 1.05\n"  # x must be in [-1, 1]
    file_path.write_text(content, encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="Line 1: x must be in \\[-1, 1\\], got 1.05."):
        parser.parse_file(file_path)


def test_parse_empty_file(tmp_path: Path):
    file_path = tmp_path / "empty.dat"
    file_path.write_text("", encoding="utf-8")
    
    parser = TimeSpinXParser()
    with pytest.raises(ParseError, match="contains no data."):
        parser.parse_file(file_path)
