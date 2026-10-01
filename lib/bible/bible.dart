import 'dart:convert';
import 'dart:isolate';

import 'package:flutter/services.dart';

import 'scripture_ref.dart';

enum Testament { old, newTestament }

class Book {
  const Book({
    required this.id,
    required this.name,
    required this.modernName,
    required this.testament,
    required this.aliases,
    required this.chapters,
  });

  final String id;

  /// Douay-Rheims name, e.g. "Isaias".
  final String name;

  /// Common modern name, e.g. "Isaiah".
  final String modernName;
  final Testament testament;

  /// Normalized names that refer to this book, from the data build.
  final List<String> aliases;

  /// `chapters[c - 1][v - 1]`; null where the source text lacks a verse.
  final List<List<String?>> chapters;

  int get chapterCount => chapters.length;

  int verseCount(int chapter) => chapter >= 1 && chapter <= chapters.length ? chapters[chapter - 1].length : 0;

  /// "Isaias (Isaiah)" when the names differ.
  String get displayName => name == modernName ? name : '$name ($modernName)';
}

class Verse {
  const Verse(this.bookId, this.chapter, this.number, this.text);

  final String bookId;
  final int chapter;
  final int number;
  final String text;
}

/// The Douay-Rheims Bible, held in memory.
class Bible {
  Bible(this.books) : _byId = {for (final b in books) b.id: b};

  factory Bible.fromJson(Map<String, dynamic> json) => Bible([
        for (final b in (json['books'] as List<dynamic>).cast<Map<String, dynamic>>())
          Book(
            id: b['id'] as String,
            name: b['name'] as String,
            modernName: b['modern'] as String,
            testament: b['testament'] == 'new' ? Testament.newTestament : Testament.old,
            aliases: [for (final a in b['aliases'] as List<dynamic>) a as String],
            chapters: [
              for (final c in b['chapters'] as List<dynamic>) [for (final v in c as List<dynamic>) v as String?],
            ],
          ),
      ]);

  static Future<Bible> load({AssetBundle? bundle}) async {
    final raw = await (bundle ?? rootBundle).loadString('assets/bible/douay_rheims.json', cache: false);
    return Isolate.run(() => Bible.fromJson(jsonDecode(raw) as Map<String, dynamic>));
  }

  final List<Book> books;
  final Map<String, Book> _byId;

  Book? book(String id) => _byId[id];

  /// Verses covered by [ref], in order. Verses missing from the text are skipped.
  List<Verse> versesFor(ScriptureRef ref) {
    final book = _byId[ref.bookId];
    if (book == null) return const [];
    final verses = <Verse>[];
    for (final range in ref.ranges) {
      for (var c = range.startChapter; c <= range.endChapter; c++) {
        final count = book.verseCount(c);
        final first = c == range.startChapter ? range.startVerse : 1;
        final last = c == range.endChapter ? range.endVerse : count;
        for (var v = first; v <= last && v <= count; v++) {
          final text = book.chapters[c - 1][v - 1];
          if (text != null) verses.add(Verse(book.id, c, v, text));
        }
      }
    }
    return verses;
  }

  /// Every verse of one chapter.
  List<Verse> chapter(String bookId, int chapter) {
    final count = _byId[bookId]?.verseCount(chapter) ?? 0;
    if (count == 0) return const [];
    return versesFor(ScriptureRef(bookId, [VerseRange(chapter, 1, chapter, count)]));
  }
}
