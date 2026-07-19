import { useState } from "react";
import type { FounderProfile } from "../types";
import { generateOutreach } from "../api";

export function FounderCard({ founder }: { founder: FounderProfile }) {
  const [open, setOpen] = useState(false);
  const [outreach, setOutreach] = useState<string | null>(null);
  const [loadingMsg, setLoadingMsg] = useState(false);
  const [msgError, setMsgError] = useState<string | null>(null);

  const approved = founder.decision === "approved";

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
    <div className={`founder-card ${approved ? "approved" : ""}`}>
      <div className="card-head" onClick={() => setOpen(!open)}>
        <div className="score-badge">
          <span className="num">{founder.founder_score}</span>
          <span className="of">/ 100</span>
        </div>
        <div className="head-info">
          <h3>{founder.name}</h3>
          <p>
            {founder.company}
            {founder.role ? ` · ${founder.role}` : ""}
          </p>
        </div>
        <span className={`decision-pill ${founder.decision}`}>
          {approved ? "✓ APROBADO — $100K" : "✗ NO CALIFICA"}
        </span>
        <span className="chev">{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <div className="card-body">
          <h4>Justificación</h4>
          <p className="just">{founder.justification}</p>

          <h4>Criterios ponderados (rúbrica pre-seed)</h4>
          {founder.criteria.map((c) => (
            <div className="criterion" key={c.name}>
              <div className="row">
                <span>
                  {c.name} <span className="w">· peso {c.weight}%</span>
                </span>
                <span>{c.score}/100</span>
              </div>
              <div className="bar">
                <div style={{ width: `${c.score}%` }} />
              </div>
              {c.rationale && <p className="rationale">{c.rationale}</p>}
            </div>
          ))}

          <h4>Requisitos del fondo</h4>
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
              <h4>Señales técnicas</h4>
              <div className="chips">
                {founder.signals.map((s, i) => (
                  <span className="chip" key={i}>{s}</span>
                ))}
              </div>
            </>
          )}

          {founder.evidence.length > 0 && (
            <>
              <h4>Evidencia</h4>
              {founder.evidence.map((url) => (
                <a className="evlink" key={url} href={url} target="_blank" rel="noreferrer">
                  {url}
                </a>
              ))}
            </>
          )}

          {approved && founder.check && (
            <div className="check">
              <span className="stamp">EMITIDO</span>
              <div className="bank">
                <span className="name">{founder.check.issued_by}</span>
                <span className="id">Nº {founder.check.check_id}</span>
              </div>
              <div className="amount">
                ${founder.check.amount_usd.toLocaleString("en-US")} USD
              </div>
              <p className="payto">
                <span>Páguese a la orden de:</span> {founder.check.issued_to} ·{" "}
                {founder.check.company}
              </p>
              <div className="foot">
                <span>Fecha de emisión: {founder.check.date}</span>
                <span>Aprobación instantánea · The VC Brain</span>
              </div>
            </div>
          )}

          {!approved && founder.feedback.length > 0 && (
            <div className="feedback">
              <h4>Feedback automático — qué falta para calificar</h4>
              <ul>
                {founder.feedback.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}

          <button className="outreach-btn" onClick={onOutreach} disabled={loadingMsg}>
            {loadingMsg ? "Redactando…" : "✉️ Generar outreach personalizado"}
          </button>
          {msgError && <div className="status error">{msgError}</div>}
          {outreach && <div className="outreach-box">{outreach}</div>}
        </div>
      )}
    </div>
  );
}
