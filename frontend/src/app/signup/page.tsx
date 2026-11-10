"use client";

import { AuthShell } from "@/components/auth/AuthShell";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, Lock, Mail, User, ArrowRight, Loader2, CheckCircle2, Building2, Users, MailCheck } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { fetchInviteInfo, fetchSignupOptions, InviteInfo, SignupOptions } from "@/lib/api";
import { GoogleAuthButton } from "@/components/auth/GoogleAuthButton";
import { LegalLinks } from "@/components/legal/LegalLinks";

const FIELD = "w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all";
const LABEL = "text-[11px] uppercase font-bold text-slate-500 tracking-wider block mb-1";

export default function SignUpPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [opts, setOpts] = useState<SignupOptions | null>(null);
  const [invite, setInvite] = useState<{ token: string; info: InviteInfo | null; error: string | null } | null>(null);
  const [mode, setMode] = useState<"new" | "demo">("new");
  const [company, setCompany] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [agree, setAgree] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchSignupOptions().then((o) => { setOpts(o); if (!o.new_workspace) setMode("demo"); })
      .catch(() => setOpts({ new_workspace: true, demo_workspace: true, password_min_length: 10 }));
    const token = new URLSearchParams(window.location.search).get("invite");
    if (token) {
      setInvite({ token, info: null, error: null });
      fetchInviteInfo(token)
        .then((info) => { setInvite({ token, info, error: null }); setEmail(info.email); })
        .catch((e) => setInvite({ token, info: null, error: e.message }));
    }
  }, []);

  const min = opts?.password_min_length ?? 10;
  const weak = password.length > 0 && (password.length < min || !/[a-z]/i.test(password) || !/\d/.test(password));
  const mismatch = confirm.length > 0 && confirm !== password;
  const invited = Boolean(invite?.info);
  const needsCompany = !invited && mode === "new";
  const canSubmit = fullName.trim() && email.trim() && password.length >= min && !weak && confirm === password && agree
    && (!needsCompany || company.trim().length >= 2) && !(invite && !invite.info);

  const submit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setError(null);
    try {
      await register(fullName.trim(), email.trim(), password,
        invited ? { invite_token: invite!.token } : mode === "new" ? { workspace: "new", company_name: company.trim() } : { workspace: "demo" });
      router.push(invited || mode === "demo" ? "/dashboard" : "/onboarding");
    } catch (err: any) {
      setError(err?.message || "Could not create your account. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const choice = (value: "new" | "demo", icon: React.ReactNode, title: string, text: string) => (
    <button type="button" onClick={() => setMode(value)} aria-pressed={mode === value}
            className={`text-left rounded-xl border p-2.5 transition-all ${mode === value ? "border-indigo-500 bg-indigo-50/70 ring-1 ring-indigo-200" : "border-slate-200 bg-white hover:border-slate-300"}`}>
      <span className="flex items-center gap-1.5 text-[12px] font-semibold text-slate-900">{icon}{title}</span>
      <span className="block text-[10.5px] text-slate-500 mt-0.5 leading-snug">{text}</span>
    </button>
  );

  return (
    <AuthShell>
      <div className="w-full max-w-sm relative z-10">
        <Link href="/" className="flex items-center justify-center space-x-3 mb-8 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 text-white flex items-center justify-center font-bold tracking-wider shadow-md shadow-indigo-500/25 group-hover:scale-105 transition-transform">
            BV
          </div>
          <div>
            <div className="font-bold text-base tracking-tight text-slate-900">BRANDVAULT AI</div>
            <div className="text-[11px] text-indigo-600 tracking-wider font-bold uppercase">AI Governance Platform</div>
          </div>
        </Link>

        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-soft p-6">
          <div className="mb-4">
            <div className="flex items-center space-x-2 text-slate-900">
              <ShieldCheck className="w-5 h-5 text-indigo-600" />
              <h1 className="text-lg font-bold tracking-tight">Create your account</h1>
            </div>
          </div>

          {invite && (
            <div className={`mb-4 rounded-xl border px-3 py-2.5 text-xs ${invite.error ? "border-rose-200 bg-rose-50 text-rose-700" : "border-emerald-200 bg-emerald-50 text-emerald-800"}`}>
              {invite.error ? invite.error : invite.info ? (
                <span className="flex items-start gap-2"><MailCheck className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>You were invited to <b>{invite.info.workspace}</b> as <b>{invite.info.role}</b>. Sign up with {invite.info.email}.</span></span>
              ) : <span className="flex items-center gap-2"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Checking the invitation…</span>}
            </div>
          )}

          {!invite && opts && (opts.new_workspace || opts.demo_workspace) && (
            <div className="grid grid-cols-2 gap-2 mb-4">
              {opts.new_workspace && choice("new", <Building2 className="w-3.5 h-3.5 text-indigo-600" />, "My company", "A private workspace. You become its Administrator.")}
              {opts.demo_workspace && choice("demo", <Users className="w-3.5 h-3.5 text-indigo-600" />, "Try the demo", "Join the NOVA TECH sample workspace as a Creator.")}
            </div>
          )}

          <form onSubmit={submit} className="space-y-3.5">
            {needsCompany && !invite && (
              <div>
                <label htmlFor="company" className={LABEL}>Company name</label>
                <div className="relative">
                  <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input id="company" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Acme Foods Pvt Ltd" autoComplete="organization" className={FIELD} />
                </div>
              </div>
            )}

            <div>
              <label htmlFor="name" className={LABEL}>Full name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input id="name" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Jordan Rivera" autoComplete="name" className={FIELD} />
              </div>
            </div>

            <div>
              <label htmlFor="email" className={LABEL}>Work email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input id="email" type="email" value={email} readOnly={invited} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="username" className={FIELD + (invited ? " opacity-80" : "")} />
              </div>
            </div>

            <div>
              <label htmlFor="pw" className={LABEL}>Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input id="pw" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder={`At least ${min} characters, letters and numbers`} autoComplete="new-password" className={FIELD} />
              </div>
              {weak && <p className="text-[11px] text-amber-700 mt-1 font-medium">Use at least {min} characters with both letters and numbers.</p>}
            </div>

            <div>
              <label htmlFor="pw2" className={LABEL}>Confirm password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input id="pw2" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Re-enter password" autoComplete="new-password" className={FIELD.replace("pr-3", "pr-9")} />
                {confirm.length > 0 && !mismatch && <CheckCircle2 className="w-4 h-4 text-emerald-600 absolute right-3 top-1/2 -translate-y-1/2" />}
              </div>
              {mismatch && <p className="text-[11px] text-rose-600 mt-1 font-medium">Passwords don&apos;t match.</p>}
            </div>

            <label className="flex items-start gap-2 text-[11.5px] text-slate-600">
              <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} className="mt-0.5 accent-indigo-600" />
              <span>I agree to the <Link href="/legal/terms" className="text-indigo-600 hover:underline">Terms</Link> and the <Link href="/legal/privacy" className="text-indigo-600 hover:underline">Privacy Policy</Link>.</span>
            </label>

            {error && <div className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2 font-medium">{error}</div>}

            <button type="submit" disabled={busy || !canSubmit}
              className="w-full py-2.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white disabled:opacity-50 transition-all flex items-center justify-center space-x-2 shadow-md shadow-indigo-500/20 active:scale-[0.99]">
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin text-white" /> : <ArrowRight className="w-3.5 h-3.5 text-indigo-200" />}
              <span>{busy ? "Creating…" : invited ? "Join the workspace" : mode === "new" ? "Create company workspace" : "Create account"}</span>
            </button>
          </form>

          {!invite && (
            <>
              <div className="flex items-center gap-3 my-4">
                <div className="h-px flex-1 bg-slate-100" />
                <span className="text-[10px] uppercase font-bold text-slate-400">or</span>
                <div className="h-px flex-1 bg-slate-100" />
              </div>
              <GoogleAuthButton label="Sign up with Google" />
              <p className="text-[10.5px] text-slate-400 mt-1.5 text-center">Google sign-up joins the demo workspace. Use an invitation to join your company.</p>
            </>
          )}

          <p className="text-xs text-slate-500 text-center mt-4">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-indigo-600 hover:underline">Sign in</Link>
          </p>
        </div>

        <div className="text-center mt-5 space-y-2">
          <Link href="/" className="text-xs font-medium text-slate-500 hover:text-indigo-600 transition-colors">← Back to home</Link>
          <LegalLinks />
        </div>
      </div>
    </AuthShell>
  );
}
