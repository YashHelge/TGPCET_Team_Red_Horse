"use client";

import {
  ComposedChart, Bar, Line, Area, AreaChart,
  BarChart, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend, ReferenceLine,
} from "recharts";
import type {
  PricePoint, CSADPoint, VolumePoint,
  HistogramBin, MissingDayScenario,
} from "@/app/lib/types";

const ACCENT  = "#4F46E5";
const UP      = "#059669";
const DOWN    = "#DC2626";
const MUTED   = "#94A3B8";
const GRID    = "rgba(0,0,0,0.05)";

/* ─── Shared Tooltip ──────────────────────────────── */
function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-solid px-3 py-2.5 text-xs shadow-lg" style={{ borderRadius: 12 }}>
      <p className="font-semibold text-[var(--text)] mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="flex items-center gap-1.5">
          <span className="inline-block w-2 h-2 rounded-full" style={{ background: p.color || p.fill }} />
          <span className="text-[var(--text-secondary)]">{p.name}:</span>
          <span className="font-medium text-[var(--text)]">
            {typeof p.value === "number" ? p.value.toLocaleString("en-IN") : p.value}
          </span>
        </p>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════ */
/* Candlestick Chart                                  */
/* ═══════════════════════════════════════════════════ */
export function CandlestickChart({ data }: { data: PricePoint[] }) {
  // Build OHLC candle data for ComposedChart
  const candleData = data.map((d) => ({
    ...d,
    // for bar: body of candle from open to close
    bodyLow:  Math.min(d.open, d.close),
    bodyHigh: Math.max(d.open, d.close),
    bodySize: Math.abs(d.close - d.open),
    isUp: d.close >= d.open,
    // wick data
    wickHigh: d.high,
    wickLow:  d.low,
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={candleData} barCategoryGap="20%">
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10, fill: MUTED }}
          stroke="transparent"
          tickFormatter={(v) => v.split(",")[0]}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={["auto", "auto"]}
          tick={{ fontSize: 10, fill: MUTED }}
          stroke="transparent"
          tickFormatter={(v) => `₹${Number(v).toLocaleString("en-IN")}`}
        />
        <Tooltip content={<ChartTooltip />} />

        {/* Wicks — thin line from low to high */}
        <Bar dataKey="wickHigh" stackId="wick" fill="transparent" barSize={1}>
          {candleData.map((d, i) => (
            <Cell key={i} fill="transparent" />
          ))}
        </Bar>

        {/* Candle bodies — bar from bodyLow to bodyHigh */}
        <Bar
          dataKey="bodySize"
          name="Price"
          barSize={6}
          radius={[2, 2, 2, 2]}
        >
          {candleData.map((d, i) => (
            <Cell key={i} fill={d.isUp ? UP : DOWN} fillOpacity={0.85} />
          ))}
        </Bar>

        {/* Close price line overlay */}
        <Line
          type="monotone"
          dataKey="close"
          stroke={ACCENT}
          strokeWidth={1.5}
          dot={false}
          name="Close"
          strokeOpacity={0.4}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

/* ═══════════════════════════════════════════════════ */
/* Price Area Chart (mini)                             */
/* ═══════════════════════════════════════════════════ */
export function PriceAreaChart({ data }: { data: PricePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={ACCENT} stopOpacity={0.12} />
            <stop offset="100%" stopColor={ACCENT} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis dataKey="date" tick={{ fontSize: 9, fill: MUTED }} stroke="transparent"
               tickFormatter={(v) => v.split(",")[0]} interval="preserveStartEnd" />
        <YAxis domain={["auto", "auto"]} tick={{ fontSize: 9, fill: MUTED }} stroke="transparent"
               tickFormatter={(v) => `₹${Number(v).toLocaleString("en-IN")}`} />
        <Tooltip content={<ChartTooltip />} />
        <Area type="monotone" dataKey="close" stroke={ACCENT} fill="url(#areaGrad)"
              strokeWidth={2} dot={false} name="Close Price (₹)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/* ═══════════════════════════════════════════════════ */
/* CSAD Scatter Plot                                   */
/* ═══════════════════════════════════════════════════ */
export function CSADScatter({ data }: { data: CSADPoint[] }) {
  const sorted = [...data].sort((a, b) => a.absReturn - b.absReturn);
  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={sorted}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis
          dataKey="absReturn"
          tick={{ fontSize: 10, fill: MUTED }}
          stroke="transparent"
          tickFormatter={(v) => `${(v * 100).toFixed(1)}%`}
          type="number"
          name="|Market Return|"
        />
        <YAxis
          dataKey="csad"
          tick={{ fontSize: 10, fill: MUTED }}
          stroke="transparent"
          tickFormatter={(v) => `${(v * 100).toFixed(1)}%`}
          type="number"
          name="CSAD"
        />
        <Tooltip content={<ChartTooltip />} />
        <Scatter name="Daily CSAD" dataKey="csad" fill={ACCENT} fillOpacity={0.35} r={3.5} />
        <Line
          type="monotone"
          dataKey="fitted"
          stroke={DOWN}
          strokeWidth={2.5}
          dot={false}
          name="CCK Fitted Curve"
          strokeDasharray="6 3"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

/* ═══════════════════════════════════════════════════ */
/* Volume Bar Chart                                    */
/* ═══════════════════════════════════════════════════ */
export function VolumeChart({ data }: { data: VolumePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis dataKey="date" tick={{ fontSize: 9, fill: MUTED }} stroke="transparent" interval={4} />
        <YAxis tick={{ fontSize: 9, fill: MUTED }} stroke="transparent"
               tickFormatter={(v) => `${(v / 1e6).toFixed(1)}M`} />
        <Tooltip content={<ChartTooltip />} />
        <Bar dataKey="volume" name="Volume" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => (
            <Cell key={i}
              fill={entry.isPanic ? DOWN : ACCENT}
              fillOpacity={entry.isPanic ? 0.75 : 0.25}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ═══════════════════════════════════════════════════ */
/* Monte Carlo Histogram                               */
/* ═══════════════════════════════════════════════════ */
export function MCHistogram({ data }: { data: HistogramBin[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} barGap={0}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis
          dataKey="binStart"
          tick={{ fontSize: 9, fill: MUTED }}
          stroke="transparent"
          tickFormatter={(v) => `₹${(v / 1e5).toFixed(0)}L`}
          interval={3}
        />
        <YAxis tick={{ fontSize: 9, fill: MUTED }} stroke="transparent" />
        <Tooltip content={<ChartTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, color: MUTED, paddingTop: 8 }}
          iconType="circle"
          iconSize={8}
        />
        <Bar dataKey="sip" name="Disciplined SIP" fill={UP} fillOpacity={0.55} radius={[3, 3, 0, 0]} />
        <Bar dataKey="panic" name="Panic Seller" fill={DOWN} fillOpacity={0.55} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ═══════════════════════════════════════════════════ */
/* Missing Best Days Bar Chart                         */
/* ═══════════════════════════════════════════════════ */
export function MissingDaysChart({ data }: { data: MissingDayScenario[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 10, fill: MUTED }}
          stroke="transparent"
          tickFormatter={(v) => `₹${(v / 1e5).toFixed(0)}L`}
        />
        <YAxis
          type="category"
          dataKey="scenario"
          tick={{ fontSize: 10, fill: MUTED }}
          stroke="transparent"
          width={130}
        />
        <Tooltip content={<ChartTooltip />} />
        <Bar dataKey="finalValue" name="Final Value (₹)" radius={[0, 6, 6, 0]} barSize={20}>
          {data.map((entry, i) => (
            <Cell key={i} fill={i === 0 ? UP : DOWN} fillOpacity={i === 0 ? 0.65 : 0.35 + i * 0.05} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
