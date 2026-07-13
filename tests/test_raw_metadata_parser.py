# tests/test_raw_metadata_parser.py

import pytest
from pathlib import Path
from dice_gui.raw_metadata_parser import RawMetadataParser
from dice_gui.parsers import ParseError
from dice_gui.domain import LoadedSimulation


def test_parse_valid_with_metadata_base1(tmp_path: Path):
    file_path = tmp_path / "valid_base1.dat"
    content = (
        '#@ {"type": "format", "name": "relaxed-spins", "version": 1}\n'
        '#@ {"type": "node_indexing", "base": 1}\n'
        '#@ {"type": "node", "index": 1, "name": "CTRL_1"}\n'
        '#@ {"type": "node", "index": 2, "name": "CTRL_2"}\n'
        '#@ {"type": "created", "value": "2026-01-26T18:44:00Z"}\n'
        '#@ {"type": "title", "value": "Test Run"}\n'
        '#@ {"type": "notes", "value": "Mock run desc"}\n'
        "0.000 1 0.011 -1 -0.357\n"
        "0.010 -1 0.015 1 0.301\n"
    )
    file_path.write_text(content, encoding="utf-8")

    parser = RawMetadataParser()
    loaded = parser.parse_raw_file(file_path)

    assert isinstance(loaded, LoadedSimulation)
    assert loaded.dynamic_data.num_frames == 2
    assert loaded.dynamic_data.num_nodes == 2

    metadata = loaded.static_data.metadata
    assert metadata["has_metadata"] is True
    assert metadata["title"] == "Test Run"
    assert metadata["notes"] == "Mock run desc"
    assert metadata["created"] == "2026-01-26T18:44:00Z"
    assert metadata["node_ids"] == ["CTRL_1", "CTRL_2"]
    assert metadata["base"] == 1
    assert len(metadata["warnings"]) == 0


def test_parse_valid_with_metadata_base0(tmp_path: Path):
    file_path = tmp_path / "valid_base0.dat"
    content = (
        '#@ {"type": "node_indexing", "base": 0}\n'
        '#@ {"type": "node", "index": 0, "name": "A"}\n'
        '#@ {"type": "node", "index": 1, "name": "B"}\n'
        "0.000 1 0.011 -1 -0.357\n"
    )
    file_path.write_text(content, encoding="utf-8")

    parser = RawMetadataParser()
    loaded = parser.parse_raw_file(file_path)

    metadata = loaded.static_data.metadata
    assert metadata["node_ids"] == ["A", "B"]
    assert metadata["base"] == 0
    assert len(metadata["warnings"]) == 0


def test_parse_omitted_indexing_base(tmp_path: Path):
    # If node_indexing is omitted, default base is 1
    file_path = tmp_path / "omitted_base.dat"
    content = (
        '#@ {"type": "node", "index": 1, "name": "NodeA"}\n'
        "0.000 1 0.011\n"
    )
    file_path.write_text(content, encoding="utf-8")

    parser = RawMetadataParser()
    loaded = parser.parse_raw_file(file_path)

    metadata = loaded.static_data.metadata
    assert metadata["node_ids"] == ["NodeA"]
    assert metadata["base"] == 1
    assert len(metadata["warnings"]) == 0


def test_parse_metadata_warnings(tmp_path: Path):
    file_path = tmp_path / "warnings.dat"
    content = (
        "# Regular comment to ignore\n"
        "#@ invalid_json_here\n"
        '#@ {"base": 1}\n'  # missing type
        '#@ {"type": "node_indexing", "base": 2}\n'  # invalid base value
        '#@ {"type": "node", "index": 1, "name": "FirstNode"}\n'
        '#@ {"type": "node_indexing", "base": 1}\n'  # redefined base and base after node
        '#@ {"type": "node", "index": 0, "name": "NegativeIndex"}\n'  # invalid index for base 1
        '#@ {"type": "node", "index": 1}\n'  # missing name
        '#@ {"type": "node", "name": "MissingIndex"}\n'  # missing index
        '#@ {"type": "created"}\n'  # missing value
        '#@ {"type": "node", "index": 5, "name": "OutOfBounds"}\n'  # index 5 exceeds node count of 2
        "0.000 1 0.011 -1 -0.357\n"
    )
    file_path.write_text(content, encoding="utf-8")

    parser = RawMetadataParser()
    loaded = parser.parse_raw_file(file_path)

    metadata = loaded.static_data.metadata
    assert metadata["node_ids"] == ["FirstNode", ""]
    assert metadata["has_metadata"] is True

    warnings = metadata["warnings"]
    assert len(warnings) > 0

    # Verify that warnings contain messages about specific parsing issues
    assert any("Invalid JSON metadata" in w for w in warnings)
    assert any("missing 'type' field" in w for w in warnings)
    assert any("Invalid index base" in w for w in warnings)
    assert any("Indexing base redefined" in w for w in warnings) or any("Indexing base defined after node records" in w for w in warnings)
    assert any("Node index 0 is invalid" in w for w in warnings)
    assert any("Node record missing or invalid 'index' field" in w for w in warnings)
    assert any("Node record missing 'name' field" in w for w in warnings)
    assert any("missing 'value' field" in w for w in warnings)
    assert any("out of bounds for simulation containing 2 nodes" in w for w in warnings)
