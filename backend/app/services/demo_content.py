"""
Demo campaigns for a fresh NOVA TECH workspace.

A new deployment (e.g. Render's free plan, whose disk resets on every restart)
starts with brand knowledge and demo users but no campaigns, so every screen
would be empty. This seeds a small set of example campaigns ONLY when the NOVA
TECH workspace has no submissions at all, so an existing database is never
touched.

Nothing here is invented output: each campaign is run through the real
ContentAnalyzerService (deterministic engine, no AI call, so results are the
same on every restart), and the example review decisions go through the real
PassportService. Those decisions are clearly marked as demo data in the
reviewer comment, because no person actually made them.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from backend.app.models.submission import Submission
from backend.app.services.analyzer import ContentAnalyzerService
from backend.app.services.llm import NullProvider
from backend.app.services.passport_service import PassportService
from backend.app.services.seed import NOVA_ORG_ID

DEMO_NOTE = "[Demo data] Example decision seeded at startup so the review and Brand Passport flow can be shown. No person made this decision."

# (title, department, author, copy, demo decision or None)
CAMPAIGNS = [
    ("NovaBook AI Pro 16 — Launch Announcement", "Marketing", "NOVA Creator",
     "Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only ₹69,999!",
     "Revision Requested"),
    ("NovaBook AI Pro 16 — Product Page Hero", "Web", "NOVA Creator",
     "Meet NovaBook AI Pro 16. The NovaCore N10 AI Engine delivers up to 45 TOPS sustained AI processing performance, "
     "with up to 18 hours mixed productivity workload on a single charge. Available at ₹79,999 with a "
     "2-Year On-Site Limited Hardware Warranty.",
     "Approved"),
    ("Festive Season Social Post", "Social", "NOVA Creator",
     "This festive season, grab the NovaBook AI Pro 16 — powerful, stylish and cheap! Only ₹79,999. Hurry!!!",
     None),
    ("Retail Partner Email — Pre-order Bonus", "Retail", "NOVA Creator",
     "Pre-order the NovaBook AI Pro 16 today and receive a complimentary NovaSleeve accessory with every pre-order. "
     "Launch price ₹79,999.",
     None),
    ("Comparison Banner Copy", "Marketing", "NOVA Creator",
     "NovaBook AI Pro 16 is 10x faster than every competitor and the world's fastest laptop for creators.",
     None),
    ("Enterprise Newsletter — AI Productivity", "Enterprise", "NOVA Creator",
     "For enterprise teams, NovaBook AI Pro 16 brings up to 45 TOPS sustained AI processing performance and "
     "up to 18 hours mixed productivity workload, backed by a 2-Year On-Site Limited Hardware Warranty.",
     None),
    ("Campus Offer Landing Page", "Web", "NOVA Creator",
     "Students: the NovaBook AI Pro 16 is now just ₹74,999 for a limited time. The world's fastest way to study!",
     None),
]


def seed_demo_campaigns(db: Session) -> int:
    """Create the demo campaigns if the NOVA TECH workspace has none. Returns how many were created."""
    if db.query(Submission).filter(Submission.org_id == NOVA_ORG_ID).count() > 0:
        return 0
    analyzer = ContentAnalyzerService(db, llm_provider=NullProvider())
    created: List[Submission] = []
    for title, department, author, copy, _ in CAMPAIGNS:
        sub = analyzer.analyze_submission(NOVA_ORG_ID, title, copy, author_name=author)
        sub.department = department
        created.append(sub)
    db.commit()

    passports = PassportService(db)
    for sub, (_, _, _, _, decision) in zip(created, CAMPAIGNS):
        if decision:
            passports.submit_review_decision(sub.id, decision, DEMO_NOTE,
                                             reviewer_name="NOVA Reviewer (demo)", reviewer_role="Reviewer")
    db.commit()
    return len(created)
