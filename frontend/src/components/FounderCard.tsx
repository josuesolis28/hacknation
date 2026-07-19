import { useEffect, useState } from "react";
import type { FounderProfile } from "../types";
import { generateOutreach, translateText } from "../api";
import {
  Language,
  confidenceLabel,
  copy,
  originLabel,
  relationshipLabel,
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

function CheckModal({ founder, language, onClose }: { founder: FounderProfile; language: Language; onClose: () => void }) {
  const text = copy[language];
  if (!founder.check) return null;
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
            <span className="name">{founder.check.issued_by}</span>
            <span className="id">Nº {founder.check.check_id}</span>
          </div>
          <div className="amount">${founder.check.amount_usd.toLocaleString("en-US")} USD</div>
          <p className="payto line" style={{ animationDelay: ".5s" }}>
            <span>{text.payTo}</span> {founder.check.issued_to} · {founder.check.company}
          </p>
          <div className="foot line" style={{ animationDelay: ".6s" }}>
            <span>
              {text.issueDate} {founder.check.date}
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
  onClose,
  onOpenCheck,
}: {
  founder: FounderProfile;
  language: Language;
  onClose: () => void;
  onOpenCheck: () => void;
}) {
  const [outreach, setOutreach] = useState<string | null>(null);
  const [loadingMsg, setLoadingMsg] = useState(false);
  const [msgError, setMsgError] = useState<string | null>(null);
  const [translatedJustification, setTranslatedJustification] = useState(founder.justification);
  const text = copy[language];
  const approved = founder.decision === "approved";
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

  useEffect(() => {
    if (language === "es") {
      setTranslatedJustification(founder.justification);
      return;
    }
    let active = true;
    void translateText(founder.justification, language)
      .then((value) => {
        if (active) setTranslatedJustification(value.text);
      })
      .catch(() => {
        if (active) setTranslatedJustification(founder.justification);
      });
    return () => {
      active = false;
    };
  }, [founder.justification, language]);

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
          <span className={`decision-pill ${founder.decision}`}>{approved ? text.approved : text.rejected}</span>
          <button className="modal-close" onClick={onClose} aria-label={text.closeModal}>
            ✕
          </button>
        </div>

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

        <div className="card-body">
          <h4>{text.origin}</h4>
          <p className="just">
            {origin}
            {founder.origin_region ? ` · ${founder.origin_region}` : ""}
            {` · ${confidence}`}
            {founder.incubation_program ? ` · ${founder.incubation_program}` : ""}
          </p>

          {(founder.activity_summary || founder.pitch) && (
            <>
              <h4>{text.activityLabel}</h4>
              <p className="just">{founder.activity_summary || founder.pitch}</p>
            </>
          )}

          {founder.pitch && founder.activity_summary && (
            <>
              <h4>{text.pitchLabel}</h4>
              <p className="just">{founder.pitch}</p>
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

          <h4>{text.justification}</h4>
          <p className="just">{translatedJustification}</p>

          <h4>{text.criteria}</h4>
          {founder.criteria.map((c) => (
            <div className="criterion" key={c.name}>
              <div className="row">
                <span>
                  {c.name}{" "}
                  <span className="w">
                    · {text.weight} {c.weight}%
                  </span>
                </span>
                <span>{c.score}/100</span>
              </div>
              <div className="bar">
                <div style={{ width: `${c.score}%` }} />
              </div>
              {c.rationale && <p className="rationale">{c.rationale}</p>}
            </div>
          ))}

          <h4>{text.requirements}</h4>
          {founder.requirements.map((r) => (
            <div className={`req ${r.met ? "met" : "unmet"}`} key={r.name}>
              <span className="mark">{r.met ? "✓" : "✗"}</span>
              <span>
                {r.name}
                {r.detail && <span className="detail"> — {r.detail}</span>}
              </span>
            </div>
          ))}

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

          {approved && founder.check && (
            <button className="outreach-btn check-cta" onClick={onOpenCheck}>
              <ApprovedCheckIcon /> {text.viewCheck}
            </button>
          )}

          {!approved && founder.feedback.length > 0 && (
            <div className="feedback">
              <h4>{text.feedback}</h4>
              <ul>
                {founder.feedback.map((f, i) => (
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
  );
}

export function FounderCard({
  founder,
  language,
  selected,
  onSelect,
}: {
  founder: FounderProfile;
  language: Language;
  selected: boolean;
  onSelect: () => void;
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [checkOpen, setCheckOpen] = useState(false);
  const text = copy[language];
  const approved = founder.decision === "approved";
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

  return (
    <>
      <div
        className={`startup-tile ${approved ? "approved" : ""} ${selected ? "selected" : ""}`}
        onClick={openModal}
      >
        {approved && founder.check && (
          <button
            className="approved-badge"
            title={text.viewCheck}
            aria-label={text.viewCheck}
            onClick={(e) => {
              e.stopPropagation();
              onSelect();
              setCheckOpen(true);
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
        <span className={`decision-pill ${founder.decision}`}>{approved ? text.approved : text.rejected}</span>
      </div>

      {modalOpen && (
        <StartupModal
          founder={founder}
          language={language}
          onClose={() => setModalOpen(false)}
          onOpenCheck={() => setCheckOpen(true)}
        />
      )}
      {checkOpen && <CheckModal founder={founder} language={language} onClose={() => setCheckOpen(false)} />}
    </>
  );
}
