"""
BRANDVAULT AI — Enterprise Model Context Protocol (MCP) Server
Allows external AI agents, IDEs, and LLMs to interact with BRANDVAULT brand governance tools.

Tools provided:
1. get_brand_profile
2. search_brand_guidelines
3. verify_marketing_claim
4. get_approved_asset
5. analyse_content
6. create_review_request
7. get_review_status
"""

import sys
import os
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.db.session import SessionLocal
from backend.app.models.brand import Organization, BrandRule, ApprovedFact, TerminologyRule, DocumentChunk
from backend.app.models.submission import Submission, ClaimVerification
from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services.passport_service import PassportService
from backend.app.services.seed import seed_sample_brand, NOVA_ORG_ID

def get_brand_profile(org_id: str = NOVA_ORG_ID) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        seed_sample_brand(db)
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {"error": f"Organization {org_id} not found"}
        return {
            "organization_id": org.id,
            "organization_name": org.name,
            "rules_count": len(org.rules),
            "facts_count": len(org.facts),
            "guidelines_count": len(org.guidelines),
            "brand_identity": "Understated, precise, enterprise, monochrome"
        }
    finally:
        db.close()

def search_brand_guidelines(query: str, org_id: str = NOVA_ORG_ID) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        chunks = db.query(DocumentChunk).all()
        results = []
        for c in chunks:
            if any(w.lower() in c.content.lower() for w in query.split() if len(w) > 3):
                results.append({
                    "chunk_id": c.id,
                    "page": c.page_number,
                    "content": c.content
                })
        return results[:5]
    finally:
        db.close()

def verify_marketing_claim(claim_text: str, org_id: str = NOVA_ORG_ID) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        service = ContentAnalyzerService(db)
        sub = service.analyze_submission(
            org_id=org_id,
            title="MCP Claim Verification",
            content=claim_text,
            author_name="MCP Enterprise Agent"
        )
        verifications = [
            {
                "claim": c.claim_text,
                "status": c.status,
                "category": c.category,
                "explanation": c.explanation,
                "evidence": c.evidence_text
            }
            for c in sub.claim_verifications
        ]
        return {
            "score": sub.overall_score,
            "findings_count": len(sub.findings),
            "claims": verifications
        }
    finally:
        db.close()

def get_approved_asset(category: str = "Pricing", org_id: str = NOVA_ORG_ID) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        facts = db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()
        return [
            {
                "key": f.fact_key,
                "value": f.fact_value,
                "source": f.verification_source
            }
            for f in facts if category.lower() in f.category.lower() or category == "all"
        ]
    finally:
        db.close()

def analyse_content(title: str, copy_text: str, org_id: str = NOVA_ORG_ID) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        service = ContentAnalyzerService(db)
        sub = service.analyze_submission(
            org_id=org_id,
            title=title,
            content=copy_text,
            author_name="MCP Client"
        )
        return {
            "submission_id": sub.id,
            "title": sub.title,
            "overall_score": sub.overall_score,
            "status": sub.status,
            "findings": [
                {
                    "issue_category": f.issue_category,
                    "severity": f.severity,
                    "original_text": f.original_text,
                    "explanation": f.explanation,
                    "suggested_correction": f.suggested_correction,
                    "confidence": f.confidence
                }
                for f in sub.findings
            ],
            "claims": [
                {
                    "claim": c.claim_text,
                    "status": c.status,
                    "explanation": c.explanation
                }
                for c in sub.claim_verifications
            ]
        }
    finally:
        db.close()

def create_review_request(submission_id: str, requester_name: str = "Creator") -> Dict[str, Any]:
    db = SessionLocal()
    try:
        sub = db.query(Submission).filter(Submission.id == submission_id).first()
        if not sub:
            return {"error": "Submission not found"}
        sub.status = "Pending Review"
        db.commit()
        return {
            "submission_id": sub.id,
            "status": sub.status,
            "message": "Campaign submitted for formal human review."
        }
    finally:
        db.close()

def get_review_status(submission_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        sub = db.query(Submission).filter(Submission.id == submission_id).first()
        if not sub:
            return {"error": "Submission not found"}
        return {
            "submission_id": sub.id,
            "title": sub.title,
            "status": sub.status,
            "version": sub.version,
            "overall_score": sub.overall_score,
            "has_passport": sub.passport is not None,
            "passport_number": sub.passport.passport_number if sub.passport else None
        }
    finally:
        db.close()

if __name__ == "__main__":
    print("BRANDVAULT AI MCP Server initialized. Running self-test...")
    profile = get_brand_profile()
    print("Brand Profile:", json.dumps(profile, indent=2))
    sample = verify_marketing_claim("NovaBook AI Pro 16 launch price is ₹69,999!")
    print("Sample Claim Verification:", json.dumps(sample, indent=2))
