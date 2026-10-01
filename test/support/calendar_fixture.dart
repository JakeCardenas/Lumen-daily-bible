import 'package:lumen/liturgy/liturgy.dart';

Map<String, dynamic> fixtureReading(String kind, String label, String citation, String book, List<List<int>> ranges,
        String douay, {bool differs = false, bool partial = false, List<String> alternatives = const []}) =>
    {
      'kind': kind,
      'label': label,
      'citation': citation,
      'alternatives': alternatives,
      'passages': [
        {'book': book, 'ranges': ranges},
      ],
      'douay': douay,
      'differs': differs,
      'partial': partial,
    };

Map<String, dynamic> _day(String name, List<Map<String, dynamic>> masses,
        {String? rank, List<String> optional = const [], List<String> colors = const ['green']}) =>
    {'name': name, 'season': 'Ordinary Time', 'colors': colors, 'rank': rank, 'optional': optional, 'masses': masses};

/// 2026-10-03 to 2026-10-06, with readings that exist in fixtureBible().
Map<String, dynamic> fixtureCalendarJson() => {
      'version': 1,
      'calendar': 'United States',
      'start': '2026-10-03',
      'end': '2026-10-06',
      'sets': {
        'OrdWeekday26Saturday/II': [
          fixtureReading('first_reading', 'First Reading', 'Genesis 1:1-3', 'GEN', [[1, 1, 1, 3]], 'Genesis 1:1-3'),
          fixtureReading('responsorial_psalm', 'Responsorial Psalm', 'Psalm 23:1-3', 'PSA', [[22, 1, 22, 3]],
              'Psalm 22:1-3', differs: true),
          fixtureReading('gospel', 'Gospel', 'John 3:16', 'JHN', [[3, 16, 3, 16]], 'John 3:16'),
        ],
        'OrdSunday27/A': [
          fixtureReading('first_reading', 'First Reading', 'Isaiah 9:1-6', 'ISA', [[9, 2, 9, 7]], 'Isaias 9:2-7',
              differs: true),
          fixtureReading('responsorial_psalm', 'Responsorial Psalm', 'Psalm 23:1-3a, 4', 'PSA', [[22, 1, 22, 4]],
              'Psalm 22:1-4', differs: true, partial: true),
          fixtureReading('gospel_acclamation', 'Alleluia', 'John 3:16', 'JHN', [[3, 16, 3, 16]], 'John 3:16'),
          fixtureReading('gospel', 'Gospel', 'John 3:16-18', 'JHN', [[3, 16, 3, 18]], 'John 3:16-18',
              alternatives: ['John 3:16-17']),
        ],
        'OrdWeekday27Monday/II': [
          fixtureReading('first_reading', 'First Reading', 'Genesis 1:3', 'GEN', [[1, 3, 1, 3]], 'Genesis 1:3'),
          fixtureReading('responsorial_psalm', 'Responsorial Psalm', 'Psalm 23:6', 'PSA', [[22, 6, 22, 6]],
              'Psalm 22:6', differs: true),
          fixtureReading('gospel', 'Gospel', 'John 3:1-3', 'JHN', [[3, 1, 3, 3]], 'John 3:1-3'),
        ],
        'Test/#vigil': [
          fixtureReading('first_reading', 'First Reading', 'Isaiah 9:5', 'ISA', [[9, 6, 9, 6]], 'Isaias 9:6',
              differs: true),
          fixtureReading('responsorial_psalm', 'Responsorial Psalm', 'Psalm 23:4', 'PSA', [[22, 4, 22, 4]],
              'Psalm 22:4', differs: true),
          fixtureReading('gospel', 'Gospel', 'John 3:17', 'JHN', [[3, 17, 3, 17]], 'John 3:17'),
        ],
      },
      'days': {
        '2026-10-03': _day('Saturday of the 26th Week of Ordinary Time', [
          {'title': null, 'set': 'OrdWeekday26Saturday/II'},
        ], optional: ['Saturday Memorial of the Blessed Virgin Mary']),
        '2026-10-04': _day('27th Sunday of Ordinary Time', [
          {'title': null, 'set': 'OrdSunday27/A'},
        ]),
        '2026-10-05': _day('Monday of the 27th Week of Ordinary Time', [
          {'title': null, 'set': 'OrdWeekday27Monday/II'},
        ]),
        '2026-10-06': _day('Tuesday of the 27th Week of Ordinary Time', [
          {'title': null, 'set': 'OrdWeekday27Monday/II'},
          {'title': 'Vigil Mass (evening)', 'set': 'Test/#vigil'},
        ], rank: 'Memorial', colors: ['white']),
      },
    };

LiturgicalCalendar fixtureCalendar() => LiturgicalCalendar.fromJson(fixtureCalendarJson());
