import 'package:flutter/material.dart';

/// Colored chip for a difficulty label.
class DifficultyChip extends StatelessWidget {
  const DifficultyChip({super.key, required this.difficulty});
  final String? difficulty;

  @override
  Widget build(BuildContext context) {
    final label = (difficulty == null || difficulty!.isEmpty)
        ? 'N/A'
        : difficulty!;
    final color = _colorFor(label);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
      ),
    );
  }

  Color _colorFor(String label) {
    switch (label.toLowerCase()) {
      case 'easy':
        return Colors.green.shade700;
      case 'medium':
        return Colors.orange.shade800;
      case 'hard':
        return Colors.red.shade700;
      case 'mixed':
        return Colors.blue.shade700;
      default:
        return Colors.grey.shade600;
    }
  }
}
