const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

// ------------------------------------------------------------------ //
//  Auth (Milestone D) — bearer token + demo accounts
// ------------------------------------------------------------------ //
const TOKEN_KEY = "bv_token";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: "Administrator" | "Creator" | "Reviewer";
  org_id: string;
  auth_provider?: "password" | "google";
}

// Demo credentials for the NOVA TECH judging workspace (not production secrets).
export const DEMO_CREDS: Record<string, { email: string; password: string }> = {
  Administrator: { email: "admin@novatech.demo", password: "Admin@2026" },
  Creator: { email: "creator@novatech.demo", password: "Creator@2026" },
  Reviewer: { email: "reviewer@novatech.demo", password: "Reviewer@2026" },
};

export function getToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}
export function setToken(t: string) {
  try { localStorage.setItem(TOKEN_KEY, t); } catch { /* ignore */ }
}
export function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
}
export function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

/**
 * fetch() with the signed-in user's bearer token attached. The backend scopes
 * every request to the caller's organisation from this token (Phase 1a), so
 * pages never send an org id. A 401 on an authenticated call means the session
 * expired: the token is cleared and the user is sent back to sign in.
 */
export async function apiFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const headers = { ...authHeaders(), ...((init.headers as Record<string, string>) || {}) };
  const res = await fetch(url, { ...init, headers });
  if (res.status === 401 && headers.Authorization && !url.includes("/auth/")) {
    clearToken();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
  }
  return res;
}

function orgQuery(orgId?: string, prefix: "?" | "&" = "?"): string {
  return orgId ? `${prefix}org_id=${encodeURIComponent(orgId)}` : "";
}

export async function login(email: string, password: string): Promise<AuthUser> {
  let res: Response;
  try {
    res = await apiFetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    // fetch() rejects only on a network-level failure (server down, CORS, DNS).
    throw new Error(`Can't reach the server. Make sure the backend is running at ${API_BASE.replace(/\/api\/v1\/?$/, "")}.`);
  }
  if (res.status === 401) throw new Error("Invalid email or password. Try a demo account below.");
  if (!res.ok) throw new Error(`Sign-in failed (server error ${res.status}). Please try again.`);
  const data = await res.json();
  setToken(data.access_token);
  return data.user as AuthUser;
}

export async function register(payload: {
  full_name: string;
  email: string;
  password: string;
}): Promise<AuthUser> {
  const res = await apiFetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = "Could not create account.";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) msg = body.detail[0].msg;
    } catch { /* ignore */ }
    throw new Error(msg);
  }
  const data = await res.json();
  setToken(data.access_token);
  return data.user as AuthUser;
}

// Whether the server has Google OAuth configured (client id + secret present).
export async function fetchGoogleAuthStatus(): Promise<boolean> {
  try {
    const res = await apiFetch(`${API_BASE}/auth/google/status`, { cache: "no-store" });
    if (!res.ok) return false;
    const data = await res.json();
    return Boolean(data.configured);
  } catch {
    return false;
  }
}

// Full-page redirect entry point for the Google authorization-code flow.
export function googleLoginUrl(): string {
  return `${API_BASE}/auth/google/login`;
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  const t = getToken();
  if (!t) return null;
  const res = await apiFetch(`${API_BASE}/auth/me`, { headers: { ...authHeaders() }, cache: "no-store" });
  if (!res.ok) { clearToken(); return null; }
  return res.json();
}

// Ensure a session with the given demo role (logs in if needed or role differs).
export async function ensureDemoLogin(role: "Administrator" | "Creator" | "Reviewer"): Promise<AuthUser> {
  const current = await fetchCurrentUser();
  if (current && current.role === role) return current;
  const creds = DEMO_CREDS[role];
  return login(creds.email, creds.password);
}

export interface HealthInfo {
  status: string;
  service: string;
  tagline: string;
  version: string;
  database: string;
  timestamp: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  guidelines_count: number;
  rules_count: number;
  facts_count: number;
}

export interface BrandRule {
  id: string;
  org_id: string;
  category: string;
  title: string;
  rule_text: string;
  severity: "CRITICAL" | "WARNING" | "SUGGESTION";
  source_document?: string;
  page_reference?: number;
  is_active: boolean;
  is_confirmed: boolean;
  created_at: string;
}

export interface ApprovedFact {
  id: string;
  org_id: string;
  category: string;
  fact_key: string;
  fact_value: string;
  verification_source: string;
  notes?: string;
  created_at: string;
}

export interface TerminologyRule {
  id: string;
  org_id: string;
  prohibited_term: string;
  preferred_term: string;
  explanation: string;
  is_active: boolean;
  created_at: string;
}

export interface BrandGuideline {
  id: string;
  org_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  total_pages: number;
  status: string;
  created_at: string;
}

export interface Finding {
  id: string;
  submission_id: string;
  issue_category: string;
  severity: "CRITICAL" | "WARNING" | "SUGGESTION";
  original_text: string;
  explanation: string;
  rule_reference: string;
  evidence_source: string;
  confidence: number;
  suggested_correction: string;
  is_applied: boolean;
  analysis_engine?: string;
  created_at: string;
}

export interface ClaimVerification {
  id: string;
  submission_id: string;
  claim_text: string;
  status: "Supported" | "Unsupported" | "Contradicted" | "Outdated" | "Needs Human Review";
  category: string;
  explanation: string;
  evidence_text?: string;
  source_reference?: string;
  confidence: number;
  created_at: string;
}

export interface Submission {
  id: string;
  org_id: string;
  title: string;
  content: string;
  version: number;
  status: string;
  author_name: string;
  author_role: string;
  overall_score: number;
  findings: Finding[];
  claim_verifications: ClaimVerification[];
  created_at: string;
  updated_at: string;
}

export interface BrandPassport {
  id: string;
  passport_number: string;
  submission_id: string;
  brand_name: string;
  content_title: string;
  content_hash: string;
  guideline_version: string;
  verification_status: string;
  final_score: number;
  audited_by: string;
  passport_data: Record<string, any>;
  issued_at: string;
}

export interface AgentRun {
  id: string;
  agent_name: string;
  task_name: string;
  status: string;
  execution_time_ms: number;
  tokens_used: number;
  input_preview: string;
  output_preview: string;
  event_details: Record<string, any>;
  created_at: string;
}

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await apiFetch(`${API_BASE}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchWorkspaces(): Promise<Organization[]> {
  const res = await apiFetch(`${API_BASE}/brand/workspaces`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load workspaces");
  return res.json();
}

export async function fetchGuidelines(orgId?: string): Promise<BrandGuideline[]> {
  const res = await apiFetch(`${API_BASE}/brand/guidelines${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load guidelines");
  return res.json();
}

export async function uploadGuideline(orgId: string | undefined, file: File, replaces?: string): Promise<BrandGuideline> {
  const formData = new FormData();
  if (orgId) formData.append("org_id", orgId);
  if (replaces) formData.append("replaces", replaces);
  formData.append("file", file);
  const res = await apiFetch(`${API_BASE}/brand/guidelines/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : "Failed to upload guideline");
  }
  return res.json();
}

export async function fetchRules(orgId?: string, category?: string): Promise<BrandRule[]> {
  const url = new URL(`${API_BASE}/brand/rules`);
  if (orgId) url.searchParams.set("org_id", orgId);
  if (category) url.searchParams.set("category", category);
  const res = await apiFetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch brand rules");
  return res.json();
}

export async function confirmRule(ruleId: string): Promise<BrandRule> {
  const res = await apiFetch(`${API_BASE}/brand/rules/${ruleId}/confirm`, {
    method: "PATCH",
  });
  if (!res.ok) throw new Error("Failed to confirm rule");
  return res.json();
}

export async function fetchFacts(orgId?: string): Promise<ApprovedFact[]> {
  const res = await apiFetch(`${API_BASE}/brand/facts${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch approved facts");
  return res.json();
}

export async function fetchTerms(orgId?: string): Promise<TerminologyRule[]> {
  const res = await apiFetch(`${API_BASE}/brand/terms${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch terminology rules");
  return res.json();
}

export async function analyzeContent(payload: {
  org_id?: string;
  title: string;
  content: string;
  submission_id?: string;
  author_name?: string;
}): Promise<Submission> {
  const res = await apiFetch(`${API_BASE}/content/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Content analysis failed");
  return res.json();
}

export async function applyCorrection(payload: {
  submission_id: string;
  finding_id: string;
  target_text: string;
  replacement_text: string;
}): Promise<Submission> {
  const res = await apiFetch(`${API_BASE}/content/apply-correction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to apply correction");
  return res.json();
}

export async function fetchSubmissions(orgId?: string): Promise<Submission[]> {
  const res = await apiFetch(`${API_BASE}/content/submissions${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch submissions");
  return res.json();
}

export async function fetchSubmissionDetail(id: string): Promise<Submission> {
  const res = await apiFetch(`${API_BASE}/content/submissions/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch submission detail");
  return res.json();
}

// ClaimDNA Evidence Map (R2-7)
export type EvidenceState = "supported" | "contradicted" | "missing" | "outdated" | "review";
export interface EvidenceClaim {
  id: string;
  claim_text: string;
  status: string;
  category: string;
  confidence: number;
  explanation: string;
  evidence_text: string | null;
  source_reference: string | null;
  evidence_state: EvidenceState;
  source: { present: boolean; reliability: string; freshness: string };
}
export interface EvidenceMap {
  items: EvidenceClaim[];
  summary: Record<EvidenceState, number>;
  total: number;
}
export async function fetchEvidenceMap(orgId?: string): Promise<EvidenceMap> {
  const res = await apiFetch(`${API_BASE}/claim/evidence-map${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch evidence map");
  return res.json();
}

export async function runSampleNovaTest(): Promise<Submission> {
  const res = await apiFetch(`${API_BASE}/claim/test-sample`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to run sample test");
  return res.json();
}

export async function submitApprovalDecision(payload: {
  submission_id: string;
  decision: "Approved" | "Rejected" | "Revision Requested";
  comments: string;
  /** Version the reviewer looked at; the server refuses a stale decision (409). */
  expected_version?: number;
  reviewer_name?: string;
  reviewer_role?: string;
}): Promise<Submission> {
  const res = await apiFetch(`${API_BASE}/approval/decide`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (res.status === 401) throw new Error("Sign in required to submit a decision.");
  if (res.status === 403) throw new Error("Your role is not permitted to make this decision.");
  if (res.status === 409) {
    // The content changed after the reviewer opened it — show the server's reason.
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || "This submission changed after you opened it. Reload and review the current version.");
  }
  if (!res.ok) throw new Error("Failed to submit approval decision");
  return res.json();
}

export async function fetchPassports(): Promise<BrandPassport[]> {
  const res = await apiFetch(`${API_BASE}/passport/list`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch brand passports");
  return res.json();
}

export async function fetchPassportBySubmission(id: string): Promise<BrandPassport> {
  const res = await apiFetch(`${API_BASE}/passport/by-submission/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Passport not found for this submission");
  return res.json();
}

export async function fetchAgentStats(): Promise<any> {
  const res = await apiFetch(`${API_BASE}/agent/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch agent statistics");
  return res.json();
}

export async function fetchAgentRuns(): Promise<AgentRun[]> {
  const res = await apiFetch(`${API_BASE}/agent/runs`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch agent runs");
  return res.json();
}

export interface VisualAnalysis {
  submission: Submission;
  format: string;
  dimensions: { width: number; height: number };
  metrics: {
    pixels_sampled: number;
    chromatic_fraction?: number;
    monochrome_fraction?: number;
    contrast?: number;
    avg_luminance?: number;
    dominant_palette?: { hex: string; proportion: number }[];
  };
  ocr: { available: boolean; text: string | null; reason?: string };
}

export async function analyzeImage(orgId: string | undefined, file: File): Promise<VisualAnalysis> {
  const formData = new FormData();
  if (orgId) formData.append("org_id", orgId);
  formData.append("file", file);
  const res = await apiFetch(`${API_BASE}/visual/analyze`, { method: "POST", body: formData });
  if (res.status === 415) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "This image format is not supported for pixel analysis (use PNG or BMP).");
  }
  if (!res.ok) throw new Error("Visual analysis failed");
  return res.json();
}

// ------------------------------------------------------------------ //
//  AI Copy Studio (Round 2 / R2-AI)
// ------------------------------------------------------------------ //
export interface CopyChange { from: string; to: string; reason: string; }
export interface CopyRewrite {
  original: string;
  rewritten: string;
  changes: CopyChange[];
  engine: string;        // "llm:<provider>" | "heuristic" | "none"
  model: string;
  grounded: boolean;
  note: string;
}
export interface CopyStudioStatus { llm_available: boolean; provider: string; model: string; }

export async function fetchCopyStudioStatus(): Promise<CopyStudioStatus> {
  const res = await apiFetch(`${API_BASE}/copy-studio/status`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load Copy Studio status");
  return res.json();
}
export async function rewriteCopy(content: string, orgId?: string): Promise<CopyRewrite> {
  const res = await apiFetch(`${API_BASE}/copy-studio/rewrite`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, org_id: orgId }),
  });
  if (!res.ok) throw new Error("Rewrite failed");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Brand Digital Twin Q&A (Round 2 / R2-3)
// ------------------------------------------------------------------ //
export interface TwinEvidence {
  label: string;
  detail: string;
  source: string;
  href: string;
  page: number | null;
}
export interface TwinAnswer {
  intent: string;
  grounded: boolean;
  question: string;
  answer: string;
  evidence: TwinEvidence[];
  suggestions: string[];
  phrased_by?: string;   // "llm:<provider>" when the LLM rephrased the grounded answer
  model?: string;
}
export async function askBrandTwin(question: string, orgId?: string): Promise<TwinAnswer> {
  const res = await apiFetch(`${API_BASE}/twin/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, org_id: orgId }),
  });
  if (!res.ok) throw new Error("Assistant request failed");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Onboarding / setup status (Round 2 / R2-1)
// ------------------------------------------------------------------ //
export interface OnboardingStep {
  key: string;
  label: string;
  done: boolean;
  count: number | null;
  total?: number;
  href: string;
  hint: string;
}
export interface OnboardingStatus {
  org: { id: string; name: string };
  steps: OnboardingStep[];
  completed: number;
  total: number;
  completion: number;
  is_demo: boolean;
}
export async function fetchOnboardingStatus(orgId?: string): Promise<OnboardingStatus> {
  const res = await apiFetch(`${API_BASE}/onboarding/status${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load onboarding status");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Brand Memory (Round 2 / R2-4)
// ------------------------------------------------------------------ //
export interface MemoryInsight { type: string; title: string; detail: string; count: number; }
export interface MemoryProposal { kind: string; prohibited_term: string; preferred_term: string; reason: string; occurrences: number; }
export interface BrandMemory {
  org: { id: string; name: string };
  insights: MemoryInsight[];
  proposals: MemoryProposal[];
  summary: Record<string, number>;
  note: string;
}
export async function fetchBrandMemory(orgId?: string): Promise<BrandMemory> {
  const res = await apiFetch(`${API_BASE}/memory/insights${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load brand memory");
  return res.json();
}
export async function applyMemoryTerminology(payload: {
  org_id?: string; prohibited_term: string; preferred_term: string; explanation?: string;
}): Promise<{ created: boolean; message?: string }> {
  const res = await apiFetch(`${API_BASE}/memory/apply-terminology`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (res.status === 401) throw new Error("Sign in required.");
  if (res.status === 403) throw new Error("Only an Administrator can apply a proposal.");
  if (!res.ok) throw new Error("Failed to apply proposal.");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Brand Knowledge Graph (Round 2 / R2-2)
// ------------------------------------------------------------------ //
export type GraphNodeType =
  | "brand" | "category" | "guideline" | "evidence" | "rule" | "fact" | "term"
  | "campaign" | "finding" | "claim" | "passport";

export interface GraphNode {
  id: string;
  type: GraphNodeType;
  label: string;
  parent: string | null;
  count?: number;
  href?: string;
  meta: Record<string, any>;
}
export interface GraphEdge {
  source: string;
  target: string;
  kind: "contains" | "references";
}
export interface BrandGraph {
  brand: { id: string; name: string };
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: Record<string, number>;
}

export async function fetchBrandGraph(orgId?: string): Promise<BrandGraph> {
  const res = await apiFetch(`${API_BASE}/graph/brand${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load knowledge graph");
  return res.json();
}

export async function fetchRiskRadar(orgId?: string): Promise<any> {
  const res = await apiFetch(`${API_BASE}/radar/metrics${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch risk radar metrics");
  return res.json();
}

// Predictive Risk Intelligence (R2-5)
export interface RiskDriver { label: string; value: string | number; }
export interface RiskIndicator {
  key: string;
  label: string;
  score: number;
  level: "Low" | "Medium" | "High";
  rationale: string;
  drivers: RiskDriver[];
  recommendation: string;
}
export interface RiskIntelligence {
  org: { id: string; name: string };
  overall_score: number;
  overall_level: "Low" | "Medium" | "High";
  indicators: RiskIndicator[];
  basis: string;
  history: Record<string, number>;
}
export async function fetchRiskIntelligence(orgId?: string): Promise<RiskIntelligence> {
  const res = await apiFetch(`${API_BASE}/radar/intelligence${orgQuery(orgId)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch risk intelligence");
  return res.json();
}


// ------------------------------------------------------------------ //
//  Translation Guard — multilingual claim consistency
// ------------------------------------------------------------------ //
export type TGSeverity = "CRITICAL" | "WARNING" | "INFO";
export interface TGFinding {
  type: string;
  severity: TGSeverity;
  title: string;
  explanation: string;
  original: string;
  translated: string;
  suggestion: string;
  evidence: string;
  engine: string; // "deterministic" | "llm:<provider>"
  confirmed_by_ai?: boolean;
}
export interface TGNumberRow {
  source: string | null;
  translation: string | null;
  status: "match" | "changed" | "qualifier" | "missing" | "additional";
}
export interface TGScores {
  numerical_consistency: number | null;
  claim_consistency: number | null;
  terminology_consistency: number | null;
  completeness: number | null;
  negation_consistency: number | null;
  semantic_similarity: number | null;
}
export interface TGTranslation {
  id: string;
  label: string | null;
  text: string;
  detected_lang: string;
  overall_score: number;
  verdict: "Consistent" | "Review recommended" | "Needs revision";
  language: { code: string; name: string; confidence: number; method: string };
  qualifier_check_supported: boolean;
  scores: TGScores;
  findings: TGFinding[];
  numbers: TGNumberRow[];
  corrected_translation: string;
  cultural_notes: string[];
  engine: string;
  model: string;
}
export interface TGCampaignSummary {
  id: string;
  title: string;
  source_lang: string;
  source_language: string;
  overall_score: number;
  verdict: TGTranslation["verdict"];
  engine: string;
  created_by: string | null;
  created_at: string | null;
  languages: string[];
}
export interface TGCampaign extends TGCampaignSummary {
  source_text: string;
  translations: TGTranslation[];
}
export interface TGLanguages {
  detected: { code: string; name: string }[];
  qualifier_and_negation_checks: { code: string; name: string }[];
  ai_available: boolean;
}

async function tgError(res: Response, fallback: string): Promise<never> {
  const body = await res.json().catch(() => null);
  const detail = typeof body?.detail === "string" ? body.detail : Array.isArray(body?.detail) ? body.detail[0]?.msg : null;
  throw new Error(res.status === 429 ? detail || "Too many requests — wait a moment." : detail || fallback);
}

export async function fetchTGLanguages(): Promise<TGLanguages> {
  const res = await apiFetch(`${API_BASE}/translation-guard/languages`, { cache: "no-store" });
  if (!res.ok) return tgError(res, "Failed to load supported languages");
  return res.json();
}
export async function runTranslationGuard(payload: {
  title: string;
  source_text: string;
  translations: { label?: string; text: string }[];
  use_ai?: boolean;
}): Promise<TGCampaign> {
  const res = await apiFetch(`${API_BASE}/translation-guard/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) return tgError(res, "Translation Guard analysis failed");
  return res.json();
}
export async function fetchTGCampaigns(): Promise<TGCampaignSummary[]> {
  const res = await apiFetch(`${API_BASE}/translation-guard/campaigns`, { cache: "no-store" });
  if (!res.ok) return tgError(res, "Failed to load campaigns");
  return res.json();
}
export async function fetchTGCampaign(id: string): Promise<TGCampaign> {
  const res = await apiFetch(`${API_BASE}/translation-guard/campaigns/${encodeURIComponent(id)}`, { cache: "no-store" });
  if (!res.ok) return tgError(res, "Failed to load campaign");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Shared helpers for the intelligence engines
// ------------------------------------------------------------------ //
async function engineError(res: Response, fallback: string): Promise<never> {
  const body = await res.json().catch(() => null);
  const d = body?.detail;
  throw new Error(typeof d === "string" ? d : Array.isArray(d) ? d[0]?.msg || fallback : fallback);
}
async function getJSON<T>(path: string, fallback: string): Promise<T> {
  const res = await apiFetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) return engineError(res, fallback);
  return res.json();
}
async function postJSON<T>(path: string, body: unknown, fallback: string): Promise<T> {
  const res = await apiFetch(`${API_BASE}${path}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) return engineError(res, fallback);
  return res.json();
}
async function postForm<T>(path: string, form: FormData, fallback: string): Promise<T> {
  const res = await apiFetch(`${API_BASE}${path}`, { method: "POST", body: form });
  if (!res.ok) return engineError(res, fallback);
  return res.json();
}
/** Load an auth-protected image as an object URL for an img tag. Caller revokes it. */
export async function fetchProtectedImage(path: string): Promise<string> {
  const res = await apiFetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Image unavailable");
  return URL.createObjectURL(await res.blob());
}

// ------------------------------------------------------------------ //
//  Product Truth Engine
// ------------------------------------------------------------------ //
export interface ProductFactOut {
  id: string; attribute: string; attribute_label: string; value_text: string; value_num: number | null;
  unit: string | null; qualifier: string; source_document: string | null; page_reference: number | null;
  evidence_excerpt: string | null; status: "pending" | "approved" | "rejected" | "superseded";
  is_current: boolean; expired: boolean; origin: string; valid_until: string | null;
  approved_by: string | null; approved_at: string | null; created_by: string | null; created_at: string | null;
}
export interface ProductOut { id: string; name: string; model_number: string | null; category: string | null; status: string; facts: ProductFactOut[]; }
export interface ProductsResponse { products: ProductOut[]; attributes: Record<string, string>; ai_extraction_available: boolean; }
export type TruthStatus = "Supported" | "Contradicted" | "Outdated" | "Unsupported" | "Needs Human Review";
export interface TruthClaim {
  status: TruthStatus; attribute: string; attribute_label: string; product: string | null; product_inferred: boolean;
  claim_text: string; sentence: string; submitted_value: string; approved_value: string | null;
  source_document: string | null; page_reference: number | null; evidence_excerpt: string | null;
  explanation: string; suggestion: string; fact_id: string | null;
}
export interface TruthResult {
  language: string; products_detected: string[]; product_inferred: boolean; claims: TruthClaim[];
  summary: Record<TruthStatus, number>; verdict: string;
}
export const fetchProducts = () => getJSON<ProductsResponse>("/products", "Failed to load products");
export const verifyProductClaims = (text: string) => postJSON<TruthResult>("/products/verify", { text }, "Verification failed");
export const createProduct = (p: { name: string; model_number?: string; category?: string }) =>
  postJSON<ProductOut>("/products", p, "Could not create product");
export const addProductFact = (productId: string, f: { attribute: string; value_text: string; source_document: string; page_reference?: number; evidence_excerpt?: string }) =>
  postJSON<ProductFactOut>(`/products/${productId}/facts`, f, "Could not add fact");
export const approveProductFact = (id: string) => postJSON<ProductFactOut>(`/products/facts/${id}/approve`, {}, "Could not approve");
export const rejectProductFact = (id: string) => postJSON<ProductFactOut>(`/products/facts/${id}/reject`, {}, "Could not reject");
export interface ExtractionJob {
  id: string; job_id?: string; status: string; stage: string; error: string | null;
  result?: { proposed: number; rejected_unverifiable: number; duplicates: number; note?: string } | null;
}
export const startFactExtraction = () => postJSON<ExtractionJob>("/products/extract", {}, "Could not start extraction");
export const fetchExtractionJob = (id: string) => getJSON<ExtractionJob>(`/products/extract/${id}`, "Could not read job");

// ------------------------------------------------------------------ //
//  Knowledge Gap Detector
// ------------------------------------------------------------------ //
export type GapStatus = "ok" | "missing" | "conflict" | "weak" | "stale";
export interface GapItem {
  key: string; label: string; status: GapStatus; priority: "high" | "medium" | "low"; group: string;
  detail: string; recommendation: string; evidence: { source: string; page: number | null; excerpt: string } | null;
  action: { label: string; href: string } | null;
}
export interface KnowledgeGaps {
  org: { id: string; name: string }; completeness: number; counts: Record<GapStatus, number>; items: GapItem[];
  products: { product: string; product_id: string; attributes: { attribute: string; label: string; status: GapStatus; value?: string; pending: boolean }[] }[];
  recommended_documents: string[]; basis: string; generated_at: string;
}
export const fetchKnowledgeGaps = () => getJSON<KnowledgeGaps>("/products/knowledge-gaps", "Failed to analyse knowledge gaps");

// ------------------------------------------------------------------ //
//  Campaign DNA Fingerprint (integrity)
// ------------------------------------------------------------------ //
export type IntegrityResult = "Verified Match" | "Modified After Approval" | "Unknown Version" | "New Unapproved Campaign" | "Unable to Verify";
export interface IntegrityCheck {
  id: string; result: IntegrityResult; explanation: string; similarity: number | null; input_kind: string;
  input_name: string | null; input_sha256: string; matched_passport_number: string | null;
  matched_submission_id: string | null; checked_by: string; created_at: string | null;
  details: { diff?: { change: string; approved: string; submitted: string }[]; fingerprint?: Record<string, unknown>; hint?: string };
}
export function verifyCampaignIntegrity(input: { text?: string; file?: File }): Promise<IntegrityCheck> {
  const form = new FormData();
  if (input.file) form.append("file", input.file);
  else form.append("text", input.text || "");
  return postForm<IntegrityCheck>("/passport/verify", form, "Verification failed");
}
export const fetchIntegrityChecks = () => getJSON<IntegrityCheck[]>("/passport/integrity-checks", "Failed to load history");

// ------------------------------------------------------------------ //
//  Brand Asset Library + Forensics
// ------------------------------------------------------------------ //
export interface BrandAssetOut {
  id: string; name: string; kind: string; version_label: string; status: string; current: boolean;
  width: number; height: number; mime: string; sha256: string; phash: string;
  colours: { dominant?: { hex: string; share: number }[] }; supersedes_id: string | null; superseded_by_id: string | null;
  valid_until: string | null; uploaded_by: string; approved_by: string | null; created_at: string | null;
  replacement: { id: string; name: string; version_label: string } | null;
}
export interface ForensicFinding {
  type: string; severity: "high" | "medium" | "low" | "info"; title: string; measurement: string;
  explanation: string; recommendation: string; confidence: number;
}
export interface ForensicMatch {
  asset_id: string; asset_name: string; asset_kind: string; version_label: string; asset_status: string; current: boolean;
  similarity: number; phash_distance: number; identical_file: boolean;
  logo_match: {
    method: string; confidence: number; polygon: number[][]; bbox: number[]; rotation_deg: number;
    scale_x: number; scale_y: number; out_of_frame: number; delta_e: number | null; verification: number;
  } | null;
  findings: ForensicFinding[]; replacement: { id: string; name: string; version_label: string } | null;
}
export interface Investigation {
  id: string; file_name: string; risk: "high" | "medium" | "low" | "none"; summary: string; width: number; height: number;
  sha256: string; investigated_by: string; elapsed_ms: number | null; created_at: string | null;
  matches?: ForensicMatch[]; note?: string; compared?: number;
}
export const fetchAssets = () => getJSON<BrandAssetOut[]>("/assets", "Failed to load assets");
export function uploadBrandAsset(input: { file: File; name: string; kind: string; version_label: string; supersedes_id?: string }): Promise<BrandAssetOut> {
  const form = new FormData();
  form.append("file", input.file);
  form.append("name", input.name);
  form.append("kind", input.kind);
  form.append("version_label", input.version_label);
  if (input.supersedes_id) form.append("supersedes_id", input.supersedes_id);
  return postForm<BrandAssetOut>("/assets", form, "Upload failed");
}
export function investigateAsset(file: File): Promise<Investigation> {
  const form = new FormData();
  form.append("file", file);
  return postForm<Investigation>("/assets/investigate", form, "Investigation failed");
}
export const fetchInvestigations = () => getJSON<Investigation[]>("/assets/investigations", "Failed to load investigations");
export const fetchInvestigation = (id: string) => getJSON<Investigation>(`/assets/investigations/${id}`, "Failed to load investigation");

// ------------------------------------------------------------------ //
//  Phase 2 — Launch Readiness
// ------------------------------------------------------------------ //
export type CheckStatus = "pass" | "fail" | "warn" | "pending" | "not_applicable" | "unavailable";
export type LaunchState = "Ready for Review" | "Blocked by Critical Issues" | "Pending Approval" | "Approved for Launch" | "Expired Approval" | "Requires Reanalysis";
export interface LaunchCheck { key: string; label: string; status: CheckStatus; detail: string; evidence: string[]; route_to: string | null; mandatory: boolean; }
export interface LaunchReport {
  id?: string; state: LaunchState; checks: LaunchCheck[]; counts: Record<CheckStatus, number>;
  submission: { id: string; title: string; version: number; status: string; score: number; author: string };
  unresolved_findings: { id: string; category: string; severity: string; text: string; suggestion: string }[];
  blocking: string[]; route_to: string[]; mandatory: string[]; note: string; evaluated_at: string;
}
export interface LaunchPolicy { checks: { key: string; label: string; mandatory: boolean }[]; approval_validity_days: number; updated_by: string | null; updated_at: string | null; }
export const fetchLaunchPolicy = () => getJSON<LaunchPolicy>("/launch/checks", "Failed to load launch policy");
export async function saveLaunchPolicy(p: { mandatory: string[]; approval_validity_days: number }): Promise<LaunchPolicy> {
  const res = await apiFetch(`${API_BASE}/launch/config`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(p) });
  if (!res.ok) return engineError(res, "Could not save policy");
  return res.json();
}
export const runLaunchCheck = (submissionId: string) => postJSON<LaunchReport>(`/launch/${submissionId}/check`, {}, "Readiness check failed");
export const fetchLaunchReports = (submissionId: string) =>
  getJSON<{ id: string; state: LaunchState; version: number; created_by: string; created_at: string | null }[]>(`/launch/${submissionId}/reports`, "Failed to load history");
/** Ask for human review (a creator may do this; it does not approve anything). */
export const sendForReview = (submissionId: string, version: number, comments: string) =>
  postJSON<Submission>("/approval/decide", { submission_id: submissionId, decision: "Pending Review", comments, expected_version: version }, "Could not send for review");

// ------------------------------------------------------------------ //
//  Phase 2 — Asset Lifecycle
// ------------------------------------------------------------------ //
export type LifecycleState = "Draft" | "Pending Approval" | "Approved" | "Active" | "Expiring Soon" | "Expired" | "Superseded" | "Archived";
export interface LifecycleItem {
  kind: "asset" | "product_fact" | "approved_fact" | "guideline" | "approval"; id: string; name: string; category: string;
  state: LifecycleState; valid_until: string | null; detail: string; usage: number | null; last_seen: string | null;
  seen_in: { id: string; file_name: string; risk: string }[]; replacement_available: boolean | null; href: string;
}
export interface Lifecycle {
  counts: Record<LifecycleState, number>; items: LifecycleItem[];
  alerts: { level: "warning" | "critical"; text: string; href: string }[];
  affected_campaigns: { submission_id: string; title: string; status: string; outdated: string[] }[];
  expiring_window_days: number; approval_validity_days: number; generated_at: string;
}
export const fetchLifecycle = () => getJSON<Lifecycle>("/governance/lifecycle", "Failed to load lifecycle");

// ------------------------------------------------------------------ //
//  Phase 2 — Brand Consistency analytics
// ------------------------------------------------------------------ //
export interface Heatmap { rows: string[]; columns: string[]; cells: number[][]; max: number; }
export interface ConsistencyFilters { date_from?: string; date_to?: string; severity?: string; category?: string; product?: string; department?: string; }
export interface Consistency {
  org: { id: string; name: string }; filters: ConsistencyFilters;
  options: { categories: string[]; severities: string[]; products: string[]; departments: string[] };
  kpis: { campaigns: number; findings: number; critical: number; unresolved: number; avg_score: number | null; decisions: number; approval_rate: number | null };
  heatmaps: { product: Heatmap; department: Heatmap; month: Heatmap };
  compliance: {
    campaigns: { id: string; title: string; score: number; status: string; version: number; products: string[]; department: string; findings: number; critical: number; created_at: string | null }[];
    products: { name: string; campaigns: number; avg_score: number; critical_findings: number }[];
    departments: { name: string; campaigns: number; avg_score: number; critical_findings: number }[];
  };
  terminology_repeats: { term: string; count: number; suggested: string }[];
  trends: { months: string[]; score: { month: string; avg_score: number }[]; claims: Record<string, string | number>[]; approvals: Record<string, string | number>[]; visual_findings: { month: string; count: number }[] };
  visual: { logo_misuse: Record<string, number>; colour_deviations: number; investigations: number };
  unresolved: Record<string, string | number>[];
  basis: { months_covered: number; first: string | null; last: string | null; demonstration_data: boolean; note: string };
}
export function fetchConsistency(f: ConsistencyFilters): Promise<Consistency> {
  const q = new URLSearchParams(Object.entries(f).filter(([, v]) => v) as [string, string][]).toString();
  return getJSON<Consistency>(`/analytics/consistency${q ? `?${q}` : ""}`, "Failed to load analytics");
}

// ------------------------------------------------------------------ //
//  Phase 2 — AI Reviewer Intelligence
// ------------------------------------------------------------------ //
export interface ReviewerIntel {
  decisions_analysed: number; data_sufficient: boolean; data_note: string;
  overridden_findings: { rule: string; category: string; severity: string; count: number; examples: { submission_id: string; title: string; text: string }[]; comments: string[] }[];
  unanticipated_rejections: { submission_id: string; title: string; score: number; decision: string; reviewer_comment: string }[];
  disagreements: { rule: string; decisions: Record<string, number>; reviewers_involved: number }[];
  rejected_terminology: { term: string; count: number }[];
  repeated_corrections: { from: string; to: string; count: number }[];
  turnaround: { decisions_timed: number; median_hours: number | null; max_hours: number | null };
  queue: { waiting: number; oldest: { submission_id: string; title: string; status: string; waiting_hours: number }[] };
  recommendations: { kind: string; title: string; detail: string; evidence: unknown[]; reviewer_comments: string[]; proposed_rule: string }[];
  principles: string; generated_at: string;
}
export const fetchReviewerIntel = () => getJSON<ReviewerIntel>("/governance/reviewer-intelligence", "Failed to load reviewer intelligence");
export const proposeGuidelineRule = (p: { title: string; rule_text: string }) =>
  postJSON<{ id: string; title: string; is_confirmed: boolean }>("/governance/reviewer-intelligence/propose", p, "Could not create draft rule");

// ------------------------------------------------------------------ //
//  Phase 3 — Campaign Stress Testing
// ------------------------------------------------------------------ //
export interface SimFinding { category: string; severity: string; text: string; explanation: string; rule: string; suggestion: string; engine: string; }
export interface SimTruth { status: string; attribute_label: string; submitted_value: string; approved_value: string | null; source_document: string | null; }
export interface Simulation {
  id: string; hypothetical: true; scenario: string; scenario_label: string; params: Record<string, string>; changes: string[];
  original: { text: string; score: number; findings: SimFinding[]; product_truth: SimTruth[] };
  simulated: { text: string; score: number; findings: SimFinding[]; product_truth: SimTruth[] };
  score_delta: number; score_comparable: boolean; introduced: SimFinding[]; resolved: SimFinding[]; not_rechecked: SimFinding[]; unchanged: number;
  product_truth_changes: SimTruth[]; translation: { verdict: string; score: number; language: string; findings: { severity: string; title: string }[] } | null;
  recommendations: string[]; note: string; engine: string;
}
export const fetchScenarios = () => getJSON<{ scenarios: { key: string; label: string }[] }>("/simulation/scenarios", "Failed to load scenarios");
export const runSimulation = (submission_id: string, scenario: string, params: Record<string, string>) =>
  postJSON<Simulation>("/simulation/run", { submission_id, scenario, params }, "Simulation failed");

// ------------------------------------------------------------------ //
//  Phase 3 — Content Similarity
// ------------------------------------------------------------------ //
export interface SimilarityMatch {
  kind: string; id: string; ref: string; pair_key: string; title: string; status: string; date: string | null; author: string | null;
  submission_id: string | null; label: string; similarity: number;
  methods: { exact: boolean; shingle_jaccard: number; tfidf_cosine: number; matching_sentences: number };
  matching_sentences: { submitted: string; existing: string; similarity: number }[]; excerpt: string;
  dismissed: boolean; dismissed_reason: string | null; recommendation: string;
}
export interface SimilarityResult { sha256: string; matches: SimilarityMatch[]; compared: number; note: string; thresholds: Record<string, number>; }
export const checkSimilarity = (p: { text?: string; submission_id?: string; include_dismissed?: boolean }) =>
  postJSON<SimilarityResult>("/similarity/check", p, "Similarity check failed");
export const fetchSimilarityClusters = () =>
  getJSON<{ clusters: { size: number; exact_duplicates: boolean; first_seen: string | null; representative: string; members: { id: string; title: string; status: string; date: string | null }[] }[] }>("/similarity/clusters", "Failed to load clusters");
export const dismissSimilarity = (pair_key: string, reason: string) => postJSON<{ dismissed: boolean }>("/similarity/dismiss", { pair_key, reason }, "Could not dismiss");
export const restoreSimilarity = (pair_key: string) => postJSON<{ restored: boolean }>("/similarity/restore", { pair_key, reason: "restored" }, "Could not restore");
export interface ImageSimilarity { sha256: string; compared: number; note: string; matches: { kind: string; id: string; title: string; label: string; phash_distance: number; dhash_distance: number; similarity: number; date: string | null }[]; }
export function checkImageSimilarity(file: File): Promise<ImageSimilarity> {
  const f = new FormData();
  f.append("file", file);
  return postForm<ImageSimilarity>("/similarity/image", f, "Image comparison failed");
}

// ------------------------------------------------------------------ //
//  Phase 3 — Brand Fraud Intelligence
// ------------------------------------------------------------------ //
export type IncidentStatus = "Under Investigation" | "Confirmed" | "False Positive" | "Resolved" | "Escalated";
export interface FraudFinding { type: string; severity: "high" | "medium" | "low" | "info"; title: string; evidence: string; confidence: number; }
export interface FraudIncident {
  id: string; number: string; source_url: string | null; source_kind: string; detected_issue: string; confidence: number;
  risk: "high" | "medium" | "low"; status: IncidentStatus; recommended_response: string; has_evidence_file: boolean;
  created_by: string; created_at: string | null; updated_at: string | null;
  findings?: FraudFinding[]; text_excerpt?: string | null; history?: { status: string; by: string; note: string; at: string }[]; evidence_sha256?: string | null;
}
export const fetchOfficialDomains = () => getJSON<{ id: string; domain: string; added_by: string }[]>("/fraud/domains", "Failed to load domains");
export const addOfficialDomain = (domain: string) => postJSON<{ id: string; domain: string; added_by: string }[]>("/fraud/domains", { domain }, "Could not add domain");
export async function removeOfficialDomain(id: string) {
  const res = await apiFetch(`${API_BASE}/fraud/domains/${id}`, { method: "DELETE" });
  if (!res.ok) return engineError(res, "Could not remove domain");
  return res.json();
}
export function investigateFraud(input: { url?: string; text?: string; file?: File }): Promise<FraudIncident> {
  const f = new FormData();
  if (input.url) f.append("url", input.url);
  if (input.text) f.append("text", input.text);
  if (input.file) f.append("file", input.file);
  return postForm<FraudIncident>("/fraud/investigate", f, "Investigation failed");
}
export const fetchIncidents = () => getJSON<FraudIncident[]>("/fraud/incidents", "Failed to load incidents");
export const fetchIncident = (id: string) => getJSON<FraudIncident>(`/fraud/incidents/${id}`, "Failed to load incident");
export const setIncidentStatus = (id: string, status: IncidentStatus, note: string) =>
  postJSON<FraudIncident>(`/fraud/incidents/${id}/status`, { status, note }, "Could not update status");

// ------------------------------------------------------------------ //
//  Phase 3 — Reputation Early Warning
// ------------------------------------------------------------------ //
export interface ReputationOverview {
  window_days: number; records: number;
  sentiment: { positive: number; neutral: number; negative: number; negative_share: number | null };
  engines: Record<string, number>;
  categories: { category: string; mentions: number; negative: number; negative_share: number; samples: string[] }[];
  recurring_phrases: { phrase: string; count: number }[];
  products: { product: string; total: number; negative: number; positive: number; negative_share: number }[];
  campaign_related: { submission_id: string; title: string; negative_mentions: number; disputed: string[]; samples: string[] }[];
  trend: { week: string; total: number; negative: number; negative_share: number }[]; trend_note: string | null; negative_rising: boolean;
  emerging: { category: string; last_14_days: number; previous_14_days: number }[];
  risks: { theme: string; level: "high" | "medium"; why: string; investigate: string }[];
  sources: Record<string, number>; batches: { batch_id: string; source: string; records: number }[]; note: string;
}
export const fetchReputation = (days = 90) => getJSON<ReputationOverview>(`/reputation/overview?days=${days}`, "Failed to load reputation");
export function uploadFeedback(file: File): Promise<{ batch_id: string; imported: number; skipped: number; problems: string[] }> {
  const f = new FormData();
  f.append("file", file);
  return postForm("/reputation/upload", f, "Upload failed");
}
export const addFeedback = (p: { text: string; rating?: number; channel?: string }) =>
  postJSON<{ batch_id: string; imported: number }>("/reputation/feedback", p, "Could not add feedback");
export async function removeFeedbackBatch(batchId: string) {
  const res = await apiFetch(`${API_BASE}/reputation/batches/${batchId}`, { method: "DELETE" });
  if (!res.ok) return engineError(res, "Could not remove batch");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Round 3 · Creative Inspection + workspace settings
// ------------------------------------------------------------------ //
export interface OcrLine { text: string; confidence: number; box: [number, number, number, number]; low_confidence?: boolean; ocr_text?: string }
export interface CreativePage { index: number; label: string; width: number; height: number; source: "ocr" | "pdf-text" | "skipped"; lines: OcrLine[]; has_image: boolean }
export interface CreativeRegion { kind: "finding" | "claim" | "logo"; id: string; severity: string; category: string; label: string; page: number; box: [number, number, number, number]; text: string }
export interface ClearSpace { required_px: number; min_margin_px: number; edges: Record<string, number>; tight_edges: string[]; intruding_text: string[]; ok: boolean }
export interface LogoCheck { page: number; asset_name: string; version_label: string; bbox: number[]; confidence: number; clear_space: ClearSpace; findings: { type: string; severity: string; title: string; measurement: string }[] }
export interface CreativeInspectionOut {
  id: string; file_name: string; kind: "image" | "pdf" | "video"; mime: string; score: number | null; text_found: boolean;
  engine: string; elapsed_ms: number; note: string | null; submission_id: string | null; created_by: string; created_at: string | null;
  page_count: number; logo_count: number;
  pages?: CreativePage[]; corrections?: { from: string; to: string; reason: string; page: number }[];
  regions?: CreativeRegion[]; logo_checks?: LogoCheck[];
  submission?: {
    id: string; title: string; status: string; overall_score: number; content: string;
    findings: { id: string; category: string; severity: string; text: string; explanation: string; rule: string; evidence: string; suggestion: string; engine: string }[];
    claims: { id: string; text: string; status: string; category: string; explanation: string }[];
  };
}
export const fetchCreativeStatus = () =>
  getJSON<{ ocr: { available: boolean; engine: string | null; reason?: string }; limits: { pdf_pages: number; ocr_pdf_pages: number; video_frames: number; max_mb: Record<string, number> } }>("/creative/status", "Could not load OCR status.");
export function inspectCreative(file: File, department?: string) {
  const f = new FormData(); f.append("file", file); if (department) f.append("department", department);
  return postForm<CreativeInspectionOut>("/creative/inspect", f, "Inspection failed.");
}
export const fetchCreativeInspections = () => getJSON<CreativeInspectionOut[]>("/creative/inspections", "Could not load inspections.");
export const fetchCreativeInspection = (id: string) => getJSON<CreativeInspectionOut>(`/creative/inspections/${id}`, "Could not load the inspection.");

export interface WorkspaceSettings {
  logo_clear_space_ratio: number;
  channels: Record<string, { label: string; max_chars: number; aspect_ratios: string[]; required: string[] }>;
  disclaimers: { id: string; label: string; trigger: string; region: string; required_any: string[] }[];
  notifications: { email: string; slack_webhook_url: string; events: string[] };
}
export const fetchWorkspaceSettings = () =>
  getJSON<{ settings: WorkspaceSettings; defaults: WorkspaceSettings; editable: boolean }>("/workspace/settings", "Could not load settings.");
export async function saveWorkspaceSettings(changes: Partial<WorkspaceSettings>): Promise<{ settings: WorkspaceSettings }> {
  const res = await apiFetch(`${API_BASE}/workspace/settings`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes) });
  if (!res.ok) return engineError(res, "Could not save settings.");
  return res.json();
}

// ------------------------------------------------------------------ //
//  Round 3 · Integrations: API keys, webhooks, notifications, channels
// ------------------------------------------------------------------ //
export interface ApiKeyOut { id: string; name: string; prefix: string; scopes: string[]; created_by: string; created_at: string | null; last_used_at: string | null; use_count: number; revoked: boolean }
export const fetchApiKeys = () => getJSON<{ keys: ApiKeyOut[]; scopes: Record<string, string> }>("/integrations/api-keys", "Could not load API keys.");
export const createApiKey = (name: string, scopes: string[]) =>
  postJSON<{ key: string; api_key: ApiKeyOut; note: string }>("/integrations/api-keys", { name, scopes }, "Could not create the key.");
export async function revokeApiKey(id: string): Promise<ApiKeyOut> {
  const res = await apiFetch(`${API_BASE}/integrations/api-keys/${id}`, { method: "DELETE" });
  if (!res.ok) return engineError(res, "Could not revoke the key.");
  return res.json();
}
export interface WebhookOut { id: string; url: string; events: string[]; active: boolean; created_by: string; created_at: string | null; secret_hint: string; last_status: string | null }
export const fetchWebhooks = () => getJSON<{ webhooks: WebhookOut[]; events: Record<string, string> }>("/integrations/webhooks", "Could not load webhooks.");
export const createWebhook = (url: string, events: string[]) =>
  postJSON<{ webhook: WebhookOut; secret: string; note: string }>("/integrations/webhooks", { url, events }, "Could not add the webhook.");
export async function disableWebhook(id: string): Promise<WebhookOut> {
  const res = await apiFetch(`${API_BASE}/integrations/webhooks/${id}`, { method: "DELETE" });
  if (!res.ok) return engineError(res, "Could not remove the webhook.");
  return res.json();
}
export const testWebhook = (id: string) => postJSON<{ delivery_id: string }>(`/integrations/webhooks/${id}/test`, {}, "Test delivery failed.");
export interface DeliveryOut { id: string; webhook_id: string; event: string; status: string; status_code: number | null; attempts: number; error: string | null; created_at: string | null; delivered_at: string | null }
export const fetchDeliveries = () => getJSON<DeliveryOut[]>("/integrations/deliveries", "Could not load deliveries.");

export interface NotificationOut { id: string; event: string; title: string; body: string; link: string | null; read: boolean; channels: Record<string, string>; created_at: string | null }
export const fetchNotifications = () => getJSON<{ unread: number; email_configured: boolean; items: NotificationOut[] }>("/notifications", "Could not load notifications.");
export const markNotificationsRead = (ids?: string[]) => postJSON<{ marked: number }>("/notifications/read", ids ?? null, "Could not update notifications.");

export interface ChannelReport {
  ok: boolean; available_channels: Record<string, string>;
  channels: { channel: string; label: string; chars?: number; max_chars?: number | null; aspect?: number | null; ok: boolean; issues: string[] }[];
  disclaimers: { id: string; label: string; region?: string; triggered: boolean; ok: boolean; present?: string[]; required_any?: string[]; issue: string | null }[];
}
export const checkChannels = (body: { text: string; channels: string[]; region?: string; width?: number; height?: number }) =>
  postJSON<ChannelReport>("/channels/check", body, "Channel check failed.");
export const API_BASE_URL = API_BASE;
export interface Capabilities { database: string; persistent_storage?: boolean; keep_awake?: { enabled: boolean; window: string | null; last_ping: string | null }; pgvector: boolean; ocr: { available: boolean; engine: string | null; reason?: string }; embeddings: { available: boolean; provider: string | null; dim?: number; reason?: string }; retrieval_mode: string; email_notifications: boolean; demo_accounts: boolean }
export const fetchCapabilities = () => getJSON<Capabilities>("/capabilities", "Could not load server capabilities.");

// ---------------------------------------------------------- browser push ----
export const fetchPushKey = () => getJSON<{ public_key: string; subscriptions: number }>("/push/public-key", "Could not load push settings.");
export const savePushSubscription = (sub: PushSubscriptionJSON) => postJSON<{ subscribed: boolean }>("/push/subscribe", sub, "Could not turn on browser notifications.");
export const removePushSubscription = (sub: PushSubscriptionJSON) => postJSON<{ removed: number }>("/push/unsubscribe", sub, "Could not turn off browser notifications.");
export const sendTestPush = () => postJSON<{ sent: number; devices: number }>("/push/test", {}, "Could not send a test notification.");
