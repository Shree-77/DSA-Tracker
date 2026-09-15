/// The authenticated user as returned by the backend (`/auth/me`, login,
/// register). Never contains the password or its hash.
class AuthUser {
  final int id;
  final String username;

  const AuthUser({required this.id, required this.username});

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
        id: json['id'] as int,
        username: json['username'] as String,
      );

  Map<String, dynamic> toJson() => {'id': id, 'username': username};
}

/// The result of a successful register/login: a token plus the user.
class AuthResult {
  final String accessToken;
  final AuthUser user;

  const AuthResult({required this.accessToken, required this.user});

  factory AuthResult.fromJson(Map<String, dynamic> json) => AuthResult(
        accessToken: json['access_token'] as String,
        user: AuthUser.fromJson((json['user'] as Map).cast<String, dynamic>()),
      );
}
