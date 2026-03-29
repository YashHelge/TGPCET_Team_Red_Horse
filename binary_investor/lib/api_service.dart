import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models.dart';

class ApiService {
  static const String baseUrl = 'https://tgpcet-team-red-horse.onrender.com';

  static Future<List<StockInfo>> fetchStocks() async {
    final res = await http.get(Uri.parse('$baseUrl/api/stocks'));
    if (res.statusCode == 200) {
      final data = json.decode(res.body);
      return (data['stocks'] as List).map((e) => StockInfo.fromJson(e)).toList();
    }
    throw Exception('Failed to load stocks');
  }

  static Future<AnalysisResult> analyze(String symbol) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/analyze'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'symbol': symbol,
        'periodDays': 365,
        'sipAmount': 10000,
        'simYears': 10,
        'nSimulations': 500,
      }),
    );
    if (res.statusCode == 200) {
      return AnalysisResult.fromJson(json.decode(res.body));
    }
    throw Exception('Analysis failed: ${res.statusCode}');
  }

  static Future<String> chat(List<ChatMessage> messages, String context) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/chat'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'messages': messages.map((m) => {'role': m.role, 'content': m.content}).toList(),
        'context': context,
      }),
    );
    if (res.statusCode == 200) {
      return json.decode(res.body)['response'] ?? 'No response';
    }
    throw Exception('Chat failed');
  }
}
