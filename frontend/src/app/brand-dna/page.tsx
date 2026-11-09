"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { useOrganization } from "@/lib/useOrganization";
import {
  Dna,
  Upload,
  CheckCircle,
  FileText,
  AlertCircle,
  Plus,
  Shield,
  Layers,
  BookOpen,
  DollarSign
} from "lucide-react";
import {
  fetchRules,
  fetchFacts,
  fetchTerms,
  fetchGuidelines,
  confirmRule,
  uploadGuideline,
  BrandRule,
  ApprovedFact,
  TerminologyRule,
  BrandGuideline
} from "@/lib/api";

export default function BrandDNAStudio() {
  const org = useOrganization();
  const [rules, setRules] = useState<BrandRule[]>([]);
  const [facts, setFacts] = useState<ApprovedFact[]>([]);
  const [terms, setTerms] = useState<TerminologyRule[]>([]);
  const [guidelines, setGuidelines] = useState<BrandGuideline[]>([]);
  const [activeTab, setActiveTab] = useState<"rules" | "facts" | "terms" | "guidelines">("rules");
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [replaces, setReplaces] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = () => {
    fetchRules().then(setRules).catch(console.error);
    fetchFacts().then(setFacts).catch(console.error);
    fetchTerms().then(setTerms).catch(console.error);
    fetchGuidelines().then(setGuidelines).catch(console.error);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleConfirmRule = async (ruleId: string) => {
    try {
      await confirmRule(ruleId);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadSuccess(null);
    setUploadError(null);
    try {
      const res = await uploadGuideline(undefined, file, replaces || undefined);
      const replaced = guidelines.find((g) => g.id === replaces);
      setUploadSuccess(`Ingested '${res.filename}' (${res.total_pages} section${res.total_pages === 1 ? "" : "s"})${replaced ? ` — '${replaced.filename}' is now kept as history and no longer cited as evidence` : ""}. New rules wait for your confirmation.`);
      setReplaces("");
      loadData();
    } catch (err: any) {
      setUploadError(err?.message || "Upload failed.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const getCategoryTheme = (cat: string) => {
    const c = (cat || "").toLowerCase();
    if (c.includes("price") || c.includes("pricing")) return "bg-amber-50 text-amber-700 border-amber-200";
    if (c.includes("tone") || c.includes("voice")) return "bg-purple-50 text-purple-700 border-purple-200";
    if (c.includes("claim")) return "bg-sky-50 text-sky-700 border-sky-200";
    if (c.includes("term")) return "bg-rose-50 text-rose-700 border-rose-200";
    return "bg-indigo-50 text-indigo-700 border-indigo-200";
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-600 uppercase mb-1 tracking-wider">
            <Dna className="w-3.5 h-3.5" />
            <span>Brand DNA Studio // Knowledge Management</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Brand Governance Profile: <span className="text-indigo-600">{org?.name || "…"}</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Ingest guidelines, verify extracted policies, manage ground-truth facts, and enforce approved terminology.
          </p>
        </div>

        {/* Upload Trigger */}
        <div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.docx,.html,.htm,.md,.txt,.csv,.xlsx"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white shadow-sm shadow-indigo-200 transition-all flex items-center space-x-2"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>{uploading ? "Ingesting…" : "Upload guideline"}</span>
          </button>
          <select value={replaces} onChange={(e) => setReplaces(e.target.value)} aria-label="Replaces an existing document"
                  className="h-10 px-2.5 rounded-xl text-xs text-slate-700 bg-white border border-slate-200 max-w-[220px]">
            <option value="">New document</option>
            {guidelines.filter((g) => g.status !== "superseded").map((g) => <option key={g.id} value={g.id}>Replaces: {g.filename}</option>)}
          </select>
          <Link href="/brand-dna/products" className="h-10 px-3.5 inline-flex items-center gap-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:border-indigo-300 hover:text-indigo-700 transition-colors">Product Truth</Link>
          <Link href="/brand-dna/knowledge-gaps" className="h-10 px-3.5 inline-flex items-center gap-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:border-indigo-300 hover:text-indigo-700 transition-colors">Knowledge gaps</Link>
        </div>
      </div>

      <p className="-mt-3 text-[11px] text-slate-500">Accepted: PDF, Word (.docx), HTML, Markdown/text, and CSV/Excel price lists. Passages are cited by page, section or row. Price-list rows for known products become pending facts in Product Truth.</p>
      {uploadError && (
        <div role="alert" className="p-3 rounded-xl border border-rose-200 bg-rose-50 text-xs text-rose-800">{uploadError}</div>
      )}
      {uploadSuccess && (
        <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/80 text-xs text-emerald-800 flex items-center justify-between font-medium">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{uploadSuccess}</span>
          </div>
          <button onClick={() => setUploadSuccess(null)} className="text-emerald-600 hover:text-emerald-800 font-bold ml-4">×</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-2 text-xs font-medium">
        <button
          onClick={() => setActiveTab("rules")}
          className={`px-3.5 py-2 rounded-xl transition-all ${
            activeTab === "rules"
              ? "bg-white text-indigo-700 font-bold shadow-sm ring-1 ring-slate-200/80"
              : "text-slate-500 hover:text-slate-900 hover:bg-slate-100/70"
          }`}
        >
          Brand Rules ({rules.length})
        </button>
        <button
          onClick={() => setActiveTab("facts")}
          className={`px-3.5 py-2 rounded-xl transition-all ${
            activeTab === "facts"
              ? "bg-white text-indigo-700 font-bold shadow-sm ring-1 ring-slate-200/80"
              : "text-slate-500 hover:text-slate-900 hover:bg-slate-100/70"
          }`}
        >
          Approved Facts & Pricing ({facts.length})
        </button>
        <button
          onClick={() => setActiveTab("terms")}
          className={`px-3.5 py-2 rounded-xl transition-all ${
            activeTab === "terms"
              ? "bg-white text-indigo-700 font-bold shadow-sm ring-1 ring-slate-200/80"
              : "text-slate-500 hover:text-slate-900 hover:bg-slate-100/70"
          }`}
        >
          Approved Terminology ({terms.length})
        </button>
        <button
          onClick={() => setActiveTab("guidelines")}
          className={`px-3.5 py-2 rounded-xl transition-all ${
            activeTab === "guidelines"
              ? "bg-white text-indigo-700 font-bold shadow-sm ring-1 ring-slate-200/80"
              : "text-slate-500 hover:text-slate-900 hover:bg-slate-100/70"
          }`}
        >
          Source Documents ({guidelines.length})
        </button>
      </div>

      {/* TAB 1: Brand Rules */}
      {activeTab === "rules" && (
        <div className="space-y-4">
          <div className="text-xs text-slate-500">
            Automatically extracted policies require administrator confirmation before becoming active brand truth.
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className="p-5 rounded-2xl border border-slate-200/90 bg-white shadow-sm flex flex-col justify-between space-y-3 hover:shadow-md transition-shadow"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-md border ${getCategoryTheme(rule.category)}`}>
                      {rule.category}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        rule.severity === "CRITICAL"
                          ? "bg-rose-50 text-rose-700 border-rose-200"
                          : "bg-amber-50 text-amber-700 border-amber-200"
                      }`}
                    >
                      {rule.severity}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-900">{rule.title}</h4>
                  <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">{rule.rule_text}</p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="truncate max-w-[200px]">Source: {rule.source_document || "Brand Manual"} (p. {rule.page_reference || 1})</span>
                  {rule.is_confirmed ? (
                    <span className="flex items-center space-x-1.5 text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md font-bold text-[10px]">
                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                      <span>CONFIRMED</span>
                    </span>
                  ) : (
                    <button
                      onClick={() => handleConfirmRule(rule.id)}
                      className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-sm transition-colors"
                    >
                      Confirm Rule
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: Approved Facts & Pricing */}
      {activeTab === "facts" && (
        <div className="space-y-4">
          <div className="border border-slate-200/90 rounded-2xl bg-white shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
              <span className="text-xs font-bold text-slate-900">Verified Enterprise Truth Records</span>
              <span className="text-[11px] text-indigo-600 font-medium">Ground Truth for ClaimDNA Engine</span>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/40 border-b border-slate-100 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-4">Category</th>
                  <th className="py-2.5 px-4">Fact / Parameter</th>
                  <th className="py-2.5 px-4">Approved Value</th>
                  <th className="py-2.5 px-4">Verification Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {facts.map((fact) => (
                  <tr key={fact.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4">
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {fact.category}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">{fact.fact_key}</td>
                    <td className="py-3.5 px-4 font-bold text-indigo-700">{fact.fact_value}</td>
                    <td className="py-3.5 px-4 text-slate-500 text-[11px]">{fact.verification_source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: Approved Terminology */}
      {activeTab === "terms" && (
        <div className="space-y-4">
          <div className="border border-slate-200/90 rounded-2xl bg-white shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
              <span className="text-xs font-bold text-slate-900">Prohibited vs Preferred Terminology</span>
              <span className="text-[11px] text-rose-600 font-semibold">Strict Lexicon Enforcement</span>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/40 border-b border-slate-100 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-2.5 px-4">Prohibited Phrase</th>
                  <th className="py-2.5 px-4">Approved Replacement</th>
                  <th className="py-2.5 px-4">Brand Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {terms.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-rose-700">
                      <span className="bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-md line-through">
                        &quot;{t.prohibited_term}&quot;
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-emerald-700">
                      <span className="bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-md">
                        &quot;{t.preferred_term}&quot;
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 text-xs">{t.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: Source Documents */}
      {activeTab === "guidelines" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {guidelines.map((g) => (
              <div key={g.id} className="p-5 rounded-2xl border border-slate-200/90 bg-white shadow-sm space-y-3 hover:shadow-md transition-shadow">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="truncate">
                    <div className="text-xs font-bold text-slate-900 truncate">{g.filename}</div>
                    <div className="text-[11px] text-slate-400">Total Pages: {g.total_pages}</div>
                  </div>
                </div>
                <div className="text-xs text-slate-500 pt-2 border-t border-slate-100 space-y-1">
                  <div className="flex justify-between">
                    <span>Document Type:</span>
                    <span className="font-semibold text-slate-700 uppercase">{g.file_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ingestion Status:</span>
                    <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.2 rounded border border-emerald-200 text-[10px]">
                      {g.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Uploaded Date:</span>
                    <span className="text-slate-700">{new Date(g.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
