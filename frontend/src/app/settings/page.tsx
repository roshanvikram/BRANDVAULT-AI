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
      <div className="border-b border-[#E5E5E5] pb-5">
        <h2 className="text-2xl font-semibold tracking-tight text-[#0A0A0A]">Enterprise Governance Configuration</h2>
        <p className="text-[13px] text-[#71717A] mt-1 max-w-2xl">
          Active system parameters, backend health telemetry, database persistence, and team credentials.
        </p>
      </div>

      {/* Product & Team Credentials */}
      <div className="p-6 rounded-xl border border-[#E5E5E5] bg-[#FFFFFF] shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-[#E5E5E5] pb-3">
          <Users className="w-4 h-4 text-[#0A0A0A]" />
          <h3 className="text-xs font-bold text-[#0A0A0A]">Team Credentials & Product Identity</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div>
            <span className="text-[#737373] font-semibold">PRODUCT NAME:</span>
            <div className="text-[#0A0A0A] font-bold mt-0.5">BRANDVAULT AI</div>
          </div>
          <div>
            <span className="text-[#737373] font-semibold">OFFICIAL TAGLINE:</span>
            <div className="text-[#0A0A0A] mt-0.5 font-medium">Protect Every Word. Preserve Every Identity.</div>
          </div>
          <div>
            <span className="text-[#737373] font-semibold">TEAM LEADER:</span>
            <div className="text-[#0A0A0A] font-bold mt-0.5">Deepak Mouriya M</div>
          </div>
          <div>
            <span className="text-[#737373] font-semibold">TEAM MEMBERS:</span>
            <div className="text-[#404040] mt-0.5 font-medium">
              Deepak Mouriya M, Roshan Vikram AV, Preethish, Aishwarya R M
            </div>
          </div>
        </div>
      </div>

      {/* Backend & Database Telemetry */}
      <div className="p-6 rounded-xl border border-[#E5E5E5] bg-[#FFFFFF] shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-[#E5E5E5] pb-3">
          <Server className="w-4 h-4 text-[#0A0A0A]" />
          <h3 className="text-xs font-bold text-[#0A0A0A]">Runtime Telemetry & Persistence Layer</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
            <span className="text-[#737373] font-semibold">SERVICE STATUS</span>
            <div className="text-[#0A0A0A] font-bold mt-1">{health?.status.toUpperCase() || "ONLINE"}</div>
          </div>
          <div className="p-3.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
            <span className="text-[#737373] font-semibold">DATABASE LAYER</span>
            <div className="text-[#0A0A0A] font-bold mt-1">{health?.database.toUpperCase() || "CONNECTED"}</div>
          </div>
          <div className="p-3.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
            <span className="text-[#737373] font-semibold">ACTIVE VERSION</span>
            <div className="text-[#0A0A0A] font-bold mt-1">v{health?.version || "1.0.0"}</div>
          </div>
        </div>
      </div>

      {/* Round 3 Roadmap Preview */}
      <div className="p-6 rounded-xl border border-[#E5E5E5] bg-[#FFFFFF] shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-[#E5E5E5] pb-3">
          <Layers className="w-4 h-4 text-[#0A0A0A]" />
          <h3 className="text-xs font-bold text-[#0A0A0A]">Round 3 Architectural Roadmap</h3>
        </div>

        <div className="space-y-3 text-xs">
          <div className="p-3.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
            <div className="font-bold text-[#0A0A0A] font-mono">1. Brand Drift Intelligence</div>
            <p className="text-[#404040] mt-0.5 leading-relaxed">
              Longitudinal tracking and time-series clustering to detect gradual erosion of brand tone across multi-quarter campaigns.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
            <div className="font-bold text-[#0A0A0A] font-mono">2. Advanced Multimodal Governance</div>
            <p className="text-[#404040] mt-0.5 leading-relaxed">
              Direct video frame-by-frame analysis, audio brand voice cadence checking, and automated 3D product asset inspection.
            </p>
          </div>
          <div className="p-3.5 rounded-lg bg-[#FAFAFA] border border-[#E5E5E5]">
            <div className="font-bold text-[#0A0A0A] font-mono">3. Enterprise MCP Integration Hub</div>
            <p className="text-[#404040] mt-0.5 leading-relaxed">
              Controlled Model Context Protocol server exposing verified brand tools to enterprise agent frameworks and creative IDEs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
