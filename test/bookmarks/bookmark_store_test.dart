import 'package:flutter_test/flutter_test.dart';
import 'package:lumen/bible/scripture_ref.dart';
import 'package:lumen/bookmarks/bookmark.dart';
import 'package:lumen/bookmarks/bookmark_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../support/bible_fixture.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final bible = fixtureBible();
  const john = ScriptureRef('JHN', [VerseRange(3, 16, 3, 16)]);
  const psalm = ScriptureRef('PSA', [VerseRange(22, 1, 22, 4)]);

  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('creates bookmarks with a label and snippet', () {
    final bookmark = Bookmark.forPassage(bible, psalm, now: DateTime(2026, 10, 1));
    expect(bookmark.label, 'Psalm 22:1-4');
    expect(bookmark.snippet, startsWith('A psalm for David'));
    expect(bookmark.id, psalm.key);
  });

  test('shortens long snippets', () {
    final short = shortSnippet('word ' * 100);
    expect(short.length, lessThanOrEqualTo(160));
    expect(short, endsWith('…'));
    expect(shortSnippet('Brief.'), 'Brief.');
  });

  test('adds, persists newest first, and ignores duplicates', () async {
    final prefs = await SharedPreferences.getInstance();
    final store = BookmarkStore(prefs);
    await store.add(Bookmark.forPassage(bible, john, now: DateTime(2026, 10, 1)));
    await store.add(Bookmark.forPassage(bible, psalm, now: DateTime(2026, 10, 2)));
    await store.add(Bookmark.forPassage(bible, john, now: DateTime(2026, 10, 3)));
    expect(store.items.map((b) => b.label), ['Psalm 22:1-4', 'John 3:16']);
    expect(store.contains(john), isTrue);

    final reloaded = BookmarkStore(prefs);
    expect(reloaded.items.map((b) => b.label), ['Psalm 22:1-4', 'John 3:16']);
    expect(reloaded.items.last.savedAt, DateTime(2026, 10, 1));
    expect(reloaded.items.first.passage.ranges.single, const VerseRange(22, 1, 22, 4));
  });

  test('removes bookmarks', () async {
    final store = BookmarkStore(await SharedPreferences.getInstance());
    await store.add(Bookmark.forPassage(bible, john));
    await store.remove(john.key);
    expect(store.items, isEmpty);
    expect(store.contains(john), isFalse);
  });

  test('recovers from unreadable data without crashing', () async {
    SharedPreferences.setMockInitialValues({BookmarkStore.storageKey: '{not json'});
    final prefs = await SharedPreferences.getInstance();
    final store = BookmarkStore(prefs);
    expect(store.items, isEmpty);
    await Future<void>.delayed(Duration.zero);
    expect(prefs.getString(BookmarkStore.unreadableKey), '{not json');
    expect(prefs.getString(BookmarkStore.storageKey), isNull);
  });
}
