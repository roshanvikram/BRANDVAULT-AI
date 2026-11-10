import Link from "next/link";

const LINKS = [
  { href: "/legal/privacy", label: "Privacy" },
  { href: "/legal/terms", label: "Terms" },
  { href: "/legal/dpa", label: "Data processing" },
  { href: "/legal/security", label: "Security" },
];

export function LegalLinks() {
  return (
    <nav aria-label="Legal" className="flex flex-wrap justify-center gap-x-3 gap-y-1 text-[11px] text-slate-400">
      {LINKS.map((l) => <Link key={l.href} href={l.href} className="hover:text-indigo-600 hover:underline">{l.label}</Link>)}
    </nav>
  );
}

export function LegalPage({ title, updated, children }: { title: string; updated: string; children: React.ReactNode }) {
  return (
    <main className="min-h-screen px-4 py-10">
      <article className="mx-auto max-w-3xl bv-glass-edge bg-white/90 border border-white/75 rounded-2xl p-6 sm:p-10 text-[13.5px] leading-relaxed text-slate-700
                          [&_h2]:text-base [&_h2]:font-semibold [&_h2]:text-slate-900 [&_h2]:mt-7 [&_h2]:mb-2
                          [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1 [&_p]:mt-2 [&_td]:align-top [&_td]:py-1.5 [&_td]:pr-3">
        <Link href="/" className="text-xs font-semibold text-indigo-600 hover:underline">← BrandVault AI</Link>
        <h1 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        <p className="text-xs text-slate-500 mt-1">Last updated {updated}</p>
        <div role="note" className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-[12px] text-amber-900">
          <b>Template.</b> This describes how the BrandVault software actually handles data. Before customers rely on it,
          fill in the parts in [square brackets] and have it reviewed by a lawyer for your country.
        </div>
        {children}
        <div className="mt-10 pt-4 border-t border-slate-100"><LegalLinks /></div>
      </article>
    </main>
  );
}
