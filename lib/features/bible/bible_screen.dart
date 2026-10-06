import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../bible/bible.dart';
import '../../theme.dart';
import 'chapter_list_screen.dart';
import 'search_results.dart';

/// The Bible tab: a search field above the list of books.
class BibleScreen extends StatefulWidget {
  const BibleScreen({super.key});

  @override
  State<BibleScreen> createState() => _BibleScreenState();
}

class _BibleScreenState extends State<BibleScreen> {
  final _controller = TextEditingController();
  Timer? _debounce;
  String _query = '';

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250), () {
      if (mounted) setState(() => _query = value.trim());
    });
  }

  void _submit(String value) {
    _debounce?.cancel();
    setState(() => _query = value.trim());
  }

  void _clear() {
    _debounce?.cancel();
    _controller.clear();
    setState(() => _query = '');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bible')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: TextField(
              controller: _controller,
              onChanged: _onChanged,
              onSubmitted: _submit,
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                labelText: 'Search the Bible',
                hintText: 'Words or a reference, such as John 3:16',
                border: const OutlineInputBorder(),
                suffix: _query.isEmpty ? null : TextButton(onPressed: _clear, child: const Text('Clear')),
              ),
            ),
          ),
          Expanded(child: _query.length < 2 ? const BookList() : SearchResults(query: _query)),
        ],
      ),
    );
  }
}

class BookList extends StatelessWidget {
  const BookList({super.key});

  @override
  Widget build(BuildContext context) {
    final books = context.read<Bible>().books;
    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        const _SectionHeader('Old Testament'),
        for (final book in books.where((b) => b.testament == Testament.old)) _BookTile(book: book),
        const _SectionHeader('New Testament'),
        for (final book in books.where((b) => b.testament == Testament.newTestament)) _BookTile(book: book),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);

  final String title;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
        child: Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(color: LumenColors.accent)),
      );
}

class _BookTile extends StatelessWidget {
  const _BookTile({required this.book});

  final Book book;

  @override
  Widget build(BuildContext context) => ListTile(
        title: Text(book.name),
        subtitle: book.modernName == book.name ? null : Text(book.modernName),
        onTap: () => Navigator.of(context)
            .push(MaterialPageRoute<void>(builder: (_) => ChapterListScreen(bookId: book.id))),
      );
}
