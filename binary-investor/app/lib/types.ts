export interface StockInfo {
  symbol: string;
  name: string;
  sector: string;
  exchange: string;
}

export interface StockQuote {
  symbol: string;
  name: string;
  price: number;
  prevClose: number;
  change: number;
  changePct: number;
  volume: number;
  dayHigh: number;
  dayLow: number;
  week52High: number;
  week52Low: number;
  marketCap: number;
  peRatio: number;
  sector: string;
  exchange: string;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/* ── Indicators ── */
export interface IndicatorSet {
  priceAction: any;
  trend: {
    ema: { ema9: number; ema21: number; ema50: number; ema200: number; trend: string };
    macd: { macd: number; signal: number; histogram: number; crossover: string };
    adx: { adx: number; plusDI: number; minusDI: number; trendStrength: string };
    parabolicSar: { sar: number; trend: string };
    superTrend: { supertrend: number; signal: string };
    ichimoku: { tenkan: number; kijun: number; senkouA: number; senkouB: number; signal: string };
  };
  momentum: {
    rsi: { rsi: number; signal: string; divergence: string };
    stochastic: { k: number; d: number; signal: string };
    williamsR: { williamsR: number; signal: string };
    mfi: { mfi: number; signal: string };
    roc: { roc: number };
    cci: { cci: number; signal: string };
  };
  volatility: {
    bollingerBands: { upper: number; middle: number; lower: number; percentB: number; bandwidth: number; squeeze: boolean };
    atr: { atr: number; atrPct: number };
    keltnerChannels: { upper: number; middle: number; lower: number };
    historicalVol: { histVol: number; avgVol: number; volRatio: number };
  };
  volume: {
    vwap: { vwap: number; priceVsVwap: string };
    obv: { obv: number; obvTrend: string };
    adLine: { adLine: number; adTrend: string };
    cmf: { cmf: number; signal: string };
    relativeVolume: { relativeVolume: number; anomaly: boolean };
  };
  behavioral: {
    panicScore: { panicScore: number; level: string; factors: Record<string, number>; details: any };
    behaviorGap: { investmentReturn: number; investmentCagr: number; investorCagr: number; behaviorGap: number; periodYears: number };
  };
  multiTimeframe?: { timeframes: Record<string, string>; consensus: string; alignment: number; total: number };
}

/* ── Trading Decision ── */
export interface TradingDecision {
  action: string;
  confidence: number;
  entry: { price: number; type: string };
  stopLoss: number;
  takeProfit1: number;
  takeProfit2: number;
  positionSizePct: number;
  riskReward: number;
  reasoning: string;
  alerts: string[];
  symbol: string;
  name: string;
  currentPrice: number;
  regime: string;
}

/* ── Full Analysis ── */
export interface AnalysisResult {
  quote: StockQuote;
  chart: PricePoint[];
  regime: { current: string; confidence: number };
  signal: { action: string; confidence: number; probabilities: Record<string, number> };
  indicators: IndicatorSet;
  sentiment: { score: number; label: string; articleCount: number; articles?: { title: string; source: string; url: string; date: string | number; summary: string }[] };
  volatility: { forecasted: number; historical: number; riskLevel: string };
  fundamentals: any;
  herding: { herdingDetected: boolean; intensity: number; gamma2: number; pValue: number };
  multiTimeframe: any;
}

/* ── Paper Trading ── */
export interface Portfolio {
  portfolioId: string;
  initialBalance: number;
  cash: number;
  positionsValue: number;
  totalEquity: number;
  totalPnl: number;
  totalPnlPct: number;
  openPositions: number;
  totalTrades: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
}

export interface Position {
  id: string;
  symbol: string;
  action: string;
  entryPrice: number;
  currentPrice: number;
  quantity: number;
  pnl: number;
  pnlPct: number;
  stopLoss: number;
  takeProfit1: number;
  takeProfit2: number;
  status: string;
  holdingDays: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
