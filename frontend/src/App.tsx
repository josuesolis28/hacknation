import { useEffect, useState } from "react";
import { analyzeProfiles, clearAccessToken, fetchHealth, hasAccessToken, runMaschmeyerScout } from "./api";
import { FounderCard } from "./components/FounderCard";
import { Login } from "./components/Login";
import { ProfileNetworkView } from "./components/ProfileNetwork";
import { StartupMetrics } from "./components/StartupMetrics";
import { Language, copy, loadLanguage, saveLanguage } from "./i18n";
import type { FounderProfile, PipelineResult, ProfileNetwork } from "./types";

type Stage = "initializing" | "detecting" | "validating" | "complete";

function Workspace() {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [stage, setStage] = useState<Stage>("initializing");
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<Language>(() => loadLanguage("en"));
  const [selected, setSelected] = useState<FounderProfile | null>(null);
  const [network, setNetwork] = useState<ProfileNetwork | null>(null);
  const [networkLoading, setNetworkLoading] = useState(false);
  const [networkError, setNetworkError] = useState<string | null>(null);
  const text = copy[language];

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

  useEffect(() => {
    const run = async () => {
      setStage("detecting");
      const timer = window.setTimeout(() => setStage("validating"), 850);
      try {
        const pipeline = await runMaschmeyerScout();
        setResult(pipeline);
        setSelected(pipeline.founders[0] ?? null);
        setStage("complete");
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        window.clearTimeout(timer);
      }
    };
    void run();
  }, []);

  const inspect = async (founder: FounderProfile) => {
    setSelected(founder);
    setNetworkLoading(true);
    setNetworkError(null);
    setNetwork(null);
    try {
      setNetwork(await analyzeProfiles(founder));
    } catch (e) {
      setNetworkError(e instanceof Error ? e.message : String(e));
    } finally {
      setNetworkLoading(false);
    }
  };

  const statusLabel =
    stage === "complete" ? text.complete : stage === "validating" ? text.validatingSignals : text.scanning;
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
          {result?.founders.map((founder) => (
            <FounderCard
              key={`${founder.name}-${founder.company}`}
              founder={founder}
              language={language}
              selected={selected?.name === founder.name && selected?.company === founder.company}
              onSelect={() => setSelected(founder)}
              onAnalyze={() => void inspect(founder)}
            />
          ))}
        </section>
        <ProfileNetworkView
          founder={selected}
          network={network}
          loading={networkLoading}
          error={networkError}
          language={language}
        />
      </div>

      <StartupMetrics founder={selected} language={language} />
    </main>
  );
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(hasAccessToken());
  return authenticated ? <Workspace /> : <Login onSuccess={() => setAuthenticated(true)} />;
}
