import React, { lazy, Suspense, useState } from "react";

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
        <Login onLogin={handleLogin} onNavigateHome={() => setRoute("landing")} />
      )}
      {route === "app" && (
        token ? (
          <Dashboard token={token} onLogout={handleLogout} onNavigateHome={() => setRoute("landing")} />
        ) : (
          <Login onLogin={handleLogin} onNavigateHome={() => setRoute("landing")} />
        )
      )}
    </Suspense>
  );
}
