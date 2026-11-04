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
      <div className="border-b border-[#262626] pb-5">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#737373] uppercase mb-1">
          <Sliders className="w-3.5 h-3.5 text-[#A3A3A3]" />
          <span>System Settings & Architecture // CodeNexus India 2026</span>
        </div>
        <h2 className="text-xl font-bold tracking-tight text-[#FFFFFF]">Enterprise Governance Configuration</h2>
        <p className="text-xs text-[#A3A3A3] mt-0.5">
          Active system parameters, backend health telemetry, database persistence, and team credentials.
        </p>
      </div>

      {/* Product & Team Credentials */}
      <div className="p-5 rounded-lg border border-[#262626] bg-[#121212] space-y-4">
        <div className="flex items-center space-x-2 border-b border-[#262626] pb-3">
          <Users className="w-4 h-4 text-[#A3A3A3]" />
          <h3 className="text-xs font-semibold text-[#FFFFFF]">Team Credentials & Product Identity</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div>
            <span className="text-[#737373]">PRODUCT NAME:</span>
            <div className="text-[#FFFFFF] font-bold mt-0.5">BRANDVAULT AI</div>
          </div>
          <div>
            <span className="text-[#737373]">OFFICIAL TAGLINE:</span>
            <div className="text-[#FFFFFF] mt-0.5">Protect Every Word. Preserve Every Identity.</div>
          </div>
          <div>
            <span className="text-[#737373]">TEAM LEADER:</span>
            <div className="text-[#FFFFFF] font-bold mt-0.5">Deepak Mouriya M</div>
          </div>
          <div>
            <span className="text-[#737373]">TEAM MEMBERS:</span>
            <div className="text-[#A3A3A3] mt-0.5">
              Deepak Mouriya M, Roshan Vikram AV, Preethish, Aishwarya R M
            </div>
          </div>
        </div>
      </div>

      {/* Backend & Database Telemetry */}
      <div className="p-5 rounded-lg border border-[#262626] bg-[#121212] space-y-4">
        <div className="flex items-center space-x-2 border-b border-[#262626] pb-3">
          <Server className="w-4 h-4 text-[#A3A3A3]" />
          <h3 className="text-xs font-semibold text-[#FFFFFF]">Runtime Telemetry & Persistence Layer</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3 rounded bg-[#0A0A0A] border border-[#262626]">
            <span className="text-[#737373]">SERVICE STATUS</span>
            <div className="text-[#FFFFFF] font-bold mt-1">{health?.status.toUpperCase() || "ONLINE"}</div>
          </div>
          <div className="p-3 rounded bg-[#0A0A0A] border border-[#262626]">
            <span className="text-[#737373]">DATABASE LAYER</span>
            <div className="text-[#FFFFFF] font-bold mt-1">{health?.database.toUpperCase() || "CONNECTED"}</div>
          </div>
          <div className="p-3 rounded bg-[#0A0A0A] border border-[#262626]">
            <span className="text-[#737373]">ACTIVE VERSION</span>
            <div className="text-[#FFFFFF] font-bold mt-1">v{health?.version || "1.0.0"}</div>
          </div>
        </div>
      </div>

      {/* Round 3 Roadmap Preview */}
      <div className="p-5 rounded-lg border border-[#262626] bg-[#121212] space-y-4">
        <div className="flex items-center space-x-2 border-b border-[#262626] pb-3">
          <Layers className="w-4 h-4 text-[#A3A3A3]" />
          <h3 className="text-xs font-semibold text-[#FFFFFF]">Round 3 Architectural Roadmap</h3>
        </div>

        <div className="space-y-3 text-xs">
          <div className="p-3 rounded bg-[#0A0A0A] border border-[#262626]">
            <div className="font-semibold text-[#FFFFFF] font-mono">1. Brand Drift Intelligence</div>
            <p className="text-[#A3A3A3] mt-0.5">
              Longitudinal tracking and time-series clustering to detect gradual erosion of brand tone across multi-quarter campaigns.
            </p>
          </div>
          <div className="p-3 rounded bg-[#0A0A0A] border border-[#262626]">
            <div className="font-semibold text-[#FFFFFF] font-mono">2. Advanced Multimodal Governance</div>
            <p className="text-[#A3A3A3] mt-0.5">
              Direct video frame-by-frame analysis, audio brand voice cadence checking, and automated 3D product asset inspection.
            </p>
          </div>
          <div className="p-3 rounded bg-[#0A0A0A] border border-[#262626]">
            <div className="font-semibold text-[#FFFFFF] font-mono">3. Enterprise MCP Integration Hub</div>
            <p className="text-[#A3A3A3] mt-0.5">
              Controlled Model Context Protocol server exposing verified brand tools to enterprise agent frameworks and creative IDEs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
