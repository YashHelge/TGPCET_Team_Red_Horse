class StockInfo {
  final String symbol;
  final String name;
  final String sector;
  final String index;

  StockInfo({required this.symbol, required this.name, required this.sector, required this.index});

  factory StockInfo.fromJson(Map<String, dynamic> json) => StockInfo(
    symbol: json['symbol'] ?? '',
    name: json['name'] ?? '',
    sector: json['sector'] ?? '',
    index: json['index'] ?? '',
  );
}

class StockQuote {
  final String symbol, name, sector;
  final double price, prevClose, change, changePct;
  final int volume, avgVolume;
  final double dayHigh, dayLow, week52High, week52Low;
  final double marketCap, peRatio;

  StockQuote({
    required this.symbol, required this.name, required this.sector,
    required this.price, required this.prevClose, required this.change,
    required this.changePct, required this.volume, required this.avgVolume,
    required this.dayHigh, required this.dayLow, required this.week52High,
    required this.week52Low, required this.marketCap, required this.peRatio,
  });

  factory StockQuote.fromJson(Map<String, dynamic> j) => StockQuote(
    symbol: j['symbol'] ?? '', name: j['name'] ?? '', sector: j['sector'] ?? '',
    price: (j['price'] ?? 0).toDouble(), prevClose: (j['prevClose'] ?? 0).toDouble(),
    change: (j['change'] ?? 0).toDouble(), changePct: (j['changePct'] ?? 0).toDouble(),
    volume: (j['volume'] ?? 0).toInt(), avgVolume: (j['avgVolume'] ?? 0).toInt(),
    dayHigh: (j['dayHigh'] ?? 0).toDouble(), dayLow: (j['dayLow'] ?? 0).toDouble(),
    week52High: (j['week52High'] ?? 0).toDouble(), week52Low: (j['week52Low'] ?? 0).toDouble(),
    marketCap: (j['marketCap'] ?? 0).toDouble(), peRatio: (j['peRatio'] ?? 0).toDouble(),
  );
}

class PricePoint {
  final String date;
  final double open, high, low, close;
  final int volume;

  PricePoint({required this.date, required this.open, required this.high,
    required this.low, required this.close, required this.volume});

  factory PricePoint.fromJson(Map<String, dynamic> j) => PricePoint(
    date: j['date'] ?? '', open: (j['open'] ?? 0).toDouble(),
    high: (j['high'] ?? 0).toDouble(), low: (j['low'] ?? 0).toDouble(),
    close: (j['close'] ?? 0).toDouble(), volume: (j['volume'] ?? 0).toInt(),
  );
}

class CSADPoint {
  final double absReturn, csad, mktReturn, fitted;
  CSADPoint({required this.absReturn, required this.csad, required this.mktReturn, required this.fitted});
  factory CSADPoint.fromJson(Map<String, dynamic> j) => CSADPoint(
    absReturn: (j['absReturn'] ?? 0).toDouble(), csad: (j['csad'] ?? 0).toDouble(),
    mktReturn: (j['mktReturn'] ?? 0).toDouble(), fitted: (j['fitted'] ?? 0).toDouble(),
  );
}

class HerdingResult {
  final String sector;
  final int nStocks, observations;
  final bool herdingDetected;
  final double intensity, gamma2, gamma1, alpha, pValue, tStat, rSquared;
  final List<CSADPoint> csadData;
  final String? error;

  HerdingResult({
    required this.sector, required this.nStocks, required this.observations,
    required this.herdingDetected, required this.intensity, required this.gamma2,
    required this.gamma1, required this.alpha, required this.pValue,
    required this.tStat, required this.rSquared, required this.csadData, this.error,
  });

  factory HerdingResult.fromJson(Map<String, dynamic> j) => HerdingResult(
    sector: j['sector'] ?? '', nStocks: (j['nStocks'] ?? 0).toInt(),
    observations: (j['observations'] ?? 0).toInt(),
    herdingDetected: j['herdingDetected'] ?? false,
    intensity: (j['intensity'] ?? 0).toDouble(),
    gamma2: (j['gamma2'] ?? 0).toDouble(), gamma1: (j['gamma1'] ?? 0).toDouble(),
    alpha: (j['alpha'] ?? 0).toDouble(), pValue: (j['pValue'] ?? 0).toDouble(),
    tStat: (j['tStat'] ?? 0).toDouble(), rSquared: (j['rSquared'] ?? 0).toDouble(),
    csadData: (j['csadData'] as List? ?? []).map((e) => CSADPoint.fromJson(e)).toList(),
    error: j['error'],
  );
}

class PanicFactors {
  final double volumeAnomaly, deliveryPressure, priceVolDivergence, drawdownSeverity, volatilityRegime;
  PanicFactors({required this.volumeAnomaly, required this.deliveryPressure,
    required this.priceVolDivergence, required this.drawdownSeverity, required this.volatilityRegime});
  factory PanicFactors.fromJson(Map<String, dynamic> j) => PanicFactors(
    volumeAnomaly: (j['volumeAnomaly'] ?? 0).toDouble(),
    deliveryPressure: (j['deliveryPressure'] ?? 0).toDouble(),
    priceVolDivergence: (j['priceVolDivergence'] ?? 0).toDouble(),
    drawdownSeverity: (j['drawdownSeverity'] ?? 0).toDouble(),
    volatilityRegime: (j['volatilityRegime'] ?? 0).toDouble(),
  );
}

class VolumePoint {
  final String date;
  final int volume;
  final double zscore, returns;
  final bool isPanic;
  VolumePoint({required this.date, required this.volume, required this.zscore,
    required this.returns, required this.isPanic});
  factory VolumePoint.fromJson(Map<String, dynamic> j) => VolumePoint(
    date: j['date'] ?? '', volume: (j['volume'] ?? 0).toInt(),
    zscore: (j['zscore'] ?? 0).toDouble(), returns: (j['returns'] ?? 0).toDouble(),
    isPanic: j['isPanic'] ?? false,
  );
}

class PanicResult {
  final double panicScore;
  final String level;
  final PanicFactors factors;
  final List<VolumePoint> volumeData;

  PanicResult({required this.panicScore, required this.level,
    required this.factors, required this.volumeData});

  factory PanicResult.fromJson(Map<String, dynamic> j) => PanicResult(
    panicScore: (j['panicScore'] ?? 0).toDouble(),
    level: j['level'] ?? 'CALM',
    factors: PanicFactors.fromJson(j['factors'] ?? {}),
    volumeData: (j['volumeData'] as List? ?? []).map((e) => VolumePoint.fromJson(e)).toList(),
  );
}

class BehaviorGapResult {
  final double investmentReturn, investmentCagr, investorCagr, behaviorGap;
  final int periodYears;
  final String gapInterpretation;

  BehaviorGapResult({required this.investmentReturn, required this.investmentCagr,
    required this.investorCagr, required this.behaviorGap,
    required this.periodYears, required this.gapInterpretation});

  factory BehaviorGapResult.fromJson(Map<String, dynamic> j) => BehaviorGapResult(
    investmentReturn: (j['investmentReturn'] ?? 0).toDouble(),
    investmentCagr: (j['investmentCagr'] ?? 0).toDouble(),
    investorCagr: (j['investorCagr'] ?? 0).toDouble(),
    behaviorGap: (j['behaviorGap'] ?? 0).toDouble(),
    periodYears: (j['periodYears'] ?? 0).toInt(),
    gapInterpretation: j['gapInterpretation'] ?? '',
  );
}

class MissingDayScenario {
  final String scenario;
  final double finalValue, totalReturn, cagr, reduction;
  MissingDayScenario({required this.scenario, required this.finalValue,
    required this.totalReturn, required this.cagr, required this.reduction});
  factory MissingDayScenario.fromJson(Map<String, dynamic> j) => MissingDayScenario(
    scenario: j['scenario'] ?? '', finalValue: (j['finalValue'] ?? 0).toDouble(),
    totalReturn: (j['totalReturn'] ?? 0).toDouble(),
    cagr: (j['cagr'] ?? 0).toDouble(), reduction: (j['reduction'] ?? 0).toDouble(),
  );
}

class HistogramBin {
  final double binStart, binEnd;
  final int sip, panic;
  HistogramBin({required this.binStart, required this.binEnd, required this.sip, required this.panic});
  factory HistogramBin.fromJson(Map<String, dynamic> j) => HistogramBin(
    binStart: (j['binStart'] ?? 0).toDouble(), binEnd: (j['binEnd'] ?? 0).toDouble(),
    sip: (j['sip'] ?? 0).toInt(), panic: (j['panic'] ?? 0).toInt(),
  );
}

class MonteCarloResult {
  final double totalInvested;
  final int years, nSimulations;
  final Map<String, double> sip, panicStats;
  final Map<String, double> costOfPanic;
  final List<HistogramBin> histogram;

  MonteCarloResult({required this.totalInvested, required this.years,
    required this.nSimulations, required this.sip, required this.panicStats,
    required this.costOfPanic, required this.histogram});

  factory MonteCarloResult.fromJson(Map<String, dynamic> j) {
    Map<String, double> parseDoubleMap(Map<String, dynamic>? m) {
      if (m == null) return {};
      return m.map((k, v) => MapEntry(k, (v ?? 0).toDouble()));
    }
    return MonteCarloResult(
      totalInvested: (j['totalInvested'] ?? 0).toDouble(),
      years: (j['years'] ?? 0).toInt(),
      nSimulations: (j['nSimulations'] ?? 0).toInt(),
      sip: parseDoubleMap(j['sip'] as Map<String, dynamic>?),
      panicStats: parseDoubleMap(j['panic'] as Map<String, dynamic>?),
      costOfPanic: parseDoubleMap(j['costOfPanic'] as Map<String, dynamic>?),
      histogram: (j['histogram'] as List? ?? []).map((e) => HistogramBin.fromJson(e)).toList(),
    );
  }
}

class AnalysisResult {
  final StockQuote quote;
  final List<PricePoint> priceChart;
  final HerdingResult herding;
  final PanicResult panic;
  final BehaviorGapResult behaviorGap;
  final List<MissingDayScenario> missingDays;
  final MonteCarloResult monteCarlo;

  AnalysisResult({required this.quote, required this.priceChart,
    required this.herding, required this.panic, required this.behaviorGap,
    required this.missingDays, required this.monteCarlo});

  factory AnalysisResult.fromJson(Map<String, dynamic> j) => AnalysisResult(
    quote: StockQuote.fromJson(j['quote'] ?? {}),
    priceChart: (j['priceChart'] as List? ?? []).map((e) => PricePoint.fromJson(e)).toList(),
    herding: HerdingResult.fromJson(j['herding'] ?? {}),
    panic: PanicResult.fromJson(j['panic'] ?? {}),
    behaviorGap: BehaviorGapResult.fromJson(j['behaviorGap'] ?? {}),
    missingDays: (j['missingDays'] as List? ?? []).map((e) => MissingDayScenario.fromJson(e)).toList(),
    monteCarlo: MonteCarloResult.fromJson(j['monteCarlo'] ?? {}),
  );
}

class ChatMessage {
  final String role;
  final String content;
  ChatMessage({required this.role, required this.content});
}
