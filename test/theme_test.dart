import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/theme.dart';

void main() {
  test('uses the warm light palette', () {
    final theme = lumenTheme();
    expect(theme.brightness, Brightness.light);
    expect(theme.scaffoldBackgroundColor, LumenColors.background);
    expect(theme.colorScheme.primary, LumenColors.accent);
    expect(theme.colorScheme.onSurface, LumenColors.ink);
  });

  testWidgets('scripture style uses Literata', (tester) async {
    late TextStyle style;
    await tester.pumpWidget(MaterialApp(
      theme: lumenTheme(),
      home: Builder(builder: (context) {
        style = scriptureStyle(context);
        return const SizedBox();
      }),
    ));
    expect(style.fontFamily, scriptureFontFamily);
    expect(style.height, 1.6);
  });
}
