import 'package:flutter/material.dart';

import '../models/study_status.dart';

/// Visual indicator: ✓ completed, → current, ○ not started.
class StatusIcon extends StatelessWidget {
  const StatusIcon({super.key, required this.status, this.isCurrent = false});

  final StudyStatus status;
  final bool isCurrent;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    if (status == StudyStatus.done) {
      return Icon(Icons.check_circle, color: Colors.green.shade600, size: 24);
    }
    if (status == StudyStatus.skipped) {
      return Icon(Icons.remove_circle_outline,
          color: scheme.outline, size: 24);
    }
    if (isCurrent || status == StudyStatus.inProgress) {
      return Icon(Icons.play_circle_fill, color: scheme.primary, size: 24);
    }
    return Icon(Icons.circle_outlined, color: scheme.outline, size: 24);
  }
}
