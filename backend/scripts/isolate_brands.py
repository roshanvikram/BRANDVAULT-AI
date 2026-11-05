import sys, os
sys.path.insert(0, os.path.abspath("."))
import uuid
import datetime
from backend.app.db.session import SessionLocal
from backend.app.models.brand import Organization, BrandGuideline, DocumentChunk, BrandRule, ApprovedFact, TerminologyRule
from backend.app.models.user import User, ROLE_ADMIN, ROLE_CREATOR, ROLE_REVIEWER
from backend.app.core.security import hash_password

def run_isolation():
    db = SessionLocal()

    # 1. Ensure VORTEXA TECHNOLOGIES organization exists
    vortexa = db.query(Organization).filter(Organization.id == 'vortexa-tech-org-002').first()
    if not vortexa:
        vortexa = Organization(
            id='vortexa-tech-org-002',
            name='VORTEXA TECHNOLOGIES',
            slug='vortexa-technologies'
        )
        db.add(vortexa)
        db.commit()
        print('Created VORTEXA TECHNOLOGIES organization.')
    else:
        print('VORTEXA TECHNOLOGIES organization already exists.')

    # 2. Add demo users for VORTEXA
    for spec in [
        {"email": "admin@vortexa.demo", "full_name": "VORTEXA Admin", "role": ROLE_ADMIN, "password": "Admin@2026"},
        {"email": "creator@vortexa.demo", "full_name": "VORTEXA Creator", "role": ROLE_CREATOR, "password": "Creator@2026"},
        {"email": "reviewer@vortexa.demo", "full_name": "VORTEXA Reviewer", "role": ROLE_REVIEWER, "password": "Reviewer@2026"},
    ]:
        if not db.query(User).filter(User.email == spec["email"]).first():
            salt, pwd_hash = hash_password(spec["password"])
            db.add(User(
                id=str(uuid.uuid4()),
                org_id='vortexa-tech-org-002',
                email=spec["email"],
                full_name=spec["full_name"],
                role=spec["role"],
                salt=salt,
                password_hash=pwd_hash,
            ))
            db.commit()
            print(f'Created VORTEXA demo user: {spec["email"]}')

    # 3. Clean up duplicates and reassign VORTEXA guidelines
    v_guidelines = db.query(BrandGuideline).filter(BrandGuideline.filename.like('%VORTEXA%')).all()
    print(f'Found {len(v_guidelines)} VORTEXA guidelines.')

    if len(v_guidelines) > 1:
        primary_vortexa_gl = v_guidelines[0]
        primary_vortexa_gl.org_id = 'vortexa-tech-org-002'
        for dup in v_guidelines[1:]:
            db.delete(dup)
        db.commit()
        print('Removed duplicate VORTEXA guidelines. Kept primary.')
    elif len(v_guidelines) == 1:
        v_guidelines[0].org_id = 'vortexa-tech-org-002'
        db.commit()
        print('Reassigned VORTEXA guideline to vortexa-tech-org-002.')

    # Reassign chunks belonging to vortexa guideline
    v_gl = db.query(BrandGuideline).filter(BrandGuideline.org_id == 'vortexa-tech-org-002').first()
    if v_gl:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.guideline_id == v_gl.id).all()
        print(f'VORTEXA guideline has {len(chunks)} chunks.')

    # 4. Clean up rules: Reassign rules with source VORTEXA to vortexa-tech-org-002
    v_rules = db.query(BrandRule).filter(BrandRule.source_document.like('%VORTEXA%')).all()
    print(f'Found {len(v_rules)} rules sourced from VORTEXA.')

    # Deduplicate rules by rule_text
    seen_texts = set()
    for r in v_rules:
        norm = r.rule_text.strip().lower()
        if norm in seen_texts:
            db.delete(r)
        else:
            seen_texts.add(norm)
            r.org_id = 'vortexa-tech-org-002'
    db.commit()
    print(f'Deduplicated and reassigned VORTEXA rules. {len(seen_texts)} unique rules kept under VORTEXA.')

    # 5. Add VORTEXA Approved Facts from the document
    if not db.query(ApprovedFact).filter(ApprovedFact.org_id == 'vortexa-tech-org-002').first():
        db.add_all([
            ApprovedFact(
                id=str(uuid.uuid4()),
                org_id='vortexa-tech-org-002',
                category='Pricing',
                fact_key='VortexBook AI Pro 16 Launch Price',
                fact_value='₹79,999',
                verification_source='VT-BG-2026-001 Page 2, Section 5',
                notes='Approved launch price is ₹79,999. Any other price like ₹69,999 is contradicted.'
            ),
            ApprovedFact(
                id=str(uuid.uuid4()),
                org_id='vortexa-tech-org-002',
                category='Product',
                fact_key='Primary Approved Product Name',
                fact_value='VortexBook AI Pro 16',
                verification_source='VT-BG-2026-001 Page 2, Section 4',
                notes='Use exact name on first mention. Shortened name: VortexBook AI Pro.'
            ),
            ApprovedFact(
                id=str(uuid.uuid4()),
                org_id='vortexa-tech-org-002',
                category='Specification',
                fact_key='Document Metadata',
                fact_value='Document ID: VT-BG-2026-001, Version 1.0, Effective Date: 05 Nov 2026',
                verification_source='VT-BG-2026-001 Page 1',
                notes='Owner: Brand Governance Team. Status: Approved.'
            )
        ])
        db.commit()
        print('Added VORTEXA approved ground truth facts.')

    # 6. Add VORTEXA Terminology Rules from the document
    if not db.query(TerminologyRule).filter(TerminologyRule.org_id == 'vortexa-tech-org-002').first():
        db.add_all([
            TerminologyRule(
                id=str(uuid.uuid4()),
                org_id='vortexa-tech-org-002',
                prohibited_term='budget laptop',
                preferred_term='dependable productivity laptop',
                explanation='VORTEXA Brand Guidelines Section 4: Do not use budget laptop.'
            ),
            TerminologyRule(
                id=str(uuid.uuid4()),
                org_id='vortexa-tech-org-002',
                prohibited_term='cheap AI device',
                preferred_term='AI-powered productivity device',
                explanation='VORTEXA Brand Guidelines Section 4: Do not use cheap AI device.'
            ),
            TerminologyRule(
                id=str(uuid.uuid4()),
                org_id='vortexa-tech-org-002',
                prohibited_term="world's fastest",
                preferred_term='dependable everyday performance',
                explanation="Section 3: Do not use 'world\\'s fastest' without explicit benchmark verification."
            ),
            TerminologyRule(
                id=str(uuid.uuid4()),
                org_id='vortexa-tech-org-002',
                prohibited_term='Vortex Book',
                preferred_term='VortexBook AI Pro 16',
                explanation='Section 4: Do not split the name into Vortex Book.'
            ),
        ])
        db.commit()
        print('Added VORTEXA terminology rules.')

    # 7. Index RAG for both orgs
    from backend.app.services.rag import RagRetriever
    retriever = RagRetriever(db)
    retriever.index_org('nova-tech-org-001')
    retriever.index_org('vortexa-tech-org-002')
    print('Refreshed RAG indices for both NOVA TECH and VORTEXA TECHNOLOGIES.')

    # Print summary
    for o in db.query(Organization).all():
        gls = db.query(BrandGuideline).filter(BrandGuideline.org_id == o.id).count()
        rls = db.query(BrandRule).filter(BrandRule.org_id == o.id).count()
        fcts = db.query(ApprovedFact).filter(ApprovedFact.org_id == o.id).count()
        trms = db.query(TerminologyRule).filter(TerminologyRule.org_id == o.id).count()
        print(f'ORG: {o.name} ({o.id}) -> {gls} guidelines, {rls} rules, {fcts} facts, {trms} terms')

    db.close()

if __name__ == '__main__':
    run_isolation()
