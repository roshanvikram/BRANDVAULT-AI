import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "BRANDVAULT AI — Protect Every Word. Preserve Every Identity.",
  description: "Enterprise Agentic Brand Governance & Evidence Retrieval Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#F8FAFC] text-[#0F172A] min-h-screen antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

