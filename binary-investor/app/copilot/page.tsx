"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send, Sparkles, Loader2, ArrowLeft, MessageCircle,
} from "lucide-react";
import type { ChatMessage } from "@/app/lib/types";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export default function AICopilotPage() {
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
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updated.map((m) => ({ role: m.role, content: m.content })),
          context: "",
        }),
      });
      const data = await res.json();
      setMessages([...updated, { role: "assistant", content: data.response }]);
    } catch {
      setMessages([
        ...updated,
        { role: "assistant", content: "Could not reach AI server. Please ensure the Python backend is running." },
      ]);
    }
    setLoading(false);
  };

  const starters = [
    { icon: "🐑", label: "What is herd mentality in stock markets?", },
    { icon: "😰", label: "How do I avoid panic selling?", },
    { icon: "💰", label: "Why is SIP better than lump sum?", },
    { icon: "📊", label: "Explain the behavior gap for Indian investors", },
    { icon: "🧠", label: "What cognitive biases affect stock investing?", },
    { icon: "📉", label: "How to stay calm during a market crash?", },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav className="navbar px-6 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <ArrowLeft size={18} className="text-[var(--text-secondary)]" />
          <span className="text-sm font-medium text-[var(--text-secondary)]">
            Back to Dashboard
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <MessageCircle size={18} className="text-[var(--accent)]" />
          <span className="text-sm font-bold text-[var(--text)]">AI Copilot</span>
        </div>
        <div className="text-[10px] text-[var(--text-muted)] font-mono">
          llama-3.3-70b
        </div>
      </nav>

      {/* Main chat area */}
      <div className="flex-1 max-w-3xl mx-auto w-full flex flex-col px-4">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto py-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-16">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[var(--accent-light)] mb-4">
                <Sparkles size={28} className="text-[var(--accent)]" />
              </div>
              <h2 className="text-xl font-bold text-[var(--text)] mb-2">
                Ask the AI Copilot anything
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mb-8 max-w-md mx-auto">
                Your personal behavioral finance advisor. Ask about stock biases,
                investment strategies, or market psychology.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg mx-auto">
                {starters.map((s) => (
                  <button
                    key={s.label}
                    onClick={() => send(s.label)}
                    className="glass text-left px-4 py-3 text-sm text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--accent-light)] transition-all cursor-pointer flex items-center gap-2.5"
                    style={{ borderRadius: 14 }}
                  >
                    <span className="text-lg">{s.icon}</span>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={`px-5 py-3.5 text-sm leading-relaxed whitespace-pre-wrap max-w-[85%] ${
                m.role === "user"
                  ? "chat-user ml-auto"
                  : "chat-ai mr-auto"
              }`}
            >
              {m.role === "assistant" && (
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Sparkles size={12} className="text-[var(--accent)]" />
                  <span className="text-[10px] font-semibold text-[var(--accent)] uppercase tracking-wider">
                    AI Copilot
                  </span>
                </div>
              )}
              {m.content}
            </div>
          ))}

          {loading && (
            <div className="chat-ai mr-auto px-5 py-3.5 flex items-center gap-2 max-w-[85%]">
              <Loader2 size={14} className="animate-spin text-[var(--accent)]" />
              <span className="text-sm text-[var(--text-muted)]">Thinking...</span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="py-4 border-t border-[var(--glass-border)]">
          <div className="flex items-center gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
              placeholder="Ask about investing biases, stock strategies..."
              className="flex-1 glass px-5 py-3 text-sm text-[var(--text)] placeholder-[var(--text-muted)] outline-none"
              style={{ borderRadius: 14 }}
            />
            <button
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              className="p-3 rounded-xl bg-[var(--accent)] text-white disabled:opacity-30 hover:brightness-105 transition-all cursor-pointer shrink-0"
            >
              <Send size={16} />
            </button>
          </div>
          <p className="text-[10px] text-[var(--text-muted)] text-center mt-2">
            Powered by Groq · llama-3.3-70b-versatile · Not financial advice
          </p>
        </div>
      </div>
    </div>
  );
}
