import json
from pathlib import Path

from app.services.diff_engine import compare_specs
from app.services.risk import risk_score

ROOT = Path(__file__).parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "examples" / name).read_text())


def test_detects_breaking_and_non_breaking_changes():
    findings = compare_specs(load("orders-v1.json"), load("orders-v2.json"))
    categories = {finding.category for finding in findings}
    assert "response_field_removed" in categories
    assert "response_type_changed" in categories
    assert "required_request_field_added" in categories
    assert "endpoint_added" in categories
    assert risk_score(findings) > 0


def test_empty_specs_have_no_findings():
    assert compare_specs({"paths": {}}, {"paths": {}}) == []
