import { useEffect, useState } from "react";
import type { Check, FounderProfile } from "../types";
import { DecisionState, generateOutreach } from "../api";
import { useTranslatedFounder } from "../hooks/useTranslatedFounder";
import {
  Language,
  confidenceLabel,
  copy,
  criterionLabel,
  originLabel,
  platformLabel,
  relationshipLabel,
  requirementLabel,
  trafficDescription,
  trafficLabel,
} from "../i18n";

function ApprovedCheckIcon() {
  return (
    <svg className="check-draw" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="22" cy="22" r="19" />
      <path d="M13 22.5L19 28.5L31 15.5" />
    </svg>
  );
}

function buildManualCheck(founder: FounderProfile): Check {
  return {
    check_id: `MGV-${new Date().getFullYear()}-${Math.random().toString(16).slice(2, 8).toUpperCase()}`,
    amount_usd: 100_000,
    issued_to: founder.name,
    company: founder.company,
    issued_by: "Maschmeyer Group Ventures",
    date: new Date().toISOString().slice(0, 10),
    status: "issued",
  };
}

function CheckModal({ check, language, onClose }: { check: Check; language: Language; onClose: () => void }) {
  const text = copy[language];
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="check-modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="check-modal-head">
          <ApprovedCheckIcon />
          <div>
            <strong>{text.checkGrantedTitle}</strong>
            <span>{text.instant}</span>
          </div>
          <button className="modal-close on-dark" onClick={onClose} aria-label={text.closeModal}>
            ✕
          </button>
        </div>
        <div className="check-modal-body">
          <div className="line" style={{ animationDelay: ".2s" }}>
            <span className="stamp">{text.issued}</span>
          </div>
          <div className="bank line" style={{ animationDelay: ".3s" }}>
            <span className="name">{check.issued_by}</span>
            <span className="id">Nº {check.check_id}</span>
          </div>
          <div className="amount">${check.amount_usd.toLocaleString("en-US")} USD</div>
          <p className="payto line" style={{ animationDelay: ".5s" }}>
            <span>{text.payTo}</span> {check.issued_to} · {check.company}
          </p>
          <div className="foot line" style={{ animationDelay: ".6s" }}>
            <span>
              {text.issueDate} {check.date}
            </span>
            <span>{text.instant}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function StartupModal({
  founder,
  language,
  forced,
  discarded,
  onClose,
  onGenerateCheck,
  onDiscard,
  onUndoDiscard,
}: {
  founder: FounderProfile;
  language: Language;
  forced: boolean;
  discarded: boolean;
  onClose: () => void;
  onGenerateCheck: () => void;
  onDiscard: () => void;
  onUndoDiscard: () => void;
}) {
  const [outreach, setOutreach] = useState<string | null>(null);
  const [loadingMsg, setLoadingMsg] = useState(false);
  const [msgError, setMsgError] = useState<string | null>(null);
  const translated = useTranslatedFounder(founder, language);
  const text = copy[language];
  const approved = founder.decision === "approved" || forced;
  const origin = originLabel(founder, language);
  const confidence = confidenceLabel(founder.origin_confidence, language);
  const skills = founder.skills?.length ? founder.skills : founder.signals.slice(0, 4);
  const area = founder.section || founder.area || founder.signals[0] || "—";
  const email = founder.business_email || founder.contact_hint || "—";
  const round = founder.round_size || founder.capital_raised || "—";
  const light = founder.traffic_light || "red";
  const lightLabel = trafficLabel(light, language);
  const lightDesc = trafficDescription(light, language);
  const team = founder.team?.length
    ? founder.team
    : founder.name
      ? [{ name: founder.name, role: founder.role || text.relFounder, relationship: "founder", skills: founder.skills || [], area: founder.area || founder.section || "", profile_url: "" }]
      : [];
  const business = founder.business_model && founder.business_model !== "unknown" ? founder.business_model : text.unknownModel;

  const onOutreach = async () => {
    setLoadingMsg(true);
    setMsgError(null);
    try {
      const { message } = await generateOutreach(founder);
      setOutreach(message);
    } catch (e) {
      setMsgError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingMsg(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-panel-head">
          <div className="score-badge">
            <span className="num">{founder.founder_score}</span>
            <span className="of">/ 100</span>
          </div>
          <div className="head-info">
            <h3>{founder.company}</h3>
            <p>
              {founder.name}
              {founder.role ? ` · ${founder.role}` : ""}
              {email !== "—" ? ` · ${email}` : ""}
            </p>
            <span className={`traffic-light traffic-${light}`} title={lightDesc}>
              <span className="traffic-dot" />
              {lightLabel}
            </span>
            <span
              className={`origin-badge ${founder.country_code || founder.origin_region || "unknown"}`}
              title={`${text.origin}: ${origin} (${confidence})`}
            >
              {founder.country_code || origin} · {confidence}
            </span>
            {founder.section && <span className="section-badge">{founder.section}</span>}
          </div>
          {discarded ? (
            <span className="decision-pill discarded">{text.discardedPill}</span>
          ) : (
            <span className={`decision-pill ${approved ? "approved" : founder.decision}`}>
              {approved ? text.approved : text.rejected}
            </span>
          )}
          <button className="modal-close" onClick={onClose} aria-label={text.closeModal}>
            ✕
          </button>
        </div>

        <div className="modal-scroll">
          <div className="profile-tiles">
            <article className="profile-tile">
              <span>{text.sectionLabel}</span>
              <strong>{area}</strong>
            </article>
            <article className="profile-tile">
              <span>{text.roundSize}</span>
              <strong>{round}</strong>
            </article>
            <article className="profile-tile skills-tile">
              <span>{text.businessEmail}</span>
              <strong className="email-value">{email}</strong>
              {skills.length > 0 && (
                <div className="skill-chips" style={{ marginTop: 8 }}>
                  {skills.slice(0, 3).map((skill) => (
                    <span className="skill-chip" key={skill}>
                      {skill}
                    </span>
                  ))}
                </div>
              )}
            </article>
          </div>

          {/* Resumen financiero — arriba, referencial para todo el modal */}
          <div className="modal-financial-strip">
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
              <strong>{business}</strong>
              <small>{text.b2bB2cHint}</small>
            </article>
          </div>

          <div className="modal-columns">
            {/* Izquierda: equipo (CTO, cofounders), pitch y evidencia pública */}
            <div className="card-body modal-col">
              <h4>{text.origin}</h4>
              <p className="just">
                {origin}
                {founder.origin_region ? ` · ${founder.origin_region}` : ""}
                {` · ${confidence}`}
                {founder.incubation_program ? ` · ${founder.incubation_program}` : ""}
              </p>

              {(translated?.activity_summary || translated?.pitch) && (
                <>
                  <h4>{text.activityLabel}</h4>
                  <p className="just">{translated?.activity_summary || translated?.pitch}</p>
                </>
              )}

              {translated?.pitch && translated?.activity_summary && (
                <>
                  <h4>{text.pitchLabel}</h4>
                  <p className="just">{translated.pitch}</p>
                </>
              )}

              <h4>{text.fundTeam}</h4>
              {team.length === 0 ? (
                <p className="muted">{text.fundTeamEmpty}</p>
              ) : (
                <div className="team-roster">
                  {team.map((member, i) => (
                    <article className="team-member" key={`${member.name}-${i}`}>
                      <div className="team-member-head">
                        <strong>{member.name}</strong>
                        <span className={`rel-pill rel-${member.relationship}`}>
                          {relationshipLabel(member.relationship, language)}
                        </span>
                      </div>
                      <p className="team-member-role">
                        {member.role || "—"}
                        {member.area ? ` · ${member.area}` : ""}
                      </p>
                      {member.skills?.length > 0 && (
                        <div className="skill-chips">
                          {member.skills.slice(0, 4).map((skill) => (
                            <span className="skill-chip" key={skill}>
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}
                      {member.profile_url && (
                        <a className="evlink" href={member.profile_url} target="_blank" rel="noreferrer">
                          {member.profile_url}
                        </a>
                      )}
                    </article>
                  ))}
                </div>
              )}

              {founder.signals.length > 0 && (
                <>
                  <h4>{text.signals}</h4>
                  <div className="chips">
                    {founder.signals.map((s, i) => (
                      <span className="chip" key={i}>
                        {s}
                      </span>
                    ))}
                  </div>
                </>
              )}

              {founder.evidence.length > 0 && (
                <>
                  <h4>{text.evidence}</h4>
                  {founder.evidence.map((url) => (
                    <a className="evlink" key={url} href={url} target="_blank" rel="noreferrer">
                      {url}
                    </a>
                  ))}
                </>
              )}

              {founder.social_links && founder.social_links.length > 0 && (
                <>
                  <h4>{text.communityLinks}</h4>
                  <div className="social-grid">
                    {founder.social_links.map((link) => (
                      <a
                        className={`social-card platform-${(link.platform || "other").toLowerCase()}`}
                        key={link.url}
                        href={link.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <span>{platformLabel(link.platform, language)}</span>
                        <strong>{link.label || platformLabel(link.platform, language)}</strong>
                      </a>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Derecha: análisis completo (rúbrica, gates, fondos, feedback) */}
            <div className="card-body modal-col">
              <h4>{text.justification}</h4>
              <p className="just">{translated?.justification}</p>

              <h4>{text.criteria}</h4>
              {founder.criteria.map((c, i) => (
                <div className="criterion" key={c.name}>
                  <div className="row">
                    <span>
                      {criterionLabel(c.name, language)}{" "}
                      <span className="w">
                        · {text.weight} {c.weight}%
                      </span>
                    </span>
                    <span>{c.score}/100</span>
                  </div>
                  <div className="bar">
                    <div style={{ width: `${c.score}%` }} />
                  </div>
                  {translated?.criteriaRationale[i] && <p className="rationale">{translated.criteriaRationale[i]}</p>}
                </div>
              ))}

              <h4>{text.requirements}</h4>
              {founder.requirements.map((r, i) => (
                <div className={`req ${r.met ? "met" : "unmet"}`} key={r.name}>
                  <span className="mark">{r.met ? "✓" : "✗"}</span>
                  <span>
                    {requirementLabel(r.name, language)}
                    {translated?.requirementDetail[i] && <span className="detail"> — {translated.requirementDetail[i]}</span>}
                  </span>
                </div>
              ))}

              <h4>{text.fundingRoundsTitle}</h4>
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

              <h4>{text.clientsTitle}</h4>
              {founder.clients && founder.clients.length > 0 ? (
                <div className="chips">
                  {founder.clients.map((client) => (
                    <span className="chip" key={client}>
                      {client}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="muted">{text.clientsEmpty}</p>
              )}

              {!approved && (translated?.feedback.length ?? 0) > 0 && (
                <div className="feedback">
                  <h4>{text.feedback}</h4>
                  <ul>
                    {translated?.feedback.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}

              <button className="outreach-btn" onClick={onOutreach} disabled={loadingMsg}>
                {loadingMsg ? text.drafting : text.outreach}
              </button>
              {msgError && <div className="status error">{msgError}</div>}
              {outreach && <div className="outreach-box">{outreach}</div>}
            </div>
          </div>
        </div>

        <div className="modal-actions">
          {discarded ? (
            <button className="outreach-btn" onClick={onUndoDiscard}>
              {text.undoDiscard}
            </button>
          ) : approved ? (
            <button className="outreach-btn check-cta" onClick={onGenerateCheck}>
              <ApprovedCheckIcon /> {text.generateCheck}
            </button>
          ) : (
            <>
              <button className="outreach-btn" onClick={onDiscard}>
                {text.discardFeedback}
              </button>
              {light === "yellow" && (
                <button className="outreach-btn check-cta" onClick={onGenerateCheck}>
                  {text.generateOverride}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function FounderCard({
  founder,
  language,
  selected,
  onSelect,
  initialDecision,
  onDecisionChange,
}: {
  founder: FounderProfile;
  language: Language;
  selected: boolean;
  onSelect: () => void;
  initialDecision?: DecisionState;
  onDecisionChange?: (company: string, name: string, state: DecisionState) => void;
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [checkOpen, setCheckOpen] = useState(false);
  const [forced, setForced] = useState(initialDecision === "forced");
  const [manualCheck, setManualCheck] = useState<Check | null>(null);
  const [discarded, setDiscarded] = useState(initialDecision === "discarded");
  const text = copy[language];

  // getDecisions() resuelve después del primer render — aplica la decisión
  // persistida en cuanto llega, sin pisar un cambio local ya hecho.
  useEffect(() => {
    if (initialDecision === "forced" && !forced) {
      setManualCheck(buildManualCheck(founder));
      setForced(true);
    }
    if (initialDecision === "discarded" && !discarded) setDiscarded(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialDecision]);

  const backendApproved = founder.decision === "approved";
  const isApproved = backendApproved || forced;
  const activeCheck = founder.check || manualCheck;
  const origin = originLabel(founder, language);
  const confidence = confidenceLabel(founder.origin_confidence, language);
  const light = founder.traffic_light || "red";
  const lightLabel = trafficLabel(light, language);
  const lightDesc = trafficDescription(light, language);
  const email = founder.business_email || founder.contact_hint || "—";

  const openModal = () => {
    onSelect();
    setModalOpen(true);
  };

  const openCheck = () => {
    if (!activeCheck) setManualCheck(buildManualCheck(founder));
    setCheckOpen(true);
  };

  const forceApprove = () => {
    setManualCheck(buildManualCheck(founder));
    setForced(true);
    setDiscarded(false);
    onDecisionChange?.(founder.company, founder.name, "forced");
  };

  return (
    <>
      <div
        className={`startup-tile ${isApproved ? "approved" : ""} ${selected ? "selected" : ""} ${discarded ? "discarded" : ""}`}
        onClick={openModal}
      >
        {isApproved && (
          <button
            className="approved-badge"
            title={text.viewCheck}
            aria-label={text.viewCheck}
            onClick={(e) => {
              e.stopPropagation();
              onSelect();
              openCheck();
            }}
          >
            <ApprovedCheckIcon />
          </button>
        )}
        <div className="score-badge">
          <span className="num">{founder.founder_score}</span>
          <span className="of">/ 100</span>
        </div>
        <h3>{founder.company}</h3>
        <p className="tile-sub">
          {founder.name}
          {founder.role ? ` · ${founder.role}` : ""}
        </p>
        <p className="tile-email">{email}</p>
        <span className={`traffic-light traffic-${light}`} title={lightDesc}>
          <span className="traffic-dot" />
          {lightLabel}
        </span>
        <span
          className={`origin-badge ${founder.country_code || founder.origin_region || "unknown"}`}
          title={`${text.origin}: ${origin} (${confidence})`}
        >
          {founder.country_code || origin} · {confidence}
        </span>
        {founder.section && <span className="section-badge">{founder.section}</span>}
        {discarded ? (
          <span className="decision-pill discarded">{text.discardedPill}</span>
        ) : (
          <span className={`decision-pill ${isApproved ? "approved" : founder.decision}`}>
            {isApproved ? text.approved : text.rejected}
          </span>
        )}
        {forced && !discarded && <span className="section-badge manual-badge">{text.manualApproval}</span>}
      </div>

      {modalOpen && (
        <StartupModal
          founder={founder}
          language={language}
          forced={forced}
          discarded={discarded}
          onClose={() => setModalOpen(false)}
          onGenerateCheck={() => {
            if (!isApproved) forceApprove();
            openCheck();
          }}
          onDiscard={() => {
            setDiscarded(true);
            setModalOpen(false);
            onDecisionChange?.(founder.company, founder.name, "discarded");
          }}
          onUndoDiscard={() => {
            setDiscarded(false);
            onDecisionChange?.(founder.company, founder.name, "clear");
          }}
        />
      )}
      {checkOpen && activeCheck && (
        <CheckModal check={activeCheck} language={language} onClose={() => setCheckOpen(false)} />
      )}
    </>
  );
}
