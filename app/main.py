import json
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Comparison, Finding, Specification, get_db, init_db
from app.schemas import (
    ComparisonRequest,
    ComparisonResponse,
    SpecificationResponse,
)
from app.services.diff_engine import compare_specs
from app.services.risk import risk_score

app = FastAPI(title=settings.app_name, version="0.1.0", description="OpenAPI compatibility analysis API")
DB = Annotated[Session, Depends(get_db)]

init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/specs", response_model=SpecificationResponse, status_code=status.HTTP_201_CREATED)
def upload_spec(name: str, file: UploadFile = File(...), db: Session = Depends(get_db)) -> Specification:
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(400, "Only OpenAPI JSON files are supported")
    raw = file.file.read(settings.max_upload_bytes + 1)
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(413, "Specification file is too large")
    try:
        content = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Uploaded file is not valid JSON") from exc
    if content.get("openapi", "").split(".")[0] != "3":
        raise HTTPException(400, "Only OpenAPI 3 specifications are supported")
    version = str(content.get("info", {}).get("version", "unknown"))
    spec = Specification(name=name, version=version, content=content)
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


@app.get("/api/v1/specs", response_model=list[SpecificationResponse])
def list_specs(db: DB) -> list[Specification]:
    return db.query(Specification).order_by(Specification.created_at.desc()).all()


@app.post("/api/v1/comparisons", response_model=ComparisonResponse, status_code=status.HTTP_201_CREATED)
def compare(request: ComparisonRequest, db: DB) -> dict:
    old = db.get(Specification, request.old_spec_id)
    new = db.get(Specification, request.new_spec_id)
    if not old or not new:
        raise HTTPException(404, "Both specifications must exist")
    data = compare_specs(old.content, new.content)
    comparison = Comparison(old_spec_id=old.id, new_spec_id=new.id, risk_score=risk_score(data))
    comparison.findings = [Finding(**item.__dict__) for item in data]
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    counts = {"critical": 0, "major": 0, "minor": 0, "warning": 0, "info": 0}
    for finding in comparison.findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return {"id": comparison.id, "status": comparison.status, "risk_score": comparison.risk_score, "summary": counts, "findings": comparison.findings}


@app.get("/api/v1/comparisons/{comparison_id}", response_model=ComparisonResponse)
def get_comparison(comparison_id: str, db: DB) -> dict:
    comparison = db.get(Comparison, comparison_id)
    if not comparison:
        raise HTTPException(404, "Comparison not found")
    counts = {"critical": 0, "major": 0, "minor": 0, "warning": 0, "info": 0}
    for finding in comparison.findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return {"id": comparison.id, "status": comparison.status, "risk_score": comparison.risk_score, "summary": counts, "findings": comparison.findings}
