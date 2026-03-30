"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp, TrendingDown, Activity, BarChart2,
  Brain, Zap, AlertTriangle, CheckCircle2, ChevronRight,
  Info, Loader2, RefreshCw, Sparkles, Target,
  ArrowUpRight, ArrowDownRight, Sun, Moon, Shield, Clock, Eye,
} from "lucide-react";
import Link from "next/link";
import StockSelector from "@/app/components/StockSelector";
import AICopilotPanel from "@/app/components/AICopilot";
import {
  CandlestickChart, VolumeBarChart, PriceAreaChart,
  CSADScatterPlot, PanicVolumeChart, ZScoreChart,
} from "@/app/components/Charts";
import type { StockInfo, AnalysisResult, TradingDecision } from "@/app/lib/types";

const API = process.env.NEXT_PUBLIC_API_URL || "";

/* ─── Helpers ─── */
function fmtPrice(n: number, symbol: string): string {
  if (!n && n !== 0) return "—";
  if (symbol.endsWith(".NS") || symbol.endsWith(".BO")) return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
  if (symbol.endsWith(".L")) return `£${n.toLocaleString("en-GB", { maximumFractionDigits: 2 })}`;
  if (symbol.endsWith(".DE")) return `€${n.toLocaleString("de-DE", { maximumFractionDigits: 2 })}`;
  if (symbol.endsWith(".T")) return `¥${n.toLocaleString("ja-JP", { maximumFractionDigits: 0 })}`;
  if (symbol.endsWith(".HK")) return `HK$${n.toLocaleString("en-HK", { maximumFractionDigits: 2 })}`;
  return `$${n.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

function fmtPct(n: number, digits = 2): string {
  if (!n && n !== 0) return "—";
  return `${n > 0 ? "+" : ""}${n.toFixed(digits)}%`;
}

function fmtLargeNum(n: number): string {
  if (!n) return "—";
  if (n >= 1e12) return `${(n / 1e12).toFixed(1)}T`;
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n.toFixed(0);
}

/* ─── Section ─── */
function Section({ title, subtitle, icon, children, delay = 0 }: {
  title: string; subtitle?: string; icon?: React.ReactNode;
  children: React.ReactNode; delay?: number;
}) {
  return (
    <div className="card fade-up" style={{ animationDelay: `${delay}s`, opacity: 0 }}>
      <div style={{ padding: "18px 22px 14px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {icon && (
            <div style={{
              width: 30, height: 30, borderRadius: 8,
              background: "var(--accent-soft)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              {icon}
            </div>
          )}
          <div>
            <h2 className="section-title" style={{ fontSize: 16 }}>{title}</h2>
            {subtitle && <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 1 }}>{subtitle}</p>}
          </div>
        </div>
      </div>
      <div style={{ padding: "18px 22px" }}>{children}</div>
    </div>
  );
}

/* ─── Metric Card ─── */
function MetricCard({ label, value, sub, color, icon }: {
  label: string; value: string | number; sub?: string; color?: string; icon?: React.ReactNode;
}) {
  return (
    <div className="metric-card" style={{ padding: "16px 18px" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase", fontFamily: "var(--font-body)" }}>
          {label}
        </span>
        {icon && <span>{icon}</span>}
      </div>
      <div className="num-display" style={{ fontSize: 20, fontWeight: 700, color: color || "var(--text)", lineHeight: 1.1 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, fontFamily: "var(--font-body)" }}>{sub}</div>}
    </div>
  );
}

/* ─── Stat Row ─── */
function StatRow({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="stat-row">
      <span style={{ fontSize: 13, color: "var(--text-secondary)", fontFamily: "var(--font-body)" }}>{label}</span>
      <span className="num-display" style={{ fontSize: 13, fontWeight: 600, color: color || "var(--text)" }}>{value}</span>
    </div>
  );
}

/* ─── Score Ring ─── */
function ScoreRing({ score, label, color }: { score: number; label: string; color: string }) {
  const clamped = Math.min(100, Math.max(0, score));
  const c = 2 * Math.PI * 44;
  const d = (clamped / 100) * c;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
      <div style={{ position: "relative", width: 100, height: 100 }}>
        <svg width="100" height="100" style={{ transform: "rotate(-90deg)" }}>
          <circle cx="50" cy="50" r="44" fill="none" stroke="var(--border)" strokeWidth="7" />
          <circle cx="50" cy="50" r="44" fill="none" stroke={color} strokeWidth="7"
            strokeDasharray={`${d} ${c}`} strokeLinecap="round"
            style={{ transition: "stroke-dasharray 1s ease" }} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <span className="num-display" style={{ fontSize: 20, fontWeight: 800, color, lineHeight: 1 }}>{clamped.toFixed(0)}</span>
          <span style={{ fontSize: 9, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>/100</span>
        </div>
      </div>
      <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", fontFamily: "var(--font-body)" }}>{label}</span>
    </div>
  );
}

/* ─── Theme Toggle ─── */
function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    setDark(document.documentElement.getAttribute("data-theme") === "dark");
  }, []);
  const toggle = () => {
    const next = !dark;
    setDark(next);
    if (next) {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem("tradeos-theme", "dark");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("tradeos-theme", "light");
    }
  };
  return (
    <button className="theme-toggle" onClick={toggle} aria-label="Toggle theme">
      {dark ? <Sun size={16} style={{ color: "var(--text-muted)" }} /> : <Moon size={16} style={{ color: "var(--text-muted)" }} />}
    </button>
  );
}

/* ─── Navbar ─── */
function Navbar() {
  return (
    <nav className="navbar" style={{ padding: "0 24px" }}>
      <div style={{ maxWidth: 1320, margin: "0 auto", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Activity size={16} style={{ color: "var(--accent-text)" }} />
          </div>
          <div>
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 16, color: "var(--text)", lineHeight: 1 }}>TradeOS</div>
            <div style={{ fontSize: 9, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase" }}>Intelligence Platform</div>
          </div>
        </Link>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Link href="/copilot" style={{ padding: "6px 14px", borderRadius: 8, fontSize: 13, fontWeight: 500, color: "var(--accent)", textDecoration: "none", background: "var(--accent-soft)", display: "flex", alignItems: "center", gap: 5 }}>
            <Sparkles size={12} /> AI Chat
          </Link>
          <ThemeToggle />
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--up)" }} className="pulse-soft" />
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Live</span>
          </div>
        </div>
      </div>
    </nav>
  );
}

/* ─── Footer ─── */
function Footer() {
  return (
    <footer className="footer" style={{ padding: "36px 24px 28px" }}>
      <div style={{ maxWidth: 1320, margin: "0 auto" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 40, marginBottom: 28 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <div style={{ width: 24, height: 24, borderRadius: 6, background: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Activity size={12} style={{ color: "var(--accent-text)" }} />
              </div>
              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 14, color: "var(--text)" }}>TradeOS</span>
            </div>
            <p style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.6 }}>
              Institutional-grade stock intelligence with 40+ technical indicators and AI-powered trading decisions.
            </p>
          </div>
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Analysis</p>
            {["40+ Technical Indicators", "5-Model AI Pipeline", "Multi-Timeframe Confluence", "Paper Trading", "Behavioral Finance"].map(item => (
              <p key={item} style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 5 }}>{item}</p>
            ))}
          </div>
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Coverage</p>
            {["50 Indian Stocks (NSE)", "60 US Stocks (NYSE/NASDAQ)", "15 UK Stocks (LSE)", "15 European (XETRA)", "20 Asian + 10 ETFs"].map(item => (
              <p key={item} style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 5 }}>{item}</p>
            ))}
          </div>
        </div>
        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 16, display: "flex", justifyContent: "space-between" }}>
          <p style={{ fontSize: 11, color: "var(--text-dim)" }}>© 2026 TradeOS · Not financial advice</p>
          <p style={{ fontSize: 11, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>v2.0</p>
        </div>
      </div>
    </footer>
  );
}

/* ═══════════════════════════════════════════════════
   MAIN DASHBOARD
   ═══════════════════════════════════════════════════ */
export default function DashboardPage() {
  const [selected, setSelected] = useState<StockInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [decision, setDecision] = useState<TradingDecision | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"candle" | "area">("candle");

  const analyze = async (stock: StockInfo) => {
    setSelected(stock);
    setLoading(true);
    setError(null);
    setResult(null);
    setDecision(null);

    try {
      const [analysisRes, decisionRes] = await Promise.allSettled([
        fetch(`${API}/api/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symbol: stock.symbol }),
        }),
        fetch(`${API}/api/decision/${encodeURIComponent(stock.symbol)}`, { method: "POST" }),
      ]);

      if (analysisRes.status === "fulfilled" && analysisRes.value.ok) {
        const data: AnalysisResult = await analysisRes.value.json();
        setResult(data);
      } else {
        throw new Error("Analysis failed");
      }

      if (decisionRes.status === "fulfilled" && decisionRes.value.ok) {
        const dec: TradingDecision = await decisionRes.value.json();
        setDecision(dec);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch data.");
    }
    setLoading(false);
  };

  const quote = result?.quote;
  const isUp = (quote?.changePct || 0) >= 0;
  const sym = selected?.symbol || "";

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Navbar />

      {/* Hero */}
      <div style={{ background: "var(--bg-sunken)", borderBottom: "1px solid var(--border)", padding: "40px 24px" }}>
        <div style={{ maxWidth: 1320, margin: "0 auto" }}>
          <div className="fade-up delay-1">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <span className="badge badge-info">40+ Indicators</span>
              <span className="badge badge-neutral">200 Global Stocks</span>
              <span className="badge badge-neutral">AI Decisions</span>
            </div>
            <h1 style={{
              fontFamily: "var(--font-display)", fontWeight: 800,
              fontSize: "clamp(26px, 3.5vw, 40px)", color: "var(--text)",
              lineHeight: 1.1, letterSpacing: "-0.03em", marginBottom: 10,
            }}>
              Institutional-grade<br/>
              <span style={{ color: "var(--accent)" }}>stock intelligence.</span>
            </h1>
            <p style={{ fontSize: 15, color: "var(--text-secondary)", maxWidth: 520, lineHeight: 1.6 }}>
              AI-powered analysis with BUY/SELL/HOLD decisions, precise entry points, stop-loss, and target prices across global markets.
            </p>
          </div>

          <div className="fade-up delay-3" style={{ marginTop: 28, display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
            <StockSelector selected={selected} onSelect={analyze} />
            {loading && (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Loader2 size={16} className="spin-slow" style={{ color: "var(--accent)" }} />
                <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Running analysis pipeline...</span>
              </div>
            )}
          </div>

          {error && (
            <div className="fade-in" style={{
              marginTop: 14, padding: "10px 16px", borderRadius: 10,
              background: "var(--down-soft)", border: "1px solid var(--down-border)",
              display: "flex", alignItems: "center", gap: 8,
            }}>
              <AlertTriangle size={14} style={{ color: "var(--down)", flexShrink: 0 }} />
              <span style={{ fontSize: 13, color: "var(--down)" }}>{error}</span>
            </div>
          )}
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div style={{ maxWidth: 1320, margin: "28px auto", padding: "0 24px", width: "100%" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 20 }}>
            {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 90, borderRadius: 16 }} />)}
          </div>
          <div className="skeleton" style={{ height: 400, borderRadius: 16 }} />
        </div>
      )}

      {/* ══════════ RESULTS ══════════ */}
      {result && quote && !loading && (
        <div style={{ maxWidth: 1320, margin: "28px auto", padding: "0 24px 60px", width: "100%", display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Stock Header */}
          <div className="card fade-up delay-1" style={{ padding: "22px 24px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <div style={{
                  width: 48, height: 48, borderRadius: 12,
                  background: isUp ? "var(--up-soft)" : "var(--down-soft)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  {isUp ? <TrendingUp size={22} style={{ color: "var(--up)" }} /> : <TrendingDown size={22} style={{ color: "var(--down)" }} />}
                </div>
                <div>
                  <div style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 20, color: "var(--text)", lineHeight: 1 }}>{quote.name}</div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 3, fontFamily: "var(--font-mono)", display: "flex", gap: 6, alignItems: "center" }}>
                    <span>{sym}</span>
                    <span style={{ color: "var(--border)" }}>·</span>
                    <span>{quote.sector}</span>
                    <span style={{ color: "var(--border)" }}>·</span>
                    <span>{quote.exchange}</span>
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <div style={{ textAlign: "right" }}>
                  <div className="num-display" style={{ fontSize: 28, fontWeight: 800, color: "var(--text)", lineHeight: 1 }}>
                    {fmtPrice(quote.price, sym)}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end", marginTop: 3 }}>
                    {isUp ? <ArrowUpRight size={13} style={{ color: "var(--up)" }} /> : <ArrowDownRight size={13} style={{ color: "var(--down)" }} />}
                    <span className={`badge ${isUp ? "badge-up" : "badge-down"}`}>{fmtPct(quote.changePct)}</span>
                  </div>
                </div>
                <button className="btn-ghost" onClick={() => analyze(selected!)} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  <RefreshCw size={13} /> Refresh
                </button>
              </div>
            </div>

            {/* Quick stats */}
            <div style={{
              display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 10, marginTop: 18,
              paddingTop: 18, borderTop: "1px solid var(--border)",
            }}>
              {[
                { label: "52W High", value: fmtPrice(quote.week52High, sym) },
                { label: "52W Low", value: fmtPrice(quote.week52Low, sym) },
                { label: "P/E", value: quote.peRatio ? quote.peRatio.toFixed(1) : "—" },
                { label: "Mkt Cap", value: fmtLargeNum(quote.marketCap) },
                { label: "Volume", value: fmtLargeNum(quote.volume) },
                { label: "Day Range", value: `${fmtPrice(quote.dayLow, sym)} – ${fmtPrice(quote.dayHigh, sym)}` },
              ].map(({ label, value }) => (
                <div key={label} style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 10, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 3 }}>{label}</div>
                  <div className="num-display" style={{ fontSize: 13, fontWeight: 700, color: "var(--text)" }}>{value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Decision Card + Key Metrics */}
          <div className="fade-up delay-2" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {/* AI Decision */}
            {decision && (
              <div className={`card decision-${decision.action.toLowerCase().replace("strong_", "")}`} style={{ padding: "22px 24px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 30, height: 30, borderRadius: 8, background: "var(--accent-soft)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Brain size={15} style={{ color: "var(--accent)" }} />
                    </div>
                    <div>
                      <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15, color: "var(--text)" }}>AI Trading Decision</div>
                      <div style={{ fontSize: 10, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Algorithmic Intelligence</div>
                    </div>
                  </div>
                  <span className={`badge ${decision.action.includes("BUY") ? "badge-up" : decision.action.includes("SELL") ? "badge-down" : "badge-warn"}`}
                    style={{ fontSize: 14, padding: "6px 16px", fontWeight: 700 }}>
                    {decision.action.replace("STRONG_", "⚡ ")}
                  </span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 10, marginBottom: 14 }}>
                  <div className="card-sunken" style={{ padding: "10px 12px", textAlign: "center" }}>
                    <div style={{ fontSize: 9, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 3 }}>Entry</div>
                    <div className="num-display" style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>
                      {decision.action === "HOLD" ? "—" : fmtPrice(decision.entry.price, sym)}
                    </div>
                  </div>
                  <div className="card-sunken" style={{ padding: "10px 12px", textAlign: "center" }}>
                    <div style={{ fontSize: 9, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 3 }}>Stop Loss</div>
                    <div className="num-display" style={{ fontSize: 14, fontWeight: 700, color: "var(--down)" }}>
                      {decision.action === "HOLD" ? "—" : fmtPrice(decision.stopLoss, sym)}
                    </div>
                  </div>
                  <div className="card-sunken" style={{ padding: "10px 12px", textAlign: "center" }}>
                    <div style={{ fontSize: 9, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 3 }}>Target 1</div>
                    <div className="num-display" style={{ fontSize: 14, fontWeight: 700, color: "var(--up)" }}>
                      {decision.action === "HOLD" ? "—" : fmtPrice(decision.takeProfit1, sym)}
                    </div>
                  </div>
                  <div className="card-sunken" style={{ padding: "10px 12px", textAlign: "center" }}>
                    <div style={{ fontSize: 9, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: 3 }}>Target 2</div>
                    <div className="num-display" style={{ fontSize: 14, fontWeight: 700, color: "var(--up)" }}>
                      {decision.action === "HOLD" ? "—" : fmtPrice(decision.takeProfit2, sym)}
                    </div>
                  </div>
                </div>
                <StatRow label="Confidence" value={`${(decision.confidence * 100).toFixed(0)}%`} />
                <StatRow label="Position Size" value={decision.action === "HOLD" ? "—" : `${decision.positionSizePct.toFixed(1)}%`} />
                <StatRow label="Risk / Reward" value={decision.action === "HOLD" || decision.riskReward === 0 ? "—" : `1 : ${decision.riskReward.toFixed(1)}`} color={decision.action !== "HOLD" ? "var(--up)" : undefined} />
                <StatRow label="Regime" value={decision.regime.replace(/_/g, " ")} />
                {decision.reasoning && (
                  <div style={{ marginTop: 12, padding: "10px 14px", background: "var(--bg-sunken)", borderRadius: 10, border: "1px solid var(--border-light)" }}>
                    <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>{decision.reasoning}</p>
                  </div>
                )}
              </div>
            )}

            {/* Key Metrics */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <MetricCard
                label="Market Regime"
                value={result.regime.current.replace(/_/g, " ")}
                sub={`${(result.regime.confidence * 100).toFixed(0)}% confidence`}
                color={result.regime.current.includes("BULL") ? "var(--up)" : result.regime.current.includes("BEAR") || result.regime.current.includes("CRISIS") ? "var(--down)" : "var(--warn)"}
                icon={<Eye size={14} style={{ color: "var(--text-muted)" }} />}
              />
              <MetricCard
                label="Signal"
                value={result.signal.action}
                sub={`${(result.signal.confidence * 100).toFixed(0)}% probability`}
                color={result.signal.action === "BUY" ? "var(--up)" : result.signal.action === "SELL" ? "var(--down)" : "var(--warn)"}
                icon={<Target size={14} style={{ color: "var(--text-muted)" }} />}
              />
              <MetricCard
                label="Sentiment"
                value={result.sentiment.label.replace(/_/g, " ")}
                sub={`Score: ${result.sentiment.score.toFixed(2)} · ${result.sentiment.articleCount} articles`}
                color={result.sentiment.score > 0.1 ? "var(--up)" : result.sentiment.score < -0.1 ? "var(--down)" : "var(--text-secondary)"}
                icon={<Sparkles size={14} style={{ color: "var(--text-muted)" }} />}
              />
              <MetricCard
                label="Volatility Risk"
                value={result.volatility.riskLevel}
                sub={`Current: ${(result.volatility.forecasted * 100).toFixed(1)}%`}
                color={result.volatility.riskLevel === "HIGH" ? "var(--down)" : result.volatility.riskLevel === "ELEVATED" ? "var(--warn)" : "var(--up)"}
                icon={<Activity size={14} style={{ color: "var(--text-muted)" }} />}
              />
            </div>
          </div>

          {/* Price Chart + AI Copilot */}
          <div className="fade-up delay-3" style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 20 }}>
            <div className="card">
              <div style={{ padding: "18px 22px 0" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                  <div>
                    <h2 className="section-title" style={{ fontSize: 16 }}>Price Chart</h2>
                    <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 1 }}>{result.chart.length} data points</p>
                  </div>
                  <div className="tab-bar" style={{ minWidth: 150 }}>
                    <button className={`tab-item ${activeTab === "candle" ? "active" : ""}`} onClick={() => setActiveTab("candle")}>Candlestick</button>
                    <button className={`tab-item ${activeTab === "area" ? "active" : ""}`} onClick={() => setActiveTab("area")}>Area</button>
                  </div>
                </div>
              </div>
              <div style={{ padding: "0 10px 8px" }}>
                {activeTab === "candle" ? <CandlestickChart data={result.chart} /> : <PriceAreaChart data={result.chart} />}
              </div>
              <div style={{ padding: "0 10px 14px", borderTop: "1px solid var(--border)" }}>
                <p style={{ fontSize: 10, color: "var(--text-dim)", padding: "6px 10px 2px", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Volume</p>
                <VolumeBarChart data={result.chart} />
              </div>
            </div>
            <AICopilotPanel result={result} />
          </div>

          {/* Technical Indicators Grid */}
          <div className="fade-up delay-4" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
            {/* Trend */}
            <Section title="Trend Analysis" icon={<TrendingUp size={14} style={{ color: "var(--accent)" }} />}>
              <StatRow label="EMA Trend" value={result.indicators.trend.ema.trend.replace(/_/g, " ")}
                color={result.indicators.trend.ema.trend.includes("BULL") ? "var(--up)" : result.indicators.trend.ema.trend.includes("BEAR") ? "var(--down)" : "var(--text)"} />
              <StatRow label="MACD" value={result.indicators.trend.macd.crossover} color={result.indicators.trend.macd.crossover === "BULLISH" ? "var(--up)" : result.indicators.trend.macd.crossover === "BEARISH" ? "var(--down)" : "var(--text)"} />
              <StatRow label="ADX" value={`${result.indicators.trend.adx.adx.toFixed(1)} (${result.indicators.trend.adx.trendStrength})`} />
              <StatRow label="SuperTrend" value={result.indicators.trend.superTrend.signal} color={result.indicators.trend.superTrend.signal === "BUY" ? "var(--up)" : "var(--down)"} />
              <StatRow label="Ichimoku" value={result.indicators.trend.ichimoku.signal.replace(/_/g, " ")} />
              <StatRow label="Parabolic SAR" value={result.indicators.trend.parabolicSar.trend} />
            </Section>

            {/* Momentum */}
            <Section title="Momentum" icon={<Zap size={14} style={{ color: "var(--accent)" }} />}>
              <StatRow label="RSI (14)" value={result.indicators.momentum.rsi.rsi.toFixed(1)}
                color={result.indicators.momentum.rsi.rsi > 70 ? "var(--down)" : result.indicators.momentum.rsi.rsi < 30 ? "var(--up)" : "var(--text)"} />
              <StatRow label="RSI Signal" value={result.indicators.momentum.rsi.signal} />
              <StatRow label="Stochastic %K" value={result.indicators.momentum.stochastic.k.toFixed(1)} />
              <StatRow label="MFI" value={result.indicators.momentum.mfi.mfi.toFixed(1)} />
              <StatRow label="Williams %R" value={result.indicators.momentum.williamsR.williamsR.toFixed(1)} />
              <StatRow label="CCI" value={result.indicators.momentum.cci.cci.toFixed(1)} />
            </Section>

            {/* Volume */}
            <Section title="Volume Analysis" icon={<BarChart2 size={14} style={{ color: "var(--accent)" }} />}>
              <StatRow label="vs VWAP" value={result.indicators.volume.vwap.priceVsVwap}
                color={result.indicators.volume.vwap.priceVsVwap === "ABOVE" ? "var(--up)" : "var(--down)"} />
              <StatRow label="OBV Trend" value={result.indicators.volume.obv.obvTrend}
                color={result.indicators.volume.obv.obvTrend === "RISING" ? "var(--up)" : "var(--down)"} />
              <StatRow label="A/D Line" value={result.indicators.volume.adLine.adTrend} />
              <StatRow label="CMF" value={`${result.indicators.volume.cmf.cmf.toFixed(3)} (${result.indicators.volume.cmf.signal.replace(/_/g, " ")})`} />
              <StatRow label="Relative Vol" value={`${result.indicators.volume.relativeVolume.relativeVolume.toFixed(1)}x`}
                color={result.indicators.volume.relativeVolume.anomaly ? "var(--warn)" : "var(--text)"} />
            </Section>
          </div>

          {/* Behavioral + Volatility */}
          <div className="fade-up delay-5" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {/* Behavioral */}
            <Section title="Behavioral Finance" subtitle="Panic score & herding detection" icon={<Brain size={14} style={{ color: "var(--accent)" }} />}>
              <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 16 }}>
                <ScoreRing
                  score={result.indicators.behavioral.panicScore.panicScore}
                  label="Panic"
                  color={result.indicators.behavioral.panicScore.panicScore > 60 ? "var(--down)" : result.indicators.behavioral.panicScore.panicScore > 35 ? "var(--warn)" : "var(--up)"}
                />
                <div style={{ flex: 1 }}>
                  <span className={`badge ${result.indicators.behavioral.panicScore.panicScore > 60 ? "badge-down" : result.indicators.behavioral.panicScore.panicScore > 35 ? "badge-warn" : "badge-up"}`} style={{ marginBottom: 10, display: "inline-flex" }}>
                    {result.indicators.behavioral.panicScore.level}
                  </span>
                  {Object.entries(result.indicators.behavioral.panicScore.factors || {}).map(([key, value]) => (
                    <div key={key} style={{ marginBottom: 6 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                        <span className="num-display" style={{ fontSize: 11, fontWeight: 600 }}>{(value as number)?.toFixed(1)}</span>
                      </div>
                      <div className="progress-bar">
                        <div className="progress-bar-fill" style={{
                          width: `${Math.min(100, value as number)}%`,
                          background: (value as number) > 60 ? "var(--down)" : (value as number) > 35 ? "var(--warn)" : "var(--up)",
                        }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <StatRow label="Herding" value={result.herding.herdingDetected ? "Detected" : "Not Detected"}
                color={result.herding.herdingDetected ? "var(--down)" : "var(--up)"} />
              <StatRow label="γ₂ Coefficient" value={result.herding.gamma2?.toFixed(4) || "—"} />
              <StatRow label="p-Value" value={result.herding.pValue?.toFixed(4) || "—"} />
            </Section>

            {/* Volatility + Multi-Timeframe */}
            <Section title="Volatility & Timeframes" subtitle="GARCH forecast & multi-TF confluence" icon={<Activity size={14} style={{ color: "var(--accent)" }} />}>
              <StatRow label="Bollinger %B" value={result.indicators.volatility.bollingerBands.percentB.toFixed(3)} />
              <StatRow label="BB Squeeze" value={result.indicators.volatility.bollingerBands.squeeze ? "YES" : "No"} color={result.indicators.volatility.bollingerBands.squeeze ? "var(--warn)" : "var(--text)"} />
              <StatRow label="ATR" value={`${result.indicators.volatility.atr.atr.toFixed(2)} (${result.indicators.volatility.atr.atrPct.toFixed(2)}%)`} />
              <StatRow label="Historical Vol" value={`${result.indicators.volatility.historicalVol.histVol.toFixed(1)}%`} />
              <StatRow label="Vol Ratio" value={result.indicators.volatility.historicalVol.volRatio.toFixed(2)} color={result.indicators.volatility.historicalVol.volRatio > 1.5 ? "var(--down)" : "var(--text)"} />
              <StatRow label="Forecasted Vol" value={`${(result.volatility.forecasted * 100).toFixed(1)}%`} />

              {result.multiTimeframe?.timeframes && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>Multi-Timeframe</div>
                  {Object.entries(result.multiTimeframe.timeframes).map(([tf, signal]) => (
                    <StatRow key={tf} label={tf.toUpperCase()} value={signal as string}
                      color={(signal as string) === "BUY" ? "var(--up)" : (signal as string) === "SELL" ? "var(--down)" : "var(--text-muted)"} />
                  ))}
                  <StatRow label="Consensus" value={result.multiTimeframe.consensus}
                    color={result.multiTimeframe.consensus === "BUY" ? "var(--up)" : result.multiTimeframe.consensus === "SELL" ? "var(--down)" : "var(--warn)"} />
                </div>
              )}
            </Section>
          </div>

          {/* News Sources — transparent article list */}
          {result.sentiment.articles && result.sentiment.articles.length > 0 && (
            <div className="fade-up delay-6">
              <Section title="News Sources" subtitle={`${result.sentiment.articles.length} articles analyzed for sentiment`} icon={<Info size={14} style={{ color: "var(--accent)" }} />}>
                <div style={{ maxHeight: 320, overflowY: "auto" }}>
                  {result.sentiment.articles.map((article: { title: string; source: string; url: string; date: string | number; summary: string }, idx: number) => (
                    <div key={idx} style={{
                      padding: "10px 0",
                      borderBottom: idx < result.sentiment.articles.length - 1 ? "1px solid var(--border)" : "none",
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                        <div style={{ flex: 1 }}>
                          {article.url ? (
                            <a href={article.url} target="_blank" rel="noopener noreferrer"
                              style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", textDecoration: "none", lineHeight: 1.4, display: "block" }}>
                              {article.title || "Untitled Article"}
                            </a>
                          ) : (
                            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", lineHeight: 1.4, display: "block" }}>
                              {article.title || "Untitled Article"}
                            </span>
                          )}
                          <div style={{ display: "flex", gap: 8, marginTop: 4, alignItems: "center" }}>
                            <span style={{ fontSize: 11, color: "var(--accent)", fontWeight: 600 }}>
                              {article.source || "Unknown Source"}
                            </span>
                            {article.date && (
                              <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                                {typeof article.date === 'number'
                                  ? new Date(article.date * 1000).toLocaleDateString()
                                  : new Date(article.date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                          {article.summary && (
                            <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, lineHeight: 1.5 }}>
                              {article.summary}
                            </p>
                          )}
                        </div>
                        {article.url && (
                          <a href={article.url} target="_blank" rel="noopener noreferrer"
                            style={{ flexShrink: 0, color: "var(--accent)" }}>
                            <ArrowUpRight size={14} />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            </div>
          )}

          {/* Disclaimer */}
          <div className="card-sunken fade-up delay-6" style={{ padding: "12px 18px", display: "flex", alignItems: "center", gap: 8 }}>
            <Info size={14} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
            <p style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.5 }}>
              TradeOS v2.0 · All decisions are computed algorithmically using mathematical models and indicator consensus — not AI opinions. Analysis is for educational purposes only and does not constitute financial advice.
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !result && !error && (
        <div style={{ maxWidth: 1320, margin: "48px auto", padding: "0 24px", width: "100%", flex: 1 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
            {[
              { icon: <Target size={24} style={{ color: "var(--accent)" }} />, title: "AI Decisions", desc: "BUY / SELL / HOLD signals with exact entry, stop-loss, and take-profit levels powered by a 5-model AI pipeline." },
              { icon: <BarChart2 size={24} style={{ color: "var(--accent)" }} />, title: "40+ Indicators", desc: "Price action, trend, momentum, volatility, volume, and behavioral indicators computed in real-time." },
              { icon: <Brain size={24} style={{ color: "var(--accent)" }} />, title: "Regime Detection", desc: "Classifies markets into Bull, Bear, Range, or Crisis modes using statistical learning models." },
              { icon: <Shield size={24} style={{ color: "var(--accent)" }} />, title: "Risk Management", desc: "Kelly Criterion position sizing, ATR-based stops, and auto-exit conditions for disciplined trading." },
            ].map(({ icon, title, desc }) => (
              <div key={title} className="card" style={{ padding: "22px" }}>
                <div style={{ marginBottom: 14 }}>{icon}</div>
                <h3 style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15, color: "var(--text)", marginBottom: 6 }}>{title}</h3>
                <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6 }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}