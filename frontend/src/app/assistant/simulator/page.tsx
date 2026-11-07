"use client";

import { useEffect, useMemo, useState } from "react";
import { FlaskConical, Loader2, Plus, Minus, ArrowRight, Search } from "lucide-react";
import { fetchSubmissions, fetchScenarios, runSimulation, Submission, Simulation } from "@/lib/api";
import { CARD, Badge, PageHeader, ErrorNote, Loading, BTN_PRIMARY, INPUT } from "@/components/engines/ui";

const PARAMS: Record<string, { key: string; label: string; placeholder: string }[]> = {
  price_change: [{ key: "new_price", label: "New price (₹)", placeholder: "74999" }],
  tagline_change: [{ key: "find", label: "Replace this text", placeholder: "exact text from the campaign" }, { key: "replace", label: "With", placeholder: "new wording" }],
  translate: [{ key: "language", label: "Language", placeholder: "Hindi" }],
  product_discontinued: [{ key: "product", label: "Product (optional)", placeholder: "leave empty for the product named in the copy" }],
};

function FindingRow({ f, tone }: { f: Simulation["introduced"][number]; tone: "bad" | "good" }) {
  return (
    <li className={`rounded-xl border p-3 ${tone === "bad" ? "border-rose-200 bg-rose-50/40" : "border-emerald-200 bg-emerald-50/40"}`}>
      <div className="flex flex-wrap items-center gap-1.5">
        {tone === "bad" ? <Plus className="w-3.5 h-3.5 text-rose-600" /> : <Minus className="w-3.5 h-3.5 text-emerald-600" />}
        <Badge tone={f.severity === "CRITICAL" ? "bad" : f.severity === "WARNING" ? "warn" : "neutral"}>{f.severity}</Badge>
        <span className="text-xs text-slate-500">{f.category}</span>
      </div>
      <div className="mt-1 text-[13px] font-semibold text-slate-900">“{f.text}”</div>
      <p className="text-xs text-slate-600">{f.explanation}</p>
    </li>
  );
}

export default function SimulatorPage() {
  const [subs, setSubs] = useState<Submission[] | null>(null);
  const [scenarios, setScenarios] = useState<{ key: string; label: string }[]>([]);
  const [filter, setFilter] = useState("");
  const [sub, setSub] = useState<Submission | null>(null);
  const [scenario, setScenario] = useState("price_change");
  const [params, setParams] = useState<Record<string, string>>({});
  const [result, setResult] = useState<Simulation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSubmissions().then(setSubs).catch((e) => setError(e.message));
    fetchScenarios().then((r) => setScenarios(r.scenarios)).catch(() => {});
  }, []);
  const list = useMemo(() => (subs || []).filter((s) => s.title.toLowerCase().includes(filter.toLowerCase())), [subs, filter]);

  const run = async () => {
    if (!sub) return;
    setBusy(true); setError(null); setResult(null);
    try { setResult(await runSimulation(sub.id, scenario, params)); }
    catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/assistant", label: "Brand Assistant" }}
        eyebrow="Campaign Stress Testing" icon={<FlaskConical className="w-3.5 h-3.5" />}
        title="What happens if we change it?"
        description="Try a hypothetical change on a copy of a campaign. The real checks run on both versions and show which risks appear or disappear. Simulations never change the campaign or your Brand DNA."
      />
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className="xl:col-span-4 space-y-4">
          <div className={`${CARD} p-4`}>
            <div className="text-xs font-semibold text-slate-500 mb-2">1 · Choose a campaign</div>
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" aria-hidden />
              <input aria-label="Filter campaigns" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter campaigns" className={`${INPUT} h-10 pl-9`} />
            </div>
            {!subs ? <Loading /> : (
              <ul className="mt-2 max-h-72 overflow-y-auto divide-y divide-slate-100">
                {list.map((s) => (
                  <li key={s.id}>
                    <button onClick={() => { setSub(s); setResult(null); }} className={`w-full text-left px-2.5 py-2 rounded-lg ${sub?.id === s.id ? "bg-indigo-50" : "hover:bg-slate-50"}`}>
                      <div className="text-[13px] font-semibold text-slate-800 truncate">{s.title}</div>
                      <div className="text-[11px] text-slate-500 truncate">{s.content}</div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className={`${CARD} p-4 space-y-3`}>
            <div className="text-xs font-semibold text-slate-500">2 · Choose a hypothetical change</div>
            <select aria-label="Scenario" value={scenario} onChange={(e) => { setScenario(e.target.value); setParams({}); setResult(null); }} className={`${INPUT} h-10`}>
              {scenarios.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
            {(PARAMS[scenario] || []).map((p) => (
              <label key={p.key} className="block text-xs text-slate-600">{p.label}
                <input value={params[p.key] || ""} onChange={(e) => setParams({ ...params, [p.key]: e.target.value })} placeholder={p.placeholder} className={`${INPUT} h-10 mt-1`} />
              </label>
            ))}
            <button onClick={run} disabled={!sub || busy} className={BTN_PRIMARY + " w-full"}>
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />} Run simulation
            </button>
            <ErrorNote message={error} />
          </div>
        </div>

        <div className="xl:col-span-8 space-y-4">
          {!result ? (
            <div className={`${CARD} p-10 text-center`}>
              <FlaskConical className="w-8 h-8 text-indigo-400 mx-auto" />
              <h3 className="mt-3 text-base font-bold text-slate-900">No simulation yet</h3>
              <p className="mt-1 text-[13px] text-slate-500 max-w-md mx-auto">Pick a campaign and a change, for example the price dropping to ₹69,999, then run the simulation.</p>
            </div>
          ) : (
            <>
              <div className="rounded-xl border border-violet-200 bg-violet-50 px-4 py-2.5 text-[13px] text-violet-900 font-medium">
                Hypothetical — {result.note}
              </div>
              <div className={`${CARD} p-5`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="text-xs text-slate-500">{result.scenario_label}</div>
                    <div className="text-[13px] text-slate-700">{result.changes.join(" · ")}</div>
                  </div>
                  {!result.score_comparable ? (
                    <span className="text-xs text-slate-500">Scores are not comparable across languages</span>
                  ) : (
                  <div className="flex items-center gap-2 text-sm font-semibold tabular-nums">
                    <span className="text-slate-500">{result.original.score}</span>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                    <span className={result.score_delta < 0 ? "text-rose-600" : result.score_delta > 0 ? "text-emerald-600" : "text-slate-900"}>{result.simulated.score}</span>
                    <Badge tone={result.score_delta < 0 ? "bad" : result.score_delta > 0 ? "good" : "neutral"}>{result.score_delta > 0 ? "+" : ""}{result.score_delta}</Badge>
                  </div>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className={`${CARD} p-4`}><div className="text-xs font-semibold text-slate-500 mb-1.5">Original</div><p className="text-sm text-slate-800 whitespace-pre-wrap">{result.original.text}</p></div>
                <div className={`${CARD} p-4 ring-1 ring-violet-200`}><div className="text-xs font-semibold text-violet-600 mb-1.5">Hypothetical</div><p className="text-sm text-slate-800 whitespace-pre-wrap">{result.simulated.text}</p></div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className={`${CARD} p-5`}>
                  <h4 className="text-sm font-bold text-slate-900">New risks ({result.introduced.length + result.product_truth_changes.filter((c) => c.status !== "Supported").length})</h4>
                  <ul className="mt-2 space-y-2">
                    {result.introduced.map((f, i) => <FindingRow key={i} f={f} tone="bad" />)}
                    {result.product_truth_changes.filter((c) => c.status !== "Supported").map((c, i) => (
                      <li key={`t${i}`} className="rounded-xl border border-rose-200 bg-rose-50/40 p-3 text-xs">
                        <Badge tone="bad">{c.status}</Badge> <span className="font-semibold text-slate-900">{c.attribute_label}: {c.submitted_value}</span>
                        {c.approved_value && <span className="text-slate-600"> · approved {c.approved_value} ({c.source_document})</span>}
                      </li>
                    ))}
                    {!result.introduced.length && !result.product_truth_changes.some((c) => c.status !== "Supported") && <li className="text-[13px] text-slate-500">None.</li>}
                  </ul>
                </div>
                <div className={`${CARD} p-5`}>
                  <h4 className="text-sm font-bold text-slate-900">Resolved ({result.resolved.length})</h4>
                  <ul className="mt-2 space-y-2">
                    {result.resolved.map((f, i) => <FindingRow key={i} f={f} tone="good" />)}
                    {!result.resolved.length && <li className="text-[13px] text-slate-500">None. {result.unchanged} finding(s) stay the same.</li>}
                  </ul>
                  {result.not_rechecked.length > 0 && (
                    <p className="mt-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                      {result.not_rechecked.length} source-language finding(s) were not re-checked in the translation (the wording checks are language-specific), so they are not counted as resolved. Use the Translation Guard result for the translated claims.
                    </p>
                  )}
                </div>
              </div>
              {result.translation && (
                <div className={`${CARD} p-5`}>
                  <h4 className="text-sm font-bold text-slate-900">Translation check ({result.translation.language}) <Badge tone={result.translation.verdict === "Consistent" ? "good" : "warn"}>{result.translation.verdict}</Badge></h4>
                  <ul className="mt-2 space-y-1 text-xs text-slate-700">{result.translation.findings.map((f, i) => <li key={i}>• {f.severity}: {f.title}</li>)}</ul>
                </div>
              )}
              <div className={`${CARD} p-5`}>
                <h4 className="text-sm font-bold text-slate-900">Recommended actions</h4>
                <ul className="mt-2 space-y-1.5">{result.recommendations.map((r, i) => <li key={i} className="text-[13px] text-indigo-700">→ {r}</li>)}</ul>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
