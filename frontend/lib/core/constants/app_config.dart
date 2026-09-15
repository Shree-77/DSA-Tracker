/// Static API configuration.
///
/// The backend URL is a compile-time constant. This is a single-user app that
/// always talks to the deployed production backend, so there is no runtime
/// override or Settings input.
class AppConfig {
  AppConfig._();

  /// Deployed production backend. Trailing slash intentionally omitted so that
  /// `apiPrefix` produces a clean `.../api` path.
  static const String baseUrl = 'https://dsa-tracker-b5w9.onrender.com';

  static String get apiPrefix => '$baseUrl/api';
}
