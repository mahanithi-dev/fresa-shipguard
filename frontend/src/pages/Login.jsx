import React, { useState } from "react";
import { LogIn, ShieldCheck, UserPlus } from "lucide-react";
import { api } from "../api/client";

export default function Login({ onLogin, onNavigateHome }) {
  const [mode, setMode] = useState("register"); // "register" (Create Account) | "login" (Sign In)
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
