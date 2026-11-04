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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#262626] pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
            <Dna className="w-3.5 h-3.5 text-[#A3A3A3]" />
            <span>Brand DNA Studio // Knowledge Management</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#FFFFFF]">Brand Governance Profile: NOVA TECH</h2>
          <p className="text-xs text-[#A3A3A3] mt-0.5">
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
            className="px-3.5 py-2 text-xs font-mono font-medium rounded border border-[#737373] bg-[#F5F5F5] text-[#0A0A0A] hover:bg-[#FFFFFF] transition-all flex items-center space-x-2 shadow-sm"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>{uploading ? "INGESTING PDF..." : "UPLOAD GUIDELINE (PDF/TXT)"}</span>
          </button>
        </div>
      </div>

      {uploadSuccess && (
        <div className="p-3 rounded border border-[#404040] bg-[#171717] text-xs font-mono text-[#FFFFFF] flex items-center justify-between">
          <span>{uploadSuccess}</span>
          <button onClick={() => setUploadSuccess(null)} className="text-[#A3A3A3] hover:text-[#FFFFFF]">×</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-[#262626] pb-1 text-xs font-mono">
        <button
          onClick={() => setActiveTab("rules")}
          className={`px-3 py-1.5 rounded transition-colors ${
            activeTab === "rules"
              ? "bg-[#171717] text-[#FFFFFF] font-medium border border-[#404040]"
              : "text-[#737373] hover:text-[#FFFFFF]"
          }`}
        >
          Brand Rules ({rules.length})
        </button>
        <button
          onClick={() => setActiveTab("facts")}
          className={`px-3 py-1.5 rounded transition-colors ${
            activeTab === "facts"
              ? "bg-[#171717] text-[#FFFFFF] font-medium border border-[#404040]"
              : "text-[#737373] hover:text-[#FFFFFF]"
          }`}
        >
          Approved Facts & Pricing ({facts.length})
        </button>
        <button
          onClick={() => setActiveTab("terms")}
          className={`px-3 py-1.5 rounded transition-colors ${
            activeTab === "terms"
              ? "bg-[#171717] text-[#FFFFFF] font-medium border border-[#404040]"
              : "text-[#737373] hover:text-[#FFFFFF]"
          }`}
        >
          Approved Terminology ({terms.length})
        </button>
        <button
          onClick={() => setActiveTab("guidelines")}
          className={`px-3 py-1.5 rounded transition-colors ${
            activeTab === "guidelines"
              ? "bg-[#171717] text-[#FFFFFF] font-medium border border-[#404040]"
              : "text-[#737373] hover:text-[#FFFFFF]"
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
                className="p-4 rounded border border-[#262626] bg-[#121212] flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-[#404040] bg-[#171717] text-[#FFFFFF]">
                      {rule.category}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                        rule.severity === "CRITICAL"
                          ? "bg-[#171717] text-[#FFFFFF] border-[#737373]"
                          : "bg-[#0A0A0A] text-[#A3A3A3] border-[#262626]"
                      }`}
                    >
                      {rule.severity}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-[#FFFFFF]">{rule.title}</h4>
                  <p className="text-xs text-[#A3A3A3] mt-1 leading-relaxed">{rule.rule_text}</p>
                </div>

                <div className="pt-2 border-t border-[#262626] flex items-center justify-between text-[11px] font-mono text-[#737373]">
                  <span>Source: {rule.source_document || "Brand Manual"} (p. {rule.page_reference || 1})</span>
                  {rule.is_confirmed ? (
                    <span className="flex items-center space-x-1 text-[#FFFFFF]">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>CONFIRMED</span>
                    </span>
                  ) : (
                    <button
                      onClick={() => handleConfirmRule(rule.id)}
                      className="px-2 py-1 rounded bg-[#F5F5F5] text-[#0A0A0A] font-medium hover:bg-[#FFFFFF] transition-colors"
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
          <div className="border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
            <div className="p-3.5 border-b border-[#262626] flex items-center justify-between">
              <span className="text-xs font-semibold text-[#FFFFFF]">Verified Enterprise Truth Records</span>
              <span className="text-[10px] font-mono text-[#737373]">Used by ClaimDNA for automated fact checking</span>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0A0A0A] border-b border-[#262626] text-[#737373] font-mono uppercase text-[10px]">
                <tr>
                  <th className="py-2 px-4">Category</th>
                  <th className="py-2 px-4">Fact / Parameter</th>
                  <th className="py-2 px-4">Approved Value</th>
                  <th className="py-2 px-4">Verification Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#262626]">
                {facts.map((fact) => (
                  <tr key={fact.id} className="hover:bg-[#171717] transition-colors">
                    <td className="py-3 px-4 font-mono text-[11px] text-[#A3A3A3]">{fact.category}</td>
                    <td className="py-3 px-4 font-medium text-[#FFFFFF]">{fact.fact_key}</td>
                    <td className="py-3 px-4 font-mono font-bold text-[#FFFFFF]">{fact.fact_value}</td>
                    <td className="py-3 px-4 text-[#A3A3A3] text-[11px] font-mono">{fact.verification_source}</td>
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
          <div className="border border-[#262626] rounded-lg bg-[#121212] overflow-hidden">
            <div className="p-3.5 border-b border-[#262626] flex items-center justify-between">
              <span className="text-xs font-semibold text-[#FFFFFF]">Prohibited vs Preferred Terminology</span>
              <span className="text-[10px] font-mono text-[#737373]">Strict Lexicon Enforcement</span>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0A0A0A] border-b border-[#262626] text-[#737373] font-mono uppercase text-[10px]">
                <tr>
                  <th className="py-2 px-4">Prohibited Phrase</th>
                  <th className="py-2 px-4">Approved Replacement</th>
                  <th className="py-2 px-4">Brand Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#262626]">
                {terms.map((t) => (
                  <tr key={t.id} className="hover:bg-[#171717] transition-colors">
                    <td className="py-3 px-4 font-mono text-[#FFFFFF] line-through decoration-[#737373]">"{t.prohibited_term}"</td>
                    <td className="py-3 px-4 font-mono text-[#FFFFFF] font-bold">"{t.preferred_term}"</td>
                    <td className="py-3 px-4 text-[#A3A3A3] text-xs">{t.explanation}</td>
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
              <div key={g.id} className="p-4 rounded border border-[#262626] bg-[#121212] space-y-2">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-[#FFFFFF]" />
                  <span className="text-xs font-bold text-[#FFFFFF]">{g.filename}</span>
                </div>
                <div className="text-[11px] font-mono text-[#A3A3A3] space-y-1">
                  <div>Type: {g.file_type.toUpperCase()} | Total Pages: {g.total_pages}</div>
                  <div>Status: <span className="text-[#FFFFFF]">{g.status.toUpperCase()}</span></div>
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
