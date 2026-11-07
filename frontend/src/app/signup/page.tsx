"use client";

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
    <div className="min-h-screen bg-[#F7F7F7] flex items-center justify-center p-6 select-none">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <Link href="/" className="flex items-center justify-center space-x-3 mb-8 group">
          <div className="w-10 h-10 rounded-xl bg-[#0A0A0A] text-white flex items-center justify-center font-mono font-bold tracking-wider shadow-sm group-hover:scale-105 transition-transform">
            BV
          </div>
          <div>
            <div className="font-bold text-sm tracking-tight text-[#0A0A0A]">BRANDVAULT AI</div>
            <div className="text-[11px] text-[#737373] tracking-widest font-mono uppercase">AI Governance</div>
          </div>
        </Link>

        {/* Card */}
        <div className="bg-white rounded-xl border border-[#E5E5E5] shadow-sm p-6">
          <div className="mb-5">
            <div className="flex items-center space-x-2 text-[#0A0A0A]">
              <ShieldCheck className="w-4 h-4" />
              <h1 className="text-base font-bold tracking-tight">Create your account</h1>
            </div>
            <p className="text-xs text-[#737373] mt-1">
              You&apos;ll join the workspace as a <span className="font-semibold text-[#0A0A0A]">Creator</span> — submit
              content for review. Approval rights are granted by an administrator.
            </p>
          </div>

          <form onSubmit={submit} className="space-y-3">
            <div>
              <label className="text-[11px] font-mono uppercase text-[#737373] font-semibold block mb-1">Full name</label>
              <div className="relative">
                <User className="w-4 h-4 text-[#A3A3A3] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jordan Rivera"
                  autoComplete="name"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg text-[#0A0A0A] placeholder-[#A3A3A3] focus:outline-none focus:border-[#0A0A0A] focus:bg-white transition-all"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-mono uppercase text-[#737373] font-semibold block mb-1">Email</label>
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
              <label className="text-[11px] font-mono uppercase text-[#737373] font-semibold block mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#A3A3A3] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  autoComplete="new-password"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg text-[#0A0A0A] placeholder-[#A3A3A3] focus:outline-none focus:border-[#0A0A0A] focus:bg-white transition-all"
                />
              </div>
              {pwShort && (
                <p className="text-[11px] text-[#A3A3A3] mt-1 font-mono">Minimum 8 characters.</p>
              )}
            </div>

            <div>
              <label className="text-[11px] font-mono uppercase text-[#737373] font-semibold block mb-1">Confirm password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#A3A3A3] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Re-enter password"
                  autoComplete="new-password"
                  className="w-full pl-9 pr-9 py-2 text-xs bg-[#FAFAFA] border border-[#E5E5E5] rounded-lg text-[#0A0A0A] placeholder-[#A3A3A3] focus:outline-none focus:border-[#0A0A0A] focus:bg-white transition-all"
                />
                {confirm.length > 0 && !mismatch && (
                  <CheckCircle2 className="w-4 h-4 text-[#0A0A0A] absolute right-3 top-1/2 -translate-y-1/2" />
                )}
              </div>
              {mismatch && (
                <p className="text-[11px] text-[#A3A3A3] mt-1 font-mono">Passwords don&apos;t match.</p>
              )}
            </div>

            {error && (
              <div className="text-[11px] font-mono text-[#0A0A0A] bg-[#F5F5F5] border border-[#E5E5E5] rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy || !canSubmit}
              className="w-full py-2.5 text-xs font-mono font-bold rounded-lg bg-[#0A0A0A] text-white hover:bg-[#262626] disabled:opacity-50 transition-all flex items-center justify-center space-x-2 shadow-sm"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ArrowRight className="w-3.5 h-3.5" />}
              <span>{busy ? "Creating…" : "Create account"}</span>
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3 my-4">
            <div className="h-px flex-1 bg-[#F0F0F0]" />
            <span className="text-[11px] font-mono uppercase text-[#A3A3A3]">or</span>
            <div className="h-px flex-1 bg-[#F0F0F0]" />
          </div>

          {/* Google OAuth */}
          <GoogleAuthButton label="Sign up with Google" />

          {/* Sign-in link */}
          <p className="text-[11px] text-[#737373] text-center mt-4">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-[#0A0A0A] hover:underline">
              Sign in
            </Link>
          </p>
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
