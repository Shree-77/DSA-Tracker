import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../constants/app_config.dart';
import 'api_exception.dart';

/// Thin HTTP wrapper that:
///   * prefixes every path with the configured API base,
///   * decodes JSON,
///   * converts the backend error envelope into [ApiException],
///   * converts socket/timeout failures into a network [ApiException].
class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  static const Duration _timeout = Duration(seconds: 20);

  Uri _uri(String path, [Map<String, dynamic>? query]) {
    final base = AppConfig.apiPrefix;
    final normalised = path.startsWith('/') ? path : '/$path';
    final uri = Uri.parse('$base$normalised');
    if (query == null || query.isEmpty) return uri;
    return uri.replace(
      queryParameters: query.map((k, v) => MapEntry(k, v.toString())),
    );
  }

  Future<dynamic> get(String path, {Map<String, dynamic>? query}) async {
    return _send(() => _client.get(_uri(path, query)));
  }

  Future<dynamic> patch(String path, {Map<String, dynamic>? body}) async {
    return _send(
      () => _client.patch(
        _uri(path),
        headers: _jsonHeaders,
        body: jsonEncode(body ?? {}),
      ),
    );
  }

  Future<dynamic> put(String path, {Map<String, dynamic>? body}) async {
    return _send(
      () => _client.put(
        _uri(path),
        headers: _jsonHeaders,
        body: jsonEncode(body ?? {}),
      ),
    );
  }

  Future<dynamic> delete(String path) async {
    return _send(() => _client.delete(_uri(path)));
  }

  /// Multipart upload used by the Excel import.
  Future<dynamic> uploadExcel(
    String path, {
    required Uint8List bytes,
    required String filename,
    required Map<String, String> fields,
  }) async {
    try {
      final request = http.MultipartRequest('POST', _uri(path));
      request.fields.addAll(fields);
      request.files.add(
        http.MultipartFile.fromBytes('file', bytes, filename: filename),
      );
      final streamed = await request.send().timeout(_timeout);
      final response = await http.Response.fromStream(streamed);
      return _handle(response);
    } on SocketException {
      throw ApiException.network();
    } on HttpException {
      throw ApiException.network();
    }
  }

  Future<dynamic> _send(Future<http.Response> Function() run) async {
    try {
      final response = await run().timeout(_timeout);
      return _handle(response);
    } on SocketException {
      throw ApiException.network();
    } on HttpException {
      throw ApiException.network();
    }
  }

  dynamic _handle(http.Response response) {
    final status = response.statusCode;
    final hasBody = response.body.isNotEmpty;
    final decoded = hasBody ? jsonDecode(response.body) : null;

    if (status >= 200 && status < 300) {
      return decoded;
    }

    if (decoded is Map && decoded['error'] is Map) {
      final err = decoded['error'] as Map;
      throw ApiException(
        code: err['code']?.toString() ?? 'ERROR',
        message: err['message']?.toString() ?? 'Request failed',
        details: (err['details'] as Map?)?.cast<String, dynamic>() ?? const {},
        statusCode: status,
      );
    }

    throw ApiException(
      code: 'HTTP_$status',
      message: 'Request failed ($status)',
      statusCode: status,
    );
  }

  static const Map<String, String> _jsonHeaders = {
    'Content-Type': 'application/json',
  };
}
