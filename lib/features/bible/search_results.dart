import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../bible/bible.dart';
import '../../bible/bible_search.dart';
import '../../bible/reference_label.dart';
import '../../bible/reference_parser.dart';
import '../../theme.dart';
import 'chapter_screen.dart';

/// References first ("Go to John 3:16"), then verses containing every searched word.
class SearchResults extends StatelessWidget {
  const SearchResults({super.key, required this.query});

  final String query;

  @override
  Widget build(BuildContext context) {
    final bible = context.read<Bible>();
    final references = context.read<ReferenceParser>().parse(query);
    final result = context.read<BibleSearch>().search(query);
    final theme = Theme.of(context);
    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        for (final match in references)
          ListTile(
            title: Text('Go to ${match.label}'),
            subtitle: match.note == null ? null : Text(match.note!),
            onTap: () => _open(context, match.bookId, match.chapter, match.verse),
          ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: Text(_summary(result, hasReferences: references.isNotEmpty), style: theme.textTheme.labelLarge),
        ),
        for (final verse in result.verses)
          ListTile(
            title: Text(verseLabel(bible, verse)),
            subtitle: HighlightedText(text: verse.text, terms: result.terms),
            onTap: () => _open(context, verse.bookId, verse.chapter, verse.number),
          ),
        if (result.truncated)
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text('Showing the first ${result.verses.length} verses. Add another word to narrow the search.',
                style: theme.textTheme.bodySmall?.copyWith(color: LumenColors.inkMuted)),
          ),
      ],
    );
  }

  static String _summary(SearchResult result, {required bool hasReferences}) {
    final count = result.verses.length;
    if (count == 0) return hasReferences ? 'No verses contain these words.' : 'No verses found.';
    return '$count${result.truncated ? '+' : ''} ${count == 1 ? 'verse' : 'verses'} found';
  }

  void _open(BuildContext context, String bookId, int chapter, int? verse) {
    Navigator.of(context).push(MaterialPageRoute<void>(
        builder: (_) => ChapterScreen(bookId: bookId, chapter: chapter, focusVerse: verse)));
  }
}

/// Verse text with the searched words in bold.
class HighlightedText extends StatelessWidget {
  const HighlightedText({super.key, required this.text, required this.terms});

  final String text;
  final List<String> terms;

  @override
  Widget build(BuildContext context) {
    final spans = <TextSpan>[];
    if (terms.isEmpty) {
      spans.add(TextSpan(text: text));
    } else {
      final pattern = RegExp('\\b(${terms.map(RegExp.escape).join('|')})', caseSensitive: false);
      var start = 0;
      for (final match in pattern.allMatches(text)) {
        if (match.start > start) spans.add(TextSpan(text: text.substring(start, match.start)));
        spans.add(TextSpan(text: match[0], style: const TextStyle(fontWeight: FontWeight.w600, color: LumenColors.ink)));
        start = match.end;
      }
      if (start < text.length) spans.add(TextSpan(text: text.substring(start)));
    }
    return Text.rich(TextSpan(children: spans), maxLines: 3, overflow: TextOverflow.ellipsis);
  }
}
