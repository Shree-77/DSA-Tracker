import 'package:flutter/material.dart';

import '../../../models/study_status.dart';

/// Segmented control: Not Started / In Progress / Done.
class StatusSelector extends StatelessWidget {
  const StatusSelector({
    super.key,
    required this.value,
    required this.onChanged,
  });

  final StudyStatus value;
  final ValueChanged<StudyStatus> onChanged;

  @override
  Widget build(BuildContext context) {
    return SegmentedButton<StudyStatus>(
      segments: const [
        ButtonSegment(
          value: StudyStatus.notStarted,
          icon: Icon(Icons.circle_outlined),
          label: Text('Not Started'),
        ),
        ButtonSegment(
          value: StudyStatus.inProgress,
          icon: Icon(Icons.timelapse),
          label: Text('In Progress'),
        ),
        ButtonSegment(
          value: StudyStatus.done,
          icon: Icon(Icons.check_circle),
          label: Text('Done'),
        ),
      ],
      selected: {_normalize(value)},
      showSelectedIcon: false,
      onSelectionChanged: (set) => onChanged(set.first),
    );
  }

  StudyStatus _normalize(StudyStatus s) =>
      s == StudyStatus.skipped ? StudyStatus.notStarted : s;
}
