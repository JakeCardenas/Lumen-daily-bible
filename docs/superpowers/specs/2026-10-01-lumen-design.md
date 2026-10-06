# Lumen — Design Spec

Date: 2026-10-01
Status: Approved design (revision 3: citation source, numbering and coverage as built; see the SDD ledger rulings)

## 1. Purpose

Lumen is a calm, simple Roman Catholic Scripture app for iOS and Android, built with Flutter and Dart. It helps people read each day's Mass readings, read and search the Bible, save passages, find gentle Scripture-based encouragement for how they feel, and receive an optional daily reminder.

### Success criteria

- Every date from 2026-01-01 through 2030-02-23 shows that day's celebration and complete Mass readings with verse text, fully offline.
- The Bible is browsable and searchable offline, by words and by reference.
- Bookmarks persist across launches.
- The daily reminder works offline, fires at the user's chosen local time, and opens the right day's readings when tapped.
- The app is fully usable with notifications disabled or denied.

### Non-goals (v1)

- Accounts, sync, analytics, remote push notifications.
- Dark mode, an in-app font-size setting (system text scaling is respected), audio.
- Calendars other than the United States national calendar.
- Responsorial refrains and other copyrighted Lectionary or ICEL text.
- Licensed translations such as NABRE or RSV-2CE. Reading text comes only from the bundled Bible, so a licensed translation can be added later.

## 2. Key decisions

| Decision | Choice | Why |
|---|---|---|
| Translation | Douay-Rheims, 1899 American edition (Challoner revision), from eBible.org | Public domain and Church-approved, with all 73 books. The first candidate file (a TSV on GitHub) was missing Psalm 9:22–39, had a shifted Exodus 6, blank verses, and a merged Job 25, so it was rejected. |
| Calendar | US national calendar: Ascension and Epiphany on Sunday, US proper saints | Primary audience. |
| Calendar strategy | Pre-built per-date table from 2026-01-01 to 2030-02-23, bundled; later dates come in app updates | Accurate, because it is generated from a maintained open engine. Simple and fully offline at runtime. |
| Calendar events | Liturgical Calendar API (Apache-2.0): event keys, names, ranks, colors, seasons, cycles | Its embedded readings have gaps and errors, so they are not used. |
| Reading citations | The API project's lectionary source files (Apache-2.0), accepted only when complete and convertible. Otherwise the citations come from AELF's daily Mass API (api.aelf.org, General Roman Calendar; citations only, never text). | The open files lack all Year B/C Sundays, most Ordinary Time weekdays and many feasts. USCCB refused automated requests (HTTP 403), so the user chose AELF, which follows the same Roman Lectionary. The user approved up to 675 requests; 664 were used. |
| Verse numbering | All conversion happens in the build (Python). The app receives ready-made Douay-Rheims verse ranges. | Keeps the error-prone logic in one place, where every reading is checked before shipping. |
| Numbering data | STEPBible TVTMS (Tyndale House, CC BY 4.0): Hebrew-to-Latin rows for Hebrew-numbered books, Greek-to-Latin rows for the New Testament, plus reviewed Douay-Rheims joins TVTMS lacks (Acts 19, 1 Thessalonians 4, 2 Thessalonians 2). Daniel keeps the same numbers. Esther's lettered additions use fixed rules. Books the Lectionary numbers from the Greek (Tobit, Judith, Wisdom, Sirach, Baruch, 1–2 Maccabees) need a reviewed per-citation entry. | No single scheme matches the US Lectionary's numbering for the Greek-numbered books. |
| Bible storage and search | Bundled JSON, loaded off the main thread, searched in memory | About 35,800 verses, so simple word-prefix matching is fast enough with no database. |
| Local storage | `shared_preferences` | Small data, no network, no account. |
| State management | `provider` with `ChangeNotifier`s and constructor-injected services | Simple and testable. |
| Navigation | Root shell with three tabs (Today, Bible, Saved), each with its own `Navigator` | No routing package needed. A notification tap switches to Today and sets the date. |
| Notifications | `flutter_local_notifications` 22.x, `timezone`, `flutter_timezone` | Well maintained and local-only. The plugin's `openAppNotificationSettings()` replaces a separate settings package. |

## 3. Architecture

```
lib/
  main.dart                        bootstrap; startup error screen
  theme.dart                       colors, typography (Literata for Scripture)
  version.dart                     app version shown in About
  app/                             LumenApp, HomeShell (tabs), ShellController, AppScope (providers), licenses
  bible/                           Bible model and loading, ScriptureRef, labels, psalm numbering, reference parser, search
  liturgy/                         LiturgicalCalendar (bundled table), LiturgicalDay, Mass, Reading
  today/                           TodayController (selected date and Mass)
  bookmarks/                       Bookmark, BookmarkStore
  moods/                           MoodLibrary
  reminders/                       settings, planner (pure Dart), gateway interface, controller, plugin gateway
  features/                        today/ bible/ saved/ mood/ settings/ screens
  widgets/                         PassageText
assets/
  bible/douay_rheims.json          generated
  liturgy/calendar_us.json         generated
  moods/moods.json                 authored
  fonts/                           Literata (OFL)
  licenses/                        Apache-2.0 (calendar data), OFL, TVTMS notice
tool/                              Python 3 data build (standard library only)
  lumen_data/                      books, bible, citations, versification, litcal, lectionary, aelf, harvest
  build_bible.py  build_calendar.py  harvest_aelf.py  show_verses.py  check_moods.py
  data/                            lectionary_fill.json, dc_overrides.json, fill_report.md (committed)
  cache/                           downloads (git-ignored; TVTMS is not redistributed)
  tests/                           unittest suites
```

Screens depend on repositories and controllers through `provider`, and the notification plugin sits behind a `NotificationGateway` interface, so widget tests use fakes.

## 4. Data pipeline

### 4.1 Bible

- Source: eBible.org `engDRA_vpl.zip` (Douay-Rheims 1899, public domain). Each line reads `BOOKCODE chapter:verse text`.
- The 73 books are kept in Douay order. Each book records its Douay name, its modern name, its testament, and every search alias (aliases are generated from one Python table so the app and build agree).
- Output: `{translation, source, books: [{id, name, modern, testament, aliases, chapters: [[verse, ...]]}]}`. Any missing verse becomes `null` and is reported.

### 4.2 Calendar and readings

1. Fetch the US calendar for the build's civil years from the API and cache it. Fetch the lectionary source files.
2. For each date, the primary celebration is the highest-ranked event that is not a vigil Mass. Optional memorials (including the Saturday memorial of Mary) and Lenten commemorations are never primary and are listed separately. A day with only optional memorials (two memorials that coincide) is the weekday, named the way LitCal names weekdays.
3. Resolve readings by event key and cycle:
   - Sunday cycle A/B/C for Sundays and feasts. Transfiguration is keyed by the date's Sunday cycle.
   - Weekday cycle I/II for Ordinary Time weekdays.
   - Seasonal weekday files and the saints' file otherwise.
   - A set is complete only if it has a first reading, a Gospel, and a responsorial psalm with verse numbers, and every citation parses. "Psalm 71" alone counts as incomplete.
4. Obligatory memorials take whatever AELF shows for them, recorded once per memorial:
   - Weekday readings, when every reading on the page covers verses of the weekday set it replaces. The weekday is the one listed on the same date, or found from the other days of the week (the Monday and Tuesday before Ash Wednesday continue the previous week).
   - Otherwise only the readings that differ are recorded, and they replace the weekday's.
   - A memorial that always displaces a weekday fixed by date (Sts. Basil and Gregory) keeps the whole page.
5. Masses:
   - Christmas Day lists Night, Dawn, and Day.
   - Christmas, Pentecost, the Assumption, the Nativity of John the Baptist, and Sts. Peter and Paul add a "Vigil Mass (evening)" to the day before.
   - The Easter Vigil is Holy Saturday's Mass.
   - Saturday-evening Sunday vigils are not listed.
6. Gaps become harvest needs. `harvest_aelf.py` handles them as follows:
   - It picks past dates (2010 to today; AELF has pages from 2016) where that key was the primary celebration, then dates where a US-only memorial or a memorial known to keep the weekday readings displaced it. Cached pages are tried first.
   - It fetches AELF's page for each date, at least 1.5 s apart, cached, with a hard cap on network requests (`--max-pages`). The US Ascension (Sunday) is read from AELF's Thursday page.
   - It reads citations only, converting French book abbreviations and Greek psalm numbers.
   - A page is accepted only if AELF's own details match: week, day and year parity for Ordinary Time weekdays; the year letter for Sundays and feasts; the rank for feasts and solemnities; no obligatory memorial on a plain weekday.
   - A second reading AELF lists as another first reading takes the second-reading slot where the open data has one.
   - Reviewed typo fixes in `tool/data/fill_corrections.json` are applied, and listed in the fill report.
   - Results go to `tool/data/lectionary_fill.json`, plus a human-readable `fill_report.md`.
7. Output `calendar_us.json`:

```json
{"version": 1, "calendar": "United States", "start": "2026-01-01", "end": "2030-02-23",
 "sets": {"OrdSunday27/A": [{"kind": "first_reading", "label": "First Reading", "citation": "Isaiah 5:1-7",
   "alternatives": [], "passages": [{"book": "ISA", "ranges": [[5, 1, 5, 7]]}],
   "douay": "Isaias 5:1-7", "differs": false, "partial": false}]},
 "days": {"2026-10-04": {"name": "27th Sunday of Ordinary Time", "season": "Ordinary Time", "colors": ["green"],
   "rank": null, "optional": [], "masses": [{"title": null, "set": "OrdSunday27/A"}]}}}
```

The build fails, and nothing is written, if any of these is true:
- A date has no Mass.
- A Mass has no Gospel, or has no reading other than the Gospel.
- Any range points outside the Douay-Rheims text.
- Any spot check fails (§8).

### 4.3 Citation conversion (build-time)

- **Parser:**
  - Accepts `Book C:V-V, V`, verse letters (`5-6ab`), `and`, and chapter-crossing ranges with any dash (`52:13—53:12`).
  - A `;` starts a new chapter, or a new book when a name follows (`John 1:7; Luke 1:17`).
  - Accepts `A|B` alternatives, `Cf.`/`See` prefixes, dual psalm numbers `103 (102)` (the larger is the Hebrew number), whole chapters, the European `84,5`, Esther's lettered chapters (`C:12`), and lectionary abbreviations. AELF's French references are converted to these forms first.
  - A typo seen in the source data ("Hewbrews") is accepted.
- **Hebrew-numbered books** are converted with TVTMS rows that describe Latin Bibles. Rows specific to Douay-Rheims win. Where TVTMS lists no change, the verse keeps its number, except that Psalms fall back to the standard Hebrew→Vulgate psalm rule. When one Hebrew verse becomes two Latin verses, verse parts pick the half (`63:19b` → `64:1`).
- **Esther's additions** use fixed rules: A:1–11 → 11:2–12, A:12–17 → 12:1–6, B → 13:1–7, C:1–11 → 13:8–18, C:12–30 → 14:1–19, E → 16:1–24, F:1–10 → 10:4–13.
- **Greek-numbered books** must have an entry in `tool/data/dc_overrides.json`. Each entry is reviewed against the Douay text at both ends. Missing ones are written to `dc_overrides_todo.json` with a proposal and the build stops.
- **Output:**
  - Overlapping and adjacent ranges are merged in citation order.
  - Each reading carries the Lectionary citation as written and a formatted Douay reference.
  - `differs` is set when the numbers differ, which shows "Douay-Rheims: …" in the app.
  - `partial` is set when verse letters were rounded to whole verses.
- A reading may span books (an acclamation such as `John 1:7; Luke 1:17`), so it holds a list of passages.

## 5. Screens and UX

The tone is calm. Warm light colors: ivory background `#FBF7F0`, warm white surfaces `#FFFDF8`, deep brown-gray text `#2B2620`, and one muted accent `#8A5A2B`.
- Scripture is set in Literata (OFL, bundled), and the UI uses the system font.
- System text scaling is respected, and layouts must not overflow at 200%.
- There are no dialogs or pop-ups. The only exceptions are the system permission prompt and the system time picker, both opened by the user.
- There are no streaks or badges, and no decorative imagery or ornamental icons.
- The bottom navigation uses text labels with simple outline icons.
- Repeated buttons carry specific screen-reader labels (for example "Save Gospel").

### Today

- Header: the date, the celebration name, and the liturgical color and season as text ("Green · Ordinary Time · Memorial"). When optional memorials fall that day, a line reads "Optional memorial: …".
- Date controls: "Previous day", "Back to today", and "Next day", limited to the bundled range. Outside the range a plain message says readings are not included for that date.
- When there are several Masses, a row of choice chips appears ("Mass of the day", "Vigil Mass (evening)", "Mass during the Night", …).
- Reading sections, in Lectionary order: label, citation, "Douay-Rheims: …" when the numbering differs, "Or: …" alternatives, the verse text, a note when verses were cited in part, and "Save".
- Optional section: "How are you feeling?", with buttons for Sad, Anxious, Hopeless, Happy, and Grateful.
- A "Settings" text button in the app bar.

### Mood page

- Title: "Feeling sad", "Feeling grateful", and so on.
- Content: the passage reference (Douay naming, plus "Psalm 34 in most modern Bibles" where useful), the verse text, a reflection of 2–4 sentences, and a "Show a prayer" button that expands the prayer.
- Buttons: "Another passage" and "Save passage". Each mood has five entries, and the first one shown changes with the date.
- Footer on every mood: "These readings offer spiritual encouragement. They are not a substitute for care from a doctor or counselor."
- Sad and Hopeless also show: "If you are in danger or thinking about ending your life, call or text 988 (US) or your local emergency number."
- Content lives in `assets/moods/moods.json`. Reflections and prayers are original writing, except the traditional Memorare. They make no clinical claims.

### Bible

- Search field: "Search the Bible", with the hint "Words or a reference, such as John 3:16".
  - Results appear after 250 ms.
  - References come first ("Go to John 3:16").
  - Psalms convert from modern numbering and offer both readings: "Go to Psalm 22" (Psalm 23 in most modern Bibles) and "Go to Psalm 23" (Douay-Rheims numbering).
  - Word search is case- and accent-insensitive, and every word must match the start of a word. It shows the first 200 matches with highlighted terms.
- Book list: Old and New Testament sections, showing the Douay name and the modern name when they differ.
- Chapter grid, then the chapter reader.
  - Tapping verses selects them, and a bottom bar shows "N verses selected", "Clear", and "Save".
  - "Previous chapter" and "Next chapter" buttons.
  - Search results open with the verse scrolled into view.

### Saved

- Newest first: reference, snippet, and "Saved Oct 1, 2026". Tap to open the passage, which has an "Open chapter" button. Each row has a "Remove" button.
- Empty state: "Passages you save will appear here. Choose Save under a reading, or select verses in the Bible."

### Settings

- Daily reminder section:
  - Switch: "Daily reminder".
  - "Time", with "Change" opening the system time picker. The default is 8:00 AM.
  - Switch: "Show Scripture in notification preview", with an explanation.
  - The permission help card, when needed.
  - A note that reminders are local, work offline, and may be delayed a few minutes by battery-saving settings.
- About section: Scripture source, daily-readings sources and licenses, verse-numbering data, the spiritual-support disclaimer, typeface, a "View licenses" button (Flutter's license page, with the Apache-2.0, OFL, and TVTMS notices registered), and the version.

## 6. Daily reminder

### Permission flow

1. The plugin is initialized with every `request*Permission` flag false, so nothing prompts at launch.
2. When the user turns the switch on, request permission: `POST_NOTIFICATIONS` on Android 13+, and alert and sound (no badge) on iOS.
3. If granted: save `enabled = true` and schedule.
4. If denied: the switch stays off and an inline card appears, with no dialog.
   - The card reads "Notifications are off for Lumen", followed by the steps.
   - iOS: "To allow them, open Settings, tap Notifications, choose Lumen, and turn on Allow Notifications."
   - Android: "To allow them, open Settings, tap Apps, choose Lumen, tap Notifications, and turn them on."
   - It ends with "You can keep using Lumen without them." and an "Open Settings" button, which calls the plugin's `openAppNotificationSettings()`.
5. On every launch and resume with reminders on, re-check notification access. If it was revoked, show the same card while the switch stays on.

### Scheduling (`reminder_planner.dart` decides what to schedule; `ReminderController` does it)

- Get the IANA time zone from `flutter_timezone`, call `tz.setLocalLocation`, and store it.
- **Previews off:** one `zonedSchedule` at the next HH:MM local time, repeating daily (`matchDateTimeComponents: time`).
  - Body: "Today's readings are ready."
  - Payload `today`, which opens the date on which it is tapped.
- **Previews on:** one notification per day for the next 60 days, with ids 1–60 (under iOS's limit of 64 pending notifications).
  - Body: "{Celebration} · Gospel: {citation}", or the generic text when a date is outside the data.
  - Payload `day:YYYY-MM-DD`, which opens that date even when tapped later.
- **When to reschedule** (cancel all, then schedule):
  - On launch.
  - On settings changes.
  - On resume, when the time zone changed or fewer than 30 days of individual reminders remain.
- A scheduling error shows "The reminder couldn't be scheduled. Try turning it off and on again." The rest of the app is unaffected.

### Platform details

- **Android:**
  - Channel `daily_reading` ("Daily reading"), default importance and priority, category `reminder`.
  - Scheduled with `AndroidScheduleMode.inexactAllowWhileIdle`. There is no exact-alarm permission, which Play policy restricts, so delivery can be a few minutes late.
  - `RECEIVE_BOOT_COMPLETED` and the plugin's two receivers are declared, so reminders survive reboot.
  - Core library desugaring is enabled.
  - Visibility is `private`: on a secure lock screen with sensitive content hidden, Android shows its standard "Contents hidden" placeholder (the plugin does not support a custom public version).
  - No full-screen intent.
  - The status icon is a monochrome book glyph, kept from resource shrinking with `res/raw/keep.xml`.
- **iOS:**
  - Interruption level `active`, never time-sensitive or critical.
  - `AppDelegate.swift` sets the `UNUserNotificationCenter` delegate, as the plugin requires.
  - Lock-screen and preview display follow the user's iOS settings. The app never claims it can force them.

### Tap handling

- Warm start: `onDidReceiveNotificationResponse` reaches a `NotificationRouter`. The app switches to Today, pops to its first screen, and shows the payload's date.
- Cold start: `getNotificationAppLaunchDetails()` at bootstrap feeds the same router.
- A date outside the bundled range shows today instead.

### Known limits (documented in the README)

- After travel, the reminder follows the new time zone once Lumen is opened.
- With previews on, reminders run out if Lumen is not opened for about 60 days. Opening it refills them. With previews off, the single repeating reminder never runs out.

## 7. Error handling

- **Assets missing or corrupt at startup:** a plain screen, "Lumen couldn't load its readings. Please reinstall the app."
- **Notification plugin fails to start:** the app still opens. Reminder actions fail softly, and the Settings note appears.
- **Corrupt bookmark data:** start empty, keep the unreadable value under a backup key, no crash.

## 8. Testing

- **Python** (`cd tool && python3 -m unittest discover -s tests`):
  - Book names and aliases.
  - VPL parsing, with gaps reported.
  - Every citation form in §4.3.
  - TVTMS parsing priority.
  - Isaiah 9 and 63–64, Psalm fallbacks and splits, Esther additions, the reviewed override path, and invalid verses.
  - Calendar assembly: primary selection, memorial weekday lookup, vigils, incomplete-set detection, harvest needs.
  - Harvest date choice, AELF page checks, and memorial classification.
  - AELF reference conversion and page parsing, including every quirk seen in the cached pages.
  - The generated assets, which must pass validation and the spot checks:
    - Ash Wednesday 2026-02-18, Easter 2026-04-05, and Ascension 2026-05-17 (US Sunday).
    - Christmas 2026 lists three Masses, and Christmas Eve two.
    - 2026-10-05 is Galatians 1:6-12 and Luke 10:25-37.
    - The Immaculate Conception moves to Monday in every year where Dec 8 is a Sunday.
- **Dart** (`flutter test`):
  - Bible model and labels, psalm numbering, reference parsing, search.
  - Calendar model and TodayController.
  - Bookmark store, including corrupt data.
  - Reminder planner: previews off and on, a time already past today, and DST in America/New_York.
  - Reminder controller with a fake gateway: no prompt until enabled, granted, denied, revoked on resume, time zone change, scheduling failure.
  - Widget tests:
    - Every screen and the tab shell.
    - Back navigation.
    - Notification payloads, both cold and warm.
    - Save and remove.
    - Mood crisis line and disclaimer.
    - Permission help on iOS and Android.
    - 200% text with no overflow.
  - Real-asset tests: every day in the calendar resolves to verse text, and the mood passages exist.
- `flutter analyze` must be clean.

## 9. Toolchain and verification limits

- Flutter 3.47.5 (stable) and Dart 3.13.4, installed with Homebrew. Python 3.12, standard library only.
- Xcode 27 and CocoaPods were installed during the build; the app was built and launched on the iOS Simulator (iPhone 18 Pro, iOS 27). There is no Android SDK, so the Android build is unverified. On-device notification behavior goes to the user through the README's device checklist.
- The app identifier `app.lumen.lumen` is a placeholder to change before publishing.

## 10. Risks

- **Calendar engine errors:** the engine could have edge-case mistakes. Mitigations are the spot checks, the fill report (audited for every Sunday, feast and memorial), and AELF page checks by week, day, year and rank.
- **Deuterocanonical citations:** each one depends on a reviewed override, a one-time review effort that blocks the build until done.
- **Data ends at 2030-02-23:** the 7th and 8th Sundays of Year B had no AELF page yet. Rerunning `tool/` with a later `END` and shipping an update extends it. This is documented in the README.
