import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

/// Simple JSON cache backed by SharedPreferences.
///
/// Used to keep the current plan and today's data available when the backend
/// is unreachable. This is intentionally minimal (no full offline sync).
class CacheService {
  static const _todayKey = 'cache_today';
  static const _progressKey = 'cache_progress';
  static const _daysKey = 'cache_days';
  static const _planKey = 'cache_plan';

  Future<void> _putJson(String key, Object value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(key, jsonEncode(value));
  }

  Future<dynamic> _getJson(String key) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(key);
    if (raw == null) return null;
    try {
      return jsonDecode(raw);
    } catch (_) {
      return null;
    }
  }

  Future<void> saveToday(Map<String, dynamic> json) => _putJson(_todayKey, json);
  Future<Map<String, dynamic>?> readToday() async =>
      (await _getJson(_todayKey))?.cast<String, dynamic>();

  Future<void> saveProgress(Map<String, dynamic> json) =>
      _putJson(_progressKey, json);
  Future<Map<String, dynamic>?> readProgress() async =>
      (await _getJson(_progressKey))?.cast<String, dynamic>();

  Future<void> saveDays(List<Map<String, dynamic>> json) =>
      _putJson(_daysKey, json);
  Future<List<Map<String, dynamic>>?> readDays() async {
    final data = await _getJson(_daysKey);
    if (data is List) {
      return data.map((e) => (e as Map).cast<String, dynamic>()).toList();
    }
    return null;
  }

  Future<void> savePlan(Map<String, dynamic> json) => _putJson(_planKey, json);
  Future<Map<String, dynamic>?> readPlan() async =>
      (await _getJson(_planKey))?.cast<String, dynamic>();

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    for (final key in [_todayKey, _progressKey, _daysKey, _planKey]) {
      await prefs.remove(key);
    }
  }
}
