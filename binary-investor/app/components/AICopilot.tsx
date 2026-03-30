"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Loader2, ExternalLink } from "lucide-react";
import type { ChatMessage, AnalysisResult } from "@/app/lib/types";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  result: AnalysisResult | null;
}

const API = process.env.NEXT_PUBLIC_API_URL || "";

export default function AICopilotPanel({ result }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: ChatMessage = { role: "user", content: text.trim() };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setLoading(true);

    try {
      const context = result
        ? `Analyzing: ${result.quote.name} (${result.quote.symbol})
Price: ${result.quote.price} | Change: ${result.quote.changePct?.toFixed(2)}%
Regime: ${result.regime.current} | Signal: ${result.signal.action} (${(result.signal.confidence * 100).toFixed(0)}%)
Sentiment: ${result.sentiment.label} (${result.sentiment.score.toFixed(2)})
Volatility Risk: ${result.volatility.riskLevel} | Forecasted: ${(result.volatility.forecasted * 100).toFixed(1)}%
RSI: ${result.indicators.momentum?.rsi?.rsi?.toFixed(1)} | MACD: ${result.indicators.trend?.macd?.crossover}
Herding: ${result.herding.herdingDetected ? "DETECTED" : "Not detected"}`
        : "";

      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updated.map((m) => ({ role: m.role, content: m.content })),
          context,
          symbol: result?.quote.symbol,
        }),
      });
      const data = await res.json();
      setMessages([...updated, { role: "assistant", content: data.response }]);
    } catch {
      setMessages([...updated, { role: "assistant", content: "⚠️ Could not reach AI server." }]);
    }
    setLoading(false);
  };

  const quickActions = result ? [
    { label: "📊 Should I buy?", prompt: `Based on the analysis of ${result.quote.name}: regime is ${result.regime.current}, signal is ${result.signal.action} with ${(result.signal.confidence * 100).toFixed(0)}% confidence. Should I take a position?` },
    { label: "🎯 Explain the signal", prompt: `Break down why ${result.quote.name} is showing a ${result.signal.action} signal. Include the key indicators driving this.` },
    { label: "⚠️ What's the risk?", prompt: `What are the key risks for ${result.quote.name}? Volatility is ${result.volatility.riskLevel}, panic score is ${result.indicators.behavioral?.panicScore?.panicScore?.toFixed(0)}/100.` },
  ] : [
    { label: "📈 How to read signals?", prompt: "How do I interpret BUY/SELL/HOLD signals and what should I consider before acting on them?" },
    { label: "🛡️ Risk management", prompt: "What are the key risk management principles every trader should follow?" },
    { label: "🌍 Global diversification", prompt: "How should I think about diversifying across Indian, US, and European stocks?" },
  ];

  return (
    <div className="card flex flex-col" style={{ height: 460 }}>
      {/* Header */}
      <div style={{
        padding: "14px 18px",
        borderBottom: "1px solid var(--border)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: "var(--accent-soft)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <Sparkles size={14} style={{ color: "var(--accent)" }} />
          </div>
          <div>
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 13, color: "var(--text)" }}>TradeOS AI</div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>llama-3.3-70b</div>
          </div>
        </div>
        <Link href="/copilot" style={{ display: "flex", alignItems: "center", gap: 4, textDecoration: "none" }}>
          <span style={{ fontSize: 11, color: "var(--accent)", fontWeight: 500 }}>Full Chat</span>
          <ExternalLink size={11} style={{ color: "var(--accent)" }} />
        </Link>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px 8px", display: "flex", flexDirection: "column", gap: 10 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", paddingTop: 12 }}>
            <Sparkles size={22} style={{ color: "var(--accent)", margin: "0 auto 8px", opacity: 0.4 }} />
            <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 10, lineHeight: 1.5 }}>
              {result ? `Ask about ${result.quote.name}` : "Select a stock to get insights"}
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              {quickActions.map((a) => (
                <button
                  key={a.label}
                  onClick={() => send(a.prompt)}
                  className="card-sunken"
                  style={{
                    padding: "8px 12px", cursor: "pointer", border: "1px solid var(--border)",
                    textAlign: "left", fontSize: 12, color: "var(--text-secondary)",
                    transition: "all 0.15s ease", fontFamily: "var(--font-body)",
                    borderRadius: 8,
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = "var(--accent-soft)")}
                  onMouseLeave={e => (e.currentTarget.style.background = "")}
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "chat-user" : "chat-ai"}
            style={{ padding: "10px 14px", fontSize: 12, lineHeight: 1.6, maxWidth: "90%", alignSelf: m.role === "user" ? "flex-end" : "flex-start", fontFamily: "var(--font-body)" }}>
            {m.role === "assistant" && (
              <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 3 }}>
                <Sparkles size={10} style={{ color: "var(--accent)" }} />
                <span style={{ fontSize: 9, fontWeight: 700, color: "var(--accent)", letterSpacing: "0.06em", textTransform: "uppercase" }}>TradeOS AI</span>
              </div>
            )}
            {m.role === "assistant" ? (
              <div className="markdown-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown></div>
            ) : (
              <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-ai" style={{ padding: "10px 14px", display: "flex", alignItems: "center", gap: 8, alignSelf: "flex-start" }}>
            <Loader2 size={12} className="spin-slow" style={{ color: "var(--accent)" }} />
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Thinking...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "10px 14px", borderTop: "1px solid var(--border)" }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
            placeholder="Ask anything..."
            className="glass-inset"
            style={{
              flex: 1, padding: "9px 14px", fontSize: 12,
              color: "var(--text)", outline: "none", border: "1px solid transparent",
              fontFamily: "var(--font-body)", borderRadius: 8,
              transition: "border-color 0.15s ease",
            }}
            onFocus={e => (e.currentTarget.style.borderColor = "var(--accent)")}
            onBlur={e => (e.currentTarget.style.borderColor = "transparent")}
          />
          <button onClick={() => send(input)} disabled={!input.trim() || loading}
            className="btn-primary" style={{ padding: "9px 14px", borderRadius: 8, flexShrink: 0 }}>
            <Send size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}