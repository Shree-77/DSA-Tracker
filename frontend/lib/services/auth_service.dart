import 'package:shared_preferences/shared_preferences.dart';

import '../core/network/api.dart';
import '../core/network/api_client.dart';
import '../models/auth_user.dart';

/// Handles authentication calls and persists the access token so the user stays
/// signed in across app launches.
class AuthService {
  AuthService({ApiClient? client}) : _client = client ?? apiClient;

  final ApiClient _client;

  static const _tokenKey = 'auth_token';
  static const _usernameKey = 'auth_username';

  /// Register a new account. Throws [ApiException] (code `USERNAME_TAKEN`) if
  /// the username is already in use.
  Future<AuthResult> register(String username, String password) async {
    final data = await _client.post(
      '/auth/register',
      body: {'username': username, 'password': password},
    );
    final result = AuthResult.fromJson((data as Map).cast<String, dynamic>());
    await _persist(result);
    return result;
  }

  /// Log in with an existing account. Throws [ApiException] (code
  /// `INVALID_CREDENTIALS`) on a wrong username/password.
  Future<AuthResult> login(String username, String password) async {
    final data = await _client.post(
      '/auth/login',
      body: {'username': username, 'password': password},
    );
    final result = AuthResult.fromJson((data as Map).cast<String, dynamic>());
    await _persist(result);
    return result;
  }

  /// Restore a saved session (call once at startup). Returns the saved username
  /// when a token is present, else null. Applies the token to the API client.
  Future<String?> restoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    if (token == null || token.isEmpty) return null;
    _client.setAuthToken(token);
    return prefs.getString(_usernameKey);
  }

  Future<void> logout() async {
    _client.setAuthToken(null);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_usernameKey);
  }

  Future<void> _persist(AuthResult result) async {
    _client.setAuthToken(result.accessToken);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, result.accessToken);
    await prefs.setString(_usernameKey, result.user.username);
  }
}
