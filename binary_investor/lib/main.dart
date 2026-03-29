import 'package:flutter/material.dart';
import 'app_theme.dart';
import 'home_screen.dart';
import 'copilot_screen.dart';

void main() {
  runApp(const BinaryInvestorApp());
}

class BinaryInvestorApp extends StatelessWidget {
  const BinaryInvestorApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Binary Investor',
      theme: AppTheme.theme,
      debugShowCheckedModeBanner: false,
      home: const MainShell(),
    );
  }
}

class MainShell extends StatefulWidget {
  const MainShell({super.key});
  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  final _pages = const <Widget>[
    HomeScreen(),
    CopilotScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.insights_rounded),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.smart_toy_rounded),
            label: 'AI Copilot',
          ),
        ],
      ),
    );
  }
}
