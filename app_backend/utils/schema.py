from typing import Any

from fastapi import HTTPException


def normalize_input_schema(input_schema: dict[str, Any] | None) -> dict[str, Any]:
    if not input_schema:
        return {"type": "object", "properties": {}}

    if "type" in input_schema or "properties" in input_schema or "$schema" in input_schema:
        return input_schema

    properties = {}
    for name, schema in input_schema.items():
        if isinstance(schema, str):
            properties[name] = {"type": schema}
        elif isinstance(schema, dict):
            properties[name] = schema
        else:
            properties[name] = {"type": "string"}

    return {
        "type": "object",
        "properties": properties,
        "required": list(input_schema.keys()),
    }


def validate_input_against_schema(input_data: dict[str, Any], input_schema: dict[str, Any] | None) -> None:
    schema = normalize_input_schema(input_schema)
    missing = [field for field in schema.get("required", []) if input_data.get(field) in [None, ""]]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required input fields: {', '.join(missing)}")

    properties = schema.get("properties", {})
    for field, field_schema in properties.items():
        if field not in input_data or input_data[field] is None:
            continue
        expected_type = field_schema.get("type") if isinstance(field_schema, dict) else None
        value = input_data[field]
        if expected_type == "string" and not isinstance(value, str):
            raise HTTPException(status_code=400, detail=f"Input field '{field}' must be a string")
        if expected_type == "object" and not isinstance(value, dict):
            raise HTTPException(status_code=400, detail=f"Input field '{field}' must be an object")
        if expected_type == "array" and not isinstance(value, list):
            raise HTTPException(status_code=400, detail=f"Input field '{field}' must be an array")
