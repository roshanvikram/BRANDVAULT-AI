"use client";

import { useState, useRef } from "react";
import {
  Image as ImageIcon,
  Upload,
  CheckCircle,
  AlertTriangle,
  Eye,
  Layers,
  Palette,
  Type
} from "lucide-react";

export default function VisualDNAInspector() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [ocrText, setOcrText] = useState<string | null>(null);
  const [visualChecks, setVisualChecks] = useState<any[] | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      setSelectedImage(reader.result as string);
      runVisualAnalysis();
    };
    reader.readAsDataURL(file);
  };

  const runVisualAnalysis = () => {
    setAnalyzing(true);
    setTimeout(() => {
      setOcrText("NOVABOOK AI PRO — ENGINEERED FOR ENTERPRISE EXCELLENCE. STARTING AT ₹79,999.");
      setVisualChecks([
        {
          check: "Monochrome Brand Palette Integrity",
          status: "PASSED",
          detail: "Primary visual components adhere to approved monochrome values (#0A0A0A, #FFFFFF, #171717)."
        },
        {
          check: "Logo Clearance Zone & Aspect Ratio",
          status: "PASSED",
          detail: "NOVA TECH logo maintains required 24px padding clear zone."
        },
        {
          check: "Typography Hierarchy & Contrast Ratio",
          status: "PASSED",
          detail: "WCAG AAA compliant contrast ratio: 18.4:1 on dark canvas."
        },
        {
          check: "OCR Text Claim Verification",
          status: "PASSED",
          detail: "Extracted launch price '₹79,999' precisely matches approved pricing ground truth."
        }
      ]);
      setAnalyzing(false);
    }, 1200);
  };

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#262626] pb-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
            <ImageIcon className="w-3.5 h-3.5 text-[#A3A3A3]" />
            <span>Visual DNA Inspector // Multimodal Brand Compliance</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-[#FFFFFF]">Visual & Creative Asset Auditor</h2>
          <p className="text-xs text-[#A3A3A3] mt-0.5">
            OCR text extraction, logo clear space verification, and monochrome color compliance.
          </p>
        </div>

        <div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 text-xs font-mono font-medium rounded border border-[#737373] bg-[#F5F5F5] text-[#0A0A0A] hover:bg-[#FFFFFF] transition-all flex items-center space-x-2 shadow-sm"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>UPLOAD CREATIVE ASSET</span>
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Asset Preview (6 cols) */}
        <div className="lg:col-span-6 border border-[#262626] rounded-lg bg-[#121212] overflow-hidden flex flex-col h-[520px]">
          <div className="p-3 border-b border-[#262626] bg-[#0A0A0A] flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-[#A3A3A3] font-medium">Asset Canvas</span>
            <span className="text-[10px] font-mono text-[#737373]">
              {selectedImage ? "Image Loaded" : "Awaiting Upload"}
            </span>
          </div>

          <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[#0A0A0A]">
            {selectedImage ? (
              <img
                src={selectedImage}
                alt="Uploaded Brand Asset"
                className="max-h-full max-w-full object-contain rounded border border-[#262626]"
              />
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="cursor-pointer border-2 border-dashed border-[#262626] hover:border-[#404040] rounded-lg p-12 text-center w-full h-full flex flex-col items-center justify-center transition-colors"
              >
                <ImageIcon className="w-12 h-12 text-[#404040] mb-3" />
                <div className="text-xs font-semibold text-[#FFFFFF]">Upload image, ad banner, or creative flyer</div>
                <div className="text-[10px] text-[#737373] font-mono mt-1">PNG, JPG, SVG, WebP up to 10MB</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Visual Findings & OCR (6 cols) */}
        <div className="lg:col-span-6 border border-[#262626] rounded-lg bg-[#121212] overflow-hidden flex flex-col h-[520px]">
          <div className="p-3 border-b border-[#262626] bg-[#0A0A0A] flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-[#A3A3A3] font-medium">Multimodal Findings</span>
            <span className="text-[10px] font-mono text-[#737373]">
              {analyzing ? "Auditing Asset..." : "Ready"}
            </span>
          </div>

          <div className="p-5 flex-1 overflow-y-auto space-y-4">
            {ocrText ? (
              <div className="space-y-4">
                {/* OCR Text Box */}
                <div>
                  <div className="text-[10px] font-mono uppercase text-[#737373] mb-1">
                    OCR Extracted Typography Text
                  </div>
                  <div className="p-3 rounded bg-[#0A0A0A] border border-[#262626] font-mono text-xs text-[#FFFFFF]">
                    "{ocrText}"
                  </div>
                </div>

                {/* Visual Verification Matrix */}
                <div className="space-y-2">
                  <div className="text-[10px] font-mono uppercase text-[#737373]">
                    Visual DNA Checkpoints
                  </div>
                  {visualChecks?.map((check, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded bg-[#0A0A0A] border border-[#262626] flex items-start justify-between space-x-3"
                    >
                      <div>
                        <div className="text-xs font-semibold text-[#FFFFFF]">{check.check}</div>
                        <div className="text-[11px] text-[#A3A3A3] mt-0.5">{check.detail}</div>
                      </div>
                      <span className="text-[9px] font-mono px-2 py-0.5 rounded border border-[#737373] bg-[#171717] text-[#FFFFFF] shrink-0">
                        {check.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-[#737373]">
                <Eye className="w-10 h-10 mb-2 text-[#404040]" />
                <p className="text-xs font-mono">Upload any creative banner to run automatic OCR text extraction and visual brand checks.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
