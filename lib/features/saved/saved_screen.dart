import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../bookmarks/bookmark_store.dart';
import 'passage_screen.dart';

/// The Saved tab: bookmarked passages, newest first.
class SavedScreen extends StatelessWidget {
  const SavedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final bookmarks = context.watch<BookmarkStore>();
    final items = bookmarks.items;
    return Scaffold(
      appBar: AppBar(title: const Text('Saved')),
      body: items.isEmpty
          ? Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                'Passages you save will appear here. Choose Save under a reading, or select verses in the Bible.',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.only(bottom: 24),
              itemCount: items.length,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final bookmark = items[index];
                return ListTile(
                  title: Text(bookmark.label),
                  subtitle: Text('${bookmark.snippet}\nSaved ${DateFormat.yMMMd().format(bookmark.savedAt)}',
                      maxLines: 4, overflow: TextOverflow.ellipsis),
                  isThreeLine: true,
                  onTap: () => Navigator.of(context)
                      .push(MaterialPageRoute<void>(builder: (_) => PassageScreen(bookmark: bookmark))),
                  trailing: TextButton(
                    onPressed: () => bookmarks.remove(bookmark.id),
                    child: Text('Remove', semanticsLabel: 'Remove ${bookmark.label}'),
                  ),
                );
              },
            ),
    );
  }
}
