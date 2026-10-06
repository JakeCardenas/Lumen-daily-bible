import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../liturgy/liturgy.dart';
import '../../moods/moods.dart';
import '../../theme.dart';
import '../../version.dart';
import 'section_title.dart';

class AboutSection extends StatelessWidget {
  const AboutSection({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SectionTitle('About'),
        const _AboutBlock(
          'Scripture',
          'Douay-Rheims Bible, 1899 American Edition (Challoner revision). Public domain; text courtesy of '
              'eBible.org. Verse numbers follow the Douay-Rheims, which differs from many modern Bibles in places '
              'such as the Psalms.',
        ),
        _AboutBlock(
          'Daily readings',
          "Follows the liturgical calendar for the United States. The calendar and reading citations come from the "
              "Liturgical Calendar API by John Romano D'Orazio and contributors (Apache License 2.0); citations "
              'missing there were taken from the daily Mass readings published by AELF (Association Episcopale '
              'Liturgique pour les pays Francophones), which follow the same Roman Lectionary. Readings are included '
              'through ${DateFormat.yMMMMd().format(context.read<LiturgicalCalendar>().last)}. The text shown is the '
              'Douay-Rheims, so its wording differs from the Lectionary read at Mass.',
        ),
        const _AboutBlock(
          'Verse numbering',
          "Conversions between numbering traditions use STEPBible's TVTMS data from Tyndale House, Cambridge "
              '(CC BY 4.0), github.com/STEPBible.',
        ),
        const _AboutBlock('Spiritual support', moodDisclaimer),
        const _AboutBlock('Typeface', 'Literata by TypeTogether, SIL Open Font License 1.1.'),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton(
              onPressed: () =>
                  showLicensePage(context: context, applicationName: 'Lumen', applicationVersion: lumenVersion),
              child: const Text('View licenses'),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: Text('Version $lumenVersion',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: LumenColors.inkMuted)),
        ),
      ],
    );
  }
}

class _AboutBlock extends StatelessWidget {
  const _AboutBlock(this.title, this.body);

  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: theme.textTheme.labelLarge),
          const SizedBox(height: 2),
          Text(body, style: theme.textTheme.bodyMedium),
        ],
      ),
    );
  }
}
