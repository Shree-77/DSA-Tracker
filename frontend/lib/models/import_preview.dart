class PhaseSummary {
  final String name;
  final int days;
  const PhaseSummary({required this.name, required this.days});

  factory PhaseSummary.fromJson(Map<String, dynamic> json) =>
      PhaseSummary(name: json['name'] as String, days: json['days'] as int);
}

class ImportPreview {
  final bool valid;
  final String planName;
  final int totalDays;
  final int totalWeeks;
  final int totalPhases;
  final List<PhaseSummary> phases;
  final DateTime? startDate;
  final DateTime? endDate;
  final List<String> errors;
  final int trackersDetected;

  const ImportPreview({
    required this.valid,
    required this.planName,
    required this.totalDays,
    required this.totalWeeks,
    required this.totalPhases,
    this.phases = const [],
    this.startDate,
    this.endDate,
    this.errors = const [],
    this.trackersDetected = 0,
  });

  factory ImportPreview.fromJson(Map<String, dynamic> json) => ImportPreview(
        valid: json['valid'] as bool? ?? false,
        planName: json['plan_name'] as String? ?? 'Imported Plan',
        totalDays: json['total_days'] as int? ?? 0,
        totalWeeks: json['total_weeks'] as int? ?? 0,
        totalPhases: json['total_phases'] as int? ?? 0,
        phases: ((json['phases'] as List?) ?? [])
            .map((e) => PhaseSummary.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
        startDate: json['start_date'] != null
            ? DateTime.tryParse(json['start_date'].toString())
            : null,
        endDate: json['end_date'] != null
            ? DateTime.tryParse(json['end_date'].toString())
            : null,
        errors: ((json['errors'] as List?) ?? [])
            .map((e) => e.toString())
            .toList(),
        trackersDetected: json['trackers_detected'] as int? ?? 0,
      );
}

class ImportSummary {
  final int planId;
  final String planName;
  final int totalDays;
  final int totalWeeks;
  final int totalPhases;

  const ImportSummary({
    required this.planId,
    required this.planName,
    required this.totalDays,
    required this.totalWeeks,
    required this.totalPhases,
  });

  factory ImportSummary.fromJson(Map<String, dynamic> json) => ImportSummary(
        planId: (json['plan'] as Map)['id'] as int,
        planName: (json['plan'] as Map)['name'] as String,
        totalDays: json['total_days'] as int,
        totalWeeks: json['total_weeks'] as int,
        totalPhases: json['total_phases'] as int,
      );
}
