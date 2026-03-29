import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'models.dart';
import 'api_service.dart';
import 'app_theme.dart';
import 'report_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<StockInfo> _stocks = [];
  List<StockInfo> _filtered = [];
  StockInfo? _selected;
  bool _loadingStocks = true;
  bool _analyzing = false;
  final _searchCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadStocks();
  }

  Future<void> _loadStocks() async {
    try {
      final stocks = await ApiService.fetchStocks();
      setState(() {
        _stocks = stocks;
        _filtered = stocks;
        _loadingStocks = false;
      });
    } catch (e) {
      setState(() => _loadingStocks = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load stocks: $e'), backgroundColor: AppColors.downMid),
        );
      }
    }
  }

  void _filter(String q) {
    setState(() {
      _filtered = _stocks.where((s) =>
        s.name.toLowerCase().contains(q.toLowerCase()) ||
        s.symbol.toLowerCase().contains(q.toLowerCase()) ||
        s.sector.toLowerCase().contains(q.toLowerCase())
      ).toList();
    });
  }

  Future<void> _analyze() async {
    if (_selected == null) return;
    setState(() => _analyzing = true);
    try {
      final result = await ApiService.analyze(_selected!.symbol);
      if (mounted) {
        Navigator.push(context, MaterialPageRoute(
          builder: (_) => ReportScreen(result: result),
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Analysis failed: $e'), backgroundColor: AppColors.downMid),
        );
      }
    }
    if (mounted) setState(() => _analyzing = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 24),
              // Brand
              Row(
                children: [
                  Container(
                    width: 44, height: 44,
                    decoration: BoxDecoration(
                      color: AppColors.accentLight,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.insights_rounded, color: AppColors.accent, size: 22),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Binary Investor', style: GoogleFonts.syne(
                        fontWeight: FontWeight.w800, fontSize: 22, color: AppColors.text,
                        letterSpacing: -0.5,
                      )),
                      Text('Behavioral Bias Detector', style: GoogleFonts.dmSans(
                        fontSize: 12, color: AppColors.textMuted,
                      )),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // Hero text
              Text('Detect Your\nInvesting Biases', style: GoogleFonts.syne(
                fontWeight: FontWeight.w800, fontSize: 30, color: AppColors.text,
                height: 1.15, letterSpacing: -0.8,
              )),
              const SizedBox(height: 10),
              Text(
                'Select any Indian stock to get a one-tap behavioral analysis report with herding detection, panic scoring, and AI copilot.',
                style: GoogleFonts.dmSans(fontSize: 14, color: AppColors.textSecondary, height: 1.6),
              ),
              const SizedBox(height: 28),

              // Search
              TextField(
                controller: _searchCtrl,
                onChanged: _filter,
                decoration: InputDecoration(
                  hintText: 'Search stocks by name, symbol or sector...',
                  prefixIcon: const Icon(Icons.search_rounded, color: AppColors.textMuted, size: 20),
                  suffixIcon: _searchCtrl.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 18, color: AppColors.textMuted),
                        onPressed: () { _searchCtrl.clear(); _filter(''); },
                      )
                    : null,
                ),
              ),
              const SizedBox(height: 16),

              // Stock list
              if (_loadingStocks)
                const Center(child: Padding(
                  padding: EdgeInsets.all(40),
                  child: CircularProgressIndicator(color: AppColors.accent),
                ))
              else
                Container(
                  height: 300,
                  decoration: BoxDecoration(
                    color: AppColors.bgCard.withAlpha(210),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: AppColors.glassBorder),
                  ),
                  child: _filtered.isEmpty
                    ? Center(child: Text('No stocks found', style: GoogleFonts.dmSans(color: AppColors.textMuted)))
                    : ListView.separated(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        itemCount: _filtered.length,
                        separatorBuilder: (context2, index2) => Divider(height: 1, color: AppColors.glassBorder, indent: 16, endIndent: 16),
                        itemBuilder: (context, i) {
                          final stock = _filtered[i];
                          final selected = _selected?.symbol == stock.symbol;
                          return ListTile(
                            dense: true,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                            selected: selected,
                            selectedTileColor: AppColors.accentFaint,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            leading: Container(
                              width: 36, height: 36,
                              decoration: BoxDecoration(
                                color: selected ? AppColors.accentLight : AppColors.bgWarm,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              alignment: Alignment.center,
                              child: Text(
                                stock.name.substring(0, 1),
                                style: GoogleFonts.syne(
                                  fontWeight: FontWeight.w700, fontSize: 14,
                                  color: selected ? AppColors.accent : AppColors.textSecondary,
                                ),
                              ),
                            ),
                            title: Text(stock.name, style: GoogleFonts.dmSans(
                              fontWeight: FontWeight.w500, fontSize: 13, color: AppColors.text,
                            )),
                            subtitle: Text(stock.symbol, style: GoogleFonts.dmMono(
                              fontSize: 10, color: AppColors.textMuted,
                            )),
                            trailing: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppColors.bgWarm,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(stock.sector, style: GoogleFonts.dmSans(
                                fontSize: 9, fontWeight: FontWeight.w500, color: AppColors.textMuted,
                              )),
                            ),
                            onTap: () => setState(() => _selected = stock),
                          );
                        },
                      ),
                ),

              const SizedBox(height: 20),

              // Selected stock + Analyze button
              if (_selected != null) ...[
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.accentFaint,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.accentMid.withAlpha(40)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle_rounded, color: AppColors.accentMid, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(_selected!.name, style: GoogleFonts.dmSans(
                              fontWeight: FontWeight.w600, fontSize: 14, color: AppColors.text,
                            )),
                            Text('${_selected!.symbol} · ${_selected!.sector}', style: GoogleFonts.dmMono(
                              fontSize: 11, color: AppColors.textMuted,
                            )),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, size: 16, color: AppColors.textMuted),
                        onPressed: () => setState(() => _selected = null),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _selected != null && !_analyzing ? _analyze : null,
                  icon: _analyzing
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.bolt_rounded, size: 18),
                  label: Text(_analyzing ? 'Generating Report...' : 'Generate Report'),
                ),
              ),

              if (_analyzing)
                Padding(
                  padding: const EdgeInsets.only(top: 16),
                  child: Center(
                    child: Text(
                      'This may take 15-30 seconds...',
                      style: GoogleFonts.dmSans(fontSize: 12, color: AppColors.textMuted),
                    ),
                  ),
                ),

              const SizedBox(height: 32),

              // Info cards
              _InfoCard(
                icon: Icons.psychology_rounded,
                title: 'Herding Detection',
                desc: 'CCK econometric model to detect herd mentality across sector peers.',
              ),
              const SizedBox(height: 10),
              _InfoCard(
                icon: Icons.warning_amber_rounded,
                title: 'Panic Scanner',
                desc: '5-factor real-time panic scoring: volume anomaly, delivery, drawdown, divergence, volatility.',
              ),
              const SizedBox(height: 10),
              _InfoCard(
                icon: Icons.trending_up_rounded,
                title: 'Monte Carlo SIP vs Panic',
                desc: '500 simulations showing why disciplined SIP beats panic selling.',
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String title, desc;
  const _InfoCard({required this.icon, required this.title, required this.desc});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.bgCard.withAlpha(210),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.glassBorder),
      ),
      child: Row(
        children: [
          Container(
            width: 38, height: 38,
            decoration: BoxDecoration(
              color: AppColors.accentLight,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: AppColors.accent, size: 18),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: GoogleFonts.syne(fontWeight: FontWeight.w700, fontSize: 13, color: AppColors.text)),
                const SizedBox(height: 2),
                Text(desc, style: GoogleFonts.dmSans(fontSize: 11, color: AppColors.textMuted, height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
