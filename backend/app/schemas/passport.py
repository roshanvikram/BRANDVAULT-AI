from pydantic import BaseModel
from typing import Optional, Any, Dict
import datetime

class BrandPassportResponse(BaseModel):
    id: str
    passport_number: str
    submission_id: str
    brand_name: str
    content_title: str
    content_hash: str
    guideline_version: str
    verification_status: str
    final_score: int
    audited_by: str
    passport_data: Dict[str, Any]
    issued_at: datetime.datetime

    class Config:
        from_attributes = True

class AgentRunResponse(BaseModel):
    id: str
    agent_name: str
    task_name: str
    status: str
    execution_time_ms: int
    tokens_used: int
    input_preview: str
    output_preview: str
    event_details: Dict[str, Any]
    created_at: datetime.datetime

    class Config:
        from_attributes = True

