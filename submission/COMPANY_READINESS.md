# Company readiness

What was added so a real company (not just the demo) can use BrandVault, and what still needs people or money rather than code.

## Built and tested

| Area | What exists now | How to use it |
|---|---|---|
| Company workspaces | Sign-up creates a private workspace; the founder becomes its Administrator. The demo workspace remains available as an option. | Sign-up page → **My company** |
| Team | Email invitations with a role, role changes, turning access off, unlocking a locked account. A workspace always keeps an Administrator. | Settings → Team |
| Sign-in security | Two-step sign-in (TOTP authenticator apps), lockout after 5 wrong tries, password rules (10+ characters, letters and numbers, no common passwords), sessions end on password or role change, "sign out everywhere". | Settings → Security |
| Audit | Security log: sign-ins, failures, lockouts, two-step changes, invitations, role changes, exports, deletions, with IP and time. | Settings → Security (Administrators) |
| Data protection | Full workspace export (JSON + files, secrets removed), close my account, delete the workspace permanently. | Settings → Data & privacy |
| Legal | Privacy Policy, Terms, Data Processing Agreement and Security pages that describe the real system, with the company-specific parts marked [like this]. | `/legal/...`, linked from sign-in and sign-up |
| Operations | Request ID on every response; JSON request logs; server errors stored and shown to Administrators; optional Sentry; Prometheus `/metrics`; `/ready` check; security headers on the API and the website. | Settings → System |
| Backups | Portable backup, verify and restore tool (SQLite and PostgreSQL); restore refuses non-empty databases. | `python -m backend.scripts.backup` |
| AI reliability | Anthropic, Groq, OpenAI and Gemini drivers in one fallback chain (one provider's rate limit or outage no longer turns AI off), plus a one-hour answer cache. | Set more than one API key |
| Fraud monitoring | Look-alike domain watch: searches public Certificate Transparency logs (crt.sh) daily and on demand, scores each domain, and turns a hit into an incident in one click. | Brand Fraud Intelligence → Look-alike domain watch |
| Fix found on the way | Brand Fraud missed the same name on another extension (`brand.cc` copying `brand.com`), and treated `.co.in` names as subdomains. Both are fixed and covered by tests. | |

**Tests:** 21 new automated tests (`backend/tests/test_company_readiness.py`), including the RFC 6238 test vectors for two-step codes and a full backup round trip. Full suite: 276 tests pass (3 PostgreSQL-only tests skipped on SQLite). A real domain-watch search found 149 certificates and 5 look-alike domains for a test domain.

## Still needed (not code)

| Item | Why | Who |
|---|---|---|
| Persistent database | The live site still uses SQLite, which is wiped on restart. Add Neon's `DATABASE_URL` in Render. | You (5 minutes, free) |
| Always-on hosting | The free plan sleeps outside 9 AM–8:30 PM IST. A paid instance is about $7 a month per service. | You (cost) |
| Production settings | Set `FRONTEND_URL`, `SEED_DEMO_CONTENT=false`, `DEMO_ACCOUNTS_ENABLED=false`, SMTP for invitation emails. | You |
| Legal review | Fill in the [bracketed] parts of the legal pages; a lawyer must review them. | Lawyer |
| Pilot customers | Real brand teams using it for a few weeks; their feedback decides what to fix next. Reviewer insight also needs this real history. | Business |
| Independent security test | A penetration test before regulated customers; SOC 2 / ISO 27001 if customers ask. | Security firm |
| Social media and ad monitoring | Needs paid data feeds or platform API approval (Meta, Google Ads). | Business decision |
| Paid AI plan | Free AI tiers slow down under heavy use; the fallback chain helps but does not remove the limit. | You (cost) |
