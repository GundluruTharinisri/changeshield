from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReplayResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    method: str
    path: str
    expected_status: int
    actual_status: int | None
    response_time_ms: float
    passed: bool
    error_message: str | None


class ReplayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_url: str
    status: str
    total_requests: int
    passed_requests: int
    failed_requests: int
    created_at: datetime
    completed_at: datetime | None
    results: list[ReplayResultResponse]
