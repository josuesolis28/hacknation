import { useEffect, useState } from "react";
import { FormMeta, SubmissionTeamMember, getMeta, submitStartup } from "../api";
import { Language, copy } from "../i18n";

function FormBody({
  language,
  onSubmitted,
}: {
  language: Language;
  onSubmitted: () => void;
}) {
  const text = copy[language];
  const [meta, setMeta] = useState<FormMeta | null>(null);
  const [company, setCompany] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [country, setCountry] = useState("");
  const [website, setWebsite] = useState("");
  const [section, setSection] = useState("");
  const [roundSize, setRoundSize] = useState("");
  const [pitch, setPitch] = useState("");
  const [extraText, setExtraText] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [businessEmail, setBusinessEmail] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [instagram, setInstagram] = useState("");
  const [xUrl, setXUrl] = useState("");
  const [team, setTeam] = useState<SubmissionTeamMember[]>([{ name: "", role: "" }]);
  const [pdf, setPdf] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getMeta()
      .then((m) => {
        setMeta(m);
        setCountry(m.countries[0]?.name ?? "");
        setSection(m.sections[0] ?? "");
        setRoundSize(m.round_sizes[0] ?? "");
      })
      .catch(() => undefined);
  }, []);

  const updateTeamMember = (i: number, field: "name" | "role", value: string) => {
    setTeam((prev) => prev.map((m, idx) => (idx === i ? { ...m, [field]: value } : m)));
  };

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      await submitStartup({
        company,
        name,
        role,
        country,
        website,
        section,
        round_size: roundSize,
        pitch,
        extra_text: extraText,
        video_url: videoUrl,
        business_email: businessEmail,
        linkedin,
        instagram,
        x_url: xUrl,
        team,
        pdf,
      });
      onSubmitted();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="card-body submit-form">
        <label>
          {text.submitCompany}
          <input value={company} onChange={(e) => setCompany(e.target.value)} required />
        </label>
        <label>
          {text.submitFounderName}
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          {text.submitRole}
          <input value={role} onChange={(e) => setRole(e.target.value)} />
        </label>
        <label>
          {text.submitCountry}
          <select value={country} onChange={(e) => setCountry(e.target.value)}>
            {meta?.countries.map((c) => (
              <option key={c.code} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          {text.submitBusinessEmail}
          <input
            type="email"
            value={businessEmail}
            onChange={(e) => setBusinessEmail(e.target.value)}
            placeholder="contact@company.com"
          />
        </label>
        <label>
          {text.submitWebsite}
          <input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://" />
        </label>
        <label>
          {text.submitSection}
          <select value={section} onChange={(e) => setSection(e.target.value)}>
            {meta?.sections.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          {text.submitRoundSize}
          <select value={roundSize} onChange={(e) => setRoundSize(e.target.value)}>
            {meta?.round_sizes.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>

        <div className="submit-full submit-team">
          <span className="submit-section-label">{text.submitTeam}</span>
          {team.map((member, i) => (
            <div className="submit-team-row" key={i}>
              <input
                value={member.name}
                onChange={(e) => updateTeamMember(i, "name", e.target.value)}
                placeholder={i === 0 ? text.submitFounderName : text.submitTeamMemberName}
              />
              <input
                value={member.role}
                onChange={(e) => updateTeamMember(i, "role", e.target.value)}
                placeholder={text.submitTeamMemberRole}
              />
              {team.length > 1 && (
                <button
                  type="button"
                  className="ghost"
                  onClick={() => setTeam((prev) => prev.filter((_, idx) => idx !== i))}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            className="ghost submit-add-member"
            onClick={() => setTeam((prev) => [...prev, { name: "", role: "" }])}
          >
            {text.submitAddTeamMember}
          </button>
        </div>

        <label>
          {text.submitLinkedin}
          <input value={linkedin} onChange={(e) => setLinkedin(e.target.value)} placeholder="https://linkedin.com/company/..." />
        </label>
        <label>
          {text.submitInstagram}
          <input value={instagram} onChange={(e) => setInstagram(e.target.value)} placeholder="https://instagram.com/..." />
        </label>
        <label>
          {text.submitX}
          <input value={xUrl} onChange={(e) => setXUrl(e.target.value)} placeholder="https://x.com/..." />
        </label>
        <label>
          {text.submitVideoUrl} *
          <input
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="https://youtube.com/..."
            required
          />
        </label>
        <label className="submit-full">
          {text.submitPitch}
          <textarea value={pitch} onChange={(e) => setPitch(e.target.value)} rows={2} />
        </label>
        <label>
          {text.submitPdf}
          <input type="file" accept="application/pdf" onChange={(e) => setPdf(e.target.files?.[0] ?? null)} />
        </label>
        <label className="submit-full">
          {text.submitExtraText}
          <small className="muted">{text.submitExtraTextHint}</small>
          <textarea value={extraText} onChange={(e) => setExtraText(e.target.value)} rows={6} />
        </label>
        {error && <div className="status error">{error}</div>}
      </div>
      <div className="modal-actions">
        <button
          className="outreach-btn check-cta"
          disabled={loading || !company.trim() || !name.trim() || !country || !videoUrl.trim()}
          onClick={() => void submit()}
        >
          {loading ? text.submitting : text.submitButton}
        </button>
      </div>
    </>
  );
}

/** ``inline``: sin el overlay/backdrop de modal — para usarse embebido
 * directamente en una página (p. ej. el panel de la startup), no como popup. */
export function SubmitStartup({
  language,
  onClose,
  inline = false,
}: {
  language: Language;
  onClose: () => void;
  inline?: boolean;
}) {
  const text = copy[language];
  const [success, setSuccess] = useState(false);

  const body = success ? (
    <div className="modal-scroll">
      <div className="card-body">
        <h4>{text.submitSuccessTitle}</h4>
        <p className="just">{text.submitSuccessBody}</p>
      </div>
    </div>
  ) : (
    <div className="modal-scroll">
      <FormBody language={language} onSubmitted={() => setSuccess(true)} />
    </div>
  );

  if (inline) {
    return (
      <div className="submit-panel submit-inline">
        <div className="section-heading">
          <div>
            <h2>{text.submitModalTitle}</h2>
            <p>{text.submitModalHint}</p>
          </div>
        </div>
        {body}
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel submit-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-panel-head">
          <div className="head-info">
            <h3>{text.submitModalTitle}</h3>
            <p>{text.submitModalHint}</p>
          </div>
          <button className="modal-close" onClick={onClose} aria-label={text.closeModal}>
            ✕
          </button>
        </div>
        {body}
      </div>
    </div>
  );
}
