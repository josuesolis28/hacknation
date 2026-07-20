import { TicketNote, TicketStatus } from "../api";
import { useTranslatedFounder } from "../hooks/useTranslatedFounder";
import { Language, copy, trafficLabel } from "../i18n";
import type { FounderProfile } from "../types";

function TicketCard({
  founder,
  status,
  note,
  language,
  onMove,
}: {
  founder: FounderProfile;
  status: TicketStatus;
  note?: TicketNote;
  language: Language;
  onMove: (status: TicketStatus) => void;
}) {
  const text = copy[language];
  const translated = useTranslatedFounder(founder, language);
  const light = founder.traffic_light || "red";

  return (
    <article className={`ticket-card ticket-${status}`}>
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

      {status === "approved" && founder.check && (
        <p className="ticket-check-line">
          ${founder.check.amount_usd.toLocaleString("en-US")} USD · Nº {founder.check.check_id}
        </p>
      )}

      {status === "rejected" && note ? (
        <p className="ticket-note">{note.note}</p>
      ) : (
        <>
          {(translated?.feedback.length ?? 0) > 0 && (
            <ul className="ticket-feedback">
              {translated?.feedback.slice(0, 2).map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          )}
          {!(translated?.feedback.length ?? 0) && translated?.justification && (
            <p className="ticket-justification">{translated.justification}</p>
          )}
        </>
      )}

      <div className="ticket-actions">
        <button className="ghost" onClick={() => onMove("clear")}>
          {text.removeFromTickets}
        </button>
      </div>
    </article>
  );
}

const COLUMNS: { status: TicketStatus; titleKey: "ticketsApproved" | "ticketsRejected" }[] = [
  { status: "approved", titleKey: "ticketsApproved" },
  { status: "rejected", titleKey: "ticketsRejected" },
];

export function TicketsBoard({
  founders,
  tickets,
  notes,
  language,
  onTicketChange,
}: {
  founders: FounderProfile[];
  tickets: Record<string, string>;
  notes: Record<string, TicketNote>;
  language: Language;
  onTicketChange: (company: string, name: string, status: TicketStatus) => void;
}) {
  const text = copy[language];
  const byKey = (f: FounderProfile) => `${f.company.trim().toLowerCase()}|${f.name.trim().toLowerCase()}`;
  const withTickets = founders
    .map((f) => ({ founder: f, status: tickets[byKey(f)] as TicketStatus | undefined }))
    .filter((x): x is { founder: FounderProfile; status: TicketStatus } => Boolean(x.status));

  if (withTickets.length === 0) return null;

  return (
    <section className="tickets-board">
      <div className="section-heading">
        <div>
          <span className="eyebrow">{text.ticketsEyebrow}</span>
          <h2>{text.ticketsTitle}</h2>
        </div>
      </div>
      <div className="tickets-columns">
        {COLUMNS.map((col) => {
          const items = withTickets.filter((x) => x.status === col.status);
          return (
            <div className="tickets-column" key={col.status}>
              <h3>
                {text[col.titleKey]} <span className="tickets-count">{items.length}</span>
              </h3>
              {items.length === 0 ? (
                <p className="muted">{text.ticketsEmpty}</p>
              ) : (
                items.map(({ founder }) => (
                  <TicketCard
                    key={byKey(founder)}
                    founder={founder}
                    status={col.status}
                    note={notes[byKey(founder)]}
                    language={language}
                    onMove={(status) => onTicketChange(founder.company, founder.name, status)}
                  />
                ))
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
