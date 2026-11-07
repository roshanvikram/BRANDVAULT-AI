"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, Lock, Mail, ArrowRight, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { DEMO_CREDS, setToken } from "@/lib/api";
import { GoogleAuthButton } from "@/components/auth/GoogleAuthButton";

const DEMO_ROLES: ("Administrator" | "Creator" | "Reviewer")[] = ["Administrator", "Creator", "Reviewer"];

const OAUTH_ERRORS: Record<string, string> = {
  google_no_code: "Google did not return an authorization code. Please try again.",
  google_bad_state: "The sign-in request expired or was invalid. Please try again.",
  google_token_exchange: "Google rejected the authorization. Please try again.",
  google_unreachable: "Could not reach Google to complete sign-in. Check the server's connectivity.",
  google_profile: "Google did not return a usable profile. Please try again.",
  google_unverified_email: "Your Google email is not verified.",
  account_disabled: "This account is disabled. Contact an administrator.",
};

export default function LoginPage() {
  const router = useRouter();
  const { login, refresh } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Google OAuth bounces back to /login with the token (or an error) in the URL
  // fragment — never a query string, so it stays out of server logs.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) return;
    const params = new URLSearchParams(hash);
    const token = params.get("token");
    const err = params.get("error");
    // Clear the fragment so the token isn't left in the address bar / history.
    history.replaceState(null, "", window.location.pathname);
    if (token) {
      setToken(token);
      setBusy(true);
      refresh().then(() => router.push("/dashboard"));
    } else if (err) {
      setError(OAUTH_ERRORS[err] || "Google sign-in failed. Please try again.");
    }
  }, [refresh, router]);

  const submit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!email || !password) return;
    setBusy(true);
    setError(null);
    try {
      await login(email.trim(), password);
      router.push("/dashboard");
    } catch (err: any) {
      // Surface the real reason (bad credentials vs. server unreachable vs.
      // server error) rather than always blaming the credentials.
      setError(err?.message || "Sign-in failed. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const fillDemo = (role: "Administrator" | "Creator" | "Reviewer") => {
    setEmail(DEMO_CREDS[role].email);
    setPassword(DEMO_CREDS[role].password);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-6 select-none relative overflow-hidden">
      {/* Ambient background glow */}
      <div aria-hidden className="pointer-events-none absolute -top-40 -left-40 w-96 h-96 rounded-full bg-indigo-200/40 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-purple-200/40 blur-3xl" />

      <div className="w-full max-w-sm relative z-10">
        {/* Brand */}
        <Link href="/" className="flex items-center justify-center space-x-3 mb-8 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 text-white flex items-center justify-center font-bold tracking-wider shadow-md shadow-indigo-500/25 group-hover:scale-105 transition-transform">
            BV
          </div>
          <div>
            <div className="font-bold text-base tracking-tight text-slate-900">BRANDVAULT AI</div>
            <div className="text-[11px] text-indigo-600 tracking-wider font-bold uppercase">AI Governance Platform</div>
          </div>
        </Link>

        {/* Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-soft p-6">
          <div className="mb-5">
            <div className="flex items-center space-x-2 text-slate-900">
              <ShieldCheck className="w-5 h-5 text-indigo-600" />
              <h1 className="text-lg font-bold tracking-tight">Sign in</h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">Access the brand governance operating system.</p>
          </div>

          <form onSubmit={submit} className="space-y-3.5">
            <div>
              <label className="text-[11px] uppercase font-bold text-slate-500 tracking-wider block mb-1">Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  autoComplete="username"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] uppercase font-bold text-slate-500 tracking-wider block mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all"
                />
              </div>
            </div>

            {error && (
              <div className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2 font-medium">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy || !email || !password}
              className="w-full py-2.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white disabled:opacity-50 transition-all flex items-center justify-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin text-white" /> : <ArrowRight className="w-3.5 h-3.5 text-indigo-200" />}
              <span>{busy ? "Signing in…" : "Sign in"}</span>
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-4">
            <div className="h-px flex-1 bg-slate-100" />
            <span className="text-[10px] uppercase font-bold text-slate-400">or</span>
            <div className="h-px flex-1 bg-slate-100" />
          </div>

          {/* Google OAuth */}
          <GoogleAuthButton label="Continue with Google" />

          {/* Sign-up link */}
          <p className="text-xs text-slate-500 text-center mt-4">
            New to BrandVault?{" "}
            <Link href="/signup" className="font-semibold text-indigo-600 hover:underline">
              Create an account
            </Link>
          </p>

          {/* Demo accounts */}
          <div className="mt-5 pt-4 border-t border-slate-100">
            <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">Demo accounts (one-click fill)</div>
            <div className="grid grid-cols-3 gap-2">
              {[
                { r: "Administrator", label: "Admin", cls: "bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100" },
                { r: "Reviewer", label: "Reviewer", cls: "bg-purple-50 text-purple-800 border-purple-200 hover:bg-purple-100" },
                { r: "Creator", label: "Creator", cls: "bg-indigo-50 text-indigo-800 border-indigo-200 hover:bg-indigo-100" },
              ].map(({ r, label, cls }) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => fillDemo(r as any)}
                  className={`px-2 py-1.5 text-xs font-semibold rounded-xl border transition-all shadow-sm ${cls}`}
                >
                  {label}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
              Reviewers & Administrators can approve content; Creators can submit for review.
            </p>
          </div>
        </div>

        <div className="text-center mt-5">
          <Link href="/" className="text-xs font-medium text-slate-500 hover:text-indigo-600 transition-colors">
            ← Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
