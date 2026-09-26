from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    image_id: str = Field(..., pattern=r"^[A-Za-z0-9\-]{3,48}$")
    image_b_id: Optional[str] = Field(None, pattern=r"^[A-Za-z0-9\-]{3,48}$")
    session_id: Optional[str] = Field(None, pattern=r"^[A-Za-z0-9\-]{3,48}$")


class AnalyzeRequest(BaseModel):
    analysis_type: str = Field("object_detection", pattern=r"^(object_detection|segmentation|change_detection|image_understanding)$")
    image_id: str = Field(..., pattern=r"^[A-Za-z0-9\-]{3,48}$")
    image_b_id: Optional[str] = Field(None, pattern=r"^[A-Za-z0-9\-]{3,48}$")
    target: Optional[str] = Field(None, max_length=40)
    session_id: Optional[str] = Field(None, pattern=r"^[A-Za-z0-9\-]{3,48}$")


class PipelineStep(BaseModel):
    stage: str
    detail: str
    ms: float


class AnalysisRecord(BaseModel):
    id: str
    created: str
    query: str
    intent: dict[str, Any]
    answer: str
    confidence: Optional[float] = None
    confidence_tier: str
    status: str
    evidence: dict[str, Any]
    visualization: dict[str, Any]
    pipeline: list[PipelineStep]
    image_ids: dict[str, Optional[str]]
    engine_label: str
    is_demo: bool
    disclaimer: str
    root_id: Optional[str] = None
    warnings: list[str] = []
    suggestions: list[str] = []


class ErrorBody(BaseModel):
    code: str
    message: str
