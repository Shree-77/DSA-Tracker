import 'study_status.dart';

class StudyDay {
  final int id;
  final int planId;
  final int dayNumber;
  final int? weekNumber;
  final String? phase;
  final String? focus;
  final String? task;
  final String? difficulty;
  final StudyStatus status;
  final DateTime? scheduledDate;
  final DateTime? completedAt;
  final String? notes;

  const StudyDay({
    required this.id,
    required this.planId,
    required this.dayNumber,
    required this.status,
    this.weekNumber,
    this.phase,
    this.focus,
    this.task,
    this.difficulty,
    this.scheduledDate,
    this.completedAt,
    this.notes,
  });

  factory StudyDay.fromJson(Map<String, dynamic> json) {
    return StudyDay(
      id: json['id'] as int,
      planId: json['plan_id'] as int,
      dayNumber: json['day_number'] as int,
      weekNumber: json['week_number'] as int?,
      phase: json['phase'] as String?,
      focus: json['focus'] as String?,
      task: json['task'] as String?,
      difficulty: json['difficulty'] as String?,
      status: StudyStatus.fromWire(json['status'] as String?),
      scheduledDate: _date(json['scheduled_date']),
      completedAt: _date(json['completed_at']),
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'plan_id': planId,
        'day_number': dayNumber,
        'week_number': weekNumber,
        'phase': phase,
        'focus': focus,
        'task': task,
        'difficulty': difficulty,
        'status': status.wire,
        'scheduled_date': scheduledDate?.toIso8601String(),
        'completed_at': completedAt?.toIso8601String(),
        'notes': notes,
      };

  static DateTime? _date(dynamic value) {
    if (value == null) return null;
    return DateTime.tryParse(value.toString());
  }
}
