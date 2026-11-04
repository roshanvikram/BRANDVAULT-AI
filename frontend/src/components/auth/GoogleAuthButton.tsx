"use client";

import { useEffect, useState } from "react";
import { fetchGoogleAuthStatus, googleLoginUrl } from "@/lib/api";

/**
 * "Continue with Google" button.
 *
 * It is only clickable when the backend reports that Google OAuth credentials
 * are configured (GET /auth/google/status). Otherwise it renders disabled with
 * an explicit note — we never show a button that silently does nothing.
 */
export function GoogleAuthButton({ label = "Continue with Google" }: { label?: string }) {
  const [status, setStatus] = useState<"loading" | "ready" | "unconfigured">("loading");

  useEffect(() => {
    fetchGoogleAuthStatus().then((ok) => setStatus(ok ? "ready" : "unconfigured"));
  }, []);

  const start = () => {
    // Full-page navigation into the server-side authorization-code flow.
    window.location.href = googleLoginUrl();
  };

  const disabled = status !== "ready";

  return (
    <div>
      <button
        type="button"
        onClick={start}
        disabled={disabled}
        title={status === "unconfigured" ? "Google sign-in is not configured on this server" : undefined}
        className="w-full py-2.5 text-xs font-mono font-semibold rounded-lg border border-[#E5E5E5] bg-white text-[#0A0A0A] hover:bg-[#F5F5F5] hover:border-[#A3A3A3] disabled:opacity-50 disabled:hover:bg-white disabled:hover:border-[#E5E5E5] disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2.5"
      >
        <GoogleG />
        <span>{status === "loading" ? "CHECKING…" : label}</span>
      </button>
      {status === "unconfigured" && (
        <p className="text-[10px] text-[#A3A3A3] mt-1.5 leading-relaxed font-mono">
          Set <span className="text-[#737373]">GOOGLE_CLIENT_ID</span> and{" "}
          <span className="text-[#737373]">GOOGLE_CLIENT_SECRET</span> on the server to enable.
        </p>
      )}
    </div>
  );
}

function GoogleG() {
  return (
    <svg className="w-4 h-4 shrink-0" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
    </svg>
  );
}
