class WeeklyProgress {
  final int weekNumber;
  final String? phase;
  final int total;
  final int completed;

  const WeeklyProgress({
    required this.weekNumber,
    required this.total,
    required this.completed,
    this.phase,
  });

  factory WeeklyProgress.fromJson(Map<String, dynamic> json) => WeeklyProgress(
        weekNumber: json['week_number'] as int,
        phase: json['phase'] as String?,
        total: json['total'] as int,
        completed: json['completed'] as int,
      );

  double get ratio => total == 0 ? 0 : completed / total;
}

class DifficultyBreakdown {
  final String difficulty;
  final int total;
  final int completed;

  const DifficultyBreakdown({
    required this.difficulty,
    required this.total,
    required this.completed,
  });

  factory DifficultyBreakdown.fromJson(Map<String, dynamic> json) =>
      DifficultyBreakdown(
        difficulty: json['difficulty'] as String,
        total: json['total'] as int,
        completed: json['completed'] as int,
      );
}

class Progress {
  final int totalDays;
  final int completedDays;
  final int remainingDays;
  final double completionPercentage;
  final int currentStreak;
  final int longestStreak;
  final double totalStudyHours;
  final int problemsAttempted;
  final int solvedAlone;
  final int neededHint;
  final int neededSolution;
  final double? averageConfidence;
  final List<WeeklyProgress> weekly;
  final List<DifficultyBreakdown> difficulty;

  const Progress({
    required this.totalDays,
    required this.completedDays,
    required this.remainingDays,
    required this.completionPercentage,
    required this.currentStreak,
    required this.longestStreak,
    required this.totalStudyHours,
    required this.problemsAttempted,
    required this.solvedAlone,
    required this.neededHint,
    required this.neededSolution,
    this.averageConfidence,
    this.weekly = const [],
    this.difficulty = const [],
  });

  factory Progress.fromJson(Map<String, dynamic> json) => Progress(
        totalDays: json['total_days'] as int,
        completedDays: json['completed_days'] as int,
        remainingDays: json['remaining_days'] as int,
        completionPercentage:
            (json['completion_percentage'] as num).toDouble(),
        currentStreak: json['current_streak'] as int,
        longestStreak: json['longest_streak'] as int,
        totalStudyHours: (json['total_study_hours'] as num).toDouble(),
        problemsAttempted: json['problems_attempted'] as int,
        solvedAlone: json['solved_alone'] as int,
        neededHint: json['needed_hint'] as int,
        neededSolution: json['needed_solution'] as int,
        averageConfidence: (json['average_confidence'] as num?)?.toDouble(),
        weekly: ((json['weekly'] as List?) ?? [])
            .map((e) => WeeklyProgress.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
        difficulty: ((json['difficulty'] as List?) ?? [])
            .map((e) =>
                DifficultyBreakdown.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
      );
}
