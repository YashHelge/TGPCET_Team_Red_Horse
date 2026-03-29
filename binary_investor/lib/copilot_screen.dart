import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'models.dart';
import 'api_service.dart';
import 'app_theme.dart';

class CopilotScreen extends StatefulWidget {
  final AnalysisResult? result;
  const CopilotScreen({super.key, this.result});
  @override
  State<CopilotScreen> createState() => _CopilotScreenState();
}

class _CopilotScreenState extends State<CopilotScreen> {
  final List<ChatMessage> _messages = [];
  final _inputCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _loading = false;

  String get _context {
    final r = widget.result;
    if (r == null) return '';
    return 'Analyzing: ${r.quote.name} (${r.quote.symbol})\n'
        'Price: ₹${r.quote.price} | Change: ${r.quote.changePct.toStringAsFixed(2)}%\n'
        'Herding: ${r.herding.herdingDetected ? "DETECTED" : "NOT detected"} | Intensity: ${r.herding.intensity.toStringAsFixed(2)}\n'
        'Panic Score: ${r.panic.panicScore.toStringAsFixed(1)} (${r.panic.level})\n'
        'Behavior Gap: ${r.behaviorGap.behaviorGap.toStringAsFixed(2)}% per year\n'
        'P/E Ratio: ${r.quote.peRatio} | Market Cap: ₹${r.quote.marketCap}';
  }

  List<_QuickAction> get _quickActions {
    final r = widget.result;
    if (r != null) {
      return [
        _QuickAction('🐑', 'Am I being a sheep?', 'I\'m looking at ${r.quote.name}. The herding score is ${r.herding.intensity.toStringAsFixed(2)}. Am I falling into herd mentality?'),
        _QuickAction('😰', 'Should I worry?', '${r.quote.name} has a panic score of ${r.panic.panicScore.toStringAsFixed(1)} (${r.panic.level}). What should I do?'),
        _QuickAction('💡', 'Explain the gap', 'My behavior gap for ${r.quote.name} is ${r.behaviorGap.behaviorGap.toStringAsFixed(2)}% per year. What does this mean in rupees?'),
      ];
    }
    return [
      _QuickAction('🐑', 'What is herd mentality?', 'Explain herd mentality in Indian stock markets with examples.'),
      _QuickAction('😰', 'How to avoid panic?', 'How do I avoid panic selling during a market crash?'),
      _QuickAction('💰', 'Why SIP beats timing?', 'Why does SIP beat market timing for most Indian investors?'),
    ];
  }

  Future<void> _send(String text) async {
    if (text.trim().isEmpty || _loading) return;
    final userMsg = ChatMessage(role: 'user', content: text.trim());
    setState(() {
      _messages.add(userMsg);
      _loading = true;
    });
    _inputCtrl.clear();
    _scrollToBottom();

    try {
      final response = await ApiService.chat(_messages, _context);
      setState(() => _messages.add(ChatMessage(role: 'assistant', content: response)));
    } catch (e) {
      setState(() => _messages.add(ChatMessage(role: 'assistant', content: '⚠️ Could not reach AI server.')));
    }
    setState(() => _loading = false);
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 30, height: 30,
              decoration: BoxDecoration(
                color: AppColors.accentLight,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.smart_toy_rounded, color: AppColors.accent, size: 16),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('AI Copilot', style: GoogleFonts.syne(
                  fontWeight: FontWeight.w700, fontSize: 15, color: AppColors.text,
                )),
                Text('llama-3.3-70b', style: GoogleFonts.dmMono(
                  fontSize: 10, color: AppColors.textMuted,
                )),
              ],
            ),
          ],
        ),
        actions: [
          if (_messages.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.refresh_rounded, size: 20),
              onPressed: () => setState(() => _messages.clear()),
              tooltip: 'Clear chat',
            ),
        ],
      ),
      body: Column(
        children: [
          // Messages area
          Expanded(
            child: _messages.isEmpty
              ? _buildEmptyState()
              : ListView.builder(
                  controller: _scrollCtrl,
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  itemCount: _messages.length + (_loading ? 1 : 0),
                  itemBuilder: (context, i) {
                    if (i == _messages.length && _loading) {
                      return _buildLoadingBubble();
                    }
                    final msg = _messages[i];
                    return _buildMessageBubble(msg);
                  },
                ),
          ),

          // Input area
          Container(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 20),
            decoration: BoxDecoration(
              color: AppColors.bgCard,
              border: Border(top: BorderSide(color: AppColors.glassBorder)),
            ),
            child: SafeArea(
              top: false,
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _inputCtrl,
                      maxLines: 3,
                      minLines: 1,
                      textInputAction: TextInputAction.send,
                      onSubmitted: _send,
                      decoration: InputDecoration(
                        hintText: 'Ask about investing biases...',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(color: AppColors.glassBorder),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    decoration: BoxDecoration(
                      color: AppColors.accent,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: IconButton(
                      icon: const Icon(Icons.send_rounded, color: Colors.white, size: 18),
                      onPressed: () => _send(_inputCtrl.text),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const SizedBox(height: 24),
          Container(
            width: 64, height: 64,
            decoration: BoxDecoration(
              color: AppColors.accentLight,
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(Icons.smart_toy_rounded, color: AppColors.accent, size: 28),
          ),
          const SizedBox(height: 16),
          Text('Ask me anything', style: GoogleFonts.syne(
            fontWeight: FontWeight.w800, fontSize: 24, color: AppColors.text,
          )),
          const SizedBox(height: 8),
          Text(
            widget.result != null
              ? 'Ask about ${widget.result!.quote.name} analysis'
              : 'Your behavioral finance advisor for Indian stocks',
            style: GoogleFonts.dmSans(fontSize: 13, color: AppColors.textSecondary),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 28),
          ..._quickActions.map((a) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Material(
              color: AppColors.bgCard.withAlpha(210),
              borderRadius: BorderRadius.circular(16),
              child: InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () => _send(a.prompt),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.glassBorder),
                  ),
                  child: Row(
                    children: [
                      Text(a.icon, style: const TextStyle(fontSize: 20)),
                      const SizedBox(width: 12),
                      Expanded(child: Text(a.label, style: GoogleFonts.dmSans(
                        fontSize: 13, fontWeight: FontWeight.w500, color: AppColors.text,
                      ))),
                      const Icon(Icons.arrow_forward_ios_rounded, size: 12, color: AppColors.textDim),
                    ],
                  ),
                ),
              ),
            ),
          )),
          const SizedBox(height: 16),
          Text(
            'Powered by Groq · llama-3.3-70b · Educational use only',
            style: GoogleFonts.dmSans(fontSize: 10, color: AppColors.textDim),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg) {
    final isUser = msg.role == 'user';
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Padding(
              padding: const EdgeInsets.only(bottom: 4, left: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 20, height: 20,
                    decoration: BoxDecoration(
                      color: AppColors.accentLight,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: const Icon(Icons.smart_toy_rounded, size: 11, color: AppColors.accent),
                  ),
                  const SizedBox(width: 6),
                  Text('AI COPILOT', style: GoogleFonts.dmSans(
                    fontSize: 9, fontWeight: FontWeight.w700, color: AppColors.accent,
                    letterSpacing: 0.8,
                  )),
                ],
              ),
            ),
          ],
          Container(
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.82),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isUser ? AppColors.accentLight : AppColors.bgCard.withAlpha(220),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(18),
                topRight: const Radius.circular(18),
                bottomLeft: Radius.circular(isUser ? 18 : 4),
                bottomRight: Radius.circular(isUser ? 4 : 18),
              ),
              border: Border.all(color: isUser
                ? AppColors.accentMid.withAlpha(35)
                : AppColors.glassBorder),
            ),
            child: isUser
              ? Text(msg.content, style: GoogleFonts.dmSans(fontSize: 13, color: AppColors.text, height: 1.5))
              : MarkdownBody(
                  data: msg.content,
                  styleSheet: MarkdownStyleSheet(
                    p: GoogleFonts.dmSans(fontSize: 13, color: AppColors.text, height: 1.6),
                    strong: GoogleFonts.dmSans(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.text),
                    h1: GoogleFonts.syne(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.text),
                    h2: GoogleFonts.syne(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.text),
                    h3: GoogleFonts.syne(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.text),
                    listBullet: GoogleFonts.dmSans(fontSize: 13, color: AppColors.textSecondary),
                    code: GoogleFonts.dmMono(fontSize: 11, color: AppColors.textSecondary, backgroundColor: AppColors.bgWarm),
                    codeblockDecoration: BoxDecoration(
                      color: AppColors.bgWarm,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppColors.glassBorder),
                    ),
                    blockquoteDecoration: BoxDecoration(
                      color: AppColors.accentFaint,
                      border: Border(left: BorderSide(color: AppColors.accentMid, width: 3)),
                    ),
                  ),
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingBubble() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.bgCard.withAlpha(220),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(18),
              topRight: Radius.circular(18),
              bottomRight: Radius.circular(18),
              bottomLeft: Radius.circular(4),
            ),
            border: Border.all(color: AppColors.glassBorder),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 14, height: 14,
                child: CircularProgressIndicator(
                  strokeWidth: 2, color: AppColors.accent,
                ),
              ),
              const SizedBox(width: 10),
              Text('Thinking...', style: GoogleFonts.dmSans(fontSize: 12, color: AppColors.textMuted)),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }
}

class _QuickAction {
  final String icon, label, prompt;
  _QuickAction(this.icon, this.label, this.prompt);
}
