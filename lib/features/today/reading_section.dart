import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../bible/bible.dart';
import '../../bookmarks/bookmark.dart';
import '../../bookmarks/bookmark_store.dart';
import '../../liturgy/liturgy.dart';
import '../../theme.dart';
import '../../widgets/passage_text.dart';

/// One reading: its label, the Lectionary citation, notes about numbering, and the Douay-Rheims text.
class ReadingSection extends StatelessWidget {
  const ReadingSection({super.key, required this.reading});

  final Reading reading;

  @override
  Widget build(BuildContext context) {
    final bible = context.read<Bible>();
    final bookmarks = context.watch<BookmarkStore>();
    final theme = Theme.of(context);
    final small = theme.textTheme.bodySmall?.copyWith(color: LumenColors.inkMuted);
    final passage = reading.passages.first;
    final saved = bookmarks.contains(passage);
    return Padding(
      padding: const EdgeInsets.only(top: 28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(reading.label, style: theme.textTheme.labelLarge?.copyWith(color: LumenColors.accent)),
          const SizedBox(height: 2),
          Text(reading.citation, style: theme.textTheme.titleMedium),
          if (reading.numberingDiffers) Text('Douay-Rheims: ${reading.douayCitation}', style: small),
          for (final alternative in reading.alternatives) Text('Or: $alternative', style: small),
          const SizedBox(height: 8),
          for (final p in reading.passages) PassageText(verses: bible.versesFor(p)),
          if (reading.partialVerses)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text('Verses cited in part are shown in full.', style: small),
            ),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: saved ? null : () => bookmarks.add(Bookmark.forPassage(bible, passage)),
              child: Text(saved ? 'Saved' : 'Save',
                  semanticsLabel: saved ? '${reading.label} saved' : 'Save ${reading.label}'),
            ),
          ),
        ],
      ),
    );
  }
}
