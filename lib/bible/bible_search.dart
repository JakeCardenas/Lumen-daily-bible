import 'bible.dart';

class SearchResult {
  const SearchResult(this.verses, {required this.truncated, required this.terms});

  static const empty = SearchResult([], truncated: false, terms: []);

  final List<Verse> verses;
  final bool truncated;
  final List<String> terms;
}

const Map<int, String> _folded = {
  0xe0: 'a', 0xe1: 'a', 0xe2: 'a', 0xe4: 'a', 0xe6: 'ae', 0xe7: 'c', 0xe8: 'e', 0xe9: 'e', 0xea: 'e', //
  0xeb: 'e', 0xec: 'i', 0xed: 'i', 0xee: 'i', 0xef: 'i', 0xf1: 'n', 0xf2: 'o', 0xf3: 'o', 0xf4: 'o',
  0xf6: 'o', 0x153: 'oe', 0xf9: 'u', 0xfa: 'u', 0xfb: 'u', 0xfc: 'u',
};

/// Lowercase letters and digits only, accents folded, words separated by single spaces.
String normalizeForSearch(String input) {
  final buffer = StringBuffer();
  var pendingSpace = false;
  for (final rune in input.toLowerCase().runes) {
    final folded = _folded[rune];
    final isWordChar = (rune >= 0x61 && rune <= 0x7a) || (rune >= 0x30 && rune <= 0x39);
    if (folded == null && !isWordChar) {
      pendingSpace = buffer.isNotEmpty;
      continue;
    }
    if (pendingSpace) buffer.write(' ');
    pendingSpace = false;
    if (folded != null) {
      buffer.write(folded);
    } else {
      buffer.writeCharCode(rune);
    }
  }
  return buffer.toString();
}

/// Searchable words in a query: two characters or longer, without duplicates.
List<String> searchTerms(String query) =>
    normalizeForSearch(query).split(' ').where((t) => t.length >= 2).toSet().toList();

/// Word search over the whole Bible. Every term must begin a word in the verse.
class BibleSearch {
  BibleSearch(this._bible);

  final Bible _bible;
  List<(Verse, String)>? _index;
  String? _lastKey;
  SearchResult _last = SearchResult.empty;

  SearchResult search(String query, {int limit = 200}) {
    final terms = searchTerms(query);
    if (terms.isEmpty) return SearchResult.empty;
    final key = '${terms.join(' ')}|$limit';
    if (key == _lastKey) return _last;
    final hits = <Verse>[];
    var truncated = false;
    for (final (verse, text) in _index ??= _buildIndex()) {
      if (terms.every((term) => text.contains(' $term'))) {
        if (hits.length == limit) {
          truncated = true;
          break;
        }
        hits.add(verse);
      }
    }
    _lastKey = key;
    return _last = SearchResult(hits, truncated: truncated, terms: terms);
  }

  List<(Verse, String)> _buildIndex() => [
        for (final book in _bible.books)
          for (var c = 1; c <= book.chapterCount; c++)
            for (var v = 1; v <= book.verseCount(c); v++)
              if (book.chapters[c - 1][v - 1] case final text?)
                (Verse(book.id, c, v, text), ' ${normalizeForSearch(text)} '),
      ];
}
