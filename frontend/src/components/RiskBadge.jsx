import React from "react";

export default function RiskBadge({ tier }) {
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
