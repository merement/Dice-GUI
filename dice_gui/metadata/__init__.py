# dice_gui/metadata/__init__.py
#
# Package initialization for metadata handling.

from dice_gui.metadata.context import MetadataContext
from dice_gui.metadata.diagnostics import (
    DiagnosticSeverity,
    MetadataDiagnostic,
)
from dice_gui.metadata.processor import JsonMetadataProcessor
from dice_gui.metadata.state import MetadataState

__all__ = [
    "DiagnosticSeverity",
    "JsonMetadataProcessor",
    "MetadataContext",
    "MetadataDiagnostic",
    "MetadataState",
]
