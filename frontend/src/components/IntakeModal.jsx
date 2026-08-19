import React, { useState, useEffect } from "react";
import { PackagePlus, X } from "lucide-react";

export default function IntakeModal({ client, carriers, routes, isOpen, onClose, onCreated }) {
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
