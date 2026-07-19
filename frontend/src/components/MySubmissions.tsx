import { useEffect, useState } from "react";
import { MySubmission, SubmissionFile, fetchSubmissionFileBlobUrl, getMySubmissions } from "../api";
import { Language, copy } from "../i18n";

function statusLabel(status: MySubmission["status"], text: (typeof copy)[Language]): string {
  switch (status) {
    case "submitted": return text.statusSubmitted;
    case "in_progress": return text.statusInProgress;
    case "approved": return text.statusApproved;
    case "rejected": return text.statusRejected;
  }
}

function FileChip({ file }: { file: SubmissionFile }) {
  const open = async () => {
    if (file.kind === "video" && file.url) {
      window.open(file.url, "_blank", "noreferrer");
      return;
    }
    try {
      const blobUrl = await fetchSubmissionFileBlobUrl(file.id);
      window.open(blobUrl, "_blank", "noreferrer");
    } catch {
      /* si falla, simplemente no abre */
    }
  };
  const icon = file.kind === "pdf" ? "📄" : file.kind === "image" ? "🖼️" : "🎬";
  return (
    <button className="file-chip" onClick={() => void open()}>
      {icon} {file.kind === "video" ? "Video" : file.filename}
    </button>
  );
}

function SubmissionCard({ s, language, text }: { s: MySubmission; language: Language; text: (typeof copy)[Language] }) {
  return (
    <article className="ticket-card">
      <div className="ticket-card-head">
        <strong>{s.company}</strong>
        <span className={`decision-pill submission-status-${s.status}`}>{statusLabel(s.status, text)}</span>
      </div>
      <p className="ticket-card-sub">
        {s.name} · {new Date(s.created_at).toLocaleDateString(language)}
      </p>
      {s.files.length > 0 && (
        <div className="file-chips">
          {s.files.map((f) => (
            <FileChip file={f} key={f.id} />
          ))}
        </div>
      )}
      {s.status === "approved" && s.founder?.check && (
        <p className="ticket-check-line">
          ${s.founder.check.amount_usd.toLocaleString("en-US")} USD · Nº {s.founder.check.check_id}
        </p>
      )}
      {s.status === "rejected" && s.founder?.feedback && s.founder.feedback.length > 0 && (
        <ul className="ticket-feedback">
          {s.founder.feedback.slice(0, 3).map((f, j) => (
            <li key={j}>{f}</li>
          ))}
        </ul>
      )}
    </article>
  );
}

function Body({ language }: { language: Language }) {
  const text = copy[language];
  const [submissions, setSubmissions] = useState<MySubmission[] | null>(null);

  useEffect(() => {
    void getMySubmissions()
      .then(({ submissions }) => setSubmissions(submissions))
      .catch(() => setSubmissions([]));
  }, []);

  return (
    <div className="card-body">
      {submissions === null && (
        <div className="loading-state">
          <span className="spinner" />
        </div>
      )}
      {submissions?.length === 0 && <p className="muted">{text.mySubmissionsEmpty}</p>}
      {submissions?.map((s, i) => (
        <SubmissionCard s={s} language={language} text={text} key={`${s.company}-${i}`} />
      ))}
    </div>
  );
}

export function MySubmissions({
  language,
  onClose,
  inline = false,
}: {
  language: Language;
  onClose: () => void;
  inline?: boolean;
}) {
  const text = copy[language];

  if (inline) {
    return (
      <div className="submit-panel submit-inline">
        <div className="section-heading">
          <div>
            <h2>{text.mySubmissionsTitle}</h2>
          </div>
        </div>
        <Body language={language} />
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-panel-head">
          <div className="head-info">
            <h3>{text.mySubmissionsTitle}</h3>
          </div>
          <button className="modal-close" onClick={onClose} aria-label={text.closeModal}>
            ✕
          </button>
        </div>
        <div className="modal-scroll">
          <Body language={language} />
        </div>
      </div>
    </div>
  );
}
