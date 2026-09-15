import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/progress.dart';
import '../../providers/app_state.dart';
import '../../widgets/progress_bar.dart';
import '../../widgets/state_views.dart';

class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final app = context.watch<AppState>();

    return Scaffold(
      appBar: AppBar(title: const Text('Progress')),
      body: switch (app.state) {
        LoadState.loading || LoadState.idle => const LoadingView(),
        LoadState.error => ErrorView(
            message: app.errorMessage,
            onRetry: () => context.read<AppState>().bootstrap(),
          ),
        LoadState.empty => const EmptyView(
            icon: Icons.bar_chart_outlined,
            title: 'No progress yet',
            body: 'Import a plan and start studying to see progress.',
          ),
        LoadState.ready => _buildProgress(context, app),
      },
    );
  }

  Widget _buildProgress(BuildContext context, AppState app) {
    final p = app.progress;
    if (p == null) {
      return const EmptyView(
        icon: Icons.cloud_off,
        title: 'Progress unavailable offline',
        body: 'Reconnect to load your latest statistics.',
      );
    }
    return RefreshIndicator(
      onRefresh: () => context.read<AppState>().bootstrap(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        children: [
          if (app.offline) const OfflineBanner(),
          _overall(context, p),
          const SizedBox(height: 20),
          _statsRow(context, p),
          const SizedBox(height: 28),
          Text('Weekly Progress',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          ...p.weekly.map((w) => _weeklyRow(context, w)),
          const SizedBox(height: 28),
          Text('Difficulty Breakdown',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          ...p.difficulty.map((d) => _difficultyRow(context, d)),
          const SizedBox(height: 28),
          Text('Study Statistics',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          _statTile('Total study hours', p.totalStudyHours.toStringAsFixed(1)),
          _statTile('Problems attempted', '${p.problemsAttempted}'),
          _statTile('Problems solved alone', '${p.solvedAlone}'),
          _statTile('Hints used', '${p.neededHint}'),
          _statTile('Solutions needed', '${p.neededSolution}'),
          _statTile(
            'Average confidence',
            p.averageConfidence == null
                ? '—'
                : p.averageConfidence!.toStringAsFixed(1),
          ),
        ],
      ),
    );
  }

  Widget _overall(BuildContext context, Progress p) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Overall Progress',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text('${p.completedDays} / ${p.totalDays}',
                style: Theme.of(context).textTheme.headlineMedium),
            Text('${p.completionPercentage.toStringAsFixed(0)}%',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            LabeledProgressBar(value: p.completionPercentage / 100),
          ],
        ),
      ),
    );
  }

  Widget _statsRow(BuildContext context, Progress p) {
    return Row(
      children: [
        _miniStat(context, 'Completed', '${p.completedDays}', Icons.check),
        const SizedBox(width: 12),
        _miniStat(context, 'Remaining', '${p.remainingDays}', Icons.schedule),
        const SizedBox(width: 12),
        _miniStat(context, 'Streak', '${p.currentStreak}d',
            Icons.local_fire_department),
      ],
    );
  }

  Widget _miniStat(
      BuildContext context, String label, String value, IconData icon) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: Column(
            children: [
              Icon(icon, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 8),
              Text(value, style: Theme.of(context).textTheme.titleLarge),
              Text(label, style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }

  Widget _weeklyRow(BuildContext context, WeeklyProgress w) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(width: 64, child: Text('Week ${w.weekNumber}')),
          Expanded(child: LabeledProgressBar(value: w.ratio, height: 8)),
          const SizedBox(width: 12),
          Text('${w.completed}/${w.total}'),
        ],
      ),
    );
  }

  Widget _difficultyRow(BuildContext context, DifficultyBreakdown d) {
    final ratio = d.total == 0 ? 0.0 : d.completed / d.total;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(width: 72, child: Text(d.difficulty)),
          Expanded(child: LabeledProgressBar(value: ratio, height: 8)),
          const SizedBox(width: 12),
          Text('${d.completed}/${d.total}'),
        ],
      ),
    );
  }

  Widget _statTile(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
