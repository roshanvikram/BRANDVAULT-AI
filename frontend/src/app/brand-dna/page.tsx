"use client";

import { useEffect, useState, useRef } from "react";
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
  const [rules, setRules] = useState<BrandRule[]>([]);
  const [facts, setFacts] = useState<ApprovedFact[]>([]);
  const [terms, setTerms] = useState<TerminologyRule[]>([]);
  const [guidelines, setGuidelines] = useState<BrandGuideline[]>([]);
  const [activeTab, setActiveTab] = useState<"rules" | "facts" | "terms" | "guidelines">("rules");
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
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
    try {
      const res = await uploadGuideline("nova-tech-org-001", file);
      setUploadSuccess(`Successfully ingested '${res.filename}' (${res.total_pages} pages parsed).`);
      loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E5E5E5] pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
            <Dna className="w-3.5 h-3.5 text-[#0A0A0A]" />
            <span className="font-semibold">Brand DNA Studio // Knowledge Management</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A]">Brand Governance Profile: NOVA TECH</h2>
          <p className="text-xs text-[#737373] mt-0.5">
            Ingest guidelines, verify extracted policies, manage ground-truth facts, and enforce approved terminology.
          </p>
        </div>

        {/* Upload Trigger */}
        <div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.txt,.docx"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2.5 text-xs font-mono font-semibold rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#262626] transition-all flex items-center space-x-2 shadow-sm"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>{uploading ? "INGESTING PDF..." : "UPLOAD GUIDELINE (PDF/TXT)"}</span>
          </button>
        </div>
      </div>

      {uploadSuccess && (
        <div className="p-3.5 rounded-lg border border-[#E5E5E5] bg-[#F5F5F5] text-xs font-mono text-[#0A0A0A] flex items-center justify-between">
          <span>{uploadSuccess}</span>
          <button onClick={() => setUploadSuccess(null)} className="text-[#737373] hover:text-[#0A0A0A]">×</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-[#E5E5E5] pb-2 text-xs font-mono">
        <button
          onClick={() => setActiveTab("rules")}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === "rules"
              ? "bg-[#0A0A0A] text-[#FFFFFF] font-bold shadow-sm"
              : "text-[#737373] hover:text-[#0A0A0A] hover:bg-[#F5F5F5]"
          }`}
        >
          Brand Rules ({rules.length})
        </button>
        <button
          onClick={() => setActiveTab("facts")}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === "facts"
              ? "bg-[#0A0A0A] text-[#FFFFFF] font-bold shadow-sm"
              : "text-[#737373] hover:text-[#0A0A0A] hover:bg-[#F5F5F5]"
          }`}
        >
          Approved Facts & Pricing ({facts.length})
        </button>
        <button
          onClick={() => setActiveTab("terms")}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === "terms"
              ? "bg-[#0A0A0A] text-[#FFFFFF] font-bold shadow-sm"
              : "text-[#737373] hover:text-[#0A0A0A] hover:bg-[#F5F5F5]"
          }`}
        >
          Approved Terminology ({terms.length})
        </button>
        <button
          onClick={() => setActiveTab("guidelines")}
          className={`px-3 py-1.5 rounded-lg transition-colors ${
            activeTab === "guidelines"
              ? "bg-[#0A0A0A] text-[#FFFFFF] font-bold shadow-sm"
              : "text-[#737373] hover:text-[#0A0A0A] hover:bg-[#F5F5F5]"
          }`}
        >
          Source Documents ({guidelines.length})
        </button>
      </div>

      {/* TAB 1: Brand Rules */}
      {activeTab === "rules" && (
        <div className="space-y-4">
          <div className="text-xs text-[#737373] font-mono">
            Automatically extracted policies must require administrator confirmation before activation.
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className="p-5 rounded-xl border border-[#E5E5E5] bg-[#FFFFFF] shadow-sm flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-[#E5E5E5] bg-[#F5F5F5] text-[#0A0A0A] font-semibold">
                      {rule.category}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded border font-semibold ${
                        rule.severity === "CRITICAL"
                          ? "bg-[#0A0A0A] text-[#FFFFFF] border-[#0A0A0A]"
                          : "bg-[#F5F5F5] text-[#404040] border-[#E5E5E5]"
                      }`}
                    >
                      {rule.severity}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-[#0A0A0A]">{rule.title}</h4>
                  <p className="text-xs text-[#404040] mt-1.5 leading-relaxed">{rule.rule_text}</p>
                </div>

                <div className="pt-3 border-t border-[#E5E5E5] flex items-center justify-between text-[11px] font-mono text-[#737373]">
                  <span>Source: {rule.source_document || "Brand Manual"} (p. {rule.page_reference || 1})</span>
                  {rule.is_confirmed ? (
                    <span className="flex items-center space-x-1 text-[#0A0A0A] font-bold">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>CONFIRMED</span>
                    </span>
                  ) : (
                    <button
                      onClick={() => handleConfirmRule(rule.id)}
                      className="px-2.5 py-1 rounded bg-[#0A0A0A] text-[#FFFFFF] font-bold hover:bg-[#262626] transition-colors"
                    >
                      CONFIRM RULE
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
          <div className="border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden">
            <div className="p-4 border-b border-[#E5E5E5] flex items-center justify-between bg-[#F5F5F5]">
              <span className="text-xs font-bold text-[#0A0A0A]">Verified Enterprise Truth Records</span>
              <span className="text-[10px] font-mono text-[#737373]">Used by ClaimDNA for automated fact checking</span>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FFFFFF] border-b border-[#E5E5E5] text-[#737373] font-mono uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4">Category</th>
                  <th className="py-2.5 px-4">Fact / Parameter</th>
                  <th className="py-2.5 px-4">Approved Value</th>
                  <th className="py-2.5 px-4">Verification Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E5]">
                {facts.map((fact) => (
                  <tr key={fact.id} className="hover:bg-[#F5F5F5] transition-colors">
                    <td className="py-3 px-4 font-mono text-[11px] text-[#737373]">{fact.category}</td>
                    <td className="py-3 px-4 font-semibold text-[#0A0A0A]">{fact.fact_key}</td>
                    <td className="py-3 px-4 font-mono font-bold text-[#0A0A0A]">{fact.fact_value}</td>
                    <td className="py-3 px-4 text-[#737373] text-[11px] font-mono">{fact.verification_source}</td>
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
          <div className="border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden">
            <div className="p-4 border-b border-[#E5E5E5] flex items-center justify-between bg-[#F5F5F5]">
              <span className="text-xs font-bold text-[#0A0A0A]">Prohibited vs Preferred Terminology</span>
              <span className="text-[10px] font-mono text-[#737373]">Strict Lexicon Enforcement</span>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FFFFFF] border-b border-[#E5E5E5] text-[#737373] font-mono uppercase text-[10px]">
                <tr>
                  <th className="py-2.5 px-4">Prohibited Phrase</th>
                  <th className="py-2.5 px-4">Approved Replacement</th>
                  <th className="py-2.5 px-4">Brand Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E5]">
                {terms.map((t) => (
                  <tr key={t.id} className="hover:bg-[#F5F5F5] transition-colors">
                    <td className="py-3 px-4 font-mono text-[#0A0A0A] line-through decoration-[#737373]">"{t.prohibited_term}"</td>
                    <td className="py-3 px-4 font-mono text-[#0A0A0A] font-bold">"{t.preferred_term}"</td>
                    <td className="py-3 px-4 text-[#404040] text-xs">{t.explanation}</td>
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
              <div key={g.id} className="p-5 rounded-xl border border-[#E5E5E5] bg-[#FFFFFF] shadow-sm space-y-2">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-[#0A0A0A]" />
                  <span className="text-xs font-bold text-[#0A0A0A]">{g.filename}</span>
                </div>
                <div className="text-[11px] font-mono text-[#737373] space-y-1">
                  <div>Type: {g.file_type.toUpperCase()} | Total Pages: {g.total_pages}</div>
                  <div>Status: <span className="text-[#0A0A0A] font-semibold">{g.status.toUpperCase()}</span></div>
                  <div>Uploaded: {new Date(g.created_at).toLocaleDateString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
