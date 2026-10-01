import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../bible/scripture_ref.dart';
import 'bookmark.dart';

/// Saved passages, newest first, stored on the device.
class BookmarkStore extends ChangeNotifier {
  BookmarkStore(this._prefs) : _items = _read(_prefs);

  static const storageKey = 'bookmarks.v1';

  /// Unreadable data is kept here instead of being discarded.
  static const unreadableKey = 'bookmarks.v1.unreadable';

  final SharedPreferences _prefs;
  final List<Bookmark> _items;

  List<Bookmark> get items => List.unmodifiable(_items);

  bool contains(ScriptureRef passage) => _items.any((b) => b.id == passage.key);

  Future<void> add(Bookmark bookmark) async {
    if (_items.any((b) => b.id == bookmark.id)) return;
    _items.insert(0, bookmark);
    notifyListeners();
    await _save();
  }

  Future<void> remove(String id) async {
    _items.removeWhere((b) => b.id == id);
    notifyListeners();
    await _save();
  }

  Future<void> _save() => _prefs.setString(storageKey, jsonEncode([for (final b in _items) b.toJson()]));

  static List<Bookmark> _read(SharedPreferences prefs) {
    final raw = prefs.getString(storageKey);
    if (raw == null) return [];
    try {
      final items = [
        for (final item in (jsonDecode(raw) as List<dynamic>).cast<Map<String, dynamic>>()) Bookmark.fromJson(item),
      ];
      return items..sort((a, b) => b.savedAt.compareTo(a.savedAt));
    } catch (_) {
      unawaited(prefs.setString(unreadableKey, raw));
      unawaited(prefs.remove(storageKey));
      return [];
    }
  }
}
