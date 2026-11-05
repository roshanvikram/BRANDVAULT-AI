"use client";

import { useEffect, useRef, useState } from "react";
import { Volume2, Pause, Play, Square } from "lucide-react";

/**
 * "Read aloud" control backed by the browser's built-in Web Speech API
 * (window.speechSynthesis). This is a real, on-device text-to-speech voice — no
 * external service or API key — so it is labelled honestly as the browser's own
 * voice, not a proprietary cloud AI. If the browser has no speech synthesis the
 * control renders disabled with a note.
 *
 * Long text is spoken sentence-by-sentence to avoid the ~15s utterance cut-off
 * some Chromium builds impose on a single long utterance.
 */
export function ReadAloud({
  text,
  label = "Read aloud",
  compact = false,
}: {
  text: string;
  label?: string;
  compact?: boolean;
}) {
  const [supported, setSupported] = useState(true);
  const [state, setState] = useState<"idle" | "playing" | "paused">("idle");
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    const ok = typeof window !== "undefined" && "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";
    setSupported(ok);
    // Trigger voice list population in browsers that load it lazily.
    if (ok) window.speechSynthesis.getVoices();
    return () => {
      mounted.current = false;
      if (ok) window.speechSynthesis.cancel();
    };
  }, []);

  const pickVoice = (): SpeechSynthesisVoice | null => {
    const voices = window.speechSynthesis.getVoices();
    return (
      voices.find((v) => /^en[-_]?(US|GB|IN)/i.test(v.lang)) ||
      voices.find((v) => v.lang?.toLowerCase().startsWith("en")) ||
      null
    );
  };

  const start = () => {
    const synth = window.speechSynthesis;
    synth.cancel();
    const voice = pickVoice();
    const chunks = text
      .replace(/\s+/g, " ")
      .match(/[^.!?]+[.!?]*/g) || [text];

    chunks.forEach((chunk, i) => {
      const u = new SpeechSynthesisUtterance(chunk.trim());
      u.rate = 1;
      u.pitch = 1;
      if (voice) u.voice = voice;
      if (i === chunks.length - 1) {
        u.onend = () => { if (mounted.current) setState("idle"); };
      }
      u.onerror = () => { if (mounted.current) setState("idle"); };
      synth.speak(u);
    });
    setState("playing");
  };

  const toggle = () => {
    if (!supported) return;
    const synth = window.speechSynthesis;
    if (state === "idle") start();
    else if (state === "playing") { synth.pause(); setState("paused"); }
    else { synth.resume(); setState("playing"); }
  };

  const stop = () => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setState("idle");
  };

  if (compact) {
    return (
      <button
        type="button"
        onClick={toggle}
        disabled={!supported}
        title={supported ? "Listen to this step" : "Voice not supported in this browser"}
        className="w-8 h-8 rounded-lg border border-[#E5E5E5] bg-white text-[#0A0A0A] flex items-center justify-center hover:bg-[#F5F5F5] disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
      >
        {state === "playing" ? <Pause className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
      </button>
    );
  }

  return (
    <div className="inline-flex flex-col items-start gap-1">
      <div className="inline-flex items-center gap-2">
        <button
          type="button"
          onClick={toggle}
          disabled={!supported}
          className="px-4 py-2.5 text-xs font-mono font-bold rounded-xl bg-[#0A0A0A] text-white hover:bg-[#262626] disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center space-x-2 shadow-sm"
        >
          {state === "playing" ? <Pause className="w-3.5 h-3.5" /> : state === "paused" ? <Play className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          <span>{state === "idle" ? label : state === "playing" ? "Pause" : "Resume"}</span>
        </button>
        {state !== "idle" && (
          <button
            type="button"
            onClick={stop}
            title="Stop"
            className="px-3 py-2.5 text-xs font-mono font-bold rounded-xl bg-white border border-[#E5E5E5] text-[#0A0A0A] hover:bg-[#F5F5F5] transition-all flex items-center space-x-1.5"
          >
            <Square className="w-3 h-3" />
            <span>Stop</span>
          </button>
        )}
      </div>
      {!supported && (
        <span className="text-[10px] font-mono text-[#A3A3A3]">Voice is not available in this browser.</span>
      )}
      {supported && (
        <span className="text-[10px] font-mono text-[#A3A3A3]">Uses your browser&apos;s built-in voice.</span>
      )}
    </div>
  );
}
