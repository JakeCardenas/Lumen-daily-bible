import 'dart:convert';
import 'dart:isolate';

import 'package:flutter/services.dart';

import '../bible/scripture_ref.dart';

/// "2026-10-04".
String dateKey(DateTime date) =>
    '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';

DateTime dateOnly(DateTime date) => DateTime(date.year, date.month, date.day);

class Reading {
  const Reading({
    required this.kind,
    required this.label,
    required this.citation,
    required this.alternatives,
    required this.passages,
    required this.douayCitation,
    required this.numberingDiffers,
    required this.partialVerses,
  });

  factory Reading.fromJson(Map<String, dynamic> json) => Reading(
        kind: json['kind'] as String,
        label: json['label'] as String,
        citation: json['citation'] as String,
        alternatives: [for (final a in json['alternatives'] as List<dynamic>) a as String],
        passages: [
          for (final p in json['passages'] as List<dynamic>) ScriptureRef.fromJson(p as Map<String, dynamic>),
        ],
        douayCitation: json['douay'] as String,
        numberingDiffers: json['differs'] as bool,
        partialVerses: json['partial'] as bool,
      );

  /// e.g. "first_reading", "responsorial_psalm", "gospel".
  final String kind;
  final String label;

  /// The citation as the Lectionary gives it.
  final String citation;
  final List<String> alternatives;

  /// What to show, in Douay-Rheims numbering.
  final List<ScriptureRef> passages;
  final String douayCitation;
  final bool numberingDiffers;
  final bool partialVerses;
}

class Mass {
  const Mass({required this.title, required this.readings});

  final String? title;
  final List<Reading> readings;
}

class LiturgicalDay {
  const LiturgicalDay({
    required this.date,
    required this.name,
    required this.season,
    required this.colors,
    required this.rank,
    required this.optionalMemorials,
    required this.masses,
  });

  final DateTime date;
  final String name;
  final String season;
  final List<String> colors;
  final String? rank;
  final List<String> optionalMemorials;
  final List<Mass> masses;

  /// The Gospel of the first Mass, used in reminder previews.
  Reading? get gospel {
    if (masses.isEmpty) return null;
    for (final reading in masses.first.readings) {
      if (reading.kind == 'gospel') return reading;
    }
    return null;
  }
}

/// The bundled US liturgical calendar with Mass readings.
class LiturgicalCalendar {
  LiturgicalCalendar._(this.first, this.last, this._days, this._sets);

  factory LiturgicalCalendar.fromJson(Map<String, dynamic> json) => LiturgicalCalendar._(
        DateTime.parse(json['start'] as String),
        DateTime.parse(json['end'] as String),
        json['days'] as Map<String, dynamic>,
        {
          for (final entry in (json['sets'] as Map<String, dynamic>).entries)
            entry.key: [for (final r in entry.value as List<dynamic>) Reading.fromJson(r as Map<String, dynamic>)],
        },
      );

  static Future<LiturgicalCalendar> load({AssetBundle? bundle}) async {
    final raw = await (bundle ?? rootBundle).loadString('assets/liturgy/calendar_us.json', cache: false);
    return Isolate.run(() => LiturgicalCalendar.fromJson(jsonDecode(raw) as Map<String, dynamic>));
  }

  final DateTime first;
  final DateTime last;
  final Map<String, dynamic> _days;
  final Map<String, List<Reading>> _sets;

  bool covers(DateTime date) {
    final day = dateOnly(date);
    return !day.isBefore(first) && !day.isAfter(last);
  }

  LiturgicalDay? dayFor(DateTime date) {
    final raw = _days[dateKey(date)] as Map<String, dynamic>?;
    if (raw == null) return null;
    return LiturgicalDay(
      date: dateOnly(date),
      name: raw['name'] as String,
      season: raw['season'] as String,
      colors: [for (final c in raw['colors'] as List<dynamic>) c as String],
      rank: raw['rank'] as String?,
      optionalMemorials: [for (final o in raw['optional'] as List<dynamic>) o as String],
      masses: [
        for (final m in (raw['masses'] as List<dynamic>).cast<Map<String, dynamic>>())
          Mass(title: m['title'] as String?, readings: _sets[m['set'] as String] ?? const []),
      ],
    );
  }
}

/// "Green", "Violet or Rose".
String colorLabel(List<String> colors) {
  const names = {
    'purple': 'Violet', 'violet': 'Violet', 'pink': 'Rose', 'rose': 'Rose', 'green': 'Green', //
    'white': 'White', 'red': 'Red', 'gold': 'Gold', 'black': 'Black',
  };
  return [
    for (final c in colors) names[c.toLowerCase()] ?? (c.isEmpty ? c : '${c[0].toUpperCase()}${c.substring(1)}'),
  ].join(' or ');
}

/// "Green · Ordinary Time · Memorial".
String dayDescription(LiturgicalDay day) => [
      if (day.colors.isNotEmpty) colorLabel(day.colors),
      if (day.season.isNotEmpty) day.season,
      ?day.rank,
    ].join(' · ');
