import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../bible/bible.dart';
import '../../bible/reference_label.dart';
import '../../bookmarks/bookmark.dart';
import '../../bookmarks/bookmark_store.dart';
import '../../moods/moods.dart';
import '../../theme.dart';
import '../../widgets/passage_text.dart';

/// A passage, a short reflection, and an optional prayer for one mood. Spiritual support, not treatment.
class MoodScreen extends StatefulWidget {
  const MoodScreen({super.key, required this.mood, this.startIndex = 0});

  final Mood mood;
  final int startIndex;

  @override
  State<MoodScreen> createState() => _MoodScreenState();
}

class _MoodScreenState extends State<MoodScreen> {
  late int _index = widget.startIndex % widget.mood.entries.length;
  bool _showPrayer = false;

  void _next() => setState(() {
        _index = (_index + 1) % widget.mood.entries.length;
        _showPrayer = false;
      });

  @override
  Widget build(BuildContext context) {
    final bible = context.read<Bible>();
    final bookmarks = context.watch<BookmarkStore>();
    final entry = widget.mood.entries[_index];
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodySmall?.copyWith(color: LumenColors.inkMuted);
    final saved = bookmarks.contains(entry.passage);
    return Scaffold(
      appBar: AppBar(title: Text('Feeling ${widget.mood.label.toLowerCase()}')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          Text(referenceLabel(bible, entry.passage), style: theme.textTheme.titleMedium),
          if (entry.modernReference != null) Text('${entry.modernReference} in most modern Bibles', style: muted),
          const SizedBox(height: 8),
          PassageText(verses: bible.versesFor(entry.passage)),
          const SizedBox(height: 20),
          Text('Reflection', style: theme.textTheme.labelLarge?.copyWith(color: LumenColors.accent)),
          const SizedBox(height: 4),
          Text(entry.reflection, style: theme.textTheme.bodyLarge),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton(
              onPressed: () => setState(() => _showPrayer = !_showPrayer),
              child: Text(_showPrayer ? 'Hide prayer' : 'Show a prayer'),
            ),
          ),
          if (_showPrayer)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(entry.prayer, style: scriptureStyle(context).copyWith(fontStyle: FontStyle.italic)),
            ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (widget.mood.entries.length > 1)
                OutlinedButton(onPressed: _next, child: const Text('Another passage')),
              TextButton(
                onPressed: saved ? null : () => bookmarks.add(Bookmark.forPassage(bible, entry.passage)),
                child: Text(saved ? 'Saved' : 'Save passage'),
              ),
            ],
          ),
          const Divider(height: 40),
          if (widget.mood.crisisLine)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(crisisMessage, style: theme.textTheme.bodyMedium),
            ),
          Text(moodDisclaimer, style: muted),
        ],
      ),
    );
  }
}
