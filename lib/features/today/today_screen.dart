import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../liturgy/liturgy.dart';
import '../../theme.dart';
import '../../today/today_controller.dart';
import '../mood/mood_picker.dart';
import '../settings/settings_screen.dart';
import 'reading_section.dart';

/// The Today tab: the day's celebration, its Mass readings, and optional mood support.
class TodayScreen extends StatelessWidget {
  const TodayScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<TodayController>();
    final day = controller.day;
    final mass = controller.mass;
    final theme = Theme.of(context);
    final muted = theme.textTheme.bodyMedium?.copyWith(color: LumenColors.inkMuted);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Today'),
        actions: [
          TextButton(
            onPressed: () =>
                Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => const SettingsScreen())),
            child: const Text('Settings'),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 32),
        children: [
          Text(DateFormat.yMMMMEEEEd().format(controller.selectedDate), style: muted),
          const SizedBox(height: 4),
          if (day == null)
            Text('Readings for this date are not included in this version of Lumen.',
                style: theme.textTheme.titleMedium)
          else ...[
            Text(day.name, style: theme.textTheme.headlineSmall),
            const SizedBox(height: 4),
            Text(dayDescription(day), style: muted),
            if (day.optionalMemorials.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text('Optional memorial: ${day.optionalMemorials.join('; ')}', style: muted),
              ),
          ],
          const SizedBox(height: 16),
          _DateControls(controller: controller),
          if (day != null && day.masses.length > 1) _MassPicker(masses: day.masses, controller: controller),
          if (mass != null)
            for (final reading in mass.readings) ReadingSection(reading: reading),
          const Divider(height: 48),
          const MoodPicker(),
        ],
      ),
    );
  }
}

class _DateControls extends StatelessWidget {
  const _DateControls({required this.controller});

  final TodayController controller;

  @override
  Widget build(BuildContext context) => Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          OutlinedButton(
            onPressed: controller.canGoBack ? controller.previous : null,
            child: const Text('Previous day'),
          ),
          OutlinedButton(
            onPressed: controller.isShowingToday ? null : controller.goToToday,
            child: const Text('Back to today'),
          ),
          OutlinedButton(
            onPressed: controller.canGoForward ? controller.next : null,
            child: const Text('Next day'),
          ),
        ],
      );
}

class _MassPicker extends StatelessWidget {
  const _MassPicker({required this.masses, required this.controller});

  final List<Mass> masses;
  final TodayController controller;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 20),
        child: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (var i = 0; i < masses.length; i++)
              ChoiceChip(
                label: Text(masses[i].title ?? 'Mass of the day'),
                selected: controller.massIndex == i,
                showCheckmark: false,
                onSelected: (_) => controller.selectMass(i),
              ),
          ],
        ),
      );
}
