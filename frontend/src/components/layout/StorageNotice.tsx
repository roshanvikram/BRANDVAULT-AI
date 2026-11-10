"use client";

import { useEffect, useState } from "react";
import { DatabaseZap, X } from "lucide-react";
import { fetchCapabilities } from "@/lib/api";

/**
 * Tells people the truth when the server stores data on a temporary disk (SQLite on
 * free hosting): anything they add is wiped when the server restarts. Hidden once a
 * persistent database (PostgreSQL via DATABASE_URL) is connected.
 */
export function StorageNotice() {
  const [temporary, setTemporary] = useState(false);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    try { setHidden(sessionStorage.getItem("bv-storage-notice") === "hidden"); } catch { /* storage blocked */ }
    fetchCapabilities().then((c) => setTemporary(c.persistent_storage === false)).catch(() => {});
  }, []);

  if (!temporary || hidden) return null;
  return (
    <div role="status" className="mb-5 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/90 backdrop-blur px-4 py-3 text-[13px] text-amber-900">
      <DatabaseZap className="w-4 h-4 mt-0.5 shrink-0 text-amber-600" />
      <p className="flex-1 leading-relaxed">
        <span className="font-semibold">Temporary storage.</span> This server keeps data on a disk that resets when it restarts,
        so anything you add here (uploads, reviews, passports) can disappear. The demo data always comes back.
        An administrator can make it permanent by connecting a PostgreSQL database (<code className="text-[12px]">DATABASE_URL</code>).
      </p>
      <button aria-label="Hide this notice" className="p-1 rounded-lg hover:bg-amber-100"
        onClick={() => { setHidden(true); try { sessionStorage.setItem("bv-storage-notice", "hidden"); } catch { /* ignore */ } }}>
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
