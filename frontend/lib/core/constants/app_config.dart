import 'package:shared_preferences/shared_preferences.dart';

/// Runtime API configuration.
///
/// The base URL is configurable so the app can point at a development or
/// production backend without hard-coding a URL throughout the codebase.
///
/// Resolution order:
///   1. A value the user saved in Settings (SharedPreferences).
///   2. `--dart-define=API_BASE_URL=...` provided at build/run time.
///   3. The built-in development default.
class AppConfig {
  AppConfig._();

  static const String _prefsKey = 'api_base_url';

  /// Compile-time override (e.g. `flutter run --dart-define=API_BASE_URL=...`).
  static const String _fromEnv = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  /// Sensible defaults for common targets.
  static const String developmentUrl = 'http://localhost:8000';
  static const String androidEmulatorUrl = 'http://10.0.2.2:8000';

  static String _baseUrl = _fromEnv.isNotEmpty ? _fromEnv : developmentUrl;

  static String get baseUrl => _baseUrl;

  /// Load the persisted base URL (call once during app start-up).
  static Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_prefsKey);
    if (saved != null && saved.isNotEmpty) {
      _baseUrl = saved;
    } else if (_fromEnv.isNotEmpty) {
      _baseUrl = _fromEnv;
    }
  }

  static Future<void> setBaseUrl(String url) async {
    _baseUrl = url.trim();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, _baseUrl);
  }

  static String get apiPrefix => '$_baseUrl/api';
}
