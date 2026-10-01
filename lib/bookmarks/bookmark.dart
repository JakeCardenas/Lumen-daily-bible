import '../bible/bible.dart';
import '../bible/reference_label.dart';
import '../bible/scripture_ref.dart';

/// Shortens [text] to at most [max] characters, ending with an ellipsis when cut.
String shortSnippet(String text, {int max = 160}) =>
    text.length <= max ? text : '${text.substring(0, max - 1).trimRight()}…';

class Bookmark {
  const Bookmark({required this.passage, required this.label, required this.snippet, required this.savedAt});

  factory Bookmark.forPassage(Bible bible, ScriptureRef passage, {DateTime? now}) {
    final verses = bible.versesFor(passage);
    return Bookmark(
      passage: passage,
      label: referenceLabel(bible, passage),
      snippet: verses.isEmpty ? '' : shortSnippet(verses.first.text),
      savedAt: now ?? DateTime.now(),
    );
  }

  factory Bookmark.fromJson(Map<String, dynamic> json) => Bookmark(
        passage: ScriptureRef.fromJson(json['passage'] as Map<String, dynamic>),
        label: json['label'] as String,
        snippet: json['snippet'] as String,
        savedAt: DateTime.parse(json['savedAt'] as String),
      );

  final ScriptureRef passage;
  final String label;
  final String snippet;
  final DateTime savedAt;

  String get id => passage.key;

  Map<String, dynamic> toJson() => {
        'passage': passage.toJson(),
        'label': label,
        'snippet': snippet,
        'savedAt': savedAt.toIso8601String(),
      };
}
