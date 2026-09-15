import 'package:flutter_test/flutter_test.dart';
import 'package:dsa_tracker/core/constants/app_config.dart';

void main() {
  group('AppConfig URL handling', () {
    test('trims trailing slash before building API path', () {
      const baseUrl = 'https://dsa-tracker-b5w9.onrender.com/';
      final normalized = baseUrl.replaceFirst(RegExp(r'/+$'), '');
      expect(normalized, 'https://dsa-tracker-b5w9.onrender.com');
      expect('$normalized/api', 'https://dsa-tracker-b5w9.onrender.com/api');
    });
  });
}
