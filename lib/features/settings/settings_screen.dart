import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../reminders/reminder_controller.dart';
import '../../theme.dart';
import 'about_section.dart';
import 'section_title.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Settings')),
        body: ListView(
          padding: const EdgeInsets.only(bottom: 32),
          children: const [ReminderSection(), Divider(height: 32), AboutSection()],
        ),
      );
}

class ReminderSection extends StatelessWidget {
  const ReminderSection({super.key});

  @override
  Widget build(BuildContext context) {
    final reminders = context.watch<ReminderController>();
    final settings = reminders.settings;
    final theme = Theme.of(context);
    final time = TimeOfDay(hour: settings.hour, minute: settings.minute);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SectionTitle('Reminder'),
        SwitchListTile(
          title: const Text('Daily reminder'),
          subtitle: const Text("A notification each day to read the day's Scripture."),
          value: settings.enabled,
          onChanged: reminders.busy ? null : reminders.setEnabled,
        ),
        ListTile(
          title: const Text('Time'),
          subtitle: Text(time.format(context)),
          trailing: TextButton(
            onPressed: () => _pickTime(context, reminders, time),
            child: const Text('Change', semanticsLabel: 'Change reminder time'),
          ),
        ),
        SwitchListTile(
          title: const Text('Show Scripture in notification preview'),
          subtitle: const Text("Adds the day's celebration and Gospel reference. Your phone's settings still decide "
              'what appears on the lock screen.'),
          value: settings.showDetails,
          onChanged: reminders.setShowDetails,
        ),
        if (reminders.showPermissionHelp) const PermissionHelp(),
        if (reminders.schedulingFailed)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: Text("The reminder couldn't be scheduled. Try turning it off and on again.",
                style: theme.textTheme.bodyMedium?.copyWith(color: LumenColors.error)),
          ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: Text(
            'Reminders are scheduled on this phone and work offline. Battery-saving settings can delay them '
            'by a few minutes. Lumen works fully with reminders off.',
            style: theme.textTheme.bodySmall?.copyWith(color: LumenColors.inkMuted),
          ),
        ),
      ],
    );
  }

  Future<void> _pickTime(BuildContext context, ReminderController reminders, TimeOfDay initial) async {
    final picked = await showTimePicker(context: context, initialTime: initial, helpText: 'Reminder time');
    if (picked != null) await reminders.setTime(picked.hour, picked.minute);
  }
}

/// Explains how to allow notifications. Shown inline, never as a dialog.
class PermissionHelp extends StatelessWidget {
  const PermissionHelp({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final steps = theme.platform == TargetPlatform.iOS
        ? 'To allow them, open Settings, tap Notifications, choose Lumen, and turn on Allow Notifications.'
        : 'To allow them, open Settings, tap Apps, choose Lumen, tap Notifications, and turn them on.';
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: LumenColors.surfaceMuted, borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Notifications are off for Lumen', style: theme.textTheme.titleSmall),
          const SizedBox(height: 4),
          Text('$steps You can keep using Lumen without them.'),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: context.read<ReminderController>().openSystemSettings,
            child: const Text('Open Settings'),
          ),
        ],
      ),
    );
  }
}
