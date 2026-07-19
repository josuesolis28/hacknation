import { useEffect, useState } from "react";
import { runMaschmeyerScout } from "./api";
import type { PipelineResult } from "./types";
import { FounderCard } from "./components/FounderCard";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runAutomaticScout = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await runMaschmeyerScout());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void runAutomaticScout();
  }, []);

  const approved = result?.founders.filter((f) => f.decision === "approved") ?? [];

  return (
    <div className="app">
      <div className="header">
        <h1>
          🧠 The VC Brain <span className="brand">· Maschmeyer Group</span>
        </h1>
      </div>
      <p className="tagline">
        Aprobación instantánea de founders pre-seed — Scout → Judge → Score →
        Cheque automático de $100,000 USD
      </p>

      <p className="hint">
        Búsqueda automática: B2B SaaS, FinTech, InsurTech, HealthTech, RegTech,
        ciberseguridad y New Work en Estados Unidos, Europa y Latinoamérica.
        Rastrea aceleradoras, demo days, Product Hunt, F6S y comunidades del ecosistema.
      </p>

      {loading && (
        <div className="status info">
          <span className="spinner" />
          Rastreando la web y evaluando fundadores contra la rúbrica del fondo…
        </div>
      )}

      {error && <div className="status error">Error: {error}</div>}

      {result?.errors.map((e, i) => (
        <div className="status error" key={i}>{e}</div>
      ))}

      {result && result.founders.length > 0 && (
        <>
          <div className="status ok">
            {result.founders.length} candidatos evaluados sobre{" "}
            {result.raw_hits.length} fuentes · {approved.length} aprobados con
            cheque emitido · motor: {result.provider_used}
          </div>
          {result.founders.map((f) => (
            <FounderCard key={`${f.name}-${f.company}`} founder={f} />
          ))}
        </>
      )}

      {result && result.founders.length === 0 && result.errors.length === 0 && (
        <div className="status info">
          No se identificaron fundadores con evidencia suficiente en esta ejecución.
        </div>
      )}

      {result && result.raw_hits.length > 0 && (
        <details className="sources">
          <summary>🔍 Fuentes analizadas ({result.raw_hits.length})</summary>
          {result.raw_hits.map((h) => (
            <a key={h.url} href={h.url} target="_blank" rel="noreferrer">
              {h.title || h.url} · relevancia {h.score.toFixed(2)}
            </a>
          ))}
        </details>
      )}
    </div>
  );
}
