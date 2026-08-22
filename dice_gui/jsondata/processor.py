# dice_gui/jsondata/processor.py

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

from dice_gui.jsondata.context import MetadataContext
from dice_gui.jsondata.diagnostics import (
    DiagnosticSeverity,
    MetadataDiagnostic,
)
from dice_gui.jsondata.handlers import (
    FormatRecordHandler,
    MetadataRecordHandler,
    NodeIndexingRecordHandler,
    NodeRecordHandler,
    SimpleValueRecordHandler,
    UnknownRecordHandler,
)
from dice_gui.jsondata.state import MetadataState
from dice_gui.jsondata.validation import (
    as_record_type,
    shallow_json_object_copy,
)
from dice_gui.parsers import ParseError

logger = logging.getLogger(__name__)


class JsonMetadataProcessor:
    """
    Processes JSON-based metadata records.

    This class knows nothing about legacy '#@' decorations, files, or raw data
    line formats. It only understands JSON strings/objects and metadata record
    semantics.
    """

    def __init__(
        self,
        *,
        strict: bool = False,
        handlers: Mapping[str, MetadataRecordHandler] | None = None,
    ):
        self.strict = strict
        self.state = MetadataState()

        self._handlers: dict[str, MetadataRecordHandler] = {
            "format": FormatRecordHandler(),
            "node_indexing": NodeIndexingRecordHandler(),
            "node": NodeRecordHandler(),
            "created": SimpleValueRecordHandler("created"),
            "title": SimpleValueRecordHandler("title"),
            "notes": SimpleValueRecordHandler("notes"),
        }

        if handlers is not None:
            self._handlers.update(dict(handlers))

        self._unknown_handler = UnknownRecordHandler()

    def register_handler(
        self,
        record_type: str,
        handler: MetadataRecordHandler,
        *,
        replace: bool = True,
    ) -> None:
        """
        Register a handler for a metadata record type.

        This keeps the processor extensible without requiring edits to the
        processor itself whenever new metadata record types appear.
        """
        if not replace and record_type in self._handlers:
            raise ValueError(f"Handler for record type {record_type!r} already exists")

        self._handlers[record_type] = handler

    def process_json_string(
        self,
        json_string: str,
        *,
        context: MetadataContext | None = None,
    ) -> None:
        """
        Decode and process one JSON metadata record.

        The caller is responsible for stripping transport-specific decoration,
        for example '#@' in legacy raw data files.
        """
        context = context or MetadataContext()
        self.state.has_metadata = True

        try:
            record = json.loads(json_string)
        except json.JSONDecodeError as exc:
            self._add_diagnostic(
                f"Invalid JSON metadata: {exc}",
                context,
                code="metadata.invalid_json",
            )
            return

        self.process_record(record, context=context)

    def process_record(
        self,
        record: object,
        *,
        context: MetadataContext | None = None,
    ) -> None:
        """
        Process one already-decoded JSON metadata record.
        """
        context = context or MetadataContext()
        self.state.has_metadata = True

        if not isinstance(record, Mapping):
            self._add_diagnostic(
                "Metadata record is not a JSON object; record ignored.",
                context,
                code="metadata.non_object_record",
            )
            return

        # Preserve all well-formed JSON objects, including unknown records.
        self.state.raw_records.append(shallow_json_object_copy(record))

        record_type = as_record_type(record.get("type"))

        if record_type is None:
            self._add_diagnostic(
                "Metadata record missing or invalid 'type' field; record preserved "
                "but not interpreted.",
                context,
                code="metadata.invalid_type",
            )
            return

        handler = self._handlers.get(record_type, self._unknown_handler)

        diagnostic_count_before = len(self.state.diagnostics)
        handler.handle(record, self.state, context)
        self._handle_new_diagnostics_since(diagnostic_count_before)

    def build_static_metadata(self, *, num_nodes: int) -> dict[str, Any]:
        """
        Finalize interpreted metadata for a simulation with the given active
        number of nodes.

        This is where metadata referring to node indices can be reconciled
        against the actual shape of the active data.
        """
        if self.state.has_metadata and not self.state.indexing_base_declared:
            self._add_diagnostic(
                "Indexing base not explicitly declared; defaulting to base 1.",
                MetadataContext(),
                code="metadata.node_indexing.missing",
            )

        node_ids = self._build_node_ids(num_nodes)

        metadata: dict[str, Any] = {
            "node_ids": node_ids,
            "warnings": self.state.warning_messages(),
            "diagnostics": [
                diagnostic.to_dict() for diagnostic in self.state.diagnostics
            ],
            "has_metadata": self.state.has_metadata,
            "base": self.state.final_base,
            "raw_records": self.state.raw_records,
        }

        if self.state.title is not None:
            metadata["title"] = self.state.title

        if self.state.notes is not None:
            metadata["notes"] = self.state.notes

        if self.state.created is not None:
            metadata["created"] = self.state.created

        return metadata

    def _build_node_ids(self, num_nodes: int) -> list[str]:
        node_ids = [""] * num_nodes

        for python_index, name in self.state.node_names.items():
            if 0 <= python_index < num_nodes:
                node_ids[python_index] = name
                continue

            context = self.state.node_contexts.get(python_index, MetadataContext())

            self._add_diagnostic(
                f"Node canonical index {python_index} is out of bounds for "
                f"active simulation containing {num_nodes} nodes; node name ignored.",
                context,
                code="metadata.node.out_of_bounds",
            )

        return node_ids

    def _add_diagnostic(
        self,
        message: str,
        context: MetadataContext,
        *,
        severity: DiagnosticSeverity = DiagnosticSeverity.WARNING,
        code: str | None = None,
    ) -> MetadataDiagnostic:
        diagnostic = self.state.add_diagnostic(
            message,
            context,
            severity=severity,
            code=code,
        )

        logger.warning(diagnostic.format())

        if self.strict:
            raise ParseError(diagnostic.format())

        return diagnostic

    def _handle_new_diagnostics_since(self, diagnostic_count_before: int) -> None:
        """
        Handlers add diagnostics directly to state. This method logs them and,
        in strict mode, raises after the first newly-added diagnostic.
        """
        new_diagnostics = self.state.diagnostics[diagnostic_count_before:]

        for diagnostic in new_diagnostics:
            logger.warning(diagnostic.format())

        if self.strict and new_diagnostics:
            raise ParseError(new_diagnostics[0].format())

        
