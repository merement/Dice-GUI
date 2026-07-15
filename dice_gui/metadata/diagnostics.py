# dice_gui/metadata/diagnostics.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from dice_gui.metadata.context import MetadataContext


class DiagnosticSeverity(str, Enum):
    """
    Severity of a diagnostic emitted while interpreting metadata.

    The application is generally permissive, so most recoverable problems
    should be WARNING rather than ERROR.
    """

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class MetadataDiagnostic:
    """
    Structured diagnostic message for metadata processing.

    These are useful both for GUI display and for communicating malformed
    data/metadata back to the data-producing side.
    """

    message: str
    context: MetadataContext
    severity: DiagnosticSeverity = DiagnosticSeverity.WARNING
    code: str | None = None

    def format(self) -> str:
        location = self.context.describe()
        prefix_parts: list[str] = []

        if location:
            prefix_parts.append(location)

        if self.code:
            prefix_parts.append(self.code)

        if prefix_parts:
            return f"{' | '.join(prefix_parts)}: {self.message}"

        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "severity": self.severity.value,
            "code": self.code,
            "source": self.context.source,
            "line_number": self.context.line_number,
            "record_number": self.context.record_number,
        }
    
