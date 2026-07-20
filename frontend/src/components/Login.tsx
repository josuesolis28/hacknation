import { FormEvent, useEffect, useRef, useState } from "react";
import { getAuthConfig, login, loginWithGoogle, register, setAccessToken } from "../api";
import { Language, copy } from "../i18n";
import type { Role } from "../role";

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

export function Login({
  presetRole,
  language,
  setLanguage,
  onBack,
  onSuccess,
}: {
  presetRole: Role;
  language: Language;
  setLanguage: (l: Language) => void;
  onBack: () => void;
  onSuccess: (role: Role | null) => void;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const isStartup = presetRole === "startup";
  const [username, setUsername] = useState(isStartup ? "startup1" : "admin12345");
  const [password, setPassword] = useState(isStartup ? "startup1" : "admin12345");
  const [code, setCode] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regName, setRegName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState("");
  const googleBtnRef = useRef<HTMLDivElement>(null);
  const text = copy[language];

  useEffect(() => {
    void getAuthConfig()
      .then(({ google_client_id }) => setGoogleClientId(google_client_id))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!googleClientId || !googleBtnRef.current || mode !== "login" || isStartup) return;
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
              onSuccess(null);
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
  }, [googleClientId, mode, isStartup, onSuccess]);

  const submitLogin = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await login(username, password);
      setAccessToken(result.access_token);
      onSuccess(result.role);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to sign in");
    } finally {
      setLoading(false);
    }
  };

  const submitRegister = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await register(code.trim(), regEmail.trim(), regPassword, regName.trim());
      setAccessToken(result.access_token);
      onSuccess(result.role);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to register");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={mode === "login" ? submitLogin : submitRegister}>
        <div className="login-lang">
          <button type="button" className="login-back" onClick={onBack}>
            ‹ {isStartup ? text.roleStartup : text.roleInvestor}
          </button>
          <select value={language} onChange={(e) => setLanguage(e.target.value as Language)} aria-label="Language">
            <option value="en">EN</option>
            <option value="es">ES</option>
            <option value="de">DE</option>
          </select>
        </div>
        <span className="eyebrow">{text.loginEyebrow}</span>
        <h1>{text.loginTitle}</h1>
        <p>{text.loginBlurb}</p>

        <div className="login-mode-tabs">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
            {text.loginModeLogin}
          </button>
          <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
            {text.loginModeRegister}
          </button>
        </div>

        {mode === "login" ? (
          <>
            {googleClientId && !isStartup && (
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
          </>
        ) : (
          <>
            <p className="login-register-hint">{text.registerHint}</p>
            <label>
              {text.registerCode}
              <input
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="XXXXXXXX"
                required
              />
            </label>
            <label>
              {text.registerName}
              <input value={regName} onChange={(e) => setRegName(e.target.value)} />
            </label>
            <label>
              {text.registerEmail}
              <input
                type="email"
                autoComplete="email"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                required
              />
            </label>
            <label>
              {text.registerPassword}
              <input
                type="password"
                autoComplete="new-password"
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                required
                minLength={8}
              />
            </label>
            {error && <p className="form-error">{error}</p>}
            <button disabled={loading || !code.trim() || !regEmail.trim() || regPassword.length < 8}>
              {loading ? text.authenticating : text.registerButton}
            </button>
          </>
        )}
      </form>
    </main>
  );
}
