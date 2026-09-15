import 'package:flutter/material.dart';

/// 1–5 confidence selector.
class ConfidenceSelector extends StatelessWidget {
  const ConfidenceSelector({
    super.key,
    required this.value,
    required this.onChanged,
  });

  final int? value;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: List.generate(5, (i) {
        final level = i + 1;
        final selected = value == level;
        return GestureDetector(
          onTap: () => onChanged(level),
          child: Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: selected ? scheme.primary : scheme.surfaceContainerHighest,
              border: Border.all(
                color: selected ? scheme.primary : scheme.outlineVariant,
              ),
            ),
            alignment: Alignment.center,
            child: Text(
              '$level',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: selected ? scheme.onPrimary : scheme.onSurface,
              ),
            ),
          ),
        );
      }),
    );
  }
}
