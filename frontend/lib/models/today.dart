import 'study_day.dart';

/// Mirrors the backend `TodayResponse`.
class Today {
  /// One of: before | active | completed | empty
  final String state;
  final StudyDay? day;
  final List<StudyDay> upcoming;
  final int? daysUntilStart;
  final int totalDays;
  final int completedDays;
  final double completionPercentage;
  final String? message;

  const Today({
    required this.state,
    required this.totalDays,
    required this.completedDays,
    required this.completionPercentage,
    this.day,
    this.upcoming = const [],
    this.daysUntilStart,
    this.message,
  });

  factory Today.fromJson(Map<String, dynamic> json) {
    return Today(
      state: json['state'] as String? ?? 'empty',
      day: json['day'] != null
          ? StudyDay.fromJson((json['day'] as Map).cast<String, dynamic>())
          : null,
      upcoming: ((json['upcoming'] as List?) ?? [])
          .map((e) => StudyDay.fromJson((e as Map).cast<String, dynamic>()))
          .toList(),
      daysUntilStart: json['days_until_start'] as int?,
      totalDays: json['total_days'] as int? ?? 0,
      completedDays: json['completed_days'] as int? ?? 0,
      completionPercentage:
          (json['completion_percentage'] as num?)?.toDouble() ?? 0.0,
      message: json['message'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'state': state,
        'day': day?.toJson(),
        'upcoming': upcoming.map((e) => e.toJson()).toList(),
        'days_until_start': daysUntilStart,
        'total_days': totalDays,
        'completed_days': completedDays,
        'completion_percentage': completionPercentage,
        'message': message,
      };
}
