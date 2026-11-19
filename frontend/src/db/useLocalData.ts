import { useCallback, useEffect, useState } from "react";
import type { CoreEntityType } from "../domain/types";
import { db } from "./schema";
import { getSyncSnapshot, subscribeSync, type SyncStatusSnapshot } from "./syncEngine";

export function useOnlineStatus(): boolean {
  const [online, setOnline] = useState<boolean>(
    typeof navigator !== "undefined" ? navigator.onLine : true
  );

  useEffect(() => {
    const onUp = () => setOnline(true);
    const onDown = () => setOnline(false);
    window.addEventListener("online", onUp);
    window.addEventListener("offline", onDown);
    return () => {
      window.removeEventListener("online", onUp);
      window.removeEventListener("offline", onDown);
    };
  }, []);

  return online;
}

export function useSyncStatus(): SyncStatusSnapshot {
  const [snap, setSnap] = useState<SyncStatusSnapshot>({
    pendingCount: 0,
    conflictCount: 0,
    rejectedCount: 0,
    lastSyncAt: null,
    syncing: false,
    lastError: null,
  });

  const refresh = useCallback(async () => {
    setSnap(await getSyncSnapshot());
  }, []);

  useEffect(() => {
    void refresh();
    return subscribeSync(() => {
      void refresh();
    });
  }, [refresh]);

  return snap;
}

export function useEntityRecords<T extends { deleted_at?: string | null }>(
  entityType: CoreEntityType
): { rows: T[]; loading: boolean; reload: () => Promise<void> } {
  const [rows, setRows] = useState<T[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const reload = useCallback(async () => {
    const all = (await db.tableFor(entityType).toArray()) as T[];
    setRows(all.filter((r) => !r.deleted_at));
    setLoading(false);
  }, [entityType]);

  useEffect(() => {
    void reload();
    return subscribeSync(() => {
      void reload();
    });
  }, [reload]);

  return { rows, loading, reload };
}
