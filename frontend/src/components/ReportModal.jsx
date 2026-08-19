import React from "react";
import { FileText, X } from "lucide-react";

export default function ReportModal({ isOpen, onClose, reportSummary }) {
  if (!isOpen || !reportSummary) return null;

  return (
    <div className="erp-report-modal-overlay" onClick={onClose}>
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
              onClick={onClose}
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
  );
}
