import { LegalPage } from "@/components/legal/LegalLinks";

export const metadata = { title: "Security · BrandVault AI" };

export default function SecurityPage() {
  return (
    <LegalPage title="Security" updated="10 November 2026">
      <p>How BrandVault protects workspace data. Everything listed under &ldquo;Built in&rdquo; is implemented and covered by automated tests; items marked [to do] depend on how you run the service.</p>

      <h2>Built in</h2>
      <ul>
        <li><b>Workspace separation:</b> every query is scoped to the signed-in user&apos;s workspace; on PostgreSQL, Row-Level Security in the database enforces it a second time.</li>
        <li><b>Sign-in:</b> salted PBKDF2-SHA256 passwords (200,000 rounds), minimum length and common-password checks, account lockout after repeated failures, optional two-step sign-in with any authenticator app, optional Google sign-in.</li>
        <li><b>Sessions:</b> signed tokens that expire; changing a password, changing a role or &ldquo;sign out everywhere&rdquo; ends every older session.</li>
        <li><b>Roles:</b> Creators submit, Reviewers and Administrators approve. Nobody can raise their own role; a workspace always keeps an Administrator.</li>
        <li><b>Audit:</b> a security log of sign-ins, lockouts, two-step changes, invitations, role changes, exports and deletions.</li>
        <li><b>Integrations:</b> API keys stored only as hashes with limited scopes; webhooks signed with HMAC-SHA256.</li>
        <li><b>Web protections:</b> rate limits shared across servers, strict CORS, security headers (no framing, no MIME sniffing, HSTS in production), no stack traces in error responses.</li>
        <li><b>Data rights:</b> full workspace export and permanent deletion from Settings.</li>
        <li><b>Operations:</b> request IDs on every response, stored error reports, optional Sentry, Prometheus metrics, a portable backup and restore tool.</li>
      </ul>

      <h2>Depends on deployment</h2>
      <ul>
        <li>[to do] Persistent PostgreSQL database (for example Neon) with encryption at rest and point-in-time restore.</li>
        <li>[to do] Scheduled, encrypted off-site backups using <code>backend/scripts/backup.py</code>, and a tested restore.</li>
        <li>[to do] An independent penetration test before onboarding regulated customers.</li>
        <li>[to do] SOC 2 or ISO 27001, if your customers require it.</li>
      </ul>

      <h2>Reporting a problem</h2>
      <p>Email [security@yourcompany.com]. Please give us a reasonable time to fix an issue before disclosing it publicly.</p>
    </LegalPage>
  );
}
