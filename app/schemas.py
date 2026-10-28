from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SpecificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: str
    created_at: datetime


class ComparisonRequest(BaseModel):
    old_spec_id: str
    new_spec_id: str


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    severity: str
    category: str
    path: str
    method: str
    message: str
    old_value: Any | None = None
    new_value: Any | None = None
    recommendation: str


class ComparisonResponse(BaseModel):
    id: str
    status: str
    risk_score: int
    summary: dict[str, int]
    findings: list[FindingResponse]


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Specification not found"])
