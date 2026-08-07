"""Small Draft 2020-12 subset validator for the registry contract.

The project runtime intentionally has no third-party jsonschema dependency.
This validator supports only the schema features used by
``korean_vtuber_registry_schema_v0_1.json`` and fails closed on records.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "korean_vtuber_registry_schema_v0_1.json"
)


def load_schema(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path) if path else SCHEMA_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def validate_record(
    record: dict[str, Any],
    *,
    schema: dict[str, Any] | None = None,
) -> list[str]:
    contract = schema or load_schema()
    record_type = record.get("record_type")
    definition = contract.get("$defs", {}).get(record_type)
    if not isinstance(definition, dict):
        return [f"record_type: unknown value {record_type!r}"]
    return _validate(record, definition, contract, path="$", seen_refs=set())


def validate_ndjson(
    path: str | Path,
    *,
    expected_record_type: str | None = None,
    schema: dict[str, Any] | None = None,
) -> tuple[int, list[str]]:
    contract = schema or load_schema()
    errors: list[str] = []
    count = 0
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                errors.append(f"line {line_number}: record is not an object")
                continue
            if expected_record_type and record.get("record_type") != expected_record_type:
                errors.append(
                    f"line {line_number}: expected {expected_record_type}, "
                    f"got {record.get('record_type')!r}"
                )
            errors.extend(
                f"line {line_number}: {message}"
                for message in validate_record(record, schema=contract)
            )
    return count, errors


def _validate(
    value: Any,
    rule: dict[str, Any],
    root: dict[str, Any],
    *,
    path: str,
    seen_refs: set[str],
) -> list[str]:
    errors: list[str] = []

    ref = rule.get("$ref")
    if ref:
        if ref in seen_refs:
            return [f"{path}: cyclic schema ref {ref}"]
        target = _resolve_ref(root, str(ref))
        return _validate(value, target, root, path=path, seen_refs={*seen_refs, str(ref)})

    if "const" in rule and value != rule["const"]:
        errors.append(f"{path}: expected const {rule['const']!r}, got {value!r}")
        return errors
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"{path}: {value!r} not in enum")
        return errors

    allowed_types = rule.get("type")
    if allowed_types:
        if isinstance(allowed_types, str):
            allowed_types = [allowed_types]
        if not any(_matches_type(value, item) for item in allowed_types):
            errors.append(f"{path}: expected type {allowed_types}, got {type(value).__name__}")
            return errors

    if isinstance(value, dict):
        required = rule.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}.{key}: missing required property")
        properties = rule.get("properties", {})
        if rule.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}.{key}: additional property not allowed")
        for key, child_rule in properties.items():
            if key in value:
                errors.extend(
                    _validate(
                        value[key],
                        child_rule,
                        root,
                        path=f"{path}.{key}",
                        seen_refs=seen_refs,
                    )
                )

    if isinstance(value, list):
        if rule.get("uniqueItems"):
            serialized = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{path}: duplicate array items")
        item_rule = rule.get("items")
        if isinstance(item_rule, dict):
            for index, item in enumerate(value):
                errors.extend(
                    _validate(
                        item,
                        item_rule,
                        root,
                        path=f"{path}[{index}]",
                        seen_refs=seen_refs,
                    )
                )

    if isinstance(value, str):
        minimum = rule.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: shorter than minLength {minimum}")
        pattern = rule.get("pattern")
        if pattern and re.search(str(pattern), value) is None:
            errors.append(f"{path}: does not match {pattern!r}")

    return errors


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported external schema ref: {ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(node, dict):
        raise ValueError(f"schema ref does not resolve to object: {ref}")
    return node


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False
