"""Dependency-free recursive validation for the package JSON Schema subset."""

from __future__ import annotations

import math
import re
from typing import Any


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "null":
        return value is None
    return True


def _validate_node(value: Any, rules: dict[str, Any], path: str, errors: list[str]) -> None:
    expected = rules.get("type")
    if isinstance(expected, list):
        if not any(_type_matches(value, item) for item in expected):
            errors.append(f"Property {path} must be one of types {expected!r}")
            return
    elif isinstance(expected, str) and not _type_matches(value, expected):
        errors.append(f"Property {path} must be of type {expected}")
        return

    if "const" in rules and value != rules["const"]:
        errors.append(f"Property {path} must equal {rules['const']!r}")
    if "enum" in rules and value not in rules["enum"]:
        errors.append(f"Property {path} must be one of {rules['enum']!r}")

    numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
    if numeric:
        number = float(value)
        if not math.isfinite(number):
            errors.append(f"Property {path} must be finite")
            return
        if "minimum" in rules and number < float(rules["minimum"]):
            errors.append(f"Property {path} must be >= {rules['minimum']}")
        if "maximum" in rules and number > float(rules["maximum"]):
            errors.append(f"Property {path} must be <= {rules['maximum']}")
        if "exclusiveMinimum" in rules and number <= float(rules["exclusiveMinimum"]):
            errors.append(f"Property {path} must be > {rules['exclusiveMinimum']}")
        if "exclusiveMaximum" in rules and number >= float(rules["exclusiveMaximum"]):
            errors.append(f"Property {path} must be < {rules['exclusiveMaximum']}")

    if isinstance(value, str):
        if "minLength" in rules and len(value) < int(rules["minLength"]):
            errors.append(f"Property {path} length must be >= {rules['minLength']}")
        if "maxLength" in rules and len(value) > int(rules["maxLength"]):
            errors.append(f"Property {path} length must be <= {rules['maxLength']}")
        if "pattern" in rules and re.search(str(rules["pattern"]), value) is None:
            errors.append(f"Property {path} must match pattern {rules['pattern']!r}")

    if isinstance(value, dict):
        required = rules.get("required", [])
        properties = rules.get("properties", {})
        for key in required:
            if key not in value:
                errors.append(f"Missing required property: {path}.{key}")
        if rules.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"Unexpected property: {path}.{key}")
        for key, child_rules in properties.items():
            if key in value and isinstance(child_rules, dict):
                _validate_node(value[key], child_rules, f"{path}.{key}", errors)

    if isinstance(value, list):
        if "minItems" in rules and len(value) < int(rules["minItems"]):
            errors.append(f"Property {path} must contain at least {rules['minItems']} items")
        if "maxItems" in rules and len(value) > int(rules["maxItems"]):
            errors.append(f"Property {path} must contain at most {rules['maxItems']} items")
        item_rules = rules.get("items")
        if isinstance(item_rules, dict):
            for index, item in enumerate(value):
                _validate_node(item, item_rules, f"{path}[{index}]", errors)


def validate_case(case_data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """
    Summary:
        Validate a user case recursively against the dependency-free JSON Schema subset supported by this package.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with Changes No. 1-6 through 09.12.2024
        Clause: Package input infrastructure
        Annex: None
        Equation/Table: None
        Audit ID: AUDIT-INFRA-SCHEMA-001
        Normative status: no_code_explanatory

    Mathematical form:
        Recursive object/array traversal with required-key, type, enum/const, string, and finite numerical-bound checks.

    Parameters:
        case_data:
            Type: dict[str, Any]
            Unit: not applicable
            Meaning: Parsed user case JSON.
            Valid range: JSON object.
            Source: user input
        schema:
            Type: dict[str, Any]
            Unit: not applicable
            Meaning: Parsed package JSON schema.
            Valid range: Supported schema subset.
            Source: package schemas

    Returns:
        Type: list[str]
        Unit: validation errors
        Meaning: Empty list on success; otherwise path-aware validation messages.

    Assumptions:
        - Schemas use the supported local subset and do not require remote reference resolution.

    Sign convention:
        - Numerical bounds follow the schema exactly.

    Unit convention:
        - Units are encoded by schema/property semantics; the validator performs no unit conversion.

    Applicability:
        - All included package case schemas, including nested objects and arrays.

    Limitations:
        - This is not a complete JSON Schema engine; $ref, oneOf/anyOf/allOf, conditionals, formats and remote schemas are not implemented.

    Raises:
        TypeError: case_data or schema is not a dictionary.

    Examples:
        >>> validate_case({"x": [1.0]}, {"type":"object","required":["x"],"properties":{"x":{"type":"array","items":{"type":"number"}}}})
        []

    Tests:
        Unit tests:
            - tests/test_final_annex_and_release_consolidation.py::test_schema_validation_is_recursive_and_rejects_nan
        Validation cases:
            - CORE-RUN-001

    Implementation notes:
        - Booleans are not accepted as numbers or integers.
        - NaN and infinities are rejected recursively before numerical bounds are evaluated.
    """
    if not isinstance(case_data, dict) or not isinstance(schema, dict):
        raise TypeError("case_data and schema must be dictionaries")
    errors: list[str] = []
    _validate_node(case_data, schema, "$", errors)
    return errors
