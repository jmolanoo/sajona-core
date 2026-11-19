import React, { useState } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { AppShell, type CoreRouteId } from "./components/AppShell";
import { LotTraceModal } from "./components/LotTraceModal";
import { SyncCenterModal } from "./components/SyncCenterModal";
import { useEntityRecords } from "./db/useLocalData";
import type {
  ExtraccionMadre,
  LotePlantaMadre,
  Propagacion,
  RevisionBolsa,
  TransplanteBolsa,
  UnidadPlantaMadre,
  Variedad,
} from "./domain/types";
import { AdminCatalogosPage } from "./pages/AdminCatalogosPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { PlantaMadrePage } from "./pages/PlantaMadrePage";
import { PropagacionPage } from "./pages/PropagacionPage";
import { TransplanteBolsaPage } from "./pages/TransplanteBolsaPage";

const AuthenticatedApp: React.FC = () => {
  const [route, setRoute] = useState<CoreRouteId>("dashboard");
  const [syncOpen, setSyncOpen] = useState(false);
  const [traceLot, setTraceLot] = useState<Propagacion | null>(null);
  const [preselectedBolsaLote, setPreselectedBolsaLote] = useState<string | null>(null);

  const { rows: variedades } = useEntityRecords<Variedad>("variedades");
  const { rows: propagaciones } = useEntityRecords<Propagacion>("propagacion");
  const { rows: transplantes } = useEntityRecords<TransplanteBolsa>("transplante_bolsa");
  const { rows: revisiones } = useEntityRecords<RevisionBolsa>("revisiones_bolsa");
  const { rows: lotesMadre } = useEntityRecords<LotePlantaMadre>("lotes_planta_madre");
  const { rows: unidadesMadre } = useEntityRecords<UnidadPlantaMadre>("unidades_planta_madre");
  const { rows: extracciones } = useEntityRecords<ExtraccionMadre>("extracciones_madre");

  return (
    <AppShell activeRoute={route} onNavigate={setRoute} onOpenSync={() => setSyncOpen(true)}>
      {route === "dashboard" && (
        <DashboardPage onNavigate={setRoute} onInspectLot={(l) => setTraceLot(l)} />
      )}
      {route === "propagacion" && (
        <PropagacionPage
          onInspectLot={(l) => setTraceLot(l)}
          onSendToBolsa={(loteId) => {
            setPreselectedBolsaLote(loteId);
            setRoute("transplante_bolsa");
          }}
        />
      )}
      {route === "planta_madre" && <PlantaMadrePage />}
      {route === "transplante_bolsa" && (
        <TransplanteBolsaPage
          preselectedLoteId={preselectedBolsaLote}
          onClearPreselected={() => setPreselectedBolsaLote(null)}
        />
      )}
      {route === "admin_catalogos" && <AdminCatalogosPage />}

      <SyncCenterModal open={syncOpen} onClose={() => setSyncOpen(false)} />
      <LotTraceModal
        lote={traceLot}
        variedades={variedades}
        propagaciones={propagaciones}
        transplantes={transplantes}
        revisiones={revisiones}
        lotesMadre={lotesMadre}
        unidadesMadre={unidadesMadre}
        extracciones={extracciones}
        onClose={() => setTraceLot(null)}
      />
    </AppShell>
  );
};

const RootGate: React.FC = () => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white text-sm font-semibold">
        Cargando SAJONA Núcleo PWA...
      </div>
    );
  }
  return user ? <AuthenticatedApp /> : <LoginPage />;
};

export const App: React.FC = () => (
  <AuthProvider>
    <RootGate />
  </AuthProvider>
);

export default App;
