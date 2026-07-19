import { FormEvent, useEffect, useState } from "react";
import { login, setAccessToken } from "../api";
import { Language, copy, loadLanguage, saveLanguage } from "../i18n";

export function Login({ onSuccess }: { onSuccess: () => void }) {
  const [language, setLanguage] = useState<Language>(() => loadLanguage("en"));
  const [username, setUsername] = useState("admin12345");
  const [password, setPassword] = useState("admin12345");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const text = copy[language];

  useEffect(() => { saveLanguage(language); }, [language]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true); setError("");
    try {
      const result = await login(username, password);
      setAccessToken(result.access_token);
      onSuccess();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to sign in");
    } finally { setLoading(false); }
  };

  return <main className="login-page"><form className="login-card" onSubmit={submit}>
    <div className="login-lang"><select value={language} onChange={(e) => setLanguage(e.target.value as Language)} aria-label="Language"><option value="en">EN</option><option value="es">ES</option><option value="de">DE</option></select></div>
    <span className="eyebrow">{text.loginEyebrow}</span>
    <h1>{text.loginTitle}</h1><p>{text.loginBlurb}</p>
    <label>{text.user}<input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} /></label>
    <label>{text.password}<input autoComplete="current-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
    {error && <p className="form-error">{error}</p>}
    <button disabled={loading}>{loading ? text.authenticating : text.access}</button>
    <small>{text.loginHint}</small>
  </form></main>;
}
