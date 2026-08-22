import React, { useState, useEffect, useRef } from "react";
import {
  Bot,
  Loader2,
  Send,
  Sparkles,
  X,
  Copy,
  Check,
  RotateCcw,
  Maximize2,
  Minimize2,
  ExternalLink,
  Mail,
  AlertTriangle,
  Anchor,
  Truck,
  Lightbulb,
} from "lucide-react";

export default function ChatWidget({ client, onOpenShipmentByRef, shipments = [], showToast }) {
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "👋 **Welcome to ShipGuard AI Co-Pilot!**\n\nI am connected to your live logistics stream and Oracle database. I can analyze high-risk delays, audit carrier reliability, check port weather & berth wait times, or draft customer exception notices.",
      suggestions: [
        "🚨 Summarize High Risk",
        "🚢 Carrier Delay Summary",
        "⚓ Rotterdam Port Weather",
        "✉️ Draft Delay Email",
        "💡 Route Mitigations",
      ],
    },
  ]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [messages, open]);

  async function sendQuery(queryText) {
    const textToSend = (queryText || input).trim();
    if (!textToSend || loading) return;

    const newMessages = [...messages, { role: "user", content: textToSend }];
    setMessages(newMessages);
    if (!queryText) setInput("");
    setLoading(true);

    try {
      const res = await client.request("/ai/chat", {
        method: "POST",
        body: JSON.stringify({
          messages: newMessages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      // Generate dynamic follow-up suggestions based on response context
      const replyText = res.reply || "No response received.";
      const dynamicSuggestions = [];
      const lower = replyText.toLowerCase();

      if (lower.includes("high-risk") || lower.includes("exception")) {
        dynamicSuggestions.push("✉️ Draft Delay Email", "💡 Suggest Mitigations");
      }
      if (lower.includes("carrier")) {
        dynamicSuggestions.push("🚨 Summarize High Risk", "🚢 Compare Carrier SLAs");
      }
      if (lower.includes("port") || lower.includes("weather")) {
        dynamicSuggestions.push("⚓ Check Shanghai Weather", "🚨 View Congested Lanes");
      }
      if (dynamicSuggestions.length === 0) {
        dynamicSuggestions.push("🚨 High-Risk Overview", "🚢 Carrier Reliability", "💡 Route Playbook");
      }

      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: replyText,
          model: res.model || "ShipGuard Intelligence Engine",
          suggestions: dynamicSuggestions,
        },
      ]);
    } catch (e) {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `⚠️ **Connection Notice:** ${e.message || "Failed to reach AI service. Please check your network connection."}`,
          suggestions: ["🚨 Retry High Risk", "🚢 Check Carriers"],
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleCopy(text, idx) {
    // Strip markdown formatting for clean clipboard copy
    const cleanText = text.replace(/\*\*/g, "").replace(/\*/g, "");
    navigator.clipboard.writeText(cleanText);
    setCopiedIdx(idx);
    if (showToast) showToast("Copied to clipboard!");
    setTimeout(() => setCopiedIdx(null), 2000);
  }

  function resetChat() {
    setMessages([
      {
        role: "assistant",
        content:
          "👋 **Conversation reset.** How can I assist you with your active shipment operations today?",
        suggestions: [
          "🚨 Summarize High Risk",
          "🚢 Carrier Reliability",
          "✉️ Draft Delay Email",
          "💡 Route Mitigations",
        ],
      },
    ]);
  }

  // Formatter that converts markdown & turns shipment references into clickable interactive chips
  function renderFormattedMessage(content) {
    if (!content) return null;

    // Detect if content is an email template
    const isEmailDraft = content.includes("Draft Delay Exception Notification") || content.includes("**Subject:**");

    // Split text into paragraphs/lines
    const lines = content.split("\n");

    return (
      <div className={`erp-formatted-chat ${isEmailDraft ? "email-draft-container" : ""}`}>
        {lines.map((line, lineIdx) => {
          if (!line.trim()) {
            return <div key={lineIdx} style={{ height: 6 }} />;
          }

          // Format bold and detect shipment references within the line
          const parts = line.split(/(\*\*.*?\*\*)/g);

          return (
            <div key={lineIdx} className="erp-chat-line">
              {parts.map((part, partIdx) => {
                if (part.startsWith("**") && part.endsWith("**")) {
                  const boldText = part.slice(2, -2);
                  return (
                    <strong key={partIdx} style={{ fontWeight: 700, color: "inherit" }}>
                      {renderShipmentReferences(boldText)}
                    </strong>
                  );
                }
                return <span key={partIdx}>{renderShipmentReferences(part)}</span>;
              })}
            </div>
          );
        })}
      </div>
    );
  }

  // Scan text for references like SHP-2026-A0001 or SHP-xxxx and make them interactive
  function renderShipmentReferences(text) {
    if (!text || typeof text !== "string") return text;

    const regex = /(SHP-[A-Z0-9-]+)/gi;
    const pieces = text.split(regex);

    if (pieces.length === 1) return text;

    return pieces.map((piece, i) => {
      if (piece.match(/^SHP-[A-Z0-9-]+$/i)) {
        const refUpper = piece.toUpperCase();
        return (
          <button
            key={i}
            className="erp-chat-shipment-chip"
            title={`Click to inspect ${refUpper}`}
            onClick={(e) => {
              e.stopPropagation();
              if (onOpenShipmentByRef) {
                onOpenShipmentByRef(refUpper);
              } else {
                sendQuery(`Inspect shipment ${refUpper}`);
              }
            }}
          >
            <span>{refUpper}</span>
            <ExternalLink size={11} style={{ marginLeft: 3, opacity: 0.7 }} />
          </button>
        );
      }
      return piece;
    });
  }

  const primaryActions = [
    { label: "🚨 High Risk", query: "Summarize High Risk", icon: AlertTriangle },
    { label: "🚢 Carriers", query: "Analyze carrier reliability", icon: Truck },
    { label: "⚓ Weather", query: "Check Rotterdam port weather and congestion", icon: Anchor },
    { label: "✉️ Draft Email", query: "Draft a delay notification email", icon: Mail },
    { label: "💡 Playbook", query: "Suggest route mitigations", icon: Lightbulb },
  ];

  return (
    <>
      {/* Floating Action Trigger Button */}
      <button
        className="erp-chat-fab"
        onClick={() => setOpen(!open)}
        title="Open ShipGuard AI Logistics Assistant"
      >
        <Sparkles size={18} />
        <span>ShipGuard AI</span>
        <span className="erp-chat-status-pulse" />
      </button>

      {/* Interactive Chat Window */}
      {open && (
        <div className={`erp-chat-window ${expanded ? "expanded" : ""}`}>
          {/* Header */}
          <div className="erp-chat-header">
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div className="erp-chat-avatar">
                <Bot size={20} />
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <strong style={{ fontSize: 14 }}>ShipGuard AI Co-Pilot</strong>
                  <span className="erp-badge-live">● Live</span>
                </div>
                <span style={{ fontSize: 11, opacity: 0.85 }}>
                  Gemini & Logistics Intelligence Engine
                </span>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <button
                className="ghost-btn-light"
                title="Reset conversation"
                onClick={resetChat}
              >
                <RotateCcw size={15} />
              </button>
              <button
                className="ghost-btn-light"
                title={expanded ? "Restore size" : "Expand window"}
                onClick={() => setExpanded(!expanded)}
              >
                {expanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
              </button>
              <button
                className="ghost-btn-light"
                title="Close chat"
                onClick={() => setOpen(false)}
              >
                <X size={17} />
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="erp-chat-messages">
            {messages.map((m, idx) => (
              <div key={idx} className={`erp-chat-message-row ${m.role}`}>
                <div className={`erp-chat-bubble ${m.role}`}>
                  {renderFormattedMessage(m.content)}

                  {/* Assistant Message Actions & Suggestions */}
                  {m.role === "assistant" && (
                    <div className="erp-chat-bubble-footer">
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", marginBottom: 4 }}>
                        <button
                          className="erp-chat-copy-btn"
                          onClick={() => handleCopy(m.content, idx)}
                          title="Copy text"
                        >
                          {copiedIdx === idx ? (
                            <>
                              <Check size={12} style={{ color: "#10b981" }} />
                              <span>Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy size={12} />
                              <span>Copy</span>
                            </>
                          )}
                        </button>

                        {m.model && (
                          <span style={{ fontSize: 10, color: "#64748b", fontWeight: 500 }}>
                            ⚡ {m.model}
                          </span>
                        )}
                      </div>

                      {m.suggestions && m.suggestions.length > 0 && (
                        <div className="erp-chat-suggestions-container">
                          {m.suggestions.map((sug, sIdx) => (
                            <button
                              key={sIdx}
                              className="erp-chat-suggestion-pill"
                              onClick={() => sendQuery(sug)}
                            >
                              {sug}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="erp-chat-message-row assistant">
                <div className="erp-chat-bubble assistant loading">
                  <Loader2 size={15} className="spin" style={{ color: "#1e40af" }} />
                  <span>Analyzing live telemetry & risk vectors...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Action Pills Bar */}
          <div className="erp-chat-quick-actions">
            {primaryActions.map((action) => {
              const IconComp = action.icon;
              return (
                <button
                  key={action.label}
                  className="erp-chat-quick-pill"
                  onClick={() => sendQuery(action.query)}
                  disabled={loading}
                >
                  <IconComp size={12} />
                  <span>{action.label}</span>
                </button>
              );
            })}
          </div>

          {/* Interactive Chat Input */}
          <form
            className="erp-chat-input-form"
            onSubmit={(e) => {
              e.preventDefault();
              sendQuery();
            }}
          >
            <input
              ref={inputRef}
              placeholder="Ask about risks, carriers, ports, or shipment ref..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendQuery();
                }
              }}
            />
            <button
              className="primary-btn"
              type="submit"
              disabled={!input.trim() || loading}
              style={{ width: 40, height: 40, padding: 0, justifyContent: "center", borderRadius: 8 }}
              title="Send query (Enter)"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}

