from dataclasses import dataclass
from typing import Any


@dataclass
class FindingData:
    severity: str
    category: str
    path: str
    method: str
    message: str
    old_value: Any = None
    new_value: Any = None
    recommendation: str = "Review this change for consumer compatibility."


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


def _schema_type(schema: dict[str, Any] | None) -> Any:
    if not schema:
        return None
    return schema.get("type") or ("$ref:" + schema["$ref"] if "$ref" in schema else None)


def _properties(schema: dict[str, Any] | None) -> dict[str, Any]:
    return (schema or {}).get("properties", {})


def _required(schema: dict[str, Any] | None) -> set[str]:
    return set((schema or {}).get("required", []))


def _body_schema(operation: dict[str, Any]) -> dict[str, Any] | None:
    return operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")


def _response_schema(operation: dict[str, Any], status: str = "200") -> dict[str, Any] | None:
    response = operation.get("responses", {}).get(status, {})
    return response.get("content", {}).get("application/json", {}).get("schema")


def compare_specs(old: dict[str, Any], new: dict[str, Any]) -> list[FindingData]:
    findings: list[FindingData] = []
    old_paths = old.get("paths", {})
    new_paths = new.get("paths", {})

    for path, old_item in old_paths.items():
        if path not in new_paths:
            findings.append(FindingData("critical", "endpoint_removed", path, "*", f"Endpoint '{path}' was removed.", old_item, None, "Keep the endpoint or introduce a new API version."))
            continue
        new_item = new_paths[path]
        for method in sorted(set(old_item) & HTTP_METHODS):
            if method not in new_item:
                findings.append(FindingData("critical", "method_removed", path, method.upper(), f"{method.upper()} {path} was removed.", old_item[method], None, "Keep the method or introduce a new API version."))
                continue
            old_op, new_op = old_item[method], new_item[method]
            _compare_request_body(findings, path, method, old_op, new_op)
            _compare_responses(findings, path, method, old_op, new_op)

    for path, new_item in new_paths.items():
        if path not in old_paths:
            findings.append(FindingData("info", "endpoint_added", path, "*", f"New endpoint '{path}' was added.", None, new_item, "Add consumer documentation and tests."))
        else:
            for method in sorted(set(new_item) - set(old_paths[path])):
                if method in HTTP_METHODS:
                    findings.append(FindingData("info", "method_added", path, method.upper(), f"New method {method.upper()} {path} was added.", None, new_item[method], "Add consumer documentation and tests."))
    return findings


def _compare_request_body(findings: list[FindingData], path: str, method: str, old_op: dict[str, Any], new_op: dict[str, Any]) -> None:
    old_schema, new_schema = _body_schema(old_op), _body_schema(new_op)
    old_props, new_props = _properties(old_schema), _properties(new_schema)
    for field in sorted(_required(new_schema) - _required(old_schema)):
        if field in new_props:
            findings.append(FindingData("major", "required_request_field_added", path, method.upper(), f"Request field '{field}' became required.", False, True, "Keep the field optional or introduce a new API version."))
    for field in sorted(set(old_props) & set(new_props)):
        old_type, new_type = _schema_type(old_props[field]), _schema_type(new_props[field])
        if old_type != new_type:
            findings.append(FindingData("major", "request_type_changed", path, method.upper(), f"Request field '{field}' changed type from '{old_type}' to '{new_type}'.", old_type, new_type, "Preserve the old type or introduce a new API version."))


def _compare_responses(findings: list[FindingData], path: str, method: str, old_op: dict[str, Any], new_op: dict[str, Any]) -> None:
    old_responses, new_responses = old_op.get("responses", {}), new_op.get("responses", {})
    for status in sorted(set(old_responses) - set(new_responses)):
        findings.append(FindingData("major", "response_status_removed", path, method.upper(), f"Response status '{status}' was removed.", old_responses[status], None, "Continue returning the status or document the migration."))
    for status in sorted(set(old_responses) & set(new_responses)):
        old_schema, new_schema = _response_schema(old_op, status), _response_schema(new_op, status)
        old_props, new_props = _properties(old_schema), _properties(new_schema)
        for field in sorted(set(old_props) - set(new_props)):
            findings.append(FindingData("critical", "response_field_removed", path, method.upper(), f"Response property '{field}' was removed for status {status}.", old_props[field], None, "Keep the field for backward compatibility."))
        for field in sorted(set(old_props) & set(new_props)):
            old_type, new_type = _schema_type(old_props[field]), _schema_type(new_props[field])
            if old_type != new_type:
                findings.append(FindingData("critical", "response_type_changed", path, method.upper(), f"Response property '{field}' changed type from '{old_type}' to '{new_type}'.", old_type, new_type, "Preserve the old type or introduce a new API version."))
        for field in sorted(set(new_props) - set(old_props)):
            if field not in _required(new_schema):
                findings.append(FindingData("info", "optional_response_field_added", path, method.upper(), f"Optional response property '{field}' was added.", None, new_props[field], "Ensure consumers ignore unknown fields."))
