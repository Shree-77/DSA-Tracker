/// Models for the AI study-plan feature.

/// Non-secret view of the user's AI settings returned by the backend.
class AiSettings {
  final bool configured;
  final String? provider;
  final String? model;
  final String? apiKeyPreview;

  const AiSettings({
    required this.configured,
    this.provider,
    this.model,
    this.apiKeyPreview,
  });

  factory AiSettings.fromJson(Map<String, dynamic> json) => AiSettings(
        configured: json['configured'] as bool? ?? false,
        provider: json['provider'] as String?,
        model: json['model'] as String?,
        apiKeyPreview: json['api_key_preview'] as String?,
      );
}

/// A single chat turn. `role` is 'user' or 'assistant'.
class ChatMessage {
  final String role;
  final String content;

  const ChatMessage({required this.role, required this.content});

  bool get isUser => role == 'user';

  Map<String, dynamic> toJson() => {'role': role, 'content': content};
}

/// One day of an AI-generated plan (preview before import).
class GeneratedDay {
  final int day;
  final int? week;
  final String? phase;
  final String? focus;
  final String? task;
  final String? difficulty;
  final String? notes;

  const GeneratedDay({
    required this.day,
    this.week,
    this.phase,
    this.focus,
    this.task,
    this.difficulty,
    this.notes,
  });

  factory GeneratedDay.fromJson(Map<String, dynamic> json) => GeneratedDay(
        day: json['day'] as int,
        week: json['week'] as int?,
        phase: json['phase'] as String?,
        focus: json['focus'] as String?,
        task: json['task'] as String?,
        difficulty: json['difficulty'] as String?,
        notes: json['notes'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'day': day,
        if (week != null) 'week': week,
        if (phase != null) 'phase': phase,
        if (focus != null) 'focus': focus,
        if (task != null) 'task': task,
        if (difficulty != null) 'difficulty': difficulty,
        if (notes != null) 'notes': notes,
      };
}

/// The full structured plan the AI produced.
class GeneratedPlan {
  final String name;
  final String? description;
  final int totalDays;
  final List<GeneratedDay> days;

  const GeneratedPlan({
    required this.name,
    this.description,
    required this.totalDays,
    required this.days,
  });

  factory GeneratedPlan.fromJson(Map<String, dynamic> json) => GeneratedPlan(
        name: json['name'] as String? ?? 'AI Study Plan',
        description: json['description'] as String?,
        totalDays: json['total_days'] as int? ?? 0,
        days: ((json['days'] as List?) ?? [])
            .map((e) => GeneratedDay.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        if (description != null) 'description': description,
        'total_days': totalDays,
        'days': days.map((d) => d.toJson()).toList(),
      };

  /// Distinct week count for a compact preview summary.
  int get weekCount => days.map((d) => d.week).whereType<int>().toSet().length;
}
