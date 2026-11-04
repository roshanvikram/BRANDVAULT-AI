import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

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
    <html lang="en" className="dark">
      <body className="bg-[#0A0A0A] text-[#F5F5F5] min-h-screen flex">
        <Sidebar />
        <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
          <Header />
          <main className="flex-1 p-6 max-w-7xl w-full mx-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
