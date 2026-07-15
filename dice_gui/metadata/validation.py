# dice_gui/metadata/validation.py

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def is_mapping(value: object) -> bool:
    return isinstance(value, Mapping)


def is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def as_record_type(value: object) -> str | None:
    """
    Normalize a metadata record type.

    Returns None if the value cannot serve as a valid record type.
    """
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if not stripped:
        return None

    return stripped


def is_integral_number(value: object) -> bool:
    """
    JSON integers decode as int, but malformed metadata may contain floats.

    We accept integral floats such as 3.0, but reject 3.2 and bool.
    """
    if isinstance(value, bool):
        return False

    if isinstance(value, int):
        return True

    if isinstance(value, float):
        return value.is_integer()

    return False


def as_int(value: object) -> int | None:
    if not is_integral_number(value):
        return None

    return int(value)


def as_string(value: object) -> str | None:
    if value is None:
        return None

    return str(value)


def shallow_json_object_copy(record: Mapping[str, Any]) -> dict[str, Any]:
    """
    Store a shallow copy of a JSON object.

    This intentionally does not deep-copy. Metadata records should generally
    be treated as immutable once received.
    """
    return dict(record)
