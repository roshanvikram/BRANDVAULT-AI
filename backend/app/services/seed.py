import uuid
import datetime
from sqlalchemy.orm import Session
from backend.app.models.brand import Organization, BrandRule, ApprovedFact, TerminologyRule, BrandGuideline, DocumentChunk
from backend.app.models.user import User, ROLE_ADMIN, ROLE_CREATOR, ROLE_REVIEWER
from backend.app.core.security import hash_password

NOVA_ORG_ID = "nova-tech-org-001"

# Demo accounts for the NOVA TECH workspace (documented in README/DEPLOYMENT).
# Safe for the judging demo only — not production credentials.
DEMO_USERS = [
    {"email": "admin@novatech.demo", "full_name": "NOVA Admin", "role": ROLE_ADMIN, "password": "Admin@2026"},
    {"email": "creator@novatech.demo", "full_name": "NOVA Creator", "role": ROLE_CREATOR, "password": "Creator@2026"},
    {"email": "reviewer@novatech.demo", "full_name": "NOVA Reviewer", "role": ROLE_REVIEWER, "password": "Reviewer@2026"},
]

def seed_sample_brand(db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.id == NOVA_ORG_ID).first()
    if org:
        return org

    # 1. Create Organization
    org = Organization(
        id=NOVA_ORG_ID,
        name="NOVA TECH",
        slug="nova-tech"
    )
    db.add(org)

    # 2. Approved Guidelines Document
    guideline_id = str(uuid.uuid4())
    guideline = BrandGuideline(
        id=guideline_id,
        org_id=NOVA_ORG_ID,
        filename="NOVA_TECH_Brand_Governance_2026.pdf",
        file_path="/guidelines/NOVA_TECH_Brand_Governance_2026.pdf",
        file_type="pdf",
        file_size_bytes=1048576,
        total_pages=14,
        status="processed",
        raw_text="""NOVA TECH BRAND GOVERNANCE MANUAL (2026 EDITION)
Section 1: Pricing Policy
NovaBook AI Pro 16 official launch price is strictly ₹79,999 (inclusive of taxes). Under no circumstances may promotional copy state a lower price like ₹69,999 without executive authorization.

Section 2: Promotional & Comparative Claims
All performance assertions must be strictly verifiable. Claims claiming to be 'world's fastest' or '10x faster than every competitor' violate advertising standards LP-41 and are categorically forbidden.

Section 3: Tone & Terminology
Voice must be understated, mathematically precise, and confident. Never use sensationalist hype or informal slang. Avoid terms like 'cheap' or 'magic'."""
    )
    db.add(guideline)

    # Chunks
    chunk1 = DocumentChunk(
        id=str(uuid.uuid4()),
        guideline_id=guideline_id,
        page_number=3,
        chunk_index=0,
        content="Pricing Policy: NovaBook AI Pro 16 official launch price is strictly ₹79,999 (inclusive of taxes). Promotional claims quoting ₹69,999 or lower are strictly prohibited without written CMO clearance."
    )
    chunk2 = DocumentChunk(
        id=str(uuid.uuid4()),
        guideline_id=guideline_id,
        page_number=7,
        chunk_index=1,
        content="Advertising Claims & Competitor Comparisons: Absolute claims such as 'world's fastest AI laptop' and comparative claims like '10x faster than every competitor' require independent laboratory benchmark verification and are forbidden in general marketing copy."
    )
    chunk3 = DocumentChunk(
        id=str(uuid.uuid4()),
        guideline_id=guideline_id,
        page_number=2,
        chunk_index=2,
        content="Brand Voice & Tone: The NOVA TECH voice is calm, authoritative, understated, and mathematically precise. Avoid excessive exclamation marks and hyperbolic hype."
    )
    db.add_all([chunk1, chunk2, chunk3])

    # 3. Approved Facts
    facts = [
        ApprovedFact(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Pricing",
            fact_key="NovaBook AI Pro 16 Launch Price",
            fact_value="₹79,999",
            verification_source="Pricing Policy Master Document 2026 (DocRef #P-2026)",
            notes="Official authorized launch retail price. Valid across all national distributors."
        ),
        ApprovedFact(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Product Specification",
            fact_key="NovaCore N10 AI Engine",
            fact_value="45 TOPS NPU with sustained 3.8 GHz clock speed",
            verification_source="Engineering Specification Hardware Sheet v1.4",
            notes="Benchmarked against industry ISO standards."
        ),
        ApprovedFact(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Product Specification",
            fact_key="Standard Battery Endurance",
            fact_value="Up to 18 hours mixed productivity workload",
            verification_source="Lab Battery Benchmark Test 2026-B8",
            notes="Tested under standard 150 nits display brightness."
        ),
        ApprovedFact(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Legal & Warranty",
            fact_key="Standard Customer Warranty",
            fact_value="2-Year On-Site Limited Hardware Warranty",
            verification_source="Customer Terms & Conditions LP-41",
            notes="Includes accidental damage protection in Year 1."
        )
    ]
    db.add_all(facts)

    # 4. Brand Rules
    rules = [
        BrandRule(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Pricing",
            title="Authorized Product Pricing Rule",
            rule_text="The authorized launch price for NovaBook AI Pro is ₹79,999. Unauthorized discount prices (e.g., ₹69,999) constitute a critical brand violation.",
            severity="CRITICAL",
            source_document="NOVA_TECH_Brand_Governance_2026.pdf",
            page_reference=3,
            is_active=True,
            is_confirmed=True
        ),
        BrandRule(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Claim",
            title="Superlative Claim Prohibition",
            rule_text="Unsubstantiated absolute performance superlatives such as 'world's fastest AI laptop' are strictly forbidden without independent verified audit benchmarks.",
            severity="CRITICAL",
            source_document="NOVA_TECH_Brand_Governance_2026.pdf",
            page_reference=7,
            is_active=True,
            is_confirmed=True
        ),
        BrandRule(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Claim",
            title="Comparative Competitor Claim Rule",
            rule_text="Broad comparative claims such as '10x faster than every competitor' require specific cited test methodologies and named comparison parameters.",
            severity="CRITICAL",
            source_document="NOVA_TECH_Brand_Governance_2026.pdf",
            page_reference=7,
            is_active=True,
            is_confirmed=True
        ),
        BrandRule(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Tone & Voice",
            title="Understated & Precise Tone",
            rule_text="Marketing communications must maintain a calm, precise, and understated tone. Exclamation points and sensationalist hype words must be avoided.",
            severity="WARNING",
            source_document="NOVA_TECH_Brand_Governance_2026.pdf",
            page_reference=2,
            is_active=True,
            is_confirmed=True
        ),
        BrandRule(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            category="Terminology",
            title="Strict Product Brand Naming",
            rule_text="The product must always be cited as 'NovaBook AI Pro 16' or 'NovaBook AI Pro'. Do not use diminutive terms like 'budget laptop' or 'cheap AI device'.",
            severity="WARNING",
            source_document="NOVA_TECH_Brand_Governance_2026.pdf",
            page_reference=5,
            is_active=True,
            is_confirmed=True
        )
    ]
    db.add_all(rules)

    # 5. Terminology Rules
    terms = [
        TerminologyRule(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            prohibited_term="world's fastest",
            preferred_term="exceptionally high-performance / benchmark-leading",
            explanation="Unsubstantiated superlative that risks regulatory scrutiny and breaches advertising standards.",
            is_active=True
        ),
        TerminologyRule(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            prohibited_term="10x faster than every competitor",
            preferred_term="up to 45 TOPS sustained AI processing performance",
            explanation="Sweeping competitor comparison without verified independent lab audit.",
            is_active=True
        ),
        TerminologyRule(
            id=str(uuid.uuid4()),
            org_id=NOVA_ORG_ID,
            prohibited_term="cheap",
            preferred_term="exceptional enterprise value / highly accessible",
            explanation="Brand tone mandates an enterprise, high-craft aesthetic; 'cheap' degrades brand equity.",
            is_active=True
        )
    ]
    db.add_all(terms)

    db.commit()
    db.refresh(org)
    return org


def augment_integrity_demo(db: Session) -> None:
    """Idempotently add data that exercises the OUTDATED claim path.

    `seed_sample_brand` returns early once the org exists, so this augmenter
    runs separately on every startup and only inserts what is missing. It adds
    a time-bound promotional fact whose validity has lapsed, plus a matching
    guideline chunk, so a judge can type content referencing the expired
    pre-order bonus and see a genuine OUTDATED verification (distinct from a
    pricing contradiction). See TESTING_PLAN.md.
    """
    org = db.query(Organization).filter(Organization.id == NOVA_ORG_ID).first()
    if not org:
        return

    key = "Launch Pre-Order Bonus Offer"
    existing = (
        db.query(ApprovedFact)
        .filter(ApprovedFact.org_id == NOVA_ORG_ID, ApprovedFact.fact_key == key)
        .first()
    )
    if existing:
        return

    db.add(ApprovedFact(
        id=str(uuid.uuid4()),
        org_id=NOVA_ORG_ID,
        category="Promotion",
        fact_key=key,
        fact_value="Complimentary NovaSleeve accessory with every pre-order",
        verification_source="Q4 2024 Launch Promotion Memo (DocRef #PR-2024-11)",
        notes="Introductory pre-order incentive for the 2024 launch window.",
        valid_until=datetime.datetime(2024, 12, 31, 23, 59, 59),
        superseded_by="Promotion concluded. No active pre-order bonus exists for the 2026 campaign.",
    ))

    # A guideline chunk so retrieval has a real passage to cite for this topic.
    guideline = (
        db.query(BrandGuideline)
        .filter(BrandGuideline.org_id == NOVA_ORG_ID)
        .first()
    )
    if guideline:
        already = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.guideline_id == guideline.id, DocumentChunk.page_number == 11)
            .first()
        )
        if not already:
            db.add(DocumentChunk(
                id=str(uuid.uuid4()),
                guideline_id=guideline.id,
                page_number=11,
                chunk_index=3,
                content="Promotional Offers: The pre-order bonus (complimentary NovaSleeve accessory) applied only to the 2024 launch window and expired on 31 December 2024. It must not be advertised in current 2026 campaign material.",
            ))

    db.commit()


def seed_demo_users(db: Session) -> None:
    """Idempotently create the NOVA TECH demo accounts (Admin/Creator/Reviewer)."""
    org = db.query(Organization).filter(Organization.id == NOVA_ORG_ID).first()
    if not org:
        return
    created = False
    for spec in DEMO_USERS:
        if db.query(User).filter(User.email == spec["email"]).first():
            continue
        salt, pwd_hash = hash_password(spec["password"])
        db.add(User(
            id=str(uuid.uuid4()),
            email=spec["email"],
            full_name=spec["full_name"],
            role=spec["role"],
            org_id=NOVA_ORG_ID,
            salt=salt,
            password_hash=pwd_hash,
        ))
        created = True
    if created:
        db.commit()

