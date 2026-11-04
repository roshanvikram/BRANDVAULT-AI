"use client";

import { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { AuthProvider, RequireAuth } from "@/lib/auth";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

// Public routes render full-page without the app chrome.
const PUBLIC_ROUTES = ["/", "/login", "/signup"];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.includes(pathname);

  return (
    <AuthProvider>
      {isPublic ? (
        children
      ) : (
        <div className="flex min-h-screen w-full">
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
