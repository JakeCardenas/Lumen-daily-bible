# Lumen

A calm, offline Catholic Scripture app for iOS and Android, built with Flutter.

- **Today**: the day's Mass readings for the United States liturgical calendar, in the Douay-Rheims Bible.
  It also offers optional Scripture, reflections and prayers for how you are feeling.
- **Bible**: the full Douay-Rheims Bible (73 books), searchable by words or by reference.
- **Saved**: the passages you bookmark.
- **Daily reminder**: optional local notification at a time you choose. It works offline and never needs an account.

## Run and test

```bash
flutter pub get
flutter run
flutter analyze
flutter test
(cd tool && python3 -m unittest discover -s tests)
```

Requires Flutter 3.47 (stable). iOS builds need Xcode, and Android builds need the Android SDK.
Python 3.12 is only needed to rebuild the data.

## How it is organized

- `lib/` contains the app.
  - Screens are in `lib/features/`.
  - Data models are in `lib/bible/`, `lib/liturgy/` and `lib/moods/`.
  - Reminder logic is in `lib/reminders/`. `reminder_planner.dart` is pure Dart. The plugin sits behind `NotificationGateway`.
- `assets/` holds the generated Bible (`bible/`) and calendar (`liturgy/`), the mood content, the font, and the license texts.
- `tool/` is the Python build that generates the assets. It uses only the standard library.
- `tool/data/` holds the reviewed inputs to the calendar build:
  - `lectionary_fill.json`: citations taken from AELF where the open calendar data has none. `fill_report.md` lists them for review.
  - `dc_overrides.json`: reviewed Douay-Rheims ranges for Tobit, Judith, Wisdom, Sirach, Baruch and Maccabees.
  - `douay_joins.json`: New Testament verses that Douay-Rheims joins where TVTMS records no difference.
  - `fill_corrections.json`: reviewed fixes for typos in AELF's references.

## Rebuilding the data

```bash
cd tool
python3 build_bible.py      # Douay-Rheims 1899 from eBible.org
python3 build_calendar.py   # US calendar, 2026-01-01 to 2030-02-23
```

`build_calendar.py` exits with:
- `0` when it wrote `assets/liturgy/calendar_us.json`.
- `2` when some readings need citations. Run `python3 harvest_aelf.py --max-pages N`. It reads AELF's daily Mass API
  (api.aelf.org, General Roman Calendar), keeps citations only, waits at least 1.5 s between requests, caches every
  page under `tool/cache/`, and makes at most `N` network requests. Cached pages are free. Then run `build_calendar.py` again.
- `3` when a citation from Tobit, Judith, Wisdom, Sirach, Baruch or Maccabees needs a reviewed Douay-Rheims mapping.
  Review `tool/data/dc_overrides_todo.json` with `python3 show_verses.py SIR 35:10-20`, then add the entry to
  `tool/data/dc_overrides.json`.
- `4` when validation or a spot check fails. Nothing is written.

AELF has no pages before 2016. A set the build needs is looked for on past dates when it was celebrated, so a few
sets may need a date that AELF has not published yet.

### Extending the calendar

The calendar ends on 2030-02-23, the day before the 7th Sunday of Ordinary Time in Year B. That Sunday and the
8th Sunday of Year B (2030-03-03) had not occurred on any date AELF had published when the data was built.
To extend: raise `END` in `tool/build_calendar.py`, run the build and harvest loop above, review the new rows in
`fill_report.md`, and ship an update before 2030-02-23. The app tells people when a date has no readings.

## Before publishing

- Replace the placeholder app id `app.lumen.lumen`. That means the Android `namespace`/`applicationId` and the iOS bundle identifier.
- Add app icons.
- Keep `version` in `pubspec.yaml` and `lumenVersion` in `lib/version.dart` in step.
- Build and run on Android. Only the iOS Simulator build (iPhone 18 Pro, iOS 27) was run during development.

## Device checklist for reminders

Run this on real devices, because simulators do not show every notification behavior.

**iPhone**
1. Fresh install, open Lumen: no notification prompt appears.
2. Settings → Daily reminder on: the system prompt appears. Choose Allow.
3. Set the time two minutes ahead and lock the phone. The reminder arrives. Its lock-screen display follows iOS Settings → Notifications → Lumen.
4. Tap the reminder with Lumen closed, then again with it in the background. Both times Today opens on that day.
5. Turn on "Show Scripture in notification preview". The reminder shows the celebration and Gospel reference.
6. On a fresh install, choose Don't Allow. The switch stays off, the help card appears, and Open Settings opens Lumen's notification settings.
7. Allow, then turn notifications off in iOS Settings and return to Lumen. The help card appears.
8. Change the phone's time zone, then open Lumen. The reminder follows the new local time.
9. With a Focus mode on, reminders follow Focus rules. Lumen never uses time-sensitive alerts.

**Android 13 and later:** steps 1–8, plus:

10. Reboot the phone. The reminder still arrives.
11. With "Hide sensitive content" on, the lock screen shows "Contents hidden".
12. Delivery can be a few minutes late, because Lumen uses inexact alarms.

**Android 12 and earlier:** there is no prompt, because notifications are allowed by default. Turning them off in system settings shows the help card.

**Accessibility:** use 200% font size, plus TalkBack and VoiceOver. Buttons announce what they act on, for example "Save Gospel".

## Sources and licenses

- **Scripture:** Douay-Rheims Bible, 1899 American Edition (public domain), courtesy of eBible.org.
- **Calendar and reading citations:**
  - Liturgical Calendar API data by John Romano D'Orazio and contributors, Apache License 2.0.
  - Missing citations were taken from the daily Mass readings published by AELF (Association Episcopale Liturgique
    pour les pays Francophones), which follow the same Roman Lectionary. Citations only, no text.
- **Verse numbering:** STEPBible TVTMS by Tyndale House, Cambridge, CC BY 4.0 (github.com/STEPBible). Used at build time only.
- **Typeface:** Literata by TypeTogether, SIL Open Font License 1.1.
- **Mood reflections and prayers:** written for Lumen, except the Memorare, a traditional prayer.

## Known limitations

- Readings are included through February 23, 2030.
- Readings are shown in the Douay-Rheims, not the NABRE Lectionary heard at US Masses. Responsorial refrains are not included.
- Some citations come from AELF, which publishes the General Roman Calendar for French-speaking countries. Where the
  Lectionary offers a choice (for example the second reading at the Ascension), AELF's choice is shown.
- Android reminders can arrive a few minutes late.
- After travel, reminders follow the new time zone once Lumen is opened.
- With Scripture previews on, reminders are scheduled 60 days ahead and refill whenever Lumen opens.
