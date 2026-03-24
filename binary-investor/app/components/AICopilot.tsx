"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";
import type { ChatMessage, StockQuote } from "@/app/lib/types";

interface Props {
  quote: StockQuote | null;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AICopilot({ quote }: Props) {
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
      const context = quote
        ? `Stock: ${quote.name} (${quote.symbol})\nPrice: ₹${quote.price}\nChange: ${quote.changePct}%\nP/E: ${quote.peRatio}\nMarket Cap: ₹${quote.marketCap}`
        : "";

      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updated.map((m) => ({ role: m.role, content: m.content })),
          context,
        }),
      });
      const data = await res.json();
      setMessages([...updated, { role: "assistant", content: data.response }]);
    } catch {
      setMessages([
        ...updated,
        { role: "assistant", content: "⚠️ Could not reach AI server." },
      ]);
    }
    setLoading(false);
  };

  const quickActions = [
    { label: "🐑 Am I being a sheep?", prompt: `I'm thinking of buying ${quote?.name || "this stock"} because everyone is talking about it. Am I falling into herd mentality?` },
    { label: "😰 Should I panic?", prompt: `${quote?.name || "My stock"} has been falling. Should I sell?` },
    { label: "💰 SIP strategy", prompt: `Explain why a SIP in ${quote?.name || "this stock"} might beat market timing.` },
    { label: "📊 Full analysis", prompt: `Give me a full behavioral analysis of ${quote?.name || "this stock"} for Indian investors.` },
  ];

  return (
    <div className="glass-static overflow-hidden flex flex-col" style={{ height: "480px" }}>
      {/* Header */}
      <div className="px-5 py-3 border-b border-white/5 flex items-center gap-2">
        <Sparkles size={16} className="text-[var(--accent)]" />
        <span className="text-sm font-semibold">AI Financial Copilot</span>
        <span className="text-[10px] text-[var(--text-muted)] ml-auto font-mono">
          llama-3.3-70b
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <Sparkles size={28} className="text-[var(--accent)] mx-auto mb-3 opacity-50" />
            <p className="text-sm text-[var(--text-muted)] mb-4">
              Ask me anything about behavioral biases, Indian stocks, or investment strategies
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {quickActions.map((a) => (
                <button
                  key={a.label}
                  onClick={() => send(a.prompt)}
                  className="text-xs px-3 py-1.5 rounded-full border border-white/8 hover:border-[var(--accent)]/30 hover:bg-[var(--accent-glow)] transition-colors cursor-pointer"
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
              m.role === "user" ? "chat-user ml-8" : "chat-ai mr-8"
            }`}
          >
            {m.content}
          </div>
        ))}

        {loading && (
          <div className="chat-ai mr-8 px-4 py-3 flex items-center gap-2">
            <Loader2 size={14} className="animate-spin text-[var(--accent)]" />
            <span className="text-sm text-[var(--text-muted)]">Thinking...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-white/5">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            placeholder="Ask about biases, stocks, or strategies..."
            className="flex-1 bg-white/[0.03] border border-white/6 rounded-xl px-4 py-2.5 text-sm text-[var(--text)] placeholder-[var(--text-dim)] outline-none focus:border-[var(--accent)]/40 transition-colors"
          />
          <button
            onClick={() => send(input)}
            disabled={!input.trim() || loading}
            className="p-2.5 rounded-xl bg-[var(--accent)] text-white disabled:opacity-30 hover:brightness-110 transition-all cursor-pointer"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
