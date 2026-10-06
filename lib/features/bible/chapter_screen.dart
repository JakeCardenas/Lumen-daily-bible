import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../bible/bible.dart';
import '../../bible/reference_label.dart';
import '../../bible/scripture_ref.dart';
import '../../bookmarks/bookmark.dart';
import '../../bookmarks/bookmark_store.dart';
import '../../theme.dart';
import '../../widgets/passage_text.dart';

/// One chapter. Tapping verses selects them; the selection can be saved.
class ChapterScreen extends StatefulWidget {
  const ChapterScreen({super.key, required this.bookId, required this.chapter, this.focusVerse});

  final String bookId;
  final int chapter;

  /// Scrolled into view when the screen opens.
  final int? focusVerse;

  @override
  State<ChapterScreen> createState() => _ChapterScreenState();
}

class _ChapterScreenState extends State<ChapterScreen> {
  final Set<int> _selected = {};
  final Map<int, GlobalKey> _keys = {};

  @override
  void initState() {
    super.initState();
    final focus = widget.focusVerse;
    if (focus != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final target = _keys[focus]?.currentContext;
        if (target != null && target.mounted) Scrollable.ensureVisible(target, alignment: 0.1);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final bible = context.read<Bible>();
    final bookmarks = context.watch<BookmarkStore>();
    final book = bible.book(widget.bookId)!;
    final verses = bible.chapter(book.id, widget.chapter);
    for (final verse in verses) {
      _keys.putIfAbsent(verse.number, GlobalKey.new);
    }
    final muted = Theme.of(context).textTheme.bodySmall?.copyWith(color: LumenColors.inkMuted);
    final selection = ScriptureRef(book.id, rangesForVerses(widget.chapter, _selected));
    return Scaffold(
      appBar: AppBar(title: Text('${referenceBookName(book, book.id, singleChapter: true)} ${widget.chapter}')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (book.modernName != book.name) Text(book.modernName, style: muted),
            Text('Tap verses to select them.', style: muted),
            const SizedBox(height: 8),
            PassageText(verses: verses, selected: _selected, onVerseTap: _toggle, verseKeys: _keys),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton(
                  onPressed: widget.chapter > 1 ? () => _open(widget.chapter - 1) : null,
                  child: const Text('Previous chapter'),
                ),
                OutlinedButton(
                  onPressed: widget.chapter < book.chapterCount ? () => _open(widget.chapter + 1) : null,
                  child: const Text('Next chapter'),
                ),
              ],
            ),
          ],
        ),
      ),
      bottomNavigationBar: _selected.isEmpty
          ? null
          : _SelectionBar(
              count: _selected.length,
              saved: bookmarks.contains(selection),
              onClear: () => setState(_selected.clear),
              onSave: () async {
                await bookmarks.add(Bookmark.forPassage(bible, selection));
                if (mounted) setState(_selected.clear);
              },
            ),
    );
  }

  void _toggle(Verse verse) => setState(() {
        if (!_selected.remove(verse.number)) _selected.add(verse.number);
      });

  void _open(int chapter) => Navigator.of(context).pushReplacement(
      MaterialPageRoute<void>(builder: (_) => ChapterScreen(bookId: widget.bookId, chapter: chapter)));
}

class _SelectionBar extends StatelessWidget {
  const _SelectionBar({required this.count, required this.saved, required this.onClear, required this.onSave});

  final int count;
  final bool saved;
  final VoidCallback onClear;
  final VoidCallback onSave;

  @override
  Widget build(BuildContext context) => Material(
        color: LumenColors.surface,
        elevation: 2,
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Wrap(
              alignment: WrapAlignment.spaceBetween,
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: 8,
              runSpacing: 4,
              children: [
                Text('$count ${count == 1 ? 'verse' : 'verses'} selected'),
                Wrap(spacing: 8, children: [
                  TextButton(onPressed: onClear, child: const Text('Clear')),
                  FilledButton(onPressed: saved ? null : onSave, child: Text(saved ? 'Saved' : 'Save')),
                ]),
              ],
            ),
          ),
        ),
      );
}
