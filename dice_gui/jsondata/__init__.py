# dice_gui/jsondata/__init__.py
#
# Package initialization for metadata handling.

from dice_gui.jsondata.context import MetadataContext
from dice_gui.jsondata.diagnostics import (
    DiagnosticSeverity,
    MetadataDiagnostic,
)
from dice_gui.jsondata.processor import JsonMetadataProcessor
from dice_gui.jsondata.state import MetadataState

__all__ = [
    "DiagnosticSeverity",
    "JsonMetadataProcessor",
    "MetadataContext",
    "MetadataDiagnostic",
    "MetadataState",
]
