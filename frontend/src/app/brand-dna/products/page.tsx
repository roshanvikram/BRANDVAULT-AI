"use client";

import { useEffect, useMemo, useState } from "react";
import { Package, Plus, Sparkles, Loader2, Check, X, ShieldCheck, Search, FileText, Cpu } from "lucide-react";
import {
  fetchProducts, verifyProductClaims, createProduct, addProductFact, approveProductFact, rejectProductFact,
  startFactExtraction, fetchExtractionJob, ProductsResponse, TruthResult, TruthStatus, ExtractionJob,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CARD, Badge, Tone, PageHeader, ErrorNote, Loading, BTN_PRIMARY, BTN_SECONDARY, INPUT } from "@/components/engines/ui";

const STATUS_TONE: Record<TruthStatus, Tone> = {
  Supported: "good", Contradicted: "bad", Outdated: "bad", Unsupported: "warn", "Needs Human Review": "info",
};
const FACT_TONE: Record<string, Tone> = { approved: "good", pending: "ai", superseded: "neutral", rejected: "bad" };

export default function ProductTruthPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "Administrator";
  const [data, setData] = useState<ProductsResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [result, setResult] = useState<TruthResult | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [newProduct, setNewProduct] = useState("");
  const [factForm, setFactForm] = useState<{ productId: string; attribute: string; value: string; source: string; page: string } | null>(null);
  const [job, setJob] = useState<ExtractionJob | null>(null);

  const load = () => fetchProducts().then((d) => { setData(d); setLoadError(null); }).catch((e) => setLoadError(e.message));
  useEffect(() => { load(); }, []);

  // Poll the durable extraction job until it finishes.
  useEffect(() => {
    if (!job || ["completed", "failed", "cancelled"].includes(job.status)) return;
    const t = setTimeout(() => fetchExtractionJob(job.id).then((j) => { setJob(j); if (j.status === "completed") load(); }).catch(() => {}), 1500);
    return () => clearTimeout(t);
  }, [job]);

  const firstProduct = data?.products[0]?.name;
  const example = firstProduct ? `Get ${firstProduct} today for ₹69,999. Up to 20 hours of battery and a 3-year warranty.` : "";

  const verify = async () => {
    if (!text.trim()) return;
    setVerifying(true); setVerifyError(null);
    try { setResult(await verifyProductClaims(text.trim())); }
    catch (e: any) { setVerifyError(e.message); }
    finally { setVerifying(false); }
  };

  const act = async (fn: () => Promise<unknown>) => {
    setAdminError(null);
    try { await fn(); await load(); } catch (e: any) { setAdminError(e.message); }
  };

  const pendingCount = useMemo(() => data?.products.reduce((n, p) => n + p.facts.filter((f) => f.status === "pending").length, 0) || 0, [data]);

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/brand-dna", label: "Brand DNA Studio" }}
        eyebrow="Product Truth Engine" icon={<Package className="w-3.5 h-3.5" />}
        title="Verify every product statement against approved facts"
        description="Prices, specifications, warranties and performance claims are checked against administrator-approved product facts with their source documents. Missing facts are reported as unsupported — never guessed."
        actions={isAdmin && (
          <button
            onClick={() => act(async () => setJob(await startFactExtraction()))}
            disabled={!data?.ai_extraction_available || (!!job && !["completed", "failed"].includes(job.status))}
            title={data?.ai_extraction_available ? "AI reads your guidelines and proposes facts for approval" : "No AI model is configured on the server"}
            aria-label="Extract facts from documents (AI)"
            className={BTN_SECONDARY}
          >
            {job && !["completed", "failed"].includes(job.status) ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Cpu className="w-3.5 h-3.5" />}
            Extract facts from documents (AI)
          </button>
        )}
      />

      {job && (
        <div className={`${CARD} p-4 text-[13px] flex flex-wrap items-center gap-3`}>
          <Badge tone={job.status === "completed" ? "good" : job.status === "failed" ? "bad" : "ai"}>{job.status}</Badge>
          <span className="text-slate-600">{job.stage}</span>
          {job.result && (
            <span className="text-slate-700">
              {job.result.proposed} fact(s) proposed for approval · {job.result.rejected_unverifiable} discarded because their quoted evidence was not in the document · {job.result.duplicates} already known
            </span>
          )}
          {job.error && <span className="text-rose-700">{job.error}</span>}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Verify */}
        <div className="xl:col-span-5 space-y-4">
          <div className={`${CARD} p-5 space-y-3`}>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><Search className="w-4 h-4 text-slate-400" /> Verify marketing copy</h3>
              {example && <button onClick={() => setText(example)} className="text-xs font-semibold text-indigo-600 hover:underline">Load example</button>}
            </div>
            <label htmlFor="pt-text" className="sr-only">Marketing copy</label>
            <textarea id="pt-text" value={text} onChange={(e) => setText(e.target.value)} rows={5} maxLength={8000}
                      placeholder="Paste copy that mentions a product, price or specification…" className={`${INPUT} py-3 resize-y leading-relaxed`} />
            <div className="flex justify-end">
              <button onClick={verify} disabled={verifying || !text.trim()} className={BTN_PRIMARY}>
                {verifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                {verifying ? "Verifying…" : "Verify claims"}
              </button>
            </div>
            <ErrorNote message={verifyError} />
          </div>

          {result && (
            <div className={`${CARD} p-5 space-y-3`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-bold text-slate-900">Result</h3>
                <Badge tone={result.verdict === "Verified" ? "good" : result.verdict === "Contradicted" ? "bad" : "warn"}>{result.verdict}</Badge>
              </div>
              <p className="text-xs text-slate-500">
                Product{result.products_detected.length !== 1 ? "s" : ""}: {result.products_detected.join(", ") || "none identified"}
                {result.product_inferred && " (assumed — it is the only product on record)"}
              </p>
              {result.claims.length === 0 ? (
                <p className="text-[13px] text-slate-500">No measurable product statements (prices, hours, GB, TOPS, warranty years…) were found.</p>
              ) : (
                <ul className="space-y-2.5">
                  {result.claims.map((c, i) => (
                    <li key={i} className="rounded-xl border border-slate-200 p-3.5 space-y-1.5">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <Badge tone={STATUS_TONE[c.status]}>{c.status}</Badge>
                        <span className="text-xs font-medium text-slate-500">{c.attribute_label}{c.product ? ` · ${c.product}` : ""}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[13px]">
                        <div><div className="text-[11px] text-slate-400">Submitted</div><div className="font-semibold text-slate-900">{c.submitted_value}</div></div>
                        <div><div className="text-[11px] text-slate-400">Approved</div><div className="font-semibold text-slate-900">{c.approved_value ?? <span className="text-slate-400 font-medium">none on record</span>}</div></div>
                      </div>
                      <p className="text-xs text-slate-600">{c.explanation}</p>
                      {c.source_document && (
                        <div className="text-[11px] text-slate-500 flex items-start gap-1.5">
                          <FileText className="w-3.5 h-3.5 mt-px shrink-0" />
                          <span>{c.source_document}{c.page_reference ? ` · page ${c.page_reference}` : ""}{c.evidence_excerpt && <> — <i>“{c.evidence_excerpt}”</i></>}</span>
                        </div>
                      )}
                      {c.suggestion && <div className="text-xs font-medium text-indigo-700">→ {c.suggestion}</div>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* Knowledge */}
        <div className="xl:col-span-7 space-y-4">
          <ErrorNote message={loadError || adminError} />
          {!data ? <Loading label="Loading product knowledge…" /> : (
            <>
              {isAdmin && (
                <div className={`${CARD} p-4 flex flex-col sm:flex-row gap-2`}>
                  <label htmlFor="pt-new" className="sr-only">New product name</label>
                  <input id="pt-new" value={newProduct} onChange={(e) => setNewProduct(e.target.value)} placeholder="New product name" className={`${INPUT} h-10`} />
                  <button className={BTN_SECONDARY + " h-10"} disabled={newProduct.trim().length < 2}
                          onClick={() => act(async () => { await createProduct({ name: newProduct.trim() }); setNewProduct(""); })}>
                    <Plus className="w-3.5 h-3.5" /> Add product
                  </button>
                </div>
              )}
              {pendingCount > 0 && (
                <div className="text-[13px] text-violet-800 bg-violet-50 border border-violet-200 rounded-xl px-4 py-2.5">
                  {pendingCount} AI-proposed fact(s) are waiting for an administrator. They are not used for verification until approved.
                </div>
              )}
              {data.products.length === 0 && (
                <div className={`${CARD} p-8 text-center text-[13px] text-slate-500`}>No products yet. {isAdmin ? "Add one above, or extract facts from your guidelines." : "Ask an administrator to add your products."}</div>
              )}
              {data.products.map((p) => (
                <div key={p.id} className={`${CARD} overflow-hidden`}>
                  <div className="px-5 py-4 flex flex-wrap items-center justify-between gap-2 border-b border-slate-100">
                    <div>
                      <div className="text-[15px] font-bold text-slate-900">{p.name}</div>
                      <div className="text-xs text-slate-500">{p.model_number ? `Model ${p.model_number}` : "No model number recorded"} · {p.facts.filter((f) => f.is_current).length} current fact(s)</div>
                    </div>
                    {isAdmin && (
                      <button className={BTN_SECONDARY} onClick={() => setFactForm({ productId: p.id, attribute: "battery", value: "", source: "", page: "" })}>
                        <Plus className="w-3.5 h-3.5" /> Add approved fact
                      </button>
                    )}
                  </div>
                  {factForm?.productId === p.id && (
                    <div className="px-5 py-4 bg-slate-50/70 border-b border-slate-100 grid grid-cols-1 sm:grid-cols-6 gap-2">
                      <select aria-label="Attribute" value={factForm.attribute} onChange={(e) => setFactForm({ ...factForm, attribute: e.target.value })} className={`${INPUT} h-10 sm:col-span-2`}>
                        {Object.entries(data.attributes).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                      </select>
                      <input aria-label="Approved value" value={factForm.value} onChange={(e) => setFactForm({ ...factForm, value: e.target.value })} placeholder="e.g. Up to 18 hours" className={`${INPUT} h-10 sm:col-span-2`} />
                      <input aria-label="Source document" value={factForm.source} onChange={(e) => setFactForm({ ...factForm, source: e.target.value })} placeholder="Source document" className={`${INPUT} h-10 sm:col-span-2`} />
                      <input aria-label="Page" value={factForm.page} onChange={(e) => setFactForm({ ...factForm, page: e.target.value.replace(/\D/g, "") })} placeholder="Page" className={`${INPUT} h-10`} />
                      <div className="sm:col-span-5 flex justify-end gap-2">
                        <button className={BTN_SECONDARY} onClick={() => setFactForm(null)}>Cancel</button>
                        <button className={BTN_SECONDARY + " text-indigo-700"} disabled={!factForm.value.trim() || factForm.source.trim().length < 2}
                                onClick={() => act(async () => {
                                  await addProductFact(p.id, { attribute: factForm.attribute, value_text: factForm.value.trim(), source_document: factForm.source.trim(), page_reference: factForm.page ? Number(factForm.page) : undefined });
                                  setFactForm(null);
                                })}>
                          <Check className="w-3.5 h-3.5" /> Approve fact
                        </button>
                      </div>
                    </div>
                  )}
                  {p.facts.length === 0 ? (
                    <p className="px-5 py-4 text-[13px] text-slate-500">No facts yet.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-[13px]">
                        <thead>
                          <tr className="text-left text-xs text-slate-500 bg-slate-50/60 border-b border-slate-100">
                            <th className="px-5 py-2 font-medium">Attribute</th><th className="px-3 py-2 font-medium">Value</th>
                            <th className="px-3 py-2 font-medium">Source</th><th className="px-5 py-2 font-medium text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {p.facts.map((f) => (
                            <tr key={f.id} className="border-b border-slate-100 last:border-0 align-top">
                              <td className="px-5 py-2.5 text-slate-600 whitespace-nowrap">{f.attribute_label}</td>
                              <td className="px-3 py-2.5 font-medium text-slate-900">{f.value_text}</td>
                              <td className="px-3 py-2.5 text-xs text-slate-500">
                                {f.source_document || "—"}{f.page_reference ? ` · p.${f.page_reference}` : ""}
                                {f.origin.startsWith("llm") && <div className="mt-0.5"><Badge tone="ai"><Sparkles className="w-3 h-3" /> AI proposal</Badge></div>}
                                {!f.evidence_excerpt && f.status === "approved" && <div className="mt-0.5 text-amber-600">No document passage found</div>}
                              </td>
                              <td className="px-5 py-2.5 text-right whitespace-nowrap">
                                {f.status === "pending" && isAdmin ? (
                                  <div className="inline-flex gap-1">
                                    <button aria-label="Approve fact" onClick={() => act(() => approveProductFact(f.id))} className="p-1.5 rounded-lg text-emerald-700 hover:bg-emerald-50"><Check className="w-4 h-4" /></button>
                                    <button aria-label="Reject fact" onClick={() => act(() => rejectProductFact(f.id))} className="p-1.5 rounded-lg text-rose-700 hover:bg-rose-50"><X className="w-4 h-4" /></button>
                                  </div>
                                ) : (
                                  <Badge tone={f.expired ? "neutral" : FACT_TONE[f.status]}>{f.expired ? "expired" : f.status}</Badge>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
