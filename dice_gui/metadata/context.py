# dice_gui/metadata/context.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetadataContext:
    """
    Describes where a metadata record came from.

    This is intentionally source-agnostic. Metadata may come from a file line,
    a JSON stream, an API response, an in-memory object, or some future
    transport mechanism.
    """

    source: str | None = None
    line_number: int | None = None
    record_number: int | None = None

    def describe(self) -> str:
        parts: list[str] = []

        if self.source is not None:
            parts.append(str(self.source))

        if self.line_number is not None:
            parts.append(f"Line {self.line_number}")

        if self.record_number is not None:
            parts.append(f"Record {self.record_number}")

        return ", ".join(parts)
    
