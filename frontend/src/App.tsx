import { useEffect, useState } from "react";
import {
  DecisionState,
  TicketStatus,
  clearAccessToken,
  decisionKey,
  fetchHealth,
  getAllSubmissions,
  getDecisions,
  getLatestScan,
  getTickets,
  hasAccessToken,
  runMaschmeyerScout,
  setDecision,
  setTicketStatus,
} from "./api";
import { AnalysisPhases, Stage } from "./components/AnalysisPhases";
import { AnalyzedArchive } from "./components/AnalyzedArchive";
import { FounderCard } from "./components/FounderCard";
import { Login } from "./components/Login";
import { MySubmissions } from "./components/MySubmissions";
import { RoleChooser } from "./components/RoleChooser";
import { SubmitStartup } from "./components/SubmitStartup";
import { TicketsBoard } from "./components/TicketsBoard";
import { Language, copy, loadLanguage, saveLanguage } from "./i18n";
import { Role, clearRole, loadRole, saveRole } from "./role";
import type { FounderProfile, PipelineResult } from "./types";

function InvestorWorkspace({ language, setLanguage, onSwitchRole }: {
  language: Language;
  setLanguage: (l: Language) => void;
  onSwitchRole: () => void;
}) {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [stage, setStage] = useState<Stage>("initializing");
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<FounderProfile | null>(null);
  const [decisions, setDecisions] = useState<Record<string, DecisionState>>({});
  const [tickets, setTickets] = useState<Record<string, TicketStatus>>({});
  const [progress, setProgress] = useState(0);
  const [submissionFounders, setSubmissionFounders] = useState<FounderProfile[]>([]);
  const [view, setView] = useState<"scan" | "submissions">("scan");
  const text = copy[language];

  const reloadSubmissions = () => {
    void getAllSubmissions()
      .then(({ founders }) => setSubmissionFounders(founders))
      .catch(() => undefined);
  };

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

  const updateTicket = (company: string, name: string, status: TicketStatus) => {
    const key = decisionKey(company, name);
    setTickets((prev) => {
      const next = { ...prev };
      if (status === "clear") delete next[key];
      else next[key] = status;
      return next;
    });
    void setTicketStatus(company, name, status);
  };

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Barra de progreso simulada: el backend hace una sola llamada bloqueante
  // (no reporta % real de avance), así que se aproxima con una curva
  // asintótica que se acerca a ~92% mientras dura el escaneo y salta a 100%
  // en cuanto el resultado llega — da retroalimentación continua en vez de
  // dejar al usuario viendo un stepper estático varios segundos.
  useEffect(() => {
    if (stage === "complete") {
      setProgress(100);
      return;
    }
    if (stage === "initializing") return;
    const id = window.setInterval(() => {
      setProgress((p) => (p >= 92 ? p : p + (92 - p) * 0.06));
    }, 220);
    return () => window.clearInterval(id);
  }, [stage]);

  const rescan = async () => {
    setError(null);
    setProgress(0);
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
    void getTickets()
      .then(({ tickets }) => setTickets(tickets))
      .catch(() => undefined);
    reloadSubmissions();

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
          <button className="ghost" onClick={onSwitchRole}>
            {text.switchRole}
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

      <div className="view-tabs">
        <button className={view === "scan" ? "active" : ""} onClick={() => setView("scan")}>
          {text.tabScan}
        </button>
        <button className={view === "submissions" ? "active" : ""} onClick={() => setView("submissions")}>
          {text.tabSubmissionsReceived} {submissionFounders.length > 0 ? `(${submissionFounders.length})` : ""}
        </button>
      </div>

      {view === "scan" && (
        <>
          <AnalysisPhases stage={stage} language={language} progress={progress} />

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

          <div className="section-divider" />

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
                  ticketStatus={tickets[decisionKey(founder.company, founder.name)]}
                  onTicketChange={updateTicket}
                />
              ))}
            </div>
          </section>

          <TicketsBoard
            founders={result?.founders ?? []}
            tickets={tickets}
            language={language}
            onTicketChange={updateTicket}
          />

          <AnalyzedArchive language={language} />
        </>
      )}

      {view === "submissions" && (
        <section className="candidate-list">
          <div className="section-heading">
            <div>
              <span className="eyebrow">{text.adminSubmissionsEyebrow}</span>
              <h2>{text.adminSubmissionsTitle}</h2>
            </div>
            <span>
              {submissionFounders.length} {text.profiles}
            </span>
          </div>
          {submissionFounders.length === 0 ? (
            <p className="muted">{text.mySubmissionsEmpty}</p>
          ) : (
            <div className="startup-grid">
              {submissionFounders.map((founder) => (
                <FounderCard
                  key={`sub-${founder.name}-${founder.company}`}
                  founder={founder}
                  language={language}
                  selected={selected?.name === founder.name && selected?.company === founder.company}
                  onSelect={() => setSelected(founder)}
                  initialDecision={decisions[decisionKey(founder.company, founder.name)]}
                  onDecisionChange={updateDecision}
                  ticketStatus={tickets[decisionKey(founder.company, founder.name)]}
                  onTicketChange={updateTicket}
                />
              ))}
            </div>
          )}
        </section>
      )}

      <footer className="app-footer">{text.poweredBy}</footer>
    </main>
  );
}

function StartupWorkspace({ language, setLanguage, onSwitchRole }: {
  language: Language;
  setLanguage: (l: Language) => void;
  onSwitchRole: () => void;
}) {
  const text = copy[language];
  const [view, setView] = useState<"submit" | "mine">("submit");
  const [refreshKey, setRefreshKey] = useState(0);

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
          <button className="ghost" onClick={onSwitchRole}>
            {text.switchRole}
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

      <div className="view-tabs">
        <button className={view === "submit" ? "active" : ""} onClick={() => setView("submit")}>
          {text.submitStartupBtn}
        </button>
        <button
          className={view === "mine" ? "active" : ""}
          onClick={() => {
            setView("mine");
            setRefreshKey((k) => k + 1);
          }}
        >
          {text.mySubmissionsBtn}
        </button>
      </div>

      {view === "submit" && <SubmitStartup language={language} onClose={() => setView("mine")} inline />}
      {view === "mine" && <MySubmissions key={refreshKey} language={language} onClose={() => setView("submit")} inline />}

      <footer className="app-footer">{text.poweredBy}</footer>
    </main>
  );
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(hasAccessToken());
  const [role, setRole] = useState<Role | null>(() => loadRole());
  const [language, setLanguage] = useState<Language>(() => loadLanguage("en"));

  useEffect(() => {
    saveLanguage(language);
  }, [language]);

  if (!authenticated) return <Login onSuccess={() => setAuthenticated(true)} />;

  if (!role) {
    return (
      <RoleChooser
        language={language}
        onChoose={(r) => {
          saveRole(r);
          setRole(r);
        }}
      />
    );
  }

  const onSwitchRole = () => {
    clearRole();
    setRole(null);
  };

  return role === "investor" ? (
    <InvestorWorkspace language={language} setLanguage={setLanguage} onSwitchRole={onSwitchRole} />
  ) : (
    <StartupWorkspace language={language} setLanguage={setLanguage} onSwitchRole={onSwitchRole} />
  );
}
