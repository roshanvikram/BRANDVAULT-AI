# BRANDVAULT AI
> **Tagline:** Protect Every Word. Preserve Every Identity.  
> **Category:** Agentic AI, Brand Governance, RAG, Multimodal AI, Enterprise SaaS  
> **Event:** CodeNexus India 2026 | Round 2 | Functional Enterprise AI Product

---

## 1. Team Credentials

- **Team Leader:** Deepak Mouriya M
- **Team Members:**
  - Deepak Mouriya M
  - Roshan Vikram AV
  - Preethish
  - Aishwarya R M

---

## 2. Core Workflow Architecture

```
UPLOAD BRAND GUIDELINES → CREATE BRAND DNA → SUBMIT CONTENT → AI ANALYSIS → EVIDENCE-BASED FINDINGS → SUGGESTED CORRECTIONS → HUMAN APPROVAL → BRAND PASSPORT
```

BRANDVAULT AI is an intelligent brand-governance platform that audits marketing content against an organisation's approved brand guidelines, terminology, facts, promotional claims, and visual identity.

---

## 3. Strict Monochrome UI Design System

Designed according to the Swiss International Typographic Style, Apple simplicity, Linear enterprise interface, and Stripe dashboard hierarchy:

- `#0A0A0A` (Deep Canvas / Background)
- `#171717` (Component Card / Surface)
- `#262626` (Subtle Borders)
- `#404040` (Default Borders & Dividers)
- `#737373` (Muted Metadata & Captions)
- `#A3A3A3` (Secondary Labels & Text)
- `#E5E5E5` (Borders & Highlights)
- `#F5F5F5` (Primary Text)
- `#FFFFFF` (Headings & High-Contrast Accents)

*Zero colourful gradients, zero blue, green, red, or orange.*

---

## 4. Application Modules (10 Functional Modules)

1. **Command Center (`/`):** Executive overview of brand health index, active campaign audits, real-time agent fleet status, and instant sample test execution.
2. **Brand DNA Studio (`/brand-dna`):** Multi-format guideline ingestion (PDF/TXT), automated policy extraction, administrator confirmation flow, approved facts manager, and terminology rules.
3. **Content Intelligence (`/content-intelligence`):** Professional three-panel workspace featuring:
   - Panel 1: Content Editor with campaign title and character count.
   - Panel 2: Findings List with issue category, severity, original snippet, and one-click "Apply Fix".
   - Panel 3: Evidence & Brand Rules displaying ground-truth citations, page references, and confidence ratings.
4. **ClaimDNA (`/claim-dna`):** Evidence-backed promotional claim verification with a 5-status truth model:
   - `Supported`
   - `Unsupported`
   - `Contradicted`
   - `Outdated`
   - `Needs Human Review`
5. **Visual DNA Inspector (`/visual-dna`):** Multimodal creative asset auditor featuring image canvas preview, OCR text extraction, and strict monochrome color palette compliance.
6. **Agent Control Center (`/agent-control`):** Real-time monitoring of 6 autonomous specialist agents (Orchestrator, Brand Voice, Terminology, ClaimDNA, Suggestion, Guideline Gap) with live execution telemetry and latency logging.
7. **Approval Hub (`/approval-hub`):** Human-in-the-loop review queue supporting 3 roles (Administrator, Creator, Reviewer) with decision logging, revision tracking, and audit comments.
8. **Brand Passport (`/brand-passport`):** Cryptographic SHA-256 certificate generation with unique passport numbers (`BV-2026-XXXX`), tamper-evident audit records, and printable report view.
9. **Brand Risk Radar (`/risk-radar`):** Aggregated risk analytics tracking repeated terminology drift, claim contradiction rates, and brand vulnerability levels.
10. **Settings (`/settings`):** System configuration, database connectivity, and Round 3 architectural roadmap.

---

## 5. Technology Stack

- **Frontend:** Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide React
- **Backend:** Python 3.13, FastAPI, Pydantic v2, Uvicorn
- **Data Persistence:** SQLAlchemy ORM, SQLite persistent engine (PostgreSQL/pgvector ready)
- **Document Ingestion:** PyPDF for multi-page guideline parsing
- **Extensibility:** Enterprise Model Context Protocol (MCP) server (`backend/mcp_server.py`)

---

## 6. Getting Started

### 1. Prerequisites
- Node.js v18+ (tested on v22.19.0)
- Python 3.10+ (tested on Python 3.13.2)

### 2. Backend Setup
```bash
# Navigate to backend and activate virtualenv
cd backend
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend service
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run frontend development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 7. Verified Acceptance Test Case (NOVA TECH)

### Test Prompt:
> *"Introducing the world's fastest AI laptop! 10x faster than every competitor. Now only ₹69,999!"*

### Stored Brand Truth:
- **Brand:** NOVA TECH
- **Authorized Launch Price:** ₹79,999 (Product Pricing Master Sheet v2.4)
- **Superlative Claim Rule:** Prohibits unverified absolute claims like *"world's fastest"*.
- **Comparative Claim Rule:** Prohibits unverified comparative claims like *"10x faster than every competitor"*.

### Execution Results:
- **Price Check:** Detected ₹69,999 conflicts with approved ₹79,999 → Flagged as `CONTRADICTED` with suggested replacement to ₹79,999.
- **Performance Claim:** *"fastest AI laptop"* → Flagged as `UNSUPPORTED`.
- **Comparative Claim:** *"10x faster than every competitor"* → Flagged as `UNSUPPORTED`.
- **Brand Health Score:** Computed deterministically as 10/100 until corrections applied.
- **Brand Passport:** Generated upon Reviewer approval (`BV-2026-52ED8A`) with SHA-256 fingerprint.

---

## 8. Enterprise MCP Server

BRANDVAULT AI includes a Model Context Protocol server exposing 7 enterprise tools:
- `get_brand_profile`
- `search_brand_guidelines`
- `verify_marketing_claim`
- `get_approved_asset`
- `analyse_content`
- `create_review_request`
- `get_review_status`

Run self-test:
```bash
python backend/mcp_server.py
```

---

## 9. Round 3 Architectural Roadmap

1. **Brand Drift Intelligence:** Longitudinal time-series analysis detecting subtle erosion of brand voice across quarters.
2. **Advanced Multimodal Governance:** Frame-accurate video compliance, synthetic voice cadence verification, and 3D product rendering inspection.
3. **Enterprise MCP Integration Hub:** Bidirectional synchronization with Figma, Contentful, Adobe Creative Cloud, and Slack governance bots.

