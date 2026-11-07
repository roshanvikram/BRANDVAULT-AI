"use client";

import { useState, useRef } from "react";
import {
  Image as ImageIcon,
  Upload,
  Eye,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import { analyzeImage, VisualAnalysis } from "@/lib/api";

export default function VisualDNAInspector() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<VisualAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => setSelectedImage(reader.result as string);
    reader.readAsDataURL(file);

    setAnalyzing(true);
    setError(null);
    setResult(null);
    try {
      const res = await analyzeImage(undefined, file);
      setResult(res);
    } catch (err: any) {
      setError(err?.message || "Visual analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  };

  const m = result?.metrics;
  const findings = result?.submission.findings || [];

  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E5E5] pb-5">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-[#0A0A0A]">Visual & Creative Asset Auditor</h2>
          <p className="text-[13px] text-[#71717A] mt-1 max-w-2xl">
            Measured colour-palette & contrast analysis against the monochrome brand palette. PNG / BMP supported.
          </p>
        </div>

        <div>
          <input type="file" ref={fileInputRef} onChange={handleImageUpload} accept="image/png,image/bmp" className="hidden" />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2.5 text-xs font-medium rounded-lg bg-[#0A0A0A] text-[#FFFFFF] hover:bg-[#27272A] transition-all flex items-center space-x-2 shadow-sm"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload PNG or BMP</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Asset Preview */}
        <div className="lg:col-span-6 border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden flex flex-col h-[520px]">
          <div className="p-3 border-b border-[#E5E5E5] bg-[#F5F5F5] flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-[#0A0A0A] font-bold">Asset Canvas</span>
            <span className="text-[11px] font-mono text-[#737373]">
              {result ? `${result.format.toUpperCase()} ${result.dimensions.width}x${result.dimensions.height}` : selectedImage ? "Image Loaded" : "Awaiting Upload"}
            </span>
          </div>
          <div className="flex-1 flex flex-col items-center justify-center p-6 bg-[#FAFAFA]">
            {selectedImage ? (
              <img src={selectedImage} alt="Uploaded Brand Asset" className="max-h-full max-w-full object-contain rounded-lg border border-[#E5E5E5] shadow-sm" />
            ) : (
              <div onClick={() => fileInputRef.current?.click()} className="cursor-pointer border-2 border-dashed border-[#D4D4D4] hover:border-[#0A0A0A] rounded-xl p-12 text-center w-full h-full flex flex-col items-center justify-center transition-colors bg-[#FFFFFF]">
                <ImageIcon className="w-12 h-12 text-[#A3A3A3] mb-3" />
                <div className="text-xs font-bold text-[#0A0A0A]">Upload a PNG or BMP creative asset</div>
                <div className="text-[11px] text-[#737373] font-mono mt-1">Deterministic pixel analysis — JPEG/WebP/SVG not analysed here</div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Measured Findings */}
        <div className="lg:col-span-6 border border-[#E5E5E5] rounded-xl bg-[#FFFFFF] shadow-sm overflow-hidden flex flex-col h-[520px]">
          <div className="p-3 border-b border-[#E5E5E5] bg-[#F5F5F5] flex items-center justify-between">
            <span className="text-xs font-mono uppercase text-[#0A0A0A] font-bold">Measured Analysis</span>
            <span className="text-[11px] font-mono text-[#737373]">{analyzing ? "Measuring..." : result ? "Done" : "Ready"}</span>
          </div>

          <div className="p-5 flex-1 overflow-y-auto space-y-4">
            {error && (
              <div className="p-3 rounded-lg border border-[#E5E5E5] bg-[#F5F5F5] text-xs font-mono text-[#0A0A0A] flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {m ? (
              <div className="space-y-4">
                {/* Measured metrics */}
                <div>
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-bold mb-1.5">Measured Metrics ({m.pixels_sampled} px sampled)</div>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="p-2.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
                      <div className="text-[#737373] text-[11px]">Monochrome</div>
                      <div className="text-[#0A0A0A] font-bold">{Math.round((m.monochrome_fraction ?? 0) * 100)}%</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
                      <div className="text-[#737373] text-[11px]">Chromatic</div>
                      <div className="text-[#0A0A0A] font-bold">{Math.round((m.chromatic_fraction ?? 0) * 100)}%</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
                      <div className="text-[#737373] text-[11px]">Contrast</div>
                      <div className="text-[#0A0A0A] font-bold">{m.contrast}</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
                      <div className="text-[#737373] text-[11px]">Avg Luminance</div>
                      <div className="text-[#0A0A0A] font-bold">{m.avg_luminance}</div>
                    </div>
                  </div>
                </div>

                {/* Dominant palette */}
                {m.dominant_palette && (
                  <div>
                    <div className="text-[11px] font-mono uppercase text-[#737373] font-bold mb-1.5">Dominant Palette (measured)</div>
                    <div className="flex flex-wrap gap-2">
                      {m.dominant_palette.map((c, i) => (
                        <div key={i} className="flex items-center space-x-1.5 border border-[#E5E5E5] rounded-lg px-2 py-1 bg-[#FFFFFF]">
                          <span className="w-4 h-4 rounded border border-[#E5E5E5]" style={{ backgroundColor: c.hex }} />
                          <span className="text-[11px] font-mono text-[#0A0A0A]">{c.hex}</span>
                          <span className="text-[11px] font-mono text-[#737373]">{Math.round(c.proportion * 100)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Findings */}
                <div>
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-bold mb-1.5">Findings ({findings.length})</div>
                  {findings.length === 0 ? (
                    <div className="p-3 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5] text-xs text-[#404040] flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-[#737373]" />
                      <span>No measurable visual violations (monochrome palette, adequate contrast).</span>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {findings.map((f) => (
                        <div key={f.id} className="p-3 rounded-xl bg-[#FAFAFA] border border-[#E5E5E5]">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-[11px] font-mono px-1.5 py-0.5 rounded border border-[#E5E5E5] bg-[#FFFFFF] text-[#0A0A0A] font-semibold">{f.issue_category}</span>
                            <span className="text-[11px] font-mono text-[#737373] border border-[#E5E5E5] px-1 py-0.5 rounded">{f.severity}</span>
                          </div>
                          <div className="text-xs font-bold text-[#0A0A0A]">{f.original_text}</div>
                          <div className="text-[11px] text-[#404040] mt-0.5 leading-relaxed">{f.explanation}</div>
                          <div className="text-[11px] font-mono text-[#737373] mt-1">Source: {f.evidence_source}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* OCR status — honest */}
                <div>
                  <div className="text-[11px] font-mono uppercase text-[#737373] font-bold mb-1">OCR Text Extraction</div>
                  <div className="p-3 rounded-lg bg-[#F5F5F5] border border-[#E5E5E5] text-[11px] font-mono text-[#404040]">
                    {result?.ocr.available ? result?.ocr.text : `Unavailable — ${result?.ocr.reason || "no OCR engine configured"}`}
                  </div>
                </div>
              </div>
            ) : (
              !error && (
                <div className="h-full flex flex-col items-center justify-center text-center p-8 text-[#737373]">
                  <Eye className="w-10 h-10 mb-2 text-[#A3A3A3]" />
                  <p className="text-xs font-mono">Upload a PNG or BMP asset to run deterministic colour & contrast analysis.</p>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
