"use client";

import { useState } from "react";
import Link from "next/link";
import {
  TrendingUp, TrendingDown, Activity, AlertTriangle,
  BarChart3, Brain, Zap, Loader2, Shield, Target,
  MessageCircle, ChevronRight, Info, CheckCircle2,
  XCircle, ArrowUpRight, ArrowDownRight, Clock,
  DollarSign, PieChart, FileText,
} from "lucide-react";
import StockSelector from "@/app/components/StockSelector";
import {
  CandlestickChart, CSADScatter, VolumeChart,
  MCHistogram, MissingDaysChart,
} from "@/app/components/Charts";
import type { StockInfo, AnalysisResult } from "@/app/lib/types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

/* ═══════ Helpers ═══════ */
function formatINR(v: number): string {
  if (!v) return "₹0";
  if (v >= 1e7) return `₹${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `₹${(v / 1e5).toFixed(2)} L`;
  return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

/* ═══════ Sub-components ═══════ */

function Metric({
  label, value, sub, accent, icon: Icon,
}: {
  label: string; value: string; sub?: string;
  accent?: string; icon?: React.ElementType;
}) {
  return (
    <div className="glass p-5">
      <div className="flex items-center gap-2 mb-1.5">
        {Icon && <Icon size={14} className="text-[var(--text-muted)]" />}
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[var(--text-muted)]">
          {label}
        </span>
      </div>
      <div className="text-2xl font-bold tracking-tight" style={{ color: accent || "var(--text)" }}>
        {value}
      </div>
      {sub && <div className="text-xs text-[var(--text-muted)] mt-1">{sub}</div>}
    </div>
  );
}

function SectionDivider({
  num, title, desc, icon: Icon,
}: {
  num: string; title: string; desc: string; icon: React.ElementType;
}) {
  return (
    <div className="flex items-start gap-4 mb-5 pt-2">
      <div className="flex items-center justify-center w-11 h-11 rounded-2xl bg-[var(--accent-light)] text-[var(--accent)] shrink-0">
        <Icon size={20} />
      </div>
      <div className="flex-1">
        <div className="text-[10px] font-bold text-[var(--accent)] uppercase tracking-[0.15em] mb-0.5">
          Section {num}
        </div>
        <h2 className="text-xl font-bold text-[var(--text)] leading-tight">{title}</h2>
        <p className="text-sm text-[var(--text-secondary)] mt-1 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

function InfoBox({
  title, children, type = "info",
}: {
  title: string; children: React.ReactNode; type?: "info" | "warn" | "up" | "down";
}) {
  const styles = {
    info: "bg-[var(--accent-light)] border-[var(--accent)]/10 text-[var(--accent)]",
    warn: "bg-[var(--warn-bg)] border-[var(--warn)]/10 text-[var(--warn)]",
    up:   "bg-[var(--up-bg)] border-[var(--up)]/10 text-[var(--up)]",
    down: "bg-[var(--down-bg)] border-[var(--down)]/10 text-[var(--down)]",
  };
  return (
    <div className={`${styles[type]} border rounded-2xl px-5 py-4`}>
      <div className="flex items-center gap-2 mb-2">
        <Info size={14} />
        <span className="text-xs font-bold uppercase tracking-wider">{title}</span>
      </div>
      <div className="text-sm text-[var(--text-secondary)] leading-relaxed">{children}</div>
    </div>
  );
}

function ScoreRing({ score, label, color }: { score: number; label: string; color: string }) {
  const angle = Math.min(score / 100, 1) * 360;
  return (
    <div className="flex flex-col items-center">
      <div
        className="score-ring"
        style={{
          background: `conic-gradient(${color} 0deg, ${color} ${angle}deg, rgba(0,0,0,0.04) ${angle}deg)`,
        }}
      >
        <div className="score-ring-inner">
          <span className="text-3xl font-black" style={{ color }}>{score.toFixed(0)}</span>
          <span className="text-[10px] text-[var(--text-muted)]">/100</span>
        </div>
      </div>
      <span className="text-xs font-bold mt-2.5 uppercase tracking-wider" style={{ color }}>
        {label}
      </span>
    </div>
  );
}

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-2 rounded-full bg-black/[0.04] overflow-hidden">
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${Math.min(value, 100)}%`, background: color }}
      />
    </div>
  );
}

/* ═══════════════════════════════════════════════════ */
/* MAIN PAGE                                          */
/* ═══════════════════════════════════════════════════ */

export default function Home() {
  const [selected, setSelected] = useState<StockInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");

  const analyze = async () => {
    if (!selected) return;
    setLoading(true);
    setError("");
    setData(null);
    try {
      const res = await fetch(`${API}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: selected.symbol,
          periodDays: 365,
          sipAmount: 10000,
          simYears: 10,
          nSimulations: 500,
        }),
      });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      setData(await res.json());
    } catch (e: any) {
      setError(e.message || "Could not connect to API server.");
    }
    setLoading(false);
  };

  const q = data?.quote;
  const isUp = q && q.change >= 0;

  /* ─── Build Conclusion ──────────────────────────── */
  function getConclusion() {
    if (!data) return null;
    const { herding, panic, behaviorGap, monteCarlo } = data;

    const verdicts: { icon: React.ReactNode; text: string; type: "up" | "down" | "warn" }[] = [];

    // Herding
    if (herding.herdingDetected) {
      verdicts.push({
        icon: <XCircle size={16} />,
        text: `Herding detected in the ${herding.sector} sector (intensity: ${herding.intensity.toFixed(0)}/100). Investors in this sector are following the crowd — make sure your buy/sell decision is based on fundamentals, not social media buzz.`,
        type: "down",
      });
    } else {
      verdicts.push({
        icon: <CheckCircle2 size={16} />,
        text: `No herding detected in ${herding.sector}. Investors appear to be making independent decisions — a good sign for rational price discovery.`,
        type: "up",
      });
    }

    // Panic
    if (panic.panicScore >= 50) {
      verdicts.push({
        icon: <AlertTriangle size={16} />,
        text: `Panic score is ${panic.panicScore.toFixed(0)}/100 (${panic.level}). High selling pressure detected — avoid impulsive exits. Historically, staying invested during such phases leads to better outcomes.`,
        type: "down",
      });
    } else if (panic.panicScore >= 25) {
      verdicts.push({
        icon: <AlertTriangle size={16} />,
        text: `Moderate panic level (${panic.panicScore.toFixed(0)}/100). Some stress signals visible but not alarming. Stay disciplined with your SIP.`,
        type: "warn",
      });
    } else {
      verdicts.push({
        icon: <CheckCircle2 size={16} />,
        text: `Market is calm (panic score: ${panic.panicScore.toFixed(0)}/100). No significant panic-selling signals detected.`,
        type: "up",
      });
    }

    // Behavior Gap
    if (behaviorGap.behaviorGap > 2) {
      verdicts.push({
        icon: <XCircle size={16} />,
        text: `Behavior gap of ${behaviorGap.behaviorGap.toFixed(2)}% CAGR: the stock returned ${behaviorGap.investmentCagr.toFixed(2)}% but average investors likely earned only ${behaviorGap.investorCagr.toFixed(2)}%. Emotional trading is destroying wealth.`,
        type: "down",
      });
    } else {
      verdicts.push({
        icon: <CheckCircle2 size={16} />,
        text: `Behavior gap is manageable (${behaviorGap.behaviorGap.toFixed(2)}%). Investors are capturing most of the stock's returns.`,
        type: "up",
      });
    }

    // Monte Carlo
    verdicts.push({
      icon: <DollarSign size={16} />,
      text: `SIP beats panic selling in ${monteCarlo.costOfPanic.winRate}% of simulations. Disciplined investing would accumulate ${formatINR(monteCarlo.costOfPanic.meanLoss)} more wealth over ${monteCarlo.years} years.`,
      type: monteCarlo.costOfPanic.pctLoss > 10 ? "down" : "warn",
    });

    // Overall
    const badCount = verdicts.filter((v) => v.type === "down").length;
    let overall: { text: string; type: "up" | "down" | "warn" };
    if (badCount >= 3) {
      overall = {
        text: "Multiple red flags detected. Exercise extreme caution — stick to SIP, avoid emotional decisions, and do not follow the crowd.",
        type: "down",
      };
    } else if (badCount >= 1) {
      overall = {
        text: "Some concerns identified. Stay disciplined, maintain your SIP, and review your portfolio periodically without reacting to short-term noise.",
        type: "warn",
      };
    } else {
      overall = {
        text: "Overall healthy signals. Continue your investment strategy with confidence. Markets may fluctuate but discipline wins long-term.",
        type: "up",
      };
    }

    return { verdicts, overall };
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* ═══════ NAVBAR ═══════ */}
      <nav className="navbar px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-xl">🐑</span>
            <span className="text-base font-bold tracking-tight text-[var(--text)]">
              SheepOrSleep
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/copilot"
              className="flex items-center gap-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
            >
              <MessageCircle size={16} />
              AI Copilot
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener"
              className="text-sm text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
            >
              Docs
            </a>
          </div>
        </div>
      </nav>

      {/* ═══════ HERO ═══════ */}
      <header className="max-w-6xl mx-auto w-full px-6 pt-12 pb-6">
        <div className="max-w-2xl">
          <div className="badge badge-info mb-4">
            <Zap size={12} /> One-Tap Analysis
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--text)] leading-[1.15]">
            AI Behavioral Bias Detector
            <br />
            <span className="text-[var(--accent)]">for Indian Stocks</span>
          </h1>
          <p className="text-base text-[var(--text-secondary)] mt-4 leading-relaxed max-w-xl">
            Select any stock and get a complete behavioral analysis — herding detection,
            panic scoring, behavior gap analysis, and Monte Carlo simulation — all in one click.
          </p>
        </div>

        {/* Selector + Button */}
        <div className="mt-8 flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <StockSelector selected={selected} onSelect={setSelected} />
          <button
            onClick={analyze}
            disabled={!selected || loading}
            className="flex items-center gap-2 px-7 py-3.5 rounded-2xl bg-[var(--accent)] text-white font-semibold text-sm
              disabled:opacity-30 hover:brightness-105 active:scale-[0.98] transition-all cursor-pointer shrink-0 shadow-lg shadow-indigo-500/20"
          >
            {loading ? (
              <><Loader2 size={16} className="animate-spin" /> Analyzing...</>
            ) : (
              <><Zap size={16} /> Generate Report</>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 bg-[var(--down-bg)] border border-[var(--down)]/10 rounded-2xl px-5 py-3 text-sm text-[var(--down)]">
            ⚠️ {error}
          </div>
        )}
      </header>

      {/* ═══════ LOADING STATE ═══════ */}
      {loading && (
        <div className="max-w-6xl mx-auto px-6 py-16 w-full flex flex-col items-center gap-5">
          <Loader2 size={44} className="animate-spin text-[var(--accent)]" />
          <p className="text-sm text-[var(--text-secondary)]">
            Running CCK model, panic detection, Monte Carlo simulation...
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full max-w-2xl">
            {[1, 2, 3, 4].map((i) => <div key={i} className="shimmer h-28" />)}
          </div>
        </div>
      )}

      {/* ═══════ REPORT ═══════ */}
      {data && !loading && (
        <main className="max-w-6xl mx-auto px-6 pb-12 w-full space-y-14">
          {/* ── SECTION 1: Stock Overview ──────────── */}
          <section className="fade-in">
            <SectionDivider
              num="01" icon={TrendingUp}
              title={`${q?.name} Overview`}
              desc={`${q?.sector} · ${selected?.symbol.replace(".NS", "")} · ${selected?.index}`}
            />

            {/* Price cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
              <Metric
                label="Current Price"
                value={`₹${q?.price?.toLocaleString("en-IN")}`}
                sub={`${isUp ? "▲" : "▼"} ₹${Math.abs(q?.change || 0).toFixed(2)} (${q?.changePct?.toFixed(2)}%)`}
                icon={isUp ? TrendingUp : TrendingDown}
                accent={isUp ? "var(--up)" : "var(--down)"}
              />
              <Metric
                label="Volume"
                value={(q?.volume || 0).toLocaleString("en-IN")}
                sub={`Avg: ${(q?.avgVolume || 0).toLocaleString("en-IN")}`}
                icon={BarChart3}
              />
              <Metric
                label="Market Cap"
                value={formatINR(q?.marketCap || 0)}
                sub={`P/E Ratio: ${q?.peRatio?.toFixed(1) || "N/A"}`}
                icon={PieChart}
              />
              <Metric
                label="52-Week Range"
                value={`₹${q?.week52Low?.toLocaleString("en-IN")} — ₹${q?.week52High?.toLocaleString("en-IN")}`}
                sub={`Position: ${q?.week52High && q?.week52Low && q?.price
                  ? ((q.price - q.week52Low) / (q.week52High - q.week52Low) * 100).toFixed(0)
                  : 0}%`}
                icon={Target}
              />
            </div>

            {/* Candlestick chart */}
            {data.priceChart.length > 0 && (
              <div className="glass-solid p-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-[var(--text)]">
                    Price Chart (1 Year)
                  </h3>
                  <span className="badge badge-info text-[10px]">Candlestick + Close Line</span>
                </div>
                <CandlestickChart data={data.priceChart} />
              </div>
            )}
          </section>

          {/* ── SECTION 2: Herding Detection ──────── */}
          <section className="fade-in fade-d1">
            <SectionDivider
              num="02" icon={Activity}
              title="Herding Detection"
              desc="CCK (Chang, Cheng & Khorana) model — does the crowd control this sector?"
            />

            {data.herding.error ? (
              <InfoBox title="Insufficient Data" type="warn">
                {data.herding.error}. Need at least 3 stocks in the sector with sufficient history.
              </InfoBox>
            ) : (
              <>
                {/* Verdict banner */}
                <div
                  className={`glass-solid p-6 mb-5 flex items-center gap-5 ${
                    data.herding.herdingDetected ? "pulse" : ""
                  }`}
                  style={{
                    borderColor: data.herding.herdingDetected
                      ? "rgba(220,38,38,0.15)" : "rgba(5,150,105,0.15)",
                  }}
                >
                  <div
                    className="flex items-center justify-center w-14 h-14 rounded-2xl shrink-0"
                    style={{
                      background: data.herding.herdingDetected ? "var(--down-bg)" : "var(--up-bg)",
                    }}
                  >
                    {data.herding.herdingDetected
                      ? <AlertTriangle size={24} className="text-[var(--down)]" />
                      : <CheckCircle2 size={24} className="text-[var(--up)]" />
                    }
                  </div>
                  <div>
                    <div className="text-lg font-bold" style={{
                      color: data.herding.herdingDetected ? "var(--down)" : "var(--up)",
                    }}>
                      {data.herding.herdingDetected
                        ? `Herding Detected in ${data.herding.sector}`
                        : `No Herding in ${data.herding.sector}`}
                    </div>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">
                      {data.herding.herdingDetected
                        ? "Return dispersion decreases during extreme market moves — investors are following the crowd instead of their own analysis."
                        : "Investors appear to be making independent decisions. Return dispersion follows rational expectations."}
                    </p>
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
                  <Metric label="Herding Intensity" value={`${data.herding.intensity.toFixed(0)}/100`}
                    accent={data.herding.intensity > 50 ? "var(--down)" : data.herding.intensity > 25 ? "var(--warn)" : "var(--up)"} />
                  <Metric label="γ₂ Coefficient" value={data.herding.gamma2.toFixed(6)}
                    sub={data.herding.gamma2 < 0 ? "Negative → Herding signal" : "Non-negative → No herding"}
                    accent={data.herding.gamma2 < 0 ? "var(--down)" : "var(--up)"} />
                  <Metric label="P-value" value={data.herding.pValue.toFixed(4)}
                    sub={data.herding.pValue < 0.05 ? "Statistically significant" : "Not significant"} />
                  <Metric label="Model R²" value={data.herding.rSquared.toFixed(4)}
                    sub={`${data.herding.observations} trading days analyzed`} />
                </div>

                {/* CSAD Scatter */}
                {data.herding.csadData.length > 0 && (
                  <div className="glass-solid p-6 mb-4">
                    <h3 className="text-sm font-semibold text-[var(--text)] mb-1">
                      CSAD vs |Market Return| — Quadratic Regression
                    </h3>
                    <p className="text-xs text-[var(--text-muted)] mb-4">
                      Each dot = one trading day. If the red dashed curve bends downward, it means
                      return dispersion decreases during volatile days → herding behavior.
                    </p>
                    <CSADScatter data={data.herding.csadData} />
                  </div>
                )}

                <InfoBox title="What does this mean?" type="info">
                  The CCK model measures if stocks move together <em>more than expected</em> during
                  extreme market swings. A negative γ₂ means investors ignore their own research
                  and follow the herd — buying because others buy, or panic-selling because others sell.
                </InfoBox>
              </>
            )}
          </section>

          {/* ── SECTION 3: Panic Scanner ──────────── */}
          <section className="fade-in fade-d2">
            <SectionDivider
              num="03" icon={AlertTriangle}
              title="Panic Selling Scanner"
              desc="5-factor analysis: volume spikes, delivery pressure, price-volume divergence, drawdown & volatility"
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
              {/* Score Ring */}
              <div className="glass-solid p-6 flex justify-center items-center">
                <ScoreRing
                  score={data.panic.panicScore}
                  label={data.panic.level}
                  color={
                    data.panic.panicScore >= 70 ? "var(--down)" :
                    data.panic.panicScore >= 30 ? "var(--warn)" : "var(--up)"
                  }
                />
              </div>

              {/* Factor bars */}
              <div className="lg:col-span-2 glass-solid p-6">
                <h3 className="text-sm font-semibold mb-4">Factor Breakdown</h3>
                <div className="space-y-3.5">
                  {Object.entries(data.panic.factors).map(([key, val]) => {
                    const labels: Record<string, string> = {
                      volumeAnomaly: "Volume Anomaly",
                      deliveryPressure: "Delivery Pressure",
                      priceVolDivergence: "Price-Vol Divergence",
                      drawdownSeverity: "Drawdown Severity",
                      volatilityRegime: "Volatility Regime",
                    };
                    const fColor = (val as number) >= 50 ? "var(--down)" :
                                   (val as number) >= 25 ? "var(--warn)" : "var(--up)";
                    return (
                      <div key={key}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-[var(--text-secondary)]">
                            {labels[key] || key}
                          </span>
                          <span className="text-xs font-bold" style={{ color: fColor }}>
                            {(val as number).toFixed(0)}/100
                          </span>
                        </div>
                        <ProgressBar value={val as number} color={fColor} />
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Volume chart */}
            {data.panic.volumeData.length > 0 && (
              <div className="glass-solid p-6 mb-4">
                <h3 className="text-sm font-semibold mb-1">Volume Activity</h3>
                <p className="text-xs text-[var(--text-muted)] mb-4">
                  Red bars indicate panic-selling volume days (high volume + price drop). Clusters of red suggest sustained fear.
                </p>
                <VolumeChart data={data.panic.volumeData} />
              </div>
            )}

            <InfoBox
              title="Why does this matter?"
              type={data.panic.panicScore >= 50 ? "warn" : "info"}
            >
              Panic selling locks in losses. Research shows that investors who stayed invested through
              the 2008 crash recovered within 3 years, while those who panic-sold and re-entered later
              took over 5 years to break even.
            </InfoBox>
          </section>

          {/* ── SECTION 4: Behavior Gap & Monte Carlo ── */}
          <section className="fade-in fade-d3">
            <SectionDivider
              num="04" icon={Brain}
              title="Behavior Gap & Monte Carlo Simulation"
              desc="The financial cost of emotional decisions — and why SIP discipline always wins"
            />

            {/* Behavior Gap metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
              <Metric
                label="Investment CAGR" icon={TrendingUp}
                value={`${data.behaviorGap.investmentCagr.toFixed(2)}%`}
                sub="What the stock returned (buy & hold)"
                accent="var(--up)"
              />
              <Metric
                label="Investor CAGR" icon={TrendingDown}
                value={`${data.behaviorGap.investorCagr.toFixed(2)}%`}
                sub="What average investors actually earned"
                accent="var(--warn)"
              />
              <Metric
                label="Behavior Gap" icon={AlertTriangle}
                value={`${data.behaviorGap.behaviorGap.toFixed(2)}%`}
                sub={data.behaviorGap.gapInterpretation}
                accent={data.behaviorGap.behaviorGap > 2 ? "var(--down)" : "var(--warn)"}
              />
            </div>

            {/* 10-year cost */}
            <div className="glass-solid p-6 text-center mb-5">
              <div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--text-muted)] mb-2">
                10-Year Cost of Emotional Trading on ₹10,00,000
              </div>
              <div className="text-4xl font-black text-[var(--down)]">
                {formatINR(
                  1000000 * (
                    Math.pow(1 + data.behaviorGap.investmentCagr / 100, 10) -
                    Math.pow(1 + data.behaviorGap.investorCagr / 100, 10)
                  )
                )}
              </div>
              <div className="text-sm text-[var(--text-muted)] mt-2">
                This is how much buying-high and selling-low costs over a decade
              </div>
            </div>

            {/* Missing Best Days */}
            {data.missingDays.length > 0 && (
              <div className="glass-solid p-6 mb-5">
                <h3 className="text-sm font-semibold mb-1">
                  What If You Missed the Best Trading Days?
                </h3>
                <p className="text-xs text-[var(--text-muted)] mb-4">
                  Panic sellers exit during crashes and miss the recovery. Starting with ₹1,00,000 —
                  missing just 10 best days can cut your returns in half.
                </p>
                <MissingDaysChart data={data.missingDays} />
              </div>
            )}

            {/* Monte Carlo headline */}
            <div className="glass-solid p-6 text-center mb-5"
                 style={{ borderColor: "rgba(5,150,105,0.15)" }}>
              <div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--text-muted)] mb-2">
                Monte Carlo: Average Wealth Destroyed by Panic Selling
              </div>
              <div className="text-4xl font-black text-[var(--down)] my-1">
                {formatINR(data.monteCarlo.costOfPanic.meanLoss)}
              </div>
              <p className="text-sm text-[var(--text-secondary)]">
                SIP beats panic in{" "}
                <strong className="text-[var(--up)]">{data.monteCarlo.costOfPanic.winRate}%</strong>{" "}
                of {data.monteCarlo.nSimulations} simulated scenarios over {data.monteCarlo.years} years
              </p>
            </div>

            {/* MC detail metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
              <Metric label="Total Invested" icon={DollarSign}
                value={formatINR(data.monteCarlo.totalInvested)}
                sub={`₹10,000/month × ${data.monteCarlo.years} years`} />
              <Metric label="SIP Median Wealth" icon={TrendingUp}
                value={formatINR(data.monteCarlo.sip.median)}
                sub={`${formatINR(data.monteCarlo.sip.p10)} — ${formatINR(data.monteCarlo.sip.p90)}`}
                accent="var(--up)" />
              <Metric label="Panic Median Wealth" icon={TrendingDown}
                value={formatINR(data.monteCarlo.panic.median)}
                sub={`${formatINR(data.monteCarlo.panic.p10)} — ${formatINR(data.monteCarlo.panic.p90)}`}
                accent="var(--down)" />
              <Metric label="Wealth Reduction" icon={AlertTriangle}
                value={`${data.monteCarlo.costOfPanic.pctLoss.toFixed(1)}%`}
                sub="Lost by panic sellers" accent="var(--down)" />
            </div>

            {/* MC histogram */}
            {data.monteCarlo.histogram.length > 0 && (
              <div className="glass-solid p-6">
                <h3 className="text-sm font-semibold mb-1">
                  Wealth Distribution: SIP vs Panic Seller
                </h3>
                <p className="text-xs text-[var(--text-muted)] mb-4">
                  {data.monteCarlo.nSimulations} simulated scenarios. Green = disciplined monthly SIP investor.
                  Red = panic seller who exits after every 10% drop and waits 90 days to re-enter.
                </p>
                <MCHistogram data={data.monteCarlo.histogram} />
              </div>
            )}
          </section>

          {/* ── SECTION 5: CONCLUSION ────────────── */}
          {(() => {
            const c = getConclusion();
            if (!c) return null;
            return (
              <section className="fade-in fade-d4">
                <SectionDivider
                  num="05" icon={FileText}
                  title="Report Conclusion"
                  desc="Summary of all findings with actionable takeaways"
                />

                <div className="conclusion-card p-7">
                  <div className="space-y-4 mb-6">
                    {c.verdicts.map((v, i) => {
                      const styles = {
                        up:   "bg-[var(--up-bg)] text-[var(--up)]",
                        down: "bg-[var(--down-bg)] text-[var(--down)]",
                        warn: "bg-[var(--warn-bg)] text-[var(--warn)]",
                      };
                      return (
                        <div key={i} className="flex items-start gap-3">
                          <div className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${styles[v.type]}`}>
                            {v.icon}
                          </div>
                          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                            {v.text}
                          </p>
                        </div>
                      );
                    })}
                  </div>

                  {/* Overall verdict */}
                  <div className={`rounded-2xl p-5 ${
                    c.overall.type === "up" ? "bg-[var(--up-bg)] border border-[var(--up)]/10" :
                    c.overall.type === "down" ? "bg-[var(--down-bg)] border border-[var(--down)]/10" :
                    "bg-[var(--warn-bg)] border border-[var(--warn)]/10"
                  }`}>
                    <div className="flex items-center gap-2 mb-2" style={{
                      color: c.overall.type === "up" ? "var(--up)" :
                             c.overall.type === "down" ? "var(--down)" : "var(--warn)"
                    }}>
                      <Shield size={16} />
                      <span className="text-xs font-bold uppercase tracking-wider">
                        Overall Assessment
                      </span>
                    </div>
                    <p className="text-sm font-medium text-[var(--text)] leading-relaxed">
                      {c.overall.text}
                    </p>
                  </div>

                  {/* CTA to AI Copilot */}
                  <div className="mt-5 flex items-center justify-between glass p-4" style={{ borderRadius: 16 }}>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-[var(--accent-light)]">
                        <MessageCircle size={16} className="text-[var(--accent)]" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold">Have questions about this report?</div>
                        <div className="text-xs text-[var(--text-muted)]">
                          Chat with AI Copilot for personalized behavioral advice
                        </div>
                      </div>
                    </div>
                    <Link
                      href="/copilot"
                      className="flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline"
                    >
                      Open Copilot <ChevronRight size={16} />
                    </Link>
                  </div>
                </div>
              </section>
            );
          })()}
        </main>
      )}

      {/* ═══════ EMPTY STATE ═══════ */}
      {!data && !loading && (
        <main className="max-w-6xl mx-auto px-6 flex-1 flex items-center justify-center">
          <div className="text-center max-w-md py-20">
            <div className="text-7xl mb-5">🐑</div>
            <h2 className="text-2xl font-bold text-[var(--text)] mb-2">
              Are you a sheep or sleeping?
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mb-8 leading-relaxed">
              Select any Indian stock above and tap <strong>Generate Report</strong>.
              You&apos;ll get a complete behavioral analysis with charts, data, and a clear conclusion
              — all in one click.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {["Herding Detection", "Panic Scanner", "Behavior Gap", "Monte Carlo", "Conclusion"].map((f) => (
                <span key={f} className="badge badge-info text-[10px]">{f}</span>
              ))}
            </div>
          </div>
        </main>
      )}

      {/* ═══════ FOOTER ═══════ */}
      <footer className="mt-auto border-t border-black/5">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">🐑</span>
            <span className="text-sm font-semibold text-[var(--text)]">SheepOrSleep</span>
            <span className="text-xs text-[var(--text-muted)]">v1.0</span>
          </div>
          <p className="text-xs text-[var(--text-muted)] text-center">
            AI-powered behavioral bias detector for Indian stocks · Not financial advice · Educational purposes only
          </p>
          <div className="flex items-center gap-4">
            <Link href="/copilot" className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">
              AI Copilot
            </Link>
            <span className="text-xs text-[var(--text-dim)]">
              Built with Groq · Next.js · Recharts
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
