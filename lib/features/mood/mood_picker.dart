import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../moods/moods.dart';
import '../../theme.dart';
import '../../today/today_controller.dart';
import 'mood_screen.dart';

/// "How are you feeling?" with one button per mood. Entirely optional.
class MoodPicker extends StatelessWidget {
  const MoodPicker({super.key});

  @override
  Widget build(BuildContext context) {
    final moods = context.read<MoodLibrary>().moods;
    final today = context.watch<TodayController>().today;
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('How are you feeling?', style: theme.textTheme.titleMedium),
        const SizedBox(height: 4),
        Text('Optional. Choose a feeling for a Scripture passage, a short reflection, and a prayer.',
            style: theme.textTheme.bodySmall?.copyWith(color: LumenColors.inkMuted)),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final mood in moods)
              OutlinedButton(
                onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(
                    builder: (_) => MoodScreen(mood: mood, startIndex: moodStartIndex(today, mood.entries.length)))),
                child: Text(mood.label),
              ),
          ],
        ),
      ],
    );
  }
}
