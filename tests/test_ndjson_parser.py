import pytest
from pathlib import Path

from dice_gui.domain import LoadedSimulation
from dice_gui.parsers import NdjsonParser, ParseError


def test_parse_valid_ndjson(tmp_path: Path):
    file_path = tmp_path / "simulation.ndjson"
    content = (
        '{"type": "format", "name": "relaxed-spins", "version": 1}\n'
        '{"type": "node_indexing", "base": 1}\n'
        '{"type": "node", "index": 1, "name": "CTRL_1"}\n'
        '{"type": "sample", "time": 0.0, "r_spins": [{"state": [1, 0.12]}, {"state": [-1, 0.44]}]}\n'
        '{"type": "sample", "time": 0.1, "r_spins": [{"state": [-1, 0.15]}, {"state": [1, 0.43]}]}\n'
    )
    file_path.write_text(content, encoding="utf-8")

    parser = NdjsonParser()
    loaded = parser.parse_file(file_path)

    assert isinstance(loaded, LoadedSimulation)
    data = loaded.dynamic_data
    assert data.num_frames == 2
    assert data.num_nodes == 2

    assert list(data.times) == [0.0, 0.1]

    frame0 = data.frame(0)
    assert list(frame0.spins) == [1, -1]
    assert list(frame0.x_values) == [0.12, 0.44]

    frame1 = data.frame(1)
    assert list(frame1.spins) == [-1, 1]
    assert list(frame1.x_values) == [0.15, 0.43]

    assert loaded.static_data is not None
    meta = loaded.static_data.metadata
    assert meta["base"] == 1
    assert meta["node_ids"] == ["CTRL_1", ""]


def test_parse_ndjson_invalid_spin_strict(tmp_path: Path):
    file_path = tmp_path / "invalid_spin.ndjson"
    content = (
        '{"type": "sample", "time": 0.0, "r_spins": [{"state": [0, 0.12]}]}\n'
    )
    file_path.write_text(content, encoding="utf-8")

    parser = NdjsonParser(strict=True)
    with pytest.raises(ParseError, match="spin must be -1 or 1"):
        parser.parse_file(file_path)


def test_parse_ndjson_invalid_x_permissive(tmp_path: Path):
    file_path = tmp_path / "invalid_x.ndjson"
    content = (
        '{"type": "sample", "time": 0.0, "r_spins": [{"state": [1, 1.5]}]}\n'
        '{"type": "sample", "time": 0.1, "r_spins": [{"state": [1, 0.5]}]}\n'
    )
    file_path.write_text(content, encoding="utf-8")

    parser = NdjsonParser(strict=False)
    loaded = parser.parse_file(file_path)

    # First row is skipped, second row loaded
    assert loaded.dynamic_data.num_frames == 1
    assert loaded.dynamic_data.times[0] == 0.1
    meta = loaded.static_data.metadata
    assert "warnings" in meta
    assert len(meta["warnings"]) > 0


def test_parse_ndjson_empty_file(tmp_path: Path):
    file_path = tmp_path / "empty.ndjson"
    file_path.write_text("", encoding="utf-8")

    parser = NdjsonParser()
    with pytest.raises(ParseError, match="contains no usable sample data"):
        parser.parse_file(file_path)
