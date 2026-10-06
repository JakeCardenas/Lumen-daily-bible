import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../bible/bible.dart';
import '../../bookmarks/bookmark.dart';
import '../../widgets/passage_text.dart';
import '../bible/chapter_screen.dart';

/// A saved passage on its own, with a way into its chapter.
class PassageScreen extends StatelessWidget {
  const PassageScreen({super.key, required this.bookmark});

  final Bookmark bookmark;

  @override
  Widget build(BuildContext context) {
    final bible = context.read<Bible>();
    final first = bookmark.passage.ranges.first;
    return Scaffold(
      appBar: AppBar(title: Text(bookmark.label)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          PassageText(verses: bible.versesFor(bookmark.passage)),
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton(
              onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(
                  builder: (_) => ChapterScreen(
                      bookId: bookmark.passage.bookId, chapter: first.startChapter, focusVerse: first.startVerse))),
              child: const Text('Open chapter'),
            ),
          ),
        ],
      ),
    );
  }
}
