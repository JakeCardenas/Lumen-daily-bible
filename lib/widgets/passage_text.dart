import 'package:flutter/material.dart';

import '../bible/bible.dart';
import '../theme.dart';

/// Scripture verses with small verse numbers. With [onVerseTap], verses become selectable.
class PassageText extends StatelessWidget {
  const PassageText({
    super.key,
    required this.verses,
    this.selected = const {},
    this.onVerseTap,
    this.verseKeys = const {},
  });

  final List<Verse> verses;
  final Set<int> selected;
  final ValueChanged<Verse>? onVerseTap;

  /// Keys by verse number, so a screen can scroll a verse into view.
  final Map<int, GlobalKey> verseKeys;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (verses.isEmpty) {
      return Text('This passage is not available in the Douay-Rheims text.', style: theme.textTheme.bodyMedium);
    }
    final style = scriptureStyle(context);
    final numberStyle = style.copyWith(fontSize: 12, color: LumenColors.inkMuted);
    final showChapters = verses.map((v) => v.chapter).toSet().length > 1;
    final children = <Widget>[];
    int? chapter;
    for (final verse in verses) {
      if (showChapters && verse.chapter != chapter) {
        children.add(Padding(
          padding: EdgeInsets.only(top: chapter == null ? 0 : 12, bottom: 4),
          child: Text('Chapter ${verse.chapter}',
              style: theme.textTheme.labelMedium?.copyWith(color: LumenColors.inkMuted)),
        ));
        chapter = verse.chapter;
      }
      children.add(_VerseTile(
        key: verseKeys[verse.number],
        verse: verse,
        style: style,
        numberStyle: numberStyle,
        selected: selected.contains(verse.number),
        onTap: onVerseTap == null ? null : () => onVerseTap!(verse),
      ));
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: children);
  }
}

class _VerseTile extends StatelessWidget {
  const _VerseTile({
    super.key,
    required this.verse,
    required this.style,
    required this.numberStyle,
    required this.selected,
    this.onTap,
  });

  final Verse verse;
  final TextStyle style;
  final TextStyle numberStyle;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final text = Text.rich(
      TextSpan(children: [TextSpan(text: '${verse.number}  ', style: numberStyle), TextSpan(text: verse.text)]),
      style: style,
    );
    if (onTap == null) return Padding(padding: const EdgeInsets.symmetric(vertical: 3), child: text);
    return Semantics(
      selected: selected,
      child: Material(
        color: selected ? LumenColors.surfaceMuted : Colors.transparent,
        borderRadius: BorderRadius.circular(6),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(6),
          child: Padding(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3), child: text),
        ),
      ),
    );
  }
}
