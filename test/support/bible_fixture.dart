import 'package:lumen/bible/bible.dart';

Map<String, dynamic> _book(String id, String name, String modern, String testament, List<String> aliases,
        {required int chapters, Map<int, List<String>> text = const {}}) =>
    {
      'id': id,
      'name': name,
      'modern': modern,
      'testament': testament,
      'aliases': aliases,
      'chapters': [
        for (var c = 1; c <= chapters; c++) text[c] ?? [for (var v = 1; v <= 5; v++) '$name $c:$v placeholder.'],
      ],
    };

/// A small Bible in Douay-Rheims order: Genesis 1, 1 Kings (1 Samuel), 3 Kings (1 Kings),
/// Psalms 1-23, Isaias 1-9, and John 1-3.
Bible fixtureBible() => Bible.fromJson({
      'books': [
        _book('GEN', 'Genesis', 'Genesis', 'old', ['gen', 'genesis', 'gn'], chapters: 1, text: {
          1: [
            'In the beginning God created heaven, and earth.',
            'And the earth was void and empty, and darkness was upon the face of the deep.',
            'And God said: Be light made. And light was made.',
          ],
        }),
        _book('1SA', '1 Kings', '1 Samuel', 'old', ['1 sa', '1 sam', '1 samuel', '1 sm'], chapters: 3),
        _book('1KI', '3 Kings', '1 Kings', 'old', ['1 ki', '1 kgs', '1 kings', '3 kgs', '3 kings'], chapters: 3),
        _book('PSA', 'Psalms', 'Psalms', 'old', ['ps', 'psa', 'psalm', 'psalms'], chapters: 23, text: {
          22: [
            'A psalm for David. The Lord ruleth me: and I shall want nothing.',
            'He hath set me in a place of pasture. He hath brought me up, on the water of refreshment:',
            "He hath converted my soul. He hath led me on the paths of justice, for his own name's sake.",
            'For though I should walk in the midst of the shadow of death, I will fear no evils, for thou art with me.',
            'Thou hast prepared a table before me against them that afflict me.',
            'And thy mercy will follow me all the days of my life.',
          ],
        }),
        _book('ISA', 'Isaias', 'Isaiah', 'old', ['is', 'isa', 'isaiah', 'isaias'], chapters: 9, text: {
          9: [
            for (var v = 1; v <= 7; v++)
              v == 6 ? 'For a CHILD IS BORN to us, and a son is given to us.' : 'Isaias 9:$v placeholder.',
          ],
        }),
        _book('JHN', 'John', 'John', 'new', ['jhn', 'jn', 'john'], chapters: 3, text: {
          3: [
            for (var v = 1; v <= 21; v++)
              v == 16 ? 'For God so loved the world, as to give his only begotten Son.' : 'John 3:$v placeholder.',
          ],
        }),
      ],
    });
