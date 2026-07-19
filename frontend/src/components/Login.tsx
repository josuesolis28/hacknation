import { FormEvent, useEffect, useRef, useState } from "react";
import { getAuthConfig, login, loginWithGoogle, setAccessToken } from "../api";
import { Language, copy, loadLanguage, saveLanguage } from "../i18n";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, string>) => void;
        };
      };
    };
  }
}

const GSI_SCRIPT_ID = "google-identity-services";

function loadGsiScript(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.getElementById(GSI_SCRIPT_ID);
    if (existing) {
      existing.addEventListener("load", () => resolve());
      return;
    }
    const script = document.createElement("script");
    script.id = GSI_SCRIPT_ID;
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("No se pudo cargar Google Identity Services"));
    document.head.appendChild(script);
  });
}

export function Login({ onSuccess }: { onSuccess: () => void }) {
  const [language, setLanguage] = useState<Language>(() => loadLanguage("en"));
  const [username, setUsername] = useState("admin12345");
  const [password, setPassword] = useState("admin12345");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState("");
  const googleBtnRef = useRef<HTMLDivElement>(null);
  const text = copy[language];

  useEffect(() => {
    saveLanguage(language);
  }, [language]);

  useEffect(() => {
    void getAuthConfig()
      .then(({ google_client_id }) => setGoogleClientId(google_client_id))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!googleClientId || !googleBtnRef.current) return;
    let cancelled = false;
    void loadGsiScript().then(() => {
      if (cancelled || !window.google || !googleBtnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: (response) => {
          setLoading(true);
          setError("");
          void loginWithGoogle(response.credential)
            .then((result) => {
              setAccessToken(result.access_token);
              onSuccess();
            })
            .catch((e) => setError(e instanceof Error ? e.message : "Unable to sign in with Google"))
            .finally(() => setLoading(false));
        },
      });
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: "outline",
        size: "large",
        width: "320",
      });
    });
    return () => {
      cancelled = true;
    };
  }, [googleClientId, onSuccess]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await login(username, password);
      setAccessToken(result.access_token);
      onSuccess();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={submit}>
        <div className="login-lang">
          <select value={language} onChange={(e) => setLanguage(e.target.value as Language)} aria-label="Language">
            <option value="en">EN</option>
            <option value="es">ES</option>
            <option value="de">DE</option>
          </select>
        </div>
        <span className="eyebrow">{text.loginEyebrow}</span>
        <h1>{text.loginTitle}</h1>
        <p>{text.loginBlurb}</p>

        {googleClientId && (
          <>
            <div ref={googleBtnRef} className="google-btn-slot" />
            <div className="login-divider">
              <span>{text.orDivider}</span>
            </div>
          </>
        )}

        <label>
          {text.user}
          <input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
        <label>
          {text.password}
          <input
            autoComplete="current-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button disabled={loading}>{loading ? text.authenticating : text.access}</button>
        <small>{text.loginHint}</small>
      </form>
    </main>
  );
}
