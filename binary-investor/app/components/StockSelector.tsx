"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { Search, ChevronDown, X } from "lucide-react";
import { STOCK_UNIVERSE } from "@/app/lib/stockUniverse";
import type { StockInfo } from "@/app/lib/types";

interface Props {
  selected: StockInfo | null;
  onSelect: (stock: StockInfo) => void;
}

export default function StockSelector({ selected, onSelect }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) return STOCK_UNIVERSE;
    return STOCK_UNIVERSE.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.symbol.toLowerCase().includes(q) ||
        s.sector.toLowerCase().includes(q)
    );
  }, [query]);

  const grouped = useMemo(() => {
    const map: Record<string, StockInfo[]> = {};
    for (const s of filtered) {
      (map[s.sector] ??= []).push(s);
    }
    return Object.entries(map).sort(([a], [b]) => a.localeCompare(b));
  }, [filtered]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  return (
    <div ref={ref} className="relative w-full max-w-lg">
      {/* Trigger */}
      <button
        onClick={() => setOpen(!open)}
        className="glass w-full flex items-center justify-between px-5 py-3.5 text-left cursor-pointer"
        style={{ borderRadius: 16 }}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <Search size={16} className="text-[var(--text-muted)] shrink-0" />
          {selected ? (
            <div className="truncate">
              <span className="text-sm font-semibold text-[var(--text)]">
                {selected.name}
              </span>
              <span className="ml-2 text-xs text-[var(--text-muted)] font-mono">
                {selected.symbol.replace(".NS", "")}
              </span>
            </div>
          ) : (
            <span className="text-sm text-[var(--text-muted)]">
              Search any Indian stock...
            </span>
          )}
        </div>
        <ChevronDown
          size={16}
          className={`text-[var(--text-muted)] transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className="absolute z-50 mt-2 w-full max-h-[420px] overflow-hidden glass-solid flex flex-col"
          style={{ borderRadius: 20, boxShadow: "0 20px 60px rgba(0,0,0,0.1)" }}
        >
          {/* Search */}
          <div className="flex items-center gap-2.5 px-5 py-3 border-b border-black/5">
            <Search size={15} className="text-[var(--text-muted)]" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type stock name, symbol, or sector..."
              className="bg-transparent text-sm text-[var(--text)] placeholder-[var(--text-dim)] outline-none flex-1"
            />
            {query && (
              <button onClick={() => setQuery("")} className="cursor-pointer">
                <X size={14} className="text-[var(--text-muted)]" />
              </button>
            )}
          </div>

          {/* Results */}
          <div className="overflow-y-auto max-h-[360px]">
            {grouped.map(([sector, stocks]) => (
              <div key={sector}>
                <div className="px-5 py-2 text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--text-muted)] bg-black/[0.02] sticky top-0 z-10">
                  {sector} · {stocks.length}
                </div>
                {stocks.map((s) => (
                  <button
                    key={s.symbol}
                    onClick={() => {
                      onSelect(s);
                      setOpen(false);
                      setQuery("");
                    }}
                    className={`w-full text-left px-5 py-2.5 flex items-center justify-between hover:bg-[var(--accent-light)] transition-colors cursor-pointer ${
                      selected?.symbol === s.symbol
                        ? "bg-[var(--accent-light)]"
                        : ""
                    }`}
                  >
                    <div>
                      <span className="text-sm font-medium text-[var(--text)]">
                        {s.name}
                      </span>
                      <span className="ml-1.5 text-[10px] text-[var(--text-muted)] px-1.5 py-0.5 rounded-md bg-black/[0.03]">
                        {s.index}
                      </span>
                    </div>
                    <span className="text-xs text-[var(--text-muted)] font-mono">
                      {s.symbol.replace(".NS", "")}
                    </span>
                  </button>
                ))}
              </div>
            ))}
            {grouped.length === 0 && (
              <div className="px-5 py-10 text-center text-sm text-[var(--text-muted)]">
                No stocks matching &quot;{query}&quot;
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
