import pytest
from pathlib import Path
from dice_gui.loading import ParserRegistry, FileLoadService, UnknownParserError, LoadError
from dice_gui.domain import LoadedSimulation, TimeSeriesData
import numpy as np

class MockParser:
    def __init__(self, parser_id, name="Mock Parser"):
        self.id = parser_id
        self.name = name

    def parse_file(self, file_path: str | Path) -> LoadedSimulation:
        times = np.array([0.0])
        spins = np.array([[1]])
        x_values = np.array([[0.0]])
        return LoadedSimulation(
            dynamic_data=TimeSeriesData(times=times, spins=spins, x_values=x_values)
        )


def test_registry_registration():
    registry = ParserRegistry()
    parser1 = MockParser("p1", "Parser 1")
    parser2 = MockParser("p2", "Parser 2")
    
    registry.register(parser1, default=True)
    registry.register(parser2)
    
    assert "p1" in registry
    assert "p2" in registry
    assert "nonexistent" not in registry
    
    assert registry.get("p1") is parser1
    assert registry.get("p2") is parser2
    assert registry.default_parser_id == "p1"
    
    assert registry.parser_ids() == ["p1", "p2"]
    assert registry.parsers() == [parser1, parser2]


def test_registry_errors():
    registry = ParserRegistry()
    
    # default when empty
    with pytest.raises(RuntimeError, match="No parsers are registered."):
        _ = registry.default_parser_id
        
    parser = MockParser("p1")
    registry.register(parser)
    
    # duplicate registration
    with pytest.raises(ValueError, match="Parser ID 'p1' is already registered."):
        registry.register(parser)
        
    # get unknown parser
    with pytest.raises(UnknownParserError, match="Unknown parser ID: 'unknown'"):
        registry.get("unknown")


def test_file_load_service(tmp_path: Path):
    registry = ParserRegistry()
    parser = MockParser("mock_id")
    registry.register(parser, default=True)
    
    service = FileLoadService(registry)
    file_path = tmp_path / "test.dat"
    file_path.write_text("dummy", encoding="utf-8")
    
    loaded = service.load_file(file_path)
    assert isinstance(loaded, LoadedSimulation)
    assert loaded.parser_id == "mock_id"
    assert loaded.source_path == file_path
    
    # explicit parser id
    loaded2 = service.load_file(file_path, parser_id="mock_id")
    assert loaded2.parser_id == "mock_id"


def test_file_load_service_parser_exception(tmp_path: Path):
    class ExplodingParser:
        id = "exploder"
        name = "Exploder"
        
        def parse_file(self, file_path):
            raise RuntimeError("Boom!")

    registry = ParserRegistry()
    registry.register(ExplodingParser(), default=True)
    
    service = FileLoadService(registry)
    file_path = tmp_path / "test.dat"
    file_path.write_text("dummy", encoding="utf-8")
    
    with pytest.raises(LoadError, match="Could not load “test.dat” as Exploder:"):
        service.load_file(file_path)


def test_detect_parser_id(tmp_path: Path):
    from dice_gui.loading import detect_parser_id, create_default_parser_registry

    ndjson_file = tmp_path / "data.ndjson"
    ndjson_file.write_text('  {"type": "sample"}\n', encoding="utf-8")
    assert detect_parser_id(ndjson_file) == "ndjson"

    raw_file = tmp_path / "data.dat"
    raw_file.write_text("#@ metadata\n0.0 1 0.1", encoding="utf-8")
    assert detect_parser_id(raw_file) == "raw-metadata"


def test_automatic_file_load_service(tmp_path: Path):
    from dice_gui.loading import create_default_parser_registry

    registry = create_default_parser_registry()
    service = FileLoadService(registry)

    ndjson_file = tmp_path / "sim.ndjson"
    ndjson_file.write_text('{"type": "sample", "time": 0.0, "r_spins": [{"state": [1, 0.5]}]}\n', encoding="utf-8")

    loaded = service.load_file(ndjson_file, parser_id="auto")
    assert loaded.parser_id == "ndjson"
    assert loaded.dynamic_data.num_frames == 1

