import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../models/study_day.dart';
import '../../models/today.dart';
import '../../providers/app_state.dart';
import '../../widgets/difficulty_chip.dart';
import '../../widgets/progress_bar.dart';
import '../../widgets/state_views.dart';
import '../day_detail/day_detail_screen.dart';
import '../import_plan/import_plan_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().bootstrap();
    });
  }

  String _greeting() {
    final h = DateTime.now().hour;
    if (h < 12) return 'Good morning 👋';
    if (h < 17) return 'Good afternoon 👋';
    return 'Good evening 👋';
  }

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();

    return Scaffold(
      body: SafeArea(
        child: switch (app.state) {
          LoadState.loading || LoadState.idle => const LoadingView(),
          LoadState.error => ErrorView(
              message: app.errorMessage,
              onRetry: () => context.read<AppState>().bootstrap(),
            ),
          LoadState.empty => EmptyView(
              icon: Icons.upload_file_outlined,
              title: AppStrings.noPlanTitle,
              body: AppStrings.noPlanBody,
              actionLabel: AppStrings.importPlan,
              onAction: () => _openImport(context),
            ),
          LoadState.ready => _buildReady(context, app),
        },
      ),
    );
  }

  Widget _buildReady(BuildContext context, AppState app) {
    final today = app.today!;
    return RefreshIndicator(
      onRefresh: () => context.read<AppState>().bootstrap(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        children: [
          if (app.offline) const OfflineBanner(),
          Text(_greeting(),
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 4),
          Text(
            DateFormat('EEEE, MMMM d').format(DateTime.now()),
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 20),
          _planHeader(context, app),
          const SizedBox(height: 16),
          _todaySection(context, app, today),
          const SizedBox(height: 24),
          _overallProgress(context, today),
          const SizedBox(height: 24),
          if (today.upcoming.isNotEmpty) _upcoming(context, today),
        ],
      ),
    );
  }

  Widget _planHeader(BuildContext context, AppState app) {
    final today = app.today!;
    final currentDay = today.day?.dayNumber;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(app.plan!.name,
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(
                    currentDay != null
                        ? 'Day $currentDay of ${today.totalDays}'
                        : '${today.totalDays} days',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
            const Icon(Icons.local_fire_department, color: Colors.orange),
          ],
        ),
      ),
    );
  }

  Widget _todaySection(BuildContext context, AppState app, Today today) {
    if (today.state == 'before') {
      return _infoCard(
        context,
        icon: Icons.schedule,
        title: 'Not started yet',
        body: today.message ?? 'Your plan starts soon.',
      );
    }
    if (today.state == 'completed') {
      return _infoCard(
        context,
        icon: Icons.emoji_events,
        title: 'Plan completed 🎉',
        body: today.message ?? 'You finished the plan.',
      );
    }
    final day = today.day;
    if (day == null) {
      return _infoCard(
        context,
        icon: Icons.beach_access,
        title: 'No task scheduled today',
        body: 'Enjoy a rest day or review previous topics.',
      );
    }
    return _TodayCard(day: day, onOpen: () => _openDay(context, day));
  }

  Widget _infoCard(BuildContext context,
      {required IconData icon, required String title, required String body}) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Icon(icon, size: 32, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(body, style: Theme.of(context).textTheme.bodyMedium),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _overallProgress(BuildContext context, Today today) {
    final pct = today.completionPercentage;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Overall Progress',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        LabeledProgressBar(value: pct / 100),
        const SizedBox(height: 8),
        Text(
          '${today.completedDays} / ${today.totalDays} completed   •   '
          '${pct.toStringAsFixed(1)}%',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ],
    );
  }

  Widget _upcoming(BuildContext context, Today today) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Upcoming', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        ...today.upcoming.map(
          (d) => Card(
            child: ListTile(
              leading: CircleAvatar(child: Text('${d.dayNumber}')),
              title: Text(d.focus ?? d.task ?? 'Day ${d.dayNumber}'),
              subtitle: Text(d.phase ?? ''),
              trailing: DifficultyChip(difficulty: d.difficulty),
              onTap: () => _openDay(context, d),
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _openDay(BuildContext context, StudyDay day) async {
    final app = context.read<AppState>();
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => DayDetailScreen(planId: day.planId, dayNumber: day.dayNumber),
      ),
    );
    await app.refreshTodayAndProgress();
  }

  Future<void> _openImport(BuildContext context) async {
    final app = context.read<AppState>();
    final imported = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const ImportPlanScreen()),
    );
    if (imported == true) {
      await app.bootstrap();
    }
  }
}

class _TodayCard extends StatelessWidget {
  const _TodayCard({required this.day, required this.onOpen});
  final StudyDay day;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      color: scheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Day ${day.dayNumber} • ${day.phase ?? ''}',
                style: TextStyle(color: scheme.onPrimaryContainer)),
            const SizedBox(height: 8),
            Text("Today's Focus",
                style: TextStyle(
                    color: scheme.onPrimaryContainer.withValues(alpha: 0.7),
                    fontSize: 12)),
            Text(
              day.focus ?? day.task ?? 'Study',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: scheme.onPrimaryContainer,
                    fontWeight: FontWeight.bold,
                  ),
            ),
            if (day.task != null) ...[
              const SizedBox(height: 4),
              Text(day.task!,
                  style: TextStyle(color: scheme.onPrimaryContainer)),
            ],
            const SizedBox(height: 12),
            DifficultyChip(difficulty: day.difficulty),
            const SizedBox(height: 20),
            FilledButton.icon(
              style: FilledButton.styleFrom(
                backgroundColor: scheme.onPrimaryContainer,
                foregroundColor: scheme.primaryContainer,
              ),
              onPressed: onOpen,
              icon: const Icon(Icons.play_arrow),
              label: const Text("Start Today's Study"),
            ),
          ],
        ),
      ),
    );
  }
}
