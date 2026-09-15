import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/study_day.dart';
import '../../providers/app_state.dart';
import '../../widgets/difficulty_chip.dart';
import '../../widgets/state_views.dart';
import '../../widgets/status_icon.dart';
import '../day_detail/day_detail_screen.dart';

class PlanScreen extends StatelessWidget {
  const PlanScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();

    return Scaffold(
      appBar: AppBar(title: Text(app.plan?.name ?? 'Plan')),
      body: switch (app.state) {
        LoadState.loading || LoadState.idle => const LoadingView(),
        LoadState.error => ErrorView(
            message: app.errorMessage,
            onRetry: () => context.read<AppState>().bootstrap(),
          ),
        LoadState.empty => const EmptyView(
            icon: Icons.calendar_month_outlined,
            title: 'No plan',
            body: 'Import a plan from the Home tab to see it here.',
          ),
        LoadState.ready => _buildPlan(context, app),
      },
    );
  }

  Widget _buildPlan(BuildContext context, AppState app) {
    // Group days by week.
    final Map<int, List<StudyDay>> byWeek = {};
    for (final d in app.days) {
      byWeek.putIfAbsent(d.weekNumber ?? 0, () => []).add(d);
    }
    final weeks = byWeek.keys.toList()..sort();
    final currentDay = app.currentDayNumber;

    return RefreshIndicator(
      onRefresh: () => context.read<AppState>().bootstrap(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          if (app.offline) const OfflineBanner(),
          for (final week in weeks)
            _WeekSection(
              week: week,
              days: byWeek[week]!,
              currentDay: currentDay,
              onOpenDay: (day) => _openDay(context, day),
            ),
        ],
      ),
    );
  }

  Future<void> _openDay(BuildContext context, StudyDay day) async {
    final app = context.read<AppState>();
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) =>
            DayDetailScreen(planId: day.planId, dayNumber: day.dayNumber),
      ),
    );
    await app.refreshTodayAndProgress();
  }
}

class _WeekSection extends StatelessWidget {
  const _WeekSection({
    required this.week,
    required this.days,
    required this.currentDay,
    required this.onOpenDay,
  });

  final int week;
  final List<StudyDay> days;
  final int? currentDay;
  final void Function(StudyDay) onOpenDay;

  @override
  Widget build(BuildContext context) {
    final phase = days
        .firstWhere((d) => d.phase != null,
            orElse: () => days.first)
        .phase;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 16, bottom: 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Week ${week == 0 ? '—' : week}',
                  style: Theme.of(context).textTheme.titleLarge),
              if (phase != null)
                Text(phase, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ),
        Card(
          child: Column(
            children: [
              for (final day in days)
                ListTile(
                  leading: StatusIcon(
                    status: day.status,
                    isCurrent: day.dayNumber == currentDay,
                  ),
                  title: Text('Day ${day.dayNumber} • ${day.focus ?? ''}'),
                  subtitle: day.task != null ? Text(day.task!) : null,
                  trailing: DifficultyChip(difficulty: day.difficulty),
                  onTap: () => onOpenDay(day),
                ),
            ],
          ),
        ),
      ],
    );
  }
}
