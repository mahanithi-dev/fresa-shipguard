import React, { useState } from "react";
import { Bot, Check, Copy, Loader2, Sparkles, X } from "lucide-react";
import RiskBadge from "./RiskBadge";

export default function ShipmentDrawer({ selected, onClose, client, showToast }) {
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");
  const [aiCopied, setAiCopied] = useState(false);

  if (!selected) return null;

  return (
    <>
      <div className={`erp-drawer-overlay ${selected ? "open" : ""}`} onClick={onClose} />
      <aside className={`erp-drawer ${selected ? "open" : ""}`}>
        <div className="erp-drawer-header">
          <div>
            <span className="status-tag in_transit" style={{ marginBottom: 4, display: "inline-block" }}>
              {selected.status}
            </span>
            <h3>{selected.shipment_ref}</h3>
          </div>
          <button className="ghost-btn" onClick={onClose}>
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
              {(selected.history || []).map((event) => (
                <div key={event.history_id} style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #f1f5f9", paddingBottom: 6, fontSize: 13 }}>
                  <span>{event.event_type}</span>
                  <time style={{ color: "#64748b", fontSize: 12 }}>{new Date(event.event_ts).toLocaleDateString()}</time>
                </div>
              ))}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
