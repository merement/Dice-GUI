# dice_gui/jsondata/state.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dice_gui.jsondata.context import MetadataContext
from dice_gui.jsondata.diagnostics import (
    DiagnosticSeverity,
    MetadataDiagnostic,
)


@dataclass
class MetadataState:
    """
    Mutable state accumulated while interpreting metadata records.

    This state is intentionally contextual and stream-friendly. For example,
    the current indexing base is not treated as an immutable global fact.
    Later metadata records may change the active context.
    """

    has_metadata: bool = False

    # Current interpretation context.
    current_index_base: int = 1
    indexing_base_declared: bool = False

    # Interpreted metadata.
    node_names: dict[int, str] = field(default_factory=dict)
    node_contexts: dict[int, MetadataContext] = field(default_factory=dict)

    title: str | None = None
    title_context: MetadataContext | None = None

    notes: str | None = None
    notes_context: MetadataContext | None = None

    created: str | None = None
    created_context: MetadataContext | None = None

    # Preserve original well-formed JSON metadata objects for forward
    # compatibility and debugging.
    raw_records: list[dict[str, Any]] = field(default_factory=list)

    # Structured diagnostics.
    diagnostics: list[MetadataDiagnostic] = field(default_factory=list)

    def add_diagnostic(
        self,
        message: str,
        context: MetadataContext,
        *,
        severity: DiagnosticSeverity = DiagnosticSeverity.WARNING,
        code: str | None = None,
    ) -> MetadataDiagnostic:
        diagnostic = MetadataDiagnostic(
            message=message,
            context=context,
            severity=severity,
            code=code,
        )
        self.diagnostics.append(diagnostic)
        return diagnostic

    def warning_messages(self) -> list[str]:
        """
        Legacy-friendly formatted warning strings.

        The GUI can later consume `diagnostics` directly, but this keeps
        compatibility with existing metadata["warnings"] expectations.
        """
        return [diagnostic.format() for diagnostic in self.diagnostics]

    @property
    def final_base(self) -> int:
        """
        Compatibility alias.

        Historically metadata exposed `base`. In the new interpretation model,
        this is simply the final active indexing base after processing all
        metadata records.
        """
        return self.current_index_base
    
