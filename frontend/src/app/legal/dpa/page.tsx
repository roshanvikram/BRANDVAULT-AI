import { LegalPage } from "@/components/legal/LegalLinks";

export const metadata = { title: "Data Processing Agreement · BrandVault AI" };

export default function DpaPage() {
  return (
    <LegalPage title="Data Processing Agreement" updated="10 November 2026">
      <p>This agreement applies when [Your company name] (&ldquo;processor&rdquo;) processes personal data in content the customer (&ldquo;controller&rdquo;) adds to BrandVault. It forms part of the <a href="/legal/terms" className="text-indigo-600 underline">Terms of Service</a>.</p>

      <h2>1. Scope</h2>
      <table><tbody>
        <tr><td><b>Purpose</b></td><td>Brand-governance checks, reviews, approvals and records requested by the controller.</td></tr>
        <tr><td><b>Data subjects</b></td><td>The controller&apos;s staff using the service; people named in uploaded content or customer feedback.</td></tr>
        <tr><td><b>Data types</b></td><td>Names, work emails, roles; any personal data inside uploaded documents, images and feedback.</td></tr>
        <tr><td><b>Duration</b></td><td>While the workspace exists, then deletion as in section 7.</td></tr>
      </tbody></table>

      <h2>2. Instructions</h2>
      <p>The processor processes the data only to provide the service and on the controller&apos;s documented instructions, including through the controller&apos;s use of the app.</p>

      <h2>3. Confidentiality</h2>
      <p>Everyone with access to the data is bound by confidentiality.</p>

      <h2>4. Security measures</h2>
      <ul>
        <li>Encryption in transit (HTTPS). [Encryption at rest provided by the database host.]</li>
        <li>Each workspace&apos;s data is separated by the application and, on PostgreSQL, by database Row-Level Security policies.</li>
        <li>Passwords stored as salted PBKDF2-SHA256 hashes; optional two-step sign-in (TOTP); lockout after repeated failed sign-ins.</li>
        <li>Role-based access (Creator, Reviewer, Administrator); a security log of sign-ins, role changes, exports and deletions.</li>
        <li>API keys stored only as hashes; signed webhooks; request rate limits.</li>
        <li>Backups: [frequency, retention, encryption, location].</li>
      </ul>

      <h2>5. Sub-processors</h2>
      <p>The controller authorises these sub-processors: [Render (hosting), Neon (database), the AI providers enabled for the workspace, the email provider, Sentry if enabled]. The processor will give [30] days&apos; notice of a new sub-processor, during which the controller may object.</p>

      <h2>6. Assistance</h2>
      <p>The processor helps the controller answer data-subject requests (the app provides export and deletion), and with security, breach-notification and impact-assessment duties. The processor notifies the controller of a personal-data breach without undue delay and within [48] hours of becoming aware of it.</p>

      <h2>7. Deletion and return</h2>
      <p>The controller can export all workspace data and delete the workspace at any time. Deletion removes the records from the live database at once; copies in backups expire within [30] days.</p>

      <h2>8. Audits</h2>
      <p>The processor makes available the information needed to show compliance, and allows audits [once a year, with 30 days&apos; notice].</p>

      <h2>9. Transfers</h2>
      <p>[Where data is stored; Standard Contractual Clauses or other safeguards for transfers.]</p>
    </LegalPage>
  );
}
