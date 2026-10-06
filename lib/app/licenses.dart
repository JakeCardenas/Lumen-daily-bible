import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Adds the licences of bundled data and fonts to Flutter's licence page.
void registerLicenses() {
  LicenseRegistry.addLicense(() async* {
    yield LicenseEntryWithLineBreaks(['Liturgical Calendar API (calendar and reading citations)'],
        await rootBundle.loadString('assets/licenses/litcal-apache-2.0.txt'));
    yield LicenseEntryWithLineBreaks(['STEPBible TVTMS (verse numbering data)'],
        await rootBundle.loadString('assets/licenses/stepbible-tvtms.txt'));
    yield LicenseEntryWithLineBreaks(
        ['Literata typeface'], await rootBundle.loadString('assets/licenses/literata-ofl.txt'));
  });
}
