import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/study_status.dart';
import '../../models/tracker.dart';
import '../../providers/day_detail_provider.dart';
import '../../widgets/difficulty_chip.dart';
import '../../widgets/state_views.dart';
import 'widgets/confidence_selector.dart';
import 'widgets/counter_field.dart';
import 'widgets/status_selector.dart';

class DayDetailScreen extends StatelessWidget {
  const DayDetailScreen({
    super.key,
    required this.planId,
    required this.dayNumber,
  });

  final int planId;
  final int dayNumber;

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) =>
          DayDetailProvider(planId: planId, dayNumber: dayNumber)..load(),
      child: const _DayDetailView(),
    );
  }
}

class _DayDetailView extends StatefulWidget {
  const _DayDetailView();

  @override
  State<_DayDetailView> createState() => _DayDetailViewState();
}

class _DayDetailViewState extends State<_DayDetailView> {
  final _hoursCtrl = TextEditingController();
  final _reflectionCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  bool _controllersInit = false;

  @override
  void dispose() {
    _hoursCtrl.dispose();
    _reflectionCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  void _initControllers(DayDetailProvider p) {
    if (_controllersInit) return;
    _hoursCtrl.text =
        p.tracker.studyHours == 0 ? '' : p.tracker.studyHours.toString();
    _reflectionCtrl.text = p.tracker.reflection ?? '';
    _notesCtrl.text = p.notes;
    _controllersInit = true;
  }

  @override
  Widget build(BuildContext context) {
    final p = context.watch<DayDetailProvider>();

    return Scaffold(
      appBar: AppBar(title: Text('Day ${p.dayNumber}')),
      body: switch (p.state) {
        DayLoad.loading => const LoadingView(),
        DayLoad.error => ErrorView(
            message: p.errorMessage,
            onRetry: () => context.read<DayDetailProvider>().load(),
          ),
        DayLoad.ready => _buildContent(context, p),
      },
    );
  }

  Widget _buildContent(BuildContext context, DayDetailProvider p) {
    _initControllers(p);
    final day = p.day!;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      children: [
        // Header
        Text(day.phase ?? '', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 4),
        Text(day.focus ?? '',
            style: Theme.of(context).textTheme.headlineSmall),
        if (day.task != null) ...[
          const SizedBox(height: 8),
          Text(day.task!, style: Theme.of(context).textTheme.bodyLarge),
        ],
        const SizedBox(height: 12),
        Row(children: [DifficultyChip(difficulty: day.difficulty)]),
        const Divider(height: 40),

        // Status
        Text('Status', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        StatusSelector(
          value: day.status,
          onChanged: (s) => context.read<DayDetailProvider>().setStatusLocal(s),
        ),
        const Divider(height: 40),

        // Study time
        Text('Study Time', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        TextField(
          controller: _hoursCtrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(
            labelText: 'Study Hours',
            hintText: 'e.g. 2.0',
          ),
          onChanged: (v) {
            final hours = double.tryParse(v) ?? 0;
            context
                .read<DayDetailProvider>()
                .updateTracker(p.tracker.copyWith(studyHours: hours));
          },
        ),
        const SizedBox(height: 24),

        // Problem tracking
        Text('Problem Tracking',
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        CounterField(
          label: 'Problems Attempted',
          value: p.tracker.problemsAttempted,
          onChanged: (v) => context
              .read<DayDetailProvider>()
              .updateTracker(p.tracker.copyWith(problemsAttempted: v)),
        ),
        CounterField(
          label: 'Solved Alone',
          value: p.tracker.solvedAlone,
          onChanged: (v) => context
              .read<DayDetailProvider>()
              .updateTracker(p.tracker.copyWith(solvedAlone: v)),
        ),
        CounterField(
          label: 'Needed Hint',
          value: p.tracker.neededHint,
          onChanged: (v) => context
              .read<DayDetailProvider>()
              .updateTracker(p.tracker.copyWith(neededHint: v)),
        ),
        CounterField(
          label: 'Needed Solution',
          value: p.tracker.neededSolution,
          onChanged: (v) => context
              .read<DayDetailProvider>()
              .updateTracker(p.tracker.copyWith(neededSolution: v)),
        ),
        const Divider(height: 40),

        // Confidence
        Text('Confidence', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        ConfidenceSelector(
          value: p.tracker.confidence,
          onChanged: (v) => context
              .read<DayDetailProvider>()
              .updateTracker(p.tracker.copyWith(confidence: v)),
        ),
        const Divider(height: 40),

        // Reflection
        Text('Reflection', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        TextField(
          controller: _reflectionCtrl,
          maxLines: 3,
          decoration:
              const InputDecoration(hintText: 'What did I learn today?'),
          onChanged: (v) => context
              .read<DayDetailProvider>()
              .updateTracker(p.tracker.copyWith(reflection: v)),
        ),
        const SizedBox(height: 20),

        // Notes
        Text('Notes', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        TextField(
          controller: _notesCtrl,
          maxLines: 3,
          decoration: const InputDecoration(hintText: 'Additional notes...'),
          onChanged: (v) =>
              context.read<DayDetailProvider>().updateNotes(v),
        ),
        const SizedBox(height: 28),

        // Actions
        FilledButton(
          onPressed: p.saving ? null : () => _save(context),
          child: p.saving
              ? const SizedBox(
                  height: 20, width: 20, child: CircularProgressIndicator())
              : const Text('Save Progress'),
        ),
        const SizedBox(height: 12),
        FilledButton.tonal(
          onPressed: p.saving ? null : () => _markComplete(context),
          child: const Text('Mark Day Complete'),
        ),
      ],
    );
  }

  Future<void> _save(BuildContext context) async {
    final ok = await context.read<DayDetailProvider>().save();
    if (!context.mounted) return;
    _snack(context, ok ? 'Progress saved' : 'Could not save progress');
  }

  Future<void> _markComplete(BuildContext context) async {
    final provider = context.read<DayDetailProvider>();
    final ok = await provider.save(overrideStatus: StudyStatus.done);
    if (!context.mounted) return;
    if (ok) {
      _snack(context, 'Day marked complete 🎉');
      Navigator.of(context).pop();
    } else {
      _snack(context, 'Could not update day');
    }
  }

  void _snack(BuildContext context, String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }
}
