"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { Search, ChevronDown, X, Globe } from "lucide-react";
import { STOCK_UNIVERSE, getExchanges } from "@/app/lib/stockUniverse";
import type { StockInfo } from "@/app/lib/types";

interface Props {
  selected: StockInfo | null;
  onSelect: (stock: StockInfo) => void;
}

const EXCHANGE_ICONS: Record<string, string> = {
  NSE: "🇮🇳", NASDAQ: "🇺🇸", NYSE: "🇺🇸", LSE: "🇬🇧",
  XETRA: "🇩🇪", TSE: "🇯🇵", HKEX: "🇭🇰",
};

export default function StockSelector({ selected, onSelect }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [exchangeFilter, setExchangeFilter] = useState<string>("");
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    let list = STOCK_UNIVERSE;
    if (exchangeFilter) list = list.filter((s) => s.exchange === exchangeFilter);
    const q = query.toLowerCase().trim();
    if (!q) return list;
    return list.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.symbol.toLowerCase().includes(q) ||
        s.sector.toLowerCase().includes(q)
    );
  }, [query, exchangeFilter]);

  const grouped = useMemo(() => {
    const map: Record<string, StockInfo[]> = {};
    for (const s of filtered) {
      (map[s.exchange] ??= []).push(s);
    }
    return Object.entries(map).sort(([a], [b]) => {
      const order = ["NSE", "NASDAQ", "NYSE", "LSE", "XETRA", "TSE", "HKEX"];
      return order.indexOf(a) - order.indexOf(b);
    });
  }, [filtered]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  const exchanges = getExchanges();

  return (
    <div ref={ref} className="relative w-full max-w-xl">
      {/* Trigger */}
      <button
        onClick={() => setOpen(!open)}
        className="glass w-full flex items-center justify-between gap-3 px-5 py-4 text-left cursor-pointer"
        style={{ borderRadius: 14 }}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: selected ? "var(--accent-soft)" : "var(--bg-sunken)",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}>
            {selected
              ? <span style={{ fontSize: 16 }}>{EXCHANGE_ICONS[selected.exchange] || "📊"}</span>
              : <Search size={16} style={{ color: "var(--text-muted)" }} />
            }
          </div>
          {selected ? (
            <div className="truncate">
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15, color: "var(--text)" }}>
                {selected.name}
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: 1 }}>
                {selected.symbol} · {selected.sector} · {selected.exchange}
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: 15, color: "var(--text)" }}>
                Search Stocks
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 1 }}>
                {STOCK_UNIVERSE.length} stocks · 7 exchanges · Global markets
              </div>
            </div>
          )}
        </div>
        <ChevronDown size={16} style={{
          color: "var(--text-muted)", transition: "transform 0.2s ease",
          transform: open ? "rotate(180deg)" : "rotate(0deg)", flexShrink: 0,
        }} />
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className="card-elevated absolute z-50 mt-2 w-full overflow-hidden flex flex-col"
          style={{ maxHeight: 480, borderRadius: 16, boxShadow: "var(--shadow-lg)" }}
        >
          {/* Search */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
            <Search size={15} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name, symbol, sector..."
              style={{
                background: "transparent", border: "none", outline: "none",
                fontSize: 14, color: "var(--text)", flex: 1, fontFamily: "var(--font-body)",
              }}
            />
            {query && (
              <button onClick={() => setQuery("")} style={{ cursor: "pointer", lineHeight: 0 }}>
                <X size={14} style={{ color: "var(--text-muted)" }} />
              </button>
            )}
          </div>

          {/* Exchange Filters */}
          <div style={{
            display: "flex", gap: 4, padding: "8px 12px",
            borderBottom: "1px solid var(--border)", overflowX: "auto",
          }}>
            <button
              onClick={() => setExchangeFilter("")}
              style={{
                padding: "4px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600,
                border: "1px solid var(--border)", cursor: "pointer", whiteSpace: "nowrap",
                background: !exchangeFilter ? "var(--accent)" : "transparent",
                color: !exchangeFilter ? "var(--accent-text)" : "var(--text-muted)",
              }}
            >
              All
            </button>
            {exchanges.map((ex) => (
              <button
                key={ex}
                onClick={() => setExchangeFilter(exchangeFilter === ex ? "" : ex)}
                style={{
                  padding: "4px 10px", borderRadius: 6, fontSize: 11, fontWeight: 500,
                  border: "1px solid var(--border)", cursor: "pointer", whiteSpace: "nowrap",
                  background: exchangeFilter === ex ? "var(--accent)" : "transparent",
                  color: exchangeFilter === ex ? "var(--accent-text)" : "var(--text-muted)",
                  display: "flex", alignItems: "center", gap: 4,
                }}
              >
                <span style={{ fontSize: 12 }}>{EXCHANGE_ICONS[ex] || ""}</span>
                {ex}
              </button>
            ))}
          </div>

          {/* Results */}
          <div style={{ overflowY: "auto", flex: 1 }}>
            {grouped.length === 0 ? (
              <div style={{ padding: "32px 16px", textAlign: "center" }}>
                <div style={{ fontSize: 28, marginBottom: 8 }}>🔍</div>
                <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No stocks matching &ldquo;{query}&rdquo;</p>
              </div>
            ) : (
              grouped.map(([exchange, stocks]) => (
                <div key={exchange}>
                  <div style={{
                    padding: "6px 16px", fontSize: 10, fontWeight: 700, textTransform: "uppercase",
                    letterSpacing: "0.1em", color: "var(--text-muted)", background: "var(--bg-sunken)",
                    borderBottom: "1px solid var(--border)", position: "sticky", top: 0, zIndex: 10,
                    display: "flex", alignItems: "center", gap: 6, fontFamily: "var(--font-body)",
                  }}>
                    <span>{EXCHANGE_ICONS[exchange] || "📊"}</span>
                    <span>{exchange}</span>
                    <span style={{ background: "var(--border)", borderRadius: 999, padding: "1px 7px", fontSize: 9 }}>
                      {stocks.length}
                    </span>
                  </div>
                  {stocks.map((s) => {
                    const isSelected = selected?.symbol === s.symbol;
                    return (
                      <button
                        key={s.symbol}
                        onClick={() => { onSelect(s); setOpen(false); setQuery(""); }}
                        style={{
                          width: "100%", textAlign: "left", padding: "10px 16px",
                          display: "flex", alignItems: "center", justifyContent: "space-between",
                          cursor: "pointer", border: "none",
                          background: isSelected ? "var(--accent-soft)" : "transparent",
                          transition: "background 0.1s ease", fontFamily: "var(--font-body)",
                        }}
                        onMouseEnter={(e) => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = "var(--surface-hover)"; }}
                        onMouseLeave={(e) => { if (!isSelected) (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                      >
                        <div>
                          <span style={{ fontSize: 13, fontWeight: 500, color: isSelected ? "var(--accent)" : "var(--text)" }}>
                            {s.name}
                          </span>
                          <span style={{
                            marginLeft: 8, fontSize: 10, color: "var(--text-muted)",
                            background: "var(--bg-sunken)", borderRadius: 5, padding: "2px 6px",
                          }}>
                            {s.sector}
                          </span>
                        </div>
                        <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                          {s.symbol}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}