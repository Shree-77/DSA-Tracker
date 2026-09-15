/// Lifecycle status of a study plan (mirrors the backend `PlanStatus` enum).
enum PlanStatus {
  active,
  completed,
  archived;

  /// Wire value sent to / received from the backend.
  String get wire => switch (this) {
        PlanStatus.active => 'ACTIVE',
        PlanStatus.completed => 'COMPLETED',
        PlanStatus.archived => 'ARCHIVED',
      };

  static PlanStatus fromWire(String? value) => switch (value) {
        'COMPLETED' => PlanStatus.completed,
        'ARCHIVED' => PlanStatus.archived,
        _ => PlanStatus.active,
      };

  String get label => switch (this) {
        PlanStatus.active => 'Active',
        PlanStatus.completed => 'Completed',
        PlanStatus.archived => 'Archived',
      };
}

class Plan {
  final int id;
  final String name;
  final String? description;
  final int totalDays;
  final PlanStatus status;

  /// True when this is the user's currently selected ("current") plan.
  final bool isSelected;
  final DateTime? completedAt;
  final DateTime? createdAt;

  const Plan({
    required this.id,
    required this.name,
    required this.totalDays,
    this.status = PlanStatus.active,
    this.isSelected = false,
    this.description,
    this.completedAt,
    this.createdAt,
  });

  bool get isCompleted => status == PlanStatus.completed;

  factory Plan.fromJson(Map<String, dynamic> json) {
    return Plan(
      id: json['id'] as int,
      name: json['name'] as String,
      description: json['description'] as String?,
      totalDays: json['total_days'] as int? ?? 0,
      status: PlanStatus.fromWire(json['status'] as String?),
      isSelected: json['is_selected'] as bool? ?? false,
      completedAt: json['completed_at'] != null
          ? DateTime.tryParse(json['completed_at'].toString())
          : null,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'description': description,
        'total_days': totalDays,
        'status': status.wire,
        'is_selected': isSelected,
        'completed_at': completedAt?.toIso8601String(),
        'created_at': createdAt?.toIso8601String(),
      };
}
