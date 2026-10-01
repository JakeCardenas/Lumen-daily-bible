import 'package:flutter/material.dart';

/// Lumen's warm, light palette.
abstract final class LumenColors {
  static const background = Color(0xFFFBF7F0);
  static const surface = Color(0xFFFFFDF8);
  static const surfaceMuted = Color(0xFFF3ECE0);
  static const ink = Color(0xFF2B2620);
  static const inkMuted = Color(0xFF6B6157);
  static const accent = Color(0xFF8A5A2B);
  static const divider = Color(0xFFE6DCCB);
  static const error = Color(0xFF9A3B2E);
}

const scriptureFontFamily = 'Literata';

ThemeData lumenTheme() {
  final scheme = ColorScheme.fromSeed(seedColor: LumenColors.accent).copyWith(
    primary: LumenColors.accent,
    onPrimary: Colors.white,
    surface: LumenColors.surface,
    onSurface: LumenColors.ink,
    onSurfaceVariant: LumenColors.inkMuted,
    outline: LumenColors.divider,
    outlineVariant: LumenColors.divider,
    error: LumenColors.error,
    surfaceContainerLowest: LumenColors.surface,
    surfaceContainerLow: LumenColors.background,
    surfaceContainer: LumenColors.surfaceMuted,
    surfaceContainerHigh: LumenColors.surfaceMuted,
    surfaceContainerHighest: LumenColors.surfaceMuted,
    secondaryContainer: LumenColors.surfaceMuted,
    onSecondaryContainer: LumenColors.ink,
  );
  final base = ThemeData(colorScheme: scheme, useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: LumenColors.background,
    appBarTheme: const AppBarTheme(
      backgroundColor: LumenColors.background,
      foregroundColor: LumenColors.ink,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
    ),
    navigationBarTheme: const NavigationBarThemeData(
      backgroundColor: LumenColors.surface,
      indicatorColor: LumenColors.surfaceMuted,
      labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
    ),
    dividerTheme: const DividerThemeData(color: LumenColors.divider, thickness: 1),
    textTheme: base.textTheme.apply(bodyColor: LumenColors.ink, displayColor: LumenColors.ink),
  );
}

/// Body text style for Scripture passages.
TextStyle scriptureStyle(BuildContext context) =>
    (Theme.of(context).textTheme.bodyLarge ?? const TextStyle()).copyWith(
      fontFamily: scriptureFontFamily,
      fontSize: 18,
      height: 1.6,
      color: LumenColors.ink,
    );
