import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../models/plan.dart';
import '../../providers/app_state.dart';

/// Lets the user browse all their study plans, switch the active plan, and
/// review the ones they have already completed.
///
/// Switching is non-destructive — it only changes which plan is "current".
class PlanSwitcherScreen extends StatefulWidget {
  const PlanSwitcherScreen({super.key});

  @override
  State<PlanSwitcherScreen> createState() => _PlanSwitcherScreenState();
}

class _PlanSwitcherScreenState extends State<PlanSwitcherScreen> {
  @override
  void initState() {
    super.initState();
    // Refresh the plan list when the screen opens so it reflects any
    // completions or imports that happened elsewhere.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().refreshPlans();
    });
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();
    final active = app.allPlans.where((p) => !p.isCompleted).toList();
    final completed = app.allPlans.where((p) => p.isCompleted).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('My Plans')),
      body: RefreshIndicator(
        onRefresh: () => app.refreshPlans(),
        child: app.allPlans.isEmpty
            ? ListView(
                children: const [
                  SizedBox(height: 120),
                  Center(child: Text('No plans yet. Import one to begin.')),
                ],
              )
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (app.switching)
                    const Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: LinearProgressIndicator(),
                    ),
                  _section(context, 'Active plans'),
                  ...active.map((p) => _PlanTile(
                        plan: p,
                        isCurrent: p.id == app.plan?.id,
                        onTap: () => _switch(context, p),
                      )),
                  if (completed.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    _section(context, 'Completed'),
                    ...completed.map((p) => _PlanTile(
                          plan: p,
                          isCurrent: p.id == app.plan?.id,
                          onTap: () => _switch(context, p),
                        )),
                  ],
                ],
              ),
      ),
    );
  }

  Widget _section(BuildContext context, String title) => Padding(
        padding: const EdgeInsets.only(bottom: 8, top: 4),
        child: Text(
          title.toUpperCase(),
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: Theme.of(context).colorScheme.primary,
                letterSpacing: 0.8,
              ),
        ),
      );

  Future<void> _switch(BuildContext context, Plan plan) async {
    final app = context.read<AppState>();
    if (plan.id == app.plan?.id) {
      Navigator.of(context).maybePop();
      return;
    }
    await app.switchPlan(plan.id);
    if (!context.mounted) return;
    if (app.errorMessage != null && app.offline) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not switch: ${app.errorMessage}')),
      );
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Switched to "${plan.name}"')),
    );
    Navigator.of(context).maybePop();
  }
}

class _PlanTile extends StatelessWidget {
  const _PlanTile({
    required this.plan,
    required this.isCurrent,
    required this.onTap,
  });

  final Plan plan;
  final bool isCurrent;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final subtitleParts = <String>['${plan.totalDays} days'];
    if (plan.isCompleted && plan.completedAt != null) {
      subtitleParts.add(
        'Completed ${DateFormat.yMMMd().format(plan.completedAt!.toLocal())}',
      );
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isCurrent
            ? BorderSide(color: scheme.primary, width: 2)
            : BorderSide.none,
      ),
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: plan.isCompleted
              ? scheme.tertiaryContainer
              : scheme.primaryContainer,
          child: Icon(
            plan.isCompleted ? Icons.emoji_events : Icons.menu_book,
            color: plan.isCompleted
                ? scheme.onTertiaryContainer
                : scheme.onPrimaryContainer,
          ),
        ),
        title: Text(
          plan.name,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(subtitleParts.join(' · ')),
        trailing: isCurrent
            ? Chip(
                label: const Text('Current'),
                backgroundColor: scheme.primaryContainer,
                labelStyle: TextStyle(color: scheme.onPrimaryContainer),
                visualDensity: VisualDensity.compact,
              )
            : const Icon(Icons.chevron_right),
      ),
    );
  }
}
