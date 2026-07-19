import type { FounderProfile } from "../types";
import { Language, copy } from "../i18n";
import { useTranslatedFounder } from "../hooks/useTranslatedFounder";

export function StartupMetrics({ founder, language }: { founder: FounderProfile | null; language: Language }) {
  const text = copy[language];
  const translated = useTranslatedFounder(founder, language);
  if (!founder) {
    return (
      <section className="startup-metrics empty">
        <div>
          <h2>{text.metricsTitle}</h2>
          <p>{text.metricsEmpty}</p>
        </div>
      </section>
    );
  }

  const email = founder.business_email || founder.contact_hint || text.noPublicData;
  const section = founder.section || founder.area || text.noPublicData;
  const round = founder.round_size || founder.capital_raised || text.noPublicData;
  const activity = translated?.activity_summary || translated?.justification || text.noPublicData;
  const pitch = translated?.pitch || text.noPublicData;
  const other = translated?.other_info || translated?.impact_summary || "";

  return (
    <section className="startup-metrics">
      <div className="metrics-head">
        <div>
          <h2>{founder.company}</h2>
          <p>
            {text.origin}: {founder.country || founder.country_code || "DACH"}
            {founder.section ? ` · ${founder.section}` : ""}
          </p>
        </div>
      </div>
      <div className="metrics-board intake-board">
        <article>
          <span>{text.companyName}</span>
          <strong>{founder.company}</strong>
          <small>{founder.name}{founder.role ? ` · ${founder.role}` : ""}</small>
        </article>
        <article>
          <span>{text.businessEmail}</span>
          <strong className="email-value">{email}</strong>
          <small>{text.publicSourcesOnly}</small>
        </article>
        <article>
          <span>{text.origin}</span>
          <strong>{founder.country || founder.country_code || "DACH"}</strong>
          <small>Germany · Switzerland · Austria</small>
        </article>
        <article>
          <span>{text.sectionLabel}</span>
          <strong>{section}</strong>
          <small>{text.sectionHint}</small>
        </article>
        <article className="span-2">
          <span>{text.activityLabel}</span>
          <strong className="prose">{activity}</strong>
        </article>
        <article>
          <span>{text.roundSize}</span>
          <strong>{round}</strong>
          <small>{text.roundHint}</small>
        </article>
        <article className="span-2">
          <span>{text.pitchLabel}</span>
          <strong className="prose">{pitch}</strong>
          {other ? <small>{text.otherInfo}: {other}</small> : <small>{text.otherInfoHint}</small>}
        </article>
      </div>

      <div className="capital-section">
        <span className="eyebrow">{text.capitalTitle}</span>
        <div className="capital-board">
          <article className="capital-tile">
            <span>{text.totalCapitalLabel}</span>
            <strong>{founder.total_capital || founder.capital_raised || text.noPublicData}</strong>
            <small>{text.publicSourcesOnly}</small>
          </article>
          <article className="capital-tile">
            <span>{text.revenueLabel}</span>
            <strong>{founder.revenue_signal || text.revenueEmpty}</strong>
            <small>{text.publicSourcesOnly}</small>
          </article>
          <article className="capital-tile">
            <span>{text.businessModel}</span>
            <strong>{founder.business_model && founder.business_model !== "unknown" ? founder.business_model : text.unknownModel}</strong>
            <small>{text.b2bB2cHint}</small>
          </article>
        </div>

        <h3 className="panel-subtitle">{text.fundingRoundsTitle}</h3>
        {founder.funding_rounds && founder.funding_rounds.length > 0 ? (
          <div className="funding-table">
            {founder.funding_rounds.map((round_, i) => (
              <div className="funding-row" key={`${round_.investor}-${i}`}>
                <strong>{round_.investor}</strong>
                <span>{round_.round_name || "—"}</span>
                <span>{round_.amount || "—"}</span>
                <span>{round_.date || "—"}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">{text.fundingRoundsEmpty}</p>
        )}

        <h3 className="panel-subtitle">{text.clientsTitle}</h3>
        {founder.clients && founder.clients.length > 0 ? (
          <div className="chips">
            {founder.clients.map((client) => (
              <span className="chip" key={client}>{client}</span>
            ))}
          </div>
        ) : (
          <p className="muted">{text.clientsEmpty}</p>
        )}
      </div>
    </section>
  );
}
