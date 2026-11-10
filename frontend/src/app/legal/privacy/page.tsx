import { LegalPage } from "@/components/legal/LegalLinks";

export const metadata = { title: "Privacy Policy · BrandVault AI" };

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" updated="10 November 2026">
      <p>[Your company name] (&ldquo;we&rdquo;) runs BrandVault AI, a brand-governance service used by companies (&ldquo;customers&rdquo;) to check marketing content against their brand rules. This policy explains what personal data the service handles and why.</p>

      <h2>Who is responsible</h2>
      <p>For content a customer uploads, the customer is the data controller and we process it on their instructions (see the <a href="/legal/dpa" className="text-indigo-600 underline">Data Processing Agreement</a>). For account and billing data, we are the controller. Contact: [privacy@yourcompany.com], [postal address].</p>

      <h2>What we collect</h2>
      <ul>
        <li><b>Account data:</b> name, work email, role, workspace, sign-in method. Passwords are stored only as salted PBKDF2-SHA256 hashes. Two-step sign-in secrets are stored to check codes.</li>
        <li><b>Content customers add:</b> brand guidelines, rules, product facts, marketing copy, images, videos, translations, customer feedback files and review decisions.</li>
        <li><b>Security records:</b> sign-in attempts, lockouts, role changes, exports and deletions, with the IP address and time.</li>
        <li><b>Service records:</b> request logs and server errors (path, time, request ID), used to run and fix the service.</li>
      </ul>
      <p>We do not use advertising trackers. The browser stores only the sign-in token and small display preferences.</p>

      <h2>Why we use it</h2>
      <ul>
        <li>To provide the service the customer signed up for (contract).</li>
        <li>To keep accounts and data secure and to investigate misuse (legitimate interest).</li>
        <li>To meet legal obligations, such as tax records for billing.</li>
      </ul>

      <h2>AI processing</h2>
      <p>When a workspace uses AI-assisted checks, the text being checked and the relevant brand rules are sent to the configured AI provider ([Groq / Anthropic / OpenAI / Google: list the ones you enable]). We send only what a check needs. [Confirm each provider&apos;s terms say it does not train on API data.] The rule-based checks run on our own servers and send nothing out.</p>

      <h2>Who we share it with</h2>
      <table><tbody>
        <tr><td><b>Hosting</b></td><td>[Render, region]: runs the application.</td></tr>
        <tr><td><b>Database</b></td><td>[Neon, region]: stores workspace data.</td></tr>
        <tr><td><b>AI providers</b></td><td>As above, only when AI checks are on.</td></tr>
        <tr><td><b>Email</b></td><td>[Your SMTP provider]: invitations and notifications.</td></tr>
        <tr><td><b>Error tracking</b></td><td>[Sentry, if enabled]: error reports without passwords or content.</td></tr>
      </tbody></table>
      <p>We do not sell personal data.</p>

      <h2>How long we keep it</h2>
      <p>Workspace data is kept while the customer&apos;s account is active. A workspace administrator can delete the whole workspace at any time in Settings → Data &amp; privacy; this removes its records immediately. Backups are kept for [30] days and then deleted. Security records are kept for [12 months].</p>

      <h2>Your rights</h2>
      <p>You can ask to see, correct, export or delete your personal data, and object to or restrict its use. In the app: administrators can download the workspace&apos;s data and delete the workspace; every user can close their own account in Settings → Data &amp; privacy. For anything else, write to [privacy@yourcompany.com]. You can also complain to your data protection authority ([e.g. the Data Protection Board of India / your EU supervisory authority]).</p>

      <h2>International transfers</h2>
      <p>[State where data is stored and, for transfers out of the EU/UK or India, the safeguard used, such as Standard Contractual Clauses.]</p>

      <h2>Changes</h2>
      <p>We will post changes here and tell workspace administrators by email before material changes take effect.</p>
    </LegalPage>
  );
}
