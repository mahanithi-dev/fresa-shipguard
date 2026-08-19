import React, { useState } from "react";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";

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
    <>
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
    </>
  );
}
