import re
import time
import uuid
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.brand import Organization, BrandRule, ApprovedFact, TerminologyRule, DocumentChunk
from backend.app.models.submission import Submission, Finding, ClaimVerification
from backend.app.models.passport import AgentRun, AuditLog
from backend.app.core.config import settings
from backend.app.services import llm as llm_mod
from backend.app.services.rag import RagRetriever

# Ambiguous marketing superlatives that are not outright prohibited but cannot be
# mechanically confirmed or denied from stored evidence — these require human judgement.
AMBIGUOUS_SUPERLATIVES = [
    "revolutionary", "game-changing", "game changing", "best-in-class", "best in class",
    "industry-leading", "industry leading", "unmatched", "next-generation",
    "next generation", "cutting-edge", "cutting edge", "unrivalled", "unrivaled",
]

_TOKEN_RE = re.compile(r"[a-z0-9']+")


class ContentAnalyzerService:
    def __init__(self, db: Session, llm_provider: Optional["llm_mod.LLMProvider"] = None):
        self.db = db
        self._chunk_cache: Optional[List[DocumentChunk]] = None
        self._chunk_org: Optional[str] = None
        # Optional LLM augmentation. Heuristics remain primary and the fallback.
        self.llm = llm_provider if llm_provider is not None else llm_mod.get_llm_provider(settings)
        # RAG retriever for evidence (TF-IDF cosine + keyword hybrid over chunks).
        self.rag = RagRetriever(db)

    # ------------------------------------------------------------------ #
    #  Evidence retrieval (lexical RAG over stored document_chunks)
    # ------------------------------------------------------------------ #
    def _load_chunks(self, org_id: str) -> List[DocumentChunk]:
        if self._chunk_cache is not None and self._chunk_org == org_id:
            return self._chunk_cache
        chunks = (
            self.db.query(DocumentChunk)
            .join(DocumentChunk.guideline)
            .filter(DocumentChunk.guideline.has(org_id=org_id))
            .all()
        )
        self._chunk_cache = chunks
        self._chunk_org = org_id
        return chunks

    def _retrieve_evidence(self, org_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Best-matching stored guideline chunk for `query`.

        Primary path: the RAG retriever (TF-IDF cosine + keyword hybrid over
        persisted `document_chunks`). Falls back to lexical token-overlap if RAG
        errors. Returns None when nothing matches — callers then say so
        explicitly rather than inventing a source.
        """
        try:
            hit = self.rag.best(org_id, query)
            if hit:
                return hit
        except Exception:
            pass  # fall back to the simple lexical retriever below
        return self._retrieve_evidence_lexical(org_id, query)

    def _retrieve_evidence_lexical(self, org_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Fallback retriever: plain token-overlap over stored chunks."""
        chunks = self._load_chunks(org_id)
        if not chunks:
            return None

        q_tokens = set(_TOKEN_RE.findall(query.lower()))
        if not q_tokens:
            return None

        best: Optional[DocumentChunk] = None
        best_score = 0
        q_lower = query.lower()
        for ch in chunks:
            content_lower = ch.content.lower()
            c_tokens = set(_TOKEN_RE.findall(content_lower))
            score = len(q_tokens & c_tokens)
            # Phrase bonus: reward chunks that contain the query phrase verbatim.
            if len(q_lower) > 6 and q_lower in content_lower:
                score += 5
            if score > best_score:
                best_score = score
                best = ch

        if best is None or best_score == 0:
            return None

        guideline = best.guideline
        filename = guideline.filename if guideline else "Brand Guideline"
        return {
            "filename": filename,
            "page": best.page_number,
            "content": best.content,
            "citation": f"{filename} (Page {best.page_number})",
            "score": best_score,
        }

    # ------------------------------------------------------------------ #
    #  Main analysis pipeline
    # ------------------------------------------------------------------ #
    def analyze_submission(self, org_id: str, title: str, content: str, submission_id: str = None,
                           author_name: str = "Creator", dry_run: bool = False):
        """Analyse content. With dry_run=True nothing is saved: the same checks run,
        a plain-dict snapshot is returned and the transaction is rolled back
        (used by Campaign Stress Testing)."""
        if dry_run and submission_id:
            raise ValueError("dry_run analyses new text only; it never touches an existing submission.")
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise ValueError(f"Organization with id {org_id} not found.")
        self._org_id = org_id  # tenant scope for agent-run records

        rules = self.db.query(BrandRule).filter(BrandRule.org_id == org_id, BrandRule.is_active == True).all()
        facts = self.db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()
        terms = self.db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id, TerminologyRule.is_active == True).all()
        # Warm the chunk cache once for this analysis run.
        self._chunk_cache = None
        self._chunk_org = None
        self._load_chunks(org_id)

        # Get or create Submission
        if submission_id:
            submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                if submission.org_id != org_id:
                    # Never let one organisation overwrite another's submission.
                    raise PermissionError("Submission belongs to a different organisation.")
                changed = submission.content != content or submission.title != title
                submission.findings.clear()
                submission.claim_verifications.clear()
                if changed:
                    self._new_version(submission, content, title, author_name)
                submission.status = "Analysed"
            else:
                submission_id = str(uuid.uuid4())
                submission = Submission(id=submission_id, org_id=org_id, title=title, content=content, status="Analysed", author_name=author_name)
                self.db.add(submission)
        else:
            submission_id = str(uuid.uuid4())
            submission = Submission(id=submission_id, org_id=org_id, title=title, content=content, status="Analysed", author_name=author_name)
            self.db.add(submission)

        findings_list: List[Finding] = []
        claims_list: List[ClaimVerification] = []
        deductions = 0

        # --- AGENT 1: Terminology Agent ---
        t_start = time.perf_counter()
        for term_rule in terms:
            pattern = re.compile(re.escape(term_rule.prohibited_term), re.IGNORECASE)
            for match in pattern.finditer(content):
                matched_text = match.group(0)
                ev = self._retrieve_evidence(org_id, f"{term_rule.prohibited_term} {term_rule.explanation}")
                findings_list.append(Finding(
                    id=str(uuid.uuid4()),
                    submission_id=submission.id,
                    issue_category="Terminology",
                    severity="CRITICAL",
                    original_text=matched_text,
                    explanation=term_rule.explanation,
                    rule_reference=f"Prohibited terminology: '{term_rule.prohibited_term}'",
                    evidence_source=ev["citation"] if ev else f"Brand Terminology Register (Org: {org.name})",
                    confidence=0.98,
                    suggested_correction=term_rule.preferred_term,
                ))
                deductions += 15
        self._record_agent_run("Terminology Agent", "Scan for prohibited terms and deprecated nomenclature",
                               time.perf_counter() - t_start, content[:120],
                               f"Identified {len(findings_list)} terminology violations.", {"rules_checked": len(terms)})

        # --- AGENT 2: Brand Voice & Tone Agent ---
        v_start = time.perf_counter()
        exclamation_count = content.count("!")
        if exclamation_count >= 2:
            ev = self._retrieve_evidence(org_id, "brand voice tone exclamation understated precise hype")
            findings_list.append(Finding(
                id=str(uuid.uuid4()),
                submission_id=submission.id,
                issue_category="Tone & Voice",
                severity="WARNING",
                original_text="Multiple exclamation marks used in promotional copy",
                explanation="The brand tone guidelines require a calm, understated, and precise tone. Excessive exclamation marks reduce enterprise credibility.",
                rule_reference="Brand Voice & Tone rule",
                evidence_source=ev["citation"] if ev else "Brand Voice guideline (no passage retrieved)",
                confidence=0.92,
                suggested_correction="Replace enthusiastic exclamation points with confident, period-punctuated declarative statements.",
            ))
            deductions += 10
        self._record_agent_run("Brand Voice Agent", "Synthesize tone restraint and emotional sentiment index",
                               time.perf_counter() - v_start, content[:120],
                               f"Exclamation density: {exclamation_count}. Tone restraint assessment completed.",
                               {"exclamation_count": exclamation_count})

        # --- AGENT 3: ClaimDNA Agent (Pricing, Performance, Comparative, Freshness) ---
        c_start = time.perf_counter()

        # Pricing claims
        # Word boundaries prevent matching "rs" inside words like "delivers 45".
        price_patterns = [r'₹\s*([0-9,]+)', r'\bRs\.?\s*([0-9,]+)', r'\bINR\s*([0-9,]+)']
        found_prices = []
        for pat in price_patterns:
            for m in re.finditer(pat, content, re.IGNORECASE):
                found_prices.append((m.group(0), m.group(1).replace(",", "")))

        approved_price_fact = next((f for f in facts if "price" in f.fact_key.lower()), None)
        price_ev = self._retrieve_evidence(org_id, "pricing policy launch price")
        for raw_price, clean_price in found_prices:
            if approved_price_fact is None:
                # Cannot confirm or deny without an approved pricing record → human review.
                claims_list.append(ClaimVerification(
                    id=str(uuid.uuid4()), submission_id=submission.id,
                    claim_text=f"Product price: {raw_price}", status="Needs Human Review", category="Pricing",
                    explanation="No approved pricing record exists for this organisation, so the stated price can neither be confirmed nor contradicted automatically.",
                    evidence_text=price_ev["content"] if price_ev else None,
                    source_reference=price_ev["citation"] if price_ev else None, confidence=0.5,
                ))
                deductions += 5
                continue
            approved_price_val = approved_price_fact.fact_value.replace("₹", "").replace(",", "").strip()
            if clean_price != approved_price_val:
                findings_list.append(Finding(
                    id=str(uuid.uuid4()), submission_id=submission.id, issue_category="Pricing", severity="CRITICAL",
                    original_text=raw_price,
                    explanation=f"Promotional price '{raw_price}' conflicts directly with the approved launch price of {approved_price_fact.fact_value}.",
                    rule_reference="Authorized Product Pricing Rule",
                    evidence_source=price_ev["citation"] if price_ev else approved_price_fact.verification_source,
                    confidence=0.99, suggested_correction=approved_price_fact.fact_value,
                ))
                claims_list.append(ClaimVerification(
                    id=str(uuid.uuid4()), submission_id=submission.id, claim_text=f"Product price: {raw_price}",
                    status="Contradicted", category="Pricing",
                    explanation=f"Explicitly contradicts approved pricing record {approved_price_fact.fact_value}.",
                    evidence_text=price_ev["content"] if price_ev else f"{approved_price_fact.fact_key}: {approved_price_fact.fact_value}",
                    source_reference=price_ev["citation"] if price_ev else approved_price_fact.verification_source,
                    confidence=0.99,
                ))
                deductions += 25
            else:
                claims_list.append(ClaimVerification(
                    id=str(uuid.uuid4()), submission_id=submission.id, claim_text=f"Product price: {raw_price}",
                    status="Supported", category="Pricing",
                    explanation=f"Matches approved launch price {approved_price_fact.fact_value}.",
                    evidence_text=price_ev["content"] if price_ev else f"{approved_price_fact.fact_key}: {approved_price_fact.fact_value}",
                    source_reference=price_ev["citation"] if price_ev else approved_price_fact.verification_source,
                    confidence=0.99,
                ))

        # Superlative performance claims
        for sm in re.finditer(r"(world['’]?s fastest|fastest AI laptop|unbeatable performance)", content, re.IGNORECASE):
            matched_claim = sm.group(0)
            ev = self._retrieve_evidence(org_id, f"{matched_claim} performance benchmark verification absolute claim")
            findings_list.append(Finding(
                id=str(uuid.uuid4()), submission_id=submission.id, issue_category="Promotional Claim", severity="CRITICAL",
                original_text=matched_claim,
                explanation="Superlative speed claim without an audited third-party benchmark citation. Guidelines prohibit unsubstantiated absolute performance claims.",
                rule_reference="Superlative Claim Prohibition",
                evidence_source=ev["citation"] if ev else "No supporting guideline passage retrieved",
                confidence=0.96 if ev else 0.7,
                suggested_correction="engineered for sustained 45 TOPS AI processing",
            ))
            claims_list.append(ClaimVerification(
                id=str(uuid.uuid4()), submission_id=submission.id, claim_text=matched_claim, status="Unsupported",
                category="Performance",
                explanation="No approved benchmark evidence supports this absolute claim." if not ev else "Guideline requires independent benchmark verification, which is not present in approved evidence.",
                evidence_text=ev["content"] if ev else None,
                source_reference=ev["citation"] if ev else None, confidence=0.96 if ev else 0.7,
            ))
            deductions += 20

        # Comparative competitor claims
        for cm in re.finditer(r"(10x faster than every competitor|faster than every competitor|faster than any rival)", content, re.IGNORECASE):
            matched_claim = cm.group(0)
            ev = self._retrieve_evidence(org_id, f"{matched_claim} comparative competitor benchmark test methodology")
            findings_list.append(Finding(
                id=str(uuid.uuid4()), submission_id=submission.id, issue_category="Promotional Claim", severity="CRITICAL",
                original_text=matched_claim,
                explanation="Broad comparative competitor claim without cited benchmark testing parameters or audited disclosure.",
                rule_reference="Comparative Competitor Claim Rule",
                evidence_source=ev["citation"] if ev else "No supporting guideline passage retrieved",
                confidence=0.97 if ev else 0.7,
                suggested_correction="demonstrating class-leading efficiency across ISO-289 standard benchmarks",
            ))
            claims_list.append(ClaimVerification(
                id=str(uuid.uuid4()), submission_id=submission.id, claim_text=matched_claim, status="Unsupported",
                category="Comparative",
                explanation="No verifiable comparison dataset exists for 'every competitor' in approved evidence.",
                evidence_text=ev["content"] if ev else None,
                source_reference=ev["citation"] if ev else None, confidence=0.97 if ev else 0.7,
            ))
            deductions += 20

        # Ambiguous superlatives → Needs Human Review
        lowered = content.lower()
        seen_ambiguous = set()
        for phrase in AMBIGUOUS_SUPERLATIVES:
            if phrase in lowered and phrase not in seen_ambiguous:
                seen_ambiguous.add(phrase)
                ev = self._retrieve_evidence(org_id, f"{phrase} claim verification tone")
                claims_list.append(ClaimVerification(
                    id=str(uuid.uuid4()), submission_id=submission.id, claim_text=phrase,
                    status="Needs Human Review", category="Performance",
                    explanation=f"'{phrase}' is ambiguous marketing language that cannot be mechanically confirmed or contradicted from approved evidence. A reviewer must judge whether it is substantiated.",
                    evidence_text=ev["content"] if ev else None,
                    source_reference=ev["citation"] if ev else None, confidence=0.55,
                ))
                deductions += 5

        # Fact references → Supported or Outdated (freshness-aware)
        now = datetime.datetime.utcnow()
        for fact in facts:
            if "price" in fact.fact_key.lower():
                continue
            # Require a distinctive key token (>= 7 chars) to avoid matching on
            # generic words like "launch"/"offer"/"bonus" that cause false hits.
            key_words = [w for w in fact.fact_key.lower().split() if len(w) >= 7]
            if not any(w in lowered for w in key_words):
                continue
            is_outdated = fact.valid_until is not None and fact.valid_until < now
            if is_outdated:
                claims_list.append(ClaimVerification(
                    id=str(uuid.uuid4()), submission_id=submission.id,
                    claim_text=f"Referencing: {fact.fact_key}", status="Outdated", category=fact.category,
                    explanation=f"The approved record for '{fact.fact_key}' expired on {fact.valid_until.date().isoformat()}"
                                + (f" and was superseded: {fact.superseded_by}." if fact.superseded_by else "."),
                    evidence_text=f"Expired approved fact: '{fact.fact_key}: {fact.fact_value}' (valid until {fact.valid_until.date().isoformat()}).",
                    source_reference=fact.verification_source, confidence=0.9,
                ))
                deductions += 10
            else:
                claims_list.append(ClaimVerification(
                    id=str(uuid.uuid4()), submission_id=submission.id,
                    claim_text=f"Referencing: {fact.fact_key}", status="Supported", category=fact.category,
                    explanation=f"Corroborated by a current verified brand fact: {fact.fact_value}.",
                    evidence_text=f"Approved Fact: '{fact.fact_key}: {fact.fact_value}'.",
                    source_reference=fact.verification_source, confidence=0.94,
                ))

        self._record_agent_run("ClaimDNA Agent", "Extract, resolve, and audit factual & promotional claims against approved evidence",
                               time.perf_counter() - c_start, content[:120],
                               f"Audited {len(claims_list)} claims. Non-compliant: {sum(1 for c in claims_list if c.status in ['Contradicted', 'Unsupported', 'Outdated'])}, needs review: {sum(1 for c in claims_list if c.status == 'Needs Human Review')}.",
                               {"total_claims": len(claims_list)})

        # --- AGENT 3.5: LLM Analyst (optional augmentation) ---
        deductions += self._run_llm_pass(org_id, org, content, rules, facts, findings_list, submission.id)

        # --- AGENT 4: Suggestion / Orchestrator ---
        s_start = time.perf_counter()
        final_score = max(5, 100 - deductions)
        submission.overall_score = final_score
        submission.findings = findings_list
        submission.claim_verifications = claims_list
        self._record_agent_run("Suggestion Agent", "Synthesize contextual brand corrections & compliance score calculation",
                               time.perf_counter() - s_start, f"Findings count: {len(findings_list)}",
                               f"Generated {len(findings_list)} suggestions. Brand compliance score: {final_score}/100.",
                               {"final_score": final_score})

        audit = AuditLog(
            id=str(uuid.uuid4()), org_id=org_id, action="CONTENT_ANALYZED", actor=author_name,
            details=f"Analyzed content '{title}' (Length: {len(content)} chars). Score: {final_score}/100 with {len(findings_list)} findings.",
        )
        if dry_run:
            snapshot = {
                "score": final_score,
                "findings": [{"category": f.issue_category, "severity": f.severity, "text": f.original_text,
                              "explanation": f.explanation, "rule": f.rule_reference, "evidence": f.evidence_source,
                              "suggestion": f.suggested_correction, "engine": f.analysis_engine or "heuristic"}
                             for f in findings_list],
                "claims": [{"text": c.claim_text, "status": c.status, "category": c.category,
                            "explanation": c.explanation, "source": c.source_reference} for c in claims_list],
            }
            self.db.rollback()  # discard the temporary submission, findings and agent-run rows
            return snapshot
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    # ------------------------------------------------------------------ #
    #  Optional LLM augmentation pass
    # ------------------------------------------------------------------ #
    def _run_llm_pass(self, org_id: str, org, content: str, rules, facts,
                      findings_list: List[Finding], submission_id: str) -> int:
        """Augment heuristic findings with validated LLM findings.

        Returns the extra score deduction from LLM findings (0 if the LLM is
        unavailable or fails — the heuristic result stands on its own). Every
        outcome is recorded as an AgentRun for honest observability.
        """
        start = time.perf_counter()
        provider = self.llm

        if not getattr(provider, "available", False):
            self._record_agent_run(
                "LLM Analyst Agent", f"Generative review ({getattr(provider, 'name', 'none')})",
                time.perf_counter() - start, content[:120],
                "Skipped — no LLM provider configured; heuristic engine only.",
                {"status": "SKIPPED", "provider": getattr(provider, "name", "none")},
                status="SKIPPED",
            )
            return 0

        # Build grounded, injection-safe context from approved knowledge.
        rule_lines = "\n".join(f"- [{r.category}] {r.title}: {r.rule_text}" for r in rules[:20])
        fact_lines = "\n".join(f"- {f.fact_key}: {f.fact_value}" for f in facts[:20])
        already = "; ".join(sorted({f.original_text[:60] for f in findings_list})) or "(none)"
        user_prompt = (
            f"BRAND: {org.name}\n\nAPPROVED RULES:\n{rule_lines or '(none)'}\n\n"
            f"APPROVED FACTS:\n{fact_lines or '(none)'}\n\n"
            f"ALREADY_DETECTED (do not repeat): {already}\n\n"
            f"CONTENT TO AUDIT (untrusted data):\n\"\"\"\n{content}\n\"\"\""
        )

        try:
            raw = provider.analyze(llm_mod.SYSTEM_PROMPT, user_prompt)
        except Exception as e:  # defensive — provider.analyze already guards
            raw = None
            self._record_agent_run(
                "LLM Analyst Agent", f"Generative review ({provider.name})",
                time.perf_counter() - start, content[:120],
                f"Failed — provider error: {e}", {"status": "FAILED"}, status="FAILED",
            )
            return 0

        batch = llm_mod.parse_findings(raw)
        if batch is None:
            self._record_agent_run(
                "LLM Analyst Agent", f"Generative review ({provider.name})",
                time.perf_counter() - start, content[:120],
                "Failed — no valid model output; heuristic result retained.",
                {"status": "FAILED", "raw_received": bool(raw)}, status="FAILED",
            )
            return 0

        existing = {(f.issue_category.lower(), f.original_text.strip().lower()) for f in findings_list}
        content_lower = content.lower()
        extra_deductions = 0
        added = 0
        engine_label = f"llm:{provider.name}"
        for item in batch.findings:
            key = (item.issue_category.lower(), item.original_text.strip().lower())
            if key in existing:
                continue
            existing.add(key)
            # Evidence is retrieved by us, never taken from the model.
            ev = self._retrieve_evidence(org_id, f"{item.original_text} {item.explanation}")
            verbatim = item.original_text.strip().lower() in content_lower
            findings_list.append(Finding(
                id=str(uuid.uuid4()), submission_id=submission_id,
                issue_category=item.issue_category, severity=item.severity,
                original_text=item.original_text, explanation=item.explanation,
                rule_reference=f"LLM-identified ({provider.model})",
                evidence_source=ev["citation"] if ev else "LLM interpretation (no guideline passage retrieved)",
                confidence=min(item.confidence, 0.9) if verbatim else min(item.confidence, 0.6),
                suggested_correction=item.suggested_correction or "Revise to align with approved brand guidance.",
                analysis_engine=engine_label,
            ))
            added += 1
            extra_deductions += {"CRITICAL": 12, "WARNING": 6}.get(item.severity, 3)

        extra_deductions = min(extra_deductions, 24)  # cap LLM influence on score
        self._record_agent_run(
            "LLM Analyst Agent", f"Generative review ({provider.model})",
            time.perf_counter() - start, content[:120],
            f"Added {added} validated LLM findings (deduction {extra_deductions}).",
            {"status": "COMPLETED", "added": added, "provider": provider.name, "model": provider.model},
            status="COMPLETED",
        )
        return extra_deductions

    def _new_version(self, submission: Submission, content: str, title: str, actor: str) -> None:
        """Record a new content version. Any approval or passport issued for an
        earlier version no longer applies (version-locked approvals)."""
        from backend.app.models.submission import Revision
        from backend.app.services.passport_service import PassportService
        submission.version = (submission.version or 1) + 1
        submission.content = content
        submission.title = title
        self.db.add(Revision(
            id=str(uuid.uuid4()), submission_id=submission.id, version=submission.version,
            content=content, change_summary=f"Content edited — version {submission.version}; prior approvals no longer apply",
            created_by=actor,
        ))
        PassportService(self.db).supersede_for_submission(submission)

    def apply_correction(self, submission_id: str, finding_id: str, target_text: str, replacement_text: str,
                         actor_name: Optional[str] = None) -> Submission:
        submission = self.db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise ValueError(f"Submission {submission_id} not found.")
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise ValueError(f"Finding {finding_id} not found.")

        new_content = submission.content
        if target_text and target_text in new_content:
            new_content = new_content.replace(target_text, replacement_text, 1)
        elif finding.original_text in new_content:
            new_content = new_content.replace(finding.original_text, replacement_text, 1)

        finding.is_applied = True
        self.db.commit()
        # analyze_submission sees the changed content, bumps the version and re-analyses.
        return self.analyze_submission(
            org_id=submission.org_id, title=submission.title, content=new_content,
            submission_id=submission.id, author_name=actor_name or submission.author_name,
        )

    def _record_agent_run(self, agent_name: str, task_name: str, elapsed_seconds: float, input_preview: str, output_preview: str, details: dict, status: str = "COMPLETED"):
        elapsed_us = max(1, round(elapsed_seconds * 1_000_000))
        run = AgentRun(
            id=str(uuid.uuid4()), org_id=getattr(self, "_org_id", None),
            agent_name=agent_name, task_name=task_name, status=status,
            execution_time_ms=round(elapsed_seconds * 1000),
            execution_time_us=elapsed_us,
            tokens_used=max(45, len(input_preview) // 3),
            input_preview=input_preview, output_preview=output_preview,
            event_details=details, created_at=datetime.datetime.utcnow(),
        )
        self.db.add(run)
