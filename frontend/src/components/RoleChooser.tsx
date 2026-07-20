import { Language, copy } from "../i18n";
import type { Role } from "../role";

export function RoleChooser({
  language,
  setLanguage,
  onChoose,
}: {
  language: Language;
  setLanguage: (l: Language) => void;
  onChoose: (role: Role) => void;
}) {
  const text = copy[language];
  return (
    <main className="role-page">
      <div className="role-card">
        <div className="role-lang">
          <select value={language} onChange={(e) => setLanguage(e.target.value as Language)} aria-label="Language">
            <option value="en">EN</option>
            <option value="es">ES</option>
            <option value="de">DE</option>
          </select>
        </div>
        <span className="eyebrow">{text.loginEyebrow}</span>
        <h1>{text.roleTitle}</h1>
        <p>{text.roleHint}</p>
        <div className="role-options">
          <button className="role-option" onClick={() => onChoose("investor")}>
            <strong>{text.roleInvestor}</strong>
            <span>{text.roleInvestorHint}</span>
          </button>
          <button className="role-option" onClick={() => onChoose("startup")}>
            <strong>{text.roleStartup}</strong>
            <span>{text.roleStartupHint}</span>
          </button>
        </div>
      </div>
    </main>
  );
}
