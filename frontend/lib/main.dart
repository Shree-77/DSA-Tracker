import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/constants/app_strings.dart';
import 'core/network/api.dart';
import 'core/theme/app_theme.dart';
import 'providers/app_state.dart';
import 'providers/auth_provider.dart';
import 'providers/theme_provider.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home_shell.dart';
import 'services/notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final themeProvider = ThemeProvider();
  await themeProvider.load();
  await NotificationService.instance.init();

  final authProvider = AuthProvider();
  // Route API 401s back to the auth layer so the user is returned to login.
  apiClient.onUnauthorized = authProvider.onSessionExpired;
  await authProvider.bootstrap();

  runApp(DsaTrackerApp(
    themeProvider: themeProvider,
    authProvider: authProvider,
  ));
}

class DsaTrackerApp extends StatelessWidget {
  const DsaTrackerApp({
    super.key,
    required this.themeProvider,
    required this.authProvider,
  });

  final ThemeProvider themeProvider;
  final AuthProvider authProvider;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AppState()),
        ChangeNotifierProvider.value(value: authProvider),
        ChangeNotifierProvider.value(value: themeProvider),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, theme, _) {
          return MaterialApp(
            title: AppStrings.appName,
            debugShowCheckedModeBanner: false,
            theme: AppTheme.light,
            darkTheme: AppTheme.dark,
            themeMode: theme.mode,
            home: const AuthGate(),
          );
        },
      ),
    );
  }
}

/// Decides which top-level screen to show based on authentication status.
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    switch (auth.status) {
      case AuthStatus.unknown:
        return const Scaffold(
          body: Center(child: CircularProgressIndicator()),
        );
      case AuthStatus.unauthenticated:
        return const LoginScreen();
      case AuthStatus.authenticated:
        return const HomeShell();
    }
  }
}
