import React, { useEffect, useMemo, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import { 
  AlertTriangle, Bot, Boxes, CalendarClock, Check, Copy, Filter, 
  Loader2, LogIn, PackagePlus, RefreshCcw, Search, Send, ShieldCheck, 
  Sparkles, X, LayoutDashboard, Globe, Truck, FileText, 
  ChevronRight, LogOut, Anchor, CloudSun, DollarSign
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function api(token) {
  return {
    async request(path, options = {}) {
      const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(options.headers || {}),
        },
      });
      if (!res.ok) {
        let errorMsg = res.statusText || "Request failed";
        try {
          const payload = await res.json();
          errorMsg = payload.detail || payload.message || JSON.stringify(payload);
        } catch (e) {
          // Fallback to status text
        }
        const err = new Error(errorMsg);
        err.status = res.status;
        err.retryAfter = res.headers.get("Retry-After");
        throw err;
      }
      const text = await res.text();
      try {
        return text ? JSON.parse(text) : null;
      } catch (e) {
        return text;
      }
    },
  };
}

function RiskBadge({ tier }) {
  const tierKey = tier ? tier.toLowerCase() : "none";
  return (
    <span className={`erp-badge ${tierKey}`}>
      {tier === "HIGH" && "🔴 "}
      {tier === "MEDIUM" && "🟡 "}
      {tier === "LOW" && "🟢 "}
      {tier || "UNSCORED"}
    </span>
  );
}

function RiskMeter({ score, tier }) {
  const pct = Math.round((score || 0) * 100);
  const tierKey = tier ? tier.toLowerCase() : "low";
  return (
    <div className="erp-risk-meter">
      <div className="erp-meter-bar">
        <div className={`erp-meter-fill ${tierKey}`} style={{ width: `${pct}%` }} />
      </div>
      <span style={{ fontWeight: 800, fontSize: 13 }}>{pct}%</span>
    </div>
  );
}

function timeAgo(isoString) {
  if (!isoString) return "Just updated";
  const diffMs = Date.now() - new Date(isoString).getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "Just updated";
  if (diffMins === 1) return "1 min ago";
  if (diffMins < 60) return `${diffMins} mins ago`;
  const diffHours = Math.floor(diffMins / 60);
  return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
}

/* ==========================================================================
   LANDING PAGE (HOME PAGE - UNTOUCHED & PRESERVED)
   ========================================================================== */

function LandingPage({ onEnter }) {
  return (
    <main className="erp-landing">
      <header className="erp-header">
        <div className="erp-nav">
          <div className="erp-logo">
            <ShieldCheck size={28} />
            <span>ShipGuard</span>
          </div>
          <nav className="erp-nav-links">
            <a href="#solutions">Solutions</a>
            <a href="#features">Features</a>
            <a href="#about">About</a>
          </nav>
          <div className="erp-nav-actions">
            <button className="erp-secondary-btn" onClick={onEnter}>Sign In</button>
            <button className="erp-primary-btn" onClick={onEnter}>Enter ShipGuard</button>
          </div>
        </div>
      </header>

      <section className="erp-hero">
        <div className="erp-hero-content">
          <h1>Enterprise Shipment Risk Management</h1>
          <p className="erp-hero-subtitle">
            Predict delays, optimize operations, and reduce costs with AI-powered logistics intelligence. 
            Built for freight forwarders, logistics providers, and supply chain professionals.
          </p>
          <div className="erp-hero-stats">
            <div className="erp-stat">
              <strong>81%</strong>
              <span>Prediction Accuracy</span>
            </div>
            <div className="erp-stat">
              <strong>40%</strong>
              <span>Delay Reduction</span>
            </div>
            <div className="erp-stat">
              <strong>24/7</strong>
              <span>Real-time Monitoring</span>
            </div>
          </div>
          <div className="erp-hero-cta">
            <button className="erp-primary-btn large" onClick={onEnter}>
              Get Started
            </button>
            <button className="erp-secondary-btn large" onClick={onEnter}>
              Schedule Demo
            </button>
          </div>
        </div>
      </section>

      <section className="erp-trust" id="about">
        <div className="erp-trust-content">
          <h2>Trusted by Logistics Professionals</h2>
          <p>ShipGuard helps leading freight forwarding companies manage shipment risks and improve operational efficiency.</p>
        </div>
      </section>

      <section className="erp-solutions" id="solutions">
        <div className="erp-section-header">
          <h2>Solutions for Every Logistics Challenge</h2>
          <p>Comprehensive risk management platform designed for modern supply chain operations</p>
        </div>
        <div className="erp-solutions-grid">
          <div className="erp-solution-card">
            <div className="erp-solution-icon">
              <AlertTriangle size={32} />
            </div>
            <h3>Risk Prediction</h3>
            <p>Advanced ML models predict shipment delays before they occur, enabling proactive intervention and customer communication.</p>
            <ul>
              <li>Carrier reliability analysis</li>
              <li>Route delay patterns</li>
              <li>Seasonal risk factors</li>
            </ul>
          </div>
          <div className="erp-solution-card">
            <div className="erp-solution-icon">
              <CalendarClock size={32} />
            </div>
            <h3>Real-time Monitoring</h3>
            <p>Continuous tracking of shipments across all transport modes with automated risk scoring and status updates.</p>
            <ul>
              <li>AIR, SEA, LAND tracking</li>
              <li>Automatic risk recalculation</li>
              <li>Exception alerts</li>
            </ul>
          </div>
          <div className="erp-solution-card">
            <div className="erp-solution-icon">
              <Boxes size={32} />
            </div>
            <h3>Operations Optimization</h3>
            <p>Smart prioritization helps teams focus on high-risk shipments with actionable recommendations and AI explanations.</p>
            <ul>
              <li>Risk-based work queues</li>
              <li>AI-powered insights</li>
              <li>Performance analytics</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="erp-features" id="features">
        <div className="erp-section-header">
          <h2>Platform Capabilities</h2>
          <p>Enterprise-grade features for logistics operations teams</p>
        </div>
        <div className="erp-features-list">
          <div className="erp-feature-item">
            <div className="erp-feature-check">✓</div>
            <div className="erp-feature-text">
              <h4>Intelligent Risk Scoring</h4>
              <p>Multi-factor analysis using carrier performance, route history, cargo type, and seasonal patterns</p>
            </div>
          </div>
          <div className="erp-feature-item">
            <div className="erp-feature-check">✓</div>
            <div className="erp-feature-text">
              <h4>AI-Powered Explanations</h4>
              <p>Understand risk factors with natural language explanations powered by retrieval-augmented generation</p>
            </div>
          </div>
          <div className="erp-feature-item">
            <div className="erp-feature-check">✓</div>
            <div className="erp-feature-text">
              <h4>Comprehensive Analytics</h4>
              <p>Historical analysis, carrier performance metrics, and pattern identification for continuous improvement</p>
            </div>
          </div>
          <div className="erp-feature-item">
            <div className="erp-feature-check">✓</div>
            <div className="erp-feature-text">
              <h4>Enterprise Integration</h4>
              <p>Oracle database support, API-first architecture, and scalable deployment options</p>
            </div>
          </div>
        </div>
      </section>

      <section className="erp-cta">
        <div className="erp-cta-content">
          <h2>Ready to Transform Your Logistics Operations?</h2>
          <p>Join forward-thinking companies using ShipGuard to reduce delays and improve customer satisfaction.</p>
          <div className="erp-cta-buttons">
            <button className="erp-primary-btn large" onClick={onEnter}>
              Start Using ShipGuard
            </button>
            <button className="erp-secondary-btn large">
              Contact Sales
            </button>
          </div>
        </div>
      </section>

      <footer className="erp-footer">
        <div className="erp-footer-content">
          <div className="erp-footer-brand">
            <div className="erp-logo">
              <ShieldCheck size={24} />
              <span>ShipGuard</span>
            </div>
            <p>Intelligent Freight Forwarding Risk Management</p>
          </div>
          <div className="erp-footer-links">
            <div className="erp-footer-column">
              <h4>Product</h4>
              <a href="#solutions">Solutions</a>
              <a href="#features">Features</a>
              <a href="#">Pricing</a>
            </div>
            <div className="erp-footer-column">
              <h4>Company</h4>
              <a href="#">About</a>
              <a href="#">Careers</a>
              <a href="#">Contact</a>
            </div>
            <div className="erp-footer-column">
              <h4>Resources</h4>
              <a href="#">Documentation</a>
              <a href="#">API Reference</a>
              <a href="#">Support</a>
            </div>
          </div>
        </div>
        <div className="erp-footer-bottom">
          <p>© 2026 ShipGuard. All rights reserved.</p>
        </div>
      </footer>
    </main>
  );
}

/* ==========================================================================
   AUTHENTICATION VIEW
   ========================================================================== */

function Login({ onLogin, onNavigateHome }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const data = await api().request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      onLogin(data.access_token);
    } catch (err) {
      setError(err.message);
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
            style={{ marginBottom: 12, padding: 0, fontSize: 13, color: "#64748b", textDecoration: "underline" }}
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
        <label>
          Email or Username
          <input 
            type="text"
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            placeholder="e.g. fresa_admin or ops@shipguard.local"
            required 
            autoComplete="username"
          />
        </label>
        <label>
          Password
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            placeholder="Enter password..."
            required 
            autoComplete="current-password"
          />
        </label>
        {error && <div style={{ color: "#dc2626", fontSize: 13, fontWeight: 600 }}>{error}</div>}
        <button className="primary-btn" type="submit" style={{ width: "100%", justifyContent: "center", height: 42 }}>
          <LogIn size={18} /> Sign In to Operations Portal
        </button>
      </form>
    </main>
  );
}

/* ==========================================================================
   INTAKE MODAL DIALOG
   ========================================================================== */

function IntakeModal({ client, carriers, routes, isOpen, onClose, onCreated }) {
  const defaultRoute = routes[0];
  const defaultCarrier = carriers[0];
  const [form, setForm] = useState({});

  useEffect(() => {
    if (defaultRoute && defaultCarrier) {
      const etd = new Date();
      const eta = new Date();
      eta.setDate(etd.getDate() + Math.max(1, Math.round(defaultRoute.avg_transit_days)));
      setForm({
        shipment_ref: `SHP-2026-${Math.floor(1000 + Math.random() * 8999)}`,
        carrier_id: defaultCarrier.carrier_id,
        route_id: defaultRoute.route_id,
        mode: defaultRoute.mode,
        cargo_type: "General",
        etd: etd.toISOString().slice(0, 10),
        eta: eta.toISOString().slice(0, 10),
        status: "BOOKED",
      });
    }
  }, [defaultRoute?.route_id, defaultCarrier?.carrier_id, isOpen]);

  async function submit(event) {
    event.preventDefault();
    await client.request("/shipments", { method: "POST", body: JSON.stringify(form) });
    onClose();
    onCreated();
  }

  if (!isOpen) return null;

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(15, 23, 42, 0.5)", backdropFilter: "blur(2px)", zIndex: 300, display: "grid", placeItems: "center", padding: 20 }}>
      <form style={{ background: "#ffffff", borderRadius: 10, width: "min(560px, 100%)", padding: 24, boxShadow: "0 20px 50px rgba(0,0,0,0.2)", display: "flex", flexDirection: "column", gap: 16 }} onSubmit={submit}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #e2e8f0", paddingBottom: 14 }}>
          <h3 style={{ margin: 0, fontSize: 18, color: "#0f172a", display: "flex", alignItems: "center", gap: 8 }}>
            <PackagePlus size={20} color="#1e40af" /> Create New Shipment Record
          </h3>
          <button className="ghost-btn" type="button" onClick={onClose}><X size={18} /></button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <label>
            Shipment Reference
            <input value={form.shipment_ref || ""} onChange={(e) => setForm({ ...form, shipment_ref: e.target.value })} required />
          </label>

          <label>
            Cargo Type
            <select value={form.cargo_type || "General"} onChange={(e) => setForm({ ...form, cargo_type: e.target.value })}>
              {["General", "Reefer", "Hazardous", "Pharma", "Textiles"].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>

          <label>
            Carrier
            <select value={form.carrier_id || ""} onChange={(e) => setForm({ ...form, carrier_id: Number(e.target.value) })}>
              {carriers.map((carrier) => (
                <option key={carrier.carrier_id} value={carrier.carrier_id}>
                  {carrier.carrier_name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Trade Lane Route
            <select
              value={form.route_id || ""}
              onChange={(e) => {
                const route = routes.find((item) => item.route_id === Number(e.target.value));
                setForm({ ...form, route_id: route.route_id, mode: route.mode });
              }}
            >
              {routes.map((route) => (
                <option key={route.route_id} value={route.route_id}>
                  {route.origin_port} &gt; {route.dest_port} ({route.mode})
                </option>
              ))}
            </select>
          </label>

          <label>
            ETD (Estimated Departure)
            <input type="date" value={form.etd || ""} onChange={(e) => setForm({ ...form, etd: e.target.value })} required />
          </label>

          <label>
            ETA (Estimated Arrival)
            <input type="date" value={form.eta || ""} onChange={(e) => setForm({ ...form, eta: e.target.value })} required />
          </label>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, borderTop: "1px solid #e2e8f0", paddingTop: 16, marginTop: 6 }}>
          <button className="secondary-btn" type="button" onClick={onClose}>Cancel</button>
          <button className="primary-btn" type="submit">Create Shipment</button>
        </div>
      </form>
    </div>
  );
}

/* ==========================================================================
   CORE ENTERPRISE DASHBOARD & WORKSPACE
   ========================================================================== */

function Dashboard({ token, onLogout, onNavigateHome }) {
  const client = useMemo(() => api(token), [token]);
  const [shipments, setShipments] = useState([]);
  const [summary, setSummary] = useState({ high: 0, medium: 0, low: 0, total: 0 });
  const [metrics, setMetrics] = useState(null);
  const [carriers, setCarriers] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [externalIntel, setExternalIntel] = useState(null);
  const [activeTab, setActiveTab] = useState("worklist");
  const [selected, setSelected] = useState(null);
  const [filters, setFilters] = useState({ status: "", risk_tier: "", mode: "" });
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [totalShipments, setTotalShipments] = useState(0);
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiCopied, setAiCopied] = useState(false);
  const [intakeOpen, setIntakeOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const [reportSummary, setReportSummary] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);

  function showToast(message, type = "success") {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  }

  async function loadReportSummary() {
    try {
      const data = await client.request("/reports/summary");
      setReportSummary(data);
    } catch (err) {
      console.error("Failed to load report summary:", err);
    }
  }

  async function downloadCSV() {
    setExportLoading(true);
    try {
      const paramsObj = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
      const params = new URLSearchParams(paramsObj);
      const res = await fetch(`${API_BASE}/reports/export/csv?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to export CSV report");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `shipguard_report_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast("CSV Manifest exported successfully!");
    } catch (err) {
      setError(err.message);
      showToast(err.message || "Failed to export CSV report", "error");
    } finally {
      setExportLoading(false);
    }
  }


  async function load() {
    setError("");
    setLoading(true);
    try {
      const paramsObj = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
      paramsObj.page = page;
      paramsObj.page_size = pageSize;
      const params = new URLSearchParams(paramsObj);
      const [shipmentData, summaryData, metricsData, carrierData, routeData, externalData] = await Promise.all([
        client.request(`/shipments?${params.toString()}`),
        client.request("/risk/summary"),
        client.request("/risk/metrics"),
        client.request("/carriers?page=1&page_size=200"),
        client.request("/routes?page=1&page_size=200"),
        client.request("/external-intelligence/summary").catch(() => null),
      ]);

      if (shipmentData && shipmentData.items) {
        setShipments(shipmentData.items || []);
        setTotalShipments(shipmentData.total || 0);
        setPage(shipmentData.page || page);
        setPageSize(shipmentData.page_size || pageSize);
      } else {
        setShipments(shipmentData || []);
        setTotalShipments(Array.isArray(shipmentData) ? shipmentData.length : 0);
      }

      setSummary(summaryData || { high: 0, medium: 0, low: 0, total: 0 });
      setMetrics(metricsData || null);
      setCarriers(carrierData || []);
      setRoutes(routeData || []);
      setExternalIntel(externalData || null);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.status, filters.risk_tier, filters.mode, page, pageSize]);

  async function openShipment(id) {
    setAiExplanation("");
    setAiError("");
    setAiCopied(false);
    setSelected(await client.request(`/shipments/${id}`));
  }

  const visible = shipments.filter((shipment) => {
    const text = `${shipment.shipment_ref} ${shipment.container_no || ''} ${shipment.vessel_name || ''} ${shipment.consignee || ''} ${shipment.disruption_event || ''} ${shipment.route} ${shipment.carrier_name}`.toLowerCase();
    return text.includes(query.toLowerCase());
  });

  return (
    <div className="erp-layout">
      {toast && (
        <div className={`erp-toast ${toast.type}`}>
          <span>{toast.message}</span>
        </div>
      )}
      {/* Top Header Navigation */}
      <header className="erp-top-header">
        <div className="erp-brand-block">
          <div className="erp-logo-mark">
            <ShieldCheck size={20} />
          </div>
          <span className="erp-logo-text">ShipGuard ERP</span>
          <span className="erp-env-badge">Operations Portal</span>
        </div>

        <div className="erp-header-center">
          <div className="erp-global-search">
            <Search size={16} className="search-icon" />
            <input
              placeholder="Quick search shipment ref, container #, vessel, route..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="erp-header-actions">
          <div className="erp-sync-pill">
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#059669" }} /> Live Sync Active
          </div>
          <button className="ghost-btn" onClick={onNavigateHome}>
            Home Landing
          </button>
          <div className="erp-user-badge">
            <div className="erp-avatar">OP</div>
            <div style={{ fontSize: 12 }}>
              <div style={{ fontWeight: 700, color: "#0f172a" }}>Ops Manager</div>
              <div style={{ color: "#64748b", fontSize: 11 }}>Fresa Freight Forwarding</div>
            </div>
            <button className="ghost-btn" style={{ padding: 6, marginLeft: 6 }} onClick={onLogout} title="Logout">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="erp-body">
        {/* Sidebar Nav */}
        <aside className="erp-sidebar">
          <div>
            <div className="erp-nav-section">
              <div className="erp-nav-label">OPERATIONS WORKSPACE</div>
              <button
                className={`erp-nav-item ${activeTab === "worklist" ? "active" : ""}`}
                onClick={() => setActiveTab("worklist")}
              >
                <div className="erp-nav-item-left">
                  <LayoutDashboard size={18} />
                  <span>Shipment Worklist</span>
                </div>
                {summary.high > 0 && <span className="erp-nav-badge danger">{summary.high}</span>}
              </button>

              <button
                className={`erp-nav-item ${activeTab === "external" ? "active" : ""}`}
                onClick={() => setActiveTab("external")}
              >
                <div className="erp-nav-item-left">
                  <Globe size={18} />
                  <span>Real-World Intel</span>
                </div>
                <span className="erp-nav-badge primary">Live</span>
              </button>

              <button
                className={`erp-nav-item ${activeTab === "reports" ? "active" : ""}`}
                onClick={() => {
                  setActiveTab("reports");
                  loadReportSummary();
                }}
              >
                <div className="erp-nav-item-left">
                  <FileText size={18} />
                  <span>Reports & Analytics</span>
                </div>
                <span className="erp-nav-badge primary">New</span>
              </button>
            </div>


            <div className="erp-nav-section">
              <div className="erp-nav-label">MASTER DATA & MODEL</div>
              <div className="erp-nav-item" style={{ cursor: "default", opacity: 0.8 }}>
                <div className="erp-nav-item-left">
                  <Truck size={18} />
                  <span>Carriers ({carriers.length})</span>
                </div>
              </div>
              <div className="erp-nav-item" style={{ cursor: "default", opacity: 0.8 }}>
                <div className="erp-nav-item-left">
                  <Anchor size={18} />
                  <span>Trade Lanes ({routes.length})</span>
                </div>
              </div>
            </div>
          </div>

          <div style={{ padding: "12px", background: "#f8fafc", borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: 4, display: "flex", alignItems: "center", gap: 6 }}>
              <Sparkles size={14} color="#1e40af" /> Model Intelligence
            </div>
            {metrics ? (
              <div style={{ color: "#64748b", lineHeight: 1.4 }}>
                Precision: <strong>{(metrics.precision * 100).toFixed(0)}%</strong> · Recall: <strong>{(metrics.recall * 100).toFixed(0)}%</strong>
                <div style={{ fontSize: 11, marginTop: 2, color: "#94a3b8" }}>Target: {metrics.target_definition}</div>
              </div>
            ) : (
              <span style={{ color: "#94a3b8" }}>Loading metrics...</span>
            )}
          </div>
        </aside>

        {/* Content Pane */}
        <main className="erp-main-pane">
          {/* Top Page Header Bar */}
          <div className="erp-page-header">
            <div className="erp-page-title">
              <h2>
                {activeTab === "worklist"
                  ? "Shipment Risk & Exception Worklist"
                  : activeTab === "reports"
                  ? "Operations Risk & Analytics Reports"
                  : "Real-World Environmental Intelligence Board"}
              </h2>
              <p>
                {activeTab === "worklist"
                  ? "Monitor real-time shipment delay probabilities, carrier disruptions, and AI recommendations."
                  : activeTab === "reports"
                  ? "Export custom CSV manifests and generate publication-ready Executive PDF Risk Reports."
                  : "Live weather at major hubs, port congestion wait times, FX rates, and destination port holidays."}
              </p>

            </div>

            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <button
                className="secondary-btn"
                disabled={loading}
                onClick={async () => {
                  setLoading(true);
                  try {
                    await client.request("/external-intelligence/sync", { method: "POST" });
                    await load();
                    showToast("Live external intelligence synchronized!");
                  } catch (e) {
                    setError(e.message);
                    setLoading(false);
                  }
                }}
              >
                <RefreshCcw size={15} className={loading ? "spin" : ""} /> Sync Live APIs
              </button>

              <button
                className="secondary-btn"
                disabled={loading}
                onClick={async () => {
                  if (window.confirm("Generate fresh realistic AI shipment records with container IDs and disruptions?")) {
                    setLoading(true);
                    try {
                      const res = await client.request("/admin/generate-ai-data", { method: "POST" });
                      await load();
                      showToast(res.message || "Synthesized AI shipment records successfully!");
                    } catch (e) {
                      setError(e.message);
                      setLoading(false);
                    }
                  }
                }}
              >
                <Sparkles size={15} color="#1e40af" /> Seed AI Data
              </button>

              {activeTab === "worklist" && (
                <button className="primary-btn" onClick={() => setIntakeOpen(true)}>
                  <PackagePlus size={16} /> New Shipment
                </button>
              )}
            </div>
          </div>

          {error && (
            <div style={{ background: "#fee2e2", border: "1px solid #fca5a5", color: "#991b1b", padding: "10px 14px", borderRadius: 6, marginBottom: 18, fontSize: 13, fontWeight: 600 }}>
              ⚠️ {error}
            </div>
          )}

          {/* KPI Stat Cards */}
          <section className="erp-kpi-grid">
            <div className="erp-kpi-card total">
              <div className="erp-kpi-header">
                <span>TOTAL ACTIVE SHIPMENTS</span>
                <div className="erp-kpi-icon"><Boxes size={18} /></div>
              </div>
              <div className="erp-kpi-value">{summary.total || 0}</div>
              <div className="erp-kpi-footer">Across AIR, SEA & LAND freight</div>
            </div>

            <div className="erp-kpi-card danger">
              <div className="erp-kpi-header">
                <span>HIGH DELAY RISK</span>
                <div className="erp-kpi-icon"><AlertTriangle size={18} /></div>
              </div>
              <div className="erp-kpi-value">{summary.high || 0}</div>
              <div className="erp-kpi-footer" style={{ color: "#dc2626", fontWeight: 600 }}>Requires immediate intervention</div>
            </div>

            <div className="erp-kpi-card warning">
              <div className="erp-kpi-header">
                <span>MEDIUM RISK WARNINGS</span>
                <div className="erp-kpi-icon"><CalendarClock size={18} /></div>
              </div>
              <div className="erp-kpi-value">{summary.medium || 0}</div>
              <div className="erp-kpi-footer" style={{ color: "#d97706" }}>Watch list monitoring</div>
            </div>

            <div className="erp-kpi-card success">
              <div className="erp-kpi-header">
                <span>LOW RISK / ON TIME</span>
                <div className="erp-kpi-icon"><ShieldCheck size={18} /></div>
              </div>
              <div className="erp-kpi-value">{summary.low || 0}</div>
              <div className="erp-kpi-footer" style={{ color: "#059669" }}>On-schedule delivery path</div>
            </div>
          </section>

          {/* View Tab Switcher / Content Area */}
          {activeTab === "reports" ? (
            <section className="erp-card" style={{ padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 18 }}>📊 Operational Risk & SLA Intelligence Reports</h3>
                  <p style={{ color: "#64748b", margin: "4px 0 0 0", fontSize: 13 }}>
                    Export custom CSV manifests and generate publication-ready Executive PDF Risk Reports.
                  </p>
                </div>

                <div style={{ display: "flex", gap: 12 }}>
                  <button
                    className="secondary-btn"
                    disabled={exportLoading}
                    onClick={downloadCSV}
                    style={{ height: 38, fontWeight: 600 }}
                  >
                    {exportLoading ? <Loader2 size={16} className="spin" /> : <FileText size={16} />}
                    Export CSV Manifest
                  </button>

                  <button
                    className="primary-btn"
                    onClick={() => {
                      loadReportSummary();
                      setShowReportModal(true);
                    }}
                    style={{ height: 38 }}
                  >
                    <Sparkles size={16} /> Generate Executive PDF Report
                  </button>
                </div>
              </div>

              {/* Analytics Overview Cards */}
              {reportSummary ? (
                <>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 24 }}>
                    <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", padding: 16, borderRadius: 8 }}>
                      <div style={{ fontSize: 12, color: "#64748b", fontWeight: 700 }}>TOTAL SHIPMENTS</div>
                      <div style={{ fontSize: 24, fontWeight: 800, color: "#0f172a", marginTop: 4 }}>{reportSummary.metrics.total_shipments}</div>
                      <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{reportSummary.metrics.in_transit} in-transit</div>
                    </div>
                    <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", padding: 16, borderRadius: 8 }}>
                      <div style={{ fontSize: 12, color: "#dc2626", fontWeight: 700 }}>HIGH RISK CRITICAL</div>
                      <div style={{ fontSize: 24, fontWeight: 800, color: "#991b1b", marginTop: 4 }}>{reportSummary.metrics.high_risk}</div>
                      <div style={{ fontSize: 11, color: "#dc2626", marginTop: 2 }}>Requires immediate action</div>
                    </div>
                    <div style={{ background: "#fff7ed", border: "1px solid #fed7aa", padding: 16, borderRadius: 8 }}>
                      <div style={{ fontSize: 12, color: "#c2410c", fontWeight: 700 }}>ACTIVE DELAYS</div>
                      <div style={{ fontSize: 24, fontWeight: 800, color: "#9a3412", marginTop: 4 }}>{reportSummary.metrics.delayed}</div>
                      <div style={{ fontSize: 11, color: "#c2410c", marginTop: 2 }}>Delay status active</div>
                    </div>
                    <div style={{ background: "#ecfdf5", border: "1px solid #a7f3d0", padding: 16, borderRadius: 8 }}>
                      <div style={{ fontSize: 12, color: "#047857", fontWeight: 700 }}>AVG RISK SCORE</div>
                      <div style={{ fontSize: 24, fontWeight: 800, color: "#065f46", marginTop: 4 }}>{reportSummary.metrics.avg_risk_score_pct}%</div>
                      <div style={{ fontSize: 11, color: "#047857", marginTop: 2 }}>Model risk index</div>
                    </div>
                  </div>

                  {/* Carrier SLA Scorecards */}
                  <h4 style={{ fontSize: 16, margin: "24px 0 12px 0", color: "#0f172a" }}>🚢 Carrier Reliability & SLA Scorecards</h4>
                  <div className="erp-table-responsive" style={{ marginBottom: 28 }}>
                    <table className="erp-table">
                      <thead>
                        <tr>
                          <th>Carrier Name</th>
                          <th>Carrier Code</th>
                          <th>Active Freight Volume</th>
                          <th>Delayed Count</th>
                          <th>High Risk Volume</th>
                          <th>Historical SLA On-Time %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportSummary.carrier_scorecards.map((c) => (
                          <tr key={c.carrier_code}>
                            <td style={{ fontWeight: 700, color: "#1e40af" }}>{c.carrier_name}</td>
                            <td><code style={{ background: "#f1f5f9", padding: "2px 6px", borderRadius: 4 }}>{c.carrier_code}</code></td>
                            <td><strong>{c.total_shipments}</strong> shipments</td>
                            <td style={{ color: c.delayed_count > 0 ? "#dc2626" : "#059669", fontWeight: 600 }}>{c.delayed_count}</td>
                            <td style={{ color: c.high_risk_count > 0 ? "#dc2626" : "#059669", fontWeight: 600 }}>{c.high_risk_count}</td>
                            <td>
                              <span style={{ fontWeight: 800, color: c.on_time_pct >= 75 ? "#059669" : "#d97706" }}>
                                {c.on_time_pct}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Top Trade Lane Bottlenecks */}
                  <h4 style={{ fontSize: 16, margin: "24px 0 12px 0", color: "#0f172a" }}>⚓ Trade Lane Route Risk Matrix</h4>
                  <div className="erp-table-responsive">
                    <table className="erp-table">
                      <thead>
                        <tr>
                          <th>Trade Lane Route</th>
                          <th>Mode</th>
                          <th>Avg Planned Transit</th>
                          <th>Total Volume</th>
                          <th>High Risk Shipments</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportSummary.route_analytics.map((r) => (
                          <tr key={r.route_str + r.mode}>
                            <td style={{ fontWeight: 700 }}>{r.route_str}</td>
                            <td><span style={{ fontSize: 11, fontWeight: 700, padding: "2px 6px", background: "#f1f5f9", borderRadius: 4 }}>{r.mode}</span></td>
                            <td>{r.avg_transit_days} days</td>
                            <td>{r.total_shipments} shipments</td>
                            <td style={{ color: r.high_risk_count > 0 ? "#dc2626" : "#059669", fontWeight: 700 }}>{r.high_risk_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: "center", padding: 40, color: "#64748b" }}>
                  <Loader2 size={24} className="spin" style={{ margin: "0 auto 8px" }} />
                  <div>Loading executive report intelligence...</div>
                </div>
              )}
            </section>
          ) : activeTab === "external" ? (

            <section className="erp-card" style={{ padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 18 }}>🌐 Environmental & Port Intelligence Feed</h3>
                  <p style={{ color: "#64748b", margin: "4px 0 0 0", fontSize: 13 }}>
                    Live external data streams cached and analyzed against shipment routes.
                  </p>
                </div>
                <div style={{ fontSize: 12, color: "#475569", textAlign: "right" }}>
                  <div><strong>Data Freshness:</strong> {externalIntel ? timeAgo(externalIntel.last_updated) : "Syncing..."}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8" }}>Sources: Open-Meteo, Frankfurter FX, Nager.Date</div>
                </div>
              </div>

              <div className="erp-intel-grid">
                <div className="erp-intel-card">
                  <h4><CloudSun size={18} color="#1e40af" /> Port Weather Conditions ({externalIntel?.weather?.length || 0} Hubs)</h4>
                  <div style={{ maxHeight: 240, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
                    {(externalIntel?.weather || []).map((w) => (
                      <div key={w.port_name} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, background: w.is_severe ? "#fef2f2" : "#f8fafc", padding: "8px 12px", borderRadius: 6, border: w.is_severe ? "1px solid #fca5a5" : "1px solid #e2e8f0" }}>
                        <span><strong>{w.port_name}</strong> ({w.country_code}): {w.condition}</span>
                        <span>{w.temp_c}°C · 💨 {w.wind_kmh} km/h</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="erp-intel-card">
                  <h4><DollarSign size={18} color="#1e40af" /> Live Foreign Exchange Rates</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {(externalIntel?.currencies || []).map((c) => (
                      <div key={c.pair} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, background: "#f8fafc", padding: "10px 14px", borderRadius: 6, border: "1px solid #e2e8f0" }}>
                        <span><strong>{c.pair} Rate:</strong></span>
                        <span><strong>{c.rate.toFixed(2)}</strong> <span style={{ fontSize: 11, color: "#64748b" }}>(Vol: {c.volatility_pct}%)</span></span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="erp-intel-card">
                  <h4><Anchor size={18} color="#1e40af" /> Port Congestion Matrix</h4>
                  <div style={{ maxHeight: 240, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8 }}>
                    {(externalIntel?.port_status || []).map((p) => (
                      <div key={p.port_code} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, background: p.congestion_level === "HIGH" ? "#fff7ed" : "#f8fafc", padding: "8px 12px", borderRadius: 6, border: "1px solid #e2e8f0" }}>
                        <span><strong>{p.port_name}</strong></span>
                        <span style={{ fontWeight: 700, color: p.congestion_level === "HIGH" ? "#c2410c" : "#166534" }}>
                          {p.congestion_level} ({p.avg_vessel_wait_hours}h wait)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <h4 style={{ fontSize: 15, margin: "24px 0 12px 0", color: "#0f172a" }}>Destination Country Port Holidays ({externalIntel?.holidays?.length || 0})</h4>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12 }}>
                {(externalIntel?.holidays || []).slice(0, 12).map((h) => (
                  <div key={h.country_code + h.holiday_date + h.holiday_name} style={{ background: "#ffffff", border: "1px solid #e2e8f0", padding: "10px 12px", borderRadius: 6, fontSize: 13 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b", fontSize: 11, marginBottom: 4 }}>
                      <span style={{ fontWeight: 700 }}>{h.country_code}</span>
                      <span>{h.holiday_date}</span>
                    </div>
                    <strong style={{ color: "#0f172a" }}>{h.holiday_name}</strong>
                  </div>
                ))}
              </div>
            </section>
          ) : (
            <section className="erp-card">
              {/* Toolbar */}
              <div className="erp-toolbar">
                <div className="erp-filter-group">
                  <div className="erp-search-box">
                    <Search size={16} className="icon" />
                    <input
                      placeholder="Filter by ref, container, vessel, consignee..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </div>

                  <select value={filters.status} onChange={(e) => { setFilters({ ...filters, status: e.target.value }); setPage(1); }}>
                    <option value="">Status: All</option>
                    {["BOOKED", "IN_TRANSIT", "DELAYED", "DELIVERED"].map((item) => <option key={item}>{item}</option>)}
                  </select>

                  <select value={filters.risk_tier} onChange={(e) => { setFilters({ ...filters, risk_tier: e.target.value }); setPage(1); }}>
                    <option value="">Risk: All Tiers</option>
                    {['HIGH', 'MEDIUM', 'LOW'].map((item) => <option key={item}>{item}</option>)}
                  </select>

                  <select value={filters.mode} onChange={(e) => { setFilters({ ...filters, mode: e.target.value }); setPage(1); }}>
                    <option value="">Mode: All</option>
                    {["AIR", "SEA", "LAND"].map((item) => <option key={item}>{item}</option>)}
                  </select>

                  {(filters.status || filters.risk_tier || filters.mode || query) && (
                    <button
                      className="ghost-btn"
                      style={{ height: 32, fontSize: 12, padding: "0 8px" }}
                      onClick={() => {
                        setFilters({ status: "", risk_tier: "", mode: "" });
                        setQuery("");
                        setPage(1);
                        showToast("Filters reset to default.");
                      }}
                    >
                      <X size={14} /> Reset
                    </button>
                  )}
                </div>

                <div style={{ fontSize: 13, color: "#64748b", fontWeight: 600 }}>
                  Showing {visible.length} of {totalShipments} shipments
                </div>
              </div>

              {/* ERP Data Table */}
              <div className="erp-table-responsive">
                <table className="erp-table">
                  <thead>
                    <tr>
                      <th>Shipment Ref / Container</th>
                      <th>Vessel / Vehicle</th>
                      <th>Trade Lane Route</th>
                      <th>Carrier</th>
                      <th>Consignee</th>
                      <th>Mode</th>
                      <th>ETA Date</th>
                      <th>Status & Disruption</th>
                      <th>Delay Risk Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((shipment) => (
                      <tr key={shipment.shipment_id} onClick={() => openShipment(shipment.shipment_id)}>
                        <td>
                          <div style={{ fontWeight: 700, color: "#1e40af" }}>{shipment.shipment_ref}</div>
                          {shipment.container_no && <div style={{ fontSize: 11, color: '#64748b' }}>📦 {shipment.container_no}</div>}
                        </td>
                        <td>{shipment.vessel_name || "—"}</td>
                        <td>{shipment.route}</td>
                        <td style={{ fontWeight: 600 }}>{shipment.carrier_name}</td>
                        <td>{shipment.consignee || "—"}</td>
                        <td>
                          <span style={{ fontSize: 11, fontWeight: 700, padding: "2px 6px", background: "#f1f5f9", borderRadius: 4 }}>
                            {shipment.mode}
                          </span>
                        </td>
                        <td style={{ fontWeight: 600 }}>{shipment.eta}</td>
                        <td>
                          <span className={`status-tag ${(shipment.status || 'booked').toLowerCase()}`}>
                            {shipment.status}
                          </span>
                          {shipment.disruption_event && (
                            <span className="erp-badge high" style={{ marginLeft: 6, fontSize: 10, padding: '1px 5px' }}>
                              ⚠️ Alert
                            </span>
                          )}
                        </td>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <RiskBadge tier={shipment.risk_tier} />
                            <RiskMeter score={shipment.risk_score} tier={shipment.risk_tier} />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="erp-pagination">
                <div style={{ display: "flex", gap: 6 }}>
                  <button className="secondary-btn" style={{ height: 32, fontSize: 12 }} disabled={page === 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
                    Previous
                  </button>
                  <button className="secondary-btn" style={{ height: 32, fontSize: 12 }} disabled={page * pageSize >= totalShipments} onClick={() => setPage((p) => p + 1)}>
                    Next
                  </button>
                </div>

                <span>
                  Page <strong>{page}</strong> · Showing {totalShipments === 0 ? 0 : `${(page - 1) * pageSize + 1}-${Math.min(page * pageSize, totalShipments)}`} of {totalShipments} records
                </span>

                <select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }} style={{ height: 32, fontSize: 12 }}>
                  {[10, 25, 50, 100, 200].map((n) => <option key={n} value={n}>{n} rows / page</option>)}
                </select>
              </div>
            </section>
          )}
        </main>
      </div>

      {/* Slide-over Inspector Drawer */}
      <div className={`erp-drawer-overlay ${selected ? "open" : ""}`} onClick={() => setSelected(null)} />
      <aside className={`erp-drawer ${selected ? "open" : ""}`}>
        {selected && (
          <>
            <div className="erp-drawer-header">
              <div>
                <span className="status-tag in_transit" style={{ marginBottom: 4, display: "inline-block" }}>
                  {selected.status}
                </span>
                <h3>{selected.shipment_ref}</h3>
              </div>
              <button className="ghost-btn" onClick={() => setSelected(null)}>
                <X size={20} />
              </button>
            </div>

            <div className="erp-drawer-body">
              {/* Risk Banner */}
              <div className="erp-risk-banner">
                <div>
                  <div style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: 0.5, opacity: 0.9 }}>
                    Calculated Delay Probability
                  </div>
                  <RiskBadge tier={selected.risk?.risk_tier} />
                </div>
                <strong>{Math.round((selected.risk?.risk_score || 0) * 100)}%</strong>
              </div>

              {selected.disruption_event && (
                <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 8, padding: '12px 14px', color: '#991b1b', fontSize: 13 }}>
                  ⚠️ <strong>Active Disruption Warning:</strong> {selected.disruption_event}
                </div>
              )}

              {/* RAG AI Risk Explanation Card */}
              <div className="erp-ai-box">
                <div className="erp-ai-box-header">
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Bot size={18} /> RAG Risk Intelligence (Gemini 3.6 Flash)
                  </span>
                  <button
                    className="secondary-btn"
                    style={{ height: 28, fontSize: 12, padding: "0 8px" }}
                    disabled={aiLoading}
                    onClick={async () => {
                      setAiLoading(true);
                      setAiError("");
                      try {
                        const res = await client.request(`/ai/explain/${selected.shipment_id}`);
                        setAiExplanation(res.explanation || "No explanation available.");
                      } catch (e) {
                        setAiError(e.message || "Failed to generate AI explanation.");
                      } finally {
                        setAiLoading(false);
                      }
                    }}
                  >
                    {aiLoading ? <Loader2 size={14} className="spin" /> : <Sparkles size={14} />}
                    {aiExplanation ? "Regenerate" : "Explain Risk"}
                  </button>
                </div>

                {aiError && <div style={{ color: "#dc2626", fontSize: 12 }}>{aiError}</div>}

                {aiExplanation ? (
                  <>
                    <div className="erp-ai-box-body">{aiExplanation}</div>
                    <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
                      <button
                        className="ghost-btn"
                        style={{ height: 26, fontSize: 11, padding: "0 8px" }}
                        onClick={() => {
                          navigator.clipboard.writeText(aiExplanation);
                          setAiCopied(true);
                          showToast("AI explanation copied to clipboard!");
                          setTimeout(() => setAiCopied(false), 2000);
                        }}
                      >
                        {aiCopied ? <Check size={13} color="#059669" /> : <Copy size={13} />}
                        {aiCopied ? "Copied" : "Copy Analysis"}
                      </button>
                    </div>
                  </>
                ) : (
                  <div style={{ fontSize: 13, color: "#64748b" }}>
                    Click <strong>"Explain Risk"</strong> to run real-time RAG analysis against route weather, port congestion history, and carrier SLA records.
                  </div>
                )}
              </div>

              {/* Key Details */}
              <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 8, padding: 16, display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
                <div><strong>Carrier:</strong> {selected.carrier_name}</div>
                <div><strong>Trade Lane:</strong> {selected.route} ({selected.mode})</div>
                {selected.container_no && <div><strong>Container / BL:</strong> {selected.container_no}</div>}
                {selected.vessel_name && <div><strong>Vessel / Flight:</strong> {selected.vessel_name}</div>}
                {selected.consignee && <div><strong>Consignee:</strong> {selected.consignee}</div>}
                <div><strong>ETD:</strong> {selected.etd} · <strong>ETA:</strong> {selected.eta}</div>
              </div>

              {/* Contributing Risk Factors */}
              <div>
                <h4 style={{ margin: "0 0 10px 0", fontSize: 15 }}>Contributing Risk Factors</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {(selected.risk?.top_factors || []).map((factor, idx) => (
                    <div key={idx} style={{ background: "#ffffff", border: "1px solid #e2e8f0", padding: "10px 12px", borderRadius: 6, fontSize: 13 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700 }}>
                        <span>{factor.factor}</span>
                        <span style={{ color: "#1e40af" }}>{factor.value || factor.impact}</span>
                      </div>
                      {factor.source && <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>Source: {factor.source}</div>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Event Timeline */}
              <div>
                <h4 style={{ margin: "0 0 10px 0", fontSize: 15 }}>Milestone Audit Timeline</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {selected.history.map((event) => (
                    <div key={event.history_id} style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: 6, fontSize: 13 }}>
                      <span>{event.event_type}</span>
                      <time style={{ color: "#64748b", fontSize: 12 }}>{new Date(event.event_ts).toLocaleDateString()}</time>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </aside>

      {/* New Shipment Modal */}
      <IntakeModal
        client={client}
        carriers={carriers}
        routes={routes}
        isOpen={intakeOpen}
        onClose={() => setIntakeOpen(false)}
        onCreated={() => {
          load();
          showToast("New shipment created and risk calculated!");
        }}
      />

      {/* Executive PDF Risk Report Modal */}
      {showReportModal && reportSummary && (
        <div className="erp-report-modal-overlay" onClick={() => setShowReportModal(false)}>
          <div className="erp-report-modal" onClick={(e) => e.stopPropagation()}>
            <div className="erp-report-modal-header no-print">
              <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700 }}>
                <FileText size={20} /> Executive PDF Risk Report Preview
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <button
                  className="primary-btn"
                  style={{ padding: "6px 14px", fontSize: 13 }}
                  onClick={() => window.print()}
                >
                  🖨️ Print / Save as PDF
                </button>
                <button
                  className="ghost-btn"
                  style={{ color: "white", padding: 6 }}
                  onClick={() => setShowReportModal(false)}
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            <div className="erp-report-modal-body">
              <div className="erp-report-document">
                <div className="erp-doc-header">
                  <div className="erp-doc-title">
                    <h1>SHIPGUARD OPERATIONAL RISK & SLA INTELLIGENCE REPORT</h1>
                    <p>Executive Risk Summary & Freight Exception Briefing</p>
                  </div>
                  <div className="erp-doc-meta">
                    <div><strong>Generated:</strong> {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</div>
                    <div><strong>Prepared By:</strong> Operations Desk Manager</div>
                    <div><strong>System:</strong> ShipGuard ERP v1.0</div>
                  </div>
                </div>

                <div className="erp-doc-grid">
                  <div className="erp-doc-stat">
                    <h4>Total Freight Volume</h4>
                    <span>{reportSummary.metrics.total_shipments}</span>
                  </div>
                  <div className="erp-doc-stat" style={{ background: "#fef2f2" }}>
                    <h4 style={{ color: "#dc2626" }}>Critical High Risk</h4>
                    <span style={{ color: "#991b1b" }}>{reportSummary.metrics.high_risk}</span>
                  </div>
                  <div className="erp-doc-stat" style={{ background: "#fff7ed" }}>
                    <h4 style={{ color: "#c2410c" }}>Active Delays</h4>
                    <span style={{ color: "#9a3412" }}>{reportSummary.metrics.delayed}</span>
                  </div>
                  <div className="erp-doc-stat" style={{ background: "#ecfdf5" }}>
                    <h4 style={{ color: "#047857" }}>Avg Risk Index</h4>
                    <span style={{ color: "#065f46" }}>{reportSummary.metrics.avg_risk_score_pct}%</span>
                  </div>
                </div>

                <h3 style={{ fontSize: 15, color: "#1e3a8a", borderBottom: "1px solid #cbd5e1", paddingBottom: 6, margin: "20px 0 10px 0" }}>
                  🚨 High-Risk Exception Worklist (Top Interventions Required)
                </h3>
                <table className="erp-table" style={{ fontSize: 12, marginBottom: 20 }}>
                  <thead>
                    <tr>
                      <th>Ref</th>
                      <th>Carrier</th>
                      <th>Route</th>
                      <th>Mode</th>
                      <th>ETA</th>
                      <th>Risk %</th>
                      <th>Disruption Event</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportSummary.high_risk_exceptions.map((ex) => (
                      <tr key={ex.id}>
                        <td style={{ fontWeight: 700, color: "#1e40af" }}>{ex.ref}</td>
                        <td>{ex.carrier}</td>
                        <td>{ex.route}</td>
                        <td>{ex.mode}</td>
                        <td>{ex.eta}</td>
                        <td style={{ fontWeight: 800, color: "#dc2626" }}>{ex.score_pct}%</td>
                        <td style={{ fontSize: 11, color: "#64748b" }}>{ex.disruption || "Transit variance alert"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <h3 style={{ fontSize: 15, color: "#1e3a8a", borderBottom: "1px solid #cbd5e1", paddingBottom: 6, margin: "20px 0 10px 0" }}>
                  🚢 Carrier SLA & Reliability Summary
                </h3>
                <table className="erp-table" style={{ fontSize: 12, marginBottom: 20 }}>
                  <thead>
                    <tr>
                      <th>Carrier Name</th>
                      <th>Code</th>
                      <th>Volume</th>
                      <th>Delays</th>
                      <th>On-Time SLA %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportSummary.carrier_scorecards.map((c) => (
                      <tr key={c.carrier_code}>
                        <td style={{ fontWeight: 700 }}>{c.carrier_name}</td>
                        <td>{c.carrier_code}</td>
                        <td>{c.total_shipments}</td>
                        <td>{c.delayed_count}</td>
                        <td style={{ fontWeight: 800 }}>{c.on_time_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div style={{ marginTop: 30, paddingTop: 16, borderTop: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between", fontSize: 11, color: "#94a3b8" }}>
                  <div>Confidential · Internal Freight Forwarding Operations Use Only</div>
                  <div>Approved by Operations Management</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating AI Assistant Widget */}
      <ChatWidget client={client} />
    </div>

  );
}

/* ==========================================================================
   AI CO-PILOT CHAT WIDGET (MATCHING HOME PAGE THEME)
   ========================================================================== */

function ChatWidget({ client }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "👋 Hello! I am your ShipGuard AI Co-Pilot powered by Google Gemini. Ask me about shipment risks, carrier performance, or request a delay notification email draft!"
    }
  ]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (open) messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  async function sendQuery(queryText) {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const newMessages = [...messages, { role: "user", content: textToSend }];
    setMessages(newMessages);
    if (!queryText) setInput("");
    setLoading(true);

    try {
      const res = await client.request("/ai/chat", {
        method: "POST",
        body: JSON.stringify({ messages: newMessages.map((m) => ({ role: m.role, content: m.content })) }),
      });
      setMessages([...newMessages, { role: "assistant", content: res.reply || "No response received." }]);
    } catch (e) {
      setMessages([...newMessages, { role: "assistant", content: `⚠️ Error: ${e.message || "Failed to reach AI assistant."}` }]);
    } finally {
      setLoading(false);
    }
  }

  const promptPills = [
    "🚨 Summarize High Risk",
    "🚢 Carrier Delay Summary",
    "✉️ Draft Delay Email",
    "💡 Route Mitigations"
  ];

  return (
    <>
      <button className="erp-chat-fab" onClick={() => setOpen(!open)}>
        <Sparkles size={18} />
        <span>ShipGuard AI</span>
      </button>

      {open && (
        <div className="erp-chat-window">
          <div className="erp-chat-header">
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <Bot size={22} />
              <div>
                <strong style={{ fontSize: 14, display: "block" }}>ShipGuard AI Co-Pilot</strong>
                <span style={{ fontSize: 11, background: "rgba(255, 255, 255, 0.2)", padding: "2px 6px", borderRadius: 4 }}>
                  gemini-3.6-flash
                </span>
              </div>
            </div>
            <button className="ghost-btn" style={{ color: "#ffffff", padding: 4 }} onClick={() => setOpen(false)}>
              <X size={18} />
            </button>
          </div>

          <div className="erp-chat-messages">
            {messages.map((m, idx) => (
              <div key={idx} className={`erp-chat-bubble ${m.role}`}>
                {m.content}
              </div>
            ))}
            {loading && (
              <div className="erp-chat-bubble assistant" style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Loader2 size={14} className="spin" /> Analyzing logistics model...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, padding: "8px 12px", background: "#ffffff", borderTop: "1px solid #e2e8f0" }}>
            {promptPills.map((pill) => (
              <button
                key={pill}
                className="secondary-btn"
                style={{ height: 26, fontSize: 11, padding: "0 8px" }}
                onClick={() => sendQuery(pill)}
              >
                {pill}
              </button>
            ))}
          </div>

          <form style={{ display: "flex", gap: 8, padding: 12, background: "#ffffff", borderTop: "1px solid #e2e8f0" }} onSubmit={(e) => { e.preventDefault(); sendQuery(); }}>
            <input
              placeholder="Ask AI about shipments, risks, or draft emails..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <button className="primary-btn" type="submit" disabled={!input.trim() || loading} style={{ width: 38, height: 38, padding: 0, justifyContent: "center" }}>
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}

/* ==========================================================================
   APP ROUTER
   ========================================================================== */

function App() {
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

createRoot(document.getElementById("root")).render(<App />);
