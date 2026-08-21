import React, { useEffect, useState } from "react";
import { LogIn, ShieldCheck, UserPlus } from "lucide-react";
import { api } from "../api/client";

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

export default function Login({ initialError = "", onLogin, onNavigateHome }) {
  const [mode, setMode] = useState("register"); // "register" (Create Account) | "login" (Sign In)
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(initialError);
  const [loading, setLoading] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

  useEffect(() => {
    if (initialError) {
      setError(initialError);
    }
  }, [initialError]);

  // Triggers official Google OAuth 2.0 Account Chooser screen
  function triggerGoogleSignIn() {
    if (!googleClientId || !googleClientId.trim()) {
      setError("Google Sign-In is not configured yet. Please set VITE_GOOGLE_CLIENT_ID in frontend/.env.");
      return;
    }

    setError("");
    setLoading(true);

    const redirectUri = window.location.origin;
    const nonce = Math.random().toString(36).substring(2) + Date.now().toString(36);
    const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${encodeURIComponent(
      googleClientId.trim()
    )}&redirect_uri=${encodeURIComponent(
      redirectUri
    )}&response_type=id_token&scope=openid%20email%20profile&nonce=${nonce}&prompt=select_account`;

    // Direct browser redirect to Google's official account selector
    window.location.href = googleAuthUrl;
  }

  async function submit(event) {
    if (event) event.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        if (!name.trim()) {
          setError("Please enter your full name");
          setLoading(false);
          return;
        }
        const data = await api().request("/auth/register", {
          method: "POST",
          body: JSON.stringify({ name: name.trim(), email: email.trim(), password }),
        });
        onLogin(data.access_token);
      } else {
        const data = await api().request("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email: email.trim(), password }),
        });
        onLogin(data.access_token);
      }
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-shell">
      <form className="login-panel" onSubmit={submit} autoComplete="off">
        {onNavigateHome && (
          <button 
            type="button" 
            className="ghost-btn" 
            onClick={onNavigateHome}
            style={{ marginBottom: 8, padding: 0, fontSize: 13, color: "#64748b", textDecoration: "underline" }}
          >
            ← Back to Overview
          </button>
        )}

        <div className="login-brand">
          <ShieldCheck size={32} />
          <div>
            <h1>ShipGuard ERP</h1>
            <p>Logistics Exception & Risk Management Platform</p>
          </div>
        </div>

        {/* Mode Switcher Tabs: Slot 1 = Create Account, Slot 2 = Sign In */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", background: "#f1f5f9", borderRadius: 8, padding: 3, gap: 4, marginBottom: 16 }}>
          <button
            type="button"
            className="ghost-btn"
            style={{
              padding: "8px 0",
              fontSize: 13,
              fontWeight: 700,
              borderRadius: 6,
              background: mode === "register" ? "#ffffff" : "transparent",
              color: mode === "register" ? "#1e40af" : "#64748b",
              boxShadow: mode === "register" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
            }}
            onClick={() => { setMode("register"); setError(""); }}
          >
            Create Account
          </button>
          <button
            type="button"
            className="ghost-btn"
            style={{
              padding: "8px 0",
              fontSize: 13,
              fontWeight: 700,
              borderRadius: 6,
              background: mode === "login" ? "#ffffff" : "transparent",
              color: mode === "login" ? "#1e40af" : "#64748b",
              boxShadow: mode === "login" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
            }}
            onClick={() => { setMode("login"); setError(""); }}
          >
            Sign In
          </button>
        </div>

        {/* Google Sign In Area */}
        <div className="google-auth-container">
          <button
            type="button"
            className="google-btn-custom"
            disabled={loading}
            onClick={triggerGoogleSignIn}
          >
            <GoogleIcon />
            <span>{mode === "register" ? "Sign up with Google" : "Sign in with Google"}</span>
          </button>
        </div>

        {/* Divider */}
        <div className="login-divider">
          <span>or continue with email</span>
        </div>

        {mode === "register" && (
          <label>
            Full Name
            <input 
              type="text"
              value={name} 
              onChange={(e) => setName(e.target.value)} 
              placeholder="e.g. Mahanithi Operations"
              required 
              autoComplete="name"
            />
          </label>
        )}

        <label>
          Email Address
          <input 
            type="email"
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            placeholder="e.g. user@company.com"
            required 
            autoComplete="email"
          />
        </label>

        <label>
          Password
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            placeholder={mode === "register" ? "Create a secure password..." : "Enter password..."}
            required 
            autoComplete={mode === "register" ? "new-password" : "current-password"}
          />
        </label>

        {error && <div style={{ color: "#dc2626", fontSize: 13, fontWeight: 600 }}>⚠️ {error}</div>}

        <button className="primary-btn" type="submit" disabled={loading} style={{ width: "100%", justifyContent: "center", height: 42, marginTop: 4 }}>
          {mode === "register" ? <UserPlus size={18} /> : <LogIn size={18} />}
          {loading ? (mode === "register" ? "Creating Account..." : "Signing In...") : (mode === "register" ? "Create Account & Enter" : "Sign In to Operations Portal")}
        </button>
      </form>
    </main>
  );
}
