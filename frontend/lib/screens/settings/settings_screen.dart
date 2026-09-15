import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/app_state.dart';
import '../../providers/auth_provider.dart';
import '../../providers/theme_provider.dart';
import '../../services/notification_service.dart';
import '../ai/ai_plan_screen.dart';
import '../ai/ai_settings_screen.dart';
import '../import_plan/import_plan_screen.dart';
import '../plan/plan_switcher_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notifications = false;
  final _goalCtrl = TextEditingController(text: '2');

  @override
  void initState() {
    super.initState();
    NotificationService.instance.isEnabled().then((v) {
      if (mounted) setState(() => _notifications = v);
    });
  }

  @override
  void dispose() {
    _goalCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final theme = context.watch<ThemeProvider>();
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Account
          _sectionTitle(context, 'Account'),
          Card(
            child: ListTile(
              leading: const Icon(Icons.account_circle_outlined),
              title: Text(auth.username ?? 'Signed in'),
              subtitle: const Text('Tap to sign out'),
              trailing: const Icon(Icons.logout),
              onTap: () => _confirmLogout(context),
            ),
          ),
          const SizedBox(height: 8),

          // Current plan
          _sectionTitle(context, 'Current Plan'),
          Card(
            child: ListTile(
              title: Text(app.plan?.name ?? 'No plan imported'),
              subtitle: app.plan != null
                  ? Text(
                      '${app.plan!.totalDays} days'
                      '${app.plan!.isCompleted ? ' · Completed 🎉' : ''}',
                    )
                  : const Text('Import an Excel plan to begin'),
              leading: const Icon(Icons.menu_book),
              trailing: app.allPlans.length > 1
                  ? const Icon(Icons.swap_horiz)
                  : null,
              onTap: app.plan != null ? () => _openSwitcher(context) : null,
            ),
          ),
          const SizedBox(height: 8),

          // Switch / view all plans + completed history
          if (app.plan != null)
            Card(
              child: ListTile(
                leading: const Icon(Icons.library_books_outlined),
                title: const Text('My Plans'),
                subtitle: Text(
                  '${app.allPlans.length} plan'
                  '${app.allPlans.length == 1 ? '' : 's'}'
                  ' · switch or review completed',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => _openSwitcher(context),
              ),
            ),
          const SizedBox(height: 8),

          // AI
          _sectionTitle(context, 'AI Study Plans'),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.auto_awesome),
                  title: const Text('Create plan with AI'),
                  subtitle: const Text('Chat to design a plan, then import it'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _createWithAi(context),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.key),
                  title: const Text('AI API key'),
                  subtitle: const Text('Manage your NVIDIA API key'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const AiSettingsScreen(),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // Daily study goal
          _sectionTitle(context, 'Daily Study Goal'),
          TextField(
            controller: _goalCtrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              suffixText: 'hours',
              hintText: '2',
            ),
          ),
          const SizedBox(height: 16),

          // Notifications
          _sectionTitle(context, 'Notifications'),
          SwitchListTile(
            title: const Text('Daily reminder'),
            subtitle:
                const Text('Remind me about today\'s study session'),
            value: _notifications,
            onChanged: (v) async {
              await NotificationService.instance.setEnabled(v);
              setState(() => _notifications = v);
            },
          ),
          const SizedBox(height: 8),

          // Theme
          _sectionTitle(context, 'Appearance'),
          Card(
            child: Column(
              children: [
                RadioListTile<ThemeMode>(
                  title: const Text('System'),
                  value: ThemeMode.system,
                  groupValue: theme.mode,
                  onChanged: (m) => theme.setMode(m!),
                ),
                RadioListTile<ThemeMode>(
                  title: const Text('Light'),
                  value: ThemeMode.light,
                  groupValue: theme.mode,
                  onChanged: (m) => theme.setMode(m!),
                ),
                RadioListTile<ThemeMode>(
                  title: const Text('Dark'),
                  value: ThemeMode.dark,
                  groupValue: theme.mode,
                  onChanged: (m) => theme.setMode(m!),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Import / delete
          FilledButton.icon(
            onPressed: () => _importNew(context),
            icon: const Icon(Icons.upload_file),
            label: const Text('Import New Plan'),
          ),
          const SizedBox(height: 12),
          if (app.plan != null)
            OutlinedButton.icon(
              style: OutlinedButton.styleFrom(
                foregroundColor: Theme.of(context).colorScheme.error,
                minimumSize: const Size.fromHeight(52),
              ),
              onPressed: () => _confirmDelete(context),
              icon: const Icon(Icons.delete_outline),
              label: const Text('Delete Current Plan'),
            ),
        ],
      ),
    );
  }

  Widget _sectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 8),
      child: Text(title, style: Theme.of(context).textTheme.titleMedium),
    );
  }

  Future<void> _openSwitcher(BuildContext context) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const PlanSwitcherScreen()),
    );
  }

  Future<void> _importNew(BuildContext context) async {
    final app = context.read<AppState>();
    final imported = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const ImportPlanScreen()),
    );
    if (imported == true) await app.bootstrap();
  }

  Future<void> _createWithAi(BuildContext context) async {
    final app = context.read<AppState>();
    final imported = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const AiPlanScreen()),
    );
    if (imported == true) {
      await app.bootstrap();
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('AI plan created 🎉')),
      );
    }
  }

  Future<void> _confirmDelete(BuildContext context) async {
    final app = context.read<AppState>();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete plan?'),
        content: const Text(
          'This permanently deletes the plan and all your tracking data. '
          'This cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await app.deletePlan();
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Plan deleted')),
      );
    }
  }

  Future<void> _confirmLogout(BuildContext context) async {
    final auth = context.read<AuthProvider>();
    final app = context.read<AppState>();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign out?'),
        content: const Text('You can sign back in anytime with your username.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Sign out'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await auth.logout();
      app.reset();
      // AuthGate rebuilds and shows the login screen automatically.
    }
  }
}
