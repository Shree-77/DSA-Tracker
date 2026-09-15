import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/constants/app_strings.dart';
import 'core/theme/app_theme.dart';
import 'providers/app_state.dart';
import 'providers/theme_provider.dart';
import 'services/notification_service.dart';
import 'screens/home_shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load the theme before the first frame.
  final themeProvider = ThemeProvider();
  await themeProvider.load();
  await NotificationService.instance.init();

  runApp(DsaTrackerApp(themeProvider: themeProvider));
}

class DsaTrackerApp extends StatelessWidget {
  const DsaTrackerApp({super.key, required this.themeProvider});

  final ThemeProvider themeProvider;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AppState()),
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
            home: const HomeShell(),
          );
        },
      ),
    );
  }
}
