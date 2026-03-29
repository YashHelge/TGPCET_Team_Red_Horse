import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  static const bg = Color(0xFFF0EDE8);
  static const bgWarm = Color(0xFFF7F5F0);
  static const bgCard = Color(0xFFFDFCFB);

  static const text = Color(0xFF16120C);
  static const textSecondary = Color(0xFF4A3F30);
  static const textMuted = Color(0xFF8C7B65);
  static const textDim = Color(0xFFBDB09F);

  static const accent = Color(0xFF3730A3);
  static const accentMid = Color(0xFF6366F1);
  static const accentLight = Color(0xFFEEF0FF);
  static const accentFaint = Color(0xFFF5F5FF);

  static const up = Color(0xFF065F46);
  static const upMid = Color(0xFF059669);
  static const upBg = Color(0xFFECFDF5);

  static const down = Color(0xFF991B1B);
  static const downMid = Color(0xFFDC2626);
  static const downBg = Color(0xFFFEF2F2);

  static const warn = Color(0xFF92400E);
  static const warnMid = Color(0xFFD97706);
  static const warnBg = Color(0xFFFFFBEB);

  static const glassBorder = Color(0x121E140A);
}

class AppTheme {
  static ThemeData get theme {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: AppColors.bg,
      colorScheme: ColorScheme.light(
        primary: AppColors.accent,
        secondary: AppColors.accentMid,
        surface: AppColors.bgCard,
        onPrimary: Colors.white,
        onSurface: AppColors.text,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.bg.withAlpha(210),
        elevation: 0,
        scrolledUnderElevation: 1,
        titleTextStyle: GoogleFonts.syne(
          color: AppColors.text, fontWeight: FontWeight.w700, fontSize: 18,
        ),
        iconTheme: const IconThemeData(color: AppColors.text),
      ),
      textTheme: TextTheme(
        displayLarge: GoogleFonts.syne(fontWeight: FontWeight.w800, color: AppColors.text),
        displayMedium: GoogleFonts.syne(fontWeight: FontWeight.w700, color: AppColors.text),
        headlineMedium: GoogleFonts.syne(fontWeight: FontWeight.w700, color: AppColors.text),
        titleLarge: GoogleFonts.syne(fontWeight: FontWeight.w700, color: AppColors.text, fontSize: 18),
        titleMedium: GoogleFonts.dmSans(fontWeight: FontWeight.w600, color: AppColors.text),
        bodyLarge: GoogleFonts.dmSans(color: AppColors.text, fontSize: 15),
        bodyMedium: GoogleFonts.dmSans(color: AppColors.textSecondary, fontSize: 13),
        bodySmall: GoogleFonts.dmSans(color: AppColors.textMuted, fontSize: 12),
        labelSmall: GoogleFonts.dmMono(color: AppColors.textMuted, fontSize: 10),
      ),
      cardTheme: CardThemeData(
        color: AppColors.bgCard.withAlpha(210),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: AppColors.glassBorder),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.accent,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          textStyle: GoogleFonts.dmSans(fontWeight: FontWeight.w600, fontSize: 14),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.bgWarm,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: AppColors.glassBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: AppColors.glassBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: AppColors.accentMid, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        hintStyle: GoogleFonts.dmSans(color: AppColors.textDim, fontSize: 14),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.bgCard,
        selectedItemColor: AppColors.accent,
        unselectedItemColor: AppColors.textMuted,
        elevation: 8,
        type: BottomNavigationBarType.fixed,
      ),
    );
  }
}
