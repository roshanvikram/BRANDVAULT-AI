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
    <html lang="en">
      <body className="bg-[#FAFAFA] text-[#0A0A0A] min-h-screen flex antialiased selection:bg-[#0A0A0A] selection:text-white">
        <Sidebar />
        <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
          <Header />
          <main className="flex-1 p-6 lg:p-7 max-w-[1600px] w-full mx-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
