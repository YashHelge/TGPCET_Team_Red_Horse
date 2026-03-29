import 'package:flutter_test/flutter_test.dart';
import 'package:binary_investor/main.dart';

void main() {
  testWidgets('App renders', (WidgetTester tester) async {
    await tester.pumpWidget(const BinaryInvestorApp());
    expect(find.text('Binary Investor'), findsOneWidget);
  });
}
