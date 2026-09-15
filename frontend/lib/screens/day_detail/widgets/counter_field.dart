import 'package:flutter/material.dart';

/// A label with -/+ stepper for integer problem counts.
class CounterField extends StatelessWidget {
  const CounterField({
    super.key,
    required this.label,
    required this.value,
    required this.onChanged,
    this.min = 0,
  });

  final String label;
  final int value;
  final int min;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          IconButton.filledTonal(
            iconSize: 20,
            onPressed:
                value > min ? () => onChanged(value - 1) : null,
            icon: const Icon(Icons.remove),
          ),
          SizedBox(
            width: 40,
            child: Text(
              '$value',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ),
          IconButton.filledTonal(
            iconSize: 20,
            onPressed: () => onChanged(value + 1),
            icon: const Icon(Icons.add),
          ),
        ],
      ),
    );
  }
}
