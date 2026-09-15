class Plan {
  final int id;
  final String name;
  final String? description;
  final int totalDays;
  final DateTime? createdAt;

  const Plan({
    required this.id,
    required this.name,
    required this.totalDays,
    this.description,
    this.createdAt,
  });

  factory Plan.fromJson(Map<String, dynamic> json) {
    return Plan(
      id: json['id'] as int,
      name: json['name'] as String,
      description: json['description'] as String?,
      totalDays: json['total_days'] as int? ?? 0,
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
        'created_at': createdAt?.toIso8601String(),
      };
}
