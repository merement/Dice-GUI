# dice_gui/metadata/records.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dice_gui.metadata.context import MetadataContext


@dataclass(frozen=True)
class TypedMetadataRecord:
    """
    Base class for typed metadata records.

    The current processor still dispatches from raw JSON mappings because that
    is flexible and convenient. These typed records provide a natural place for
    richer future parsing and validation as record schemas stabilize.
    """

    type: str
    raw: dict[str, Any]
    context: MetadataContext


@dataclass(frozen=True)
class NodeIndexingRecord(TypedMetadataRecord):
    base: int


@dataclass(frozen=True)
class NodeRecord(TypedMetadataRecord):
    index: int
    name: str
    base: int
    python_index: int


@dataclass(frozen=True)
class SimpleValueRecord(TypedMetadataRecord):
    value: str


@dataclass(frozen=True)
class UnknownMetadataRecord(TypedMetadataRecord):
    pass
