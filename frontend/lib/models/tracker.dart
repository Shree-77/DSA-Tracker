class Tracker {
  final int? id;
  final int? studyDayId;
  final DateTime? studyDate;
  final double studyHours;
  final int problemsAttempted;
  final int solvedAlone;
  final int neededHint;
  final int neededSolution;
  final int? confidence;
  final String? reflection;

  const Tracker({
    this.id,
    this.studyDayId,
    this.studyDate,
    this.studyHours = 0.0,
    this.problemsAttempted = 0,
    this.solvedAlone = 0,
    this.neededHint = 0,
    this.neededSolution = 0,
    this.confidence,
    this.reflection,
  });

  factory Tracker.empty() => const Tracker();

  factory Tracker.fromJson(Map<String, dynamic> json) {
    return Tracker(
      id: json['id'] as int?,
      studyDayId: json['study_day_id'] as int?,
      studyDate: json['study_date'] != null
          ? DateTime.tryParse(json['study_date'].toString())
          : null,
      studyHours: (json['study_hours'] as num?)?.toDouble() ?? 0.0,
      problemsAttempted: json['problems_attempted'] as int? ?? 0,
      solvedAlone: json['solved_alone'] as int? ?? 0,
      neededHint: json['needed_hint'] as int? ?? 0,
      neededSolution: json['needed_solution'] as int? ?? 0,
      confidence: json['confidence'] as int?,
      reflection: json['reflection'] as String?,
    );
  }

  Map<String, dynamic> toRequest() => {
        'study_hours': studyHours,
        'problems_attempted': problemsAttempted,
        'solved_alone': solvedAlone,
        'needed_hint': neededHint,
        'needed_solution': neededSolution,
        'confidence': confidence,
        'reflection': reflection,
      };

  Tracker copyWith({
    double? studyHours,
    int? problemsAttempted,
    int? solvedAlone,
    int? neededHint,
    int? neededSolution,
    int? confidence,
    String? reflection,
  }) {
    return Tracker(
      id: id,
      studyDayId: studyDayId,
      studyDate: studyDate,
      studyHours: studyHours ?? this.studyHours,
      problemsAttempted: problemsAttempted ?? this.problemsAttempted,
      solvedAlone: solvedAlone ?? this.solvedAlone,
      neededHint: neededHint ?? this.neededHint,
      neededSolution: neededSolution ?? this.neededSolution,
      confidence: confidence ?? this.confidence,
      reflection: reflection ?? this.reflection,
    );
  }
}
