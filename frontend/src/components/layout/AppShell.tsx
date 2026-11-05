"use client";

import { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { AuthProvider, RequireAuth } from "@/lib/auth";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

// Public routes render full-page without the app chrome.
const PUBLIC_ROUTES = ["/", "/login", "/signup", "/guide"];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.includes(pathname);

  return (
    <AuthProvider>
      {isPublic ? (
        children
      ) : (
        <div className="flex min-h-screen w-full relative">
          {/* Monochrome "organic glass" background — subtle neutral blobs that
              give frosted cards their depth without introducing any colour. */}
          <div
            aria-hidden
            className="fixed inset-0 -z-10 pointer-events-none"
            style={{
              background:
                "radial-gradient(55% 48% at 14% 8%, rgba(10,10,10,0.05), transparent 70%)," +
                "radial-gradient(48% 42% at 88% 16%, rgba(10,10,10,0.04), transparent 70%)," +
                "radial-gradient(55% 50% at 78% 92%, rgba(10,10,10,0.045), transparent 70%)," +
                "radial-gradient(40% 40% at 40% 60%, rgba(255,255,255,0.7), transparent 70%)," +
                "linear-gradient(180deg,#F4F4F5,#ECECEE)",
            }}
          />
          <Sidebar />
          <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
            <Header />
            <main className="flex-1 p-6 lg:p-7 max-w-[1600px] w-full mx-auto">
              <RequireAuth>{children}</RequireAuth>
            </main>
          </div>
        </div>
      )}
    </AuthProvider>
  );
}
