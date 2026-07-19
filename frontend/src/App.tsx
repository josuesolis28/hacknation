import { useEffect, useState } from "react";
import {
  DecisionState,
  clearAccessToken,
  decisionKey,
  fetchHealth,
  getDecisions,
  getLatestScan,
  hasAccessToken,
  runMaschmeyerScout,
  setDecision,
} from "./api";
import { AnalysisPhases, Stage } from "./components/AnalysisPhases";
import { FounderCard } from "./components/FounderCard";
import { Login } from "./components/Login";
import { PitchPanel } from "./components/PitchPanel";
import { Language, copy, loadLanguage, saveLanguage } from "./i18n";
import type { FounderProfile, PipelineResult } from "./types";

function Workspace() {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [stage, setStage] = useState<Stage>("initializing");
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<Language>(() => loadLanguage("en"));
  const [selected, setSelected] = useState<FounderProfile | null>(null);
  const [decisions, setDecisions] = useState<Record<string, DecisionState>>({});
  const text = copy[language];

  const updateDecision = (company: string, name: string, state: DecisionState) => {
    const key = decisionKey(company, name);
    setDecisions((prev) => {
      const next = { ...prev };
      if (state === "clear") delete next[key];
      else next[key] = state;
      return next;
    });
    void setDecision(company, name, state);
  };

  useEffect(() => {
    saveLanguage(language);
  }, [language]);

  useEffect(() => {
    void fetchHealth()
      .then((health) => {
        if (
          !localStorage.getItem("vcbrain_language") &&
          (health.default_language === "en" || health.default_language === "es" || health.default_language === "de")
        ) {
          setLanguage(health.default_language);
        }
      })
      .catch(() => undefined);
  }, []);

  const rescan = async () => {
    setError(null);
    setStage("detecting");
    const timer1 = window.setTimeout(() => setStage("analyzing_ux"), 750);
    const timer2 = window.setTimeout(() => setStage("validating"), 1600);
    try {
      const pipeline = await runMaschmeyerScout();
      setResult(pipeline);
      setSelected(pipeline.founders[0] ?? null);
      setStage("complete");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      window.clearTimeout(timer1);
      window.clearTimeout(timer2);
    }
  };

  useEffect(() => {
    void getDecisions()
      .then(({ decisions }) => setDecisions(decisions))
      .catch(() => undefined);

    const run = async () => {
      // Reusa el último escaneo guardado si existe — evita repetir una
      // corrida completa (y su costo) solo por refrescar el navegador.
      try {
        const { result: cached } = await getLatestScan();
        if (cached && cached.founders.length > 0) {
          setResult(cached);
          setSelected(cached.founders[0] ?? null);
          setStage("complete");
          return;
        }
      } catch {
        /* si falla, sigue con un escaneo nuevo */
      }
      await rescan();
    };
    void run();
  }, []);

  const statusLabel =
    stage === "complete"
      ? text.complete
      : stage === "validating"
        ? text.validatingSignals
        : stage === "analyzing_ux"
          ? text.phaseUx
          : text.scanning;
  const total = result?.raw_hits.length ?? 0;
  const candidates = result?.founders.length ?? 0;
  const approved = result?.founders.filter((f) => f.decision === "approved").length ?? 0;

  return (
    <main className="workspace">
      <header className="topbar">
        <div>
          <span className="eyebrow">MASCHMEYER GROUP · B2B PRIVATE INTELLIGENCE</span>
          <h1>{text.title}</h1>
          <p>{text.subtitle}</p>
        </div>
        <div className="top-actions">
          <select value={language} onChange={(e) => setLanguage(e.target.value as Language)} aria-label="Language">
            <option value="en">EN</option>
            <option value="es">ES</option>
            <option value="de">DE</option>
          </select>
          <button className="ghost" onClick={() => void rescan()} disabled={stage !== "complete"}>
            {text.rescan}
          </button>
          <button
            className="ghost"
            onClick={() => {
              clearAccessToken();
              window.location.reload();
            }}
          >
            {text.logout}
          </button>
        </div>
      </header>

      <section className={`run-status ${stage}`}>
        <div className="pulse" />
        <div>
          <strong>{statusLabel}</strong>
          <p>
            {text.scope} · HealthTech · FinTech · Food & AgTech · Logistics · HR Tech · LegalTech · Retail · EdTech ·
            CleanTech · PropTech · Cybersecurity
          </p>
        </div>
      </section>

      <AnalysisPhases stage={stage} language={language} />

      <section className="metrics">
        <article>
          <span>{text.detected}</span>
          <strong>{total}</strong>
          <small>{stage === "complete" ? text.analyzed : text.collecting}</small>
        </article>
        <article>
          <span>{text.validating}</span>
          <strong>{stage === "complete" ? candidates : Math.max(0, Math.round(total * 0.35))}</strong>
          <small>{text.founderSignals}</small>
        </article>
        <article>
          <span>{text.validated}</span>
          <strong>{approved}</strong>
          <small>
            {text.gatesMet}
            {result?.founders.filter((f) => f.country_code === "DE" || f.country_code === "CH" || f.country_code === "AT").length
              ? ` · DACH`
              : ""}
          </small>
        </article>
      </section>

      {error && <div className="status error">{error}</div>}
      {result?.errors.map((item) => (
        <div className="status error" key={item}>
          {item}
        </div>
      ))}

      <div className="analysis-grid">
        <section className="candidate-list">
          <div className="section-heading">
            <div>
              <span className="eyebrow">{text.dealFlow}</span>
              <h2>{text.founders}</h2>
            </div>
            <span>
              {candidates} {text.profiles}
            </span>
          </div>
          {stage !== "complete" && (
            <div className="loading-state">
              <span className="spinner" /> {text.analyzing}
            </div>
          )}
          <div className="startup-grid">
            {result?.founders.map((founder) => (
              <FounderCard
                key={`${founder.name}-${founder.company}`}
                founder={founder}
                language={language}
                selected={selected?.name === founder.name && selected?.company === founder.company}
                onSelect={() => setSelected(founder)}
                initialDecision={decisions[decisionKey(founder.company, founder.name)]}
                onDecisionChange={updateDecision}
              />
            ))}
          </div>
        </section>
        <PitchPanel founder={selected} language={language} />
      </div>
    </main>
  );
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(hasAccessToken());
  return authenticated ? <Workspace /> : <Login onSuccess={() => setAuthenticated(true)} />;
}
