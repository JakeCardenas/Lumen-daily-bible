import 'dart:convert';

import 'package:flutter/services.dart';

import '../bible/scripture_ref.dart';

/// Shown under every mood page and in About.
const moodDisclaimer =
    'These readings offer spiritual encouragement. They are not a substitute for care from a doctor or counselor.';

/// Shown on moods where someone may be at risk (Sad, Hopeless).
const crisisMessage =
    'If you are in danger or thinking about ending your life, call or text 988 (US) or your local emergency number.';

class MoodEntry {
  const MoodEntry({required this.passage, this.modernReference, required this.reflection, required this.prayer});

  factory MoodEntry.fromJson(Map<String, dynamic> json) => MoodEntry(
        passage: ScriptureRef.fromJson(json['passage'] as Map<String, dynamic>),
        modernReference: json['modernReference'] as String?,
        reflection: json['reflection'] as String,
        prayer: json['prayer'] as String,
      );

  /// Douay-Rheims numbering.
  final ScriptureRef passage;

  /// Where readers of modern Bibles find it, e.g. "Psalm 34", when the numbering differs.
  final String? modernReference;
  final String reflection;
  final String prayer;
}

class Mood {
  const Mood({required this.id, required this.label, required this.crisisLine, required this.entries});

  factory Mood.fromJson(Map<String, dynamic> json) => Mood(
        id: json['id'] as String,
        label: json['label'] as String,
        crisisLine: json['crisisLine'] as bool,
        entries: [
          for (final e in (json['entries'] as List<dynamic>).cast<Map<String, dynamic>>()) MoodEntry.fromJson(e),
        ],
      );

  final String id;
  final String label;

  /// Whether to show the crisis line (Sad, Hopeless).
  final bool crisisLine;
  final List<MoodEntry> entries;
}

/// Scripture, reflections and prayers for how someone is feeling. Spiritual support only.
class MoodLibrary {
  const MoodLibrary(this.moods);

  factory MoodLibrary.fromJson(Map<String, dynamic> json) => MoodLibrary([
        for (final m in (json['moods'] as List<dynamic>).cast<Map<String, dynamic>>()) Mood.fromJson(m),
      ]);

  static Future<MoodLibrary> load({AssetBundle? bundle}) async {
    final raw = await (bundle ?? rootBundle).loadString('assets/moods/moods.json');
    return MoodLibrary.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  final List<Mood> moods;
}

/// Which entry to show first on [date]; changes daily so returning visitors see something new.
int moodStartIndex(DateTime date, int count) {
  if (count <= 0) return 0;
  final days = DateTime.utc(date.year, date.month, date.day).difference(DateTime.utc(2026)).inDays;
  return days % count;
}
