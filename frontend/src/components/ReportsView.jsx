import React from "react";
import { FileText, Loader2, Sparkles } from "lucide-react";

export default function ReportsView({ reportSummary, exportLoading, downloadCSV, onOpenReportModal }) {
  return (
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
            onClick={onOpenReportModal}
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
  );
}
