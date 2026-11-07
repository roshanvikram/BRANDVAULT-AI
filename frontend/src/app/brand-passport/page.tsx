"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Award,
  ShieldCheck,
  Printer,
  Download,
  CheckCircle2,
  Lock,
  FileText,
  Clock,
  Sparkles
} from "lucide-react";
import { fetchPassports, BrandPassport } from "@/lib/api";

export default function BrandPassportPage() {
  const [passports, setPassports] = useState<BrandPassport[]>([]);
  const [selectedPassport, setSelectedPassport] = useState<BrandPassport | null>(null);

  useEffect(() => {
    fetchPassports()
      .then((data) => {
        setPassports(data);
        if (data.length > 0) {
          setSelectedPassport(data[0]);
        }
      })
      .catch(console.error);
  }, []);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Header (Hidden during print) */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5 select-none">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-semibold border border-emerald-200">
              Brand Passport
            </span>
            <span className="text-[11px] text-slate-500">Cryptographic Governance Certificates</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">Official Brand Governance Passports</h2>
          <p className="text-[13px] text-slate-600 mt-0.5 max-w-2xl">
            Immutable, tamper-evident audit records verifying brand guideline compliance and human approval.
          </p>
        </div>

        <Link href="/brand-passport/verify" className="h-10 px-3.5 inline-flex items-center gap-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:border-indigo-300 hover:text-indigo-700 transition-colors">Verify a campaign</Link>
        {selectedPassport && (
          <button
            onClick={handlePrint}
            className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white transition-all flex items-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]"
          >
            <Printer className="w-3.5 h-3.5 text-indigo-200" />
            <span>Export / Print Passport</span>
          </button>
        )}
      </div>

      {passports.length === 0 ? (
        <div className="p-12 text-center border border-slate-200/80 rounded-2xl bg-white shadow-soft text-slate-500">
          <Award className="w-12 h-12 mx-auto mb-2 text-indigo-300" />
          <h3 className="text-sm font-bold text-slate-900">No Brand Passports Issued Yet</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            When campaigns are approved in the Approval Hub, a permanent cryptographic Brand Passport is automatically generated.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Passport Selector List (Hidden during print) (4 cols) */}
          <div className="no-print lg:col-span-4 border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden flex flex-col h-[680px]">
            <div className="p-3.5 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Issued Certificates</span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">{passports.length} Records</span>
            </div>

            <div className="p-3 flex-1 overflow-y-auto space-y-2">
              {passports.map((p) => {
                const isSelected = selectedPassport?.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedPassport(p)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all shadow-sm ${
                      isSelected
                        ? "bg-indigo-50/40 border-indigo-500 ring-2 ring-indigo-200"
                        : "bg-white border-slate-200/80 hover:border-indigo-300"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono font-bold text-slate-900">{p.passport_number}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {p.verification_status}
                      </span>
                    </div>
                    <div className="text-xs font-bold text-slate-800 truncate">{p.content_title}</div>
                    <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
                      <span>Score: <strong className="text-indigo-600">{p.final_score}/100</strong></span>
                      <span>{new Date(p.issued_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Official Printable Brand Passport Certificate View (8 cols) */}
          <div className="lg:col-span-8">
            {selectedPassport && (
              <div className="border border-slate-200/80 rounded-2xl bg-white p-8 space-y-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-indigo-500 via-emerald-400 to-indigo-600" />
                {/* Certificate Watermark / Header */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between border-b border-slate-100 pb-6 gap-4">
                  <div>
                    <div className="flex items-center space-x-2 text-xs font-semibold text-indigo-600 mb-1">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span>BRANDVAULT GOVERNANCE PASSPORT</span>
                    </div>
                    <h3 className="text-2xl font-bold tracking-tight text-slate-900">
                      CERTIFICATE OF BRAND COMPLIANCE
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Issued under BRANDVAULT Enterprise Protocol LP-41
                    </p>
                  </div>

                  <div className="text-left sm:text-right">
                    <div className="text-lg font-mono font-bold text-slate-900">{selectedPassport.passport_number}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      {new Date(selectedPassport.issued_at).toUTCString()}
                    </div>
                    <div className="inline-block mt-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
                      STATUS: {selectedPassport.verification_status.toUpperCase()}
                    </div>
                  </div>
                </div>

                {/* Metadata Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs">
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">ORGANIZATION</div>
                    <div className="font-bold text-slate-900 mt-0.5">{selectedPassport.brand_name}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">GUIDELINE VERSION</div>
                    <div className="font-bold text-slate-900 mt-0.5">{selectedPassport.guideline_version}</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">COMPLIANCE SCORE</div>
                    <div className="font-bold text-emerald-700 mt-0.5">{selectedPassport.final_score}/100</div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">AUDITOR RECORD</div>
                    <div className="font-bold text-slate-900 mt-0.5 truncate">{selectedPassport.audited_by}</div>
                  </div>
                </div>

                {/* Approved Marketing Copy */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1.5">
                    Certified Marketing Copy Payload
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs leading-relaxed font-sans text-slate-800">
                    "{selectedPassport.passport_data?.content || "Verified marketing copy"}"
                  </div>
                </div>

                {/* Cryptographic Hash */}
                <div className="p-3.5 rounded-xl bg-indigo-50/50 border border-indigo-100 text-[11px] space-y-1">
                  <div className="flex items-center space-x-1.5 text-indigo-900 font-bold">
                    <Lock className="w-3.5 h-3.5 text-indigo-600" />
                    <span>CRYPTOGRAPHIC CONTENT INTEGRITY FINGERPRINT (SHA-256)</span>
                  </div>
                  <div className="text-indigo-950 font-mono text-[11px] break-all select-all">
                    {selectedPassport.content_hash}
                  </div>
                </div>

                {/* Audit Signoff Footer */}
                <div className="pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 text-xs">
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">CERTIFIED REVIEWER</div>
                    <div className="font-bold text-slate-900 mt-0.5">{selectedPassport.audited_by}</div>
                    <div className="text-[11px] text-slate-500">CodeNexus India 2026 · Team Lead: Deepak Mouriya M</div>
                  </div>

                  <div className="text-left sm:text-right">
                    <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">VERIFICATION PROTOCOL</div>
                    <div className="font-bold text-indigo-600 mt-0.5">BRANDVAULT AGENTIC RAG v1.0</div>
                    <div className="text-[11px] text-slate-500">Immutable Ledger Record</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
