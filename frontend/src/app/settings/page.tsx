"use client";

import { useEffect, useState } from "react";
import {
  Sliders,
  Server,
  Database,
  Users,
  Shield,
  Layers,
  Key,
  Info
} from "lucide-react";
import { fetchHealth, HealthInfo } from "@/lib/api";

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthInfo | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(console.error);
  }, []);

  return (
    <div className="space-y-6 select-none max-w-4xl">
      {/* Header */}
      <div className="border-b border-slate-200/80 pb-5">
        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[11px] font-semibold border border-slate-200">
            Settings & System
          </span>
          <span className="text-[11px] text-slate-500">Global Configuration</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">Enterprise Governance Configuration</h2>
        <p className="text-[13px] text-slate-600 mt-0.5 max-w-2xl">
          Active system parameters, backend health telemetry, database persistence, and team credentials.
        </p>
      </div>

      {/* Product & Team Credentials */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-soft space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <Users className="w-4 h-4 text-indigo-600" />
          <h3 className="text-xs font-bold text-slate-900">Team Credentials & Product Identity</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">PRODUCT NAME</span>
            <div className="text-slate-900 font-bold mt-0.5">BRANDVAULT AI</div>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">OFFICIAL TAGLINE</span>
            <div className="text-slate-800 mt-0.5 font-medium">Protect Every Word. Preserve Every Identity.</div>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">TEAM LEADER</span>
            <div className="text-slate-900 font-bold mt-0.5">Deepak Mouriya M</div>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">TEAM MEMBERS</span>
            <div className="text-slate-700 mt-0.5 font-medium">
              Deepak Mouriya M, Roshan Vikram AV, Preethish, Aishwarya R M
            </div>
          </div>
        </div>
      </div>

      {/* Backend & Database Telemetry */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-soft space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <Server className="w-4 h-4 text-emerald-600" />
          <h3 className="text-xs font-bold text-slate-900">Runtime Telemetry & Persistence Layer</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-100">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">SERVICE STATUS</span>
            <div className="text-emerald-700 font-bold mt-1 text-sm flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>{health?.status.toUpperCase() || "ONLINE"}</span>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-100">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">DATABASE LAYER</span>
            <div className="text-indigo-700 font-bold mt-1 text-sm">{health?.database.toUpperCase() || "CONNECTED"}</div>
          </div>
          <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100">
            <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">ACTIVE VERSION</span>
            <div className="text-purple-700 font-bold mt-1 text-sm">v{health?.version || "1.0.0"}</div>
          </div>
        </div>
      </div>

      {/* Round 3 Roadmap Preview */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-soft space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <Layers className="w-4 h-4 text-indigo-600" />
          <h3 className="text-xs font-bold text-slate-900">Round 3 Architectural Roadmap</h3>
        </div>

        <div className="space-y-3 text-xs">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="font-bold text-slate-900 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-indigo-500" />
              <span>1. Brand Drift Intelligence</span>
            </div>
            <p className="text-slate-600 mt-1 leading-relaxed">
              Longitudinal tracking and time-series clustering to detect gradual erosion of brand tone across multi-quarter campaigns.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="font-bold text-slate-900 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-500" />
              <span>2. Advanced Multimodal Governance</span>
            </div>
            <p className="text-slate-600 mt-1 leading-relaxed">
              Direct video frame-by-frame analysis, audio brand voice cadence checking, and automated 3D product asset inspection.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="font-bold text-slate-900 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-sky-500" />
              <span>3. Enterprise MCP Integration Hub</span>
            </div>
            <p className="text-slate-600 mt-1 leading-relaxed">
              Controlled Model Context Protocol server exposing verified brand tools to enterprise agent frameworks and creative IDEs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
