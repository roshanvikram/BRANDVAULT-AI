"use client";

import { useEffect, useState } from "react";
import { Users, Lightbulb, Clock, Inbox, FilePlus2, Check } from "lucide-react";
import { fetchReviewerIntel, proposeGuidelineRule, ReviewerIntel } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CARD, Badge, PageHeader, ErrorNote, Loading, BTN_SECONDARY } from "@/components/engines/ui";

const KIND_LABEL: Record<string, string> = {
  clarify_policy: "Clarify policy", align_reviewers: "Reviewer guidance", rule_gap: "Possible rule gap", terminology: "Creator guidance",
};

export default function ReviewerIntelligencePage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "Administrator";
  const [data, setData] = useState<ReviewerIntel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drafted, setDrafted] = useState<Record<number, boolean>>({});

  useEffect(() => { fetchReviewerIntel().then(setData).catch((e) => setError(e.message)); }, []);

  const draft = async (i: number, title: string, text: string) => {
    setError(null);
    try { await proposeGuidelineRule({ title, rule_text: text }); setDrafted((d) => ({ ...d, [i]: true })); }
    catch (e: any) { setError(e.message); }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        back={{ href: "/approval-hub", label: "Approval Hub" }}
        eyebrow="AI Reviewer Intelligence" icon={<Users className="w-3.5 h-3.5" />}
        title="What reviewer decisions say about your rules"
        description="Compares AI findings with recorded human decisions to find unclear policies, unwritten exceptions, rule gaps and review bottlenecks. It analyses policies, not people — there are no reviewer rankings, and guidelines are never changed automatically."
      />
      <ErrorNote message={error} />
      {!data ? <Loading label="Analysing decisions…" /> : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[["Decisions analysed", data.decisions_analysed], ["Median turnaround", data.turnaround.median_hours === null ? "—" : `${data.turnaround.median_hours} h`],
              ["Waiting for review", data.queue.waiting], ["Suggestions", data.recommendations.length]].map(([k, v]) => (
              <div key={k as string} className={`${CARD} p-4`}>
                <div className="text-xs text-slate-500">{k}</div>
                <div className="mt-1 text-2xl font-bold text-slate-900 tabular-nums">{v}</div>
              </div>
            ))}
          </div>
          {!data.data_sufficient && (
            <div className="text-[13px] text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">{data.data_note}</div>
          )}

          <div className={`${CARD} p-5`}>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><Lightbulb className="w-4 h-4 text-amber-500" /> Suggested guideline improvements</h3>
            {data.recommendations.length === 0 ? (
              <p className="mt-2 text-[13px] text-slate-500">No repeated pattern yet. Suggestions appear once the same issue recurs across decisions.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {data.recommendations.map((r, i) => (
                  <li key={i} className="rounded-xl border border-slate-200 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2"><Badge tone="ai">{KIND_LABEL[r.kind] || r.kind}</Badge><span className="text-[13px] font-semibold text-slate-900">{r.title}</span></div>
                      {isAdmin && (
                        drafted[i] ? <Badge tone="good"><Check className="w-3 h-3" /> Draft rule created</Badge> :
                        <button onClick={() => draft(i, r.title.slice(0, 250), r.proposed_rule)} className={BTN_SECONDARY}><FilePlus2 className="w-3.5 h-3.5" /> Create draft rule</button>
                      )}
                    </div>
                    <p className="mt-1.5 text-xs text-slate-600">{r.detail}</p>
                    {r.reviewer_comments.length > 0 && (
                      <div className="mt-2 space-y-1">{r.reviewer_comments.map((c, j) => <p key={j} className="text-[11px] text-slate-500 italic">Reviewer: “{c}”</p>)}</div>
                    )}
                    <p className="mt-2 text-xs text-indigo-700">Proposed: {r.proposed_rule}</p>
                  </li>
                ))}
              </ul>
            )}
            {isAdmin && <p className="mt-3 text-[11px] text-slate-400">Draft rules are not enforced until you confirm them in Brand DNA Studio.</p>}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">Findings reviewers approved anyway</h3>
              {data.overridden_findings.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">None recorded.</p> : (
                <ul className="mt-2 divide-y divide-slate-100">
                  {data.overridden_findings.slice(0, 8).map((o) => (
                    <li key={o.rule} className="py-2.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[13px] font-medium text-slate-800">{o.rule}</span>
                        <span className="text-xs font-semibold text-slate-700 tabular-nums shrink-0">{o.count}×</span>
                      </div>
                      <div className="text-[11px] text-slate-500">{o.category} · {o.severity} · e.g. “{o.examples[0]?.text}” in {o.examples[0]?.title}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">Rejections the AI did not anticipate</h3>
              {data.unanticipated_rejections.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">None recorded.</p> : (
                <ul className="mt-2 divide-y divide-slate-100">
                  {data.unanticipated_rejections.slice(0, 8).map((u) => (
                    <li key={u.submission_id} className="py-2.5">
                      <div className="flex items-center justify-between gap-2"><span className="text-[13px] font-medium text-slate-800 truncate">{u.title}</span><Badge tone="warn">{u.decision} · AI {u.score}</Badge></div>
                      {u.reviewer_comment && <div className="text-[11px] text-slate-500 italic">“{u.reviewer_comment}”</div>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900">Rules decided differently</h3>
              {data.disagreements.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">No conflicting decisions recorded.</p> : (
                <ul className="mt-2 space-y-2">
                  {data.disagreements.map((d) => (
                    <li key={d.rule} className="text-xs text-slate-700"><span className="font-medium">{d.rule}</span> — {Object.entries(d.decisions).map(([k, v]) => `${k} ${v}`).join(" · ")}</li>
                  ))}
                </ul>
              )}
            </div>
            <div className={`${CARD} p-5`}>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><Inbox className="w-4 h-4 text-slate-400" /> Review queue</h3>
              {data.queue.oldest.length === 0 ? <p className="mt-2 text-[13px] text-slate-500">Nothing waiting.</p> : (
                <ul className="mt-2 divide-y divide-slate-100">
                  {data.queue.oldest.map((q) => (
                    <li key={q.submission_id} className="py-2 flex items-center justify-between gap-2 text-xs">
                      <span className="text-slate-700 truncate">{q.title}</span>
                      <span className="text-slate-500 shrink-0 inline-flex items-center gap-1"><Clock className="w-3 h-3" /> {q.waiting_hours} h · {q.status}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          <p className="text-[11px] text-slate-400">{data.principles}</p>
        </>
      )}
    </div>
  );
}
