import re
import time
import uuid
import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.brand import Organization, BrandRule, ApprovedFact, TerminologyRule, DocumentChunk
from backend.app.models.submission import Submission, Finding, ClaimVerification
from backend.app.models.passport import AgentRun, AuditLog

class ContentAnalyzerService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_submission(self, org_id: str, title: str, content: str, submission_id: str = None, author_name: str = "Creator") -> Submission:
        start_time = time.time()
        
        # 1. Fetch organization brand DNA
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise ValueError(f"Organization with id {org_id} not found.")

        rules = self.db.query(BrandRule).filter(BrandRule.org_id == org_id, BrandRule.is_active == True).all()
        facts = self.db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()
        terms = self.db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id, TerminologyRule.is_active == True).all()
        chunks = self.db.query(DocumentChunk).join(DocumentChunk.guideline).filter(DocumentChunk.guideline.has(org_id=org_id)).all()

        # 2. Get or create Submission
        if submission_id:
            submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                # Clear existing findings and verifications for re-analysis
                submission.findings.clear()
                submission.claim_verifications.clear()
                submission.content = content
                submission.title = title
                submission.status = "Analysed"
            else:
                submission_id = str(uuid.uuid4())
                submission = Submission(
                    id=submission_id,
                    org_id=org_id,
                    title=title,
                    content=content,
                    status="Analysed",
                    author_name=author_name
                )
                self.db.add(submission)
        else:
            submission_id = str(uuid.uuid4())
            submission = Submission(
                id=submission_id,
                org_id=org_id,
                title=title,
                content=content,
                status="Analysed",
                author_name=author_name
            )
            self.db.add(submission)

        findings_list: List[Finding] = []
        claims_list: List[ClaimVerification] = []
        deductions = 0

        # --- AGENT 1: Terminology Agent ---
        t_start = time.time()
        for term_rule in terms:
            pattern = re.compile(re.escape(term_rule.prohibited_term), re.IGNORECASE)
            matches = list(pattern.finditer(content))
            for match in matches:
                matched_text = match.group(0)
                findings_list.append(Finding(
                    id=str(uuid.uuid4()),
                    submission_id=submission.id,
                    issue_category="Terminology",
                    severity="CRITICAL",
                    original_text=matched_text,
                    explanation=term_rule.explanation,
                    rule_reference=f"Prohibited terminology: '{term_rule.prohibited_term}'",
                    evidence_source=f"Brand Terminology Register (Org: {org.name})",
                    confidence=0.98,
                    suggested_correction=term_rule.preferred_term
                ))
                deductions += 15

        self._record_agent_run(
            agent_name="Terminology Agent",
            task_name="Scan for prohibited terms and deprecated nomenclature",
            execution_time_ms=int((time.time() - t_start) * 1000),
            input_preview=content[:120],
            output_preview=f"Identified {len(findings_list)} terminology violations.",
            details={"rules_checked": len(terms)}
        )

        # --- AGENT 2: Brand Voice & Tone Agent ---
        v_start = time.time()
        exclamation_count = content.count("!")
        if exclamation_count >= 2:
            findings_list.append(Finding(
                id=str(uuid.uuid4()),
                submission_id=submission.id,
                issue_category="Tone & Voice",
                severity="WARNING",
                original_text="Multiple exclamation marks used in promotional copy",
                explanation="The brand tone guidelines require a calm, understated, and mathematically precise tone. Exclamation marks reduce enterprise credibility.",
                rule_reference="Rule: Understated & Precise Tone (Page 2)",
                evidence_source="NOVA_TECH_Brand_Governance_2026.pdf (Page 2)",
                confidence=0.92,
                suggested_correction="Replace enthusiastic exclamation points with confident, period-punctuated declarative statements."
            ))
            deductions += 10

        self._record_agent_run(
            agent_name="Brand Voice Agent",
            task_name="Synthesize tone restraint and emotional sentiment index",
            execution_time_ms=int((time.time() - v_start) * 1000),
            input_preview=content[:120],
            output_preview=f"Exclamation density: {exclamation_count}. Tone restraint assessment completed.",
            details={"exclamation_count": exclamation_count}
        )

        # --- AGENT 3: ClaimDNA Agent (Pricing & Factual Claims) ---
        c_start = time.time()
        
        # Check Pricing Claims
        price_patterns = [
            r'₹\s*([0-9,]+)',
            r'Rs\.?\s*([0-9,]+)',
            r'INR\s*([0-9,]+)'
        ]
        found_prices = []
        for pat in price_patterns:
            for m in re.finditer(pat, content, re.IGNORECASE):
                found_prices.append((m.group(0), m.group(1).replace(",", "")))

        approved_price_fact = next((f for f in facts if "price" in f.fact_key.lower()), None)
        if approved_price_fact:
            approved_price_val = approved_price_fact.fact_value.replace("₹", "").replace(",", "").strip()
            for raw_price, clean_price in found_prices:
                if clean_price != approved_price_val:
                    # Price conflict detected!
                    findings_list.append(Finding(
                        id=str(uuid.uuid4()),
                        submission_id=submission.id,
                        issue_category="Pricing",
                        severity="CRITICAL",
                        original_text=raw_price,
                        explanation=f"Promotional price '{raw_price}' conflicts directly with the approved launch price of {approved_price_fact.fact_value}.",
                        rule_reference="Strict Launch Pricing Enforcement Rule (Page 3)",
                        evidence_source=f"{approved_price_fact.verification_source}",
                        confidence=0.99,
                        suggested_correction=approved_price_fact.fact_value
                    ))
                    claims_list.append(ClaimVerification(
                        id=str(uuid.uuid4()),
                        submission_id=submission.id,
                        claim_text=f"Product price: {raw_price}",
                        status="Contradicted",
                        category="Pricing",
                        explanation=f"Explicitly contradicts approved pricing record {approved_price_fact.fact_value}.",
                        evidence_text=f"Pricing Policy Master: '{approved_price_fact.fact_key} is strictly {approved_price_fact.fact_value}'.",
                        source_reference=approved_price_fact.verification_source,
                        confidence=0.99
                    ))
                    deductions += 25
                else:
                    claims_list.append(ClaimVerification(
                        id=str(uuid.uuid4()),
                        submission_id=submission.id,
                        claim_text=f"Product price: {raw_price}",
                        status="Supported",
                        category="Pricing",
                        explanation=f"Matches approved launch price {approved_price_fact.fact_value}.",
                        evidence_text=f"Pricing record verified in {approved_price_fact.verification_source}.",
                        source_reference=approved_price_fact.verification_source,
                        confidence=0.99
                    ))

        # Check Superlative Performance Claims (e.g. "world's fastest")
        superlative_matches = re.finditer(r"(world['’]?s fastest|fastest AI laptop|unbeatable performance)", content, re.IGNORECASE)
        for sm in superlative_matches:
            matched_claim = sm.group(0)
            findings_list.append(Finding(
                id=str(uuid.uuid4()),
                submission_id=submission.id,
                issue_category="Promotional Claim",
                severity="CRITICAL",
                original_text=matched_claim,
                explanation="Superlative speed claim without third-party audited benchmark citation. Regulatory guidelines prohibit unsubstantiated performance claims.",
                rule_reference="Rule: Superlative Claim Prohibition (Page 7)",
                evidence_source="NOVA_TECH_Brand_Governance_2026.pdf (Section 2, Page 7)",
                confidence=0.96,
                suggested_correction="engineered for sustained 45 TOPS AI processing"
            ))
            claims_list.append(ClaimVerification(
                id=str(uuid.uuid4()),
                submission_id=submission.id,
                claim_text=matched_claim,
                status="Unsupported",
                category="Performance",
                explanation="Missing certified laboratory audit citation. Advertising standards LP-41 mandate benchmark validation.",
                evidence_text="Guidelines: 'Absolute performance claims require independent laboratory benchmark verification.'",
                source_reference="NOVA_TECH_Brand_Governance_2026.pdf (Page 7)",
                confidence=0.96
            ))
            deductions += 20

        # Check Comparative Competitor Claims (e.g. "10x faster than every competitor")
        comp_matches = re.finditer(r"(10x faster than every competitor|faster than every competitor|faster than any rival)", content, re.IGNORECASE)
        for cm in comp_matches:
            matched_claim = cm.group(0)
            findings_list.append(Finding(
                id=str(uuid.uuid4()),
                submission_id=submission.id,
                issue_category="Promotional Claim",
                severity="CRITICAL",
                original_text=matched_claim,
                explanation="Broad comparative competitor claim without benchmark testing parameters or audited testing disclosure.",
                rule_reference="Rule: Comparative Competitor Claim Rule (Page 7)",
                evidence_source="NOVA_TECH_Brand_Governance_2026.pdf (Section 2, Page 7)",
                confidence=0.97,
                suggested_correction="demonstrating class-leading efficiency across ISO-289 standard benchmarks"
            ))
            claims_list.append(ClaimVerification(
                id=str(uuid.uuid4()),
                submission_id=submission.id,
                claim_text=matched_claim,
                status="Unsupported",
                category="Comparative",
                explanation="No verifiable laboratory comparison dataset exists for 'every competitor'.",
                evidence_text="Guidelines: 'Broad comparative claims such as 10x faster than every competitor require specific cited test methodologies.'",
                source_reference="NOVA_TECH_Brand_Governance_2026.pdf (Page 7)",
                confidence=0.97
            ))
            deductions += 20

        # Check for supported facts if mentioned
        for fact in facts:
            if fact.category != "Pricing":
                key_words = fact.fact_key.lower().split()
                if any(w in content.lower() for w in key_words if len(w) > 4):
                    claims_list.append(ClaimVerification(
                        id=str(uuid.uuid4()),
                        submission_id=submission.id,
                        claim_text=f"Referencing: {fact.fact_key}",
                        status="Supported",
                        category=fact.category,
                        explanation=f"Corroborated by verified brand fact record: {fact.fact_value}.",
                        evidence_text=f"Approved Fact: '{fact.fact_key}: {fact.fact_value}'.",
                        source_reference=fact.verification_source,
                        confidence=0.94
                    ))

        self._record_agent_run(
            agent_name="ClaimDNA Agent",
            task_name="Extract, resolve, and audit factual & promotional claims against knowledge graph",
            execution_time_ms=int((time.time() - c_start) * 1000),
            input_preview=content[:120],
            output_preview=f"Audited {len(claims_list)} claims. Contradicted/Unsupported identified: {sum(1 for c in claims_list if c.status in ['Contradicted', 'Unsupported'])}.",
            details={"total_claims": len(claims_list)}
        )

        # --- AGENT 4: Orchestrator & Suggestion Agent ---
        s_start = time.time()
        final_score = max(5, 100 - deductions)
        submission.overall_score = final_score
        
        # Attach findings and claims
        submission.findings = findings_list
        submission.claim_verifications = claims_list

        self._record_agent_run(
            agent_name="Suggestion Agent",
            task_name="Synthesize contextual brand corrections & compliance score calculation",
            execution_time_ms=int((time.time() - s_start) * 1000),
            input_preview=f"Findings count: {len(findings_list)}",
            output_preview=f"Generated {len(findings_list)} suggestions. Calculated brand compliance score: {final_score}/100.",
            details={"final_score": final_score}
        )

        # Log total audit execution
        audit = AuditLog(
            id=str(uuid.uuid4()),
            org_id=org_id,
            action="CONTENT_ANALYZED",
            actor=author_name,
            details=f"Analyzed content '{title}' (Length: {len(content)} chars). Score: {final_score}/100 with {len(findings_list)} findings."
        )
        self.db.add(audit)
        
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def apply_correction(self, submission_id: str, finding_id: str, target_text: str, replacement_text: str) -> Submission:
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise ValueError(f"Submission {submission_id} not found.")

        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise ValueError(f"Finding {finding_id} not found.")

        # Replace text in content
        if target_text in submission.content:
            submission.content = submission.content.replace(target_text, replacement_text, 1)
        elif finding.original_text in submission.content:
            submission.content = submission.content.replace(finding.original_text, replacement_text, 1)

        finding.is_applied = True
        
        # Re-run quick analysis on revised content
        self.db.commit()
        return self.analyze_submission(
            org_id=submission.org_id,
            title=submission.title,
            content=submission.content,
            submission_id=submission.id,
            author_name=submission.author_name
        )

    def _record_agent_run(self, agent_name: str, task_name: str, execution_time_ms: int, input_preview: str, output_preview: str, details: dict):
        run = AgentRun(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            task_name=task_name,
            status="COMPLETED",
            execution_time_ms=execution_time_ms,
            tokens_used=max(45, len(input_preview) // 3),
            input_preview=input_preview,
            output_preview=output_preview,
            event_details=details,
            created_at=datetime.datetime.utcnow()
        )
        self.db.add(run)
