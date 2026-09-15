import 'package:flutter_test/flutter_test.dart';
import 'package:dsa_tracker/core/constants/app_config.dart';

void main() {
  group('AppConfig', () {
    test('points at the deployed production backend', () {
      expect(AppConfig.baseUrl, 'https://dsa-tracker-b5w9.onrender.com');
    });

    test('builds a clean /api prefix without a double slash', () {
      expect(AppConfig.apiPrefix, 'https://dsa-tracker-b5w9.onrender.com/api');
    });
  });
}
