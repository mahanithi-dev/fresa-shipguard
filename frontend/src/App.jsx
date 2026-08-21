import React, { lazy, Suspense, useEffect, useState } from "react";
import { api } from "./api/client";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));

function RouteLoadingFallback() {
  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#f8fafc", color: "#64748b", fontFamily: "sans-serif" }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ width: 28, height: 28, border: "3px solid #e2e8f0", borderTopColor: "#1e40af", borderRadius: "50%", animation: "spin 0.8s linear infinite", margin: "0 auto 12px" }} />
        <div style={{ fontSize: 13, fontWeight: 600, color: "#0f172a" }}>Loading ShipGuard...</div>
      </div>
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("shipguard-token"));
  const [route, setRoute] = useState("landing");
  const [authError, setAuthError] = useState("");

  // Handle Google OAuth Redirect Response (e.g. from accounts.google.com/#id_token=...)
  useEffect(() => {
    const hash = window.location.hash ? window.location.hash.substring(1) : "";
    const search = window.location.search ? window.location.search.substring(1) : "";
    const params = new URLSearchParams(hash || search);

    const errorParam = params.get("error");
    if (errorParam) {
      window.history.replaceState(null, "", window.location.pathname);
      setAuthError(errorParam === "access_denied" ? "Google sign-in was cancelled." : `Google sign-in error: ${errorParam}`);
      setRoute("login");
      return;
    }

    const idToken = params.get("id_token") || params.get("credential");
    if (idToken) {
      window.history.replaceState(null, "", window.location.pathname);
      api().request("/auth/google", {
        method: "POST",
        body: JSON.stringify({ id_token: idToken }),
      }).then((data) => {
        handleLogin(data.access_token);
      }).catch((err) => {
        console.error("Google authentication error:", err);
        setAuthError(err.message || "Google authentication failed.");
        setRoute("login");
      });
    }
  }, []);

  function handleLogin(nextToken) {
    localStorage.setItem("shipguard-token", nextToken);
    setToken(nextToken);
    setRoute("app");
  }

  function handleLogout() {
    localStorage.removeItem("shipguard-token");
    setToken(null);
    setRoute("landing");
  }

  function handleEnterShipGuard() {
    if (token) {
      setRoute("app");
    } else {
      setRoute("login");
    }
  }

  return (
    <Suspense fallback={<RouteLoadingFallback />}>
      {route === "landing" && (
        <LandingPage onEnter={handleEnterShipGuard} />
      )}
      {route === "login" && (
        <Login
          initialError={authError}
          onLogin={handleLogin}
          onNavigateHome={() => { setAuthError(""); setRoute("landing"); }}
        />
      )}
      {route === "app" && (
        token ? (
          <Dashboard token={token} onLogout={handleLogout} onNavigateHome={() => setRoute("landing")} />
        ) : (
          <Login
            initialError={authError}
            onLogin={handleLogin}
            onNavigateHome={() => { setAuthError(""); setRoute("landing"); }}
          />
        )
      )}
    </Suspense>
  );
}
