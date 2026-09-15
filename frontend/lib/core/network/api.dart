import 'api_client.dart';

/// Process-wide singleton [ApiClient].
///
/// A single instance guarantees the bearer token set at login is attached to
/// every request made by any service (plans, days, trackers, etc.).
final ApiClient apiClient = ApiClient();
