import React, { useState } from "react";
import {
  LayoutDashboard,
  LogOut,
  Menu,
  Package,
  RefreshCw,
  Settings,
  Sprout,
  Trees,
  Wifi,
  WifiOff,
  X,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useOnlineStatus, useSyncStatus } from "../db/useLocalData";

export type CoreRouteId =
  | "dashboard"
  | "propagacion"
  | "planta_madre"
  | "transplante_bolsa"
  | "admin_catalogos";

const CORE_NAV: Array<{
  id: CoreRouteId;
  label: string;
  shortLabel: string;
  icon: React.FC<{ className?: string }>;
}> = [
  { id: "dashboard", label: "Dashboard", shortLabel: "Inicio", icon: LayoutDashboard },
  { id: "propagacion", label: "Propagación", shortLabel: "Propag.", icon: Sprout },
  { id: "planta_madre", label: "Planta Madre", shortLabel: "Madres", icon: Trees },
  { id: "transplante_bolsa", label: "Transplante Bolsa", shortLabel: "Bolsa", icon: Package },
];

export const AppShell: React.FC<{
  activeRoute: CoreRouteId;
  onNavigate: (r: CoreRouteId) => void;
  onOpenSync: () => void;
  children: React.ReactNode;
}> = ({ activeRoute, onNavigate, onOpenSync, children }) => {
  const { user, logout } = useAuth();
  const online = useOnlineStatus();
  const syncSnap = useSyncStatus();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const currentLabel =
    CORE_NAV.find((n) => n.id === activeRoute)?.label ||
    (activeRoute === "admin_catalogos" ? "Catálogos y Gobernanza" : "Dashboard");

  const statusText = !online
    ? "Sin conexión"
    : syncSnap.conflictCount > 0
      ? `${syncSnap.conflictCount} Conflicto`
      : syncSnap.pendingCount > 0
        ? `${syncSnap.pendingCount} Pend.`
        : syncSnap.syncing
          ? "Sincronizando"
          : "En línea";

  const statusClass = !online
    ? "bg-slate-900 text-amber-300"
    : syncSnap.conflictCount > 0
      ? "bg-red-950 text-red-200"
      : syncSnap.pendingCount > 0
        ? "bg-amber-600 text-white"
        : "bg-emerald-700 text-white";

  const go = (id: CoreRouteId) => {
    onNavigate(id);
    setDrawerOpen(false);
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-100">
      {/* Sidebar Desktop */}
      <aside className="hidden md:flex md:w-64 md:flex-col bg-slate-900 text-slate-100 shrink-0">
        <div className="bg-brand-800 px-5 py-4 border-b border-brand-900">
          <div className="flex items-center justify-between">
            <span className="font-extrabold text-lg tracking-wide text-white">SAJONA</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-brand-900 text-red-100">
              NÚCLEO PWA
            </span>
          </div>
          <p className="text-[11px] text-red-100 mt-0.5">Módulos 1–3 + Dashboard</p>
        </div>

        <nav className="flex-1 p-3 space-y-1.5" aria-label="Módulos principales">
          {CORE_NAV.map((item) => {
            const Icon = item.icon;
            const active = activeRoute === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => go(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition ${
                  active ? "bg-brand-700 text-white shadow" : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="p-3 border-t border-slate-800 space-y-2">
          {user?.role === "ADMIN" && (
            <button
              type="button"
              onClick={() => go("admin_catalogos")}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold ${
                activeRoute === "admin_catalogos"
                  ? "bg-slate-700 text-white"
                  : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              <Settings className="w-4 h-4" /> Catálogos y Usuarios
            </button>
          )}
          <div className="px-3 py-2 rounded-lg bg-slate-800/80 text-xs">
            <div className="font-bold text-white truncate">{user?.username}</div>
            <div className="text-[11px] text-emerald-400 font-semibold">{user?.role}</div>
          </div>
        </div>
      </aside>

      {/* Drawer Móvil */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div className="w-72 bg-slate-900 text-white flex flex-col h-full shadow-2xl">
            <div className="bg-brand-800 px-4 py-3 flex items-center justify-between">
              <div>
                <div className="font-bold text-base">SAJONA NÚCLEO</div>
                <div className="text-[11px] text-red-100">{user?.username} • {user?.role}</div>
              </div>
              <button type="button" onClick={() => setDrawerOpen(false)} aria-label="Cerrar menú">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-3 space-y-1.5 flex-1">
              {CORE_NAV.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => go(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold ${
                      activeRoute === item.id ? "bg-brand-700 text-white" : "text-slate-200"
                    }`}
                  >
                    <Icon className="w-4 h-4" /> {item.label}
                  </button>
                );
              })}
              {user?.role === "ADMIN" && (
                <button
                  type="button"
                  onClick={() => go("admin_catalogos")}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-slate-300"
                >
                  <Settings className="w-4 h-4" /> Catálogos y Usuarios
                </button>
              )}
            </div>
          </div>
          <div className="flex-1 bg-slate-950/60" onClick={() => setDrawerOpen(false)} />
        </div>
      )}

      {/* Contenido Principal */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 bg-brand-800 text-white shadow">
          <div className="flex items-center justify-between gap-2 px-3 sm:px-6 py-2.5">
            <div className="flex items-center gap-2 min-w-0">
              <button
                type="button"
                onClick={() => setDrawerOpen(true)}
                aria-label="Abrir menú"
                className="md:hidden p-2 rounded-lg hover:bg-brand-700"
              >
                <Menu className="w-5 h-5" />
              </button>
              <div className="min-w-0">
                <div className="text-sm sm:text-base font-extrabold truncate">SAJONA ADE</div>
                <div className="text-[11px] text-red-100 truncate">Inicio › {currentLabel}</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onOpenSync}
                aria-label="Estado de conexión y sincronización"
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold shadow ${statusClass}`}
              >
                {!online ? (
                  <WifiOff className="w-3.5 h-3.5" />
                ) : syncSnap.syncing ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Wifi className="w-3.5 h-3.5" />
                )}
                <span>{statusText}</span>
              </button>
              <button
                type="button"
                onClick={() => void logout()}
                aria-label="Cerrar sesión"
                className="p-2 rounded-lg hover:bg-brand-700"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>

          {!online && (
            <div className="bg-slate-900 text-amber-200 text-[11px] sm:text-xs font-medium px-4 py-1.5 text-center border-t border-slate-700">
              Modo Offline-First activo: los registros se guardan en IndexedDB y se sincronizarán al
              recuperar conectividad.
            </div>
          )}
        </header>

        <main className="flex-1 p-3 sm:p-6 pb-24 md:pb-8 max-w-7xl w-full mx-auto">
          {children}
        </main>

        {/* Bottom Navigation Móvil (exactamente los 4 módulos del sistema) */}
        <nav
          aria-label="Navegación inferior"
          className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-slate-200 grid grid-cols-4 shadow-lg"
        >
          {CORE_NAV.map((item) => {
            const Icon = item.icon;
            const active = activeRoute === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => go(item.id)}
                className={`flex flex-col items-center justify-center py-2 text-[11px] font-semibold ${
                  active ? "text-brand-800" : "text-slate-500"
                }`}
              >
                <Icon className="w-5 h-5 mb-0.5" />
                <span>{item.shortLabel}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};
