import { LegalPage } from "@/components/legal/LegalLinks";

export const metadata = { title: "Terms of Service · BrandVault AI" };

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service" updated="10 November 2026">
      <p>These terms are an agreement between [Your company name] and the organisation that creates a BrandVault workspace (&ldquo;you&rdquo;). The person who signs up confirms they may accept them for that organisation.</p>

      <h2>The service</h2>
      <p>BrandVault checks marketing content against the brand rules, facts and guidelines you provide, and records reviews and approvals. Checks are aids to human review. <b>You remain responsible for what you publish.</b> Approvals in BrandVault are made by your own reviewers.</p>

      <h2>Accounts</h2>
      <ul>
        <li>Keep sign-in details private. Administrators control who joins the workspace and with which role.</li>
        <li>Tell us promptly at [security@yourcompany.com] about any suspected unauthorised access.</li>
      </ul>

      <h2>Your content</h2>
      <p>You own the content you upload. You give us permission to store and process it only to provide the service to you. You confirm you have the right to upload it.</p>

      <h2>Acceptable use</h2>
      <p>Do not use the service to break the law, to upload malware, to probe or overload it, or to access another customer&apos;s data. We may suspend accounts that do.</p>

      <h2>Fees</h2>
      <p>[Plans, prices, billing period, taxes and renewal terms. Remove this section for free pilots.]</p>

      <h2>Availability and support</h2>
      <p>[Target availability, e.g. 99.5% monthly, maintenance windows, support hours and response times.] Free or trial workspaces have no availability commitment.</p>

      <h2>Ending the agreement</h2>
      <p>You can stop at any time and delete your workspace in Settings → Data &amp; privacy. Download an export first if you need your data; deletion cannot be undone. [Notice period and refund terms for paid plans.]</p>

      <h2>Liability</h2>
      <p>[Warranty disclaimer, limitation of liability and indemnities: have your lawyer draft these for your market.]</p>

      <h2>Governing law</h2>
      <p>[Country and courts.]</p>

      <h2>Contact</h2>
      <p>[legal@yourcompany.com], [postal address].</p>
    </LegalPage>
  );
}
