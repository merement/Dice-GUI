# dice_gui/loading.py or dice_gui/parsers.py

from pathlib import Path

from dice_gui.domain import LoadedSimulation
from dice_gui.parsers import ParseError, TimeSpinXParser

# from typing import Protocol
# class SimulationParser(Protocol):
#     id: str
#     name: str
#     file_filter: str

#     def parse_file(self, file_path: str | Path) -> LoadedSimulation:
#         pass


class UnknownParserError(Exception):
    pass


class ParserRegistry:
    def __init__(self):
        self._parsers = {}

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
    registry.register(TimeSpinXParser(), default=True)
    return registry


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

        if parser_id is None:
            parser_id = self.parser_registry.default_parser_id

        parser = self.parser_registry.get(parser_id)

        try:
            loaded = parser.parse_file(file_path)
        except ParseError:
            raise
        except FileNotFoundError:
            raise
        except Exception as exc:
            raise LoadError(
                f"Failed to load {path} with parser {parser_id!r}: {exc}"
            ) from exc

        loaded.source_path = path
        loaded.parser_id = parser_id

        return loaded
