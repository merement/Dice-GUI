# dice_gui/metadata/handlers.py

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from dice_gui.metadata.context import MetadataContext
from dice_gui.metadata.state import MetadataState
from dice_gui.metadata.validation import as_int, as_string


class MetadataRecordHandler(Protocol):
    """
    Protocol for metadata record handlers.

    Handlers are deliberately permissive. They should usually emit diagnostics
    and return rather than raising exceptions.
    """

    def handle(
        self,
        record: Mapping[str, Any],
        state: MetadataState,
        context: MetadataContext,
    ) -> None:
        ...


class FormatRecordHandler:
    """
    Handles format records.

    Currently this is a no-op, but this is the natural place for future format
    compatibility checks.
    """

    def handle(
        self,
        record: Mapping[str, Any],
        state: MetadataState,
        context: MetadataContext,
    ) -> None:
        return


class NodeIndexingRecordHandler:
    """
    Handles records such as:

        {"type": "node_indexing", "base": 1}

    Unlike the previous implementation, the indexing base is contextual. Later
    records may change it. This better fits stream-style metadata.
    """

    def handle(
        self,
        record: Mapping[str, Any],
        state: MetadataState,
        context: MetadataContext,
    ) -> None:
        base = as_int(record.get("base"))

        if base is None:
            state.add_diagnostic(
                f"Invalid indexing base {record.get('base')!r}; "
                f"keeping current base {state.current_index_base}.",
                context,
                code="metadata.node_indexing.invalid_base",
            )
            return

        if base not in (0, 1):
            state.add_diagnostic(
                f"Indexing base is recommended to be 0 or 1, got {base}.",
                context,
                code="metadata.node_indexing.non_standard_base",
            )

        # Check if base is defined after nodes have been registered
        if state.node_names:
            state.add_diagnostic(
                "Indexing base defined after node records.",
                context,
                code="metadata.node_indexing.defined_after_nodes",
            )

        # Check if base is redefined
        elif state.indexing_base_declared:
            state.add_diagnostic(
                "Indexing base redefined.",
                context,
                code="metadata.node_indexing.redefined",
            )

        state.current_index_base = base
        state.indexing_base_declared = True


class NodeRecordHandler:
    """
    Handles records such as:

        {"type": "node", "index": 1, "name": "A"}

    A node record may optionally carry its own base:

        {"type": "node", "index": 12, "base": 12, "name": "A"}

    If present and valid, the record-local base takes precedence over the
    current state base for that record only.
    """

    def handle(
        self,
        record: Mapping[str, Any],
        state: MetadataState,
        context: MetadataContext,
    ) -> None:
        raw_index = record.get("index")
        index = as_int(raw_index)

        if index is None:
            state.add_diagnostic(
                f"Node record missing or invalid 'index' field: {raw_index!r}.",
                context,
                code="metadata.node.invalid_index",
            )
            return

        name = as_string(record.get("name"))

        if name is None:
            state.add_diagnostic(
                "Node record missing 'name' field.",
                context,
                code="metadata.node.missing_name",
            )
            return

        record_base = as_int(record.get("base"))

        if "base" in record and record_base is None:
            state.add_diagnostic(
                f"Node record has invalid local base {record.get('base')!r}; "
                f"using current base {state.current_index_base}.",
                context,
                code="metadata.node.invalid_local_base",
            )

        effective_base = (
            record_base if record_base is not None else state.current_index_base
        )

        python_index = index - effective_base

        if python_index < 0:
            state.add_diagnostic(
                f"Node index {index} is invalid for base {effective_base}; "
                "node record ignored.",
                context,
                code="metadata.node.negative_python_index",
            )
            return

        previous_name = state.node_names.get(python_index)

        if previous_name is not None and previous_name != name:
            state.add_diagnostic(
                f"Node name for canonical index {python_index} changed "
                f"from {previous_name!r} to {name!r}; using latest value.",
                context,
                code="metadata.node.name_overwritten",
            )

        state.node_names[python_index] = name
        state.node_contexts[python_index] = context


class SimpleValueRecordHandler:
    """
    Handles singleton value records such as title, notes, and created.

    Last value wins, with diagnostics when a value is overwritten.
    """

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.context_field_name = f"{field_name}_context"

    def handle(
        self,
        record: Mapping[str, Any],
        state: MetadataState,
        context: MetadataContext,
    ) -> None:
        value = as_string(record.get("value"))

        if value is None:
            state.add_diagnostic(
                f"Metadata record {self.field_name!r} missing 'value' field.",
                context,
                code=f"metadata.{self.field_name}.missing_value",
            )
            return

        previous_value = getattr(state, self.field_name)

        if previous_value is not None and previous_value != value:
            state.add_diagnostic(
                f"Metadata field {self.field_name!r} changed "
                f"from {previous_value!r} to {value!r}; using latest value.",
                context,
                code=f"metadata.{self.field_name}.overwritten",
            )

        setattr(state, self.field_name, value)
        setattr(state, self.context_field_name, context)


class UnknownRecordHandler:
    """
    Handles records with unknown type.

    Unknown records are preserved in state.raw_records by the processor before
    dispatch. This handler only emits a diagnostic.
    """

    def handle(
        self,
        record: Mapping[str, Any],
        state: MetadataState,
        context: MetadataContext,
    ) -> None:
        state.add_diagnostic(
            f"Unknown metadata record type {record.get('type')!r}; "
            "record preserved but not interpreted.",
            context,
            code="metadata.unknown_record_type",
        )
        
