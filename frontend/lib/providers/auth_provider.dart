import 'package:flutter/foundation.dart';

import '../core/network/api_exception.dart';
import '../models/auth_user.dart';
import '../services/auth_service.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

/// Owns authentication state for the whole app. The UI watches [status] to
/// decide whether to show the login screen or the app shell.
class AuthProvider extends ChangeNotifier {
  AuthProvider({AuthService? service}) : _service = service ?? AuthService();

  final AuthService _service;

  AuthStatus status = AuthStatus.unknown;
  AuthUser? user;
  String? username;
  bool submitting = false;
  String? errorMessage;

  bool get isAuthenticated => status == AuthStatus.authenticated;

  /// Restore any saved session at startup.
  Future<void> bootstrap() async {
    username = await _service.restoreSession();
    status = username != null
        ? AuthStatus.authenticated
        : AuthStatus.unauthenticated;
    notifyListeners();
  }

  Future<bool> login(String username, String password) =>
      _run(() => _service.login(username.trim(), password));

  Future<bool> register(String username, String password) =>
      _run(() => _service.register(username.trim(), password));

  Future<void> logout() async {
    await _service.logout();
    user = null;
    username = null;
    status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  /// Called when the API client detects an expired/invalid token (401).
  void onSessionExpired() {
    if (status == AuthStatus.authenticated) {
      user = null;
      status = AuthStatus.unauthenticated;
      errorMessage = 'Your session expired. Please sign in again.';
      notifyListeners();
    }
  }

  Future<bool> _run(Future<AuthResult> Function() action) async {
    submitting = true;
    errorMessage = null;
    notifyListeners();
    try {
      final result = await action();
      user = result.user;
      username = result.user.username;
      status = AuthStatus.authenticated;
      return true;
    } on ApiException catch (e) {
      errorMessage = e.message;
      return false;
    } catch (_) {
      errorMessage = 'Something went wrong. Please try again.';
      return false;
    } finally {
      submitting = false;
      notifyListeners();
    }
  }
}
