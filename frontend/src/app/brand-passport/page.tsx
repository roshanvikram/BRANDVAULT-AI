"use client";

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
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E5E5] pb-5 select-none">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
            <Award className="w-3.5 h-3.5 text-[#0A0A0A]" />
            <span className="font-semibold">Brand Passport Repository // Cryptographic Audit Certificates</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A]">Official Brand Governance Passports</h2>
          <p className="text-xs text-[#737373] mt-0.5">
            Immutable, tamper-evident audit records verifying brand guideline compliance and human approval.
          </p>
        </div>

        {selectedPassport && (
          <button
            onClick={handlePrint}
            className="px-4 py-2.5 text-xs font-mono font-semibold rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#262626] transition-all flex items-center space-x-2 shadow-sm"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>EXPORT / PRINT CERTIFICATE</span>
          </button>
        )}
      </div>

      {passports.length === 0 ? (
        <div className="p-12 text-center border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm text-[#737373]">
          <Award className="w-10 h-10 mx-auto mb-2 text-[#A3A3A3]" />
          <h3 className="text-sm font-bold text-[#0A0A0A]">No Brand Passports Issued Yet</h3>
          <p className="text-xs font-mono mt-1">
            When campaigns are approved in the Approval Hub, a permanent cryptographic Brand Passport is automatically generated.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Passport Selector List (Hidden during print) (4 cols) */}
          <div className="no-print lg:col-span-4 border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden flex flex-col h-[680px]">
            <div className="p-3 border-b border-[#E5E5E5] bg-[#F5F5F5] flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-[#0A0A0A] font-bold">Issued Certificates</span>
              <span className="text-[10px] font-mono text-[#737373]">{passports.length} Records</span>
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
                        ? "bg-[#F5F5F5] border-[#0A0A0A]"
                        : "bg-[#FFFFFF] border-[#E5E5E5] hover:border-[#A3A3A3]"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono font-bold text-[#0A0A0A]">{p.passport_number}</span>
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded border border-[#E5E5E5] bg-[#FFFFFF] text-[#0A0A0A] font-bold">
                        {p.verification_status}
                      </span>
                    </div>
                    <div className="text-xs font-bold text-[#404040] truncate">{p.content_title}</div>
                    <div className="text-[10px] text-[#737373] font-mono mt-1">
                      Score: {p.final_score}/100 | {new Date(p.issued_at).toLocaleDateString()}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Official Printable Brand Passport Certificate View (8 cols) */}
          <div className="lg:col-span-8">
            {selectedPassport && (
              <div className="border border-[#0A0A0A] rounded-2xl bg-[#FFFFFF] p-8 space-y-6 shadow-xl relative overflow-hidden">
                {/* Certificate Watermark / Header */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between border-b border-[#E5E5E5] pb-6 gap-4">
                  <div>
                    <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] mb-1">
                      <ShieldCheck className="w-4 h-4 text-[#0A0A0A]" />
                      <span className="font-bold text-[#0A0A0A]">BRANDVAULT GOVERNANCE PASSPORT</span>
                    </div>
                    <h3 className="text-2xl font-bold tracking-tight text-[#0A0A0A]">
                      CERTIFICATE OF BRAND COMPLIANCE
                    </h3>
                    <p className="text-xs text-[#737373] font-mono mt-0.5">
                      Issued under BRANDVAULT Enterprise Protocol LP-41
                    </p>
                  </div>

                  <div className="text-left sm:text-right font-mono">
                    <div className="text-lg font-bold text-[#0A0A0A]">{selectedPassport.passport_number}</div>
                    <div className="text-[10px] text-[#737373]">
                      TIMESTAMP: {new Date(selectedPassport.issued_at).toUTCString()}
                    </div>
                    <div className="inline-block mt-2 px-3 py-1 rounded bg-[#0A0A0A] text-xs font-bold text-[#FFFFFF] shadow-sm">
                      STATUS: {selectedPassport.verification_status}
                    </div>
                  </div>
                </div>

                {/* Metadata Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-[#F5F5F5] border border-[#E5E5E5] text-xs font-mono">
                  <div>
                    <div className="text-[10px] text-[#737373] font-bold">ORGANIZATION</div>
                    <div className="font-bold text-[#0A0A0A] mt-0.5">{selectedPassport.brand_name}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-[#737373] font-bold">GUIDELINE VERSION</div>
                    <div className="font-bold text-[#0A0A0A] mt-0.5">{selectedPassport.guideline_version}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-[#737373] font-bold">COMPLIANCE SCORE</div>
                    <div className="font-bold text-[#0A0A0A] mt-0.5">{selectedPassport.final_score}/100</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-[#737373] font-bold">AUDITOR RECORD</div>
                    <div className="font-bold text-[#0A0A0A] mt-0.5 truncate">{selectedPassport.audited_by}</div>
                  </div>
                </div>

                {/* Approved Marketing Copy */}
                <div>
                  <div className="text-[10px] font-mono uppercase text-[#737373] font-bold mb-1">
                    Certified Marketing Copy Payload
                  </div>
                  <div className="p-4 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5] text-xs leading-relaxed font-sans text-[#0A0A0A]">
                    "{selectedPassport.passport_data?.content || "Verified marketing copy"}"
                  </div>
                </div>

                {/* Cryptographic Hash */}
                <div className="p-3.5 rounded-xl bg-[#F5F5F5] border border-[#E5E5E5] font-mono text-[11px] space-y-1">
                  <div className="flex items-center space-x-1.5 text-[#0A0A0A] font-bold">
                    <Lock className="w-3.5 h-3.5" />
                    <span>CRYPTOGRAPHIC CONTENT INTEGRITY FINGERPRINT (SHA-256)</span>
                  </div>
                  <div className="text-[#404040] break-all select-all font-mono text-[10px]">
                    {selectedPassport.content_hash}
                  </div>
                </div>

                {/* Audit Signoff Footer */}
                <div className="pt-6 border-t border-[#E5E5E5] flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4 text-xs font-mono">
                  <div>
                    <div className="text-[10px] text-[#737373]">CERTIFIED REVIEWER</div>
                    <div className="font-bold text-[#0A0A0A] mt-0.5">{selectedPassport.audited_by}</div>
                    <div className="text-[10px] text-[#737373]">CodeNexus India 2026 // Team Lead: Deepak Mouriya M</div>
                  </div>

                  <div className="text-left sm:text-right">
                    <div className="text-[10px] text-[#737373]">VERIFICATION PROTOCOL</div>
                    <div className="font-bold text-[#0A0A0A] mt-0.5">BRANDVAULT AGENTIC RAG v1.0</div>
                    <div className="text-[10px] text-[#737373]">Immutable Ledger Record</div>
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
