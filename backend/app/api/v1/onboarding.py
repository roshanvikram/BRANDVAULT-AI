"""
Onboarding / setup status API (Round 2 / R2-1).

Returns REAL setup completion for an organisation, computed from persisted
records — never a hardcoded "done". Each step reports whether it is satisfied,
a live count, and where to complete it. The guided onboarding wizard renders
directly from this, so progress always reflects the actual saved configuration.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.seed import NOVA_ORG_ID
from backend.app.models.brand import Organization, BrandGuideline, BrandRule, ApprovedFact, TerminologyRule
from backend.app.models.user import User, ROLE_ADMIN, ROLE_REVIEWER
from backend.app.models.submission import Submission
from backend.app.models.passport import BrandPassport

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get("/status")
def onboarding_status(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    guidelines = db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id).count()
    rules_total = db.query(BrandRule).filter(BrandRule.org_id == org_id).count()
    rules_confirmed = db.query(BrandRule).filter(BrandRule.org_id == org_id, BrandRule.is_confirmed == True).count()  # noqa: E712
    facts = db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).count()
    terms = db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id).count()
    reviewers = db.query(User).filter(
        User.org_id == org_id, User.role.in_([ROLE_ADMIN, ROLE_REVIEWER])
    ).count()
    submissions = db.query(Submission).filter(Submission.org_id == org_id).count()
    passports = (
        db.query(BrandPassport)
        .join(Submission, BrandPassport.submission_id == Submission.id)
        .filter(Submission.org_id == org_id)
        .count()
    )

    steps = [
        {"key": "organization", "label": "Create your organisation",
         "done": True, "count": None, "href": "/settings",
         "hint": f"Workspace '{org.name}' is active."},
        {"key": "guidelines", "label": "Upload brand guidelines",
         "done": guidelines > 0, "count": guidelines, "href": "/brand-dna",
         "hint": "Add a PDF or text guideline so rules can be extracted."},
        {"key": "rules", "label": "Review & confirm brand rules",
         "done": rules_confirmed > 0, "count": rules_confirmed, "total": rules_total, "href": "/brand-dna",
         "hint": "Confirm extracted rules before they become active in analysis."},
        {"key": "facts", "label": "Add approved product facts",
         "done": facts > 0, "count": facts, "href": "/claim-dna",
         "hint": "Approved facts are the ground truth ClaimDNA verifies against."},
        {"key": "terminology", "label": "Define approved terminology",
         "done": terms > 0, "count": terms, "href": "/brand-dna",
         "hint": "Prohibited-vs-preferred terms guide tone and wording checks."},
        {"key": "reviewers", "label": "Have an authorised reviewer",
         "done": reviewers > 0, "count": reviewers, "href": "/settings",
         "hint": "Only Reviewers/Administrators can approve content."},
        {"key": "sample_test", "label": "Run your first content analysis",
         "done": submissions > 0, "count": submissions, "href": "/content-intelligence",
         "hint": "Analyse a piece of marketing copy against your brand DNA."},
        {"key": "passport", "label": "Issue a Brand Passport",
         "done": passports > 0, "count": passports, "href": "/approval-hub",
         "hint": "Approve analysed content to certify it with a Brand Passport."},
    ]

    done_count = sum(1 for s in steps if s["done"])
    completion = round(done_count / len(steps) * 100)

    return {
        "org": {"id": org.id, "name": org.name},
        "steps": steps,
        "completed": done_count,
        "total": len(steps),
        "completion": completion,
        # NOVA TECH ships pre-seeded as an explorable demo; flagged so the UI can label it.
        "is_demo": org.id == NOVA_ORG_ID,
    }
