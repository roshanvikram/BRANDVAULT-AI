"use client";

import { AuthShell } from "@/components/auth/AuthShell";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, Lock, Mail, User, ArrowRight, Loader2, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { GoogleAuthButton } from "@/components/auth/GoogleAuthButton";

export default function SignUpPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const pwShort = password.length > 0 && password.length < 8;
  const mismatch = confirm.length > 0 && confirm !== password;
  const canSubmit = fullName.trim() && email.trim() && password.length >= 8 && confirm === password;

  const submit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setError(null);
    try {
      await register(fullName.trim(), email.trim(), password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Could not create your account. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell>
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
              <h1 className="text-lg font-bold tracking-tight">Create your account</h1>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              You&apos;ll join the workspace as a <span className="font-semibold text-indigo-700">Creator</span> — submit
              content for review.
            </p>
          </div>

          <form onSubmit={submit} className="space-y-3.5">
            <div>
              <label className="text-[11px] uppercase font-bold text-slate-500 tracking-wider block mb-1">Full name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jordan Rivera"
                  autoComplete="name"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all"
                />
              </div>
            </div>

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
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all"
                />
              </div>
              {pwShort && (
                <p className="text-[11px] text-amber-600 mt-1 font-medium">Minimum 8 characters.</p>
              )}
            </div>

            <div>
              <label className="text-[11px] uppercase font-bold text-slate-500 tracking-wider block mb-1">Confirm password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Re-enter password"
                  autoComplete="new-password"
                  className="w-full pl-9 pr-9 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all"
                />
                {confirm.length > 0 && !mismatch && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 absolute right-3 top-1/2 -translate-y-1/2" />
                )}
              </div>
              {mismatch && (
                <p className="text-[11px] text-rose-600 mt-1 font-medium">Passwords don&apos;t match.</p>
              )}
            </div>

            {error && (
              <div className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2 font-medium">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy || !canSubmit}
              className="w-full py-2.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white disabled:opacity-50 transition-all flex items-center justify-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin text-white" /> : <ArrowRight className="w-3.5 h-3.5 text-indigo-200" />}
              <span>{busy ? "Creating…" : "Create account"}</span>
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-4">
            <div className="h-px flex-1 bg-slate-100" />
            <span className="text-[10px] uppercase font-bold text-slate-400">or</span>
            <div className="h-px flex-1 bg-slate-100" />
          </div>

          {/* Google OAuth */}
          <GoogleAuthButton label="Sign up with Google" />

          {/* Sign-in link */}
          <p className="text-xs text-slate-500 text-center mt-4">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-indigo-600 hover:underline">
              Sign in
            </Link>
          </p>
        </div>

        <div className="text-center mt-5">
          <Link href="/" className="text-xs font-medium text-slate-500 hover:text-indigo-600 transition-colors">
            ← Back to home
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}
