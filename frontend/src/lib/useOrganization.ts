"use client";

import { useEffect, useState } from "react";
import { fetchWorkspaces, Organization } from "@/lib/api";
import { useAuth } from "@/lib/auth";

/** The signed-in user's organisation, as returned by the backend. */
export function useOrganization(): Organization | null {
  const { user } = useAuth();
  const [org, setOrg] = useState<Organization | null>(null);

  useEffect(() => {
    if (!user) {
      setOrg(null);
      return;
    }
    let cancelled = false;
    fetchWorkspaces()
      .then((orgs) => {
        if (!cancelled) setOrg(orgs.find((o) => o.id === user.org_id) || null);
      })
      .catch(() => !cancelled && setOrg(null));
    return () => {
      cancelled = true;
    };
  }, [user]);

  return org;
}
