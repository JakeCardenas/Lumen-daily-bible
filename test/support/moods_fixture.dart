import 'package:lumen/moods/moods.dart';

MoodLibrary fixtureMoods() => MoodLibrary.fromJson({
      'moods': [
        {
          'id': 'sad',
          'label': 'Sad',
          'crisisLine': true,
          'entries': [
            {
              'passage': {
                'book': 'PSA',
                'ranges': [
                  [22, 4, 22, 4],
                ],
              },
              'modernReference': 'Psalm 23',
              'reflection': 'Reflection one.',
              'prayer': 'Prayer one.',
            },
            {
              'passage': {
                'book': 'JHN',
                'ranges': [
                  [3, 16, 3, 16],
                ],
              },
              'reflection': 'Reflection two.',
              'prayer': 'Prayer two.',
            },
          ],
        },
        {
          'id': 'grateful',
          'label': 'Grateful',
          'crisisLine': false,
          'entries': [
            {
              'passage': {
                'book': 'GEN',
                'ranges': [
                  [1, 1, 1, 1],
                ],
              },
              'reflection': 'Reflection three.',
              'prayer': 'Prayer three.',
            },
          ],
        },
      ],
    });
