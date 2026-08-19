import React from "react";

export default function RiskMeter({ score, tier }) {
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
