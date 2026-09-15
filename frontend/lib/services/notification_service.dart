import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Optional local notifications. The app works fully without them.
///
/// Notifications are a best-effort convenience: on unsupported platforms
/// (e.g. web) the calls are safely no-ops.
class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();

  static const _enabledKey = 'notifications_enabled';
  final _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized || kIsWeb) return;
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings();
    const settings = InitializationSettings(android: android, iOS: ios);
    try {
      await _plugin.initialize(settings);
      _initialized = true;
    } catch (_) {
      // Notifications unavailable on this platform; ignore.
    }
  }

  Future<bool> isEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_enabledKey) ?? false;
  }

  Future<void> setEnabled(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_enabledKey, value);
    if (value) {
      await init();
    } else {
      await cancelAll();
    }
  }

  /// Immediate reminder for today's task.
  Future<void> showTodayReminder(String task) async {
    if (kIsWeb || !await isEnabled()) return;
    await init();
    if (!_initialized) return;

    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'dsa_daily',
        'Daily DSA Reminder',
        channelDescription: 'Reminders for your daily DSA session',
        importance: Importance.high,
        priority: Priority.high,
      ),
      iOS: DarwinNotificationDetails(),
    );

    try {
      await _plugin.show(
        1,
        'Your DSA session is waiting for you.',
        "Today's task: $task",
        details,
      );
    } catch (_) {
      // Ignore platform failures.
    }
  }

  Future<void> cancelAll() async {
    if (kIsWeb) return;
    try {
      await _plugin.cancelAll();
    } catch (_) {}
  }
}
