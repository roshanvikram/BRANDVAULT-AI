from pydantic import BaseModel
from typing import Optional, Any
import datetime

class ApiResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    tagline: str
    version: str
    database: str
    timestamp: str

