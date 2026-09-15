/// Mirrors the backend `StudyStatus` enum.
enum StudyStatus {
  notStarted('NOT_STARTED'),
  inProgress('IN_PROGRESS'),
  done('DONE'),
  skipped('SKIPPED');

  final String wire;
  const StudyStatus(this.wire);

  static StudyStatus fromWire(String? value) {
    return StudyStatus.values.firstWhere(
      (s) => s.wire == value,
      orElse: () => StudyStatus.notStarted,
    );
  }

  String get label => switch (this) {
        StudyStatus.notStarted => 'Not Started',
        StudyStatus.inProgress => 'In Progress',
        StudyStatus.done => 'Done',
        StudyStatus.skipped => 'Skipped',
      };
}
