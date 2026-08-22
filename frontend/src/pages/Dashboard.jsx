import React, { lazy, Suspense, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle, Anchor, Boxes, CalendarClock, FileText, Globe,
  LayoutDashboard, Loader2, LogOut, PackagePlus, RefreshCcw, Search,
  ShieldCheck, Sparkles, Truck, X
} from "lucide-react";
import { api, API_BASE } from "../api/client";
import RiskBadge from "../components/RiskBadge";
import RiskMeter from "../components/RiskMeter";

const IntakeModal = lazy(() => import("../components/IntakeModal"));
const ReportModal = lazy(() => import("../components/ReportModal"));
const ShipmentDrawer = lazy(() => import("../components/ShipmentDrawer"));
const ChatWidget = lazy(() => import("../components/ChatWidget"));
const LanesView = lazy(() => import("../components/LanesView"));
const ReportsView = lazy(() => import("../components/ReportsView"));

function ComponentFallback() {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 40, color: "#64748b", gap: 8 }}>
      <Loader2 size={18} className="spin" />
      <span>Loading module...</span>
    </div>
  );
}

export default function Dashboard({ token, onLogout, onNavigateHome }) {
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
      if (err.status === 401 || (err.message && err.message.toLowerCase().includes("token"))) {
        onLogout();
        return;
      }
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

              {/* Seed AI Data feature preserved but hidden from frontend UI */}
              {false && (
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
              )}

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
            <Suspense fallback={<ComponentFallback />}>
              <ReportsView
                reportSummary={reportSummary}
                exportLoading={exportLoading}
                downloadCSV={downloadCSV}
                onOpenReportModal={() => {
                  loadReportSummary();
                  setShowReportModal(true);
                }}
              />
            </Suspense>
          ) : activeTab === "external" ? (
            <Suspense fallback={<ComponentFallback />}>
              <LanesView externalIntel={externalIntel} />
            </Suspense>
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
      <Suspense fallback={null}>
        {selected && (
          <ShipmentDrawer
            selected={selected}
            onClose={() => setSelected(null)}
            client={client}
            showToast={showToast}
          />
        )}
      </Suspense>

      {/* New Shipment Modal */}
      <Suspense fallback={null}>
        {intakeOpen && (
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
        )}
      </Suspense>

      {/* Executive PDF Risk Report Modal */}
      <Suspense fallback={null}>
        {showReportModal && (
          <ReportModal
            isOpen={showReportModal}
            onClose={() => setShowReportModal(false)}
            reportSummary={reportSummary}
          />
        )}
      </Suspense>

      {/* Floating AI Assistant Widget */}
      <Suspense fallback={null}>
        <ChatWidget
          client={client}
          shipments={shipments}
          showToast={showToast}
          onOpenShipmentByRef={(ref) => {
            const match = shipments.find((s) => s.shipment_ref.toLowerCase() === ref.toLowerCase());
            if (match) {
              openShipment(match.shipment_id);
              showToast(`Opened inspection drawer for ${ref}`);
            } else {
              showToast(`Shipment ${ref} not in current active page view`);
            }
          }}
        />
      </Suspense>
    </div>
  );
}

