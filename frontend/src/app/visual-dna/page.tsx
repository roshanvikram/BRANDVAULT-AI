"use client";

import Link from "next/link";
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[11px] font-semibold border border-indigo-200">
              Multimodal Audit
            </span>
            <span className="text-[11px] text-slate-500">Pixel & Contrast Engine</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">Visual & Creative Asset Auditor</h2>
          <p className="text-[13px] text-slate-600 mt-1 max-w-2xl">
            Measured colour palette, luminance and contrast. PNG, JPEG, WebP and BMP supported. To check the text inside a creative, use Creative Inspection.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/visual-dna/creative" className="h-10 px-3.5 inline-flex items-center gap-1.5 rounded-xl text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-colors">Creative Inspection</Link>
          <Link href="/visual-dna/forensics" className="h-10 px-3.5 inline-flex items-center gap-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:border-indigo-300 hover:text-indigo-700 transition-colors">Asset Forensics</Link>
          <input type="file" ref={fileInputRef} onChange={handleImageUpload} accept="image/png,image/bmp,image/jpeg,image/webp" className="hidden" />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white transition-all flex items-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]"
          >
            <Upload className="w-4 h-4 text-indigo-200" />
            <span>Upload image</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Asset Preview */}
        <div className="lg:col-span-6 border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden flex flex-col h-[520px]">
          <div className="p-3.5 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Asset Canvas</span>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
              {result ? `${result.format.toUpperCase()} ${result.dimensions.width}x${result.dimensions.height}` : selectedImage ? "Image Loaded" : "Awaiting Upload"}
            </span>
          </div>
          <div className="flex-1 flex flex-col items-center justify-center p-6 bg-slate-50/40">
            {selectedImage ? (
              <img src={selectedImage} alt="Uploaded Brand Asset" className="max-h-full max-w-full object-contain rounded-xl border border-slate-200 shadow-sm" />
            ) : (
              <div onClick={() => fileInputRef.current?.click()} className="cursor-pointer border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl p-12 text-center w-full h-full flex flex-col items-center justify-center transition-all bg-white hover:bg-indigo-50/20 group">
                <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <ImageIcon className="w-7 h-7" />
                </div>
                <div className="text-sm font-bold text-slate-900">Upload a creative image (PNG, JPEG, WebP or BMP)</div>
                <div className="text-xs text-slate-500 mt-1 max-w-xs">Deterministic pixel analysis — JPEG/WebP/SVG not analysed here</div>
                <span className="mt-3 text-xs font-semibold text-indigo-600 group-hover:underline">Browse file</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Measured Findings */}
        <div className="lg:col-span-6 border border-slate-200/80 rounded-2xl bg-white shadow-soft overflow-hidden flex flex-col h-[520px]">
          <div className="p-3.5 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Measured Analysis</span>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
              {analyzing ? "Measuring..." : result ? "Analysis Complete" : "Ready"}
            </span>
          </div>

          <div className="p-5 flex-1 overflow-y-auto space-y-4">
            {error && (
              <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {m ? (
              <div className="space-y-4">
                {/* Measured metrics */}
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                    Measured Metrics ({m.pixels_sampled?.toLocaleString()} px sampled)
                  </div>
                  <div className="grid grid-cols-2 gap-2.5 text-xs">
                    <div className="p-3 rounded-xl bg-indigo-50/60 border border-indigo-100">
                      <div className="text-slate-600 text-[11px] font-medium">Monochrome</div>
                      <div className="text-indigo-900 text-lg font-bold mt-0.5">{Math.round((m.monochrome_fraction ?? 0) * 100)}%</div>
                    </div>
                    <div className="p-3 rounded-xl bg-purple-50/60 border border-purple-100">
                      <div className="text-slate-600 text-[11px] font-medium">Chromatic</div>
                      <div className="text-purple-900 text-lg font-bold mt-0.5">{Math.round((m.chromatic_fraction ?? 0) * 100)}%</div>
                    </div>
                    <div className="p-3 rounded-xl bg-sky-50/60 border border-sky-100">
                      <div className="text-slate-600 text-[11px] font-medium">Contrast Ratio</div>
                      <div className="text-sky-900 text-lg font-bold mt-0.5">{m.contrast}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100">
                      <div className="text-slate-600 text-[11px] font-medium">Avg Luminance</div>
                      <div className="text-emerald-900 text-lg font-bold mt-0.5">{m.avg_luminance}</div>
                    </div>
                  </div>
                </div>

                {/* Dominant palette */}
                {m.dominant_palette && (
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">Dominant Palette (measured)</div>
                    <div className="flex flex-wrap gap-2">
                      {m.dominant_palette.map((c, i) => (
                        <div key={i} className="flex items-center space-x-1.5 border border-slate-200 rounded-xl px-2.5 py-1.5 bg-white shadow-sm">
                          <span className="w-4 h-4 rounded-md border border-slate-300" style={{ backgroundColor: c.hex }} />
                          <span className="text-[11px] font-mono font-bold text-slate-800">{c.hex}</span>
                          <span className="text-[11px] text-slate-500">({Math.round(c.proportion * 100)}%)</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Findings */}
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">Findings ({findings.length})</div>
                  {findings.length === 0 ? (
                    <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center space-x-2.5">
                      <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span className="font-medium">No measurable visual violations (monochrome palette, adequate contrast).</span>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {findings.map((f) => (
                        <div key={f.id} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-800 font-semibold">{f.issue_category}</span>
                            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">{f.severity}</span>
                          </div>
                          <div className="text-xs font-bold text-slate-900">{f.original_text}</div>
                          <div className="text-[11px] text-slate-600 mt-1 leading-relaxed">{f.explanation}</div>
                          <div className="text-[10px] font-mono text-slate-400 mt-1.5">Source: {f.evidence_source}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* OCR status */}
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">OCR Text Extraction</div>
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-700">
                    {result?.ocr.available ? result?.ocr.text : `Unavailable — ${result?.ocr.reason || "no OCR engine configured"}`}
                  </div>
                </div>
              </div>
            ) : (
              !error && (
                <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
                  <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mb-3 text-slate-400">
                    <Eye className="w-6 h-6" />
                  </div>
                  <p className="text-xs max-w-xs text-slate-500">Upload a PNG or BMP asset to run deterministic color & contrast analysis.</p>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
