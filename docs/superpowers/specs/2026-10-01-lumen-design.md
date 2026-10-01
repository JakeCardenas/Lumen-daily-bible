# Lumen — Design Spec

Date: 2026-10-01
Status: Approved design, pending spec review

## 1. Purpose

Lumen is a calm, simple Roman Catholic Scripture app for iOS and Android, built with Flutter and Dart. It helps people read each day's Mass readings, read and search the Bible, save passages, find gentle Scripture-based encouragement for how they feel, and receive an optional daily reminder.

### Success criteria

- Every calendar date from 2026-01-01 through 2035-12-31 shows that day's celebration and complete Mass readings with verse text, fully offline.
- The Bible is browsable and searchable offline (by words and by reference).
- Bookmarks persist across launches.
- The daily reminder works offline, fires at the user's chosen local time, and opens that day's readings when tapped.
- The app is fully usable with notifications disabled or denied.

### Non-goals (v1)

- Accounts, sync, analytics, remote push notifications.
- Dark mode, adjustable in-app font size (system text scaling is respected), audio.
- Calendars other than the United States national calendar.
- Responsorial refrains and other copyrighted Lectionary/ICEL text.
- Licensed translations (NABRE, RSV-2CE). The code keeps a seam for one later.

## 2. Key decisions

| Decision | Choice | Why |
|---|---|---|
| Translation | Douay-Rheims, Challoner revision | Public domain, Church-approved, all 73 books. No license needed. |
| Calendar | US national calendar (Ascension and Epiphany on Sunday, US proper saints) | Primary audience. |
| Calendar strategy | Pre-built per-date table for 2026–2035, bundled | Accurate (generated from a maintained open engine), trivially simple at runtime, fully offline. Avoids re-implementing hundreds of precedence and transfer rules. |
| Lectionary citations | Liturgical Calendar API data (Apache-2.0) plus a verified fill for missing days from USCCB's published daily citations (citations and lectionary numbers only, never text) | The open dataset lacks most Ordinary Time weekdays. Citations are factual references. The user approved a one-time harvest for verification. |
| Bible storage and search | Bundled JSON, loaded into memory, searched on a background isolate | About 35k verses; linear search is fast; no native database dependency. |
| Local storage | `shared_preferences` (bookmarks as JSON, reminder settings) | Small data, no network, no account. |
| State management | `provider` with `ChangeNotifier`s and constructor-injected services | Simple and testable. |
| Navigation | Root shell with three tabs (Today, Bible, Saved), each tab its own `Navigator` | No routing package needed. A notification tap switches to Today and sets the date. |
| Notifications | `flutter_local_notifications` 22.x, `timezone`, `flutter_timezone`, `app_settings` | Well maintained, local only, works offline. |

## 3. Architecture

```
lib/
  main.dart                       bootstrap: load assets, init services, run app
  app.dart                        MaterialApp, theme, root shell (3 tabs)
  theme/                          colors, typography (Literata for Scripture)
  bible/
    bible_models.dart             Book, Verse, VerseRef, Passage
    bible_repository.dart         load asset, chapters, verse ranges
    bible_search.dart             text search (isolate) and reference parsing
    book_names.dart               Douay names, modern names, aliases
  liturgy/
    liturgical_day.dart           LiturgicalDay, Mass, ReadingCitation models
    liturgical_calendar.dart      date to LiturgicalDay (from bundled table)
    citation_parser.dart          lectionary citation string to ranges
    versification.dart            modern/Hebrew to Douay (books, psalms, special cases)
    reading_resolver.dart         citation to Passage text from BibleRepository
  bookmarks/
    bookmark.dart, bookmark_store.dart
  moods/
    mood_models.dart, mood_repository.dart
  reminders/
    reminder_settings.dart        enabled, time, showDetails (persisted)
    reminder_planner.dart         pure Dart: what to schedule (testable)
    reminder_service.dart         wraps flutter_local_notifications
    notification_gateway.dart     interface, so tests can use a fake
  features/
    today/ bible/ saved/ mood/ settings/   screens and widgets
assets/
  bible/douay_rheims.json
  liturgy/calendar_us.json
  moods/moods.json
  fonts/Literata-*.ttf (+ OFL.txt)
tool/
  build_bible.py                  drb.tsv to assets/bible/douay_rheims.json
  fetch_litcal.py                 US calendar 2026–2035 and lectionary JSON (cached in tool/cache/)
  harvest_usccb.py                citations for gap days (cached, rate-limited)
  build_calendar.py               merge into assets/liturgy/calendar_us.json
  data/lectionary_fill.json       harvested and reconciled citations, with source dates
```

Each unit has one job. Screens depend on repositories and services through interfaces, so widget tests can inject fakes.

## 4. Data pipeline

### 4.1 Bible

- Source: Douay-Rheims TSV (public domain). Columns: book name, abbreviation, book number, chapter, verse, text.
- Keep only the 73 biblical books. Drop the Catechism, both canon law codes and the GIRM, which the source file also contains and which are not public domain.
- Output: `{books: [{id, name, modernName, testament, chapters: [[verse text, ...], ...]}]}`. Verse numbering follows the source.

### 4.2 Calendar and readings

1. `fetch_litcal.py` downloads `calendar/nation/US/{year}?year_type=CIVIL` for 2025–2035 (2025 is used only for reconciliation), plus the open lectionary JSON files. Raw responses are cached under `tool/cache/`.
2. For every date, pick the celebration in effect: the highest-ranked event, excluding Saturday vigil Masses of Sunday. Record optional memorials as alternatives.
3. Resolve readings by event key and cycle: the Sunday cycle (A/B/C) for Sundays and feasts, and the weekday cycle (I/II) for Ordinary Time weekdays. Use the citations embedded in the API response when present, otherwise the lectionary files.
4. For keys still missing (mostly Ordinary Time weekdays, plus a few feasts and solemnities), use `tool/data/lectionary_fill.json`. `harvest_usccb.py` builds it:
   - Fetch USCCB daily pages for past dates whose celebration maps to a missing key: Year I from 2019, 2021, 2023 and 2025; Year II from 2020, 2022, 2024 and 2026, up to today. Throttle to about 1 request per second and cache each response.
   - Extract only the reading headings, citations and lectionary number.
   - Accept a date for a weekday key only if its lectionary number equals the expected Ordinary Time weekday number, `305 + (week − 1) × 6 + dayIndex` (Monday = 0 … Saturday = 5; for example week 27 Monday = 461). This rules out proper memorial readings.
   - When several years agree, keep the citation. When they disagree, list the conflict in `tool/data/fill_report.md` and stop the build until it is resolved.
5. Days with several Masses (Christmas: Vigil, Night, Dawn, Day; Easter Vigil; Palm Sunday) keep each Mass as a separate entry.
6. Output `calendar_us.json`, keyed by ISO date: `{name, season, color, rank, cycle, masses: [{title, readings: [{kind, citation, shortCitation?}]}], optionalMemorials: [names]}`.

The build fails if any date from 2026 to 2035 lacks a first reading, psalm or Gospel, or if any citation does not resolve to Douay-Rheims text (§4.3).

### 4.3 Citation conversion (`citation_parser.dart`, `versification.dart`)

- Grammar covers:
  - `Book C:V-V, V, V-V`, with verse letters (`5-6ab`).
  - `and` as a separator.
  - Chapter-crossing ranges (`5:20-6:2`, `52:13—53:12`).
  - Alternatives (`A|B`): longer and shorter forms.
  - Prefixes such as `Cf.` and `See`.
  - Psalm dual numbering such as `Psalm 103 (102): ...`.
  - Whole-psalm citations (`Psalm 24`).
- Verse letters are rounded to whole verses, and the screen notes this.
- Book mapping from modern to Douay:
  - The historical books: 1 Samuel→1 Kings, 2 Samuel→2 Kings, 1 Kings→3 Kings, 2 Kings→4 Kings, 1–2 Chronicles→1–2 Paralipomenon, Ezra→1 Esdras, Nehemiah→2 Esdras.
  - The prophets: Isaiah→Isaias, Jeremiah→Jeremias, Hosea→Osee, Obadiah→Abdias, Jonah→Jonas, Micah→Micheas, Zephaniah→Sophonias, Haggai→Aggeus, Zechariah→Zacharias, Malachi→Malachias.
  - The other books: Joshua→Josue, Tobit→Tobias, Sirach→Ecclesiasticus, Song of Songs→Canticle of Canticles, 1–2 Maccabees→1–2 Machabees, Revelation→Apocalypse.
  - Common abbreviations are also accepted.
- Psalm numbering converts Hebrew to Vulgate, including the joins and splits:
  - Hebrew 9 and 10 join as Vulgate 9 (Hebrew 10:1 = 9:22).
  - Hebrew 114 and 115 join as Vulgate 113 (Hebrew 115:1 = 113:9).
  - Hebrew 116 splits into Vulgate 114 (verses 1–9) and 115 (verse 10 onward = 115:1).
  - Hebrew 147 splits into Vulgate 146 (verses 1–11) and 147 (verse 12 onward = 147:1).
  - Hebrew 11–113 and 117–146 are one lower in the Vulgate.
- Other numbering differences: Malachi 3:19–24 → Malachias 4:1–6; Joel 3 → Joel 2:28–32 and Joel 4 → Joel 3; Esther's lettered additions (A–F) → Douay Esther 10:4–16:24; Sirach where the Douay versification differs. Each case gets a unit test.
- A citation that cannot be mapped fails the data build rather than showing wrong text.

## 5. Screens and UX

The tone is calm. Warm light colors: ivory background (about `#FBF7F0`), warm white surfaces, deep brown-gray text (about `#2B2620`), one muted accent (about `#8A5A2B`). Scripture is set in Literata (OFL, bundled); the UI uses the system font. System text scaling is respected. There are no dialogs or pop-ups (the system permission prompt is the only one, and the user triggers it), no streaks or badges, no decorative imagery or ornamental icons. The bottom navigation uses text labels with simple outline icons. Every interactive element has a clear text label and is announced correctly by screen readers.

### Today

- Header: date, celebration name, season, and liturgical color as text ("Green · Ordinary Time"). If any optional memorials fall that day, a note reads "Optional memorial: Saint …".
- A Mass selector (text segmented buttons) appears only on days with several Masses.
- Reading sections: First Reading, Responsorial Psalm, Second Reading (when present), Alleluia Verse, Gospel. Each shows:
  - a label and the lectionary citation,
  - "Douay-Rheims: …" when the Douay reference differs,
  - the verse text with small verse numbers,
  - a "Save" text button.
- Date controls: "Previous day", "Today", "Next day", limited to the bundled range. Outside the range a plain message says readings are not available for that date.
- Optional section: "How are you feeling?", with buttons for Sad, Anxious, Hopeless, Happy and Grateful, which open the Mood page.
- A "Settings" text button in the app bar.

### Mood page

- One passage (citation and Douay-Rheims text), a short reflection of 2–4 sentences, and a "Show a prayer" button that expands the prayer.
- "Another passage" cycles through 4–6 entries per mood. The starting entry varies by date.
- "Save" bookmarks the passage.
- Footer on every mood: "These readings offer spiritual encouragement. They are not a substitute for care from a doctor or counselor."
- Sad and Hopeless also show an inline line: "If you are in danger or thinking about ending your life, call or text 988 (US) or your local emergency number."
- Content lives in `assets/moods/moods.json`. Reflections and prayers are original writing, plus traditional public-domain prayers where they fit (for example the Memorare). Theology stays orthodox and gentle and makes no clinical claims.

### Bible

- A search field sits at the top. Input that looks like a reference ("John 3:16", "Isaiah 9", "Ps 23", modern or Douay names) shows a "Go to …" result first, and Psalms are converted to the Douay numbering. Other input runs a case- and diacritic-insensitive word search, with results showing the reference and a highlighted snippet (first 200, with a "Show more" button).
- Book list grouped as Old Testament and New Testament, showing the Douay name and the modern name when they differ ("Isaias (Isaiah)").
- Chapter grid, then the chapter reader. "Previous chapter" and "Next chapter" sit at the bottom.
- Tapping verses toggles a selection. A bottom bar then shows "Save" and "Clear".

### Saved

- Newest first: reference, a two-line snippet, and the date saved.
- Tap to open the passage in the reader. A "Remove" text button on each row.
- Empty state: one plain sentence explaining how to save.

### Settings

- Daily reminder: an on/off switch, a time ("8:00 AM", changed with the system time picker), and a "Show Scripture in notification preview" switch with a one-line explanation.
- About: the translation (Douay-Rheims, Challoner revision, public domain), data sources and licenses (Liturgical Calendar API, Apache-2.0, credited; citations cross-checked against USCCB daily readings), Literata OFL, the support disclaimer, and the app version.

## 6. Daily reminder

### Permission flow

1. The plugin is initialized with all `request*Permission` flags false, so nothing prompts at launch.
2. When the user turns the switch on, request permission (Android 13+ `POST_NOTIFICATIONS`; iOS alert and sound, no badge).
3. If granted: save `enabled = true` and schedule.
4. If denied: the switch stays off, and an inline note appears under it. It explains how to allow notifications in Settings › Notifications › Lumen (iOS) or Settings › Apps › Lumen › Notifications (Android), and offers an "Open Settings" button (`app_settings`). There is no dialog, and nothing else in the app changes.
5. Every time the app launches or resumes with reminders on, check whether notifications are still allowed. If they are not, show the same inline note in Settings.

### Scheduling (`reminder_planner.dart` decides what to schedule; `reminder_service.dart` does it)

- Get the local IANA time zone with `flutter_timezone`, call `tz.setLocalLocation`, and store the zone name.
- Details off: a single `zonedSchedule` at the next occurrence of HH:MM local, repeating daily (`matchDateTimeComponents: time`). Body: "Today's readings are ready."
- Details on: individual notifications for the next 60 days (under iOS's limit of 64 pending notifications). Body: "{Celebration} · Gospel: {citation}", for example "27th Sunday in Ordinary Time · Gospel: Matthew 21:33-43". The window refills on every launch and resume.
- Reschedule from scratch (cancel all, then schedule) when settings change, the app launches or resumes and the stored zone differs, or the window has less than 30 days left.
- Every notification carries the payload `day:YYYY-MM-DD`, the date it is for.

### Platform details

- Android:
  - Channel `daily_reading` ("Daily reading"), default importance.
  - `AndroidScheduleMode.inexactAllowWhileIdle`. No exact-alarm permission, which Play policy restricts, so delivery can be a few minutes late.
  - The plugin's boot receivers and `RECEIVE_BOOT_COMPLETED` are declared, so reminders survive a reboot.
  - Core library desugaring is enabled, as the plugin requires.
  - Visibility is private, with a generic public version ("Lumen · Daily reading reminder"), so the phone's "hide sensitive content" setting still applies.
  - No `fullScreenIntent`. The small icon is a plain monochrome glyph.
- iOS:
  - Standard (`active`) interruption level, no time-sensitive or critical alerts.
  - `AppDelegate.swift` sets the `UNUserNotificationCenter` delegate, the one line the plugin requires.
  - Lock-screen and preview display follow the user's iOS settings. The app never claims it can force them.

### Tap handling

- Warm start: `onDidReceiveNotificationResponse` parses the payload, switches to Today, and sets the date.
- Cold start: `getNotificationAppLaunchDetails()` at bootstrap does the same.
- A date outside the bundled range falls back to today.

## 7. Error handling

- Missing or corrupt assets: a plain message, "Lumen couldn't load its readings. Please reinstall the app." These are bundled assets, so this indicates a broken build.
- A notification scheduling failure: the inline note in Settings says "Reminder couldn't be scheduled" and the app continues normally.
- Corrupt bookmark data: start empty and keep the corrupt raw value under a backup key. No crash.

## 8. Testing

- Unit tests:
  - Citation grammar: every form listed in §4.3.
  - Versification: psalm joins and splits, books, and the special cases, checked against known Douay text (for example Hebrew Psalm 23 resolves to text beginning "The Lord ruleth me").
  - Reference search and word search.
  - Bookmark store round-trip and corrupt-data recovery.
  - Reminder planner: details on and off, the 60-day window, time zone change, and DST transitions (for example America/New_York in March and November).
  - Payload parsing.
- Data coverage test: every date from 2026-01-01 to 2035-12-31 has a celebration and a primary Mass whose first reading, psalm and Gospel resolve to non-empty Douay-Rheims text. Spot checks against known dates: Christmas, Easter 2026 (April 5), Ascension Sunday 2026 (May 17, US), Immaculate Conception moved in 2035, and 2026-10-05 (Galatians 1:6-12, Luke 10:25-37).
- Widget tests: tab navigation; Today renders a fixture day; a notification payload opens Today for that date; saving from Today and Bible, and removing from Saved; the reminder switch with a fake gateway (granted, denied, revoked); the mood page with crisis line, prayer toggle and disclaimer.
- `flutter analyze` must be clean.

## 9. Toolchain and verification limits

- Required: Flutter SDK (stable). It is not installed yet and will be installed only with the user's consent.
- iOS builds need Xcode (installed by the user from the App Store). Android builds need the Android SDK. Without them, verification stops at `flutter analyze` and `flutter test`. Native builds and on-device notification behavior must then be checked by the user. A short checklist will be provided.

## 10. Risks

- The open calendar engine could have edge-case errors. Mitigations: the spot-check tests, and the USCCB reconciliation report lists any disagreement between the engine's citations and USCCB for overlapping past dates.
- Douay-Rheims versification can differ in rare places beyond those listed. Any unmappable citation fails the build, and the citation shown always comes from the Lectionary.
- The data runs only to 2035. Rerunning `tool/` and shipping an update extends it, and this is documented in the README.
