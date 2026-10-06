import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../bible/bible.dart';
import 'chapter_screen.dart';

class ChapterListScreen extends StatelessWidget {
  const ChapterListScreen({super.key, required this.bookId});

  final String bookId;

  @override
  Widget build(BuildContext context) {
    final book = context.read<Bible>().book(bookId)!;
    return Scaffold(
      appBar: AppBar(title: Text(book.displayName)),
      body: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
            maxCrossAxisExtent: 80, mainAxisSpacing: 8, crossAxisSpacing: 8),
        itemCount: book.chapterCount,
        itemBuilder: (context, index) {
          final chapter = index + 1;
          return OutlinedButton(
            style: OutlinedButton.styleFrom(padding: EdgeInsets.zero),
            onPressed: () => Navigator.of(context)
                .push(MaterialPageRoute<void>(builder: (_) => ChapterScreen(bookId: bookId, chapter: chapter))),
            child: Text('$chapter', semanticsLabel: 'Chapter $chapter'),
          );
        },
      ),
    );
  }
}
