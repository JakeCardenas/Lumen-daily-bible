import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/features/bible/bible_screen.dart';
import 'package:lumen/features/bible/chapter_screen.dart';

import '../support/harness.dart';

void main() {
  testWidgets('lists books with Douay-Rheims and modern names', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const BibleScreen()));
    expect(find.text('Old Testament'), findsOneWidget);
    expect(find.text('Isaias'), findsOneWidget);
    expect(find.text('Isaiah'), findsOneWidget);
    expect(find.text('New Testament'), findsOneWidget);
  });

  testWidgets('opens a chapter from the book list', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const BibleScreen()));
    await tester.tap(find.text('Genesis'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('1'));
    await tester.pumpAndSettle();
    expect(find.text('Genesis 1'), findsOneWidget);
    expect(find.textContaining('In the beginning'), findsOneWidget);
  });

  testWidgets('a reference search offers both psalm numberings', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const BibleScreen()));
    await tester.enterText(find.byType(TextField), 'Psalm 23');
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('Go to Psalm 22'), findsOneWidget);
    expect(find.text('Psalm 23 in most modern Bibles'), findsOneWidget);
    expect(find.text('Go to Psalm 23'), findsOneWidget);
    await tester.tap(find.text('Go to Psalm 22'));
    await tester.pumpAndSettle();
    expect(find.textContaining('The Lord ruleth me'), findsOneWidget);
  });

  testWidgets('a word search lists matching verses and Clear returns to the books', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const BibleScreen()));
    await tester.enterText(find.byType(TextField), 'loved world');
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('1 verse found'), findsOneWidget);
    expect(find.text('John 3:16'), findsOneWidget);
    await tester.tap(find.text('Clear'));
    await tester.pump();
    expect(find.text('Old Testament'), findsOneWidget);
  });

  testWidgets('selecting verses and saving creates a bookmark', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const ChapterScreen(bookId: 'PSA', chapter: 22)));
    expect(find.text('Psalm 22'), findsOneWidget);
    await tester.tap(find.textContaining('The Lord ruleth me'));
    await tester.tap(find.textContaining('He hath set me'));
    await tester.pump();
    expect(find.text('2 verses selected'), findsOneWidget);
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(deps.bookmarks.items.single.label, 'Psalm 22:1-2');
    expect(find.text('2 verses selected'), findsNothing);
  });

  testWidgets('moves between chapters', (tester) async {
    final deps = await TestDeps.create();
    await tester.pumpWidget(deps.wrap(const ChapterScreen(bookId: 'JHN', chapter: 2)));
    await tester.tap(find.text('Next chapter'));
    await tester.pumpAndSettle();
    expect(find.text('John 3'), findsOneWidget);
    final next = tester.widget<OutlinedButton>(find.widgetWithText(OutlinedButton, 'Next chapter'));
    expect(next.onPressed, isNull);
  });
}
