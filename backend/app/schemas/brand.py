from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class OrganizationBase(BaseModel):
    name: str
    slug: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime.datetime
    guidelines_count: int = 0
    rules_count: int = 0
    facts_count: int = 0

    class Config:
        from_attributes = True


class BrandRuleBase(BaseModel):
    category: str
    title: str
    rule_text: str
    severity: str = "CRITICAL" # CRITICAL, WARNING, SUGGESTION
    source_document: Optional[str] = None
    page_reference: Optional[int] = None
    is_active: bool = True
    is_confirmed: bool = True

class BrandRuleCreate(BrandRuleBase):
    pass

class BrandRuleResponse(BrandRuleBase):
    id: str
    org_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class ApprovedFactBase(BaseModel):
    category: str
    fact_key: str
    fact_value: str
    verification_source: str
    notes: Optional[str] = None

class ApprovedFactCreate(ApprovedFactBase):
    pass

class ApprovedFactResponse(ApprovedFactBase):
    id: str
    org_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TerminologyRuleBase(BaseModel):
    prohibited_term: str
    preferred_term: str
    explanation: str
    is_active: bool = True

class TerminologyRuleCreate(TerminologyRuleBase):
    pass

class TerminologyRuleResponse(TerminologyRuleBase):
    id: str
    org_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class BrandGuidelineResponse(BaseModel):
    id: str
    org_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    total_pages: int
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True
