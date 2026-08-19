import React from "react";
import { Anchor, CloudSun, DollarSign } from "lucide-react";

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

export default function LanesView({ externalIntel }) {
  return (
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
  );
}
