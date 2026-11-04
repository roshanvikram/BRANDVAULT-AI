"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { AuthUser, fetchCurrentUser, login as apiLogin, clearToken } from "@/lib/api";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      setUser(await fetchCurrentUser());
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    (async () => {
      await refresh();
      setLoading(false);
    })();
  }, []);

  const login = async (email: string, password: string) => {
    const u = await apiLogin(email, password);
    setUser(u);
    return u;
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

export function initials(name: string | undefined): string {
  if (!name) return "··";
  const parts = name.trim().split(/\s+/);
  return (parts[0]?.[0] || "") + (parts.length > 1 ? parts[parts.length - 1][0] : "");
}

/** Gate for authenticated app routes — redirects to /login when signed out. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center text-[#737373]">
        <ShieldCheck className="w-8 h-8 mb-3 text-[#A3A3A3] animate-pulse" />
        <p className="text-xs font-mono">Verifying session…</p>
      </div>
    );
  }
  if (!user) return null;
  return <>{children}</>;
}
