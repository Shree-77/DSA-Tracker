/// Normalised representation of a backend error envelope:
/// `{ "error": { "code": "...", "message": "...", "details": {} } }`.
class ApiException implements Exception {
  final String code;
  final String message;
  final Map<String, dynamic> details;
  final int? statusCode;

  ApiException({
    required this.code,
    required this.message,
    this.details = const {},
    this.statusCode,
  });

  /// Errors reported per Excel row (used by the import screen), if present.
  List<String> get rowErrors {
    final errors = details['errors'];
    if (errors is List) {
      return errors.map((e) => e.toString()).toList();
    }
    return const [];
  }

  factory ApiException.network([String? message]) => ApiException(
        code: 'NETWORK_ERROR',
        message: message ?? 'Could not reach the server. Check your connection.',
      );

  @override
  String toString() => 'ApiException($code): $message';
}
