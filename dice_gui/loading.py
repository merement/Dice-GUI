from pathlib import Path

from dice_gui.domain import LoadedSimulation
from dice_gui.parsers import (
    ParseError,
    TimeSpinXParser,
    RawMetadataParser,
    NdjsonParser,
)


class UnknownParserError(Exception):
    pass


class ParserRegistry:
    def __init__(self):
        self._parsers = {}
        self._default_parser_id = None

    def register(self, parser, *, default: bool = False):
        parser_id = parser.id

        if parser_id in self._parsers:
            raise ValueError(f"Parser ID {parser_id!r} is already registered.")

        self._parsers[parser_id] = parser

        if default or self._default_parser_id is None:
            self._default_parser_id = parser_id

    def __contains__(self, parser_id: str) -> bool:
        return parser_id in self._parsers

    def get(self, parser_id: str):
        try:
            return self._parsers[parser_id]
        except KeyError as exc:
            raise UnknownParserError(f"Unknown parser ID: {parser_id!r}") from exc

    def parser_ids(self) -> list[str]:
        return list(self._parsers.keys())

    def parsers(self) -> list:
        return list(self._parsers.values())

    @property
    def default_parser_id(self) -> str:
        if self._default_parser_id is None:
            raise RuntimeError("No parsers are registered.")
        return self._default_parser_id


def create_default_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(RawMetadataParser(), default=True)
    registry.register(NdjsonParser(), default=False)
    registry.register(TimeSpinXParser(), default=False)
    return registry


def detect_parser_id(file_path: str | Path) -> str:
    """
    Determines input file format based on syntax:
    If the first non-whitespace character in the file is '{', returns 'ndjson';
    otherwise returns 'raw-metadata'.
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8", errors="replace") as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                return "raw-metadata"
            stripped = chunk.lstrip()
            if stripped:
                if stripped[0] == "{":
                    return "ndjson"
                return "raw-metadata"


class LoadError(Exception):
    pass


class FileLoadService:
    def __init__(self, parser_registry: ParserRegistry):
        self.parser_registry = parser_registry

    def load_file(
        self,
        file_path: str | Path,
        parser_id: str | None = None,
    ) -> LoadedSimulation:
        path = Path(file_path)

        requested_mode = parser_id
        if parser_id == "auto" or parser_id is None:
            if parser_id == "auto":
                detected = detect_parser_id(path)
                if detected in self.parser_registry:
                    effective_parser_id = detected
                else:
                    effective_parser_id = self.parser_registry.default_parser_id
            else:
                effective_parser_id = self.parser_registry.default_parser_id
        else:
            effective_parser_id = parser_id

        parser = self.parser_registry.get(effective_parser_id)

        try:
            if hasattr(parser, "parse_file"):
                loaded = parser.parse_file(file_path)
            elif hasattr(parser, "parse_raw_file"):
                loaded = parser.parse_raw_file(file_path)
            else:
                raise LoadError(f"Parser {effective_parser_id!r} has no parse method.")
        except ParseError as exc:
            mode_desc = f"{parser.name} (Automatic)" if requested_mode == "auto" else parser.name
            raise ParseError(f"Could not load “{path.name}” as {mode_desc}:\n{exc}") from exc
        except FileNotFoundError:
            raise
        except Exception as exc:
            mode_desc = f"{parser.name} (Automatic)" if requested_mode == "auto" else parser.name
            raise LoadError(f"Could not load “{path.name}” as {mode_desc}:\n{exc}") from exc

        loaded.source_path = path
        loaded.parser_id = effective_parser_id

        return loaded

