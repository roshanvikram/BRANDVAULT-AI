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
    } catch {
      setError("Invalid email or password. Try a demo account below.");
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
    <div className="min-h-screen bg-[#F7F7F7] flex items-center justify-center p-6 select-none">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <Link href="/" className="flex items-center justify-center space-x-3 mb-8 group">
          <div className="w-10 h-10 rounded-xl bg-[#0A0A0A] text-white flex items-center justify-center font-mono font-bold tracking-wider shadow-sm group-hover:scale-105 transition-transform">
            BV
          </div>
          <div>
            <div className="font-bold text-sm tracking-tight text-[#0A0A0A]">BRANDVAULT AI</div>
            <div className="text-[9px] text-[#737373] tracking-widest font-mono uppercase">AI Governance</div>
          </div>
        </Link>

        {/* Card */}
        <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-sm p-6">
          <div className="mb-5">
            <div className="flex items-center space-x-2 text-[#0A0A0A]">
              <ShieldCheck className="w-4 h-4" />
              <h1 className="text-base font-bold tracking-tight">Sign in</h1>
            </div>
            <p className="text-xs text-[#737373] mt-1">Access the brand governance console.</p>
          </div>

          <form onSubmit={submit} className="space-y-3">
            <div>
              <label className="text-[10px] font-mono uppercase text-[#737373] font-semibold block mb-1">Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#A3A3A3] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  autoComplete="username"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg text-[#0A0A0A] placeholder-[#A3A3A3] focus:outline-none focus:border-[#0A0A0A] focus:bg-white transition-all"
                />
              </div>
            </div>

            <div>
              <label className="text-[10px] font-mono uppercase text-[#737373] font-semibold block mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#A3A3A3] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg text-[#0A0A0A] placeholder-[#A3A3A3] focus:outline-none focus:border-[#0A0A0A] focus:bg-white transition-all"
                />
              </div>
            </div>

            {error && (
              <div className="text-[11px] font-mono text-[#0A0A0A] bg-[#F5F5F5] border border-[#E5E5E5] rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy || !email || !password}
              className="w-full py-2.5 text-xs font-mono font-bold rounded-lg bg-[#0A0A0A] text-white hover:bg-[#262626] disabled:opacity-50 transition-all flex items-center justify-center space-x-2 shadow-sm"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ArrowRight className="w-3.5 h-3.5" />}
              <span>{busy ? "SIGNING IN…" : "SIGN IN"}</span>
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-4">
            <div className="h-px flex-1 bg-[#F0F0F0]" />
            <span className="text-[10px] font-mono uppercase text-[#A3A3A3]">or</span>
            <div className="h-px flex-1 bg-[#F0F0F0]" />
          </div>

          {/* Google OAuth */}
          <GoogleAuthButton label="Continue with Google" />

          {/* Sign-up link */}
          <p className="text-[11px] text-[#737373] text-center mt-4">
            New to BrandVault?{" "}
            <Link href="/signup" className="font-semibold text-[#0A0A0A] hover:underline">
              Create an account
            </Link>
          </p>

          {/* Demo accounts */}
          <div className="mt-5 pt-4 border-t border-[#F0F0F0]">
            <div className="text-[10px] font-mono uppercase text-[#A3A3A3] font-bold mb-2">Demo accounts (one-click fill)</div>
            <div className="grid grid-cols-3 gap-2">
              {DEMO_ROLES.map((role) => (
                <button
                  key={role}
                  type="button"
                  onClick={() => fillDemo(role)}
                  className="px-2 py-1.5 text-[10px] font-mono font-semibold rounded-lg border border-[#E5E5E5] bg-white text-[#0A0A0A] hover:bg-[#F5F5F5] hover:border-[#A3A3A3] transition-all"
                >
                  {role === "Administrator" ? "Admin" : role}
                </button>
              ))}
            </div>
            <p className="text-[10px] text-[#A3A3A3] mt-2 leading-relaxed">
              Reviewers & Administrators can approve content; Creators can submit for review.
            </p>
          </div>
        </div>

        <div className="text-center mt-5">
          <Link href="/" className="text-[11px] font-mono text-[#737373] hover:text-[#0A0A0A] transition-colors">
            ← Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
