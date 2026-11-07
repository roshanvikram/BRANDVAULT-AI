"use client";

import { useCallback, useEffect, useRef, useState, ReactNode } from "react";
import { Play, Pause, SkipBack, SkipForward, RotateCcw, Volume2, VolumeX } from "lucide-react";

export type WalkStep = { n: number; title: string; summary: string; ill: ReactNode; shot?: string };

/**
 * An in-page "video" walkthrough: it auto-advances through the guide steps,
 * showing each illustration while (optionally) narrating the step with the
 * browser's built-in speech synthesis. It is an honest animated tour built from
 * the real guide content — not a recorded screen capture, and labelled as such.
 *
 * When voice narration is on, each step advances when its narration finishes
 * (with a safety timeout); otherwise a fixed per-step timer drives it. A real
 * recorded video can be shown instead via NEXT_PUBLIC_GUIDE_VIDEO_URL (handled
 * by the guide page).
 */
const STEP_MS = 8000;

function pickVoice(): SpeechSynthesisVoice | null {
  const voices = window.speechSynthesis.getVoices();
  return (
    voices.find((v) => /^en[-_]?(US|GB|IN)/i.test(v.lang)) ||
    voices.find((v) => v.lang?.toLowerCase().startsWith("en")) ||
    null
  );
}

export function WalkthroughPlayer({ steps }: { steps: WalkStep[] }) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [narrate, setNarrate] = useState(true);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [progress, setProgress] = useState(0);
  const [done, setDone] = useState(false);

  const timer = useRef<number | null>(null);
  const raf = useRef<number | null>(null);
  const playingRef = useRef(playing);
  playingRef.current = playing;

  useEffect(() => {
    setVoiceSupported(typeof window !== "undefined" && "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined");
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
    };
  }, []);

  const clearTimers = useCallback(() => {
    if (timer.current) { window.clearTimeout(timer.current); timer.current = null; }
    if (raf.current) { cancelAnimationFrame(raf.current); raf.current = null; }
    if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
  }, []);

  const advance = useCallback(() => {
    setIndex((i) => {
      if (i < steps.length - 1) return i + 1;
      setPlaying(false);
      setDone(true);
      return i;
    });
  }, [steps.length]);

  // Drive the current step while playing.
  useEffect(() => {
    clearTimers();
    setProgress(0);
    if (!playing) return;

    const step = steps[index];
    const text = `Step ${step.n}. ${step.title}. ${step.summary}`;
    const useVoice = narrate && voiceSupported;

    let durationMs = STEP_MS;
    if (useVoice) {
      const words = text.split(/\s+/).length;
      durationMs = Math.max(5000, Math.min(22000, (words / 2.6) * 1000));
      const u = new SpeechSynthesisUtterance(text);
      const v = pickVoice();
      if (v) u.voice = v;
      u.onend = () => { if (playingRef.current) advance(); };
      u.onerror = () => { if (playingRef.current) { timer.current = window.setTimeout(advance, 1500); } };
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
      // Safety net in case onend never fires.
      timer.current = window.setTimeout(() => { if (playingRef.current) advance(); }, durationMs * 2);
    } else {
      timer.current = window.setTimeout(() => { if (playingRef.current) advance(); }, durationMs);
    }

    const start = performance.now();
    const tick = (t: number) => {
      const p = Math.min(100, ((t - start) / durationMs) * 100);
      setProgress(p);
      if (p < 100 && playingRef.current) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);

    return clearTimers;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, playing, narrate, voiceSupported]);

  const togglePlay = () => {
    if (done) { setDone(false); setIndex(0); setPlaying(true); return; }
    setPlaying((p) => !p);
  };
  const goTo = (i: number) => { setDone(false); setIndex(Math.max(0, Math.min(steps.length - 1, i))); };
  const prev = () => goTo(index - 1);
  const next = () => { if (index < steps.length - 1) goTo(index + 1); };

  const step = steps[index];
  const hasShots = steps.some((s) => s.shot);

  return (
    <div className="w-full">
      {/* Player frame */}
      <div className="rounded-xl border border-[#E5E5E5] bg-[#0A0A0A] shadow-sm overflow-hidden">
        {/* Screen */}
        <div className="relative bg-[#FAFAFA] aspect-video flex items-center justify-center overflow-hidden">
          {step.shot ? (
            <div key={index} className="absolute inset-0 animate-[fadeIn_.35s_ease]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={step.shot} alt={`${step.title} — screenshot`} className="w-full h-full object-cover" />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 via-black/35 to-transparent p-4 pt-12">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-lg bg-white text-[#0A0A0A] flex items-center justify-center font-mono font-bold text-[11px] shrink-0">{step.n}</span>
                  <h3 className="text-sm sm:text-base font-bold tracking-tight text-white">{step.title}</h3>
                </div>
              </div>
            </div>
          ) : (
            <div key={index} className="w-full h-full p-6 sm:p-10 flex flex-col items-center justify-center text-center animate-[fadeIn_.35s_ease]">
              <div className="w-full max-w-[280px] aspect-[200/140] mb-4">{step.ill}</div>
              <div className="flex items-center justify-center space-x-2">
                <span className="w-6 h-6 rounded-lg bg-[#0A0A0A] text-white flex items-center justify-center font-mono font-bold text-[11px]">{step.n}</span>
                <h3 className="text-sm sm:text-base font-bold tracking-tight text-[#0A0A0A]">{step.title}</h3>
              </div>
              <p className="text-[11px] sm:text-xs text-[#737373] mt-2 max-w-md leading-relaxed">{step.summary}</p>
            </div>
          )}

          {/* Overlay play button when paused/idle */}
          {!playing && (
            <button
              onClick={togglePlay}
              className="absolute inset-0 flex items-center justify-center bg-black/5 hover:bg-black/10 transition-colors group"
              aria-label={done ? "Replay walkthrough" : "Play walkthrough"}
            >
              <span className="w-14 h-14 rounded-full bg-[#0A0A0A] text-white flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform">
                {done ? <RotateCcw className="w-6 h-6" /> : <Play className="w-6 h-6 ml-0.5" />}
              </span>
            </button>
          )}
        </div>

        {/* Progress bar */}
        <div className="h-1 w-full bg-[#262626]">
          <div className="h-full bg-white transition-[width] duration-100 ease-linear" style={{ width: `${progress}%` }} />
        </div>

        {/* Controls */}
        <div className="px-4 py-3 flex items-center justify-between text-white">
          <div className="flex items-center space-x-1">
            <button onClick={prev} disabled={index === 0} title="Previous step" className="p-2 rounded-lg hover:bg-[#262626] disabled:opacity-30 disabled:hover:bg-transparent transition-colors">
              <SkipBack className="w-4 h-4" />
            </button>
            <button onClick={togglePlay} title={playing ? "Pause" : "Play"} className="p-2 rounded-lg hover:bg-[#262626] transition-colors">
              {playing ? <Pause className="w-5 h-5" /> : done ? <RotateCcw className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            <button onClick={next} disabled={index === steps.length - 1} title="Next step" className="p-2 rounded-lg hover:bg-[#262626] disabled:opacity-30 disabled:hover:bg-transparent transition-colors">
              <SkipForward className="w-4 h-4" />
            </button>
          </div>

          <div className="text-[11px] font-mono text-[#A3A3A3]">
            Step {index + 1} / {steps.length}
          </div>

          <button
            onClick={() => setNarrate((v) => !v)}
            disabled={!voiceSupported}
            title={!voiceSupported ? "Voice not supported in this browser" : narrate ? "Mute narration" : "Unmute narration"}
            className="p-2 rounded-lg hover:bg-[#262626] disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
          >
            {narrate && voiceSupported ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>
        </div>

        {/* Step dots */}
        <div className="px-4 pb-3 flex items-center justify-center gap-1.5">
          {steps.map((s, i) => (
            <button
              key={s.n}
              onClick={() => goTo(i)}
              title={`Step ${s.n}`}
              className={`h-1.5 rounded-full transition-all ${i === index ? "w-5 bg-white" : "w-1.5 bg-[#404040] hover:bg-[#737373]"}`}
            />
          ))}
        </div>
      </div>

      <p className="text-[11px] font-mono text-[#A3A3A3] mt-2 text-center">
        {hasShots ? "Real screens captured from the running app" : "Animated walkthrough"}{voiceSupported ? " · narrated with your browser's built-in voice" : ""}.
      </p>

      <style jsx>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}
