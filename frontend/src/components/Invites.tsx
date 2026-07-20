import { useEffect, useState } from "react";
import { InviteCode, createInvite, listInvites } from "../api";
import { Language, copy } from "../i18n";
import type { Role } from "../role";

export function Invites({ language, onClose }: { language: Language; onClose: () => void }) {
  const text = copy[language];
  const [role, setRole] = useState<Role>("startup");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invites, setInvites] = useState<InviteCode[] | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const reload = () => {
    void listInvites()
      .then(({ invites }) => setInvites(invites))
      .catch(() => setInvites([]));
  };

  useEffect(() => {
    reload();
  }, []);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      await createInvite(role, note.trim());
      setNote("");
      reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const copy_ = (code: string) => {
    void navigator.clipboard.writeText(code).then(() => {
      setCopiedCode(code);
      window.setTimeout(() => setCopiedCode(null), 1500);
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-panel-head">
          <div className="head-info">
            <h3>{text.invitesTitle}</h3>
          </div>
          <button className="modal-close" onClick={onClose} aria-label={text.closeModal}>
            ✕
          </button>
        </div>
        <div className="modal-scroll">
          <div className="card-body">
            <h4>{text.invitesGenerate}</h4>
            <div className="submit-form invites-form">
              <label>
                {text.invitesRole}
                <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
                  <option value="startup">{text.roleStartup}</option>
                  <option value="investor">{text.roleInvestor}</option>
                </select>
              </label>
              <label>
                {text.invitesNote}
                <input value={note} onChange={(e) => setNote(e.target.value)} placeholder={text.invitesNotePlaceholder} />
              </label>
            </div>
            {error && <div className="status error">{error}</div>}
            <button className="outreach-btn check-cta" disabled={loading} onClick={() => void generate()}>
              {text.invitesCreateBtn}
            </button>

            <h4>{text.invitesListTitle}</h4>
            {invites === null && (
              <div className="loading-state">
                <span className="spinner" />
              </div>
            )}
            {invites?.length === 0 && <p className="muted">{text.invitesEmpty}</p>}
            {invites?.map((inv) => (
              <article className="ticket-card" key={inv.code}>
                <div className="ticket-card-head">
                  <strong className="invite-code">{inv.code}</strong>
                  <span className={`decision-pill submission-status-${inv.used_by ? "approved" : "submitted"}`}>
                    {inv.used_by ? `${text.invitesUsedBy}: ${inv.used_by}` : text.invitesUnused}
                  </span>
                </div>
                <p className="ticket-card-sub">
                  {inv.role === "startup" ? text.roleStartup : text.roleInvestor}
                  {inv.note ? ` · ${inv.note}` : ""} · {new Date(inv.created_at).toLocaleDateString(language)}
                </p>
                {!inv.used_by && (
                  <button className="file-chip" onClick={() => copy_(inv.code)}>
                    {copiedCode === inv.code ? text.invitesCopied : text.invitesCopy}
                  </button>
                )}
              </article>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
