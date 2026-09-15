import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/app_state.dart';
import '../../providers/theme_provider.dart';
import '../../services/notification_service.dart';
import '../import_plan/import_plan_screen.dart';

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

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Current plan
          _sectionTitle(context, 'Current Plan'),
          Card(
            child: ListTile(
              title: Text(app.plan?.name ?? 'No plan imported'),
              subtitle: app.plan != null
                  ? Text('${app.plan!.totalDays} days')
                  : const Text('Import an Excel plan to begin'),
              leading: const Icon(Icons.menu_book),
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

  Future<void> _importNew(BuildContext context) async {
    final app = context.read<AppState>();
    final imported = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const ImportPlanScreen()),
    );
    if (imported == true) await app.bootstrap();
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
}
