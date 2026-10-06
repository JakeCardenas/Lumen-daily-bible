import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/scripture_ref.dart';
import 'package:lumen/theme.dart';
import 'package:lumen/widgets/passage_text.dart';

import '../support/bible_fixture.dart';

void main() {
  final bible = fixtureBible();

  Widget host(Widget child) => MaterialApp(theme: lumenTheme(), home: Scaffold(body: SingleChildScrollView(child: child)));

  testWidgets('shows verse numbers, and chapter labels when a passage spans chapters', (tester) async {
    await tester.pumpWidget(host(PassageText(verses: bible.versesFor(const ScriptureRef('PSA', [VerseRange(21, 5, 22, 1)])))));
    expect(find.text('Chapter 21'), findsOneWidget);
    expect(find.text('Chapter 22'), findsOneWidget);
    expect(find.textContaining('5  Psalms 21:5 placeholder.'), findsOneWidget);
  });

  testWidgets('omits chapter labels within one chapter', (tester) async {
    await tester.pumpWidget(host(PassageText(verses: bible.chapter('GEN', 1))));
    expect(find.textContaining('Chapter'), findsNothing);
  });

  testWidgets('tapping a selectable verse reports it', (tester) async {
    int? tapped;
    await tester.pumpWidget(host(PassageText(verses: bible.chapter('GEN', 1), onVerseTap: (v) => tapped = v.number)));
    await tester.tap(find.textContaining('Be light made'));
    expect(tapped, 3);
  });

  testWidgets('explains a missing passage', (tester) async {
    await tester.pumpWidget(host(const PassageText(verses: [])));
    expect(find.text('This passage is not available in the Douay-Rheims text.'), findsOneWidget);
  });
}
