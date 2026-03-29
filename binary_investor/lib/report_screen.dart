import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import 'models.dart';
import 'app_theme.dart';
import 'copilot_screen.dart';

final _inr = NumberFormat('#,##,###', 'en_IN');

class ReportScreen extends StatelessWidget {
  final AnalysisResult result;
  const ReportScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final q = result.quote;
    final isUp = q.changePct >= 0;
    return Scaffold(
      appBar: AppBar(
        title: Text(q.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.smart_toy_rounded, size: 22),
            tooltip: 'AI Copilot',
            onPressed: () => Navigator.push(context, MaterialPageRoute(
              builder: (_) => CopilotScreen(result: result),
            )),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 40),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ──── Quote Card ────
            _SectionCard(
              title: 'Stock Overview',
              icon: Icons.candlestick_chart_rounded,
              child: Column(
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text('₹${q.price.toStringAsFixed(2)}', style: GoogleFonts.syne(
                        fontWeight: FontWeight.w800, fontSize: 28, color: AppColors.text,
                      )),
                      const SizedBox(width: 10),
                      _Badge(
                        text: '${isUp ? "+" : ""}${q.changePct.toStringAsFixed(2)}%',
                        color: isUp ? AppColors.up : AppColors.down,
                        bg: isUp ? AppColors.upBg : AppColors.downBg,
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      Text('${q.symbol} · ${q.sector}', style: GoogleFonts.dmMono(
                        fontSize: 11, color: AppColors.textMuted,
                      )),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _StatRow('Market Cap', '₹${_formatLargeNum(q.marketCap)}'),
                  _StatRow('P/E Ratio', q.peRatio.toStringAsFixed(1)),
                  _StatRow('Volume', _inr.format(q.volume)),
                  _StatRow('52W High / Low', '₹${q.week52High.toStringAsFixed(0)} / ₹${q.week52Low.toStringAsFixed(0)}'),
                  _StatRow('Day Range', '₹${q.dayLow.toStringAsFixed(0)} – ₹${q.dayHigh.toStringAsFixed(0)}'),
                  if (result.priceChart.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    SizedBox(height: 180, child: _PriceLineChart(data: result.priceChart)),
                  ],
                ],
              ),
            ),

            // ──── Herding ────
            _SectionCard(
              title: 'Herding Detection',
              icon: Icons.psychology_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _VerdictBadge(
                    detected: result.herding.herdingDetected,
                    label: result.herding.herdingDetected ? 'HERDING DETECTED' : 'NO HERDING',
                  ),
                  const SizedBox(height: 12),
                  _StatRow('Sector', result.herding.sector),
                  _StatRow('Intensity', '${result.herding.intensity.toStringAsFixed(1)} / 100'),
                  _StatRow('γ₂ (gamma)', result.herding.gamma2.toStringAsFixed(6)),
                  _StatRow('p-value', result.herding.pValue.toStringAsFixed(4)),
                  _StatRow('R²', result.herding.rSquared.toStringAsFixed(4)),
                  _StatRow('Observations', '${result.herding.observations}'),
                  if (result.herding.csadData.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text('CSAD vs |Market Return|', style: GoogleFonts.syne(
                      fontWeight: FontWeight.w700, fontSize: 12, color: AppColors.textSecondary,
                    )),
                    const SizedBox(height: 8),
                    SizedBox(height: 200, child: _CSADChart(data: result.herding.csadData)),
                  ],
                ],
              ),
            ),

            // ──── Panic ────
            _SectionCard(
              title: 'Panic Selling Scanner',
              icon: Icons.warning_amber_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(child: _PanicRing(score: result.panic.panicScore, level: result.panic.level)),
                  const SizedBox(height: 16),
                  _FactorBar('Volume Anomaly', result.panic.factors.volumeAnomaly, 0.30),
                  _FactorBar('Delivery Pressure', result.panic.factors.deliveryPressure, 0.20),
                  _FactorBar('Price-Vol Divergence', result.panic.factors.priceVolDivergence, 0.25),
                  _FactorBar('Drawdown Severity', result.panic.factors.drawdownSeverity, 0.15),
                  _FactorBar('Volatility Regime', result.panic.factors.volatilityRegime, 0.10),
                  if (result.panic.volumeData.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text('Volume Activity', style: GoogleFonts.syne(
                      fontWeight: FontWeight.w700, fontSize: 12, color: AppColors.textSecondary,
                    )),
                    const SizedBox(height: 8),
                    SizedBox(height: 160, child: _VolumeChart(data: result.panic.volumeData)),
                  ],
                ],
              ),
            ),

            // ──── Behavior Gap ────
            _SectionCard(
              title: 'Behavior Gap',
              icon: Icons.trending_up_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(child: _MetricTile('Investment CAGR', '${result.behaviorGap.investmentCagr.toStringAsFixed(2)}%', AppColors.upMid)),
                      const SizedBox(width: 10),
                      Expanded(child: _MetricTile('Investor CAGR', '${result.behaviorGap.investorCagr.toStringAsFixed(2)}%', AppColors.warnMid)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(child: _MetricTile('Behavior Gap', '${result.behaviorGap.behaviorGap.toStringAsFixed(2)}%', AppColors.downMid)),
                      const SizedBox(width: 10),
                      Expanded(child: _MetricTile('Period', '${result.behaviorGap.periodYears} years', AppColors.accent)),
                    ],
                  ),
                  if (result.behaviorGap.gapInterpretation.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.warnBg,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(result.behaviorGap.gapInterpretation, style: GoogleFonts.dmSans(
                        fontSize: 12, color: AppColors.warn, height: 1.5,
                      )),
                    ),
                  ],
                  if (result.missingDays.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text('Missing Best Days', style: GoogleFonts.syne(
                      fontWeight: FontWeight.w700, fontSize: 12, color: AppColors.textSecondary,
                    )),
                    const SizedBox(height: 8),
                    ...result.missingDays.map((d) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: _StatRow(d.scenario, '${d.cagr.toStringAsFixed(1)}% CAGR (–${d.reduction.toStringAsFixed(0)}%)'),
                    )),
                  ],
                ],
              ),
            ),

            // ──── Monte Carlo ────
            _SectionCard(
              title: 'Monte Carlo: SIP vs Panic',
              icon: Icons.casino_rounded,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(child: _MetricTile('SIP Mean', '₹${_inr.format(result.monteCarlo.sip['mean']?.toInt() ?? 0)}', AppColors.upMid)),
                      const SizedBox(width: 10),
                      Expanded(child: _MetricTile('Panic Mean', '₹${_inr.format(result.monteCarlo.panicStats['mean']?.toInt() ?? 0)}', AppColors.downMid)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(child: _MetricTile('SIP Win Rate', '${(result.monteCarlo.costOfPanic['winRate'] ?? 0).toStringAsFixed(1)}%', AppColors.accent)),
                      const SizedBox(width: 10),
                      Expanded(child: _MetricTile('Avg Loss', '₹${_inr.format((result.monteCarlo.costOfPanic['meanLoss'] ?? 0).toInt())}', AppColors.warnMid)),
                    ],
                  ),
                  if (result.monteCarlo.histogram.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text('Wealth Distribution', style: GoogleFonts.syne(
                      fontWeight: FontWeight.w700, fontSize: 12, color: AppColors.textSecondary,
                    )),
                    const SizedBox(height: 8),
                    SizedBox(height: 200, child: _MCHistogram(data: result.monteCarlo.histogram)),
                  ],
                ],
              ),
            ),

            // ──── Conclusion ────
            _ConclusionCard(result: result),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}

// ═══════ Reusable widgets ═══════

class _SectionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Widget child;
  const _SectionCard({required this.title, required this.icon, required this.child});
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: AppColors.bgCard.withAlpha(210),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: AppColors.glassBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 30, height: 30,
                  decoration: BoxDecoration(color: AppColors.accentLight, borderRadius: BorderRadius.circular(8)),
                  child: Icon(icon, color: AppColors.accent, size: 16),
                ),
                const SizedBox(width: 10),
                Text(title, style: GoogleFonts.syne(fontWeight: FontWeight.w700, fontSize: 15, color: AppColors.text)),
              ],
            ),
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }
}

class _StatRow extends StatelessWidget {
  final String label, value;
  const _StatRow(this.label, this.value);
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: GoogleFonts.dmSans(fontSize: 12, color: AppColors.textMuted)),
          Text(value, style: GoogleFonts.dmMono(fontSize: 12, fontWeight: FontWeight.w500, color: AppColors.text)),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  final String text;
  final Color color, bg;
  const _Badge({required this.text, required this.color, required this.bg});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8)),
      child: Text(text, style: GoogleFonts.dmMono(fontSize: 11, fontWeight: FontWeight.w600, color: color)),
    );
  }
}

class _VerdictBadge extends StatelessWidget {
  final bool detected;
  final String label;
  const _VerdictBadge({required this.detected, required this.label});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: detected ? AppColors.downBg : AppColors.upBg,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(detected ? Icons.warning_rounded : Icons.check_circle_rounded,
            size: 14, color: detected ? AppColors.downMid : AppColors.upMid),
          const SizedBox(width: 6),
          Text(label, style: GoogleFonts.dmSans(
            fontSize: 11, fontWeight: FontWeight.w700, color: detected ? AppColors.down : AppColors.up,
            letterSpacing: 0.5,
          )),
        ],
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  final String label, value;
  final Color color;
  const _MetricTile(this.label, this.value, this.color);
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.bgWarm,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.glassBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: GoogleFonts.dmSans(fontSize: 10, color: AppColors.textMuted, fontWeight: FontWeight.w500)),
          const SizedBox(height: 4),
          Text(value, style: GoogleFonts.syne(fontSize: 16, fontWeight: FontWeight.w700, color: color)),
        ],
      ),
    );
  }
}

class _FactorBar extends StatelessWidget {
  final String label;
  final double score;
  final double weight;
  const _FactorBar(this.label, this.score, this.weight);
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: GoogleFonts.dmSans(fontSize: 11, color: AppColors.textSecondary)),
              Text('${score.toStringAsFixed(1)} · ${(weight * 100).toInt()}%',
                style: GoogleFonts.dmMono(fontSize: 10, color: AppColors.textMuted)),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: (score / 100).clamp(0, 1),
              minHeight: 5,
              backgroundColor: AppColors.bgWarm,
              valueColor: AlwaysStoppedAnimation(
                score >= 70 ? AppColors.downMid : score >= 40 ? AppColors.warnMid : AppColors.upMid,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ──── Panic Score Ring ────
class _PanicRing extends StatelessWidget {
  final double score;
  final String level;
  const _PanicRing({required this.score, required this.level});
  @override
  Widget build(BuildContext context) {
    final color = score >= 70 ? AppColors.downMid : score >= 40 ? AppColors.warnMid : AppColors.upMid;
    return SizedBox(
      width: 120, height: 120,
      child: Stack(
        alignment: Alignment.center,
        children: [
          SizedBox(
            width: 120, height: 120,
            child: CircularProgressIndicator(
              value: (score / 100).clamp(0, 1),
              strokeWidth: 10,
              backgroundColor: AppColors.bgWarm,
              valueColor: AlwaysStoppedAnimation(color),
              strokeCap: StrokeCap.round,
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(score.toStringAsFixed(0), style: GoogleFonts.syne(
                fontWeight: FontWeight.w800, fontSize: 26, color: color,
              )),
              Text(level, style: GoogleFonts.dmSans(
                fontSize: 9, fontWeight: FontWeight.w700, color: AppColors.textMuted,
                letterSpacing: 0.5,
              )),
            ],
          ),
        ],
      ),
    );
  }
}

// ──── Conclusion Card ────
class _ConclusionCard extends StatelessWidget {
  final AnalysisResult result;
  const _ConclusionCard({required this.result});
  @override
  Widget build(BuildContext context) {
    final h = result.herding;
    final p = result.panic;
    final b = result.behaviorGap;
    final mc = result.monteCarlo;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.bgCard.withAlpha(220),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.accentMid.withAlpha(30)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            height: 3, width: double.infinity,
            decoration: BoxDecoration(
              color: AppColors.accentMid,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 14),
          Text('Conclusion', style: GoogleFonts.syne(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.text)),
          const SizedBox(height: 14),
          _ConclusionItem(
            icon: Icons.psychology_rounded,
            title: 'Herding',
            text: h.herdingDetected
              ? 'Significant herd behavior detected in the ${h.sector} sector (γ₂ = ${h.gamma2.toStringAsFixed(4)}, p = ${h.pValue.toStringAsFixed(4)}). Intensity: ${h.intensity.toStringAsFixed(1)}/100.'
              : 'No significant herding detected in the ${h.sector} sector. Stock returns disperse naturally.',
            color: h.herdingDetected ? AppColors.downMid : AppColors.upMid,
          ),
          const SizedBox(height: 10),
          _ConclusionItem(
            icon: Icons.warning_amber_rounded,
            title: 'Panic Level',
            text: 'Panic score: ${p.panicScore.toStringAsFixed(1)}/100 (${p.level}). ${p.panicScore >= 50 ? "Elevated panic detected — consider staying disciplined." : "Market conditions appear relatively calm."}',
            color: p.panicScore >= 50 ? AppColors.downMid : AppColors.upMid,
          ),
          const SizedBox(height: 10),
          _ConclusionItem(
            icon: Icons.trending_up_rounded,
            title: 'Behavior Gap',
            text: 'Emotional trading costs an estimated ${b.behaviorGap.toStringAsFixed(2)}% CAGR per year. Investment CAGR: ${b.investmentCagr.toStringAsFixed(2)}% vs Investor CAGR: ${b.investorCagr.toStringAsFixed(2)}%.',
            color: b.behaviorGap > 2 ? AppColors.warnMid : AppColors.upMid,
          ),
          const SizedBox(height: 10),
          _ConclusionItem(
            icon: Icons.casino_rounded,
            title: 'SIP vs Panic',
            text: 'Across ${mc.nSimulations} simulations, disciplined SIP wins ${(mc.costOfPanic['winRate'] ?? 0).toStringAsFixed(1)}% of the time. Average panic loss: ₹${_inr.format((mc.costOfPanic['meanLoss'] ?? 0).toInt())}.',
            color: (mc.costOfPanic['winRate'] ?? 0) > 70 ? AppColors.upMid : AppColors.warnMid,
          ),
          const SizedBox(height: 16),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.accentFaint,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Text(
              '💡 Stay disciplined. SIP beats panic selling in the vast majority of market scenarios. Avoid being a sheep — think independently.',
              style: GoogleFonts.dmSans(fontSize: 12, color: AppColors.accent, fontWeight: FontWeight.w500, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }
}

class _ConclusionItem extends StatelessWidget {
  final IconData icon;
  final String title, text;
  final Color color;
  const _ConclusionItem({required this.icon, required this.title, required this.text, required this.color});
  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 26, height: 26,
          decoration: BoxDecoration(
            color: color.withAlpha(25),
            borderRadius: BorderRadius.circular(7),
          ),
          child: Icon(icon, size: 14, color: color),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: GoogleFonts.syne(fontWeight: FontWeight.w700, fontSize: 12, color: AppColors.text)),
              const SizedBox(height: 2),
              Text(text, style: GoogleFonts.dmSans(fontSize: 11, color: AppColors.textSecondary, height: 1.5)),
            ],
          ),
        ),
      ],
    );
  }
}

// ═══════ Charts ═══════

class _PriceLineChart extends StatelessWidget {
  final List<PricePoint> data;
  const _PriceLineChart({required this.data});
  @override
  Widget build(BuildContext context) {
    if (data.isEmpty) return const SizedBox.shrink();
    final spots = data.asMap().entries.map((e) =>
      FlSpot(e.key.toDouble(), e.value.close),
    ).toList();
    final minY = data.map((d) => d.close).reduce((a, b) => a < b ? a : b);
    final maxY = data.map((d) => d.close).reduce((a, b) => a > b ? a : b);
    final range = maxY - minY;
    return LineChart(LineChartData(
      gridData: FlGridData(show: false),
      titlesData: FlTitlesData(show: false),
      borderData: FlBorderData(show: false),
      minY: minY - range * 0.1,
      maxY: maxY + range * 0.1,
      lineBarsData: [
        LineChartBarData(
          spots: spots,
          isCurved: true,
          curveSmoothness: 0.25,
          color: AppColors.accentMid,
          barWidth: 2,
          dotData: FlDotData(show: false),
          belowBarData: BarAreaData(
            show: true,
            color: AppColors.accentMid.withAlpha(20),
          ),
        ),
      ],
      lineTouchData: LineTouchData(
        touchTooltipData: LineTouchTooltipData(
          getTooltipItems: (spots) => spots.map((s) =>
            LineTooltipItem('₹${s.y.toStringAsFixed(2)}', GoogleFonts.dmMono(fontSize: 11, color: AppColors.text)),
          ).toList(),
        ),
      ),
    ));
  }
}

class _CSADChart extends StatelessWidget {
  final List<CSADPoint> data;
  const _CSADChart({required this.data});
  @override
  Widget build(BuildContext context) {
    return ScatterChart(ScatterChartData(
      gridData: FlGridData(show: false),
      titlesData: FlTitlesData(show: false),
      borderData: FlBorderData(show: false),
      scatterSpots: data.map((d) => ScatterSpot(
        d.absReturn, d.csad,
        dotPainter: FlDotCirclePainter(
          radius: 2.5,
          color: AppColors.accentMid.withAlpha(120),
          strokeWidth: 0,
        ),
      )).toList(),
      scatterTouchData: ScatterTouchData(enabled: false),
    ));
  }
}

class _VolumeChart extends StatelessWidget {
  final List<VolumePoint> data;
  const _VolumeChart({required this.data});
  @override
  Widget build(BuildContext context) {
    final maxVol = data.map((d) => d.volume).reduce((a, b) => a > b ? a : b).toDouble();
    return BarChart(BarChartData(
      gridData: FlGridData(show: false),
      titlesData: FlTitlesData(show: false),
      borderData: FlBorderData(show: false),
      maxY: maxVol * 1.1,
      barGroups: data.asMap().entries.map((e) => BarChartGroupData(
        x: e.key,
        barRods: [
          BarChartRodData(
            toY: e.value.volume.toDouble(),
            width: 3,
            color: e.value.isPanic ? AppColors.downMid : AppColors.accentMid.withAlpha(120),
            borderRadius: BorderRadius.circular(1),
          ),
        ],
      )).toList(),
      barTouchData: BarTouchData(enabled: false),
    ));
  }
}

class _MCHistogram extends StatelessWidget {
  final List<HistogramBin> data;
  const _MCHistogram({required this.data});
  @override
  Widget build(BuildContext context) {
    final maxVal = data.fold<int>(0, (m, d) => [m, d.sip, d.panic].reduce((a, b) => a > b ? a : b));
    return BarChart(BarChartData(
      gridData: FlGridData(show: false),
      titlesData: FlTitlesData(show: false),
      borderData: FlBorderData(show: false),
      maxY: maxVal * 1.15,
      barGroups: data.asMap().entries.map((e) => BarChartGroupData(
        x: e.key,
        barsSpace: 1,
        barRods: [
          BarChartRodData(toY: e.value.sip.toDouble(), width: 5, color: AppColors.upMid.withAlpha(180), borderRadius: BorderRadius.circular(2)),
          BarChartRodData(toY: e.value.panic.toDouble(), width: 5, color: AppColors.downMid.withAlpha(180), borderRadius: BorderRadius.circular(2)),
        ],
      )).toList(),
      barTouchData: BarTouchData(enabled: false),
    ));
  }
}

String _formatLargeNum(double n) {
  if (n >= 1e12) return '${(n / 1e12).toStringAsFixed(2)}T';
  if (n >= 1e9) return '${(n / 1e9).toStringAsFixed(2)}B';
  if (n >= 1e7) return '${(n / 1e7).toStringAsFixed(2)}Cr';
  if (n >= 1e5) return '${(n / 1e5).toStringAsFixed(2)}L';
  return _inr.format(n.toInt());
}
