import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

// Brief allows Inter as the primary sans; mono for technical identifiers.
// Variable names kept as --font-geist-* so globals.css / tailwind are unchanged.
const geistSans = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = JetBrains_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

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
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body className="bg-[#F7F7F7] text-[#0A0A0A] min-h-screen antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
