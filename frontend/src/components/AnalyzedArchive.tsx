import { useEffect, useState } from "react";
import { CompanyRecord, getCompanies } from "../api";
import { Language, copy, trafficLabel } from "../i18n";

export function AnalyzedArchive({ language }: { language: Language }) {
  const text = copy[language];
  const [open, setOpen] = useState(false);
  const [companies, setCompanies] = useState<CompanyRecord[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || companies !== null) return;
    setLoading(true);
    void getCompanies()
      .then(({ companies }) => setCompanies(companies))
      .catch(() => setCompanies([]))
      .finally(() => setLoading(false));
  }, [open, companies]);

  return (
    <section className="archive-board">
      <button className="archive-toggle" onClick={() => setOpen((v) => !v)}>
        <span>
          <span className="eyebrow">{text.archiveEyebrow}</span>
          <h2>{text.archiveTitle}</h2>
        </span>
        <span className="chev">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="archive-body">
          {loading && (
            <div className="loading-state">
              <span className="spinner" /> {text.archiveLoading}
            </div>
          )}
          {!loading && companies && companies.length === 0 && <p className="muted">{text.archiveEmpty}</p>}
          {!loading && companies && companies.length > 0 && (
            <div className="archive-grid">
              {companies.map(({ founder, last_seen, times_seen }) => {
                const light = founder.traffic_light || "red";
                return (
                  <article className="ticket-card" key={`${founder.company}-${founder.name}`}>
                    <div className="ticket-card-head">
                      <strong>{founder.company}</strong>
                      <span className={`traffic-light traffic-${light}`}>
                        <span className="traffic-dot" />
                        {trafficLabel(light, language)}
                      </span>
                    </div>
                    <p className="ticket-card-sub">
                      {founder.name}
                      {founder.role ? ` · ${founder.role}` : ""} · {founder.founder_score}/100
                    </p>
                    <p className="archive-meta">
                      {text.archiveSeenTimes.replace("{n}", String(times_seen))} ·{" "}
                      {new Date(last_seen).toLocaleDateString(language)}
                    </p>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
