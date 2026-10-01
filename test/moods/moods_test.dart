import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/moods/moods.dart';

import '../support/moods_fixture.dart';

void main() {
  test('reads moods and entries', () {
    final library = fixtureMoods();
    expect(library.moods.map((m) => m.id), ['sad', 'grateful']);
    final sad = library.moods.first;
    expect(sad.crisisLine, isTrue);
    expect(sad.entries.first.modernReference, 'Psalm 23');
    expect(sad.entries.first.passage.bookId, 'PSA');
    expect(sad.entries.last.modernReference, isNull);
  });

  test('support messages use the agreed wording', () {
    expect(moodDisclaimer,
        'These readings offer spiritual encouragement. They are not a substitute for care from a doctor or counselor.');
    expect(crisisMessage, contains('call or text 988 (US) or your local emergency number'));
  });

  test('the first entry shown changes by day and stays in range', () {
    final indexes = {for (var d = 1; d <= 10; d++) moodStartIndex(DateTime(2026, 10, d), 5)};
    expect(indexes, {0, 1, 2, 3, 4});
    expect(moodStartIndex(DateTime(2026, 10, 4, 23), 5), moodStartIndex(DateTime(2026, 10, 4, 1), 5));
    expect(moodStartIndex(DateTime(2025, 1, 1), 3), inInclusiveRange(0, 2));
    expect(moodStartIndex(DateTime(2026, 1, 1), 0), 0);
  });
}
